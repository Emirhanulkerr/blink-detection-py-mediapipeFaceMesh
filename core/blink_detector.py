from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time
from typing import Deque, List, Sequence, Tuple

from scipy.spatial.distance import euclidean
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

from utils.config import AppConfig
from utils.helpers import landmark_to_pixel

LEFT_EYE_INDICES: Tuple[int, ...] = (33, 160, 158, 133, 153, 144)
RIGHT_EYE_INDICES: Tuple[int, ...] = (362, 385, 387, 263, 373, 380)


@dataclass
class BlinkResult:
    """Blink detection outputs for a single frame."""

    left_ear: float
    right_ear: float
    avg_ear: float
    blink_count: int
    blink_event: bool
    is_blinking: bool
    threshold: float
    face_detected: bool


class BlinkDetector:
    """Blink detection logic based on Eye Aspect Ratio (EAR)."""

    def __init__(self, config: AppConfig) -> None:
        self._base_threshold = float(config.ear_threshold)
        self._min_frames = int(config.min_consecutive_frames)
        self._dynamic_threshold = bool(config.dynamic_threshold)
        self._dynamic_ratio = float(config.dynamic_ratio)
        self._debounce_sec = float(config.blink_debounce_ms) / 1000.0

        self._blink_count = 0
        self._closed_frames = 0
        self._is_blinking = False
        self._last_blink_time = 0.0
        self._open_ear_ema: float | None = None
        self._ema_alpha = 0.1

        self._ear_history: Deque[float] = deque(maxlen=config.ear_history_size)
        self._blink_events: List[dict] = []
        self._session_start = time.time()

    @staticmethod
    def compute_ear(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        p4: Tuple[float, float],
        p5: Tuple[float, float],
        p6: Tuple[float, float],
    ) -> float:
        """Compute EAR from six eye landmark points."""
        p2_p6 = euclidean(p2, p6)
        p3_p5 = euclidean(p3, p5)
        p1_p4 = euclidean(p1, p4)
        if p1_p4 <= 0:
            return 0.0
        return (p2_p6 + p3_p5) / (2.0 * p1_p4)

    def update_from_landmarks(
        self,
        landmarks: Sequence[NormalizedLandmark],
        image_shape: Tuple[int, int, int],
        timestamp: float,
    ) -> BlinkResult:
        """Update blink state from landmarks."""
        height, width = image_shape[0], image_shape[1]
        left_points = self._eye_points(landmarks, LEFT_EYE_INDICES, width, height)
        right_points = self._eye_points(landmarks, RIGHT_EYE_INDICES, width, height)

        left_ear = self.compute_ear(*left_points)
        right_ear = self.compute_ear(*right_points)

        return self.process_ear(left_ear, right_ear, timestamp)

    def process_ear(self, left_ear: float, right_ear: float, timestamp: float) -> BlinkResult:
        """Update blink state from explicit EAR values."""
        avg_ear = (left_ear + right_ear) / 2.0
        threshold = self._compute_threshold(avg_ear)
        blink_event = False

        if left_ear < threshold and right_ear < threshold:
            self._closed_frames += 1
            if self._closed_frames >= self._min_frames:
                self._is_blinking = True
        else:
            if self._is_blinking and self._closed_frames >= self._min_frames:
                if (timestamp - self._last_blink_time) >= self._debounce_sec:
                    self._blink_count += 1
                    self._last_blink_time = timestamp
                    blink_event = True
                    self._blink_events.append({"timestamp": timestamp, "ear": avg_ear})
            self._closed_frames = 0
            self._is_blinking = False

        self._ear_history.append(avg_ear)

        return BlinkResult(
            left_ear=left_ear,
            right_ear=right_ear,
            avg_ear=avg_ear,
            blink_count=self._blink_count,
            blink_event=blink_event,
            is_blinking=self._is_blinking,
            threshold=threshold,
            face_detected=True,
        )

    def update_no_face(self, timestamp: float) -> BlinkResult:
        """Return a result when no face is detected."""
        return BlinkResult(
            left_ear=0.0,
            right_ear=0.0,
            avg_ear=0.0,
            blink_count=self._blink_count,
            blink_event=False,
            is_blinking=False,
            threshold=self._base_threshold,
            face_detected=False,
        )

    def set_threshold(self, value: float) -> None:
        """Override the base EAR threshold."""
        self._base_threshold = float(value)

    def set_dynamic_threshold(self, enabled: bool) -> None:
        """Enable or disable dynamic thresholding."""
        self._dynamic_threshold = bool(enabled)
        self._open_ear_ema = None

    def reset(self) -> None:
        """Reset blink counters and history."""
        self._blink_count = 0
        self._closed_frames = 0
        self._is_blinking = False
        self._last_blink_time = 0.0
        self._open_ear_ema = None
        self._ear_history.clear()
        self._blink_events.clear()
        self._session_start = time.time()

    def get_blink_events(self) -> List[dict]:
        """Return a copy of blink event list."""
        return list(self._blink_events)

    def get_ear_history(self) -> List[float]:
        """Return a copy of EAR history."""
        return list(self._ear_history)

    def get_session_stats(self) -> dict:
        """Return aggregated session statistics."""
        duration = max(0.0, time.time() - self._session_start)
        blink_rate = (self._blink_count / duration) * 60.0 if duration > 0 else 0.0
        if self._ear_history:
            avg_ear = sum(self._ear_history) / len(self._ear_history)
            min_ear = min(self._ear_history)
            max_ear = max(self._ear_history)
        else:
            avg_ear = 0.0
            min_ear = 0.0
            max_ear = 0.0

        return {
            "duration_sec": duration,
            "blink_count": self._blink_count,
            "blink_rate": blink_rate,
            "avg_ear": avg_ear,
            "min_ear": min_ear,
            "max_ear": max_ear,
        }

    def _compute_threshold(self, avg_ear: float) -> float:
        if not self._dynamic_threshold:
            return self._base_threshold

        if self._open_ear_ema is None:
            self._open_ear_ema = avg_ear
        elif avg_ear > self._base_threshold:
            self._open_ear_ema = (self._ema_alpha * avg_ear) + (
                (1.0 - self._ema_alpha) * self._open_ear_ema
            )

        if self._open_ear_ema is None:
            return self._base_threshold

        dynamic_threshold = self._open_ear_ema * self._dynamic_ratio
        return max(self._base_threshold, dynamic_threshold)

    @staticmethod
    def _eye_points(
        landmarks: Sequence[NormalizedLandmark],
        indices: Sequence[int],
        width: int,
        height: int,
    ) -> Tuple[Tuple[float, float], ...]:
        return tuple(landmark_to_pixel(landmarks[i], width, height) for i in indices)
