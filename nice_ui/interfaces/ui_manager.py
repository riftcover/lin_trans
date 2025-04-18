from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any


class UIManagerInterface(ABC):
    """UI管理器接口，定义UI相关操作"""

    @abstractmethod
    def show_login_window(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        显示登录窗口
        
        Args:
            callback: 登录成功后的回调函数，接收用户信息作为参数
        """
        pass
    
    @abstractmethod
    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        """
        显示消息提示
        
        Args:
            title: 消息标题
            message: 消息内容
            message_type: 消息类型，可选值："info", "success", "warning", "error"
        """
        pass
