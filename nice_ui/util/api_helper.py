"""
API调用辅助工具 - 用于在PySide6中正确调用异步API

这个模块提供了在PySide6 UI线程中安全调用异步API的工具类。
遵循Linus的设计原则：简洁、实用、无特殊情况。
"""

import asyncio
from typing import Any, Callable, Optional
from PySide6.QtCore import QObject, Signal, QThread

from api_client import api_client
from utils import logger


class ApiCallSignals(QObject):
    """API调用信号"""
    success = Signal(object)  # 成功信号，携带结果数据
    error = Signal(str)       # 错误信号，携带错误信息
    finished = Signal()       # 完成信号


class ApiCallWorker(QThread):
    """API调用工作线程 - 在独立线程中运行异步事件循环"""

    def __init__(self, async_func: Callable, *args, **kwargs):
        super().__init__()
        self.signals = ApiCallSignals()
        self.async_func = async_func
        self.args = args
        self.kwargs = kwargs
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # 连接finished信号到自动清理
        self.signals.finished.connect(self.deleteLater)

    def run(self):
        """在新的事件循环中运行异步函数"""
        self.loop = None
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # 检查事件循环是否已关闭
            if self.loop.is_closed():
                logger.warning("事件循环已关闭，无法执行API调用")
                self.signals.error.emit("事件循环已关闭")
                return

            # 执行异步函数
            result = self.loop.run_until_complete(self.async_func(*self.args, **self.kwargs))
            self.signals.success.emit(result)

        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            self.signals.error.emit(str(e))
        finally:
            # 安全关闭事件循环
            if self.loop and not self.loop.is_closed():
                try:
                    self.loop.close()
                except Exception as e:
                    logger.warning(f"关闭事件循环时出错: {e}")
            self.signals.finished.emit()

    def stop(self):
        """停止线程"""
        if self.isRunning():
            # 如果有事件循环，尝试停止它
            if self.loop and not self.loop.is_closed():
                try:
                    # 在事件循环中调用stop
                    self.loop.call_soon_threadsafe(self.loop.stop)
                except Exception as e:
                    logger.warning(f"停止事件循环时出错: {e}")

            # 退出线程
            self.quit()
            # 等待线程结束，最多3秒
            if not self.wait(3000):
                logger.warning("线程未能在3秒内正常结束")
                self.terminate()  # 强制终止


class ApiHelper:
    """API调用辅助类 - 简化在UI中调用异步API的过程"""

    # 类级别的线程管理
    _active_workers = []

    @classmethod
    def call_async(cls, async_func: Callable,
                   success_callback: Optional[Callable] = None,
                   error_callback: Optional[Callable] = None,
                   finished_callback: Optional[Callable] = None,
                   *args, **kwargs) -> ApiCallWorker:
        """
        调用异步API函数

        Args:
            async_func: 要调用的异步函数
            success_callback: 成功回调函数，接收结果作为参数
            error_callback: 错误回调函数，接收错误信息作为参数
            finished_callback: 完成回调函数，无参数
            *args, **kwargs: 传递给异步函数的参数

        Returns:
            ApiCallWorker: 工作线程对象
        """
        worker = ApiCallWorker(async_func, *args, **kwargs)

        # 连接信号
        if success_callback:
            worker.signals.success.connect(success_callback)
        if error_callback:
            worker.signals.error.connect(error_callback)

        # 包装finished_callback以便清理
        def cleanup_wrapper():
            if worker in cls._active_workers:
                cls._active_workers.remove(worker)
            if finished_callback and callable(finished_callback):
                finished_callback()

        worker.signals.finished.connect(cleanup_wrapper)

        # 添加到活跃线程列表
        cls._active_workers.append(worker)

        # 启动线程
        worker.start()
        return worker

    @classmethod
    def cleanup_all(cls):
        """清理所有活跃的工作线程"""
        for worker in cls._active_workers[:]:  # 创建副本以避免修改列表时的问题
            if worker.isRunning():
                worker.stop()
        cls._active_workers.clear()
    
    @classmethod
    def login(cls, email: str, password: str,
              success_callback: Optional[Callable] = None,
              error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """用户登录的便捷方法"""
        return cls.call_async(
            api_client.login, success_callback, error_callback, None,
            email, password
        )

    @classmethod
    def get_balance(cls, success_callback: Optional[Callable] = None,
                    error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """获取余额的便捷方法"""
        return cls.call_async(
            api_client.get_balance, success_callback, error_callback, None
        )

    @classmethod
    def refresh_session(cls, success_callback: Optional[Callable] = None,
                        error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """刷新会话的便捷方法"""
        return cls.call_async(
            api_client.refresh_session, success_callback, error_callback, None
        )
    
    @classmethod
    def get_history(cls, page: int = 1, page_size: int = 10,
                    success_callback: Optional[Callable] = None,
                    error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """获取历史记录的便捷方法"""
        return cls.call_async(
            api_client.get_history, success_callback, error_callback, None,
            page, page_size
        )

    @classmethod
    def get_id(cls, success_callback: Optional[Callable] = None,
               error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """获取用户ID的便捷方法"""
        return cls.call_async(
            api_client.get_id, success_callback, error_callback, None
        )

    @classmethod
    def consume_tokens(cls, token_amount: int, feature_key: str = "asr", user_id: Optional[str] = None,
                       success_callback: Optional[Callable] = None,
                       error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """消费代币的便捷方法"""
        return cls.call_async(
            api_client.consume_tokens, success_callback, error_callback, None,
            token_amount, feature_key, user_id
        )

    @classmethod
    def create_recharge_order(cls, user_id: str, amount_in_yuan: float, token_amount: int,
                              success_callback: Optional[Callable] = None,
                              error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """创建充值订单的便捷方法"""
        return cls.call_async(
            api_client.create_recharge_order, success_callback, error_callback, None,
            user_id, amount_in_yuan, token_amount
        )

    @classmethod
    def check_version(cls, platform: str, current_version: str,
                      success_callback: Optional[Callable] = None,
                      error_callback: Optional[Callable] = None) -> ApiCallWorker:
        """检查版本的便捷方法"""
        return cls.call_async(
            api_client.check_version, success_callback, error_callback, None,
            platform, current_version
        )


# 为了向后兼容，提供一些常用的快捷函数
def async_login(email: str, password: str, success_callback: Callable, error_callback: Callable = None):
    """异步登录 - 向后兼容函数"""
    return ApiHelper.login(email, password, success_callback, error_callback)


def async_get_balance(success_callback: Callable, error_callback: Callable = None):
    """异步获取余额 - 向后兼容函数"""
    return ApiHelper.get_balance(success_callback, error_callback)


def async_refresh_session(success_callback: Callable, error_callback: Callable = None):
    """异步刷新会话 - 向后兼容函数"""
    return ApiHelper.refresh_session(success_callback, error_callback)
