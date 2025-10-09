"""
服务提供者 - 使用模块级单例

设计原则:
1. 延迟初始化 - 服务在首次访问时创建
2. 线程安全 - Python的模块导入是线程安全的
3. 全局访问 - 任何地方都能访问
4. 向后兼容 - 保留ServiceProvider类
5. 显式依赖注入 - 通过构造函数传递依赖

依赖关系（单向，无循环）:
    UIManager (无依赖)
        ↑
        ├── TokenService(ui_manager)
        │       ↑
        └── AuthService(ui_manager, token_service)

关键：按依赖顺序创建服务
    1. UIManager（无依赖）
    2. TokenService（依赖UIManager）
    3. AuthService（依赖UIManager和TokenService）
"""
from utils import logger


# 延迟创建的服务实例
_ui_manager = None
_auth_service = None
_token_service = None


def _ensure_services_initialized():
    """
    确保服务已初始化（延迟初始化）

    关键：按依赖顺序创建，避免循环依赖
    """
    global _ui_manager, _auth_service, _token_service

    # 1. 创建UIManager（无依赖）
    if _ui_manager is None:
        from nice_ui.managers.ui_manager import MainUIManager
        _ui_manager = MainUIManager()
        logger.debug("UIManager已初始化")

    # 2. 创建TokenService（依赖UIManager）
    if _token_service is None:
        from nice_ui.services.token_service import TokenService
        _token_service = TokenService(_ui_manager)
        logger.debug("TokenService已初始化")

    # 3. 创建AuthService（依赖UIManager和TokenService）
    if _auth_service is None:
        from nice_ui.services.auth_service import AuthService
        _auth_service = AuthService(_ui_manager, _token_service)  # ← 显式注入
        logger.debug("AuthService已初始化")


def get_ui_manager():
    """
    获取UI管理器

    Returns:
        MainUIManager: UI管理器实例
    """
    _ensure_services_initialized()
    return _ui_manager


def get_auth_service():
    """
    获取认证服务

    Returns:
        AuthService: 认证服务实例
    """
    _ensure_services_initialized()
    return _auth_service


def get_token_service():
    """
    获取代币服务

    Returns:
        TokenService: 代币服务实例
    """
    _ensure_services_initialized()
    return _token_service


# 向后兼容：保留ServiceProvider类
class ServiceProvider:
    """
    服务提供者 - 向后兼容包装器

    注意：这个类只是为了向后兼容，推荐直接使用模块级函数：
    - get_ui_manager()
    - get_auth_service()
    - get_token_service()
    """

    def get_ui_manager(self):
        """获取UI管理器"""
        return get_ui_manager()

    def get_auth_service(self):
        """获取认证服务"""
        return get_auth_service()

    def get_token_service(self):
        """获取代币服务"""
        return get_token_service()
