from typing import Optional, Dict, Any

from nice_ui.interfaces.token import TokenServiceInterface
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
        if getattr(self, '_initialized', False):
            return
        self.ui_manager = ui_manager
        self._initialized = True
    
    def get_user_balance(self) -> int:
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
                return 0
                
        except AuthenticationError as e:
            logger.error(f"认证错误，无法获取代币余额: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"获取代币余额时发生错误: {str(e)}")
            return 0
    
    def calculate_asr_tokens(self, video_duration: float) -> int:
        """
        计算ASR任务所需代币
        
        Args:
            video_duration: 视频时长（秒）
            
        Returns:
            int: 所需代币数量
        """
        from nice_ui.configure import config
        if not video_duration:
            return 0
        # 根据配置计算ASR任务所需代币
        # 这里使用config.asr_qps作为计算因子，您可能需要根据实际情况调整
        return int(video_duration * config.trans_qps)
    
    def calculate_translation_tokens(self, word_count: int) -> int:
        """
        计算翻译任务所需代币
        
        Args:
            word_count: 单词数量
            
        Returns:
            int: 所需代币数量
        """
        from nice_ui.configure import config
        if not word_count:
            return 0
        # 根据配置计算翻译任务所需代币
        # 这里使用config.trans_qps作为计算因子，您可能需要根据实际情况调整
        return int(word_count * getattr(config, 'trans_qps', 0.1))
    
    def is_balance_sufficient(self, required_tokens: int) -> bool:
        """
        检查余额是否足够
        
        Args:
            required_tokens: 所需代币数量
            
        Returns:
            bool: 余额是否足够
        """
        current_balance = self.get_user_balance()
        return current_balance >= required_tokens
    
    def prompt_recharge_dialog(self) -> bool:
        """
        弹出充值对话框并等待用户操作
        
        Returns:
            bool: True表示充值成功或用户确认继续，False表示取消
        """
        from PySide6.QtWidgets import QMessageBox, QApplication
        from nice_ui.ui.purchase_dialog import PurchaseDialog
        
        # 创建对话框
        msg_box = QMessageBox()
        msg_box.setWindowTitle("代币不足")
        msg_box.setText("您的代币余额不足以完成当前任务。")
        msg_box.setInformativeText("是否前往充值页面进行充值？")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        
        # 显示对话框并获取用户选择
        result = msg_box.exec()
        
        if result == QMessageBox.Yes:
            # 用户选择了"是"，打开充值对话框
            try:
                # 获取主窗口实例
                main_window = None
                for widget in QApplication.topLevelWidgets():
                    if widget.objectName() == "MainWindow":
                        main_window = widget
                        break
                
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
                        return True
                    else:
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
