"""
HWID Checker — entry point.

Usage:
    python main.py
"""
import sys
import os

# Ensure project root is on sys.path so all `core.*` / `ui.*` imports work.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HWID 9527")
    app.setOrganizationName("Lenovo ODM Tools")

    # Set a clean default font (compatible with Qt6 ≥ 6.4)
    font = QFont()
    for family in ["Inter", "Noto Sans", "Segoe UI", "Sans Serif"]:
        font.setFamily(family)
        if font.exactMatch():
            break
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
