from __future__ import annotations

import queue
import sys

from PyQt6.QtWidgets import QApplication

from core.blink_detector import BlinkDetector
from core.camera_manager import CameraManager
from core.face_detector import FaceDetector
from core.fps_counter import FPSCounter
from core.processing_worker import ProcessingWorker
from core.signal_manager import SignalManager
from ui.main_window import MainWindow
from utils.config import load_config
from utils.logger import setup_logger


def main() -> None:
    """Application entrypoint."""
    config = load_config()
    signal_manager = SignalManager()
    logger = setup_logger(config.log_dir, config.log_level, signal_manager)

    frame_queue: queue.Queue = queue.Queue(maxsize=config.frame_queue_size)
    result_queue: queue.Queue = queue.Queue(maxsize=config.result_queue_size)

    camera_manager = CameraManager(config, frame_queue, signal_manager, logger)
    face_detector = FaceDetector(config, logger)
    blink_detector = BlinkDetector(config)
    fps_counter = FPSCounter()

    processor = ProcessingWorker(
        config=config,
        frame_queue=frame_queue,
        result_queue=result_queue,
        face_detector=face_detector,
        blink_detector=blink_detector,
        fps_counter=fps_counter,
        signal_manager=signal_manager,
        logger=logger,
    )

    app = QApplication(sys.argv)
    window = MainWindow(
        config=config,
        camera_manager=camera_manager,
        processor=processor,
        result_queue=result_queue,
        signal_manager=signal_manager,
        logger=logger,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
