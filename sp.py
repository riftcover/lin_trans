# -*- coding: utf-8 -*-
import sys, os
from pathlib import Path
import time

from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPixmap, QPalette, QBrush, QIcon, QGuiApplication
from videotrans import VERSION




os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


class StartWindow(QtWidgets.QWidget):
    def __init__(self):
        super(StartWindow, self).__init__()
        QTimer.singleShot(200, self.run)

    def run(self):
        # 创建并显示窗口B
        # try:

        if not Path("./nostyle.txt").exists():
            import videotrans.ui.dark.darkstyle_rc
            with open('./videotrans/styles/style.qss', 'r', encoding='utf-8') as f:
                app.setStyleSheet(f.read())

        st = time.time()
        from videotrans.mainwin.spwin import MainWindow
        MainWindow()
        Path(Path.cwd() / "tmp").mkdir(parents=True, exist_ok=True)
        et = time.time()
        print(f'启动用时：{et - st}')
        self.close()
        # except Exception as e:
        #     print(e)
        #     print(f'main window {str(e)}')

    def center(self):
        screen = QGuiApplication.primaryScreen()
        screen_resolution = screen.geometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()
        self.move(QPoint(int((self.width - 560) / 2), int((self.height - 350) / 2)))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    try:
        startwin = StartWindow()
    except Exception as e:
        print(f"error:{str(e)}")
    sys.exit(app.exec())
