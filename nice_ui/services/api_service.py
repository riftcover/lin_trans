"""
统一的API调用服务
提供线程安全的异步API调用，避免阻塞主线程
"""
import asyncio
import threading
from typing import Optional, Dict, Callable, Any
from enum import Enum

from PySide6.QtCore import QObject, Signal, QThread, QMutex, QMutexLocker

from api_client import api_client
from utils import logger


class ApiTaskType(Enum):
    """API任务类型枚举"""
    SINGLE = "single"  # 单个任务
    BATCH = "batch"   # 批量任务


class ApiSignals(QObject):
    """API信号管理"""
    # 单个任务完成信号
    task_completed = Signal(str, dict)  # task_id, result
    task_failed = Signal(str, str)      # task_id, error_message
    
    # 批量任务信号
    batch_task_completed = Signal(str, dict)  # task_name, result
    batch_task_failed = Signal(str, str)      # task_name, error_message
    batch_all_completed = Signal(str)         # batch_id
    
    # 通用信号
    worker_finished = Signal()


class ApiTask:
    """API任务封装"""
    def __init__(self, task_id: str, func: Callable, args: tuple = (), kwargs: dict = None):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}


class ApiWorkerThread(QThread):
    """API工作线程 - 支持单个任务和批量任务"""
    
    def __init__(self, task_type: ApiTaskType):
        super().__init__()
        self.signals = ApiSignals()
        self.task_type = task_type
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # 单个任务模式
        self.single_task: Optional[ApiTask] = None
        
        # 批量任务模式
        self.batch_id: str = ""
        self.batch_tasks: Dict[str, ApiTask] = {}
    
    def set_single_task(self, task: ApiTask):
        """设置单个任务"""
        self.single_task = task
    
    def set_batch_tasks(self, batch_id: str, tasks: Dict[str, ApiTask]):
        """设置批量任务"""
        self.batch_id = batch_id
        self.batch_tasks = tasks
    
    def run(self):
        """运行异步事件循环"""
        self.loop = None
        thread_id = threading.get_ident()
        logger.debug(f"ApiWorkerThread {thread_id} starting...")

        try:
            # 创建新的事件循环，使用线程ID作为标识
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # 添加延迟以避免并发冲突
            import time
            time.sleep(0.01)  # 10ms延迟

            # 确保事件循环正常运行
            if self.loop.is_closed():
                logger.error(f"Event loop {thread_id} is already closed")
                self._emit_task_failed("Event loop is closed")
                return

            logger.debug(f"Event loop {thread_id} created successfully")

            if self.task_type == ApiTaskType.SINGLE:
                self.loop.run_until_complete(self._execute_single_task())
            else:
                self.loop.run_until_complete(self._execute_batch_tasks())

        except RuntimeError as e:
            error_msg = str(e)
            if "Event loop is closed" in error_msg:
                logger.warning(f"Event loop {thread_id} was closed during execution: {e}")
                self._emit_task_failed("Event loop was closed during execution")
            elif "cannot be called from a running event loop" in error_msg:
                logger.warning(f"Event loop {thread_id} conflict: {e}")
                self._emit_task_failed("Event loop conflict")
            else:
                logger.error(f"ApiWorkerThread {thread_id} runtime error: {e}")
                self._emit_task_failed(error_msg)
        except Exception as e:
            logger.error(f"ApiWorkerThread {thread_id} error: {e}")
            self._emit_task_failed(str(e))
        finally:
            # 安全关闭事件循环
            self._safe_close_loop()
            logger.debug(f"ApiWorkerThread {thread_id} finished")
            self.signals.worker_finished.emit()

    def _execute_task_sync(self):
        """同步执行任务（作为事件循环失败时的备选方案）"""
        try:
            if self.task_type == ApiTaskType.SINGLE and self.single_task:
                # 对于单个任务，尝试同步执行
                task = self.single_task
                if hasattr(task.func, '__call__'):
                    # 如果是异步函数，我们无法同步执行，只能报错
                    import inspect
                    if inspect.iscoroutinefunction(task.func):
                        raise RuntimeError("Cannot execute async function synchronously")
                    else:
                        # 同步函数可以直接执行
                        result = task.func(*task.args, **task.kwargs)
                        self.signals.task_completed.emit(task.task_id, result)
                        return

            # 如果无法同步执行，发出失败信号
            self._emit_task_failed("Cannot execute task synchronously")

        except Exception as e:
            logger.error(f"Sync task execution failed: {e}")
            self._emit_task_failed(str(e))

    def _emit_task_failed(self, error_message: str):
        """发出任务失败信号"""
        if self.task_type == ApiTaskType.SINGLE and self.single_task:
            self.signals.task_failed.emit(self.single_task.task_id, error_message)
        else:
            self.signals.batch_task_failed.emit("system", error_message)

    def _safe_close_loop(self):
        """安全关闭事件循环"""
        if self.loop:
            try:
                if not self.loop.is_closed():
                    # 取消所有待处理的任务
                    pending = asyncio.all_tasks(self.loop)
                    for task in pending:
                        task.cancel()

                    # 关闭事件循环
                    self.loop.close()
            except Exception as e:
                logger.warning(f"Error closing event loop: {e}")
            finally:
                self.loop = None
    
    async def _execute_single_task(self):
        """执行单个任务"""
        if not self.single_task:
            logger.warning("No single task to execute")
            return
        
        task = self.single_task
        try:
            result = await task.func(*task.args, **task.kwargs)
            self.signals.task_completed.emit(task.task_id, result)
        except Exception as e:
            logger.error(f"Single task {task.task_id} failed: {e}")
            self.signals.task_failed.emit(task.task_id, str(e))
    
    async def _execute_batch_tasks(self):
        """执行批量任务"""
        if not self.batch_tasks:
            logger.warning("No batch tasks to execute")
            return
        
        # 创建所有异步任务
        async_tasks = {}
        for name, task in self.batch_tasks.items():
            async_tasks[name] = asyncio.create_task(task.func(*task.args, **task.kwargs))
        
        # 等待所有任务完成
        for name, async_task in async_tasks.items():
            try:
                result = await async_task
                self.signals.batch_task_completed.emit(name, result)
            except Exception as e:
                logger.error(f"Batch task {name} failed: {e}")
                self.signals.batch_task_failed.emit(name, str(e))
        
        self.signals.batch_all_completed.emit(self.batch_id)


