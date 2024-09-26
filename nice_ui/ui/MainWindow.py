# coding:utf-8
import asyncio
import sys

import httpx
from PySide6.QtCore import QUrl, QSettings
from PySide6.QtGui import QIcon, QDesktopServices, QColor
from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtWidgets import QApplication
from packaging import version

from nice_ui.configure import config
from nice_ui.configure.setting_cache import get_setting_cache
from nice_ui.ui import MAIN_WINDOW_SIZE
from nice_ui.ui.my_story import TableApp
from nice_ui.ui.setting_ui import SettingInterface
from nice_ui.ui.video2srt import Video2SRT
from nice_ui.ui.work_srt import WorkSrt
from vendor.qfluentwidgets import FluentIcon as FIF
from vendor.qfluentwidgets import (MessageBox, FluentWindow, FluentBackgroundTheme, setThemeColor)
from utils import logger
from components import lin_resource_rc

class Window(FluentWindow):

    def __init__(self):
        super().__init__()
        self.settings = QSettings("Locoweed", "LinLInTrans")
        # 设置主题颜色为蓝色
        setThemeColor(QColor("#0078d4"))  # 使用RGB值设置蓝色

        self.initWindow()
        self.load_proxy_settings()  # 加载代理设置
        # todo 更新检查更改地址
        # QTimer.singleShot(0, self.check_for_updates)  # 在主窗口初始化后检查更新
        # create sub interface
        # self.homeInterface = Widget('Search Interface', self)
        self.vide2srt = Video2SRT('音视频转字幕', self, self.settings)
        self.translate_srt = WorkSrt('字幕翻译', self, self.settings)
        self.my_story = TableApp('我的创作', self, self.settings)
        self.settingInterface = SettingInterface('设置', self, self.settings)

        self.initNavigation()

    def initNavigation(self):
        # self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')
        self.addSubInterface(self.vide2srt, FIF.VIDEO, '音视频转字幕')
        self.addSubInterface(self.translate_srt, FIF.BOOK_SHELF, '字幕翻译')
        self.addSubInterface(self.my_story, FIF.PALETTE, '我的创作')

        self.addSubInterface(self.settingInterface, FIF.SETTING, '设置')

        # add badge to navigation item
        # self.navigationInterface.addSeparator()
        # self.navigationInterface.addWidget(routeKey='avatar', widget=NavigationAvatarWidget('zhiyiYo', 'resource/shoko.png'), onClick=self.showMessageBox,
        #                                    position=NavigationItemPosition.BOTTOM, )
        # self.navigationInterface.widget(self.vide2srt.objectName())

    def initWindow(self):
        self.resize(MAIN_WINDOW_SIZE)
        self.setWindowIcon(QIcon(':icon/assets/linlin.png'))
        self.setWindowTitle('林林字幕')

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        # use custom background color theme (only available when the mica effect is disabled)
        self.setCustomBackgroundColor(*FluentBackgroundTheme.DEFAULT_BLUE)

        # 下面的是从spwin的initUI中复制过来的
        # 获取最后一次选择的目录
        config.last_opendir = self.settings.value("last_dir", config.last_opendir, str)
        get_setting_cache(self.settings)
        all_keys = self.settings.allKeys()  # self.settings.clear()  # for key in all_keys:  #     value = self.settings.value(key)  #     config.logger.info(f"Key: {key}, Value: {value}")

    def showMessageBox(self):
        w = MessageBox('支持作者🥰', '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀', self)
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://afdian.net/a/zhiyiYo"))

    def load_proxy_settings(self):
        if self.settings.value("use_proxy", False, type=bool):
            proxy_type = self.settings.value("proxy_type", "http", type=str)
            host = self.settings.value("proxy_host", "", type=str)
            port = self.settings.value("proxy_port", 7890, type=int)

            proxy_obj = QNetworkProxy()
            if proxy_type.lower() == "http":
                proxy_obj.setType(QNetworkProxy.HttpProxy)
            else:
                proxy_obj.setType(QNetworkProxy.Socks5Proxy)

            proxy_obj.setHostName(host)
            proxy_obj.setPort(port)
            QNetworkProxy.setApplicationProxy(proxy_obj)
            logger.info(f"程序启动时设置代理: {proxy_obj}")
        else:
            QNetworkProxy.setApplicationProxy(QNetworkProxy.NoProxy)
            logger.info("程序启动时禁用代理")

    async def fetch_latest_version(self):
        async with httpx.AsyncClient() as client:
            # todo 更新检查更改地址
            response = await client.get("https://api.github.com/repos/your_username/your_repo/releases/latest")
            response.raise_for_status()
            return response.json()["tag_name"]

    def check_for_updates(self):
        current_version = "1.0.0"  # Replace with your current version
        try:
            loop = asyncio.get_event_loop()
            latest_version = loop.run_until_complete(self.fetch_latest_version())
            if version.parse(latest_version) > version.parse(current_version):
                self.show_update_dialog(latest_version)
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

    def show_update_dialog(self, latest_version):
        dialog = MessageBox(
            "更新可用",
            f"新版本 {latest_version} 已经可用。是否要现在更新？",
            self
        )
        dialog.yesButton.setText("更新")
        dialog.cancelButton.setText("稍后")

        if dialog.exec():
            QDesktopServices.openUrl(QUrl("https://github.com/your_username/your_repo/releases/latest"))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec()
