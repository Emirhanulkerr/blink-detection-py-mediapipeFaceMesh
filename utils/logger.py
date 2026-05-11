from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from core.signal_manager import SignalManager


class QtSignalHandler(logging.Handler):
    """Logging handler that forwards logs to a Qt signal."""

    def __init__(self, signal_manager: SignalManager) -> None:
        super().__init__()
        self._signal_manager = signal_manager

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        self._signal_manager.log_ready.emit(message)


def setup_logger(
    log_dir: str,
    level: str,
    signal_manager: Optional[SignalManager] = None,
) -> logging.Logger:
    """Configure console, file, and optional UI logging."""
    logger = logging.getLogger("blink_detection")
    logger.setLevel(level.upper())
    logger.handlers.clear()
    logger.propagate = False

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(log_dir) / "blink_detection.log"

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level.upper())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level.upper())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    if signal_manager is not None:
        qt_handler = QtSignalHandler(signal_manager)
        qt_handler.setFormatter(formatter)
        qt_handler.setLevel(level.upper())
        logger.addHandler(qt_handler)

    return logger
