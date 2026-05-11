import unittest

from core.blink_detector import BlinkDetector
from utils.config import AppConfig


class BlinkDetectorTest(unittest.TestCase):
    def test_compute_ear(self) -> None:
        p1 = (0.0, 0.0)
        p4 = (4.0, 0.0)
        p2 = (1.0, 1.0)
        p6 = (1.0, -1.0)
        p3 = (3.0, 1.0)
        p5 = (3.0, -1.0)
        ear = BlinkDetector.compute_ear(p1, p2, p3, p4, p5, p6)
        self.assertAlmostEqual(ear, 0.5, places=3)

    def test_blink_count(self) -> None:
        config = AppConfig(
            ear_threshold=0.2,
            min_consecutive_frames=2,
            blink_debounce_ms=0,
            dynamic_threshold=False,
        )
        detector = BlinkDetector(config)
        timestamp = 0.0
        for ear in [0.3, 0.1, 0.1, 0.3]:
            result = detector.process_ear(ear, ear, timestamp)
            timestamp += 0.05
        self.assertEqual(result.blink_count, 1)


if __name__ == "__main__":
    unittest.main()
