from __future__ import annotations

import time


class FPSCounter:
    """Smoothed FPS counter for real-time processing."""

    def __init__(self, smoothing: float = 0.9) -> None:
        self._smoothing = smoothing
        self._last_time: float | None = None
        self._fps: float = 0.0

    def update(self) -> float:
        """Update internal FPS estimate and return the smoothed FPS."""
        now = time.perf_counter()
        if self._last_time is None:
            self._last_time = now
            return 0.0

        delta = now - self._last_time
        self._last_time = now
        if delta <= 0:
            return self._fps

        instant = 1.0 / delta
        if self._fps <= 0.0:
            self._fps = instant
        else:
            self._fps = (self._fps * self._smoothing) + (instant * (1.0 - self._smoothing))

        return self._fps

    @property
    def value(self) -> float:
        """Return the latest FPS value."""
        return self._fps
