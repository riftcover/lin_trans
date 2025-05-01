from typing import Optional

from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
from utils import logger


class TransTaskManager:
    def __init__(self):
        pass

    def consume_tokens_for_task(self,task_id:str):
        """
        为任务消费代币

        Args:
            task: ASR任务对象
        """
        logger.info('消费代币')
        try:
            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            # 从代币服务中获取代币消费量
            token_amount = token_service.get_task_token_amount(task_id)
            logger.info(f'从代币服务中获取代币消费量: {token_amount}, 任务ID: {task_id}')

            # 消费代币
            if token_amount > 0:
                logger.info(f"为ASR任务消费代币: {token_amount}")
                if token_service.consume_tokens(
                        token_amount, "cloud_asr"
                ):
                    logger.info(f"代币消费成功: {token_amount}")
                    self._notify_task_completed(task_id)

                else:
                    logger.warning(f"代币消费失败: {token_amount}")
            else:
                logger.warning("代币数量为0，不消费代币")

        except Exception as e:
            logger.error(f"消费代币时发生错误: {str(e)}")


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