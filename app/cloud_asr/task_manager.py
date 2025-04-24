import os
import time
import json
import threading
from typing import Dict, Any, Optional, List, Tuple, Callable
import uuid
from pathlib import Path

from app.cloud_asr import aliyun_sdk
from nice_ui.configure.signal import data_bridge
from utils import logger
from nice_ui.configure import config
from app.cloud_asr.aliyun_asr_client import create_aliyun_asr_client
from utils.file_utils import Segment


class ASRTaskStatus:
    """ASR任务状态常量"""
    PENDING = "PENDING"  # 等待提交
    SUBMITTED = "SUBMITTED"  # 已提交
    RUNNING = "RUNNING"  # 运行中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败


class ASRTask:
    """ASR任务对象"""

    def __init__(self, task_id: str, audio_file: str, language: str, unid: str):
        """
        初始化ASR任务

        Args:
            task_id: 任务ID
            audio_file: 音频文件路径
            language: 语言代码
            unid: 应用内唯一标识符
        """
        self.task_id = task_id
        self.audio_file = audio_file
        self.language = language
        self.unid = unid
        self.response = None  # 保存DashScope响应对象
        self.status = ASRTaskStatus.PENDING
        self.result = None
        self.error = None
        self.progress = 0
        self.created_at = time.time()
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """
        将任务转换为字典

        Returns:
            Dict: 任务字典
        """
        return {
            "task_id": self.task_id,
            "audio_file": self.audio_file,
            "language": self.language,
            "unid": self.unid,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ASRTask':
        """
        从字典创建任务

        Args:
            data: 任务字典

        Returns:
            ASRTask: 任务对象
        """
        task = cls(
            task_id=data["task_id"],
            audio_file=data["audio_file"],
            language=data["language"],
            unid=data["unid"]
        )
        task.status = data.get("status", ASRTaskStatus.PENDING)
        task.progress = data.get("progress", 0)
        task.created_at = data.get("created_at", time.time())
        task.updated_at = data.get("updated_at", time.time())
        task.error = data.get("error")
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
        """从文件加载任务状态"""
        if self.task_state_file.exists():
            try:
                with open(self.task_state_file, "r", encoding="utf-8") as f:
                    tasks_data = json.load(f)

                with self.lock:
                    for task_data in tasks_data:
                        task = ASRTask.from_dict(task_data)
                        self.tasks[task.task_id] = task

                logger.info(f"从文件加载了 {len(tasks_data)} 个ASR任务")
            except Exception as e:
                logger.error(f"加载ASR任务状态失败: {str(e)}")

    def _save_tasks(self) -> None:
        """保存任务状态到文件"""
        try:
            with self.lock:
                tasks_data = [task.to_dict() for task in self.tasks.values()]

            # 确保目录存在
            self.task_state_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.task_state_file, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存ASR任务状态失败: {str(e)}")

    def create_task(self, audio_file: str, language: str, unid: str) -> str:
        """
        创建新的ASR任务

        Args:
            audio_file: 音频文件路径
            language: 语言代码
            unid: 应用内唯一标识符

        Returns:
            str: 任务ID
        """
        # 确保语言代码是 'zh' 或 'en'

        task_id = str(uuid.uuid4())
        task = ASRTask(task_id, audio_file, language, unid)

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

    def get_tasks_by_unid(self, unid: str) -> List[ASRTask]:
        """
        获取指定unid的所有任务

        Args:
            unid: 应用内唯一标识符

        Returns:
            List[ASRTask]: 任务列表
        """
        with self.lock:
            return [task for task in self.tasks.values() if task.unid == unid]

    def update_task(self, task_id: str, **kwargs) -> None:
        """
        更新任务

        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
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
            # 创建阿里云ASR客户端
            client = create_aliyun_asr_client()

            # 使用本地文件路径
            audio_file = task.audio_file

            # 检查是否为URL
            is_url = audio_file.startswith('http://') or audio_file.startswith('https://')
            if not is_url:
                # 如果不是URL，将任务状态设置为失败
                error_msg = "不支持本地文件，请提供有效的URL地址"
                logger.error(error_msg)
                self.update_task(
                    task_id,
                    status=ASRTaskStatus.FAILED,
                    error=error_msg,
                    progress=0
                )
                return

            # 提交任务
            logger.info(f"提交ASR任务: {task_id} -> {audio_file}")
            response = client.submit_task(audio_file, task.language)

            # 保存响应对象
            task.response = response

            # 更新任务状态
            self.update_task(
                task_id,
                response=response,
                status=ASRTaskStatus.SUBMITTED,
                progress=10
            )

            logger.info(f"成功提交ASR任务: {task_id} -> {response.output.task_id}")

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
                    for task in self.tasks.values():
                        if (task.status == ASRTaskStatus.SUBMITTED or
                            task.status == ASRTaskStatus.RUNNING) and task.response:
                            tasks_to_poll.append(task)

                if not tasks_to_poll:
                    # 如果没有需要轮询的任务，等待一段时间后再检查
                    time.sleep(5)
                    continue

                # 创建阿里云ASR客户端
                client = create_aliyun_asr_client()

                # 轮询每个任务
                for task in tasks_to_poll:
                    try:
                        # 查询任务状态
                        response = client.query_task(task.response)

                        # 更新任务状态
                        if response.output.task_status == 'RUNNING':
                            # 任务正在运行
                            progress = min(50 + int(task.progress * 0.4), 90)
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
                            result_data =client.download_file(transcription_url, json_file_path)

                            # 从结果中提取字幕信息并生成SRT文件
                            srt_file_path = f"{os.path.splitext(task.audio_file)[0]}.srt"

                            # 从结果中提取字幕信息
                            parsed_results = []
                            for sentence in result_data.get('sentences', []):
                                parsed_results.append({
                                    "text": sentence.get("text", ""),
                                    "begin_time": int(float(sentence.get("begin_time", 0)) * 1000),  # 转换为毫秒
                                    "end_time": int(float(sentence.get("end_time", 0)) * 1000),  # 转换为毫秒
                                })

                            # 生成SRT文件
                            client.convert_to_srt(parsed_results, srt_file_path)

                            # 更新任务状态
                            self.update_task(
                                task.task_id,
                                response=response,
                                status=ASRTaskStatus.COMPLETED,
                                result=parsed_results,
                                progress=100
                            )

                            # 通知UI任务完成
                            self._notify_task_completed(task.unid)

                            logger.info(f"ASR任务完成: {task.task_id}")
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
                            logger.error(f"ASR任务失败: {task.task_id}, 错误: {error_msg}")
                    except Exception as e:
                        logger.error(f"轮询任务 {task.task_id} 时出错: {str(e)}")

                # 等待一段时间后再次轮询
                time.sleep(5)

            except Exception as e:
                logger.error(f"任务轮询线程出错: {str(e)}")
                time.sleep(10)  # 出错后等待较长时间再重试

    def _notify_task_completed(self, unid: str) -> None:
        """
        通知UI任务完成

        Args:
            unid: 应用内唯一标识符
        """
        try:
            # 使用数据桥通知UI
            data_bridge.emit_whisper_finished(unid)
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
