from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.json"


@dataclass
class AppConfig:
    """Application configuration loaded from JSON."""

    ear_threshold: float = 0.23
    min_consecutive_frames: int = 3
    camera_index: int = 0
    target_fps: int = 30
    frame_width: int = 640
    frame_height: int = 480
    processing_width: int = 640
    processing_height: int = 480
    dynamic_threshold: bool = True
    dynamic_ratio: float = 0.75
    blink_debounce_ms: int = 200
    ear_history_size: int = 180
    frame_queue_size: int = 4
    result_queue_size: int = 2
    min_detection_confidence: float = 0.6
    min_tracking_confidence: float = 0.6
    max_faces: int = 1
    reconnect_interval_sec: float = 2.0
    landmark_stale_frames: int = 5
    draw_landmarks: bool = True
    log_level: str = "INFO"
    log_dir: str = "data/logs"
    screenshot_dir: str = "data/screenshots"
    csv_export_dir: str = "data/logs"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AppConfig":
        """Create AppConfig from a dict, ignoring unknown keys."""
        config = AppConfig()
        for field in fields(AppConfig):
            if field.name in data:
                setattr(config, field.name, data[field.name])
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Return config as a serializable dict."""
        return asdict(self)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from disk, or write defaults if missing."""
    path = config_path or CONFIG_PATH
    if not path.exists():
        config = AppConfig()
        save_config(config, path)
        return config

    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return AppConfig()

    return AppConfig.from_dict(data)


def save_config(config: AppConfig, config_path: Optional[Path] = None) -> None:
    """Persist configuration to disk."""
    path = config_path or CONFIG_PATH
    path.write_text(json.dumps(config.to_dict(), indent=2))
