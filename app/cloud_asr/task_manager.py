import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field, validator, field_validator
from pydantic.json import pydantic_encoder

from app.cloud_asr.aliyun_asr_client import create_aliyun_asr_client
from app.cloud_asr.aliyun_oss_client import upload_file_for_asr
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from utils import logger


class ASRTaskStatus:
    """ASR任务状态常量"""
    PENDING = "PENDING"  # 等待提交
    UPLOADING = "UPLOADING"  # 上传中
    SUBMITTED = "SUBMITTED"  # 已提交
    RUNNING = "RUNNING"  # 运行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败


class ASRTaskModel(BaseModel):
    """ASR任务数据模型"""
    task_id: str = Field(..., description="应用内唯一标识符")
    audio_file: str = Field(..., description="音频文件路径")
    audio_url: Optional[str] = Field(None, description="音频文件URL，上传到OSS后生成")
    language: str = Field(..., description="语言代码")
    status: str = Field(ASRTaskStatus.PENDING, description="任务状态")
    error: Optional[str] = Field(None, description="错误信息")
    progress: int = Field(0, description="任务进度（0-100）")
    created_at: float = Field(default_factory=time.time, description="创建时间")
    updated_at: float = Field(default_factory=time.time, description="更新时间")

    @field_validator('status')
    def validate_status(cls, v):
        """验证任务状态"""
        valid_statuses = [
            ASRTaskStatus.PENDING,
            ASRTaskStatus.UPLOADING,
            ASRTaskStatus.SUBMITTED,
            ASRTaskStatus.RUNNING,
            ASRTaskStatus.COMPLETED,
            ASRTaskStatus.FAILED
        ]
        if v not in valid_statuses:
            raise ValueError(f"无效的任务状态: {v}，有效状态: {valid_statuses}")
        return v

    @field_validator('progress')
    def validate_progress(cls, v):
        """验证任务进度"""
        if not isinstance(v, int) or v < 0 or v > 100:
            raise ValueError(f"无效的任务进度: {v}，进度必须是0-100之间的整数")
        return v

    class Config:
        arbitrary_types_allowed = True  # 允许任意类型
        json_encoders = {  # 自定义JSON编码器
            Path: lambda p: str(p),  # 将Path对象转换为字符串
        }


