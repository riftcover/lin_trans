from typing import Optional, Callable, Dict, Any

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from nice_ui.interfaces.ui_manager import UIManagerInterface
from utils import logger


class MainUIManager(UIManagerInterface):
    """主UI管理器实现类，处理UI相关操作"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MainUIManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化UI管理器"""
        # 避免重复初始化
        if getattr(self, '_initialized', False):
            return
            
        self.main_window = None
        self._initialized = True
        
    def _find_main_window(self):
        """
        查找主窗口实例
        
        Returns:
            主窗口实例或None
        """
        if self.main_window is not None:
            return self.main_window
            
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "MainWindow":
                self.main_window = widget
                return self.main_window
                
        return None
    
    def show_login_window(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """
        显示登录窗口
        
        Args:
            callback: 登录成功后的回调函数，接收用户信息作为参数
        """
        main_window = self._find_main_window()
        if not main_window:
            logger.error("未找到主窗口实例")
            return
            
        # 如果提供了回调，则在登录成功后执行
        if callback:
            # 保存原始的handleLoginSuccess方法
            original_handler = main_window.handleLoginSuccess
            
            # 创建新的处理函数
            def new_handler(user_info, switch_to_profile=False):
                # 调用原始处理函数
                original_handler(user_info, switch_to_profile)
                # 调用回调
                callback(user_info)
                
                # 恢复原始处理函数
                main_window.handleLoginSuccess = original_handler
            
            # 临时替换处理函数
            main_window.handleLoginSuccess = new_handler
        
        # 显示登录界面，不切换到个人中心
        main_window.showLoginInterface(switch_to_profile=False)
    
    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        """
        显示消息提示
        
        Args:
            title: 消息标题
            message: 消息内容
            message_type: 消息类型，可选值："info", "success", "warning", "error"
        """
        from vendor.qfluentwidgets import InfoBar, InfoBarPosition
        
        main_window = self._find_main_window()
        if not main_window:
            logger.error(f"未找到主窗口实例，无法显示消息: {title} - {message}")
            return
            
        if message_type == "error":
            InfoBar.error(
                title=title,
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=main_window
            )
        elif message_type == "success":
            InfoBar.success(
                title=title,
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=main_window
            )
        elif message_type == "warning":
            InfoBar.warning(
                title=title,
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=main_window
            )
        else:
            InfoBar.info(
                title=title,
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=main_window
            )
