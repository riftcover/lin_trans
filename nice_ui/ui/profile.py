from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout)
from api_client import api_client
from utils import logger
from vendor.qfluentwidgets import (SimpleCardWidget, PushButton, FluentIcon as FIF, IconWidget, SubtitleLabel, BodyLabel, PrimaryPushButton, InfoBar, InfoBarPosition)

# 导入自定义组件
from components.widget.transaction_table import TransactionTableWidget


class ProfileInterface(QFrame):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.parent = parent

        # 父窗口引用
        self.parent_window = parent

        # 设置对象名称
        self.setObjectName(text.replace(" ", "-"))

        # 创建主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 0)

        # 创建标题栏
        self.titleBar = QHBoxLayout()
        self.titleLabel = SubtitleLabel('个人中心', self)
        self.logoutButton = PrimaryPushButton('退出登录', self)
        self.logoutButton.setFixedWidth(100)
        self.logoutButton.setVisible(False)  # 初始状态隐藏退出按钮
        self.titleBar.addWidget(self.titleLabel)
        self.titleBar.addStretch()
        self.titleBar.addWidget(self.logoutButton)
        self.vBoxLayout.addLayout(self.titleBar)

        # 账号信息卡片
        self.accountCard = SimpleCardWidget(self)
        self.accountLayout = QVBoxLayout(self.accountCard)

        # 账号信息标题
        self.accountTitle = SubtitleLabel('账号信息', self)
        self.accountLayout.addWidget(self.accountTitle)

        # 创建一个容器来包含所有账户信息
        self.accountInfoContainer = QFrame()
        self.accountInfoContainer.setObjectName('accountInfoContainer')
        self.accountInfoLayout = QVBoxLayout(self.accountInfoContainer)
        self.accountInfoLayout.setContentsMargins(0, 0, 0, 0)
        self.accountInfoLayout.setSpacing(15)  # 调整垂直间距

        # 邮箱地址
        self.emailLayout = QHBoxLayout()
        self.emailIcon = IconWidget(FIF.MAIL, self)
        self.emailIcon.setFixedSize(13, 13)

        # 创建垂直布局来包含邮箱标签和值
        self.emailContentLayout = QVBoxLayout()
        self.emailContentLayout.setContentsMargins(20, 10, 10, 0)

        self.emailLabel = BodyLabel('邮箱地址', self)
        self.emailValue = BodyLabel('未登录', self)
        self.emailLabel.setStyleSheet('color: #666666;')
        self.emailValue.setStyleSheet("""
            QLabel {
                font-size: 14px;
                background: transparent;
                border-bottom: 2px solid #dd3187;
                margin: 1px;
                min-height: 20px;
            }
        """)

        # 将图标和垂直布局添加到水平布局中
        self.emailLayout.addWidget(self.emailIcon)
        self.emailLayout.addWidget(self.emailLabel)
        self.emailLayout.addStretch()

        # 将标签和值添加到垂直布局中
        self.emailContentLayout.addLayout(self.emailLayout)
        self.emailContentLayout.addWidget(self.emailValue)
        self.emailContentLayout.setSpacing(4)

        # 算力额度
        # 创建垂直布局来包含算力所有内容
        self.quotaContentLayout = QVBoxLayout()
        self.quotaContentLayout.setContentsMargins(20, 10, 10, 0)

        # 创建水平布局来包含标题和icon
        self.quotaTitleLayout = QHBoxLayout()
        self.quotaIcon = IconWidget(FIF.SPEED_HIGH, self)
        self.quotaIcon.setFixedSize(13, 13)
        self.quotaLabel = BodyLabel('算力额度', self)
        self.quotaLabel.setStyleSheet('color: #666666;')

        self.quotaTitleLayout.addWidget(self.quotaIcon)
        self.quotaTitleLayout.addWidget(self.quotaLabel)
        self.quotaTitleLayout.addStretch()

        # 创建水平布局来包含值和单位
        self.quotaValue = SubtitleLabel('0', self)
        self.quotaUnit = BodyLabel('点数', self)

        self.quotaValueLayout = QHBoxLayout()
        self.quotaValueLayout.addWidget(self.quotaValue)
        self.quotaValueLayout.addWidget(self.quotaUnit)
        self.quotaValueLayout.addStretch()

        # 当前剩余可用算力提示
        self.quotaHint = BodyLabel('当前剩余可用算力额度', self)
        self.quotaHint.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                background: transparent;
                border-bottom: 2px solid #dd3187;
                margin: 1px;
                min-height: 20px;
            }
        """)

        # 将标签和值布局添加到垂直布局中
        self.quotaContentLayout.addLayout(self.quotaTitleLayout)
        self.quotaContentLayout.addLayout(self.quotaValueLayout)
        self.quotaContentLayout.addWidget(self.quotaHint)
        self.quotaContentLayout.setSpacing(4)

        # 将邮箱和算力布局添加到账户信息容器中
        self.accountInfoLayout.addLayout(self.emailContentLayout)
        self.accountInfoLayout.addLayout(self.quotaContentLayout)

        # 将账户信息容器添加到卡片布局中
        self.accountLayout.addWidget(self.accountInfoContainer)

        # 购买算力按钮
        self.buyButton = PushButton('购买算力', self)
        self.buyButton.setIcon(FIF.ADD)
        self.accountLayout.addWidget(self.buyButton)

        self.vBoxLayout.addWidget(self.accountCard)

        # 使用记录卡片
        self.usageCard = SimpleCardWidget(self)
        self.usageLayout = QVBoxLayout(self.usageCard)

        # 使用记录标题
        self.usageTitle = SubtitleLabel('使用记录', self)
        self.usageLayout.addWidget(self.usageTitle)

        # 创建交易记录分页表格
        self.transactionTable = TransactionTableWidget(self, page_size=10)

        # 添加分页表格到布局
        self.usageLayout.addWidget(self.transactionTable)

        self.vBoxLayout.addWidget(self.usageCard)
        self.vBoxLayout.addStretch()

        # 连接退出登录按钮的信号
        self.logoutButton.clicked.connect(self.handleLogout)

    def updateUserInfo(self, user_info: dict):
        """更新用户信息"""
        # 更新邮箱地址
        email = user_info.get('email', '未登录')
        self.emailValue.setText(email)

        try:
            # 更新算力额度
            balance_data = api_client.get_balance_sync()
            if balance_data and 'data' in balance_data:
                balance = balance_data['data'].get('balance', 0)
                self.quotaValue.setText(str(balance))
            else:
                self.quotaValue.setText('0')

            # 更新使用记录
            self.updateUsageHistory()
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")

        # 显示退出按钮
        self.logoutButton.setVisible(True)

    def updateUsageHistory(self, new_transactions=None):
        """更新使用记录表格

        Args:
            new_transactions: 可选，新的交易记录列表，如果提供则添加到现有记录中
        """
        try:
            # 如果没有提供新交易记录，则从API获取所有记录
            if new_transactions is None:
                history_data = api_client.get_history_sync()
                if not history_data or 'data' not in history_data:
                    return

                # 获取交易记录并设置到分页表格中
                transactions = history_data['data'].get('transactions', [])
                self.transactionTable.set_data(transactions)
            else:
                # 如果提供了新交易记录，添加到列表中
                self.transactionTable.set_data(new_transactions, reset_page=False)

        except Exception as e:
            logger.error(f"更新使用记录失败: {e}")



    def handleLogout(self):
        """处理退出登录"""
        # 重置用户信息显示
        self.emailValue.setText('未登录')
        self.quotaValue.setText('0')
        self.logoutButton.setVisible(False)  # 退出后隐藏退出按钮

        # 清空使用记录表格
        self.transactionTable.set_data([])

        # 清除保存的登录状态
        if self.settings:
            self.settings.remove('token')
            self.settings.sync()

        # 清除API客户端的token
        api_client.clear_token()

        # 通知主窗口退出登录
        if self.parent:
            self.parent.is_logged_in = False
            self.parent.avatarWidget.setName('未登录')
            self.parent.avatarWidget.setAvatar(':icon/assets/default_avatar.png')

        # 显示退出成功提示
        InfoBar.success(
            title='成功',
            content='已退出登录',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
