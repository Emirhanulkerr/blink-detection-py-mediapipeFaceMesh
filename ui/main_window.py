from __future__ import annotations

import queue
from typing import Optional

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.camera_manager import CameraManager
from core.processing_worker import FrameResult, ProcessingWorker
from core.signal_manager import SignalManager
from ui.styles import dark_theme, light_theme
from ui.widgets import EarGraphWidget, LogPanel, StatCard
from utils.config import AppConfig
from utils import helpers


class MainWindow(QMainWindow):
    """Main application window and UI controller."""

    def __init__(
        self,
        config: AppConfig,
        camera_manager: CameraManager,
        processor: ProcessingWorker,
        result_queue: queue.Queue,
        signal_manager: SignalManager,
        logger,
    ) -> None:
        super().__init__()
        self._config = config
        self._camera_manager = camera_manager
        self._processor = processor
        self._result_queue = result_queue
        self._signal_manager = signal_manager
        self._logger = logger

        self._current_frame: Optional[np.ndarray] = None
        self._is_dark = True

        self.setWindowTitle("Automatic Blink Detection System")
        self.setMinimumSize(1200, 720)

        self._build_ui()
        self._apply_theme()
        self._connect_signals()

        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._drain_results)
        self._ui_timer.start(16)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.stop_system()
        event.accept()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        header_layout = QHBoxLayout()

        title = QLabel("Automatic Blink Detection System")
        title.setObjectName("TitleLabel")
        header_layout.addWidget(title)
        header_layout.addStretch(1)

        self._top_start_button = QPushButton("Start")
        self._top_stop_button = QPushButton("Stop")
        self._top_reconnect_button = QPushButton("Refresh Camera")
        self._top_stop_button.setEnabled(False)
        header_layout.addWidget(self._top_start_button)
        header_layout.addWidget(self._top_stop_button)
        header_layout.addWidget(self._top_reconnect_button)

        self._theme_toggle = QCheckBox("Light theme")
        self._theme_toggle.setChecked(False)
        header_layout.addWidget(self._theme_toggle)

        main_layout.addLayout(header_layout)

        body_layout = QHBoxLayout()
        main_layout.addLayout(body_layout, stretch=1)

        self._video_label = QLabel()
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setMinimumSize(640, 360)
        self._video_label.setStyleSheet("background-color: #0b0f14; border-radius: 12px;")

        self._ear_graph = EarGraphWidget()

        video_card = QFrame()
        video_card.setObjectName("Card")
        video_layout = QVBoxLayout(video_card)
        video_layout.addWidget(self._video_label, stretch=1)
        video_layout.addWidget(self._ear_graph)

        body_layout.addWidget(video_card, stretch=3)

        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)

        stats_grid = QGridLayout()
        self._blink_card = StatCard("Blink Count", "0")
        self._fps_card = StatCard("FPS", "0.0")
        self._ear_card = StatCard("Current EAR", "0.000")
        stats_grid.addWidget(self._blink_card, 0, 0)
        stats_grid.addWidget(self._fps_card, 0, 1)
        stats_grid.addWidget(self._ear_card, 1, 0, 1, 2)
        side_layout.addLayout(stats_grid)

        status_card = QFrame()
        status_card.setObjectName("Card")
        status_layout = QVBoxLayout(status_card)
        status_label = QLabel("Camera Status")
        status_label.setObjectName("SubtleLabel")
        self._camera_status_value = QLabel("Idle")
        self._camera_status_value.setObjectName("CardValue")
        self._camera_combo = QComboBox()
        self._reconnect_button = QPushButton("Refresh Camera")
        self._populate_camera_list()
        status_layout.addWidget(status_label)
        status_layout.addWidget(self._camera_status_value)
        camera_row = QHBoxLayout()
        camera_row.addWidget(self._camera_combo, stretch=1)
        camera_row.addWidget(self._reconnect_button)
        status_layout.addLayout(camera_row)
        side_layout.addWidget(status_card)

        threshold_card = QFrame()
        threshold_card.setObjectName("Card")
        threshold_layout = QVBoxLayout(threshold_card)
        threshold_title = QLabel("EAR Threshold")
        threshold_title.setObjectName("SubtleLabel")
        self._threshold_value = QLabel(f"{self._config.ear_threshold:.2f}")
        self._threshold_value.setObjectName("CardValue")
        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setMinimum(10)
        self._threshold_slider.setMaximum(40)
        self._threshold_slider.setValue(int(self._config.ear_threshold * 100))
        threshold_layout.addWidget(threshold_title)
        threshold_layout.addWidget(self._threshold_value)
        threshold_layout.addWidget(self._threshold_slider)
        side_layout.addWidget(threshold_card)

        controls_card = QFrame()
        controls_card.setObjectName("Card")
        controls_layout = QVBoxLayout(controls_card)
        self._start_button = QPushButton("Start")
        self._stop_button = QPushButton("Stop")
        self._reset_button = QPushButton("Reset Counter")
        self._screenshot_button = QPushButton("Screenshot")
        self._export_button = QPushButton("Export CSV")
        self._stop_button.setEnabled(False)
        controls_layout.addWidget(self._start_button)
        controls_layout.addWidget(self._stop_button)
        controls_layout.addWidget(self._reset_button)
        controls_layout.addWidget(self._screenshot_button)
        controls_layout.addWidget(self._export_button)
        side_layout.addWidget(controls_card)

        log_card = QFrame()
        log_card.setObjectName("Card")
        log_layout = QVBoxLayout(log_card)
        log_label = QLabel("Log Panel")
        log_label.setObjectName("SubtleLabel")
        self._log_panel = LogPanel()
        log_layout.addWidget(log_label)
        log_layout.addWidget(self._log_panel)
        side_layout.addWidget(log_card, stretch=1)

        body_layout.addWidget(side_panel, stretch=2)

    def _connect_signals(self) -> None:
        self._start_button.clicked.connect(self.start_system)
        self._stop_button.clicked.connect(self.stop_system)
        self._reconnect_button.clicked.connect(self.reconnect_camera)
        self._top_start_button.clicked.connect(self.start_system)
        self._top_stop_button.clicked.connect(self.stop_system)
        self._top_reconnect_button.clicked.connect(self.reconnect_camera)
        self._reset_button.clicked.connect(self.reset_counter)
        self._screenshot_button.clicked.connect(self.take_screenshot)
        self._export_button.clicked.connect(self.export_csv)
        self._threshold_slider.valueChanged.connect(self._update_threshold)
        self._theme_toggle.stateChanged.connect(self._toggle_theme)
        self._camera_combo.currentIndexChanged.connect(self._change_camera)

        self._signal_manager.log_ready.connect(self._log_panel.append_line)
        self._signal_manager.status_ready.connect(self._camera_status_value.setText)

    def _apply_theme(self) -> None:
        self.setStyleSheet(dark_theme() if self._is_dark else light_theme())

    def _toggle_theme(self) -> None:
        self._is_dark = not self._theme_toggle.isChecked()
        self._apply_theme()

    def _populate_camera_list(self) -> None:
        self._camera_combo.clear()
        available = helpers.list_cameras(6)
        if not available:
            available = list(range(2))
        for idx in available:
            self._camera_combo.addItem(f"Camera {idx}", idx)
        current_index = available.index(self._config.camera_index) if self._config.camera_index in available else 0
        self._camera_combo.setCurrentIndex(current_index)

    def _change_camera(self) -> None:
        index = int(self._camera_combo.currentData())
        was_running = self._camera_manager.is_running
        if was_running:
            self.stop_system()
        self._camera_manager.set_camera_index(index)
        if was_running:
            self.start_system()

    def _update_threshold(self, value: int) -> None:
        threshold = value / 100.0
        self._threshold_value.setText(f"{threshold:.2f}")
        self._processor.set_threshold(threshold)

    def _drain_results(self) -> None:
        last_result: Optional[FrameResult] = None
        while True:
            try:
                last_result = self._result_queue.get_nowait()
            except queue.Empty:
                break

        if last_result is None:
            return

        self._update_video(last_result.frame)
        self._update_metrics(last_result)

    def _update_video(self, frame: np.ndarray) -> None:
        self._current_frame = frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = frame_rgb.shape
        bytes_per_line = channels * width
        image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image.copy())
        self._video_label.setPixmap(pixmap)

    def _update_metrics(self, result: FrameResult) -> None:
        metrics = result.metrics
        self._blink_card.set_value(str(metrics.get("blink_count", 0)))
        self._fps_card.set_value(f"{metrics.get('fps', 0.0):.1f}")
        self._ear_card.set_value(f"{metrics.get('ear', 0.0):.3f}")
        self._ear_graph.update_values(result.ear_history, metrics.get("threshold", 0.0))

    def start_system(self) -> None:
        if self._camera_manager.is_running and self._processor.is_running:
            return
        self._camera_manager.start()
        self._processor.start()
        self._start_button.setEnabled(False)
        self._stop_button.setEnabled(True)
        self._top_start_button.setEnabled(False)
        self._top_stop_button.setEnabled(True)
        self._logger.info("System started")

    def stop_system(self) -> None:
        if self._camera_manager.is_running:
            self._camera_manager.stop()
        if self._processor.is_running:
            self._processor.stop()
        self._start_button.setEnabled(True)
        self._stop_button.setEnabled(False)
        self._top_start_button.setEnabled(True)
        self._top_stop_button.setEnabled(False)

        stats = self._processor.get_session_stats()
        self._logger.info(
            "Session stats | duration=%.1fs blinks=%s rate=%.2f/min",
            stats.get("duration_sec", 0.0),
            stats.get("blink_count", 0),
            stats.get("blink_rate", 0.0),
        )

    def reconnect_camera(self) -> None:
        self._camera_manager.reconnect()
        self._logger.info("Camera reconnect requested")

    def reset_counter(self) -> None:
        self._processor.reset()
        self._blink_card.set_value("0")
        self._ear_card.set_value("0.000")
        self._logger.info("Blink counter reset")

    def take_screenshot(self) -> None:
        if self._current_frame is None:
            self._logger.warning("No frame available for screenshot")
            return
        directory = helpers.ensure_dir(self._config.screenshot_dir)
        filename = directory / f"screenshot_{helpers.timestamp_str()}.png"
        cv2.imwrite(str(filename), self._current_frame)
        self._logger.info("Screenshot saved: %s", filename)

    def export_csv(self) -> None:
        events = self._processor.get_blink_events()
        if not events:
            self._logger.warning("No blink events to export")
            return
        directory = helpers.ensure_dir(self._config.csv_export_dir)
        filename = directory / f"blink_events_{helpers.timestamp_str()}.csv"
        helpers.export_blink_events_csv(filename, events)
        self._logger.info("CSV exported: %s", filename)
