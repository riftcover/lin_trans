"""
Gladia ASR 任务管理器（重构版本）

重构说明：
1. 继承 BaseTaskManager，复用所有共同功能
2. 只保留 Gladia 特定的业务逻辑
3. 使用统一的 TaskStatus 常量
"""

import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

from app.cloud_asr.gladia_asr_client import GladiaASRClient, create_config, creat_gladia_asr_client
from app.core.base_task_manager import BaseTaskManager
from app.core.task_status import TaskStatus
from nice_ui.configure import config
from services.decorators import except_handler
from utils import logger
from utils.file_utils import funasr_write_srt_file


class ASRTask:
    """ASR任务对象"""

    def __init__(self, task_id: str, audio_file: str, language: str):
        self.task_id = task_id
        self.audio_file = audio_file
        self.audio_url = None  # Gladia音频URL
        self.result_url = None  # Gladia结果URL
        self.language = language
        self.status = TaskStatus.PENDING
        self.error = None
        self.progress = 0
        self.created_at = time.time()
        self.updated_at = time.time()
        self.auto_billing = True


class GladiaTaskManager(BaseTaskManager):
    """Gladia ASR任务管理器（重构版本）"""

    def __init__(self):
        # 初始化基类
        task_state_file = Path(f"{config.temp_path}/gladia_asr_tasks.json")
        super().__init__(task_state_file)

        # Gladia特定属性
        self.polling_thread = None
        self.polling_active = False

        # 加载现有任务
        self._load_tasks()

        logger.trace("Gladia ASR任务管理器初始化完成")

    # ==================== 实现抽象方法 ====================

    def _serialize_task(self, task: ASRTask) -> Dict[str, Any]:
        """序列化任务对象为字典"""
        return {
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

    def _deserialize_task(self, task_data: Dict[str, Any]) -> ASRTask:
        """从字典反序列化任务对象"""
        task = ASRTask(
            task_data['task_id'],
            task_data['audio_file'],
            task_data['language']
        )
        # 恢复任务状态
        for key, value in task_data.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return task

    # ==================== Gladia特定方法 ====================

    def create_task(self, task_id: str, audio_file: str, language: str, auto_billing: bool = True) -> str:
        """创建新的ASR任务"""
        task = ASRTask(task_id, audio_file, language)
        task.auto_billing = auto_billing

        with self.lock:
            self.tasks[task_id] = task

        self._save_tasks()
        return task_id

    @except_handler("ASR request failed", retry=5, delay=1)
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
            self.update_task(task_id, status=TaskStatus.UPLOADING, progress=5)
            self._notify_task_progress(task.task_id, 5)

            # 上传音频文件
            logger.info(f"开始上传音频文件 - 任务ID: {task_id}")
            audio_url = client.upload_audio(task.audio_file)

            # 更新任务状态
            self.update_task(task_id, audio_url=audio_url, status=TaskStatus.SUBMITTED, progress=15)
            self._notify_task_progress(task.task_id, 15)

            # 提交转录任务
            logger.info(f"开始提交转录任务 - 任务ID: {task_id}, 语言:{task.language}")
            config_dict = create_config(task.language)
            result_url = client.submit_transcription(audio_url, config_dict)

            # 更新任务状态
            self.update_task(
                task_id,
                result_url=result_url,
                status=TaskStatus.PROCESSING,
                progress=25
            )
            self._notify_task_progress(task.task_id, 25)

            logger.info(f"成功提交ASR任务 - 内部ID: {task_id}, Cloud结果URL: {result_url}")

            # 确保轮询线程正在运行
            self._ensure_polling_thread()

        except Exception as e:
            logger.error(f"提交ASR任务失败: {str(e)}")
            self.update_task(task_id, status=TaskStatus.FAILED, error=str(e))
            self._notify_task_failed(task.task_id, str(e))

    def _ensure_polling_thread(self):
        """确保轮询线程正在运行"""
        if not self.polling_thread or not self.polling_thread.is_alive():
            self.polling_active = True
            self.polling_thread = threading.Thread(target=self._polling_worker, daemon=True)
            self.polling_thread.start()
            logger.info("启动任务轮询线程")

    def _polling_worker(self):
        """轮询工作线程"""
        client = creat_gladia_asr_client()

        while self.polling_active:
            try:
                if not client:
                    time.sleep(5)
                    continue

                processing_tasks = []
                with self.lock:
                    processing_tasks = [
                        task for task in self.tasks.values()
                        if task.status == TaskStatus.PROCESSING and task.result_url
                    ]

                for task in processing_tasks:
                    try:
                        result = client.get_result(task.result_url)
                        status = result.get('status')

                        if status == 'done':
                            self._handle_task_completion(task, result, client)
                        elif status == 'error':
                            error_msg = result.get('error', '未知错误')
                            self.update_task(task.task_id, status=TaskStatus.FAILED, error=error_msg)
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
            segments, gladia_language = client.get_segments(result)

            if segments:
                # 更新进度到95%
                self.update_task(task.task_id, progress=95)
                self._notify_task_progress(task.task_id, 95)

                # 生成SRT文件
                audio_path = Path(task.audio_file)
                srt_file_path = audio_path.with_suffix('.srt')
                funasr_write_srt_file(segments, str(srt_file_path))

                # 更新进度到97%
                self.update_task(task.task_id, progress=97)
                self._notify_task_progress(task.task_id, 97)

                # 生成segment_data文件（使用基类方法）
                segment_data_path = self._create_segment_data_file(segments, task.audio_file)

                # 更新语言（如果是自动检测）
                if task.language == 'auto':
                    task.language = gladia_language

                # 保存segment_data路径（使用基类方法）
                self._save_segment_data_path(segment_data_path, task.audio_file, task.language)
                logger.info(f"已生成segment_data文件，智能分句功能可用")

                # 更新进度到99%
                self.update_task(task.task_id, progress=99)
                self._notify_task_progress(task.task_id, 99)

                # 更新任务状态为完成
                self.update_task(task.task_id, status=TaskStatus.COMPLETED, progress=100)

                # 扣费（使用基类方法）
                logger.info(f'ASR任务自动扣费模式，开始扣费: {task.task_id}')
                file_name = Path(task.audio_file).stem
                self._consume_tokens_for_task(task, "cloud_asr", file_name)

                logger.info(f"任务完成 - ID: {task.task_id}, SRT文件: {srt_file_path}")
            else:
                raise Exception("转录结果为空")

        except Exception as e:
            logger.error(f"处理任务完成失败: {e}")
            self.update_task(task.task_id, status=TaskStatus.FAILED, error=str(e))
            self._notify_task_failed(task.task_id, str(e))


# 全局任务管理器实例
_task_manager = None


def get_gladia_task_manager() -> GladiaTaskManager:
    """获取Gladia任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = GladiaTaskManager()
    return _task_manager
