from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent.srt_translator_adapter import SRTTranslatorAdapter
from nice_ui.configure.signal import data_bridge

if TYPE_CHECKING:
    from app.core.feature_types import FeatureKey
from nice_ui.configure import config
from nice_ui.services.service_provider import ServiceProvider
from orm.queries import ToTranslationOrm
from utils import logger


class TransTaskManager:
    """
    云翻译任务管理器

    职责：
    1. 计算翻译算力
    2. 管理翻译任务数据库记录
    """



    def calculate_and_set_translation_tokens_from_srt(self, task_id: str, srt_file_path: str) -> None:
        """
        从SRT文件计算并设置翻译算力

        Args:
            task_id: 任务ID
            srt_file_path: SRT文件路径
        """
        try:
            # 检查翻译引擎是否为云翻译
            translate_engine = config.params.get('translate_channel', '')
            if translate_engine != 'qwen_cloud':
                logger.info(f"非云翻译引擎({translate_engine})，跳过翻译算力计算")
                return

            # 检查SRT文件是否存在
            if not Path(srt_file_path).exists():
                logger.warning(f"SRT文件不存在")
                return

            # 使用SRT适配器解析内容并计算字数
            with open(srt_file_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()

            adapter = SRTTranslatorAdapter()
            entries = adapter.parse_srt_content(srt_content)

            # 计算总字符数
            total_chars = sum(len(entry.text) for entry in entries)

            # 使用TokenService计算翻译算力
            token_service = ServiceProvider().get_token_service()
            trans_tokens = token_service.calculate_trans_tokens(total_chars)

            # 设置实际翻译算力
            token_service.set_translation_tokens_for_task(task_id, trans_tokens)

            logger.info(f'翻译任务算力计算完成 - 字符数: {total_chars}, 算力: {trans_tokens}, 任务ID: {task_id}')

        except Exception as e:
            logger.error(f'计算翻译任务算力失败: {task_id}, 错误: {e}')

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

    def consume_tokens_for_task(self, task: Any, feature_key: 'FeatureKey', file_name: str) -> None:
        """
        为任务消费代币（统一回调机制）

        Args:
            task: 任务对象
            feature_key: 功能标识符（cloud_asr, cloud_trans等）
            file_name: 文件名
        """
        logger.info(task)
        logger.info(f'消费代币 - 任务ID: {task.unid}, 功能: {feature_key}')
        try:
            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            # 从代币服务中获取代币消费量
            token_amount = token_service.get_task_token_amount(task.unid)
            logger.info(f'从代币服务中获取代币消费量: {token_amount}, 任务ID: {task.unid}')
            token_amount =10

            # 消费代币
            if token_amount > 0:
                logger.info(f"为任务消费代币: {token_amount}")

                # 定义扣费成功回调：只有在扣费真正完成后才更新余额
                def on_consume_success(result):
                    logger.info(f"代币消费成功: {token_amount}, 结果: {result}")
                    # 扣费成功后，更新个人中心余额和历史记录
                    self._notify_task_completed(task.unid)

                def on_consume_error(error):
                    logger.warning(f"代币消费失败: {token_amount}, 错误: {error}")
                    # 即使扣费失败，也通知任务完成（但不更新余额）
                    data_bridge.emit_whisper_finished(task.unid)

                # 异步消费代币，通过回调处理结果
                token_service.consume_tokens(
                    token_amount, feature_key, file_name,
                    callback_success=on_consume_success,
                    callback_error=on_consume_error
                )
            else:
                logger.warning("代币数量为0，不消费代币")
                # 无需扣费，直接通知完成
                self._notify_task_completed(task.unid)

        except Exception as e:
            logger.error(f"消费代币时发生错误: {str(e)}")
            # 异常情况也要通知任务完成
            data_bridge.emit_whisper_finished(task.unid)

    def _notify_task_completed(self, task_id: str) -> None:
        """
        通知UI任务完成，更新个人中心余额和历史记录

        注意：此方法应该在扣费成功后调用，确保余额是扣费后的最新值

        Args:
            task_id: 任务ID
        """
        # 通知任务完成
        logger.info(f'更新任务完成状态，task_id: {task_id}')
        data_bridge.emit_whisper_finished(task_id)
        # 刷新余额和历史记录
        self._refresh_usage_records(task_id)

    @staticmethod
    def _refresh_usage_records(task_id: str) -> None:
        """
        刷新用户余额和历史记录

        Args:
            task_id: 任务ID（用于日志）
        """
        # 更新个人中心的余额和历史记录
        try:
            # 更新余额（异步方式，确保获取扣费后的最新余额）
            def on_balance_success(result):
                if result and "data" in result:
                    balance = result["data"].get("balance", 0)
                    logger.info(f"获取扣费后余额成功: {balance}")
                    data_bridge.emit_update_balance(balance)
                else:
                    logger.warning("获取余额失败或余额为0")

            def on_balance_error(error):
                logger.error(f"获取余额失败: {error}")

            # 异步获取余额
            from nice_ui.services.simple_api_service import simple_api_service

            simple_api_service.get_balance(
                callback_success=on_balance_success,
                callback_error=on_balance_error,
            )

            # 更新历史记录（异步方式）
            def on_history_success(result):
                if result and "data" in result:
                    transactions = result["data"].get("transactions", [])
                    logger.info(
                        f"获取历史记录成功，记录数: {len(transactions)}"
                    )
                    data_bridge.emit_update_history(transactions)
                else:
                    logger.warning("获取历史记录失败")

            def on_history_error(error):
                logger.error(f"获取历史记录失败: {error}")

            # 异步获取历史记录
            simple_api_service.get_history(
                callback_success=on_history_success,
                callback_error=on_history_error,
            )

        except Exception as e:
            logger.error(f"更新个人中心信息失败: {str(e)}")


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
