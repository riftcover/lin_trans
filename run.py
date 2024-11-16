import sys

import multiprocessing

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from nice_ui.ui.MainWindow import Window
from nice_ui.ui.video2srt import Video2SRT


def main():
    app = QApplication(sys.argv)
    # window = Video2SRT("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
