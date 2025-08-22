from typing import Optional, Dict, Any, Callable

from PySide6.QtCore import QSettings

from api_client import api_client
from nice_ui.interfaces.auth import AuthInterface
from nice_ui.interfaces.ui_manager import UIManagerInterface
from nice_ui.ui import SettingsManager
from nice_ui.util.api_helper import ApiHelper
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

    def check_login_status(self, callback=None) -> None:
        """
        检查用户是否已登录（异步版本）

        Args:
            callback: 回调函数，接收(is_logged_in: bool, balance: int)参数

        注意：这个方法现在是异步的，结果通过回调函数返回
        """
        try:
            # 获取设置对象
            settings = self._get_settings()

            # 检查是否有token
            if not settings.value('token'):
                logger.info("未找到token，需要登录")
                if callback:
                    callback(False, None)
                self.show_login_dialog()
                return

            # 使用异步方式验证token
            def on_balance_success(balance_data):
                try:
                    if 'data' in balance_data and 'balance' in balance_data['data']:
                        user_balance = int(balance_data['data']['balance'])
                        logger.info(f"用户当前代币余额: {user_balance}")
                        logger.info("用户已登录，可以继续使用云引擎")
                        if callback:
                            callback(True, user_balance)
                    else:
                        logger.warning(f"响应数据格式不正确: {balance_data}")
                        if callback:
                            callback(False, None)
                except Exception as e:
                    logger.error(f"处理余额数据失败: {e}")
                    if callback:
                        callback(False, None)

            def on_balance_error(error):
                logger.info(f"Token验证失败，需要重新登录: {error}")
                if callback:
                    callback(False, None)
                self.show_login_dialog()

            # 异步获取用户余额来验证token
            ApiHelper.get_balance(on_balance_success, on_balance_error)

        except Exception as e:
            logger.error(f"检查登录状态时发生错误: {str(e)}")
            if callback:
                callback(False, None)
            self.show_login_dialog()

    def check_login_status_sync(self) -> (bool, int):
        """
        检查用户是否已登录（同步版本，仅用于向后兼容）

        警告：这个方法只检查本地token，不验证服务器状态
        建议使用异步版本 check_login_status()

        Returns:
            tuple: (is_logged_in: bool, balance: int or None)
        """
        logger.warning("使用了已废弃的同步登录检查方法，建议使用异步版本")

        try:
            # 获取设置对象
            settings = self._get_settings()

            # 检查是否有token
            if not settings.value('token'):
                logger.info("未找到token，需要登录")
                return False, None

            # 只返回本地缓存的余额，不进行服务器验证
            cached_balance = settings.value('cached_balance', 0)
            logger.info(f"返回缓存的余额: {cached_balance}")
            return True, int(cached_balance) if cached_balance else 0

        except Exception as e:
            logger.error(f"检查登录状态时发生错误: {str(e)}")
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

        # 尝试获取用户ID - 现在get_id是异步的，这里使用缓存的值
        # 注意：这个方法现在不能直接获取用户ID，建议在UI中使用ApiHelper.get_id()
        logger.warning("AuthService.get_user_info() 中的get_id()调用已废弃，使用缓存的用户ID")
        user_id = settings.value('user_id', '')

        return {
            'user_id': user_id,
            'email': email
        }
