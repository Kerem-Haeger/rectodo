"""
RecToDo entry point.
"""

import sys

from PySide6.QtWidgets import QApplication

from main_window import MainWindow
from theme import apply_theme, ThemeMode


def main():
    """Launch the RecToDo Qt application."""
    app = QApplication(sys.argv)
    apply_theme(app, ThemeMode.DARK)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
