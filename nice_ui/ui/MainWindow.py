# coding:utf-8
import sys

from PySide6.QtCore import Qt, QUrl, QSettings
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import (NavigationItemPosition, MessageBox, FluentWindow,
                            NavigationAvatarWidget, SubtitleLabel, setFont, FluentBackgroundTheme)
from qfluentwidgets import FluentIcon as FIF
from nice_ui.ui.my_story import TableApp
from nice_ui.ui.video2srt import Video2SRT
from nice_ui.ui.work_srt import WorkSrt

from nice_ui.configure import config
from nice_ui.ui.SingalBridge import get_setting_cache


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(FluentWindow):

    def __init__(self):
        super().__init__()
        self.main_setting = QSettings("Locodol", "LinLInTrans")
        self.initWindow()
        # create sub interface
        self.homeInterface = Widget('Search Interface', self)
        self.vide2srt = Video2SRT('音视频转字幕', self,self.main_setting)
        self.translate_srt = WorkSrt('字幕翻译', self,self.main_setting)
        self.edit_srt = Widget('字幕编辑', self)
        self.my_story = TableApp('我的创作', self)


        self.settingInterface = Widget('我的设置', self)

        self.initNavigation()



    def initNavigation(self):

        self.addSubInterface(self.vide2srt, FIF.VIDEO, '音视频转字幕')
        self.addSubInterface(self.translate_srt, FIF.BOOK_SHELF, '字幕翻译')
        self.addSubInterface(self.edit_srt, FIF.EDIT, '字幕编辑')
        self.navigationInterface.addSeparator()
        self.addSubInterface(self.my_story, FIF.PALETTE, '我的创作')
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')


        # add custom widget to bottom
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=NavigationAvatarWidget('zhiyiYo', 'resource/shoko.png'),
            onClick=self.showMessageBox,
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

        # add badge to navigation item
        item = self.navigationInterface.widget(self.vide2srt.objectName())
        # InfoBadge.attension(
        #     text=9,
        #     parent=item.parent(),
        #     target=item,
        #     position=InfoBadgePosition.NAVIGATION_ITEM
        # )

        # NOTE: enable acrylic effect
        # self.navigationInterface.setAcrylicEnabled(True)

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets')

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        # use custom background color theme (only available when the mica effect is disabled)
        self.setCustomBackgroundColor(*FluentBackgroundTheme.DEFAULT_BLUE)


        #下面的是从spwin的initUI中复制过来的
        # 获取最后一次选择的目录
        config.last_opendir = self.main_setting.value("last_dir", config.last_opendir, str)
        get_setting_cache(self.main_setting)


    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://afdian.net/a/zhiyiYo"))



    # 存储本地数据



if __name__ == '__main__':
    # setTheme(Theme.DARK)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
