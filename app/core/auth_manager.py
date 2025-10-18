"""
认证状态管理器
负责统一管理认证状态的持久化存储，作为 QSettings 的唯一访问点
"""
import time
from typing import Optional

from PySide6.QtCore import QSettings

from utils import logger


class AuthManager:
    """认证状态管理器 - QSettings 的唯一访问点

    职责：
    1. 保存认证状态到 QSettings
    2. 从 QSettings 加载认证状态
    3. 清除认证数据（保留 email 用于记住账号）

    设计原则：
    - 单一数据源：所有认证数据的读写都通过这个类
    - 原子操作：保存和清除都是完整的，不会出现部分数据
    - 保持键名不变：使用原有的 'token', 'refresh_token', 'token_expires_at', 'email'
    - 记住账号：登出时保留 email，方便下次登录
    """

    # 所有认证相关的键名（email 在登出时不会被清除）
    KEYS = ['token', 'refresh_token', 'token_expires_at', 'email']
    
    def __init__(self, settings: QSettings):
        """初始化认证管理器
        
        Args:
            settings: QSettings 实例
        """
        self._settings = settings
    
    def save_auth_state(self, token: str, refresh_token: str, 
                       expires_at: int, email: str = "") -> None:
        """保存完整的认证状态
        
        Args:
            token: 访问 token
            refresh_token: 刷新 token
            expires_at: token 过期时间戳（秒）
            email: 用户邮箱（可选）
        """
        self._settings.setValue('token', token)
        self._settings.setValue('refresh_token', refresh_token)
        self._settings.setValue('token_expires_at', expires_at)
        
        if email:
            self._settings.setValue('email', email)
        
        self._settings.sync()
        logger.info(f"认证状态已保存，过期时间: {time.ctime(expires_at)}")
    
    def load_to_api_client(self, api_client) -> bool:
        """加载认证状态到 APIClient
        
        Args:
            api_client: APIClient 实例
            
        Returns:
            bool: 是否成功加载（即是否存在已保存的 token）
        """
        return api_client.load_token_from_settings(self._settings)
    
    def clear_auth_state(self) -> None:
        """清除认证状态

        清除认证相关的键：token, refresh_token, token_expires_at
        注意：不清除 email（保留用于记住账号功能）
        """
        keys_to_clear = ['token', 'refresh_token', 'token_expires_at']
        for key in keys_to_clear:
            self._settings.remove(key)
        self._settings.sync()
        logger.info("认证状态已清除（保留邮箱）")
    
    def get_email(self) -> object:
        """获取保存的邮箱地址
        
        Returns:
            str: 保存的邮箱地址，如果不存在则返回空字符串
        """
        return self._settings.value('email', '')
    
    def get_token_expires_at(self) -> Optional[int]:
        """获取保存的 token 过期时间
        
        Returns:
            Optional[int]: token 过期时间戳，如果不存在则返回 None
        """
        expires_at = self._settings.value('token_expires_at')
        logger.trace(f"get_token_expires_at: {expires_at}")
        logger.trace(type(expires_at))
        if expires_at:
            try:
                return int(expires_at)
            except (ValueError, TypeError):
                logger.warning("Invalid token_expires_at in settings")
                return None
        return None

