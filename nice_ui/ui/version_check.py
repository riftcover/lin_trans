import asyncio
from PySide6.QtCore import QThread, Signal
from utils import logger
from api_client import api_client

class VersionCheckThread(QThread):
    """版本检查线程 - 支持异步API调用"""

    # 多个API结果信号，用于将来扩展
    api_result = Signal(str, dict)  # endpoint_name, result
    api_error = Signal(str, str)    # endpoint_name, error_message
    all_apis_complete = Signal()
    
    # 单个API模式的信号
    version_check_complete = Signal(dict)  # 版本检查结果

    def __init__(self, platform, current_version, multi_api_mode=False):
        super().__init__()
        self.platform = platform
        self.current_version = current_version
        self.loop = None
        self.multi_api_mode = multi_api_mode  # 是否使用多个API模式

    def run(self):
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            if self.multi_api_mode:
                # 多个API模式，并发调用多个API
                self.loop.run_until_complete(self._fetch_multiple_apis())
            else:
                # 单个API模式，只调用版本检查API
                result = self.loop.run_until_complete(self._fetch_data())
                self.version_check_complete.emit(result)
        except Exception as e:
            logger.error(f"版本检查线程出错: {str(e)}")
            # 模拟一个错误响应，以便于前端处理
            error_response = {
                "code": 500,
                "message": "error",
                "data": {
                    "status": "VERSION_CHECK_FAILED",
                    "detail": str(e)
                }
            }
            if not self.multi_api_mode:
                self.version_check_complete.emit(error_response)
            else:
                self.api_error.emit("version", str(e))
                self.all_apis_complete.emit()
        finally:
            # 关闭事件循环
            if self.loop:
                self.loop.close()

    def run_multi_api_mode(self):
        """在多个API模式下运行线程"""
        self.multi_api_mode = True
        self.start()

    async def _fetch_data(self):
        """获取数据的异步方法，当前只调用版本检查API"""
        # 创建异步任务
        tasks = {
            "version": asyncio.create_task(api_client.check_version(self.platform, self.current_version))
        }

        # 当前只返回版本检查结果
        try:
            return await tasks["version"]
        except Exception as e:
            logger.error(f"版本检查API调用失败: {str(e)}")
            raise

    async def _fetch_multiple_apis(self):
        """并发调用多个API并处理结果 - 用于将来扩展"""
        # 创建多个异步任务
        tasks = {
            "version": asyncio.create_task(api_client.check_version(self.platform, self.current_version)),
            # 将来可以添加更多的API调用，例如：
            # "profile": asyncio.create_task(api_client.get_profile())
        }

        # 使用 as_completed 处理完成的任务
        for task_name, task in tasks.items():
            try:
                # 等待任务完成
                result = await task
                # 发送结果信号
                self.api_result.emit(task_name, result)
            except Exception as e:
                logger.error(f"API {task_name} 调用失败: {str(e)}")
                self.api_error.emit(task_name, str(e))

        # 所有API调用完成
        self.all_apis_complete.emit()
