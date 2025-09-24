from typing import Optional, Dict, Any, Callable

from PySide6.QtCore import QSettings

from app.core.api_client import api_client
from nice_ui.services.token_refresh_service import get_token_refresh_service
from nice_ui.services.api_service import api_service
from nice_ui.interfaces.auth import AuthInterface
from nice_ui.interfaces.ui_manager import UIManagerInterface
from nice_ui.ui import SettingsManager
from utils import logger


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
            self._settings = SettingsManager.get_instance()
        return self._settings

    def check_login_status(self) -> (bool, int):
        """
        检查用户是否已登录

        Returns:
            bool: True表示已登录，False表示未登录,int:用户余额
        """
        try:
            # 获取设置对象
            settings = self._get_settings()

            # 检查是否有token
            if not settings.value('token'):
                logger.info("未找到token，需要登录")
                self.show_login_dialog()
                return False, None

            # 检查token是否过期（简化验证，不进行API调用）
            if api_client.is_token_expired():
                logger.info("Token已过期，需要重新登录")
                self.show_login_dialog()
                return False, None

            # Token存在且未过期，获取真实余额
            logger.info("用户已登录，获取用户余额")

            # 从TokenService获取同步余额
            from nice_ui.services.service_provider import ServiceProvider
            service_provider = ServiceProvider()
            token_service = service_provider.get_token_service()
            user_balance = token_service.get_user_balance()

            logger.info(f"用户余额: {user_balance}")
            return True, user_balance

        except Exception as e:
            logger.error(f"检查登录状态时发生错误: {str(e)}")
            self.show_login_dialog()
            return False, None

    def show_login_dialog(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        显示登录对话框

        Args:
            callback: 登录成功后的回调函数，接收用户信息作为参数
        """
        self.ui_manager.show_login_window(callback)

    def logout(self) -> None:
        """用户登出"""
        # 停止token刷新服务
        token_refresh_service = get_token_refresh_service()
        token_refresh_service.stop_monitoring()

        # 重置API服务状态
        api_service.reset_service()

        # 清除API客户端的token
        api_client.clear_token()

        # 清除设置中的token和相关信息
        settings = self._get_settings()
        settings.remove('token')
        settings.remove('refresh_token')
        settings.remove('token_expires_at')
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
