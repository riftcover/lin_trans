import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from nice_ui.ui.MainWindow import Window


def start():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())