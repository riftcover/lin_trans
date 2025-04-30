from typing import List, Dict

from nice_ui.configure import config
from nice_ui.interfaces.token import TokenServiceInterface, RechargePackage
from nice_ui.interfaces.ui_manager import UIManagerInterface
from api_client import api_client, AuthenticationError
from utils import logger

class TokenAmountManager:
    """代币消费量管理器，负责存储和获取任务的代币消费量"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenAmountManager, cls).__new__(cls)
            cls._instance._token_amounts = {}
        return cls._instance

    def set_token_amount(self, key: str, amount: int) -> None:
        """设置任务的代币消费量

        Args:
            key: 任务ID或文件路径
            amount: 代币消费量
        """
        self._token_amounts[key] = amount
        logger.info(f"设置任务代币消费量: {amount}, 键: {key}")

    def get_token_amount(self, key: str, default: int = 10) -> int:
        """获取任务的代币消费量

        Args:
            key: 任务ID或文件路径
            default: 默认代币消费量

        Returns:
            int: 代币消费量
        """
        amount = self._token_amounts.get(key, default)
        logger.info(f"获取任务代币消费量: {amount}, 键: {key}")
        return amount

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
        from nice_ui.configure import config
        self.asr_qps = None
        self.trans_qps = None

        self._initialized = True

    def update_token_coefficients(self) -> bool:
        """
        从服务器获取并更新算力消耗系数

        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取代币消耗系数
            response = api_client.get_token_coefficients_sync()
            if response and 'data' in response:
                coefficients = response['data']
                # 遍历系数列表，更新对应的值
                for coef in coefficients:
                    if coef['coefficient_key'] == 'asr_qps':
                        old_value = self.asr_qps
                        self.asr_qps = float(coef['coefficient_value'])
                        logger.info(f"从服务器更新ASR算力消耗系数: {old_value} -> {self.asr_qps}")
                    elif coef['coefficient_key'] == 'trans_qps':
                        old_value = self.trans_qps
                        self.trans_qps = float(coef['coefficient_value'])
                        logger.info(f"从服务器更新翻译算力消耗系数: {old_value} -> {self.trans_qps}")
                return True
            return False
        except Exception as e:
            logger.error(f"更新算力消耗系数失败: {str(e)}")
            return False

    def get_user_balance(self) -> int | bool:
        """
        获取用户当前代币余额

        Returns:
            int: 用户当前代币余额，如果获取失败则返回0
        """
        try:
            # 获取用户余额
            balance_data = api_client.get_balance_sync()

            # 解析响应数据获取代币余额
            if 'data' in balance_data and 'balance' in balance_data['data']:
                balance = balance_data['data']['balance']
                logger.info(f"用户当前代币余额: {balance}")
                return int(balance)
            else:
                logger.warning(f"响应数据格式不正确: {balance_data}")
                return False

        except AuthenticationError as e:
            logger.error(f"认证错误，无法获取代币余额: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"获取代币余额时发生错误: {str(e)}")
            return False

    def get_user_history(self) -> list:
        """
        获取用户当前消费记录

        Returns:

        """
        # 更新历史记录
        try:
            # 获取最新的交易记录
            history_data = api_client.get_history_sync(page=1, page_size=10)
            if history_data and 'data' in history_data:
                transactions = history_data['data'].get('transactions', [])
                total_records = history_data['data'].get('total', 0)
                logger.info(f"更新交易历史记录: 共 {total_records} 条记录")
                return transactions
                # 通知UI更新历史记录
        except Exception as e:
            logger.error(f"获取交易历史记录失败: {str(e)}")
    def calculate_asr_tokens(self, video_duration: float) -> int:
        """
        计算ASR任务所需代币

        Args:
            video_duration: 视频时长（秒）

        Returns:
            int: 所需代币数量
        """
        return int(video_duration * self.asr_qps) if video_duration else 0


    def calculate_trans_tokens(self,word_counts:int,translate_engine=None) ->int:
        """

        Args:
            word_counts: 翻译文本长度
            translate_engine:翻译模型

        Returns:
            int: 所需代币数量
        """
        # 根据不同的翻译引擎设置不同的算力消耗系数
        if translate_engine in ["chatGPT", "LocalLLM", "AzureGPT", "Gemini"]:
            # AI大模型翻译，消耗更多算力
            qps_count = 3
        elif translate_engine in ["DeepL", "DeepLx"]:
            # DeepL系列翻译，消耗中等算力
            qps_count = 2.5
        elif translate_engine in ["Google", "Microsoft", "Baidu", "Tencent"]:
            # 传统翻译API，消耗标准算力
            qps_count = 2
        else:
            # 其他翻译引擎，默认算力消耗
            qps_count = 1.5



        return int(word_counts * self.trans_qps) if word_counts else 0

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
        获取充值套餐列表

            Returns:
            dict: 充值套餐列表
        """
        try:
            # 获取充值套餐列表
            packages_data = api_client.recharge_packages_sync()

            # 解析响应数据获取充值套餐列表
            packages = packages_data.get('data', [])
            logger.info(f"充值套餐列表: {packages}")
            return packages
        except Exception as e:
            logger.error(f"获取充值套餐列表时发生错误: {str(e)}")
            return []

    def calculate_asr_tokens(self, duration_seconds: float) -> int:
        """
        计算ASR任务所需的代币数量

        Args:
            duration_seconds: 音频时长（秒）

        Returns:
            int: 所需代币数量
        """
        # 每分钟消费10个代币，不足一分钟按一分钟计算
        return max(1, int(duration_seconds / 60 + 0.5)) * 10

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

    def consume_tokens(self, token_amount: int, feature_key: str = "asr") -> bool:
        """
        消费代币

        Args:
            token_amount: 消费的代币数量
            feature_key: 功能标识符，默认为"asr"

        Returns:
            bool: 消费是否成功
        """
        try:
            # 调用api_client中的方法消费代币
            us_id = api_client.get_id()
            api_client.consume_tokens_sync(token_amount, feature_key,us_id)
            logger.info(f"消费代币成功: {token_amount}")
            return True

        except Exception as e:
            logger.error(f"消费代币时发生错误: {str(e)}")
            return False