class ApiService(QObject):
    """统一的API调用服务 - 单例模式"""
    
    _instance = None
    _mutex = QMutex()
    
    def __new__(cls):
        with QMutexLocker(cls._mutex):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        
        # 工作线程管理
        self._active_workers: Dict[str, ApiWorkerThread] = {}
        self._task_counter = 0
        self._max_concurrent_workers = 2  # 进一步限制最大并发工作线程数

        # 任务队列管理
        self._pending_tasks = []  # 待执行的任务队列
        self._is_processing_queue = False  # 是否正在处理队列
        
        logger.info("ApiService initialized")
    
    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        self._task_counter += 1
        return f"api_task_{self._task_counter}"
    
    def execute_single_task(self, func: Callable, args: tuple = (), kwargs: dict = None,
                          task_id: str = None) -> str:
        """
        执行单个API任务

        Args:
            func: 要执行的异步函数
            args: 函数参数
            kwargs: 函数关键字参数
            task_id: 任务ID，如果不提供则自动生成

        Returns:
            str: 任务ID
        """
        if task_id is None:
            task_id = self._generate_task_id()

        # 检查并发限制
        active_count = len([w for w in self._active_workers.values() if w.isRunning()])
        if active_count >= self._max_concurrent_workers:
            logger.info(f"Queueing task {task_id} due to concurrency limit ({active_count} active)")
            # 将任务加入队列
            self._pending_tasks.append((task_id, func, args, kwargs or {}))
            self._process_task_queue()  # 尝试处理队列
            return task_id

        # 创建任务
        task = ApiTask(task_id, func, args, kwargs or {})

        # 创建工作线程
        worker = ApiWorkerThread(ApiTaskType.SINGLE)
        worker.set_single_task(task)

        # 存储工作线程引用
        self._active_workers[task_id] = worker

        # 连接信号
        worker.signals.worker_finished.connect(lambda: self._on_worker_finished(task_id))

        # 启动线程
        worker.start()

        logger.debug(f"Started single API task: {task_id}")
        return task_id
    
    def execute_batch_tasks(self, tasks: Dict[str, tuple], batch_id: str = None) -> str:
        """
        执行批量API任务
        
        Args:
            tasks: 任务字典，格式为 {task_name: (func, args, kwargs)}
            batch_id: 批次ID，如果不提供则自动生成
            
        Returns:
            str: 批次ID
        """
        if batch_id is None:
            batch_id = self._generate_task_id()
        
        # 创建任务对象
        api_tasks = {}
        for name, (func, args, kwargs) in tasks.items():
            api_tasks[name] = ApiTask(f"{batch_id}_{name}", func, args, kwargs)
        
        # 创建工作线程
        worker = ApiWorkerThread(ApiTaskType.BATCH)
        worker.set_batch_tasks(batch_id, api_tasks)
        
        # 存储工作线程引用
        self._active_workers[batch_id] = worker
        
        # 连接信号
        worker.signals.worker_finished.connect(lambda: self._cleanup_worker(batch_id))
        
        # 启动线程
        worker.start()
        
        logger.debug(f"Started batch API tasks: {batch_id}")
        return batch_id
    
    def _cleanup_worker(self, worker_id: str):
        """清理完成的工作线程"""
        if worker_id in self._active_workers:
            worker = self._active_workers.pop(worker_id)
            worker.deleteLater()
            logger.debug(f"Cleaned up worker: {worker_id}")

    def _on_worker_finished(self, worker_id: str):
        """工作线程完成时的处理"""
        self._cleanup_worker(worker_id)
        # 尝试处理队列中的下一个任务
        self._process_task_queue()

    def _process_task_queue(self):
        """处理任务队列"""
        if self._is_processing_queue or not self._pending_tasks:
            return

        self._is_processing_queue = True

        try:
            # 检查是否可以启动新任务
            active_count = len([w for w in self._active_workers.values() if w.isRunning()])

            while self._pending_tasks and active_count < self._max_concurrent_workers:
                # 从队列中取出任务
                task_id, func, args, kwargs = self._pending_tasks.pop(0)

                logger.debug(f"Processing queued task: {task_id}")

                # 创建任务
                task = ApiTask(task_id, func, args, kwargs)

                # 创建工作线程
                worker = ApiWorkerThread(ApiTaskType.SINGLE)
                worker.set_single_task(task)

                # 存储工作线程引用
                self._active_workers[task_id] = worker

                # 连接信号
                worker.signals.worker_finished.connect(lambda tid=task_id: self._on_worker_finished(tid))

                # 启动线程
                worker.start()

                active_count += 1
                logger.debug(f"Started queued API task: {task_id}")

        finally:
            self._is_processing_queue = False

    def _cleanup_finished_workers(self):
        """清理所有已完成的工作线程"""
        finished_workers = []
        for worker_id, worker in self._active_workers.items():
            if worker.isFinished():
                finished_workers.append(worker_id)

        for worker_id in finished_workers:
            self._cleanup_worker(worker_id)

        if finished_workers:
            logger.debug(f"Cleaned up {len(finished_workers)} finished workers")
    
    def get_worker_signals(self, worker_id: str) -> Optional[ApiSignals]:
        """获取指定工作线程的信号对象"""
        worker = self._active_workers.get(worker_id)
        return worker.signals if worker else None

    def reset_service(self):
        """重置API服务状态，清理所有活跃的工作线程"""
        logger.info("Resetting API service...")

        # 停止并清理所有活跃的工作线程
        for worker_id, worker in list(self._active_workers.items()):
            try:
                if worker.isRunning():
                    worker.quit()
                    worker.wait(1000)  # 等待最多1秒
                worker.deleteLater()
            except Exception as e:
                logger.warning(f"Error cleaning up worker {worker_id}: {e}")

        self._active_workers.clear()
        self._task_counter = 0

        # 清理任务队列
        self._pending_tasks.clear()
        self._is_processing_queue = False

        logger.info("API service reset completed")
    
    # 便捷方法 - 常用API调用
    def refresh_token(self, callback_success: Callable = None, callback_error: Callable = None) -> str:
        """刷新token"""
        task_id = self.execute_single_task(api_client.refresh_session)
        
        if callback_success or callback_error:
            signals = self.get_worker_signals(task_id)
            if signals:
                if callback_success:
                    signals.task_completed.connect(lambda tid, result: callback_success(result))
                if callback_error:
                    signals.task_failed.connect(lambda tid, error: callback_error(error))
        
        return task_id
    
    def get_balance(self, callback_success: Callable = None, callback_error: Callable = None) -> str:
        """获取余额"""
        task_id = self.execute_single_task(api_client.get_balance)
        
        if callback_success or callback_error:
            signals = self.get_worker_signals(task_id)
            if signals:
                if callback_success:
                    signals.task_completed.connect(lambda tid, result: callback_success(result))
                if callback_error:
                    signals.task_failed.connect(lambda tid, error: callback_error(error))
        
        return task_id
    
    def create_recharge_order(self, user_id: str, price: float, amount: int,
                            callback_success: Callable = None, callback_error: Callable = None) -> str:
        """创建充值订单"""
        task_id = self.execute_single_task(
            api_client.create_recharge_order, 
            args=(user_id, price, amount)
        )
        
        if callback_success or callback_error:
            signals = self.get_worker_signals(task_id)
            if signals:
                if callback_success:
                    signals.task_completed.connect(lambda tid, result: callback_success(result))
                if callback_error:
                    signals.task_failed.connect(lambda tid, error: callback_error(error))
        
        return task_id
    
    def get_order_status(self, order_id: str, callback_success: Callable = None, 
                        callback_error: Callable = None) -> str:
        """获取订单状态"""
        task_id = self.execute_single_task(
            api_client.get_order_status,
            args=(order_id,)
        )
        
        if callback_success or callback_error:
            signals = self.get_worker_signals(task_id)
            if signals:
                if callback_success:
                    signals.task_completed.connect(lambda tid, result: callback_success(result))
                if callback_error:
                    signals.task_failed.connect(lambda tid, error: callback_error(error))
        
        return task_id


# 全局API服务实例
api_service = ApiService()
