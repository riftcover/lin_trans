# 充值页面
from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QPixmap, QColor, QDesktopServices
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                               QFrame, QPushButton, QWidget)

from api_client import api_client
from nice_ui.services.service_provider import ServiceProvider
from nice_ui.services.simple_api_service import simple_api_service
from utils import logger
from vendor.qfluentwidgets import (SubtitleLabel, BodyLabel, PrimaryPushButton, FluentIcon as FIF, StrongBodyLabel)
from vendor.qfluentwidgets.common.style_sheet import FluentStyleSheet
from vendor.qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase


class RechargeCard(QFrame):
    """充值卡片组件"""

    clicked = Signal(int)  # 点击信号，传递充值点数

    def __init__(self, amount: int, price: str, parent=None):
        """
        初始化充值卡片

        Args:
            amount: 充值点数
            price: 价格显示文本
            parent: 父组件
        """
        super().__init__(parent=parent)
        self.amount = amount
        self.isSelected = False

        # 设置样式
        self.setObjectName("rechargeCard")
        self._updateStyle()

        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(10, 6, 10, 6)  # 减小边距
        self.vBoxLayout.setSpacing(1)  # 减小间距

        # 添加点数标签
        self.amountLabel = StrongBodyLabel(f"{amount}", self)
        self.amountLabel.setAlignment(Qt.AlignCenter)
        self.amountLabel.setStyleSheet("font-size: 18px;")  # 调整字体大小

        # 添加单位标签
        self.unitLabel = BodyLabel("点数", self)
        self.unitLabel.setAlignment(Qt.AlignCenter)
        self.unitLabel.setStyleSheet("font-size: 12px;")  # 调整字体大小

        # 添加价格标签
        self.priceLabel = BodyLabel(price, self)
        self.priceLabel.setAlignment(Qt.AlignCenter)
        self.priceLabel.setStyleSheet("color: #ff6d6d; font-size: 14px;")  # 调整字体大小和颜色

        # 添加到布局
        self.vBoxLayout.addWidget(self.amountLabel)
        self.vBoxLayout.addWidget(self.unitLabel)
        self.vBoxLayout.addWidget(self.priceLabel)

        # 设置固定大小
        self.setFixedSize(160, 80)

        # 设置鼠标追踪
        self.setMouseTracking(True)

    def _updateStyle(self):
        """更新样式"""
        if self.isSelected:
            self.setStyleSheet("""
                #rechargeCard {
                    background-color: #e8f0fe;
                    border-radius: 6px;
                    border: 2px solid #7C3AED;
                    padding: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                #rechargeCard {
                    background-color: #f5f5f5;
                    border-radius: 6px;
                    border: 1px solid #e0e0e0;
                    padding: 5px;
                }
                #rechargeCard:hover {
                    background-color: #e8f0fe;
                    border: 1px solid #7C3AED;
                }
            """)

    def setSelected(self, selected: bool):
        """设置选中状态"""
        self.isSelected = selected
        self._updateStyle()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)
        self.clicked.emit(self.amount)


