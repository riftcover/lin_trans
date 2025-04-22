from typing import List

from nice_ui.interfaces.token import TokenServiceInterface, RechargePackage
from nice_ui.interfaces.ui_manager import UIManagerInterface
from api_client import api_client, AuthenticationError
from utils import logger


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
        self._initialized = True

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

    def calculate_asr_tokens(self, video_duration: float) -> int:
        """
        计算ASR任务所需代币

        Args:
            video_duration: 视频时长（秒）

        Returns:
            int: 所需代币数量
        """
        from nice_ui.configure import config
        return int(video_duration * config.trans_qps) if video_duration else 0

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
