from __future__ import annotations

from typing import Callable, Optional
import logging
import queue
import threading
import time
import sys

import cv2

from core.signal_manager import SignalManager
from utils.config import AppConfig


class CameraManager:
    """Camera capture with auto reconnect and FPS limiting."""

    def __init__(
        self,
        config: AppConfig,
        frame_queue: queue.Queue,
        signal_manager: SignalManager,
        logger: logging.Logger,
        capture_factory: Optional[Callable[[int], cv2.VideoCapture]] = None,
    ) -> None:
        self._camera_index = int(config.camera_index)
        self._target_fps = int(config.target_fps)
        self._frame_width = int(config.frame_width)
        self._frame_height = int(config.frame_height)
        self._reconnect_interval = float(config.reconnect_interval_sec)

        self._frame_queue = frame_queue
        self._signal_manager = signal_manager
        self._logger = logger
        self._capture_factory = capture_factory or cv2.VideoCapture

        self._capture: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._running = False
        self._open_failures = 0
        self._last_hint_time = 0.0
        self._hint_interval = 5.0

    def start(self) -> None:
        """Start the camera capture thread."""
        if self._running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self) -> None:
        """Stop the camera capture thread and release the camera."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._thread = None
        self._running = False
        self._release_capture()

    def open(self) -> bool:
        """Open the camera once without starting the thread."""
        with self._lock:
            return self._open_capture()

    def set_camera_index(self, index: int) -> None:
        """Switch to another camera index."""
        with self._lock:
            self._camera_index = int(index)
            self._release_capture()

    def set_target_fps(self, fps: int) -> None:
        """Update the FPS limiter."""
        self._target_fps = int(fps)

    def reconnect(self) -> None:
        """Force the camera to reconnect on the next capture cycle."""
        with self._lock:
            self._release_capture()
            self._open_failures = 0
        if not self._running:
            opened = self._open_capture()
            if opened:
                self._signal_manager.status_ready.emit("Camera OK")
            else:
                self._handle_open_failure()

    @property
    def is_running(self) -> bool:
        return self._running

    def _run(self) -> None:
        target_interval = 1.0 / self._target_fps if self._target_fps > 0 else 0.0
        while not self._stop_event.is_set():
            if not self._capture or not self._capture.isOpened():
                opened = self._open_capture()
                if not opened:
                    self._handle_open_failure()
                    time.sleep(self._reconnect_interval)
                    continue

            frame_start = time.perf_counter()
            ret, frame = self._capture.read()
            if not ret:
                self._logger.warning("Camera frame read failed")
                self._signal_manager.status_ready.emit("Camera disconnected")
                self._release_capture()
                time.sleep(self._reconnect_interval)
                continue

            self._signal_manager.status_ready.emit("Camera OK")

            if self._frame_queue.full():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    pass
            try:
                self._frame_queue.put_nowait(frame)
            except queue.Full:
                pass

            elapsed = time.perf_counter() - frame_start
            if target_interval > 0 and elapsed < target_interval:
                time.sleep(target_interval - elapsed)

        self._release_capture()

    def _open_capture(self) -> bool:
        self._release_capture()
        self._capture = self._capture_factory(self._camera_index)
        if not self._capture or not self._capture.isOpened():
            self._logger.error("Failed to open camera index %s", self._camera_index)
            self._capture = None
            return False

        self._open_failures = 0

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._frame_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._frame_height)
        if self._target_fps > 0:
            self._capture.set(cv2.CAP_PROP_FPS, self._target_fps)
        self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return True

    def _handle_open_failure(self) -> None:
        self._open_failures += 1
        now = time.monotonic()
        if self._open_failures < 3 or (now - self._last_hint_time) < self._hint_interval:
            self._signal_manager.status_ready.emit("Camera not available")
            return

        self._last_hint_time = now
        if sys.platform == "darwin":
            message = (
                "Camera permission denied. Allow access in System Settings > Privacy & Security > Camera."
            )
        else:
            message = "Camera permission denied or in use. Check system camera permissions."
        self._signal_manager.status_ready.emit(message)
        self._logger.warning(message)

    def _release_capture(self) -> None:
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception:
                pass
        self._capture = None
