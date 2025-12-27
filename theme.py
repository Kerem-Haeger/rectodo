from enum import Enum

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"


def apply_theme(app: QApplication, mode: ThemeMode) -> None:
    """
    Apply a light or dark theme to the whole app.
    This ignores the OS theme to keep the contrast obvious.
    """
    app.setStyle("Fusion")

    palette = QPalette()

    if mode == ThemeMode.DARK:
        # Dark greys + light text
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(230, 230, 230))
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, QColor(230, 230, 230))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    else:
        # Proper light theme: white bg, dark text
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(233, 233, 233))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.Button, QColor(233, 233, 233))
        palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    app.setPalette(palette)
