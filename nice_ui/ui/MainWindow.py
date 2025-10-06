# coding:utf-8
import asyncio
import platform
import sys
from pathlib import Path

import httpx
from PySide6.QtCore import QUrl, Qt, Slot, QTimer
from PySide6.QtGui import QIcon, QDesktopServices, QColor, QFont
from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtWidgets import QApplication
from packaging import version

from app.core.api_client import api_client, AuthenticationError
from nice_ui.services.api_service import api_service
from nice_ui.services.token_refresh_service import get_token_refresh_service
from nice_ui.services.simple_api_service import simple_api_service
from nice_ui.configure import config
from nice_ui.configure.setting_cache import get_setting_cache
from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
from nice_ui.ui import MAIN_WINDOW_SIZE, SettingsManager

# bug: TableApp 大量导入导致启动程序耗时久
from nice_ui.ui.my_story import TableApp
from nice_ui.ui.profile import ProfileInterface
from nice_ui.ui.setting_ui import SettingInterface
from nice_ui.ui.video2srt import Video2SRT
from nice_ui.ui.work_srt import WorkSrt
from utils import logger
from vendor.qfluentwidgets import FluentIcon as FIF, NavigationItemPosition
from vendor.qfluentwidgets import (MessageBox, FluentWindow, MacFluentWindow, FluentBackgroundTheme, setThemeColor, )
from vendor.qfluentwidgets import NavigationAvatarWidget, InfoBar, InfoBarPosition


# 智能选择窗口类型
def _create_smart_window_class():
    """根据平台智能选择窗口类型"""
    if sys.platform == "darwin":
        # macOS使用原生标题栏版本
        return MacFluentWindow
    else:
        # 其他平台使用标准版本
        return FluentWindow