class ASRTask:
    """ASR任务对象"""

    def __init__(self, task_id: str, audio_file: str, language: str,):
        """
        初始化ASR任务

        Args:
            task_id: 应用内唯一标识符
            audio_file: 音频文件路径
            language: 语言代码
        """
        self.task_id = task_id
        self.audio_file = audio_file
        self.audio_url = None  # 音频文件URL，上传到OSS后生成
        self.language = language
        self.response = None  # 保存DashScope响应对象
        self.status = ASRTaskStatus.PENDING
        self.error = None
        self.progress = 0
        self.created_at = time.time()
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """
        将任务转换为字典，使用Pydantic模型进行验证和转换

        Returns:
            Dict: 任务字典
        """
        # 创建Pydantic模型
        model = ASRTaskModel(
            task_id=self.task_id,
            audio_file=self.audio_file,
            audio_url=self.audio_url,
            language=self.language,
            status=self.status,
            error=self.error,
            progress=self.progress,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

        # 转换为字典
        return model.model_dump(exclude_none=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ASRTask':
        """
        从字典创建任务，使用Pydantic模型进行验证和转换

        Args:
            data: 任务字典

        Returns:
            ASRTask: 任务对象

        Raises:
            ValidationError: 如果数据验证失败
        """
        # 使用Pydantic模型验证和转换数据
        model = ASRTaskModel(**data)

        # 创建ASRTask对象
        task = cls(
            task_id=model.task_id,
            audio_file=model.audio_file,
            language=model.language
        )

        # 设置其他属性
        task.audio_url = model.audio_url
        task.status = model.status
        task.progress = model.progress
        task.created_at = model.created_at
        task.updated_at = model.updated_at
        task.error = model.error

        return task


class ASRTaskManager:
    """ASR任务管理器，负责管理和跟踪ASR任务"""

    def __init__(self):
        """初始化任务管理器"""
        self.tasks: Dict[str, ASRTask] = {}
        self.lock = threading.Lock()
        self.polling_thread = None
        self.stop_polling = threading.Event()
        self.task_state_file = Path(config.root_path) / "tmp" / "asr_tasks.json"
        self._load_tasks()

    def _load_tasks(self) -> None:
        """从文件加载任务状态，使用Pydantic模型进行验证和转换"""
        if not self.task_state_file.exists():
            return
        try:
            with open(self.task_state_file, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)

            with self.lock:
                loaded_count = 0
                for task_data in tasks_data:
                    try:
                        # 使用Pydantic模型验证数据
                        model = ASRTaskModel(**task_data)
                        # 使用验证后的数据创建ASRTask对象
                        task = ASRTask.from_dict(model.model_dump())
                        self.tasks[task.task_id] = task
                        loaded_count += 1
                    except Exception as task_e:
                        logger.error(f"加载任务数据失败: {str(task_e)}")
                        # 尝试使用旧方法
                        try:
                            task = ASRTask.from_dict(task_data)
                            self.tasks[task.task_id] = task
                            loaded_count += 1
                        except Exception as fallback_e:
                            logger.error(f"使用旧方法加载任务数据也失败: {str(fallback_e)}")

            logger.info(f"从文件加载了 {loaded_count} 个ASR任务")
        except Exception as e:
            logger.error(f"加载ASR任务状态失败: {str(e)}")

    def _save_tasks(self) -> None:
        """保存任务状态到文件，使用Pydantic模型进行序列化"""
        try:
            with self.lock:
                # 使用Pydantic模型序列化任务数据
                tasks_data = []
                for task in self.tasks.values():
                    try:
                        # 创建Pydantic模型
                        model = ASRTaskModel(
                            task_id=task.task_id,
                            audio_file=task.audio_file,
                            audio_url=task.audio_url,
                            language=task.language,
                            status=task.status,
                            error=task.error,
                            progress=task.progress,
                            created_at=task.created_at,
                            updated_at=task.updated_at
                        )
                        # 转换为字典
                        tasks_data.append(model.model_dump(exclude_none=True))
                    except Exception as task_e:
                        logger.error(f"序列化任务数据失败: {str(task_e)}")
                        # 如果序列化失败，使用旧方法
                        tasks_data.append(task.to_dict())

            # 确保目录存在
            self.task_state_file.parent.mkdir(parents=True, exist_ok=True)

            # 使用自定义编码器序列化JSON
            with open(self.task_state_file, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2, default=pydantic_encoder)

            logger.debug(f"成功保存 {len(tasks_data)} 个ASR任务到文件")

        except Exception as e:
            logger.error(f"保存ASR任务状态失败: {str(e)}")

    def create_task(self, task_id: str, audio_file: str, language: str) -> str:
        """
        创建新的ASR任务

        Args:
            task_id: 应用内唯一标识符
            audio_file: 音频文件路径
            language: 语言代码

        Returns:
            str: 任务ID
        """
        # 确保语言代码是 'zh' 或 'en'

        task = ASRTask(task_id, audio_file, language)

        with self.lock:
            self.tasks[task_id] = task

        self._save_tasks()
        return task_id

    def get_task(self, task_id: str) -> Optional[ASRTask]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            Optional[ASRTask]: 任务对象，如果不存在则返回None
        """
        with self.lock:
            return self.tasks.get(task_id)

    def get_tasks_by_task_id(self, task_id: str) -> List[ASRTask]:
        """
        获取指定task_id的所有任务

        Args:
            task_id: 应用内唯一标识符

        Returns:
            List[ASRTask]: 任务列表
        """
        with self.lock:
            return [task for task in self.tasks.values() if task.task_id == task_id]

    def update_task(self, task_id: str, **kwargs) -> None:
        """
        更新任务

        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
        """
        with self.lock:
            if task := self.tasks.get(task_id):
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = time.time()

        self._save_tasks()

    def submit_task(self, task_id: str) -> None:
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

            # 检查是否为URL
            is_url = audio_file.startswith('http://') or audio_file.startswith('https://')

            # 如果是本地文件，先上传到OSS
            if not is_url:
                # 检查文件是否存在
                if not os.path.exists(audio_file):
                    error_msg = f"文件不存在: {audio_file}"
                    logger.error(error_msg)
                    self.update_task(
                        task_id,
                        status=ASRTaskStatus.FAILED,
                        error=error_msg,
                        progress=0
                    )
                    return

                # 更新任务状态为上传中
                self.update_task(
                    task_id,
                    status=ASRTaskStatus.UPLOADING,
                    progress=5
                )

                # 定义进度回调函数
                def progress_callback(progress):
                    # 进度范围从5%到9%
                    task_progress = 5 + int(progress * 0.04)
                    self.update_task(task_id, progress=task_progress)

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
                        status=ASRTaskStatus.FAILED,
                        error=error_msg,
                        progress=0
                    )
                    return

                # 上传成功，更新文件URL
                logger.info(f"文件上传成功: {url}")
                self.update_task(
                    task_id,
                    audio_url=url,
                    progress=10
                )

                # 使用生成的URL作为音频文件路径
                audio_file = url
            else:
                # 如果已经是URL，直接使用
                self.update_task(
                    task_id,
                    audio_url=audio_file,
                    progress=10
                )

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
                status=ASRTaskStatus.SUBMITTED,
                progress=15
            )

            logger.info(f"成功提交ASR任务 - 内部ID: {task_id}, 阿里云ID: {aliyun_task_id}")

            # 确保轮询线程正在运行
            self._ensure_polling_thread()

        except Exception as e:
            logger.error(f"提交ASR任务失败: {str(e)}")
            self.update_task(
                task_id,
                status=ASRTaskStatus.FAILED,
                error=str(e)
            )

    def _ensure_polling_thread(self) -> None:
        """确保轮询线程正在运行"""
        if self.polling_thread is None or not self.polling_thread.is_alive():
            self.stop_polling.clear()
            self.polling_thread = threading.Thread(target=self._poll_tasks)
            self.polling_thread.daemon = True
            self.polling_thread.start()

    def _poll_tasks(self) -> None:    # sourcery skip: low-code-quality
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
                        in [ASRTaskStatus.SUBMITTED, ASRTaskStatus.RUNNING]
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
                                status=ASRTaskStatus.RUNNING,
                                progress=progress
                            )
                        elif response.output.task_status == 'SUCCEEDED':
                            # 任务成功完成
                            # 解析结果，获取转写结果的URL
                            transcription_url = client.parse_result(response)

                            # 下载转写结果文件
                            json_file_path = f"{os.path.splitext(task.audio_file)[0]}_asr_result.json"
                            saved_path = client.download_file(transcription_url, json_file_path)

                            # # 读取下载的JSON文件
                            # try:
                            #     with open(saved_path, 'r', encoding='utf-8') as f:
                            #         result_data = json.load(f)
                            # except Exception as e:
                            #     logger.error(f"读取ASR结果文件失败: {str(e)}")
                            #     raise
                            #
                            # # 从结果中提取字幕信息并生成SRT文件
                            # srt_file_path = f"{os.path.splitext(task.audio_file)[0]}.srt"
                            #
                            # # 从结果中提取字幕信息
                            # parsed_results = []
                            # for sentence in result_data.get('sentences', []):
                            #     parsed_results.append({
                            #         "text": sentence.get("text", ""),
                            #         "begin_time": int(float(sentence.get("begin_time", 0)) * 1000),  # 转换为毫秒
                            #         "end_time": int(float(sentence.get("end_time", 0)) * 1000),  # 转换为毫秒
                            #     })
                            #
                            # # 生成SRT文件
                            # client.convert_to_srt(parsed_results, srt_file_path)

                            # 更新任务状态
                            self.update_task(
                                task.task_id,
                                response=response,
                                status=ASRTaskStatus.COMPLETED,
                                progress=100
                            )

                            # 通知UI任务完成
                            self._notify_task_completed(task.task_id)

                            aliyun_task_id = response.output.task_id if hasattr(response, 'output') else 'unknown'
                            logger.info(f"ASR任务完成 - 内部ID: {task.task_id}, 阿里云ID: {aliyun_task_id}")
                        elif response.output.task_status == 'FAILED':
                            # 任务失败
                            error_msg = response.message if hasattr(response, 'message') else "未知错误"
                            self.update_task(
                                task.task_id,
                                response=response,
                                status=ASRTaskStatus.FAILED,
                                error=error_msg,
                                progress=0
                            )
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

    def _notify_task_completed(self, task_id: Optional[str]) -> None:
        """
        通知UI任务完成

        Args:
            task_id: 应用内唯一标识符（可选）
        """
        try:
            # task_id，使用数据桥通知UI
            if task_id:
                data_bridge.emit_whisper_finished(task_id)
        except Exception as e:
            logger.error(f"通知任务完成失败: {str(e)}")

    def stop(self) -> None:
        """停止任务管理器"""
        self.stop_polling.set()
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=2)
        self._save_tasks()


# 单例模式
_task_manager_instance = None


def get_task_manager() -> ASRTaskManager:
    """
    获取任务管理器实例

    Returns:
        ASRTaskManager: 任务管理器实例
    """
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = ASRTaskManager()
    return _task_manager_instance
