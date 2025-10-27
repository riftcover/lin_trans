"""
推荐中心 - 展示推荐战绩和分享推荐链接

功能：
1. 展示推荐码（大字体显示，支持一键复制）
2. 展示推荐统计数据（累计邀请、已激活、待激活、累计奖励）
3. 分享推荐链接（复制链接、生成二维码）
4. 推荐明细列表（分页展示）
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QClipboard
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QDialog, QApplication, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)

from nice_ui.services.simple_api_service import simple_api_service
from utils import logger
from vendor.qfluentwidgets import (
    SimpleCardWidget, PushButton, FluentIcon as FIF, 
    IconWidget, SubtitleLabel, BodyLabel, PrimaryPushButton,
    InfoBar, InfoBarPosition, TransparentToolButton, StrongBodyLabel
)

# import qrcode


class ReferralCenterInterface(QFrame):
    """推荐中心界面"""
    
    # 样式常量
    CODE_STYLE = """
        QLabel {
            font-size: 32px;
            font-weight: bold;
            color: #7C3AED;
            background: transparent;
            padding: 10px;
            letter-spacing: 4px;
        }
    """
    
    STAT_VALUE_STYLE = """
        QLabel {
            font-size: 24px;
            font-weight: bold;
            color: #1F2937;
        }
    """
    
    STAT_LABEL_STYLE = """
        QLabel {
            font-size: 13px;
            color: #6B7280;
        }
    """

    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.parent = parent
        self.parent_window = parent
        
        # 数据
        self.referral_code = ""
        self.stats = None
        self.history = []
        self.current_page = 1
        self.page_size = 10
        self.total_records = 0
        
        # 设置对象名称
        self.setObjectName(text)
        
        # 初始化UI
        self._setup_ui()
        
        # 连接信号
        self._connect_signals()

    def _setup_ui(self):
        """设置UI布局"""
        # 创建主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 20)
        
        # 标题栏
        self._init_title_bar()
        
        # 推荐码卡片
        self._init_referral_code_card()
        
        # 统计数据卡片
        self._init_stats_cards()
        
        # # 推荐明细卡片
        # self._init_history_card()
        
        # 添加底部弹性空间
        self.vBoxLayout.addStretch()

    def _connect_signals(self):
        """连接信号和槽"""
        self.copyCodeButton.clicked.connect(self.copy_referral_code)
        self.copyLinkButton.clicked.connect(self.copy_referral_link)
        # self.qrcodeButton.clicked.connect(self.show_qrcode_dialog)
        self.refreshButton.clicked.connect(self.load_data)

    def _init_title_bar(self):
        """初始化标题栏"""
        self.titleBar = QHBoxLayout()
        self.titleLabel = SubtitleLabel('推荐中心', self)
        self.refreshButton = TransparentToolButton(FIF.SYNC, self)
        self.refreshButton.setToolTip('刷新数据')
        
        self.titleBar.addWidget(self.titleLabel)
        self.titleBar.addStretch()
        self.titleBar.addWidget(self.refreshButton)
        
        self.vBoxLayout.addLayout(self.titleBar)

    def _init_referral_code_card(self):
        """初始化推荐码卡片"""
        self.codeCard = SimpleCardWidget(self)
        self.codeLayout = QVBoxLayout(self.codeCard)
        self.codeLayout.setSpacing(15)
        
        # 标题
        titleLayout = QHBoxLayout()
        titleIcon = IconWidget(FIF.SHARE, self)
        titleIcon.setFixedSize(20, 20)
        titleLabel = SubtitleLabel('我的推荐码', self)
        titleLayout.addWidget(titleIcon)
        titleLayout.addWidget(titleLabel)
        titleLayout.addStretch()
        self.codeLayout.addLayout(titleLayout)
        
        # 推荐码显示（大字体）
        self.codeValue = BodyLabel('加载中...', self)
        self.codeValue.setStyleSheet(self.CODE_STYLE)
        self.codeValue.setAlignment(Qt.AlignCenter)
        self.codeLayout.addWidget(self.codeValue)
        
        # 提示文字
        hintLabel = BodyLabel('分享你的推荐码，邀请好友注册，双方各得1000代币奖励', self)
        hintLabel.setStyleSheet('color: #6B7280; font-size: 12px;')
        hintLabel.setAlignment(Qt.AlignCenter)
        self.codeLayout.addWidget(hintLabel)
        
        # 按钮组
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(10)
        
        self.copyCodeButton = PrimaryPushButton('复制推荐码', self)
        self.copyCodeButton.setIcon(FIF.COPY)
        self.copyCodeButton.setFixedHeight(36)
        
        self.copyLinkButton = PushButton('复制推荐链接', self)
        self.copyLinkButton.setIcon(FIF.LINK)
        self.copyLinkButton.setFixedHeight(36)
        
        buttonLayout.addWidget(self.copyCodeButton)
        buttonLayout.addWidget(self.copyLinkButton)
        

        # self.qrcodeButton = PushButton('生成二维码', self)
        # self.qrcodeButton.setIcon(FIF.QRCODE)
        # self.qrcodeButton.setFixedHeight(36)
        # buttonLayout.addWidget(self.qrcodeButton)
        
        buttonLayout.addStretch()
        self.codeLayout.addLayout(buttonLayout)
        
        self.vBoxLayout.addWidget(self.codeCard)

    def _init_stats_cards(self):
        """初始化统计数据卡片"""
        # 创建水平布局容纳4个统计卡片
        statsLayout = QHBoxLayout()
        statsLayout.setSpacing(15)
        
        # 创建4个统计卡片
        self.totalCard = self._create_stat_card(FIF.PEOPLE, '累计邀请', '0', '#3B82F6')
        self.rewardedCard = self._create_stat_card(FIF.ACCEPT, '已激活', '0', '#10B981')
        self.pendingCard = self._create_stat_card(FIF.HISTORY, '待激活', '0', '#F59E0B')
        self.tokensCard = self._create_stat_card(FIF.CERTIFICATE, '累计奖励', '0 代币', '#8B5CF6')
        
        statsLayout.addWidget(self.totalCard)
        statsLayout.addWidget(self.rewardedCard)
        statsLayout.addWidget(self.pendingCard)
        statsLayout.addWidget(self.tokensCard)
        
        self.vBoxLayout.addLayout(statsLayout)

    def _create_stat_card(self, icon, label_text, value_text, color):
        """创建单个统计卡片"""
        card = SimpleCardWidget(self)
        card.setFixedHeight(120)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # 图标和标签
        topLayout = QHBoxLayout()
        icon_widget = IconWidget(icon, self)
        icon_widget.setFixedSize(24, 24)
        label = BodyLabel(label_text, self)
        label.setStyleSheet(self.STAT_LABEL_STYLE)
        topLayout.addWidget(icon_widget)
        topLayout.addWidget(label)
        topLayout.addStretch()
        layout.addLayout(topLayout)
        
        # 数值
        value = StrongBodyLabel(value_text, self)
        value.setStyleSheet(self.STAT_VALUE_STYLE)
        layout.addWidget(value)
        layout.addStretch()
        
        # 保存value引用以便后续更新
        card.valueLabel = value
        
        return card

    def _init_history_card(self):
        """初始化推荐明细卡片"""
        self.historyCard = SimpleCardWidget(self)
        self.historyLayout = QVBoxLayout(self.historyCard)
        
        # 标题
        titleLayout = QHBoxLayout()
        titleIcon = IconWidget(FIF.HISTORY, self)
        titleIcon.setFixedSize(20, 20)
        titleLabel = SubtitleLabel('推荐明细', self)
        titleLayout.addWidget(titleIcon)
        titleLayout.addWidget(titleLabel)
        titleLayout.addStretch()
        self.historyLayout.addLayout(titleLayout)
        
        # 创建表格
        self.historyTable = QTableWidget(self)
        self.historyTable.setColumnCount(5)
        self.historyTable.setHorizontalHeaderLabels(['用户ID', '奖励金额', '状态', '注册时间', '发放时间'])
        
        # 设置表格样式
        self.historyTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.historyTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.historyTable.setAlternatingRowColors(True)
        self.historyTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.historyTable.verticalHeader().setVisible(False)
        self.historyTable.setMinimumHeight(300)
        
        self.historyLayout.addWidget(self.historyTable)
        
        # 分页按钮
        pageLayout = QHBoxLayout()
        self.prevButton = PushButton('上一页', self)
        self.prevButton.setFixedWidth(100)
        self.prevButton.clicked.connect(self.prev_page)
        
        self.pageLabel = BodyLabel('第 1 页', self)
        self.pageLabel.setAlignment(Qt.AlignCenter)
        
        self.nextButton = PushButton('下一页', self)
        self.nextButton.setFixedWidth(100)
        self.nextButton.clicked.connect(self.next_page)
        
        pageLayout.addStretch()
        pageLayout.addWidget(self.prevButton)
        pageLayout.addWidget(self.pageLabel)
        pageLayout.addWidget(self.nextButton)
        pageLayout.addStretch()
        
        self.historyLayout.addLayout(pageLayout)
        
        self.vBoxLayout.addWidget(self.historyCard)

    # ============================================
    # 数据加载方法
    # ============================================

    def load_data(self):
        """加载所有数据"""
        logger.info("开始加载推荐中心数据")
        self._show_info_bar('info', '加载中', '正在获取推荐数据...', 1000)
        
        # 加载推荐码
        self._load_referral_code()
        
        # 加载统计数据
        self._load_stats()
        
        # 加载推荐明细
        # self._load_history()

    def _load_referral_code(self):
        """加载推荐码"""
        def on_success(result):
            if result and 'data' in result:
                self.referral_code = result['data'].get('referral_code', '')
                self.codeValue.setText(self.referral_code)
                logger.info(f"推荐码加载成功: {self.referral_code}")
            else:
                self.codeValue.setText('获取失败')
                logger.warning("获取推荐码失败")
        
        def on_error(error):
            logger.error(f"获取推荐码失败: {error}")
            self.codeValue.setText('获取失败')
            self._show_info_bar('error', '错误', '获取推荐码失败', 2000)
        
        simple_api_service.get_referral_code(
            callback_success=on_success,
            callback_error=on_error
        )

    def _load_stats(self):
        """加载统计数据"""
        def on_success(result):
            if result and 'data' in result:
                self.stats = result['data']
                self._update_stats_ui()
                logger.info(f"统计数据加载成功: {self.stats}")
            else:
                logger.warning("获取统计数据失败")
        
        def on_error(error):
            logger.error(f"获取统计数据失败: {error}")
            self._show_info_bar('error', '错误', '获取统计数据失败', 2000)
        
        simple_api_service.get_referral_stats(
            callback_success=on_success,
            callback_error=on_error
        )

    def _load_history(self, page=None):
        """加载推荐明细"""
        if page is not None:
            self.current_page = page
        
        def on_success(result):
            if result and 'data' in result:
                data = result['data']
                self.history = data.get('referrals', [])
                self.total_records = data.get('total', 0)
                self._update_history_ui()
                logger.info(f"推荐明细加载成功: 第{self.current_page}页, 共{self.total_records}条")
            else:
                logger.warning("获取推荐明细失败")
        
        def on_error(error):
            logger.error(f"获取推荐明细失败: {error}")
            self._show_info_bar('error', '错误', '获取推荐明细失败', 2000)
        
        simple_api_service.get_referral_history(
            page=self.current_page,
            page_size=self.page_size,
            callback_success=on_success,
            callback_error=on_error
        )

    # ============================================
    # UI更新方法
    # ============================================

    def _update_stats_ui(self):
        """更新统计数据UI"""
        if not self.stats:
            return
        
        self.totalCard.valueLabel.setText(str(self.stats.get('total_referrals', 0)))
        self.rewardedCard.valueLabel.setText(str(self.stats.get('rewarded_referrals', 0)))
        self.pendingCard.valueLabel.setText(str(self.stats.get('pending_referrals', 0)))
        self.tokensCard.valueLabel.setText(f"{self.stats.get('total_rewards', 0)} 代币")

    def _update_history_ui(self):
        """更新推荐明细UI"""
        # 清空表格
        self.historyTable.setRowCount(0)
        
        # 填充数据
        for row, item in enumerate(self.history):
            self.historyTable.insertRow(row)
            
            # 用户ID（只显示前8位）
            user_id = item.get('referee_id', '')
            self.historyTable.setItem(row, 0, QTableWidgetItem(user_id[:8] + '...'))
            
            # 奖励金额
            amount = item.get('reward_amount', 0)
            self.historyTable.setItem(row, 1, QTableWidgetItem(f"{amount} 代币"))
            
            # 状态
            status = item.get('reward_status', 0)
            status_text = self._get_status_text(status)
            self.historyTable.setItem(row, 2, QTableWidgetItem(status_text))
            
            # 注册时间
            created_at = item.get('created_at', 0)
            created_time = self._format_timestamp(created_at)
            self.historyTable.setItem(row, 3, QTableWidgetItem(created_time))
            
            # 发放时间
            rewarded_at = item.get('rewarded_at')
            rewarded_time = self._format_timestamp(rewarded_at) if rewarded_at else '-'
            self.historyTable.setItem(row, 4, QTableWidgetItem(rewarded_time))
        
        # 更新分页信息
        total_pages = (self.total_records + self.page_size - 1) // self.page_size
        self.pageLabel.setText(f"第 {self.current_page} / {total_pages} 页")
        self.prevButton.setEnabled(self.current_page > 1)
        self.nextButton.setEnabled(self.current_page < total_pages)

    # ============================================
    # 业务方法
    # ============================================

    def copy_referral_code(self):
        """复制推荐码到剪贴板"""
        if not self.referral_code:
            self._show_info_bar('warning', '提示', '推荐码未加载', 2000)
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.referral_code)
        self._show_info_bar('success', '成功', '推荐码已复制到剪贴板', 2000)
        logger.info(f"推荐码已复制: {self.referral_code}")

    def copy_referral_link(self):
        """复制推荐链接到剪贴板"""
        if not self.referral_code:
            self._show_info_bar('warning', '提示', '推荐码未加载', 2000)
            return
        
        # 生成推荐链接（需要根据实际域名修改）
        base_url = "https://www.lapped-ai.com"
        link = f"{base_url}/register?ref={self.referral_code}"
        
        clipboard = QApplication.clipboard()
        clipboard.setText(link)
        self._show_info_bar('success', '成功', '推荐链接已复制到剪贴板', 2000)
        logger.info(f"推荐链接已复制: {link}")

    def show_qrcode_dialog(self):
        """显示二维码对话框"""
        if not self.referral_code:
            self._show_info_bar('warning', '提示', '推荐码未加载', 2000)
            return
        
        # 生成推荐链接
        base_url = "https://www.lapped-ai.com"
        link = f"{base_url}/register?ref={self.referral_code}"

        
        # 创建并显示二维码对话框
        dialog = QRCodeDialog(link, self.referral_code, self)
        dialog.exec()

    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self._load_history(self.current_page - 1)

    def next_page(self):
        """下一页"""
        total_pages = (self.total_records + self.page_size - 1) // self.page_size
        if self.current_page < total_pages:
            self._load_history(self.current_page + 1)

    # ============================================
    # 辅助方法
    # ============================================

    def _get_status_text(self, status: int) -> str:
        """获取状态文本"""
        status_map = {
            0: '待激活',
            1: '已发放',
            2: '失败'
        }
        return status_map.get(status, '未知')

    def _format_timestamp(self, timestamp) -> str:
        """格式化时间戳"""
        if not timestamp:
            return '-'
        
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)  # 毫秒转秒
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return '-'

    def _show_info_bar(self, type_='info', title='提示', content='', duration=2000):
        """显示信息提示栏"""
        bar_method = getattr(InfoBar, type_)
        bar_method(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=duration,
            parent=self
        )


class QRCodeDialog(QDialog):
    """二维码对话框"""
    
    def __init__(self, url: str, code: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.code = code
        
        self.setWindowTitle('推荐二维码')
        self.setFixedSize(400, 500)
        
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = SubtitleLabel('扫码注册', self)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 生成二维码
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(self.url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为QPixmap
        img.save('/tmp/qrcode.png')
        pixmap = QPixmap('/tmp/qrcode.png')
        pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # 显示二维码
        qr_label = QLabel(self)
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)
        
        # 推荐码
        code_label = BodyLabel(f'推荐码: {self.code}', self)
        code_label.setAlignment(Qt.AlignCenter)
        code_label.setStyleSheet('font-size: 14px; color: #6B7280;')
        layout.addWidget(code_label)
        
        # 提示
        hint = BodyLabel('使用微信扫描二维码注册', self)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet('font-size: 12px; color: #9CA3AF;')
        layout.addWidget(hint)
        
        # 关闭按钮
        close_btn = PrimaryPushButton('关闭', self)
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(self.close)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

