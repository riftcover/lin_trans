"""
Gladia ASR 任务管理器
"""

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field
from pydantic.json import pydantic_encoder

from app.cloud_asr.gladia_asr_client import GladiaASRClient, create_config, creat_gladia_asr_client
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge

from utils import logger
from utils.file_utils import funasr_write_srt_file


class ASRTaskStatus:
    """ASR任务状态常量"""
    PENDING = "PENDING"  # 等待处理
    UPLOADING = "UPLOADING"  # 上传中
    SUBMITTED = "SUBMITTED"  # 已提交
    PROCESSING = "PROCESSING"  # 处理中
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败


class ASRTask:
    """ASR任务对象"""

    def __init__(self, task_id: str, audio_file: str, language: str):
        self.task_id = task_id
        self.audio_file = audio_file
        self.audio_url = None  # Gladia音频URL
        self.result_url = None  # Gladia结果URL
        self.language = language
        self.status = ASRTaskStatus.PENDING
        self.error = None
        self.progress = 0
        self.created_at = time.time()
        self.updated_at = time.time()
        self.auto_billing = True


class GladiaTaskManager:
    """Gladia ASR任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, ASRTask] = {}
        self.lock = threading.Lock()
        self.polling_thread = None
        self.polling_active = False
        self.tasks_file = Path("tmp/asr_tasks.json")

        # 确保目录存在
        self.tasks_file.parent.mkdir(exist_ok=True)

        # 加载现有任务
        self._load_tasks()

        logger.trace("Gladia ASR任务管理器初始化完成")

    def create_task(self, task_id: str, audio_file: str, language: str, auto_billing: bool = True) -> str:
        """创建新的ASR任务"""
        task = ASRTask(task_id, audio_file, language)
        task.auto_billing = auto_billing

        with self.lock:
            self.tasks[task_id] = task

        self._save_tasks()
        return task_id

    def get_task(self, task_id: str) -> Optional[ASRTask]:
        """获取任务"""
        with self.lock:
            return self.tasks.get(task_id)

    def submit_task(self, task_id: str):
        """提交任务到Gladia"""
        task = self.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        try:
            # 创建Gladia客户端
            client = creat_gladia_asr_client()

            # 更新任务状态
            self.update_task(task_id, status=ASRTaskStatus.UPLOADING, progress=5)
            self._notify_task_progress(task.task_id, 5)

            # 上传音频文件
            logger.info(f"开始上传音频文件 - 任务ID: {task_id}")
            audio_url = client.upload_audio(task.audio_file)

            # 更新任务状态
            self.update_task(task_id, audio_url=audio_url, status=ASRTaskStatus.SUBMITTED, progress=15)
            self._notify_task_progress(task.task_id, 15)

            # 提交转录任务
            logger.info(f"开始提交转录任务 - 任务ID: {task_id}")
            config_dict = create_config(diarization=False)  # 简化配置
            result_url = client.submit_transcription(audio_url, config_dict)

            # 更新任务状态
            self.update_task(
                task_id,
                result_url=result_url,
                status=ASRTaskStatus.PROCESSING,
                progress=25
            )
            self._notify_task_progress(task.task_id, 25)

            logger.info(f"成功提交ASR任务 - 内部ID: {task_id}, Gladia结果URL: {result_url}")

            # 确保轮询线程正在运行
            self._ensure_polling_thread()

        except Exception as e:
            logger.error(f"提交ASR任务失败: {str(e)}")
            self.update_task(
                task_id,
                status=ASRTaskStatus.FAILED,
                error=str(e)
            )
            self._notify_task_failed(task.task_id, str(e))

    def update_task(self, task_id: str, **kwargs):
        """更新任务信息"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = time.time()
                self._save_tasks()

    def _load_tasks(self):
        """从文件加载任务"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)

                for task_data in tasks_data:
                    task = ASRTask(
                        task_data['task_id'],
                        task_data['audio_file'],
                        task_data['language']
                    )
                    # 恢复任务状态
                    for key, value in task_data.items():
                        if hasattr(task, key):
                            setattr(task, key, value)

                    self.tasks[task.task_id] = task

                logger.info(f"加载了 {len(self.tasks)} 个任务")
            except Exception as e:
                logger.error(f"加载任务失败: {e}")

    def _save_tasks(self):
        """保存任务到文件"""
        try:
            tasks_data = []
            for task in self.tasks.values():
                task_dict = {
                    'task_id': task.task_id,
                    'audio_file': task.audio_file,
                    'audio_url': task.audio_url,
                    'result_url': task.result_url,
                    'language': task.language,
                    'status': task.status,
                    'error': task.error,
                    'progress': task.progress,
                    'created_at': task.created_at,
                    'updated_at': task.updated_at
                }
                tasks_data.append(task_dict)

            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务失败: {e}")

    def _ensure_polling_thread(self):
        """确保轮询线程正在运行"""
        if not self.polling_thread or not self.polling_thread.is_alive():
            self.polling_active = True
            self.polling_thread = threading.Thread(target=self._polling_worker, daemon=True)
            self.polling_thread.start()
            logger.info("启动任务轮询线程")

    def _polling_worker(self):
        """轮询工作线程"""
        api_key = config.params.get("gladia_api_key", "")
        client = GladiaASRClient(api_key) if api_key else None

        while self.polling_active:
            try:
                if not client:
                    time.sleep(5)
                    continue

                processing_tasks = []
                with self.lock:
                    processing_tasks = [
                        task for task in self.tasks.values()
                        if task.status == ASRTaskStatus.PROCESSING and task.result_url
                    ]

                for task in processing_tasks:
                    try:
                        result = client.get_result(task.result_url)
                        status = result.get('status')

                        if status == 'done':
                            self._handle_task_completion(task, result, client)
                        elif status == 'error':
                            error_msg = result.get('error', '未知错误')
                            self.update_task(task.task_id, status=ASRTaskStatus.FAILED, error=error_msg)
                            self._notify_task_failed(task.task_id, error_msg)
                        else:
                            # 更新进度
                            progress = min(90, task.progress + 5)
                            self.update_task(task.task_id, progress=progress)
                            self._notify_task_progress(task.task_id, progress)

                    except Exception as e:
                        logger.error(f"轮询任务 {task.task_id} 失败: {e}")

                time.sleep(2)  # 2秒轮询一次

            except Exception as e:
                logger.error(f"轮询线程异常: {e}")
                time.sleep(5)

    def _handle_task_completion(self, task: ASRTask, result: Dict, client: GladiaASRClient):
        """处理任务完成"""
        try:
            # 获取转录结果
            segments = client.get_segments(result)

            if segments:
                # 生成SRT文件
                srt_file_path = f"{os.path.splitext(task.audio_file)[0]}.srt"
                funasr_write_srt_file(segments, srt_file_path)

                # 更新任务状态
                self.update_task(task.task_id, status=ASRTaskStatus.COMPLETED, progress=100)
                self._notify_task_completed(task.task_id)

                logger.info(f"任务完成 - ID: {task.task_id}, SRT文件: {srt_file_path}")
            else:
                raise Exception("转录结果为空")

        except Exception as e:
            logger.error(f"处理任务完成失败: {e}")
            self.update_task(task.task_id, status=ASRTaskStatus.FAILED, error=str(e))
            self._notify_task_failed(task.task_id, str(e))

    def _notify_task_progress(self, task_id: str, progress: int):
        """通知任务进度"""
        data_bridge.emit_whisper_working(task_id, progress)

    def _notify_task_completed(self, task_id: str):
        """通知任务完成"""
        data_bridge.emit_whisper_finished(task_id)

    def _notify_task_failed(self, task_id: str, error: str):
        """通知任务失败"""
        data_bridge.emit_task_error(task_id, error)


# 全局任务管理器实例
_task_manager = None


def get_gladia_task_manager() -> GladiaTaskManager:
    """获取Gladia任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = GladiaTaskManager()
    return _task_manager
