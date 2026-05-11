import logging
import queue
import unittest

import cv2
import numpy as np

from core.camera_manager import CameraManager
from core.signal_manager import SignalManager
from utils.config import AppConfig


class DummyCapture:
    def __init__(self, opened: bool = True) -> None:
        self._opened = opened
        self.properties = {}

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        return True, np.zeros((10, 10, 3), dtype=np.uint8)

    def release(self) -> None:
        self._opened = False

    def set(self, prop_id: int, value) -> bool:
        self.properties[prop_id] = value
        return True


class CameraManagerTest(unittest.TestCase):
    def test_open_success(self) -> None:
        config = AppConfig()

        def factory(_index: int):
            return DummyCapture(opened=True)

        manager = CameraManager(
            config,
            queue.Queue(),
            SignalManager(),
            logging.getLogger("test"),
            capture_factory=factory,
        )
        self.assertTrue(manager.open())

    def test_open_failure(self) -> None:
        config = AppConfig()

        def factory(_index: int):
            return DummyCapture(opened=False)

        manager = CameraManager(
            config,
            queue.Queue(),
            SignalManager(),
            logging.getLogger("test"),
            capture_factory=factory,
        )
        self.assertFalse(manager.open())


if __name__ == "__main__":
    unittest.main()
