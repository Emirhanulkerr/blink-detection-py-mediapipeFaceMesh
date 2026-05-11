from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class SignalManager(QObject):
    """Central signal hub for thread-safe UI updates."""

    frame_ready = pyqtSignal(object)
    metrics_ready = pyqtSignal(dict)
    status_ready = pyqtSignal(str)
    log_ready = pyqtSignal(str)
