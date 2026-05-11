from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import cv2
import numpy as np
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark

Point = Tuple[int, int]


def draw_eye_landmarks(
    frame: np.ndarray,
    landmarks: Sequence[NormalizedLandmark],
    image_shape: Tuple[int, int, int],
    indices: Sequence[int],
    color: Tuple[int, int, int],
) -> None:
    """Draw eye landmarks and a thin contour line."""
    height, width = image_shape[0], image_shape[1]
    points: List[Point] = []

    for idx in indices:
        lm = landmarks[idx]
        x = int(lm.x * width)
        y = int(lm.y * height)
        points.append((x, y))
        cv2.circle(frame, (x, y), 2, color, -1, lineType=cv2.LINE_AA)

    if len(points) >= 2:
        cv2.polylines(
            frame,
            [np.array(points, dtype=np.int32)],
            isClosed=True,
            color=color,
            thickness=1,
            lineType=cv2.LINE_AA,
        )


def draw_text_block(
    frame: np.ndarray,
    lines: Iterable[str],
    origin: Point = (12, 24),
    line_height: int = 22,
) -> None:
    """Draw multiple lines of text on the frame."""
    x, y = origin
    for line in lines:
        cv2.putText(
            frame,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )
        y += line_height
