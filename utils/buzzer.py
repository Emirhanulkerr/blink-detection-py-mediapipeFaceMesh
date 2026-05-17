from __future__ import annotations

import logging
import sys
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

NATURAL_BLINK_MAX_MS = 500
CONTINUOUS_ALARM_MS = 5000

BLINK_TYPE_NATURAL = "natural_blink"
BLINK_TYPE_PROLONGED = "prolonged_blink"


def classify_blink_type(closed_duration_ms: float) -> str:
    """Classify a completed blink by how long the eyes stayed closed."""
    if closed_duration_ms < NATURAL_BLINK_MAX_MS:
        return BLINK_TYPE_NATURAL
    return BLINK_TYPE_PROLONGED


def _beep(frequency: int, duration_ms: int) -> None:
    if sys.platform == "win32":
        import winsound

        winsound.Beep(frequency, duration_ms)
    else:
        print("\a", end="", flush=True)
        time.sleep(duration_ms / 1000.0)


class BuzzerController:
    """Play warning tones while eyes stay closed beyond normal blink duration."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._mode = "idle"
        self._lock = threading.Lock()

    def update(self, eyes_closed: bool, closed_duration_ms: float) -> None:
        """Drive alarm state from per-frame eye closure duration."""
        if not self._enabled:
            return

        if not eyes_closed:
            self.stop()
            return

        if closed_duration_ms >= CONTINUOUS_ALARM_MS:
            self._ensure_mode("continuous", self._continuous_alarm_loop)
        elif closed_duration_ms >= NATURAL_BLINK_MAX_MS:
            self._ensure_mode("warning", self._warning_alarm_loop)

    def stop(self) -> None:
        """Stop any active alarm immediately."""
        with self._lock:
            self._stop_event.set()
            thread = self._thread
            self._thread = None
            self._mode = "idle"

        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)

    def shutdown(self) -> None:
        """Stop alarms and disable further playback."""
        self._enabled = False
        self.stop()

    def _ensure_mode(self, mode: str, loop: Callable[[], None]) -> None:
        with self._lock:
            if self._mode == mode and self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.set()
            if self._thread is not None and self._thread.is_alive():
                old_thread = self._thread
            else:
                old_thread = None
            self._stop_event = threading.Event()
            self._mode = mode
            self._thread = threading.Thread(target=self._run_loop, args=(loop,), daemon=True)
            self._thread.start()

        if old_thread is not None and old_thread is not threading.current_thread():
            old_thread.join(timeout=1.0)

    def _run_loop(self, loop: Callable[[], None]) -> None:
        try:
            loop()
        except Exception:
            logger.exception("Buzzer alarm loop failed")

    def _warning_alarm_loop(self) -> None:
        """Three longer beeps with short gaps, repeated until stopped."""
        while not self._stop_event.is_set():
            for _ in range(3):
                if self._stop_event.is_set():
                    return
                _beep(880, 420)
                if self._stop_event.wait(0.18):
                    return
            if self._stop_event.wait(0.55):
                return

    def _continuous_alarm_loop(self) -> None:
        """Rapid longer beeps until eyes open."""
        while not self._stop_event.is_set():
            _beep(1100, 380)
            if self._stop_event.wait(0.12):
                return
            _beep(880, 380)
            if self._stop_event.wait(0.12):
                return
