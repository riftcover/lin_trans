"""
简化的API调用服务
使用单一工作线程和共享事件循环，避免复杂的线程管理
"""
import asyncio
import threading
from typing import Optional, Callable, Any
from queue import Queue, Empty
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QThread, QMutex, QMutexLocker, QTimer

from app.core.api_client import api_client
from utils import logger


@dataclass
class ApiRequest:
    """API请求封装"""
    request_id: str
    func: Callable
    args: tuple
    kwargs: dict
    callback_success: Optional[Callable] = None
    callback_error: Optional[Callable] = None


class ApiWorkerSignals(QObject):
    """API工作线程信号"""
    request_completed = Signal(str, object)  # request_id, result
    request_failed = Signal(str, str)        # request_id, error_message


class ApiWorkerThread(QThread):
    """单一的API工作线程，使用共享事件循环"""
    
    def __init__(self):
        super().__init__()
        self.signals = ApiWorkerSignals()
        self.request_queue = Queue()
        self.loop = None
        self.should_stop = False
        
    def add_request(self, request: ApiRequest):
        """添加API请求到队列"""
        self.request_queue.put(request)
        
    def stop_worker(self):
        """停止工作线程"""
        self.should_stop = True
        # 添加一个停止信号到队列
        self.request_queue.put(None)
        
    def run(self):
        """运行工作线程"""
        thread_id = threading.get_ident()
        
        try:
            # 创建事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 处理请求队列
            while not self.should_stop:
                try:
                    # 从队列中获取请求（阻塞等待）
                    request = self.request_queue.get(timeout=1.0)
                    
                    if request is None:  # 停止信号
                        break
                        
                    # 执行异步请求
                    self._execute_request(request)
                    
                except Empty:
                    # 队列为空，继续等待
                    continue
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    
        except Exception as e:
            logger.error(f"ApiWorkerThread {thread_id} error: {e}")
        finally:
            # 清理事件循环
            if self.loop and not self.loop.is_closed():
                try:
                    # 取消所有待处理的任务
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()
                    
                    # 关闭事件循环
                    self.loop.close()
                    logger.info(f"Event loop {thread_id} closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing event loop: {e}")
            
            logger.info(f"ApiWorkerThread {thread_id} finished")
    
    def _execute_request(self, request: ApiRequest):
        """执行单个API请求"""
        try:
            # 在事件循环中执行异步函数
            result = self.loop.run_until_complete(
                request.func(*request.args, **request.kwargs)
            )
            
            # 发出成功信号
            self.signals.request_completed.emit(request.request_id, result)
            
        except Exception as e:
            error_msg = str(e)
            logger.debug(f"Request {request.func.__name__} failed: {error_msg}")
            
            # 发出失败信号
            self.signals.request_failed.emit(request.request_id, error_msg)


class SimpleApiService(QObject):
    """简化的API调用服务"""
    
    _instance = None
    _mutex = QMutex()
    
    def __new__(cls):
        with QMutexLocker(cls._mutex):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        
        super().__init__()
        self._initialized = True
        
        # 工作线程
        self._worker_thread = None
        self._request_counter = 0
        self._active_requests = {}  # request_id -> (callback_success, callback_error)
        
        # 启动工作线程
        self._start_worker()
    
    def _start_worker(self):
        """启动工作线程"""
        if self._worker_thread and self._worker_thread.isRunning():
            return
            
        self._worker_thread = ApiWorkerThread()
        
        # 连接信号
        self._worker_thread.signals.request_completed.connect(self._on_request_completed)
        self._worker_thread.signals.request_failed.connect(self._on_request_failed)
        
        # 启动线程
        self._worker_thread.start()
    
    def _stop_worker(self):
        """停止工作线程"""
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.stop_worker()
            self._worker_thread.wait(3000)  # 等待最多3秒
            self._worker_thread = None
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        self._request_counter += 1
        return f"api_req_{self._request_counter}"
    
    def _on_request_completed(self, request_id: str, result: Any):
        """处理请求完成"""
        if request_id in self._active_requests:
            callback_success, callback_error = self._active_requests.pop(request_id)
            if callback_success:
                try:
                    callback_success(result)
                except Exception as e:
                    logger.error(f"Error in success callback for {request_id}: {e}")
    
    def _on_request_failed(self, request_id: str, error_msg: str):
        """处理请求失败"""
        if request_id in self._active_requests:
            callback_success, callback_error = self._active_requests.pop(request_id)
            if callback_error:
                try:
                    callback_error(error_msg)
                except Exception as e:
                    logger.error(f"Error in error callback for {request_id}: {e}")
    
    def execute_async(self, func: Callable, args: tuple = (), kwargs: dict = None,
                     callback_success: Callable = None, callback_error: Callable = None) -> str:
        """
        执行异步API调用
        
        Args:
            func: 要执行的异步函数
            args: 函数参数
            kwargs: 函数关键字参数
            callback_success: 成功回调函数，接收result参数
            callback_error: 失败回调函数，接收error_msg参数
            
        Returns:
            str: 请求ID
        """
        # 确保工作线程正在运行
        if not self._worker_thread or not self._worker_thread.isRunning():
            self._start_worker()
        
        # 生成请求ID
        request_id = self._generate_request_id()
        
        # 创建请求
        request = ApiRequest(
            request_id=request_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
            callback_success=callback_success,
            callback_error=callback_error
        )
        
        # 存储回调函数
        self._active_requests[request_id] = (callback_success, callback_error)
        
        # 添加到工作线程队列
        self._worker_thread.add_request(request)

        return request_id
    
    def reset_service(self):
        """重置服务状态"""
        
        # 清理活跃请求
        self._active_requests.clear()
        
        # 停止并重启工作线程
        self._stop_worker()
        self._start_worker()
        
        # 重置计数器
        self._request_counter = 0
    
    # 便捷方法
    def login(self, email: str, password: str, callback_success: Callable = None, 
             callback_error: Callable = None) -> str:
        """用户登录"""
        return self.execute_async(
            api_client.login,
            args=(email, password),
            callback_success=callback_success,
            callback_error=callback_error
        )
    
    def refresh_token(self, callback_success: Callable = None, callback_error: Callable = None) -> str:
        """刷新token"""
        return self.execute_async(
            api_client.refresh_session,
            callback_success=callback_success,
            callback_error=callback_error
        )
    
    def get_balance(self, callback_success: Callable = None, callback_error: Callable = None) -> str:
        """获取余额"""
        return self.execute_async(
            api_client.get_balance,
            callback_success=callback_success,
            callback_error=callback_error
        )
    
    def get_history(self, page: int = 1, page_size: int = 10, 
                   callback_success: Callable = None, callback_error: Callable = None) -> str:
        """获取交易历史"""
        return self.execute_async(
            api_client.get_history,
            args=(page, page_size),
            callback_success=callback_success,
            callback_error=callback_error
        )
    
    def get_token_coefficients(self, callback_success: Callable = None, 
                              callback_error: Callable = None) -> str:
        """获取算力消耗系数"""
        return self.execute_async(
            api_client.get_token_coefficients,
            callback_success=callback_success,
            callback_error=callback_error
        )


# 全局简化API服务实例
simple_api_service = SimpleApiService()
