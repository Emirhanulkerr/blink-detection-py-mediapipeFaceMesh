import unittest

from utils.buzzer import (
    BLINK_TYPE_NATURAL,
    BLINK_TYPE_PROLONGED,
    NATURAL_BLINK_MAX_MS,
    classify_blink_type,
)


class BuzzerUtilTest(unittest.TestCase):
    def test_classify_natural_blink(self) -> None:
        self.assertEqual(classify_blink_type(0), BLINK_TYPE_NATURAL)
        self.assertEqual(classify_blink_type(NATURAL_BLINK_MAX_MS - 1), BLINK_TYPE_NATURAL)

    def test_classify_prolonged_blink(self) -> None:
        self.assertEqual(classify_blink_type(NATURAL_BLINK_MAX_MS), BLINK_TYPE_PROLONGED)
        self.assertEqual(classify_blink_type(1200), BLINK_TYPE_PROLONGED)


if __name__ == "__main__":
    unittest.main()
