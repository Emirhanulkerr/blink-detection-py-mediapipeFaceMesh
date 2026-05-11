from __future__ import annotations


def dark_theme() -> str:
    """Return the dark theme stylesheet."""
    return """
    QMainWindow {
        background-color: #0b0f14;
        color: #e8eef5;
    }
    * {
        font-family: "Montserrat", "Source Sans 3", "Sans Serif";
        font-size: 13px;
    }
    QLabel#TitleLabel {
        font-size: 20px;
        font-weight: 600;
    }
    QLabel#SubtleLabel {
        color: #9aa4b2;
    }
    QLabel#CardValue {
        font-size: 22px;
        font-weight: 600;
        color: #e6f0ff;
    }
    QFrame#Card {
        background-color: #151a21;
        border: 1px solid #202734;
        border-radius: 14px;
    }
    QFrame#Card:hover {
        border: 1px solid #2f3b4f;
    }
    QPushButton {
        background-color: #2d8a7c;
        color: #f3f7fb;
        border-radius: 10px;
        padding: 8px 12px;
    }
    QPushButton:hover {
        background-color: #3aa392;
    }
    QPushButton:pressed {
        background-color: #27746a;
    }
    QPushButton:disabled {
        background-color: #2a2f3a;
        color: #7a8594;
    }
    QSlider::groove:horizontal {
        height: 6px;
        background: #202734;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        width: 16px;
        margin: -5px 0;
        background: #3aa392;
        border-radius: 8px;
    }
    QPlainTextEdit {
        background-color: #0f141b;
        border: 1px solid #202734;
        border-radius: 10px;
        padding: 6px;
    }
    QComboBox {
        background-color: #11161f;
        border: 1px solid #202734;
        border-radius: 8px;
        padding: 4px 8px;
    }
    QCheckBox {
        spacing: 8px;
    }
    """


def light_theme() -> str:
    """Return the light theme stylesheet."""
    return """
    QMainWindow {
        background-color: #f6f8fb;
        color: #1a1f2b;
    }
    * {
        font-family: "Montserrat", "Source Sans 3", "Sans Serif";
        font-size: 13px;
    }
    QLabel#TitleLabel {
        font-size: 20px;
        font-weight: 600;
    }
    QLabel#SubtleLabel {
        color: #5b667a;
    }
    QLabel#CardValue {
        font-size: 22px;
        font-weight: 600;
        color: #152235;
    }
    QFrame#Card {
        background-color: #ffffff;
        border: 1px solid #d8e0ea;
        border-radius: 14px;
    }
    QFrame#Card:hover {
        border: 1px solid #b8c3d1;
    }
    QPushButton {
        background-color: #1a7f6a;
        color: #ffffff;
        border-radius: 10px;
        padding: 8px 12px;
    }
    QPushButton:hover {
        background-color: #239a81;
    }
    QPushButton:pressed {
        background-color: #146252;
    }
    QPushButton:disabled {
        background-color: #d7dce5;
        color: #8b96a6;
    }
    QSlider::groove:horizontal {
        height: 6px;
        background: #d8e0ea;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        width: 16px;
        margin: -5px 0;
        background: #239a81;
        border-radius: 8px;
    }
    QPlainTextEdit {
        background-color: #ffffff;
        border: 1px solid #d8e0ea;
        border-radius: 10px;
        padding: 6px;
    }
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #d8e0ea;
        border-radius: 8px;
        padding: 4px 8px;
    }
    QCheckBox {
        spacing: 8px;
    }
    """
