from __future__ import annotations

import csv
from pathlib import Path
import time
from typing import List, Sequence, Tuple

import cv2
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmark


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it does not exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def timestamp_str() -> str:
    """Return a filesystem-safe timestamp string."""
    return time.strftime("%Y%m%d_%H%M%S")


def list_cameras(max_index: int = 5) -> List[int]:
    """Return a list of available camera indices."""
    available: List[int] = []
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            available.append(idx)
        cap.release()
    return available


def export_blink_events_csv(path: str | Path, events: Sequence[dict]) -> Path:
    """Export blink events to CSV."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(["timestamp", "ear", "closed_duration_ms", "blink_type"])
        for event in events:
            writer.writerow(
                [
                    event.get("timestamp", ""),
                    event.get("ear", ""),
                    event.get("closed_duration_ms", ""),
                    event.get("blink_type", ""),
                ]
            )
    return p


def landmark_to_pixel(
    landmark: NormalizedLandmark, width: int, height: int
) -> Tuple[float, float]:
    """Convert a normalized landmark to pixel coordinates."""
    return (landmark.x * width, landmark.y * height)
