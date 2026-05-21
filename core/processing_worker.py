from __future__ import annotations

from dataclasses import dataclass
import logging
import queue
import threading
import time
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from core.blink_detector import BlinkDetector, BlinkResult, LEFT_EYE_INDICES, RIGHT_EYE_INDICES
from core.face_detector import FaceDetector
from core.fps_counter import FPSCounter
from core.signal_manager import SignalManager
from utils.buzzer import BuzzerController
from utils.config import AppConfig
from utils import drawing_utils


@dataclass
class FrameResult:
    """Processed frame container for UI consumption."""

    frame: np.ndarray
    metrics: Dict[str, Any]
    ear_history: List[float]
    timestamp: float


class ProcessingWorker:
    """Background worker that performs face detection and blink analysis."""

    def __init__(
        self,
        config: AppConfig,
        frame_queue: queue.Queue,
        result_queue: queue.Queue,
        face_detector: FaceDetector,
        blink_detector: BlinkDetector,
        fps_counter: FPSCounter,
        signal_manager: SignalManager,
        logger: logging.Logger,
    ) -> None:
        self._config = config
        self._frame_queue = frame_queue
        self._result_queue = result_queue
        self._face_detector = face_detector
        self._blink_detector = blink_detector
        self._fps_counter = fps_counter
        self._signal_manager = signal_manager
        self._logger = logger

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._lock = threading.Lock()
        self._buzzer = BuzzerController(enabled=True)

    def start(self) -> None:
        """Start the processing thread."""
        if self._running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self) -> None:
        """Stop the processing thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._thread = None
        self._running = False
        self._buzzer.stop()

    @property
    def is_running(self) -> bool:
        return self._running

    def set_threshold(self, value: float) -> None:
        """Update the blink detection threshold."""
        with self._lock:
            self._blink_detector.set_threshold(value)

    def set_dynamic_threshold(self, enabled: bool) -> None:
        """Enable or disable dynamic thresholding."""
        with self._lock:
            self._blink_detector.set_dynamic_threshold(enabled)

    def reset(self) -> None:
        """Reset session metrics."""
        with self._lock:
            self._blink_detector.reset()
        self._buzzer.stop()

    def get_blink_events(self) -> List[dict]:
        """Return collected blink events."""
        with self._lock:
            return self._blink_detector.get_blink_events()

    def get_session_stats(self) -> dict:
        """Return aggregated session statistics."""
        with self._lock:
            return self._blink_detector.get_session_stats()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                frame = self._frame_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                result = self._process_frame(frame)
            except Exception as exc:
                self._logger.exception("Frame processing error: %s", exc)
                continue

            if result is not None:
                self._push_result(result)

    def _process_frame(self, frame: np.ndarray) -> Optional[FrameResult]:
        frame = self._resize_frame(frame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks = self._face_detector.detect(frame_rgb)
        timestamp = time.time()

        if landmarks is not None:
            with self._lock:
                blink_result = self._blink_detector.update_from_landmarks(
                    landmarks, frame.shape, timestamp
                )
                ear_history = self._blink_detector.get_ear_history()

            if self._config.draw_landmarks:
                drawing_utils.draw_eye_landmarks(
                    frame, landmarks, frame.shape, LEFT_EYE_INDICES, (0, 200, 255)
                )
                drawing_utils.draw_eye_landmarks(
                    frame, landmarks, frame.shape, RIGHT_EYE_INDICES, (0, 200, 255)
                )
        else:
            with self._lock:
                blink_result = self._blink_detector.update_no_face(timestamp)
                ear_history = self._blink_detector.get_ear_history()
            self._buzzer.stop()

        if landmarks is not None:
            self._buzzer.update(
                eyes_closed=blink_result.eyes_closed,
                closed_duration_ms=blink_result.closed_duration_ms,
            )

        fps = self._fps_counter.update()
        metrics = {
            "blink_count": blink_result.blink_count,
            "fps": fps,
            "ear": blink_result.avg_ear,
            "left_ear": blink_result.left_ear,
            "right_ear": blink_result.right_ear,
            "threshold": blink_result.threshold,
            "face_detected": blink_result.face_detected,
        }

        if blink_result.blink_event:
            with self._lock:
                events = self._blink_detector.get_blink_events()
            last_event = events[-1] if events else {}
            self._logger.info(
                "Blink detected at %.3f (type=%s, closed_ms=%s)",
                timestamp,
                last_event.get("blink_type", ""),
                last_event.get("closed_duration_ms", ""),
            )

        self._signal_manager.metrics_ready.emit(metrics)

        return FrameResult(
            frame=frame,
            metrics=metrics,
            ear_history=ear_history,
            timestamp=timestamp,
        )

    def _push_result(self, result: FrameResult) -> None:
        if self._result_queue.full():
            try:
                self._result_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self._result_queue.put_nowait(result)
        except queue.Full:
            pass

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        target_w = int(self._config.processing_width)
        target_h = int(self._config.processing_height)
        if target_w <= 0 or target_h <= 0:
            return frame

        height, width = frame.shape[:2]
        if width == target_w and height == target_h:
            return frame

        return cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
