# coding: utf-8
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from qfluentwidgets import setTheme, Theme

from vendor.qfluentwidgets.multimedia import SimpleMediaPlayBar, LinVideoWidget
from nice_ui.configure import config

class Demo1(QWidget):

    def __init__(self):
        super().__init__()
        setTheme(Theme.DARK)
        self.vBoxLayout = QVBoxLayout(self)
        self.resize(500, 300)

        # self.player = QMediaPlayer(self)
        # self.player.setMedia(QUrl.fromLocalFile(filename))
        # self.player.setPosition()

        self.simplePlayBar = SimpleMediaPlayBar(self)
        # self.standardPlayBar = StandardMediaPlayBar(self)

        self.vBoxLayout.addWidget(self.simplePlayBar)
        # self.vBoxLayout.addWidget(self.standardPlayBar)

        # online music
        url = QUrl('/Users/locodol/my_own/code/lin_trans/result/tt1/vv2.mp4')
        self.simplePlayBar.player.setSource(url)

        # local music
        # url = QUrl.fromLocalFile(str(Path('resource/aiko - シアワセ.mp3').absolute()))
        # self.standardPlayBar.player.setSource(url)

        # self.standardPlayBar.play()


class Demo2(QWidget):

    def __init__(self):
        super().__init__()
        self.vBoxLayout = QVBoxLayout(self)
        self.videoWidget = LinVideoWidget()
        # self.videoWidget = VideoWidget()

        self.videoWidget.setVideo(QUrl(
            'D:/dcode/lin_trans/result/tt1/tt.mp4'))
        # self.videoWidget.play()
        # self.videoWidget.setSrtFile('D:/dcode/lin_trans/result/tt1/tt.srt')
        # self.videoWidget.setSrtFile('D:/dcode/lin_trans/result/tt1/dd.srt')

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.videoWidget)
        # self.resize(634, 412)
        video_size_x,video_size_y = 1920/3, 1080/3
        config.logger.debug(f"Video size: {video_size_x}x{video_size_y}")
        self.resize(video_size_x, video_size_y+40)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        config.logger.debug(f"Window size: {self.size()}")


if __name__ == '__main__':
    app = QApplication([])
    # demo1 = Demo1()
    # demo1.show()
    demo2 = Demo2()
    demo2.show()
    sys.exit(app.exec())