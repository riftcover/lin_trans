from typing import List, Dict

from app.core.api_client import api_client
from nice_ui.interfaces.token import TokenServiceInterface, RechargePackage
from nice_ui.services.simple_api_service import simple_api_service
from nice_ui.interfaces.ui_manager import UIManagerInterface
from utils import logger


class TaskTokenInfo:
    """任务算力信息"""
    def __init__(self):
        self.asr_tokens: int = 0
        self.trans_tokens: int = 0
        self.trans_tokens_estimated: int = 0  # 翻译算力预估值
        self.is_consumed: bool = False

    @property
    def total_tokens(self) -> int:
        """获取总算力"""
        return self.asr_tokens + self.trans_tokens

    @property
    def estimated_total_tokens(self) -> int:
        """获取预估总算力"""
        return self.asr_tokens + self.trans_tokens_estimated


class TokenAmountManager:
    """代币消费量管理器，负责存储和获取任务的代币消费量"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenAmountManager, cls).__new__(cls)
            cls._instance._token_amounts = {}
            cls._instance._task_token_info = {}  # 新增：存储任务的详细算力信息
        return cls._instance

    def set_token_amount(self, key: str, amount: int) -> None:
        """设置任务的代币消费量（兼容旧接口，统一使用新系统）

        Args:
            key: 任务ID或文件路径
            amount: 代币消费量
        """
        # 统一使用_task_token_info系统
        if key not in self._task_token_info:
            self._task_token_info[key] = TaskTokenInfo()

        # 对于单一任务，将算力设置为翻译算力（保持向后兼容）
        info = self._task_token_info[key]
        info.trans_tokens = amount

        # 同时更新旧系统以保持兼容性
        self._token_amounts[key] = amount
        logger.info(f"设置任务代币消费量: {amount}, 键: {key}")

    def get_token_amount(self, key: str, default: int = 10) -> int:
        """获取任务的代币消费量（统一从新系统获取）

        Args:
            key: 任务ID或文件路径
            default: 默认代币消费量

        Returns:
            int: 代币消费量
        """
        # 优先从新系统获取
        if key in self._task_token_info:
            info = self._task_token_info[key]
            # 如果是组合任务，返回总算力；否则返回翻译算力
            amount = info.total_tokens if info.asr_tokens > 0 else info.trans_tokens
            if amount > 0:
                logger.info(f"从新系统获取任务代币消费量: {amount}, 键: {key}")
                return amount

        # 回退到旧系统
        amount = self._token_amounts.get(key, default)
        logger.info(f"从旧系统获取任务代币消费量: {amount}, 键: {key}")
        return amount

    def set_asr_tokens_for_task(self, task_id: str, asr_tokens: int) -> None:
        """设置任务的ASR算力

        Args:
            task_id: 任务ID
            asr_tokens: ASR算力
        """
        if task_id not in self._task_token_info:
            self._task_token_info[task_id] = TaskTokenInfo()

        info = self._task_token_info[task_id]
        info.asr_tokens = asr_tokens
        logger.info(f"设置任务ASR算力: {asr_tokens}, 任务ID: {task_id}")

    def set_actual_translation_tokens(self, task_id: str, trans_tokens: int) -> None:
        """设置任务的实际翻译算力

        Args:
            task_id: 任务ID
            trans_tokens: 实际翻译算力
        """
        if task_id not in self._task_token_info:
            self._task_token_info[task_id] = TaskTokenInfo()

        info = self._task_token_info[task_id]
        info.trans_tokens = trans_tokens
        logger.info(f"设置实际翻译算力: {trans_tokens}, 任务ID: {task_id}")

    def get_task_token_info(self, task_id: str) -> TaskTokenInfo:
        """获取任务的算力信息

        Args:
            task_id: 任务ID

        Returns:
            TaskTokenInfo: 任务算力信息
        """
        if task_id not in self._task_token_info:
            self._task_token_info[task_id] = TaskTokenInfo()
        return self._task_token_info[task_id]

    def mark_task_consumed(self, task_id: str) -> None:
        """标记任务已扣费

        Args:
            task_id: 任务ID
        """
        if task_id in self._task_token_info:
            self._task_token_info[task_id].is_consumed = True
            logger.info(f"标记任务已扣费: {task_id}")

    def transfer_key(self, old_key: str, new_key: str) -> None:
        """将旧键的代币消费量转移到新键

        Args:
            old_key: 旧键
            new_key: 新键
        """
        if old_key in self._token_amounts:
            amount = self._token_amounts[old_key]
            self._token_amounts[new_key] = amount
            del self._token_amounts[old_key]
            logger.info(f"转移任务代币消费量: {old_key} -> {new_key}, 代币数量: {amount}")

    def clear(self) -> None:
        """清空所有代币消费量"""
        self._token_amounts.clear()
        logger.info("清空所有任务代币消费量")

    def get_all(self) -> Dict[str, int]:
        """获取所有代币消费量

        Returns:
            Dict[str, int]: 所有代币消费量
        """
        return self._token_amounts.copy()


class TokenService(TokenServiceInterface):
    """代币服务，处理代币余额查询、消耗计算等功能"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TokenService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, ui_manager: UIManagerInterface):
        """
        初始化代币服务

        Args:
            ui_manager: UI管理器实例
        """
        self.current_balance = 0
        if getattr(self, '_initialized', False):
            return
        self.ui_manager = ui_manager
        self.token_amount_manager = TokenAmountManager()

        # 从配置中获取默认系数值
        # todo: 当前没有登录时，使用云任务代币消耗会为0，所以先写死默认值。等以后重构登录状态管理器再调整
        self.asr_qps = 4
        self.trans_qps = 16

        self._initialized = True

    def update_token_coefficients(self) -> bool:
        """
        从服务器获取并更新算力消耗系数

        Returns:
            bool: 更新是否成功
        """
        # 注意：此方法已修改为异步获取，避免阻塞主线程
        def on_success(result):
            try:
                if result and 'data' in result:
                    coefficients = result['data']
                    # 遍历系数列表，更新对应的值
                    for coef in coefficients:
                        if coef['coefficient_key'] == 'asr_qps':
                            old_value = self.asr_qps
                            self.asr_qps = float(coef['coefficient_value'])
                        elif coef['coefficient_key'] == 'trans_qps':
                            old_value = self.trans_qps
                            self.trans_qps = float(coef['coefficient_value'])
                    logger.info("算力消耗系数更新成功")
                else:
                    logger.warning("获取算力消耗系数响应格式不正确")
            except Exception as e:
                logger.error(f"处理算力消耗系数响应失败: {str(e)}")

        def on_error(error):
            logger.error(f"获取算力消耗系数失败: {str(error)}")

        try:
            # 异步获取代币消耗系数
            simple_api_service.get_token_coefficients(
                callback_success=on_success,
                callback_error=on_error
            )

            return True  # 返回True表示请求已发起
        except Exception as e:
            logger.error(f"发起获取算力消耗系数请求失败: {str(e)}")
            return False

    def get_user_balance(self) -> int:
        """
        获取用户当前代币余额（同步方式）

        Returns:
            int: 用户当前代币余额
        """
        try:
            # 动态导入避免循环依赖
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

            # 调用api_client的同步方法
            result = api_client.get_balance_sync()

            if result and 'data' in result:
                balance = result['data'].get('balance', 0)
                self.current_balance = balance  # 更新缓存
                return balance
            else:
                logger.warning("余额API返回数据格式不正确")
                return self.current_balance

        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return self.current_balance

    def get_user_history(self, page: int = 1, page_size: int = 10) -> list:
        """
        获取用户当前消费记录（同步方式）

        设计原则：
        1. 与 get_user_balance() 保持一致，都使用同步方式
        2. 调用者在后台线程，不会阻塞UI
        3. 简化数据流：直接返回数据，不需要回调嵌套

        Args:
            page: 页码，默认为1
            page_size: 每页记录数，默认为10

        Returns:
            list: 交易历史记录列表，失败时返回空列表
        """

        result = api_client.get_history_sync(page=page, page_size=page_size)

        if result and 'data' in result:
            transactions = result['data'].get('transactions', [])
            total_records = result['data'].get('total', 0)
            logger.info(f"同步获取交易历史记录成功: 共 {total_records} 条记录")
            return transactions
        else:
            logger.warning("交易历史API返回数据格式不正确")
            return []
    def calculate_asr_tokens(self, video_duration: float) -> int:
        """
        计算ASR任务所需代币

        Args:
            video_duration: 视频时长（秒）

        Returns:
            int: 所需代币数量
        """
        return int(video_duration * self.asr_qps) if video_duration else 0


    def calculate_trans_tokens(self,word_counts:int,translate_engine=None) -> int:
        """

        Args:
            word_counts: 翻译文本长度/1000
            translate_engine:翻译模型

        Returns:
            int: 所需代币数量
        """

        amount = round(word_counts * self.trans_qps/1000) if word_counts else 0
        logger.trace(f'计算代币消耗,字：{word_counts},消耗:{amount}')
        return amount

    def calculate_translation_tokens(self, word_count: int) -> int:
        """
        计算翻译任务所需代币

        Args:
            word_count: 单词数量

        Returns:
            int: 所需代币数量
        """
        from nice_ui.configure import config
        return int(word_count * getattr(config, 'trans_qps', 0.1)) if word_count else 0

    def is_balance_sufficient_with_value(self, required_tokens: int, balance: int) -> bool:
        """
        使用预先获取的余额值检查是否足够

        Args:
            required_tokens: 所需代币数量
            balance: 预先获取的余额值

        Returns:
            bool: 余额是否足够
        """
        self.current_balance = balance
        if self.current_balance:
            return self.current_balance >= required_tokens
        logger.warning(f"代币余额不足，需要 {required_tokens} 代币，当前余额 {self.current_balance}")
        return False

    def prompt_recharge_dialog(self, required_tokens: int = 0) -> bool:
        """
        弹出充值对话框并等待用户操作

        Args:
            required_tokens: 所需代币数量，默认为0

        Returns:
            bool: True表示充值成功或用户确认继续，False表示取消
        """
        # 如果登陆状态，则弹出充值对话框，未登录不弹出
        if self.current_balance:
            from PySide6.QtWidgets import QApplication
            from nice_ui.ui.purchase_dialog import PurchaseDialog
            from vendor.qfluentwidgets.components.dialog_box import MessageBox
            from vendor.qfluentwidgets.common.icon import FluentIcon as FIF

            # 获取主窗口实例
            main_window = None
            for widget in QApplication.topLevelWidgets():
                if widget.objectName() == "MainWindow":
                    main_window = widget
                    break

            # 获取当前余额

            # 创建现代化的对话框
            message = f"您的当前代币余额为: {self.current_balance}"

            if required_tokens > 0:
                message += f"\n当前任务需要的代币数量: {required_tokens}"

            message += "\n\n您的代币余额不足以完成当前任务。\n是否前往充值页面进行充值？"

            msg_box = MessageBox(
                "代币不足",
                message,
                main_window
            )

            # 设置按钮文本
            msg_box.yesButton.setText("前往充值")
            msg_box.cancelButton.setText("取消")

            # 设置图标和样式
            msg_box.yesButton.setIcon(FIF.SHOPPING_CART.icon())
            msg_box.cancelButton.setIcon(FIF.CLOSE.icon())

            # 调整对话框大小和样式
            msg_box.widget.setMinimumWidth(700)  # 设置最小宽度

            # 添加颜色和样式
            from vendor.qfluentwidgets.common.style_sheet import isDarkTheme

            # 根据当前主题设置样式
            if isDarkTheme():
                msg_box.yesButton.setProperty("type", "accent")
            else:
                msg_box.yesButton.setProperty("type", "primary")

            # 显示对话框并获取用户选择
            result = msg_box.exec()

            if result:
                # 用户选择了"是"，打开充值对话框
                try:
                    # 主窗口已在前面获取
                    if main_window:
                        # 创建充值对话框
                        purchase_dialog = PurchaseDialog(main_window)

                        # 定义充值成功的回调函数
                        def on_purchase_completed(transaction_data):
                            logger.info(f"充值成功: {transaction_data}")
                            # 更新余额显示
                            self.ui_manager.show_message("成功", "充值成功！", "success")

                        # 连接充值成功信号
                        purchase_dialog.purchaseCompleted.connect(on_purchase_completed)

                        # 显示充值对话框
                        result = purchase_dialog.exec()

                        # 如果充值成功，返回True
                        if result:
                            logger.info("用户确认充值成功")
                            return True
                        else:
                            logger.info("用户取消充值")
                            # 用户取消了充值
                            return False
                    else:
                        # 未找到主窗口，显示错误提示
                        logger.error("未找到主窗口实例，无法打开充值对话框")
                        self.ui_manager.show_message("错误", "无法打开充值页面，请重试", "error")
                        return False
                except Exception as e:
                    # 处理异常
                    logger.error(f"打开充值对话框时发生错误: {str(e)}")
                    self.ui_manager.show_message("错误", f"打开充值页面时发生错误: {str(e)}", "error")
                    return False
            else:
                # 用户选择了"否"
                return False

    def get_recharge_packages(self) -> List[RechargePackage]:
        """
        获取充值套餐列表（使用预定义数据）

        Returns:
            List[RechargePackage]: 充值套餐列表
        """
        # 返回预定义的充值套餐，避免不必要的API调用
        return [
            {'price': 10, 'token_amount': 2000},
            {'price': 20, 'token_amount': 4100},
            {'price': 50, 'token_amount': 10750},
            {'price': 75, 'token_amount': 16865},
            {'price': 100, 'token_amount': 23500},
            {'price': 150, 'token_amount': 36750}
        ]

    def set_task_token_amount(self, key: str, amount: int) -> None:
        """
        设置任务的代币消费量

        Args:
            key: 任务ID或文件路径
            amount: 代币消费量
        """
        self.token_amount_manager.set_token_amount(key, amount)

    def get_task_token_amount(self, key: str, default: int = 10) -> int:
        """
        获取任务的代币消费量

        Args:
            key: 任务ID或文件路径
            default: 默认代币消费量

        Returns:
            int: 代币消费量
        """
        return self.token_amount_manager.get_token_amount(key, default)

    def transfer_task_key(self, old_key: str, new_key: str) -> None:
        """
        将旧键的代币消费量转移到新键

        Args:
            old_key: 旧键
            new_key: 新键
        """
        self.token_amount_manager.transfer_key(old_key, new_key)

    def clear_task_tokens(self) -> None:
        """清空所有任务的代币消费量"""
        self.token_amount_manager.clear()

    def consume_tokens(self, token_amount: int, feature_key: str = "asr", file_name: str = "",
                      callback_success=None, callback_error=None) -> bool:
        """
        消费代币（异步方式）

        设计原则：Service层只负责业务逻辑，不负责UI通知
        调用者通过回调函数处理结果和UI更新

        Args:
            token_amount: 消费的代币数量
            feature_key: 功能标识符，默认为"asr"
            file_name: 文件名，默认为空字符串
            callback_success: 成功回调函数，接收 result 作为参数
            callback_error: 失败回调函数，接收错误信息作为参数

        Returns:
            bool: 请求是否成功发起（不代表消费成功，实际结果通过回调返回）
        """
        try:
            # 调用api_client中的方法消费代币（异步）
            us_id = api_client.get_id()

            def on_success(result):
                logger.info(f"消费代币成功: {token_amount}")
                # 调用外部回调，让调用者决定如何处理结果
                if callback_success:
                    callback_success(result)

            def on_error(error):
                logger.error(f"消费代币失败: {str(error)}")
                if callback_error:
                    callback_error(str(error))

            simple_api_service.execute_async(
                api_client.consume_tokens,
                args=(token_amount, file_name, feature_key, us_id),
                callback_success=on_success,
                callback_error=on_error
            )
            logger.info(f"已发起消费代币请求: {token_amount}")
            return True

        except Exception as e:
            logger.error(f"消费代币时发生错误: {str(e)}")
            if callback_error:
                callback_error(str(e))
            return False

    def set_ast_tokens_for_task(self,task_id:str ,asr_tokens:int) -> None:
        """设置任务的ASR算力

        Args:
            task_id: 任务ID
            asr_tokens: ASR算力
        """
        self.token_amount_manager.set_asr_tokens_for_task(task_id, asr_tokens)

    def set_translation_tokens_for_task(self, task_id: str, trans_tokens: int) -> None:
        """设置任务的实际翻译算力

        Args:
            task_id: 任务ID
            trans_tokens: 实际翻译算力
        """
        self.token_amount_manager.set_actual_translation_tokens(task_id, trans_tokens)

    def get_total_task_tokens(self, task_id: str) -> int:
        """获取任务的总算力（ASR + 翻译）

        Args:
            task_id: 任务ID

        Returns:
            int: 总算力
        """
        info = self.token_amount_manager.get_task_token_info(task_id)
        return info.total_tokens

    def get_estimated_task_tokens(self, task_id: str) -> int:
        """获取任务的预估总算力（ASR + 预估翻译）

        Args:
            task_id: 任务ID

        Returns:
            int: 预估总算力
        """
        info = self.token_amount_manager.get_task_token_info(task_id)
        return info.estimated_total_tokens

    def estimate_translation_tokens_by_duration(self, video_duration: float) -> int:
        """基于视频时长估算翻译算力

        Args:
            video_duration: 视频时长（秒）

        Returns:
            int: 预估翻译算力
        """
        # 经验公式：假设每分钟视频产生约100个字符的文本
        estimated_chars = int(video_duration / 60 * 100)
        return self.calculate_trans_tokens(estimated_chars)

    def set_task_tokens_estimate(self, task_id: str, asr_tokens: int, trans_tokens_estimated: int) -> None:
        """设置任务的算力预估

        Args:
            task_id: 任务ID
            asr_tokens: ASR算力
            trans_tokens_estimated: 翻译算力预估
        """
        if task_id not in self.token_amount_manager._task_token_info:
            self.token_amount_manager._task_token_info[task_id] = TaskTokenInfo()

        info = self.token_amount_manager._task_token_info[task_id]
        info.asr_tokens = asr_tokens
        info.trans_tokens_estimated = trans_tokens_estimated

        logger.info(f"设置任务算力预估: ASR={asr_tokens}, 翻译预估={trans_tokens_estimated}, 任务ID: {task_id}")

    def consume_tokens_for_task(self, task_id: str, feature_key: str,file_name: str) -> bool:
        """
        统一的任务扣费方法，适用于所有任务类型

        Args:
            task_id: 任务ID
            feature_key: 功能标识符

        Returns:
            bool: 扣费是否成功
        """
        try:
            # 获取任务算力信息
            info = self.token_amount_manager.get_task_token_info(task_id)

            # 检查是否已扣费
            if info.is_consumed:
                logger.warning(f"任务已扣费，跳过: {task_id}")
                return True

            # 确定要扣费的算力数量
            token_amount = 0
            if info.asr_tokens > 0 or info.trans_tokens > 0:
                # 如果有详细算力信息，使用总算力
                token_amount = info.total_tokens
                logger.info(f"使用详细算力信息扣费: ASR={info.asr_tokens}, 翻译={info.trans_tokens}, 总计={token_amount}")
            else:
                # 回退到旧系统
                token_amount = self.token_amount_manager.get_token_amount(task_id, 0)
                logger.info(f"使用旧系统算力信息扣费: {token_amount}")

            # 检查算力是否为0
            if token_amount <= 0:
                logger.warning(f"任务算力为0，跳过扣费: {task_id}")
                return True

            # 执行扣费
            success = self.consume_tokens(token_amount, feature_key, file_name)

            if success:
                # 标记任务已扣费
                self.token_amount_manager.mark_task_consumed(task_id)
                logger.info(f"统一扣费成功: {task_id}, 算力: {token_amount}, 类型: {feature_key}")
            else:
                logger.error(f"统一扣费失败: {task_id}, 算力: {token_amount}, 类型: {feature_key}")

            return success

        except Exception as e:
            logger.error(f"统一扣费异常: {task_id}, 类型: {feature_key}, 错误: {str(e)}")
            return False
