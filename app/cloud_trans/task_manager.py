import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict

from agent.enhanced_common_agent import translate_document
from agent.srt_translator_adapter import SRTTranslatorAdapter
from app.core.base_task_manager import BaseTaskManager
from app.core.task_models import Task, TaskTokens
from nice_ui.configure.signal import data_bridge
from services.config_manager import get_chunk_size, get_max_entries, get_sleep_time

if TYPE_CHECKING:
    from app.core.feature_types import FeatureKey
from nice_ui.configure import config
from nice_ui.services.service_provider import ServiceProvider
from orm.queries import ToTranslationOrm
from utils import logger


class TransTaskManager(BaseTaskManager):
    """
    云翻译任务管理器

    职责：
    1. 计算翻译算力（使用基类方法 calculate_and_set_trans_tokens）
    2. 管理翻译任务数据库记录
    3. 执行翻译任务并扣费

    注意：翻译任务是即时执行的，不需要持久化，所以序列化方法提供空实现

    重构说明：
    - 代币数据现在属于 Task 对象（app/core/task_models.py）
    - 使用基类的 calculate_and_set_trans_tokens() 方法
    """

    def __init__(self):
        """初始化翻译任务管理器"""
        # 初始化基类（翻译任务不需要持久化，使用临时文件）
        task_state_file = Path(f"{config.temp_path}/trans_tasks.json")
        super().__init__(task_state_file)
        logger.trace("翻译任务管理器初始化完成")

    # ==================== 实现抽象方法（翻译任务不需要持久化） ====================

    def _serialize_task(self, task: Any) -> Dict[str, Any]:
        """
        序列化任务对象为字典（翻译任务不需要持久化，提供空实现）

        Args:
            task: 任务对象

        Returns:
            Dict[str, Any]: 空字典
        """
        return {}

    def _deserialize_task(self, task_data: Dict[str, Any]) -> Any:
        """
        从字典反序列化任务对象（翻译任务不需要持久化，提供空实现）

        Args:
            task_data: 任务数据字典

        Returns:
            Any: None
        """
        return None

    def submit_task(self, task_id: str) -> None:
        """
        提交任务（翻译任务是即时执行的，不需要提交，提供空实现）

        Args:
            task_id: 任务ID
        """
        pass

    # ==================== 翻译任务特定方法 ====================

    def create_translation_task(self, task_id: str, srt_file: str) -> str:
        """
        创建翻译任务

        重构说明：
        - 与 ASR 任务保持一致，先创建 Task 对象
        - 然后计算并设置代币

        Args:
            task_id: 任务ID
            srt_file: SRT文件路径

        Returns:
            str: 任务ID
        """
        # 创建 Task 对象
        trans_task = Task(
            task_id=task_id,
            audio_file=srt_file,
            language=config.params.get("source_language", "zh"),
            tokens=TaskTokens()
        )

        with self.lock:
            self.tasks[task_id] = trans_task

        logger.info(f"创建翻译任务: task_id={task_id}, srt_file={srt_file}")

        # 计算并设置翻译代币
        self.calculate_and_set_trans_tokens(task_id, srt_file)

        return task_id

    def execute_translation(
        self,
        task: Any,
        in_document: str,
        out_document: str,
        feature_key: 'FeatureKey'
    ) -> None:
        """
        执行翻译任务并扣费

        职责：
        1. 执行翻译
        2. 扣费并刷新使用记录

        重构说明：
        - task 参数是 VideoFormatInfo 对象（UI层数据）
        - 使用 task.unid 获取已创建的 Task 对象
        - 与 ASR 任务保持一致的流程

        Args:
            task: VideoFormatInfo 对象（UI层数据，包含 unid, raw_noextname 等）
            in_document: 输入文档路径
            out_document: 输出文档路径
            feature_key: 功能键（用于扣费）
        """
        agent_type = config.params['translate_channel']
        chunk_size_int = get_chunk_size()
        max_entries_int = get_max_entries()
        sleep_time_int = get_sleep_time()

        logger.trace(f'准备翻译任务:{out_document}')
        logger.trace(
            f'任务参数:{task.unid}, {in_document}, {out_document}, {agent_type},'
            f'{chunk_size_int},{max_entries_int},{sleep_time_int},'
            f'{config.params["target_language"]},{config.params["source_language"]}'
        )

        # 获取已创建的 Task 对象
        task_id = task.unid
        trans_task = self.get_task(task_id)

        if not trans_task:
            logger.error(f"翻译任务不存在: {task_id}，请先调用 create_translation_task()")
            raise ValueError(f"翻译任务不存在: {task_id}")

        try:
            translate_document(
                unid=task.unid,
                in_document=in_document,
                out_document=out_document,
                agent_name=agent_type,
                chunk_size=chunk_size_int,
                max_entries=max_entries_int,
                sleep_time=sleep_time_int,
                target_language=config.params["target_language"],
                source_language=config.params["source_language"]
            )

            logger.info(f'翻译任务执行完成，开始扣费流程，任务ID: {task_id}')

            # 扣费并刷新使用记录（使用 Task 对象）
            self._consume_tokens_for_task(trans_task, feature_key, task.raw_noextname)

        except ValueError as e:
            # 检查是否是API密钥缺失的错误
            if "请填写API密钥" in str(e):
                logger.error(f"翻译任务失败 - API密钥缺失: {task.unid}")
                data_bridge.emit_task_error(task.unid, "填写key")
            else:
                logger.error(f"翻译任务失败: {task.unid}, 错误: {e}")
                data_bridge.emit_task_error(task.unid, str(e))
            raise e
        except Exception as e:
            logger.error(f"翻译任务失败: {task.unid}, 错误: {e}")
            data_bridge.emit_task_error(task.unid, str(e))
            raise e



    def add_translation_task_to_database(self, task_id: str, raw_name: str, task_json: str) -> None:
        """
        添加翻译任务到数据库

        Args:
            task_id: 任务ID
            raw_name: 原始文件名
            task_json: 任务JSON数据
        """
        try:
            trans_orm = ToTranslationOrm()
            trans_orm.add_data_to_table(
                task_id,
                raw_name,
                config.params['source_language'],
                config.params["source_language_code"],
                config.params['target_language'],
                config.params['translate_channel'],
                1,
                1,
                task_json
            )
            logger.info(f'翻译任务已添加到数据库 - 任务ID: {task_id}')
        except Exception as e:
            logger.error(f'添加翻译任务到数据库失败: {task_id}, 错误: {e}')
            raise e


# 单例模式
_task_manager_instance = None


def get_trans_task_manager() -> TransTaskManager:
    """
    获取任务管理器实例

    Returns:
        TransTaskManager: 任务管理器实例
    """
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TransTaskManager()
    return _task_manager_instance
