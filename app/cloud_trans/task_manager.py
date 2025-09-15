from typing import Optional

from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
from utils import logger


class TransTaskManager:
    def __init__(self):
        pass

    def consume_tokens_for_task(self, task_id: str) -> bool:
        """
        为翻译任务消费代币

        Args:
            task_id: 翻译任务ID

        Returns:
            bool: 扣费是否成功
        """
        logger.info(f'开始翻译任务扣费流程，任务ID: {task_id}')
        try:
            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            # 从代币服务中获取代币消费量
            token_amount = token_service.get_task_token_amount(task_id)
            logger.info(f'翻译任务扣费 - 算力: {token_amount}, 任务ID: {task_id}')

            # 检查代币数量
            if token_amount <= 0:
                logger.warning(f"翻译任务算力为0，跳过扣费 - 任务ID: {task_id}")
                return True  # 算力为0时认为扣费成功

            # 执行扣费
            logger.info(f"开始扣费 - 算力: {token_amount}, 任务ID: {task_id}")
            billing_success = token_service.consume_tokens(token_amount, "cloud_trans")

            if billing_success:
                logger.info(f"✅ 翻译任务扣费成功 - 算力: {token_amount}, 任务ID: {task_id}")
                self._notify_task_completed(task_id)
                return True
            else:
                logger.error(f"❌ 翻译任务扣费失败 - 算力: {token_amount}, 任务ID: {task_id}")
                return False

        except Exception as e:
            logger.error(f"❌ 翻译任务扣费异常 - 任务ID: {task_id}, 错误: {str(e)}")
            return False


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