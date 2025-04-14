from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout)
from api_client import api_client, AuthenticationError
from utils import logger
from vendor.qfluentwidgets import (SimpleCardWidget, PushButton, FluentIcon as FIF, IconWidget, SubtitleLabel, BodyLabel, PrimaryPushButton, InfoBar,
                                   InfoBarPosition)

# 导入自定义组件
from components.widget.transaction_table import TransactionTableWidget
from nice_ui.ui.purchase_dialog import PurchaseDialog


class ProfileInterface(QFrame):
    # 样式常量
    LABEL_STYLE = 'color: #666666;'
    VALUE_STYLE = """
        QLabel {
            font-size: 14px;
            background: transparent;
            border-bottom: 2px solid #3d7eff;
            margin: 1px;
            min-height: 20px;
        }
    """

    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.parent = parent
        self.parent_window = parent  # 父窗口引用

        # 当前页码和每页记录数
        self.current_page = 1
        self.page_size = 10  # 每页显示10条记录
        self.total_pages = 1
        self.total_records = 0

        # 设置对象名称
        self.setObjectName(text.replace(" ", "-"))

        # 初始化UI组件
        self._setup_ui()

        # 连接信号
        self._connect_signals()

    def _setup_ui(self):
        """设置UI布局和组件"""
        # 创建主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 0)

        # 初始化各个部分
        self._init_title_bar()
        self._init_account_card()
        self._init_usage_card()

        # 添加底部弹性空间
        self.vBoxLayout.addStretch()

    def _connect_signals(self):
        """连接信号和槽"""
        self.logoutButton.clicked.connect(self.handleLogout)
        self.buyButton.clicked.connect(self.showPurchaseDialog)

        # 连接分页表格的页码改变信号
        self.transactionTable.pageChanged.connect(self.onPageChanged)

    def _init_title_bar(self):
        """初始化标题栏"""
        self.titleBar = QHBoxLayout()
        self.titleLabel = SubtitleLabel('个人中心', self)
        self.logoutButton = PrimaryPushButton('退出登录', self)
        self.logoutButton.setFixedWidth(100)
        self.logoutButton.setVisible(False)  # 初始状态隐藏退出按钮

        self.titleBar.addWidget(self.titleLabel)
        self.titleBar.addStretch()
        self.titleBar.addWidget(self.logoutButton)

        self.vBoxLayout.addLayout(self.titleBar)

    def _init_account_card(self):
        """初始化账号信息卡片"""
        self.accountCard = SimpleCardWidget(self)
        self.accountLayout = QVBoxLayout(self.accountCard)

        # 账号信息标题
        self.accountTitle = SubtitleLabel('账号信息', self)
        self.accountLayout.addWidget(self.accountTitle)

        # 创建账户信息容器
        self._init_account_info_container()

        # 购买算力按钮
        self.buyButton = PushButton('购买算力', self)
        self.buyButton.setIcon(FIF.ADD)
        self.accountLayout.addWidget(self.buyButton)

        self.vBoxLayout.addWidget(self.accountCard)

    def _init_account_info_container(self):
        """初始化账户信息容器"""
        self.accountInfoContainer = QFrame()
        self.accountInfoContainer.setObjectName('accountInfoContainer')
        self.accountInfoLayout = QVBoxLayout(self.accountInfoContainer)
        self.accountInfoLayout.setContentsMargins(0, 0, 0, 0)
        self.accountInfoLayout.setSpacing(15)  # 调整垂直间距

        # 初始化邮箱信息部分
        self._init_email_section()

        # 初始化算力额度部分
        self._init_quota_section()

        # 将账户信息容器添加到卡片布局中
        self.accountLayout.addWidget(self.accountInfoContainer)

    def _init_email_section(self):
        """初始化邮箱信息部分"""
        # 创建垂直布局来包含邮箱标签和值
        self.emailContentLayout = QVBoxLayout()
        self.emailContentLayout.setContentsMargins(20, 10, 10, 0)
        self.emailContentLayout.setSpacing(4)

        # 邮箱标题行
        self.emailLayout = QHBoxLayout()
        self.emailIcon = IconWidget(FIF.MAIL, self)
        self.emailIcon.setFixedSize(13, 13)
        self.emailLabel = BodyLabel('邮箱地址', self)
        self.emailLabel.setStyleSheet(self.LABEL_STYLE)

        self.emailLayout.addWidget(self.emailIcon)
        self.emailLayout.addWidget(self.emailLabel)
        self.emailLayout.addStretch()

        # 邮箱值
        self.emailValue = BodyLabel('未登录', self)
        self.emailValue.setStyleSheet(self.VALUE_STYLE)

        # 将标签和值添加到垂直布局中
        self.emailContentLayout.addLayout(self.emailLayout)
        self.emailContentLayout.addWidget(self.emailValue)

        # 添加到账户信息布局
        self.accountInfoLayout.addLayout(self.emailContentLayout)

    def _init_quota_section(self):
        """初始化算力额度部分"""
        # 创建垂直布局来包含算力所有内容
        self.quotaContentLayout = QVBoxLayout()
        self.quotaContentLayout.setContentsMargins(20, 10, 10, 0)
        self.quotaContentLayout.setSpacing(4)

        # 算力标题行
        self.quotaTitleLayout = QHBoxLayout()
        self.quotaIcon = IconWidget(FIF.SPEED_HIGH, self)
        self.quotaIcon.setFixedSize(13, 13)
        self.quotaLabel = BodyLabel('算力额度', self)
        self.quotaLabel.setStyleSheet(self.LABEL_STYLE)

        self.quotaTitleLayout.addWidget(self.quotaIcon)
        self.quotaTitleLayout.addWidget(self.quotaLabel)
        self.quotaTitleLayout.addStretch()

        # 算力值和单位
        self.quotaValueLayout = QHBoxLayout()
        self.quotaValue = SubtitleLabel('0', self)
        self.quotaUnit = BodyLabel('点数', self)

        self.quotaValueLayout.addWidget(self.quotaValue)
        self.quotaValueLayout.addWidget(self.quotaUnit)
        self.quotaValueLayout.addStretch()

        # 算力提示
        self.quotaHint = BodyLabel('当前剩余可用算力额度', self)
        self.quotaHint.setStyleSheet(self.VALUE_STYLE)

        # 将所有元素添加到算力内容布局
        self.quotaContentLayout.addLayout(self.quotaTitleLayout)
        self.quotaContentLayout.addLayout(self.quotaValueLayout)
        self.quotaContentLayout.addWidget(self.quotaHint)

        # 添加到账户信息布局
        self.accountInfoLayout.addLayout(self.quotaContentLayout)

    def _init_usage_card(self):
        """初始化使用记录卡片"""
        self.usageCard = SimpleCardWidget(self)
        self.usageLayout = QVBoxLayout(self.usageCard)

        # 使用记录标题和记录数量显示
        self.usageTitleLayout = QHBoxLayout()
        self.usageTitle = SubtitleLabel('使用记录', self)
        self.recordCountLabel = BodyLabel('共 0 条记录', self)
        self.recordCountLabel.setStyleSheet('color: #666666;')

        self.usageTitleLayout.addWidget(self.usageTitle)
        self.usageTitleLayout.addStretch()
        self.usageTitleLayout.addWidget(self.recordCountLabel)

        self.usageLayout.addLayout(self.usageTitleLayout)

        # 创建交易记录分页表格 - 设置每页显示15条记录
        self.transactionTable = TransactionTableWidget(self, page_size=15)
        self.usageLayout.addWidget(self.transactionTable)

        self.vBoxLayout.addWidget(self.usageCard)

    # 辅助方法
    def _handle_auth_error(self, error_message="认证错误"):
        """处理认证错误的统一方法"""
        logger.warning(f"{error_message}")
        if self.parent:
            self.parent.handleAuthError()

    def _show_info_bar(self, type_="info", title="提示", content="", duration=2000):
        """显示统一的信息提示栏

        Args:
            type_: 提示类型，可选 'info', 'success', 'warning', 'error'
            title: 提示标题
            content: 提示内容
            duration: 显示时长（毫秒）
        """
        bar_method = getattr(InfoBar, type_)
        bar_method(title=title, content=content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=duration, parent=self)

    # 业务方法
    def updateUserInfo(self, user_info: dict):
        """更新用户信息

        Args:
            user_info: 用户信息字典
        """
        # 更新邮箱地址
        email = user_info.get('email', '未登录')
        self.emailValue.setText(email)

        try:
            # 更新算力额度
            self._update_balance()

            # 更新使用记录
            self.updateUsageHistory()

            # 显示退出按钮
            self.logoutButton.setVisible(True)
        except AuthenticationError as e:
            self._handle_auth_error(f"认证错误: {e}")
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")

    def _update_balance(self):
        """更新算力余额"""
        balance_data = api_client.get_balance_sync()
        if balance_data and 'data' in balance_data:
            balance = balance_data['data'].get('balance', 0)
            self.quotaValue.setText(str(balance))
        else:
            self.quotaValue.setText('0')

    def updateUsageHistory(self, new_transactions=None):
        """更新使用记录表格

        Args:
            new_transactions: 可选，新的交易记录列表，如果提供则添加到现有记录中
        """
        try:
            if new_transactions is None:
                # 重置当前页码到第一页
                self.current_page = 1
                # 从API获取记录
                self._fetch_all_transactions(page=1)
            else:
                # 添加新交易记录到列表中
                self.transactionTable.set_data(new_transactions, reset_page=False)
        except AuthenticationError as e:
            self._handle_auth_error(f"认证错误: {e}")
        except Exception as e:
            logger.error(f"更新使用记录失败: {e}")

    def _fetch_all_transactions(self, page=None):
        """从API获取交易记录，支持分页

        Args:
            page: 要获取的页码，如果为None则使用当前页码
        """
        # 如果指定了页码，则更新当前页码
        if page is not None:
            self.current_page = page

        # 调用API获取指定页的交易记录
        history_data = api_client.get_history_sync(
            page=self.current_page,
            page_size=self.page_size
        )

        if not history_data or 'data' not in history_data:
            return

        # 获取交易记录
        transactions = history_data['data'].get('transactions', [])

        # 更新总记录数和总页数
        self.total_records = history_data['data'].get('total', 0)
        # 计算总页数，向上取整
        self.total_pages = (self.total_records + self.page_size - 1) // self.page_size
        self.total_pages = max(1, self.total_pages)  # 确保至少有一页.
        # 输出分页信息到日志
        logger.info(f"交易记录分页信息: 当前页={self.current_page}, 总页数={self.total_pages}, 总记录数={self.total_records}, 当前页数据数量={len(transactions)}")

        # 更新记录数量标签
        self.recordCountLabel.setText(f'共 {self.total_records} 条记录')

        # 设置数据到表格，传递总页数和总记录数
        # 清空表格并设置新数据
        self.transactionTable.table.clearContents()
        self.transactionTable.table.setRowCount(len(transactions))

        # 设置总页数和当前页码
        self.transactionTable.total_pages = self.total_pages
        self.transactionTable.current_page = self.current_page

        # 更新页码指示器
        self.transactionTable.update_page_indicator()

        # 填充表格数据
        self.transactionTable._populate_table(transactions)

        # 设置当前页的数据
        self.transactionTable.all_items = transactions

    def showPurchaseDialog(self):
        """显示算力购买对话框"""
        # 检查用户是否已登录
        if self.emailValue.text() == '未登录':
            self._show_info_bar(type_="warning", title="提示", content="请先登录后再购买算力", duration=2000)
            return

        # 创建并显示购买对话框
        dialog = PurchaseDialog(self)
        dialog.purchaseCompleted.connect(self.onPurchaseCompleted)
        dialog.exec()

    def onPurchaseCompleted(self, transaction):
        """处理购买完成事件

        Args:
            transaction: 交易信息字典
        """
        try:
            # 刷新余额
            self._update_balance()

            # 添加新交易记录到表格
            if transaction:
                self._update_transaction_table(transaction)
            else:
                logger.error('没有交易记录')

            # 显示购买成功提示
            self._show_info_bar(type_="success", title="购买成功", content=f"已成功购买 {transaction.get('amount', 0)} 点算力", duration=3000)
        except AuthenticationError as e:
            self._handle_auth_error(f"认证错误: {e}")
        except Exception as e:
            logger.error(f"更新购买信息失败: {e}")
            self._show_info_bar(type_="error", title="错误", content="更新购买信息失败", duration=3000)

    def onPageChanged(self, page):
        """处理页码变化事件

        Args:
            page: 新的页码
        """
        # 输出调试日志
        logger.info(f"页码变化: 当前页={self.current_page}, 新页码={page}")

        # 如果页码与当前页码不同，则获取新页的数据
        if page != self.current_page:
            try:
                # 从 API 获取新页的数据
                logger.info(f"开始获取第 {page} 页数据")
                self._fetch_all_transactions(page=page)
                logger.info(f"获取第 {page} 页数据成功")
            except AuthenticationError as e:
                self._handle_auth_error(f"认证错误: {e}")
            except Exception as e:
                logger.error(f"获取交易记录失败: {e}")
                self._show_info_bar(type_="error", title="错误", content="获取交易记录失败", duration=2000)

    def _update_transaction_table(self, transaction):
        """更新交易记录表格

        Args:
            transaction: 新的交易记录
        """
        # 如果表格为空，需要重新获取所有记录
        if not self.transactionTable.all_items:
            self._fetch_all_transactions(page=1)  # 重置到第一页
        else:
            # 将新交易添加到现有记录中
            self.transactionTable.all_items.insert(0, transaction)
            # 增加总记录数并重新计算总页数
            self.total_records += 1
            self.total_pages = (self.total_records + self.page_size - 1) // self.page_size
            # 更新记录数量标签
            self.recordCountLabel.setText(f'共 {self.total_records} 条记录')

            # 重置到第一页
            self.current_page = 1

            # 重新获取第一页数据
            self._fetch_all_transactions(page=1)

    def handleLogout(self):
        """处理退出登录"""
        # 重置UI状态
        self._reset_ui_state()

        # 清除登录状态
        self._clear_login_state()

        # 显示退出成功提示
        self._show_info_bar(type_="success", title="成功", content="已退出登录", duration=2000)

    def _reset_ui_state(self):
        """重置UI状态"""
        self.emailValue.setText('未登录')
        self.quotaValue.setText('0')
        self.logoutButton.setVisible(False)  # 退出后隐藏退出按钮
        self.recordCountLabel.setText('共 0 条记录')  # 重置记录数量标签
        self.transactionTable.set_data([])  # 清空使用记录表格

    def _clear_login_state(self):
        """清除登录状态"""
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
