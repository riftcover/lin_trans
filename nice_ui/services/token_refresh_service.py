"""
Token自动刷新服务
负责在token过期前主动刷新，确保用户无感知的持续认证
"""
import time
from typing import Optional
from PySide6.QtCore import QTimer, QObject, Signal
from utils import logger
from app.core.api_client import api_client


class TokenRefreshService(QObject):
    """Token自动刷新服务"""
    
    # 信号：token刷新成功
    token_refreshed = Signal(dict)  # 发送新的token信息
    # 信号：token刷新失败，需要重新登录
    refresh_failed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._check_and_refresh_token)
        
        # 配置参数
        self.check_interval = 5 * 60 * 1000  # 每5分钟检查一次（毫秒）
        self.refresh_threshold = 10 * 60  # 在过期前10分钟刷新（秒）
        
        # 状态跟踪
        self._is_running = False
        self._last_refresh_time = 0
        self._token_expires_at = None
    
    def start_monitoring(self, token_expires_at: Optional[int] = None):
        """
        开始监控token状态
        
        Args:
            token_expires_at: token过期时间戳（秒），如果为None则从API客户端获取
        """
        if self._is_running:
            return
        
        # 设置过期时间
        if token_expires_at:
            self._token_expires_at = token_expires_at
        else:
            # 尝试从当前token中解析过期时间
            self._token_expires_at = self._get_token_expiry_from_settings()
        
        if not self._token_expires_at:
            logger.warning("无法获取token过期时间，使用默认24小时")
            self._token_expires_at = int(time.time()) + 24 * 3600
        
        self._is_running = True
        self.refresh_timer.start(self.check_interval)
        logger.info(f"开始监控token状态，过期时间: {time.ctime(self._token_expires_at)}")
    
    def stop_monitoring(self):
        """停止监控token状态"""
        if not self._is_running:
            return
        
        self._is_running = False
        self.refresh_timer.stop()
        logger.info("停止监控token状态")
    
    def update_token_expiry(self, expires_at: int):
        """
        更新token过期时间
        
        Args:
            expires_at: 新的过期时间戳（秒）
        """
        self._token_expires_at = expires_at
        logger.debug(f"更新token过期时间: {time.ctime(expires_at)}")
    
    def _check_and_refresh_token(self):
        """检查token状态并在需要时刷新"""
        if not self._token_expires_at:
            logger.warning("token过期时间未设置，跳过检查")
            return
        
        current_time = int(time.time())
        time_until_expiry = self._token_expires_at - current_time
        
        logger.debug(f"检查token状态，距离过期还有 {time_until_expiry} 秒")
        
        # 如果token已经过期
        if time_until_expiry <= 0:
            logger.warning("Token已过期，尝试刷新")
            self._perform_refresh()
            return
        
        # 如果接近过期时间，主动刷新
        if time_until_expiry <= self.refresh_threshold:
            logger.info(f"Token将在 {time_until_expiry} 秒后过期，开始主动刷新")
            self._perform_refresh()
    
    def _perform_refresh(self):
        """执行token刷新"""
        try:
            # 避免频繁刷新
            current_time = time.time()
            if current_time - self._last_refresh_time < 60:  # 1分钟内不重复刷新
                logger.debug("刷新间隔太短，跳过本次刷新")
                return
            
            self._last_refresh_time = current_time
            
            # 调用API客户端刷新token（使用同步版本，因为这是在定时器回调中）
            success = api_client._refresh_session_sync()
            
            if success:
                logger.info("Token刷新成功")
                
                # 更新过期时间（假设新token有效期24小时）
                new_expires_at = int(time.time()) + 24 * 3600
                self.update_token_expiry(new_expires_at)
                
                # 发送刷新成功信号
                token_info = {
                    'access_token': api_client._token,
                    'refresh_token': api_client._refresh_token,
                    'expires_at': new_expires_at
                }
                self.token_refreshed.emit(token_info)
                
                # 保存到设置中
                self._save_token_to_settings(token_info)
                
            else:
                logger.error("Token刷新失败")
                self.refresh_failed.emit()
                self.stop_monitoring()
                
        except Exception as e:
            logger.error(f"Token刷新过程中发生错误: {str(e)}")
            self.refresh_failed.emit()
            self.stop_monitoring()
    
    def _get_token_expiry_from_settings(self) -> Optional[int]:
        """从设置中获取token过期时间"""
        try:
            from nice_ui.ui import SettingsManager
            settings = SettingsManager.get_instance()
            expires_at = settings.value('token_expires_at')
            if expires_at:
                return int(expires_at)
        except Exception as e:
            logger.warning(f"无法从设置中获取token过期时间: {str(e)}")
        return None

    def _save_token_to_settings(self, token_info: dict):
        """保存token信息到设置中"""
        try:
            from nice_ui.ui import SettingsManager
            settings = SettingsManager.get_instance()

            if 'access_token' in token_info:
                settings.setValue('token', token_info['access_token'])

            if 'refresh_token' in token_info:
                settings.setValue('refresh_token', token_info['refresh_token'])
            
            if 'expires_at' in token_info:
                settings.setValue('token_expires_at', token_info['expires_at'])
            
            settings.sync()
            logger.debug("Token信息已保存到设置中")
            
        except Exception as e:
            logger.error(f"保存token信息到设置时发生错误: {str(e)}")
    
    def force_refresh(self):
        """强制刷新token"""
        logger.info("强制刷新token")
        self._perform_refresh()


# 全局token刷新服务实例
_token_refresh_service = None


def get_token_refresh_service() -> TokenRefreshService:
    """获取全局token刷新服务实例"""
    global _token_refresh_service
    if _token_refresh_service is None:
        _token_refresh_service = TokenRefreshService()
    return _token_refresh_service
