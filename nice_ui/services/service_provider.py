from nice_ui.services.auth_service import AuthService
from nice_ui.managers.ui_manager import MainUIManager
from nice_ui.services.token_service import TokenService


class ServiceProvider:
    """服务提供者，负责创建和管理服务实例"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceProvider, cls).__new__(cls)
            cls._instance._initialize_services()
        return cls._instance

    def _initialize_services(self):
        """初始化所有服务"""
        self.ui_manager = MainUIManager()
        self.auth_service = AuthService(self.ui_manager)
        self.token_service = TokenService(self.ui_manager)

    def get_auth_service(self):
        """
        获取认证服务

        Returns:
            AuthService: 认证服务实例
        """
        return self.auth_service

    def get_ui_manager(self):
        """
        获取UI管理器

        Returns:
            MainUIManager: UI管理器实例
        """
        return self.ui_manager

    def get_token_service(self):
        """
        获取代币服务

        Returns:
            TokenService: 代币服务实例
        """
        return self.token_service
