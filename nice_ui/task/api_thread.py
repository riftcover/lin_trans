import sys
import asyncio
import json
from typing import Optional, Dict, List, Callable, Any

from PySide6.QtCore import QObject, Signal, Slot, Qt, QThread

from api_client import APIClient
from utils import logger


class ApiSignals(QObject):
    """API信号管理"""
    data_received = Signal(str, dict)  # endpoint_name, data
    error_occurred = Signal(str, str)  # endpoint_name, error_message
    all_completed = Signal()


class ApiWorker(QThread):
    """API工作线程"""

    def __init__(self):
        super().__init__()
        self.signals = ApiSignals()
        self.client = APIClient()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.tasks: Dict[str, Callable] = {}  # 存储任务名称和对应的异步函数

    def add_task(self, name: str, task_func: Callable, *args, **kwargs):
        """
        添加API任务

        Args:
            name: 任务名称，用于标识结果
            task_func: 异步函数
            *args: 传递给异步函数的参数
            **kwargs: 传递给异步函数的关键字参数
        """
        self.tasks[name] = (task_func, args, kwargs)

    def clear_tasks(self):
        """清空任务列表"""
        self.tasks.clear()

    def run(self):
        """运行异步事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._fetch_all_data())
        except Exception as e:
            self.signals.error_occurred.emit("system", str(e))
        finally:
            self.loop.close()

    async def _fetch_all_data(self):
        """获取所有API数据"""
        if not self.tasks:
            logger.warning("No tasks added to ApiWorker")
            return

        # 创建所有任务
        async_tasks = {}
        for name, (task_func, args, kwargs) in self.tasks.items():
            async_tasks[name] = asyncio.create_task(task_func(*args, **kwargs))

        # 等待所有任务完成
        for name, task in async_tasks.items():
            try:
                result = await task
                self.signals.data_received.emit(name, result)
            except Exception as e:
                self.signals.error_occurred.emit(name, str(e))

        self.signals.all_completed.emit()
