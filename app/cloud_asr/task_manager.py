import json
import threading
import time
from pathlib import Path
from typing import Dict, Any

from app.cloud_asr.aliyun_asr_client import create_aliyun_asr_client
from app.cloud_asr.aliyun_oss_client import upload_file_for_asr
from app.core.base_task_manager import BaseTaskManager
from app.core.task_models import Task, TaskTokens
from app.core.task_status import TaskStatus
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from services.decorators import except_handler
from utils import logger
from utils.file_utils import funasr_write_srt_file


# ============================================
# 注意：ASRTask 已被 Task 替代（app/core/task_models.py）
# 代币数据现在属于 Task 对象
# ============================================


class AliyunASRTaskManager(BaseTaskManager):
    """阿里云ASR任务管理器"""

    def __init__(self):
        # 初始化基类
        task_state_file = Path(f"{config.temp_path}/aliyun_asr_tasks.json")
        super().__init__(task_state_file)

        # 阿里云特定属性
        self.polling_thread = None
        self.polling_active = False
        self.stop_polling = threading.Event()

        # 加载现有任务
        self._load_tasks()

        logger.trace("阿里云ASR任务管理器初始化完成")

    # ==================== 实现抽象方法 ====================

    def _serialize_task(self, task: Task) -> Dict[str, Any]:
        """
        序列化任务对象为字典

        使用 Task.to_dict() 方法（包含代币数据）
        """
        return task.to_dict()

    def _deserialize_task(self, task_data: Dict[str, Any]) -> Task:
        """
        从字典反序列化任务对象

        使用 Task.from_dict() 方法（包含代币数据）
        """
        return Task.from_dict(task_data)

    # ==================== 阿里云特定方法 ====================

    def create_task(self, task_id: str, audio_file: str, language: str, auto_billing: bool = True) -> str:
        """
        创建新的ASR任务

        使用新的 Task 类（包含代币数据）

        Args:
            task_id: 任务ID
            audio_file: 音频文件路径
            language: 语言代码
            auto_billing: 是否自动扣费（组合任务应设为False）
        """
        task = Task(
            task_id=task_id,
            audio_file=audio_file,
            language=language,
            status=TaskStatus.PENDING,
            tokens=TaskTokens(),  # 初始化代币数据
            auto_billing=auto_billing  # 保存自动扣费标志
        )

        with self.lock:
            self.tasks[task_id] = task

        self._save_tasks()
        return task_id

    @except_handler("ASR request failed", retry=5, delay=1)
    def submit_task(self, task_id: str):
        """
        提交任务到阿里云ASR

        Args:
            task_id: 任务ID
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        try:
            # 使用本地文件路径
            audio_file = task.audio_file

            # 计算并设置 ASR 代币（使用基类方法）
            try:
                self.calculate_and_set_asr_tokens(task_id)
                logger.info(f"ASR任务代币已设置: task_id={task_id}")
            except Exception as e:
                logger.warning(f"计算ASR代币失败，将在扣费时跳过: {str(e)}")

            # 检查是否为URL
            is_url = audio_file.startswith('http://') or audio_file.startswith('https://')

            # 如果是本地文件，先上传到OSS
            if not is_url:
                # 检查文件是否存在
                if not Path(audio_file).exists():
                    error_msg = f"文件不存在: {audio_file}"
                    logger.error(error_msg)
                    self.update_task(
                        task_id,
                        status=TaskStatus.FAILED,
                        error=error_msg,
                        progress=0
                    )
                    # 通知UI任务失败
                    self._notify_task_failed(task.task_id, error_msg)
                    return

                # 更新任务状态为上传中
                self.update_task(
                    task_id,
                    status=TaskStatus.UPLOADING,
                    progress=5
                )

                # 通知UI更新进度
                self._notify_task_progress(task.task_id, 5)

                # 定义进度回调函数
                def progress_callback(progress):
                    # 进度范围从5%到9%
                    task_progress = 5 + int(progress * 0.04)
                    self.update_task(task_id, progress=task_progress)
                    # 通知UI更新进度
                    self._notify_task_progress(task.task_id, task_progress)

                # 上传文件到OSS
                logger.info(f"开始上传文件到OSS: {audio_file}")
                success, url, error = upload_file_for_asr(
                    local_file_path=audio_file,
                    progress_callback=progress_callback,
                    expires=24 * 3600  # URL有效期24小时
                )

                if not success:
                    error_msg = f"上传文件失败: {error}"
                    logger.error(error_msg)
                    self.update_task(
                        task_id,
                        status=TaskStatus.FAILED,
                        error=error_msg,
                        progress=0
                    )
                    # 通知UI任务失败
                    self._notify_task_failed(task.task_id, error_msg)
                    return

                # 上传成功，更新文件URL
                logger.info(f"文件上传成功: {url}")
                self.update_task(
                    task_id,
                    audio_url=url,
                    progress=10
                )

                # 通知UI更新进度
                self._notify_task_progress(task.task_id, 10)

                # 使用生成的URL作为音频文件路径
                audio_file = url
            else:
                # 如果已经是URL，直接使用
                self.update_task(
                    task_id,
                    audio_url=audio_file,
                    progress=10
                )

                # 通知UI更新进度
                self._notify_task_progress(task.task_id, 10)

            # 创建阿里云ASR客户端
            client = create_aliyun_asr_client()

            # 提交任务
            logger.info(f"开始提交ASR任务 - 内部ID: {task_id}")
            response = client.submit_task(audio_file, task.language)

            # 保存响应对象
            task.response = response
            aliyun_task_id = response.output.task_id

            # 更新任务状态
            self.update_task(
                task_id,
                response=response,
                status=TaskStatus.SUBMITTED,
                progress=15
            )

            # 通知UI更新进度
            self._notify_task_progress(task.task_id, 15)

            logger.info(f"成功提交ASR任务 - 内部ID: {task_id}, 阿里云ID: {aliyun_task_id}")

            # 确保轮询线程正在运行
            self._ensure_polling_thread()

        except Exception as e:
            logger.error(f"提交ASR任务失败: {str(e)}")
            self.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=str(e)
            )
            # 通知UI任务失败
            self._notify_task_failed(task.task_id, str(e))

    def _ensure_polling_thread(self) -> None:
        """确保轮询线程正在运行"""
        if self.polling_thread is None or not self.polling_thread.is_alive():
            self.stop_polling.clear()
            self.polling_thread = threading.Thread(target=self._poll_tasks)
            self.polling_thread.daemon = True
            self.polling_thread.start()

    def _poll_tasks(self) -> None:  # sourcery skip: low-code-quality
        """轮询任务状态"""
        logger.info("启动ASR任务状态轮询线程")

        while not self.stop_polling.is_set():
            try:
                # 获取所有需要轮询的任务
                tasks_to_poll = []
                with self.lock:
                    tasks_to_poll.extend(
                        task
                        for task in self.tasks.values()
                        if task.status
                        in [TaskStatus.SUBMITTED, TaskStatus.RUNNING]
                        and task.response
                    )
                if not tasks_to_poll:
                    # 如果没有需要轮询的任务，等待一段时间后再检查
                    time.sleep(5)
                    continue

                # 创建阿里云ASR客户端
                client = create_aliyun_asr_client()
                logger.info(f'开始轮询 {len(tasks_to_poll)} 个ASR任务状态')

                # 轮询每个任务
                for task in tasks_to_poll:
                    try:
                        # 查询任务状态
                        aliyun_task_id = task.response.output.task_id if hasattr(task.response, 'output') else 'unknown'
                        logger.info(f'查询任务状态 - 内部ID: {task.task_id}, 阿里云ID: {aliyun_task_id}')
                        response = client.query_task(task.response)

                        # 更新任务状态
                        if response.output.task_status == 'RUNNING':
                            # 任务正在运行
                            # 进度从15%到90%
                            progress = min(15 + int((task.progress - 15) * 0.8), 90)
                            self.update_task(
                                task.task_id,
                                response=response,
                                status=TaskStatus.RUNNING,
                                progress=progress
                            )

                            # 通知UI更新进度
                            self._notify_task_progress(task.task_id, progress)
                        elif response.output.task_status == 'SUCCEEDED':
                            # 解析结果，获取转写结果的URL
                            transcription_url = client.parse_result(response)

                            # 下载转写结果文件（使用完整路径）
                            audio_path = Path(task.audio_file)
                            json_file_path = audio_path.with_name(f"{audio_path.stem}_asr_result.json")
                            saved_path = client.download_file(transcription_url, str(json_file_path))

                            # 更新任务状态为分词中
                            self.update_task(
                                task.task_id,
                                status=TaskStatus.SPLITING,
                                progress=92
                            )
                            self._notify_task_progress(task.task_id, 92)

                            # 读取下载的JSON文件
                            try:
                                with open(saved_path, 'r', encoding='utf-8') as f:
                                    json_data = json.load(f)
                            except Exception as e:
                                logger.error(f"读取ASR结果文件失败: {str(e)}")
                                raise

                            # 使用convert_to_segments_format转换格式
                            logger.info("开始转换ASR结果格式...")
                            segments = client.convert_to_segments_format(json_data)
                            logger.info(f"转换完成，得到 {len(segments)} 个segments")

                            # 更新进度
                            self.update_task(task.task_id, progress=95)
                            self._notify_task_progress(task.task_id, 95)

                            # 生成本地SRT文件（基础版本，不使用NLP分句）
                            srt_file_path = audio_path.with_suffix('.srt')
                            logger.info(f'生成本地SRT文件: {srt_file_path}')
                            funasr_write_srt_file(segments, str(srt_file_path))

                            # 更新进度
                            self.update_task(task.task_id, progress=97)
                            self._notify_task_progress(task.task_id, 97)

                            # 生成segment_data文件（供智能分句功能使用）
                            try:
                                segment_data_path = self._create_segment_data_file(segments, task.audio_file)
                                # 保存segment_data路径信息到工作对象中，供UI使用
                                self._save_segment_data_path(segment_data_path, task.audio_file, task.language)
                                logger.info(f"已生成segment_data文件，智能分句功能可用")
                            except Exception as e:
                                logger.warning(f"segment_data文件生成失败，智能分句功能将不可用: {str(e)}")

                            # 更新进度
                            self.update_task(task.task_id, progress=99)
                            self._notify_task_progress(task.task_id, 99)

                            # 更新任务状态为完成
                            self.update_task(
                                task.task_id,
                                response=response,
                                status=TaskStatus.COMPLETED,
                                progress=100
                            )

                            # 通知UI更新进度为100% - 使用线程安全的信号发送
                            data_bridge.whisper_working.emit(task.task_id, 100)

                            # 只有在自动扣费模式下才消费代币
                            if task.auto_billing:
                                logger.info(f'ASR任务自动扣费模式，开始扣费: {task.task_id}')
                                # 使用 BaseTaskManager 的统一扣费方法
                                file_name = Path(task.audio_file).stem
                                self._consume_tokens_for_task(task, "cloud_asr", file_name)
                            else:
                                logger.info(f'ASR任务非自动扣费模式，跳过扣费: {task.task_id}')
                                # 非自动扣费模式，只通知任务完成，不删除任务
                                self._notify_task_completed(task.task_id)

                            aliyun_task_id = response.output.task_id if hasattr(response, 'output') else 'unknown'
                            logger.info(f"ASR任务完成 - 内部ID: {task.task_id}, 阿里云ID: {aliyun_task_id}")
                        elif response.output.task_status == 'FAILED':
                            # 任务失败
                            error_msg = response.message if hasattr(response, 'message') else "未知错误"
                            self.update_task(
                                task.task_id,
                                response=response,
                                status=TaskStatus.FAILED,
                                error=error_msg,
                                progress=0
                            )
                            # 通知UI任务失败
                            self._notify_task_failed(task.task_id, error_msg)
                            aliyun_task_id = response.output.task_id if hasattr(response, 'output') else 'unknown'
                            logger.error(f"ASR任务失败 - 内部ID: {task.task_id}, 阿里云ID: {aliyun_task_id}, 错误: {error_msg}")
                    except Exception as e:
                        aliyun_task_id = task.response.output.task_id if hasattr(task.response, 'output') else 'unknown'
                        logger.error(f"轮询任务时出错 - 内部ID: {task.task_id}, 阿里云ID: {aliyun_task_id}, 错误: {str(e)}")

                # 等待一段时间后再次轮询
                time.sleep(5)

            except Exception as e:
                logger.error(f"任务轮询线程出错: {str(e)}")
                time.sleep(10)  # 出错后等待较长时间再重试

    def stop(self) -> None:
        """停止任务管理器"""
        self.stop_polling.set()
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=2)
        self._save_tasks()


# 全局任务管理器实例
_task_manager = None


def get_task_manager() -> AliyunASRTaskManager:
    """获取阿里云ASR任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = AliyunASRTaskManager()
    return _task_manager
