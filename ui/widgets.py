from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtCore import QLineF
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QVBoxLayout, QWidget


class StatCard(QFrame):
    """Simple card widget for a single metric."""

    def __init__(self, title: str, value: str = "0") -> None:
        super().__init__()
        self.setObjectName("Card")

        self._title_label = QLabel(title)
        self._title_label.setObjectName("SubtleLabel")
        self._value_label = QLabel(value)
        self._value_label.setObjectName("CardValue")

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.setText(value)


class LogPanel(QPlainTextEdit):
    """Scrollable log panel that appends text safely."""

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)

    def append_line(self, text: str) -> None:
        self.appendPlainText(text)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class EarGraphWidget(QWidget):
    """Lightweight EAR line chart widget."""

    def __init__(self) -> None:
        super().__init__()
        self._values: List[float] = []
        self._threshold: float = 0.0
        self.setMinimumHeight(120)

    def update_values(self, values: List[float], threshold: float) -> None:
        self._values = values[-200:]
        self._threshold = threshold
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(8, 8, -8, -8)
        painter.fillRect(rect, QColor(20, 25, 32))

        if not self._values:
            return

        min_val = min(min(self._values), 0.1)
        max_val = max(max(self._values), 0.5)
        span = max(max_val - min_val, 0.001)

        step = rect.width() / max(1, len(self._values) - 1)
        points = []
        for idx, value in enumerate(self._values):
            x = rect.left() + (idx * step)
            norm = (value - min_val) / span
            y = rect.bottom() - (norm * rect.height())
            points.append(QPointF(x, y))

        painter.setPen(QPen(QColor(61, 162, 146), 2))
        painter.drawPolyline(QPolygonF(points))

        if self._threshold > 0:
            thresh_norm = (self._threshold - min_val) / span
            thresh_y = rect.bottom() - (thresh_norm * rect.height())
            painter.setPen(QPen(QColor(235, 112, 89), 1, Qt.PenStyle.DashLine))
            painter.drawLine(
                QLineF(float(rect.left()), float(thresh_y), float(rect.right()), float(thresh_y))
            )
