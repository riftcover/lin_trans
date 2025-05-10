import sys
import asyncio
import json
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, Qt, QThread

from api_client import APIClient


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

    def run(self):
        """运行异步事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._fetch_all_data())
        except Exception as e:
            self.signals.error_occurred.emit("system", str(e))
        finally:
            # 确保清理HTTP客户端
            if self.loop.is_running():
                self.loop.run_until_complete(self.client.cleanup())
            self.loop.close()

    async def _fetch_all_data(self):
        """获取所有API数据"""
        # 初始化HTTP客户端
        await self.client.initialize()

        tasks = {
            "version": asyncio.create_task(self.client.check_version('windows', '1.0.0')),
            # "profile": asyncio.create_task(self.client.get_profile())
        }

        for name, task in tasks.items():
            try:
                result = await task
                self.signals.data_received.emit(name, result)
            except Exception as e:
                self.signals.error_occurred.emit(name, str(e))

        # 清理HTTP客户端
        await self.client.cleanup()
        self.signals.all_completed.emit()
