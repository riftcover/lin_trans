# 充值页面
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                              QFrame, QPushButton, QWidget)
from api_client import api_client
from utils import logger
from vendor.qfluentwidgets import (SubtitleLabel, BodyLabel, PrimaryPushButton, FluentIcon as FIF, StrongBodyLabel)
from vendor.qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase
from vendor.qfluentwidgets.common.style_sheet import FluentStyleSheet


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
                    border: 2px solid #3d7eff;
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
                    border: 1px solid #3d7eff;
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


class QRCodeWidget(QFrame):
    """二维码显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("qrCodeFrame")
        self.setStyleSheet("""
            #qrCodeFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                padding: 10px 10px 15px 10px;  /* 增加底部填充 */
            }
        """)

        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(10, 8, 10, 12)  # 增加底部边距
        self.vBoxLayout.setSpacing(6)

        # 添加标题
        self.titleLabel = SubtitleLabel("扫码支付", self)
        self.titleLabel.setAlignment(Qt.AlignCenter)

        # 添加二维码图像容器
        self.qrCodeContainer = QFrame(self)
        self.qrCodeContainer.setObjectName("qrCodeContainer")
        self.qrCodeContainer.setFixedSize(180, 180)  # 设置为正方形
        self.qrCodeContainer.setStyleSheet("""
            #qrCodeContainer {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-bottom: 15px;
            }
        """)

        # 二维码容器布局
        qrContainerLayout = QVBoxLayout(self.qrCodeContainer)
        qrContainerLayout.setContentsMargins(10, 10, 10, 10)  # 设置内边距
        qrContainerLayout.setSpacing(0)  # 无间距
        qrContainerLayout.setAlignment(Qt.AlignCenter)  # 居中对齐

        # 添加二维码图像
        self.qrCodeLabel = QLabel()
        self.qrCodeLabel.setAlignment(Qt.AlignCenter)
        self.qrCodeLabel.setFixedSize(160, 160)  # 调整为正方形
        self.qrCodeLabel.setStyleSheet("""
            background-color: white;
            border-radius: 4px;
        """)

        # 添加到容器布局
        qrContainerLayout.addWidget(self.qrCodeLabel, 0, Qt.AlignCenter)

        # 添加模拟支付按钮的容器（初始为空）
        self.buttonContainer = QWidget(self)
        self.buttonLayout = QHBoxLayout(self.buttonContainer)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(5)
        self.buttonLayout.setAlignment(Qt.AlignCenter)

        # 添加到布局
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.qrCodeContainer, 0, Qt.AlignCenter)

        # 在二维码容器下方添加更多空间
        self.vBoxLayout.addSpacing(25)  # 增加二维码容器与下方组件的间距

        # 添加提示文本
        self.hintLabel = BodyLabel("扫描二维码完成支付", self)
        self.hintLabel.setAlignment(Qt.AlignCenter)
        self.hintLabel.setWordWrap(True)  # 允许文本换行
        self.hintLabel.setStyleSheet("font-size: 12px; margin: 0px; padding: 0px;")
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.hintLabel)

        # 添加模拟支付按钮的容器
        self.buttonContainer = QWidget(self)
        self.buttonLayout = QHBoxLayout(self.buttonContainer)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setSpacing(5)
        self.buttonLayout.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.addSpacing(15)  # 增加提示文本与按钮之间的间距
        self.vBoxLayout.addWidget(self.buttonContainer)
        self.vBoxLayout.addSpacing(10)  # 在按钮下方添加额外的空间

        # 设置默认二维码
        self.setQRCode("请先选择充值金额")


    def clearButtons(self):
        """清除所有按钮"""
        # 清除按钮容器中的所有内容
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

    def setQRCode(self, text_or_image_path):
        """设置二维码图像或提示文本"""
        if text_or_image_path.startswith("http") or text_or_image_path.endswith((".png", ".jpg", ".jpeg")):
            # 显示二维码图像
            pixmap = QPixmap(text_or_image_path)
            if not pixmap.isNull():
                self.qrCodeLabel.setPixmap(pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # 如果加载失败，显示提示文本
                self.qrCodeLabel.setText("二维码加载失败")
                self.qrCodeLabel.setStyleSheet("""
                    background-color: #f5f5f5;
                    border: 1px dashed #cccccc;
                    border-radius: 4px;
                    width: 160px;
                    height: 160px;
                """)
        else:
            # 显示提示文本
            self.qrCodeLabel.setText(text_or_image_path)
            self.qrCodeLabel.setStyleSheet("background-color: #f5f5f5; border: 1px dashed #cccccc; width: 160px; height: 160px;")


class PurchaseDialog(MaskDialogBase):
    """算力购买对话框"""

    # 定义信号
    purchaseCompleted = Signal(dict)  # 购买完成信号，传递交易信息

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent = parent

        # 当前选择的充值金额
        self.selected_amount = 0

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

        # 添加二维码区域
        self._init_qrcode_section()

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
        self.balanceValue.setStyleSheet("color: #3d7eff;")

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

    def _init_recharge_cards(self):
        """初始化充值卡片网格"""
        # 创建网格布局
        self.cardsFrame = QFrame(self.widget)
        self.cardsLayout = QGridLayout(self.cardsFrame)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setSpacing(8)  # 减小卡片间的间距

        # 定义充值选项 (点数, 价格)
        recharge_options = [
            (100, "¥10"),
            (200, "¥20"),
            (500, "¥50"),
            (1000, "¥100"),
            (2000, "¥200"),
            (5000, "¥500")
        ]

        # 创建充值卡片
        self.rechargeCards = []
        for i, (amount, price) in enumerate(recharge_options):
            row = i // 3
            col = i % 3
            card = RechargeCard(amount, price, self.cardsFrame)
            card.clicked.connect(self._on_card_selected)
            self.cardsLayout.addWidget(card, row, col)
            self.rechargeCards.append(card)

        # 添加到主布局
        self.mainLayout.addWidget(self.cardsFrame)

        # 添加小间距以区分卡片和二维码区域
        self.mainLayout.addSpacing(5)

    def _init_qrcode_section(self):
        """初始化二维码部分"""
        self.qrCodeWidget = QRCodeWidget(self.widget)
        self.mainLayout.addWidget(self.qrCodeWidget)



    def _connect_signals(self):
        """连接信号和槽"""
        # 关闭按钮的信号已在_init_ui中连接

    def _update_balance(self):
        """更新当前余额"""
        try:
            balance_data = api_client.get_balance_sync()
            if balance_data and 'data' in balance_data:
                balance = balance_data['data'].get('balance', 0)
                self.balanceValue.setText(str(balance))
            else:
                self.balanceValue.setText("0")
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            self.balanceValue.setText("获取失败")

    def _on_card_selected(self, amount):
        """处理充值卡片选择事件"""
        self.selected_amount = amount

        # 更新卡片选中状态
        for card in self.rechargeCards:
            card.setSelected(card.amount == amount)

        # 更新二维码
        # 在实际应用中，这里应该根据选择的金额生成对应的支付二维码
        qr_code_text = f"请扫码支付 {amount} 点数"
        self.qrCodeWidget.setQRCode(qr_code_text)

        # 显示支付提示
        self.qrCodeWidget.setHint("请使用微信或支付宝扫码支付，支付完成后将自动关闭窗口")

        # 在实际应用中，这里应该启动一个轮询过程检查支付状态
        # 当支付成功后再调用process_purchase方法
        # 在演示中，我们可以添加一个模拟支付成功的按钮
        self._add_payment_simulation_button()

    def _add_payment_simulation_button(self):
        """添加模拟支付成功的按钮，并调用充值接口"""

        # 清除现有按钮
        self.qrCodeWidget.clearButtons()

        # 创建模拟支付成功按钮
        simulateButton = PrimaryPushButton("模拟支付成功", self.qrCodeWidget)
        simulateButton.setFixedHeight(30)  # 设置按钮高度更小

        # 定义点击事件处理函数
        def on_button_clicked():
            # 更新提示文本
            self.qrCodeWidget.setHint("正在处理充值请求...")

            # 禁用按钮防止重复点击
            simulateButton.setEnabled(False)

            try:
                # 调用充值接口
                us_id = api_client.get_id()
                logger.info(f'user_id:{us_id}')
                result = api_client.recharge_tokens_sync(us_id,self.selected_amount)

                # 处理成功响应
                if result and 'data' in result:
                    # 从响应中提取交易信息
                    transaction_data = result['data']
                    logger.info(f'transaction_data:{transaction_data}')

                    # 更新提示文本
                    self.qrCodeWidget.setHint("支付成功！正在处理...")

                    # 清除模拟按钮
                    self.qrCodeWidget.clearButtons()

                    # 发送购买完成信号
                    self.purchaseCompleted.emit(transaction_data)

                    # 更新余额
                    self._update_balance()

                    # 关闭对话框
                    self.accept()
                else:
                    # 处理响应中没有数据的情况
                    raise Exception("充值响应数据不完整")

            except Exception as e:
                # 处理其他错误
                logger.error(f"充值失败: {e}")
                self.qrCodeWidget.setHint(f"支付失败: {e}")
                # 重新启用按钮
                simulateButton.setEnabled(True)

        # 连接点击事件
        simulateButton.clicked.connect(on_button_clicked)

        # 添加到二维码组件
        self.qrCodeWidget.addButton(simulateButton)


# # 如果直接运行该文件，则打开充值对话框进行测试
# if __name__ == "__main__":
#     import sys
#     import traceback
#
#     # 创建应用
#     app = QApplication(sys.argv)
#
#     try:
#         # 创建主窗口（作为充值对话框的父窗口）
#         mainWindow = QWidget()
#         mainWindow.setWindowTitle("充值对话框测试")
#         mainWindow.resize(800, 600)
#         mainWindow.show()
#
#         # 创建并显示充值对话框
#         dialog = PurchaseDialog(mainWindow)
#
#         # 覆盖API调用方法，避免实际调用API导致的错误
#         def mock_get_balance_sync():
#             print("模拟获取余额")
#             return {"data": {"balance": 1000}}
#
#         # 替换API调用
#         dialog._update_balance = lambda: dialog.balanceValue.setText("1000")
#
#         # 连接购买完成信号
#         def on_purchase_completed(transaction):
#             print(f"购买完成: {transaction}")
#
#         dialog.purchaseCompleted.connect(on_purchase_completed)
#
#         # 显示对话框
#         dialog.exec()
#
#     except Exception as e:
#         print(f"错误: {e}")
#         traceback.print_exc()
#
#     # 退出应用
#     sys.exit(app.exec())
