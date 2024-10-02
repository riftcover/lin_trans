import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from nice_ui.ui.video2srt import Video2SRT

def main():
    app = QApplication(sys.argv)
    window = Video2SRT("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()