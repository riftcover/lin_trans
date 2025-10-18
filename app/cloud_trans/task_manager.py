from pathlib import Path
from typing import Optional

from agent.srt_translator_adapter import SRTTranslatorAdapter
from app.core.feature_types import FeatureKey
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
from orm.queries import ToTranslationOrm
from utils import logger


class TransTaskManager:
    def __init__(self):
        pass

    def consume_tokens_for_task(
        self,
        task_id: str,
        file_name: str,
        feature_key: FeatureKey = "cloud_trans"
    ) -> bool:
        """
        统一的任务扣费方法，适用于所有任务类型

        Args:
            task_id: 翻译任务ID
            feature_key: 任务类型，用于确定正确的feature_key
            可选值：   - "cloud_asr": 云ASR任务
                      - "cloud_trans": 纯翻译任务
                      - "asr_trans": ASR+云翻译任务
                      - "cloud_asr_trans": 云ASR+翻译任务

        Returns:
            bool: 扣费是否成功
        """
        logger.info(f'开始统一任务扣费流程，任务ID: {task_id}, 任务类型: {feature_key}')
        try:
            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            if billing_success := token_service.consume_tokens_for_task(
                task_id, feature_key, file_name
            ):
                logger.info(f"任务扣费成功 - 任务ID: {task_id}, 任务类型: {feature_key}")
                # 注意：不在这里发送完成信号，应该在调用方确认翻译真正完成后再发送
                return True
            else:
                logger.error(f"任务扣费失败 - 任务ID: {task_id}, 任务类型: {feature_key}")
                return False

        except Exception as e:
            logger.error(f"任务扣费异常 - 任务ID: {task_id}, 任务类型: {feature_key}, 错误: {str(e)}")
            return False



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
                logger.warning(f"SRT文件不存在，设置默认翻译算力: {srt_file_path}")
                self._set_default_translation_tokens(task_id)
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
            self._set_default_translation_tokens(task_id)

    def _set_default_translation_tokens(self, task_id: str) -> None:
        """设置默认翻译算力"""
        try:
            token_service = ServiceProvider().get_token_service()
            token_service.set_translation_tokens_for_task(task_id, 10)
            logger.info(f'设置默认翻译算力: 10, 任务ID: {task_id}')
        except Exception as e:
            logger.error(f'设置默认翻译算力失败: {task_id}, 错误: {e}')

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

    def setup_translation_tokens_estimate_if_needed(self, task_id: str, video_duration: float = 60) -> None:
        """
        为翻译任务设置算力预估（如果使用云翻译）

        Args:
            task_id: 任务ID
            video_duration: 视频时长（秒），默认60秒
        """
        try:
            # 检查翻译引擎是否为云翻译
            translate_engine = config.params.get('translate_channel', '')
            if translate_engine != 'qwen_cloud':
                logger.info(f"非云翻译引擎({translate_engine})，跳过翻译算力预估")
                return

            # 获取代币服务进行翻译算力预估
            token_service = ServiceProvider().get_token_service()

            # 预估翻译算力（基于视频时长）
            trans_tokens_estimated = token_service.estimate_translation_tokens_by_duration(video_duration)

            # 设置翻译算力预估（ASR算力为0，因为本地ASR不消耗算力）
            token_service.set_task_tokens_estimate(task_id, 0, trans_tokens_estimated)

            logger.info(f'翻译任务算力预估完成 - 翻译预估: {trans_tokens_estimated}, 任务ID: {task_id}')

        except Exception as e:
            logger.error(f'设置翻译任务算力预估失败: {task_id}, 错误: {e}')

    def refresh_usage_records_after_task_completion(self, task_id: str) -> None:
        """
        任务完成后刷新使用记录

        Args:
            task_id: 任务ID
        """
        try:
            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            # 更新余额
            if balance := token_service.get_user_balance():
                logger.info(f"翻译任务完成后更新用户余额: {balance}")
                data_bridge.emit_update_balance(balance)

            # 更新历史记录
            if transactions := token_service.get_user_history():
                logger.info(f"翻译任务完成后更新用户历史记录，记录数: {len(transactions)}")
                data_bridge.emit_update_history(transactions)

        except Exception as e:
            logger.error(f"翻译任务完成后刷新使用记录失败: {task_id}, 错误: {e}")

    def _notify_task_completed(self, task_id: Optional[str]) -> None:
        """
        通知UI任务完成

        Args:
            task_id: 应用内唯一标识符（可选）
        """
        try:
            # 如果有task_id，使用数据桥通知UI
            if task_id:
                logger.info(f'更新任务完成状态，task_id: {task_id}')
                data_bridge.emit_whisper_finished(task_id)

                # 更新个人中心的余额和历史记录
                try:
                    # 获取代币服务
                    token_service = ServiceProvider().get_token_service()

                    # 更新余额
                    if balance := token_service.get_user_balance():
                        logger.info(f"更新用户余额: {balance}")
                        # 通知UI更新余额显示
                        data_bridge.emit_update_balance(balance)

                    # 更新历史记录
                    if transactions := token_service.get_user_history():
                        logger.info("更新用户历史记录")
                        # 通知UI更新余额显示
                        data_bridge.emit_update_history(transactions)

                except Exception as e:
                    logger.error(f"更新个人中心信息失败: {str(e)}")

        except Exception as e:
            logger.error(f"通知任务完成失败: {str(e)}")


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
