import sys
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