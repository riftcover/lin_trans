# coding:utf-8
import asyncio
import os
import platform
import sys

import httpx
from PySide6.QtCore import QUrl, QSettings
from PySide6.QtGui import QIcon, QDesktopServices, QColor, QFont
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
from utils import logger
from vendor.qfluentwidgets import FluentIcon as FIF, NavigationItemPosition
from vendor.qfluentwidgets import (MessageBox, FluentWindow, FluentBackgroundTheme, setThemeColor, )
from nice_ui.ui.profile import ProfileInterface
from vendor.qfluentwidgets import NavigationAvatarWidget
from api_client import api_client


class Window(FluentWindow):

    def __init__(self):
        super().__init__()
        # 获取当前工作目录
        current_directory = os.path.basename(os.getcwd())
        self.settings = QSettings("Locoweed3",  f"LinLInTrans_{current_directory}")
        # 设置主题颜色为蓝色
        setThemeColor(QColor("#0078d4"))
        
        # 根据操作系统设置字体
        self.set_font()
        
        # 添加登录状态管理
        self.is_logged_in = False
        self.login_window = None

        self.initWindow()
        # create sub interface
        # self.homeInterface = Widget('Search Interface', self)
        self.vide2srt = Video2SRT("音视频转字幕", self, self.settings)
        self.translate_srt = WorkSrt("字幕翻译", self, self.settings)
        self.my_story = TableApp("我的创作", self, self.settings)
        self.settingInterface = SettingInterface("设置", self, self.settings)
        self.loginInterface = ProfileInterface("个人中心", self, self.settings)

        self.initNavigation()
        # 尝试自动登录
        self.tryAutoLogin()

    def set_font(self):
        system = platform.system()
        font = QFont()
        if system == "Windows":
            font.setFamily("Microsoft YaHei")
        elif system == "Darwin":  # macOS
            font.setFamily("PingFang SC")
        else:  # 其他系统（如Linux）使用默认字体
            return

    def initNavigation(self):
        # self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')
        self.addSubInterface(self.vide2srt, FIF.VIDEO, "音视频转字幕")
        self.addSubInterface(self.translate_srt, FIF.BOOK_SHELF, "字幕翻译")
        self.addSubInterface(self.my_story, FIF.PALETTE, "我的创作")

        self.addSubInterface(self.settingInterface, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)

        # 创建头像按钮
        self.avatarWidget = NavigationAvatarWidget(
            '未登录',
            ':icon/assets/linlin.png'
        )
        
        # 添加个人中心到导航，使用头像作为按钮
        self.navigationInterface.addWidget(
            routeKey=self.loginInterface.objectName(),
            widget=self.avatarWidget,
            onClick=self.showLoginInterface,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 将个人中心页面添加到路由系统
        self.stackedWidget.addWidget(self.loginInterface)

    def initWindow(self):
        self.resize(MAIN_WINDOW_SIZE)
        self.setWindowIcon(QIcon(":icon/assets/linlin.png"))
        self.setWindowTitle("林林字幕")

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        # use custom background color theme (only available when the mica effect is disabled)
        self.setCustomBackgroundColor(*FluentBackgroundTheme.DEFAULT_BLUE)

        # 下面的是从spwin的initUI中复制过来的
        # 获取最后一次选择的目录
        config.last_opendir = self.settings.value("last_dir", config.last_opendir, str)
        get_setting_cache(self.settings)
        all_keys = (
            self.settings.allKeys()
        )  # self.settings.clear()  # for key in all_keys:  #     value = self.settings.value(key)  #     config.logger.info(f"Key: {key}, Value: {value}")

    def showMessageBox(self):
        w = MessageBox(
            "支持作者🥰",
            "个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀",
            self,
        )
        w.yesButton.setText("来啦老弟")
        w.cancelButton.setText("下次一定")

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
            response = await client.get(
                "https://api.github.com/repos/your_username/your_repo/releases/latest"
            )
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
            "更新可用", f"新版本 {latest_version} 已经可用。是否要现在更新？", self
        )
        dialog.yesButton.setText("更新")
        dialog.cancelButton.setText("稍后")

        if dialog.exec():
            QDesktopServices.openUrl(
                QUrl("https://github.com/your_username/your_repo/releases/latest")
            )

    def tryAutoLogin(self):
        """尝试自动登录"""
        try:
            # 尝试从设置加载token
            if api_client.load_token_from_settings(self.settings):
                try:
                    # 验证token是否有效
                    user_info = {
                        'email': self.settings.value('email', '已登录'),
                    }
                    
                    # 更新登录状态
                    self.is_logged_in = True
                    self.avatarWidget.setName(user_info['email'])
                    
                    # 更新个人中心页面
                    self.loginInterface.updateUserInfo(user_info)
                    self.get_history_sync.updateHistory()
                    logger.info("自动登录成功")
                except Exception as e:
                    logger.warning(f"Token验证失败: {e}")
                    # Token无效，清除状态
                    self.settings.remove('token')
                    self.settings.sync()
                    api_client.clear_token()
            else:
                logger.info("无保存的登录状态")
        except Exception as e:
            logger.error(f"自动登录过程出错: {e}")

    def showLoginInterface(self):
        if not self.is_logged_in:
            # 如果未登录，显示登录窗口
            if not self.login_window:
                from nice_ui.ui.login import LoginWindow
                self.login_window = LoginWindow(self, self.settings)
                self.login_window.loginSuccessful.connect(self.handleLoginSuccess)
            
            # 计算登录窗口在主窗口中的居中位置
            login_x = self.x() + (self.width() - self.login_window.width()) // 2
            login_y = self.y() + (self.height() - self.login_window.height()) // 2
            self.login_window.move(login_x, login_y)
            
            self.login_window.show()
        else:
            # 如果已登录，切换到个人中心页面
            self.switchTo(self.loginInterface)
            
    def handleLoginSuccess(self, user_info):
        """处理登录成功的回调"""
        self.is_logged_in = True
        self.avatarWidget.setName(user_info.get('email', '已登录'))
        # 可以设置用户头像
        # self.avatarWidget.setAvatar('path_to_avatar')
        self.login_window.hide()
        self.switchTo(self.loginInterface)
        # 更新个人中心页面的信息
        self.loginInterface.updateUserInfo(user_info)

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        try:
            # 清理API客户端资源
            if hasattr(self, 'is_logged_in') and self.is_logged_in:
                api_client.close_sync()
                logger.info("API client resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        # 调用父类的closeEvent
        super().closeEvent(event)


if __name__ == "__main__":
    def main():
        app = QApplication(sys.argv)
        # window = Video2SRT("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
        window = Window()
        window.show()
        sys.exit(app.exec())
    main()