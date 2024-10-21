import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from nice_ui.ui.MainWindow import Window


def main():
    app = QApplication(sys.argv)
    # window = Video2SRT("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
