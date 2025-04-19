import time
from typing import Optional, Dict, Any, Callable

from nice_ui.interfaces.auth import AuthInterface
from nice_ui.interfaces.ui_manager import UIManagerInterface
from nice_ui.configure import config
from utils import logger
from api_client import api_client, AuthenticationError
from PySide6.QtCore import QSettings


class AuthService(AuthInterface):
    """认证服务实现类，处理登录状态检查和管理"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, ui_manager: UIManagerInterface):
        """
        初始化认证服务

        Args:
            ui_manager: UI管理器实例
        """
        # 避免重复初始化
        if getattr(self, '_initialized', False):
            return

        self.ui_manager = ui_manager
        self._settings = None
        self._initialized = True

    def _get_settings(self):
        """
        获取设置对象

        Returns:
            QSettings: 设置对象
        """
        if self._settings is None:
            # 获取当前工作目录
            import os
            current_directory = os.path.basename(os.getcwd())
            self._settings = QSettings("Locoweed3", f"LinLInTrans_{current_directory}")
        return self._settings

    def check_login_status(self) -> bool:
        """
        检查用户是否已登录

        Returns:
            bool: True表示已登录，False表示未登录
        """
        try:
            # 获取设置对象
            settings = self._get_settings()

            # 检查是否有token
            if not settings.value('token'):
                logger.info("未找到token，需要登录")
                self.show_login_dialog()
                return False

            # 尝试从设置中加载token
            if not api_client.load_token_from_settings(settings):
                logger.info("加载token失败，需要登录")
                self.show_login_dialog()
                return False

            # 尝试进行一个简单的API调用来验证token是否有效
            try:
                # 获取用户余额信息来验证token
                api_client.get_balance_sync()
                return True
            except Exception as e:
                logger.info(f"Token验证失败，需要重新登录 {str(e)}")
                self.show_login_dialog()
                return False

        except Exception as e:
            logger.error(f"检查登录状态时发生错误: {str(e)}")
            self.show_login_dialog()
            return False

    def show_login_dialog(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        显示登录对话框

        Args:
            callback: 登录成功后的回调函数，接收用户信息作为参数
        """
        self.ui_manager.show_login_window(callback)

    def logout(self) -> None:
        """用户登出"""
        # 清除API客户端的token
        api_client.clear_token()

        # 清除设置中的token和相关信息
        settings = self._get_settings()
        settings.remove('token')
        settings.remove('refresh_token')
        settings.sync()

        logger.info("用户已登出")

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前登录用户信息

        Returns:
            Dict或None: 用户信息字典，未登录时返回None
        """
        if not self.check_login_status():
            return None

        # 获取设置对象
        settings = self._get_settings()

        # 从设置中获取用户信息
        email = settings.value('email', '已登录')

        # 尝试获取用户ID
        try:
            user_id = api_client.get_id()
        except Exception as e:
            logger.warning(f"获取用户ID失败: {str(e)}")
            user_id = settings.value('user_id', '')

        return {
            'user_id': user_id,
            'email': email
        }