class PaymentActionWidget(QFrame):
    """支付操作组件"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("paymentActionFrame")
        self.setStyleSheet("""
            #paymentActionFrame {
                background-color: #fafafa;
                border-radius: 10px;
                border: 1px solid #e8e8e8;
                padding: 15px;
            }
        """)

        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(5, 5, 5, 5)
        self.vBoxLayout.setSpacing(12)

        # --- 头部布局 ---
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setSpacing(10)

        # 支付宝图标
        self.alipayIconLabel = QLabel(self)
        self.alipayIconLabel.setPixmap(QPixmap(":icon/assets/alipay.png").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.alipayIconLabel.setFixedSize(28, 28)

        # 标题
        self.titleLabel = SubtitleLabel("支付宝", self)

        self.headerLayout.addWidget(self.alipayIconLabel)
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch()

        # 添加分隔线
        self.separator = QFrame(self)
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setStyleSheet("background-color: #e0e0e0;")

        # 添加提示文本
        self.hintLabel = BodyLabel("选择充值套餐后，将跳转至支付宝完成支付", self)
        self.hintLabel.setAlignment(Qt.AlignCenter)
        self.hintLabel.setWordWrap(True)
        self.hintLabel.setStyleSheet("font-size: 13px; color: #606060;")

        # 添加按钮容器
        self.buttonContainer = QWidget(self)
        self.buttonLayout = QHBoxLayout(self.buttonContainer)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(5)
        self.buttonLayout.setAlignment(Qt.AlignCenter)

        # 添加到布局
        self.vBoxLayout.addLayout(self.headerLayout)
        self.vBoxLayout.addWidget(self.separator)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.hintLabel)
        self.vBoxLayout.addWidget(self.buttonContainer)
        self.vBoxLayout.addStretch(1)

    def clearButtons(self):
        """清除所有按钮"""
        while self.buttonLayout.count():
            item = self.buttonLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def addButton(self, button):
        """添加按钮到容器中"""
        self.buttonLayout.addWidget(button)

    def setHint(self, text):
        """设置提示文本"""
        self.hintLabel.setText(text)


class PurchaseDialog(MaskDialogBase):
    """算力购买对话框"""

    # 定义信号
    purchaseCompleted = Signal(dict)  # 购买完成信号，传递交易信息

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent

        # 当前选择的充值金额
        self.selected_amount = 0
        self.selected_price = 0
        self.recharge_options = []

        # 支付轮询相关
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(3000)  # 每3秒轮询一次
        self.current_order_id = None
        self.poll_count = 0
        self.max_poll_count = 100  # 最多轮询100次 (5分钟)

        # 设置对话框属性
        self.setWindowTitle("购买算力")
        self.widget.setFixedWidth(600)
        self.widget.setMinimumHeight(600)

        # 设置阴影和遮罩
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))

        # 创建主布局
        self.mainLayout = QVBoxLayout(self.widget)
        self.mainLayout.setContentsMargins(24, 24, 24, 24)
        self.mainLayout.setSpacing(15)

        # 初始化UI
        self._init_ui()

        # 连接信号
        self._connect_signals()

        # 应用样式
        FluentStyleSheet.DIALOG.apply(self)

    def reject(self):
        """重写拒绝操作，确保计时器停止"""
        if self.poll_timer.isActive():
            self.poll_timer.stop()
            logger.info("Payment polling stopped by user closing dialog.")
        super().reject()

    def _init_ui(self):
        """初始化UI"""
        # 创建标题栏布局
        self.titleBarLayout = QHBoxLayout()
        self.titleBarLayout.setContentsMargins(0, 0, 0, 10)

        # 添加标题
        self.titleLabel = SubtitleLabel("购买算力", self.widget)

        # 添加关闭按钮
        self.closeButton = QPushButton(self.widget)
        self.closeButton.setIcon(FIF.CLOSE.icon())
        self.closeButton.setFixedSize(32, 32)
        self.closeButton.setObjectName("closeButton")
        self.closeButton.setStyleSheet("""
            #closeButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
            }
            #closeButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
            #closeButton:pressed {
                background-color: rgba(0, 0, 0, 0.15);
            }
        """)
        self.closeButton.clicked.connect(self.reject)

        # 添加到标题栏布局
        self.titleBarLayout.addWidget(self.titleLabel)
        self.titleBarLayout.addStretch()
        self.titleBarLayout.addWidget(self.closeButton)

        # 添加标题栏到主布局
        self.mainLayout.addLayout(self.titleBarLayout)

        # 添加当前余额显示
        self._init_balance_section()

        # 添加充值卡片网格
        self._init_recharge_cards()

        # 添加支付方式区域
        self._init_payment_action_section()

    def _init_balance_section(self):
        """初始化余额显示部分"""
        # 创建余额显示框架
        self.balanceFrame = QFrame(self.widget)
        self.balanceFrame.setObjectName("balanceFrame")
        self.balanceFrame.setStyleSheet("""
            #balanceFrame {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        # 创建水平布局
        self.balanceLayout = QHBoxLayout(self.balanceFrame)
        self.balanceLayout.setContentsMargins(15, 10, 15, 10)

        # 添加余额标签
        self.balanceLabel = BodyLabel("当前算力余额:", self.balanceFrame)

        # 添加余额值
        self.balanceValue = SubtitleLabel("0", self.balanceFrame)
        self.balanceValue.setStyleSheet("color: #7C3AED;")

        # 添加单位
        self.balanceUnit = BodyLabel("点数", self.balanceFrame)

        # 添加到布局
        self.balanceLayout.addWidget(self.balanceLabel)
        self.balanceLayout.addWidget(self.balanceValue)
        self.balanceLayout.addWidget(self.balanceUnit)
        self.balanceLayout.addStretch()

        # 添加到主布局
        self.mainLayout.addWidget(self.balanceFrame)

        # 获取并更新当前余额
        self._update_balance()

        # 添加小间距以区分卡片和二维码区域
        self.mainLayout.addSpacing(5)

    def _init_recharge_cards(self):
        """初始化充值卡片网格"""
        # 创建网格布局
        self.cardsFrame = QFrame(self.widget)
        self.cardsLayout = QGridLayout(self.cardsFrame)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setSpacing(8)  # 减小卡片间的间距

        # 定义充值选项 (直接使用预定义数据，避免不必要的异步复杂性)
        self.recharge_options = [
            {'price': 10, 'token_amount': 2000},
            {'price': 20, 'token_amount': 4100},
            {'price': 50, 'token_amount': 10750},
            {'price': 75, 'token_amount': 16865},
            {'price': 100, 'token_amount': 23500},
            {'price': 150, 'token_amount': 36750}
        ]

        # 创建充值卡片
        self.rechargeCards = []
        for i, package in enumerate(self.recharge_options):
            row = i // 3
            col = i % 3
            amount = package.get('token_amount')
            price = f"￥{package.get('price')}"
            card = RechargeCard(amount, price, self.cardsFrame)
            card.clicked.connect(self._on_card_selected)
            self.cardsLayout.addWidget(card, row, col)
            self.rechargeCards.append(card)

        # 添加到主布局
        self.mainLayout.addWidget(self.cardsFrame)

    def _init_payment_action_section(self):
        """初始化支付操作部分"""
        self.paymentActionWidget = PaymentActionWidget(self.widget)
        self.mainLayout.addWidget(self.paymentActionWidget)

    def _connect_signals(self):
        """连接信号和槽"""
        # 关闭按钮的信号已在_init_ui中连接

    def _update_balance(self):
        """更新当前余额（异步）"""
        def on_success(result):
            if result and 'data' in result:
                balance = result['data'].get('balance', 0)
                self.balanceValue.setText(str(balance))
            else:
                self.balanceValue.setText("0")

        def on_error(error):
            logger.error(f"获取余额失败: {error}")
            self.balanceValue.setText("获取失败")

        simple_api_service.get_balance(callback_success=on_success, callback_error=on_error)

    def _on_card_selected(self, amount):
        """处理充值卡片选择事件"""
        self.selected_amount = amount

        # 从充值选项中找到对应的价格
        selected_option = next((opt for opt in self.recharge_options if opt.get('token_amount') == amount), None)
        if not selected_option:
            logger.error(f"Selected amount {amount} not found in recharge options.")
            self.paymentActionWidget.setHint("无效的充值选项")
            self.paymentActionWidget.clearButtons()
            return
        self.selected_price = selected_option.get('price', 0)

        # 更新卡片选中状态
        for card in self.rechargeCards:
            card.setSelected(card.amount == amount)

        # 更新支付区域的提示
        self.paymentActionWidget.setHint(f"您将使用支付宝支付 {self.selected_price} 元，购买 {self.selected_amount} 点数")

        # 添加创建订单按钮
        self._add_create_order_button()

    def _add_create_order_button(self):
        """添加创建订单按钮"""
        # 清除现有按钮
        self.paymentActionWidget.clearButtons()

        # 创建支付按钮
        createOrderButton = PrimaryPushButton("前往支付宝支付", self.paymentActionWidget)
        createOrderButton.setFixedHeight(30)

        def on_button_clicked():
            createOrderButton.setEnabled(False)
            createOrderButton.setText("正在创建订单...")
            self.paymentActionWidget.setHint("正在创建订单，请稍候...")

            # 异步创建订单
            self._create_recharge_order(createOrderButton)

        createOrderButton.clicked.connect(on_button_clicked)
        self.paymentActionWidget.addButton(createOrderButton)

    def _start_polling(self):
        """开始轮询支付状态"""
        if self.poll_timer.isActive():
            self.poll_timer.stop()

        self.poll_count = 0
        # 使用 lambda 来确保每次连接都是新的，避免重复连接同一个旧槽
        try:
            self.poll_timer.timeout.disconnect()
        except RuntimeError:
            pass  # 信号从未连接过
        self.poll_timer.timeout.connect(self._check_payment_status)
        self.poll_timer.start()
        logger.info(f"Started polling for order_id: {self.current_order_id}")

    def _check_payment_status(self):
        """检查支付状态的回调函数"""
        if not self.current_order_id:
            self.poll_timer.stop()
            return

        self.poll_count += 1
        logger.trace(f"Polling attempt #{self.poll_count} for order {self.current_order_id}")

        if self.poll_count > self.max_poll_count:
            self.poll_timer.stop()
            logger.warning(f"Polling timed out for order {self.current_order_id}")
            self.paymentActionWidget.setHint("支付状态查询超时，请稍后手动查询余额。")
            return

        # 异步查询订单状态
        self._check_order_status_async()

    def _create_recharge_order(self, button):
        """异步创建充值订单"""
        # 获取用户ID（同步方法，因为它只是从内存中获取）
        user_id = api_client.get_id()
        if not user_id:
            logger.error("无法获取用户ID，请重新登录")
            self.paymentActionWidget.setHint("无法获取用户ID，请重新登录")
            button.setText("重试")
            button.setEnabled(True)
            return

        def on_success(result):
            if result and 'data' in result:
                payment_url = result['data'].get('payment_url')
                self.current_order_id = result['data'].get('order_id')

                if payment_url and self.current_order_id:
                    # 打开支付链接
                    QDesktopServices.openUrl(QUrl(payment_url))
                    self.paymentActionWidget.setHint(
                        "支付页面已在浏览器中打开，请完成支付。\n支付成功后此窗口将自动关闭。"
                    )
                    # 启动轮询
                    self._start_polling()
                    button.setVisible(False)  # 隐藏按钮，防止重复点击
                else:
                    logger.error("API返回数据不完整，缺少 payment_url 或 order_id")
                    self.paymentActionWidget.setHint("API返回数据不完整")
                    button.setText("重试")
                    button.setEnabled(True)
            else:
                logger.error("创建订单失败，API返回数据格式不正确")
                self.paymentActionWidget.setHint("创建订单失败，API返回数据格式不正确")
                button.setText("重试")
                button.setEnabled(True)

        def on_error(error):
            logger.error(f"创建充值订单失败: {error}")
            self.paymentActionWidget.setHint(f"创建订单失败: {str(error)}")
            button.setText("重试")
            button.setEnabled(True)

        simple_api_service.execute_async(
            api_client.create_recharge_order,
            args=(user_id, self.selected_price, self.selected_amount),
            callback_success=on_success,
            callback_error=on_error
        )

    def _check_order_status_async(self):
        """异步检查订单状态"""
        def on_success(result):
            if result and 'data' in result:
                status = result['data'].get('status')
                logger.info(f"Order {self.current_order_id} status: {status}")

                if status == 'COMPLETED':
                    self.poll_timer.stop()
                    logger.info(f"Order {self.current_order_id} completed successfully.")
                    self.paymentActionWidget.setHint("支付成功")

                    # 触发购买完成信号 (可以传递需要的数据)
                    self.purchaseCompleted.emit(result['data'])

                    # 延迟一小会，然后关闭窗口
                    QTimer.singleShot(1500, self.accept)

                elif status == 'FAILED':
                    self.poll_timer.stop()
                    logger.warning(f"Order {self.current_order_id} has status: {status}")
                    self.paymentActionWidget.setHint("支付失败或订单已过期。")
                # else status is 'pending', do nothing and wait for next poll

        def on_error(error):
            logger.error(f"Error while polling for payment status: {error}")
            # 可以在几次失败后停止轮询
            if self.poll_count > 5:  # 如果连续失败5次
                self.poll_timer.stop()
                self.paymentActionWidget.setHint("查询支付状态时发生网络错误。")

        simple_api_service.execute_async(
            api_client.get_order_status,
            args=(self.current_order_id,),
            callback_success=on_success,
            callback_error=on_error
        )


# 如果直接运行该文件，则打开充值对话框进行测试
if __name__ == "__main__":
    import sys
    import traceback
    from PySide6.QtWidgets import QApplication

    # 创建应用
    app = QApplication(sys.argv)

    try:
        # 创建主窗口（作为充值对话框的父窗口）
        mainWindow = QWidget()
        mainWindow.setWindowTitle("充值对话框测试")
        mainWindow.resize(800, 600)
        mainWindow.show()

        # 创建并显示充值对话框
        dialog = PurchaseDialog(mainWindow)

        # 覆盖API调用方法，避免实际调用API导致的错误
        def mock_get_balance_sync():
            print("模拟获取余额")
            return {"data": {"balance": 1000}}

        # 替换API调用
        dialog._update_balance = lambda: dialog.balanceValue.setText("1000")

        # 连接购买完成信号
        def on_purchase_completed(transaction):
            print(f"购买完成: {transaction}")

        dialog.purchaseCompleted.connect(on_purchase_completed)

        # 显示对话框
        dialog.exec()

    except Exception as e:
        print(f"错误: {e}")
        traceback.print_exc()

    # 退出应用
    sys.exit(app.exec())
