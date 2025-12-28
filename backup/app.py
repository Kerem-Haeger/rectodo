"""
RecToDo - Recruitment Pipeline Management Application

Entry point for the application.
"""

import sys
from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from theme import apply_theme, ThemeMode


def main():
    """
    Main entry point for the RecToDo application.
    """
    app = QApplication(sys.argv)

    # Default theme: dark
    apply_theme(app, ThemeMode.DARK)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