class Window(_create_smart_window_class()):

    def __init__(self):
        super().__init__()
        # 设置对象名称，以便其他组件可以找到主窗口
        self.setObjectName("MainWindow")

        # 获取当前工作目录
        current_directory = Path.cwd().name
        self.settings = SettingsManager.get_instance()
        setThemeColor(QColor("#7C3AED"))

        # 根据操作系统设置字体
        self.set_font()

        # 添加登录状态管理
        self.is_logged_in = False
        self.login_window = None

        # 初始化服务提供者
        self.service_provider = ServiceProvider()
        self.auth_service = self.service_provider.get_auth_service()
        self.ui_manager = self.service_provider.get_ui_manager()

        # 初始化token刷新服务
        self.token_refresh_service = get_token_refresh_service()
        self._setup_token_refresh_signals()

        # 平台特定的窗口设置
        # self._setupPlatformSpecificFeatures()

        self.initWindow()
        # create sub interface
        # self.homeInterface = Widget('Search Interface', self)
        self.vide2srt = Video2SRT("音视频转字幕", self, self.settings)
        self.translate_srt = WorkSrt("字幕翻译", self, self.settings)
        self.my_story = TableApp("我的创作", self, self.settings)
        self.settingInterface = SettingInterface("设置", self, self.settings)
        self.loginInterface = ProfileInterface("个人中心", self, self.settings)

        self.initNavigation()
        # 连接信号
        self._connect_signals()
        # 尝试自动登录
        self.tryAutoLogin()

    def _setup_token_refresh_signals(self):
        """设置token刷新服务的信号连接"""
        self.token_refresh_service.token_refreshed.connect(self._on_token_refreshed)
        self.token_refresh_service.refresh_failed.connect(self._on_token_refresh_failed)

    def _on_token_refreshed(self, token_info):
        """处理token刷新成功"""
        logger.info("Token已自动刷新")

        # 更新设置中的token信息
        self.settings.setValue('token', token_info.get('access_token'))
        if token_info.get('refresh_token'):
            self.settings.setValue('refresh_token', token_info.get('refresh_token'))
        if token_info.get('expires_at'):
            self.settings.setValue('token_expires_at', token_info.get('expires_at'))
        self.settings.sync()

    def _on_token_refresh_failed(self):
        """处理token刷新失败"""
        logger.warning("Token刷新失败，需要重新登录")

        # 清除登录状态
        self.is_logged_in = False

        # 重置API服务状态
        simple_api_service.reset_service()

        api_client.clear_token()

        # 清除设置中的token
        self.settings.remove('token')
        self.settings.remove('refresh_token')
        self.settings.remove('token_expires_at')
        self.settings.sync()

        # 显示需要重新登录的提示
        InfoBar.warning(
            title='会话已过期',
            content='您的登录会话已过期，请重新登录',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

        # 显示登录对话框
        self.auth_service.show_login_dialog()

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
            ':icon/assets/MdiLightAccount.png'
        )

        # 添加个人中心到导航，使用头像作为按钮
        self.navigationInterface.addWidget(
            routeKey=self.loginInterface.objectName(),
            widget=self.avatarWidget,
            onClick=lambda: self.showLoginInterface(switch_to_profile=False),
            position=NavigationItemPosition.BOTTOM
        )

        # 将个人中心页面添加到路由系统
        self.stackedWidget.addWidget(self.loginInterface)

    def initWindow(self):
        self.resize(MAIN_WINDOW_SIZE)

        # 设置窗口图标 - macOS使用PNG格式
        if sys.platform == "darwin":
            self.setWindowIcon(QIcon(":/icon/assets/lapped.png"))
            # macOS: 禁用窗口状态恢复
            self.setAttribute(Qt.WA_QuitOnClose, True)
        else:
            self.setWindowIcon(QIcon(":icon/assets/lapped.ico"))

        self.setWindowTitle("Lapped AI")

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
        )
        # self.settings.clear()
        # for key in all_keys:
        #     value = self.settings.value(key)
        #     config.logger.info(f"Key: {key}, Value: {value}")

        # logger.info(config.params)

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
            # 尝试从设置加载token和refresh_token
            if api_client.load_token_from_settings(self.settings):
                try:
                    # 验证token是否有效
                    user_info = {
                        'email': self.settings.value('email', '已登录'),
                    }
                    # 更新用户信息
                    self.loginInterface.updateUserInfo(user_info)

                    # 更新登录状态
                    self.is_logged_in = True
                    self.avatarWidget.setName(user_info['email'])
                    # 更新个人中心页面
                    logger.info("自动登录成功")
                    self.avatarWidget.setAvatar(':icon/assets/MdiAccount.png')

                    # 更新算力消耗系数
                    from nice_ui.services.service_provider import ServiceProvider
                    token_service = ServiceProvider().get_token_service()
                    token_service.update_token_coefficients()

                    # 启动token刷新服务
                    expires_at = api_client.get_token_expiry_time()
                    if expires_at:
                        self.token_refresh_service.start_monitoring(expires_at)
                except AuthenticationError as e:
                    logger.warning(f"Token验证失败，尝试刷新: {e}")
                    # 异步刷新token
                    self._refresh_token_for_auto_login(user_info)
                except Exception as e:
                    # 检查是否是网络连接错误
                    if "All connection attempts failed" in str(e):
                        logger.warning(f"网络连接失败，无法验证登录状态: {e}")
                        # 显示网络连接错误提示
                        InfoBar.warning(
                            title='网络连接错误',
                            content='无法连接到服务器，请检查网络连接',
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=3000,
                            parent=self
                        )
                        # 不清除token，但也不标记为已登录
                        self.is_logged_in = False
                    else:
                        logger.warning(f"Token验证失败: {e}")
                        # Token无效，清除状态
                        self.is_logged_in = False
                        self.settings.remove('token')
                        self.settings.remove('refresh_token')
                        self.settings.sync()
                        api_client.clear_token()

                        # 重置登录窗口状态 - 修复登录按钮无法点击的问题
                        if self.login_window:
                            self.login_window.close()
                            self.login_window = None
            else:
                logger.info("无保存的登录状态")
        except Exception as e:
            logger.error(f"自动登录过程出错: {e}")

    def showLoginInterface(self, switch_to_profile=False):
        """
        显示登录界面

        Args:
            switch_to_profile: 是否在登录后切换到个人中心页面，默认为False
                              当用户主动点击个人中心按钮时为True
                              当系统自动调用登录界面时为False
        """
        if not self.is_logged_in:
            # 如果未登录，显示登录窗口
            if not self.login_window:
                from nice_ui.ui.login import LoginWindow
                self.login_window = LoginWindow(self, self.settings)
                # 登录成功后不自动跳转到个人中心页面
                self.login_window.loginSuccessful.connect(
                    lambda user_info: self.handleLoginSuccess(user_info, False)
                )

            # 计算登录窗口在主窗口中的居中位置
            login_x = self.x() + (self.width() - self.login_window.width()) // 2
            login_y = self.y() + (self.height() - self.login_window.height()) // 2
            self.login_window.move(login_x, login_y)

            self.login_window.show()
        else:
            # 如果已登录，直接切换到个人中心页面
            self.switchTo(self.loginInterface)

    def handleLoginSuccess(self, user_info, switch_to_profile=False):
        """
        处理登录成功的回调

        Args:
            user_info: 用户信息
            switch_to_profile: 是否切换到个人中心页面，默认为False
        """
        self.is_logged_in = True
        self.avatarWidget.setName(user_info.get('email', '已登录'))

        # 登录成功后使用设置图标作为头像
        # 直接使用FluentIcon作为头像，确保与导航图标一致
        self.avatarWidget.setAvatar(':icon/assets/MdiAccount.png')

        # 关闭登录窗口
        if self.login_window:
            self.login_window.hide()

        # 更新个人中心页面的信息
        self.loginInterface.updateUserInfo(user_info)

        # 延迟获取算力消耗系数，避免与其他API调用冲突
        QTimer.singleShot(500, self._delayed_update_token_coefficients)

        # 如果需要切换到个人中心页面，则切换
        if switch_to_profile:
            self.switchTo(self.loginInterface)

    def handleAuthError(self):
        """处理认证错误（401）"""
        # 异步刷新token
        self._refresh_token_for_auth_error()
        self.settings.remove('refresh_token')
        self.settings.sync()
        api_client.clear_token()

        # 重置登录窗口状态 - 修复登录按钮无法点击的问题
        if self.login_window:
            self.login_window.close()
            self.login_window = None

        # 显示错误提示
        InfoBar.error(
            title='登录过期',
            content='您的登录已过期，请重新登录',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # 显示登录窗口
        self.showLoginInterface()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        try:
            # 1. 停止token刷新服务
            if hasattr(self, 'token_refresh_service'):
                self.token_refresh_service.stop_monitoring()
                logger.info("Token refresh service stopped")

            # 2. 停止API服务的工作线程
            if hasattr(simple_api_service, '_worker_thread'):
                simple_api_service._stop_worker()
                logger.info("API worker thread stopped")

            # 3. 异步清理API客户端资源
            if hasattr(self, 'is_logged_in') and self.is_logged_in:
                # 同步关闭，不使用异步
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(api_client.close())
                    loop.close()
                    logger.info("API client closed successfully")
                except Exception as e:
                    logger.error(f"Error closing API client: {e}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # 调用父类的closeEvent
        super().closeEvent(event)

    def _connect_signals(self):
        """连接信号槽"""
        # 连接任务错误信号
        data_bridge.task_error.connect(self._on_task_error)

    @Slot(str, str)
    def _on_task_error(self, task_id: str, error_message: str):
        """处理任务错误信号"""
        logger.error(f"任务错误: {task_id} - {error_message}")

        # 显示错误提示
        InfoBar.error(
            title="任务失败",
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self
        )

    def _refresh_token_for_auto_login(self, user_info):
        """为自动登录刷新token（异步）"""
        def on_success(result):
            logger.info("Token刷新成功，重新尝试自动登录")
            # 刷新成功，更新设置中的token
            self.settings.setValue('token', api_client._token)
            if api_client._refresh_token:
                self.settings.setValue('refresh_token', api_client._refresh_token)
            self.settings.sync()

            # 更新登录状态
            self.is_logged_in = True
            self.avatarWidget.setName(user_info['email'])

            # 更新个人中心页面
            self.loginInterface.updateUserInfo(user_info)

            # 启动token刷新服务
            expires_at = api_client.get_token_expiry_time()
            if expires_at:
                self.token_refresh_service.start_monitoring(expires_at)

        def on_error(error):
            logger.error(f"Token刷新失败: {error}")
            # 刷新失败的处理逻辑可以在这里添加

        simple_api_service.refresh_token(callback_success=on_success, callback_error=on_error)

    def _refresh_token_for_auth_error(self):
        """为认证错误刷新token（异步）"""
        def on_success(result):
            logger.info("Token刷新成功")
            # 刷新成功，更新设置中的token
            self.settings.setValue('token', api_client._token)
            if api_client._refresh_token:
                self.settings.setValue('refresh_token', api_client._refresh_token)
            self.settings.sync()

            # 从服务器获取并更新算力消耗系数
            from nice_ui.services.service_provider import ServiceProvider
            token_service = ServiceProvider().get_token_service()
            token_service.update_token_coefficients()

            # 显示成功提示
            InfoBar.success(
                title='会话已更新',
                content='您的登录会话已自动更新',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

        def on_error(error):
            logger.error(f"Token刷新失败: {error}")
            # 刷新失败，清除登录状态
            self.is_logged_in = False
            self.avatarWidget.setName('未登录')

            # 清除保存的token和refresh_token
            self.settings.remove('token')
            self.settings.remove('refresh_token')
            self.settings.sync()

            # 显示登录窗口
            self.showLoginInterface()

        api_service.refresh_token(callback_success=on_success, callback_error=on_error)

    def _cleanup_api_client(self):
        """清理API客户端（异步）"""
        def on_complete(result):
            logger.info("API client resources cleaned up successfully")

        def on_error(error):
            logger.error(f"Error cleaning up API client: {error}")

        simple_api_service.execute_async(
            api_client.close,
            callback_success=on_complete,
            callback_error=on_error
        )

    def _delayed_update_token_coefficients(self):
        """延迟更新算力消耗系数"""
        try:
            from nice_ui.services.service_provider import ServiceProvider
            token_service = ServiceProvider().get_token_service()
            token_service.update_token_coefficients()
            logger.debug("Delayed token coefficients update initiated")
        except Exception as e:
            logger.error(f"Failed to update token coefficients: {e}")


if __name__ == "__main__":
    def main():
        app = QApplication(sys.argv)
        # window = Video2SRT("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
        window = Window()
        window.show()
        sys.exit(app.exec())

    main()