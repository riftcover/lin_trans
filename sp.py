# -*- coding: utf-8 -*-
import os
import sys
import time
from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtCore import QTimer, QPoint
from PySide6.QtGui import QGuiApplication

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
extra = {

    # Button colors
    'danger': '#dc3545',
    'warning': '#ffc107',
    'success': '#17a2b8',

    # Font
    'font_family': 'monoespace',
    'font_size': '13px',
    'line_height': '13px',
}

class StartWindow(QtWidgets.QWidget):
    def __init__(self):
        super(StartWindow, self).__init__()
        QTimer.singleShot(200, self.run)

    def run(self):
        # 创建并显示窗口B
        # try:

        # if not Path("./nostyle.txt").exists():
        #
        #     with open('./videotrans/styles/style.qss', 'r', encoding='utf-8') as f:
        #         app.setStyleSheet(f.read())
        # apply_stylesheet(app, theme='light_blue.xml', extra=extra)
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
