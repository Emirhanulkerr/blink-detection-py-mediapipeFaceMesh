# Automatic Blink Detection System

Production-ready, real-time blink detection using MediaPipe Face Mesh and a modern PyQt6 desktop UI.

## Requirements

- Python 3.10+
- A working webcam
- macOS, Windows, or Linux

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Configuration

All runtime settings are managed in `config.json`:

- `ear_threshold`
- `min_consecutive_frames`
- `camera_index`
- `target_fps`

## Project Structure

```
project_root/
├── main.py
├── requirements.txt
├── README.md
├── config.json
├── assets/
│   └── icons/
├── ui/
│   ├── main_window.py
│   ├── styles.py
│   └── widgets.py
├── core/
│   ├── camera_manager.py
│   ├── face_detector.py
│   ├── blink_detector.py
│   ├── fps_counter.py
│   ├── processing_worker.py
│   └── signal_manager.py
├── utils/
│   ├── config.py
│   ├── logger.py
│   ├── drawing_utils.py
│   └── helpers.py
├── data/
│   ├── logs/
│   └── screenshots/
└── tests/
    ├── test_blink_detector.py
    └── test_camera.py
```

## Algorithm Overview

1. Capture frames in a dedicated camera thread.
2. Run MediaPipe Face Mesh in a processing thread.
3. Extract eye landmarks and compute EAR for both eyes.
4. Apply blink logic with debounce and minimum closed frames.
5. Update the UI with metrics and overlay graphics.

## EAR Math

The Eye Aspect Ratio (EAR) is computed as:

```
EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
```

A blink starts when EAR drops below threshold and ends when it rises again.

## GUI Features

- Live camera preview with eye landmarks
- Blink count, FPS, and current EAR
- Dynamic threshold slider
- Session stats and CSV export
- Screenshot capture
- Log panel with file logging

## Logging

Logs are written to `data/logs/blink_detection.log` and to the console.

## Screenshots

Screenshots are saved in `data/screenshots` via the UI button.

## Troubleshooting

- **Camera not found**: Check `camera_index` in `config.json` and ensure no other app is using the webcam.
- **Low FPS**: Reduce `processing_width` and `processing_height` or lower `target_fps`.
- **No face detected**: Improve lighting and ensure the face is centered.
- **MediaPipe install issues**: Recreate the virtual environment and reinstall dependencies.

## Future Improvements

- GPU acceleration for Face Mesh
- Multi-face tracking
- Exportable session reports
- Remote streaming UI
