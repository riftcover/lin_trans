from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable


class AuthInterface(ABC):
    """认证服务接口，定义认证相关的方法"""

    @abstractmethod
    def check_login_status(self) -> bool:
        """
        检查用户是否已登录
        
        Returns:
            bool: True表示已登录，False表示未登录
        """
        pass
        
    @abstractmethod
    def show_login_dialog(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        显示登录对话框
        
        Args:
            callback: 登录成功后的回调函数，接收用户信息作为参数
        """
        pass
    
    @abstractmethod
    def logout(self) -> None:
        """用户登出"""
        pass
    
    @abstractmethod
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前登录用户信息
        
        Returns:
            Dict或None: 用户信息字典，未登录时返回None
        """
        pass
