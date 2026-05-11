from __future__ import annotations

from typing import List, Optional
import logging

import mediapipe as mp
import numpy as np
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

from utils.config import AppConfig


class FaceDetector:
    """MediaPipe Face Mesh wrapper with landmark caching."""

    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self._logger = logger
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=config.max_faces,
            refine_landmarks=True,
            min_detection_confidence=config.min_detection_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
        )
        self._last_landmarks: Optional[List[NormalizedLandmark]] = None
        self._stale_frames = 0
        self._max_stale = config.landmark_stale_frames

    def detect(self, frame_rgb: np.ndarray) -> Optional[List[NormalizedLandmark]]:
        """Return landmarks for the first detected face, or cached values."""
        try:
            results = self._face_mesh.process(frame_rgb)
        except Exception as exc:
            self._logger.error("Face mesh processing failed: %s", exc)
            return None

        if results.multi_face_landmarks:
            self._last_landmarks = results.multi_face_landmarks[0].landmark
            self._stale_frames = 0
            return self._last_landmarks

        if self._last_landmarks is not None and self._stale_frames < self._max_stale:
            self._stale_frames += 1
            return self._last_landmarks

        self._last_landmarks = None
        return None

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._face_mesh.close()
