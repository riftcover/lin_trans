from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLineEdit, QHBoxLayout
from vendor.qfluentwidgets import (
    SimpleCardWidget,
    PushButton,
    FluentIcon as FIF,
    IconWidget,
    SubtitleLabel,
    BodyLabel,
    PrimaryPushButton
)

class ProfileInterface(QFrame):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.parent = parent
        
        # 设置对象名称
        self.setObjectName(text)
        
        # 创建主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 0)
        
        # 创建标题栏
        self.titleBar = QHBoxLayout()
        self.titleLabel = SubtitleLabel('个人中心', self)
        self.logoutButton = PrimaryPushButton('退出登录', self)
        self.logoutButton.setFixedWidth(100)
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
        
        # 邮箱地址
        self.emailLayout = QHBoxLayout()
        self.emailIcon = IconWidget(FIF.MAIL, self)
        
        # 创建垂直布局来包含邮箱标签和值
        self.emailContentLayout = QVBoxLayout()
        self.emailLabel = BodyLabel('邮箱地址', self)
        self.emailValue = BodyLabel('user@example.com', self)
        
        # 创建一个容器来包含邮箱值，以便添加下划线
        self.emailValueContainer = QFrame()
        self.emailValueContainer.setObjectName('emailValueContainer')
        self.emailValueLayout = QHBoxLayout(self.emailValueContainer)
        self.emailValueLayout.setContentsMargins(0, 0, 0, 8)  # 底部留出空间给下划线
        self.emailValueLayout.addWidget(self.emailValue)
        
        self.emailValue.setStyleSheet('font-size: 16px; color: #1a1a1a;')
        self.emailLabel.setStyleSheet('color: #666666;')
        self.emailValueContainer.setStyleSheet("""
            #emailValueContainer {
                border-bottom: 1px solid #DDDDDD;
            }
        """)
        
        # 将标签和值容器添加到垂直布局中
        self.emailContentLayout.addWidget(self.emailLabel)
        self.emailContentLayout.addWidget(self.emailValueContainer)
        self.emailContentLayout.setSpacing(4)
        
        # 将图标和垂直布局添加到水平布局中
        self.emailLayout.addWidget(self.emailIcon)
        self.emailLayout.addLayout(self.emailContentLayout)
        self.emailLayout.addStretch()
        self.accountLayout.addLayout(self.emailLayout)
        
        # 添加一些间距
        self.accountLayout.addSpacing(10)
        
        # 算力额度
        self.quotaLayout = QHBoxLayout()
        self.quotaIcon = IconWidget(FIF.SPEED_HIGH, self)
        
        # 创建垂直布局来包含算力标签和值
        self.quotaContentLayout = QVBoxLayout()
        self.quotaLabel = BodyLabel('算力额度', self)
        self.quotaLabel.setStyleSheet('color: #666666;')
        
        # 创建一个容器来包含值和单位，以便添加下划线
        self.quotaValueContainer = QFrame()
        self.quotaValueContainer.setObjectName('quotaValueContainer')
        self.quotaValueLayout = QHBoxLayout(self.quotaValueContainer)
        self.quotaValueLayout.setContentsMargins(0, 0, 0, 8)  # 底部留出空间给下划线
        
        self.quotaValue = SubtitleLabel('1000', self)
        self.quotaUnit = BodyLabel('点数', self)
        self.quotaValue.setStyleSheet('font-size: 16px; color: #1a1a1a;')
        
        self.quotaValueLayout.addWidget(self.quotaValue)
        self.quotaValueLayout.addWidget(self.quotaUnit)
        self.quotaValueLayout.setSpacing(4)
        self.quotaValueLayout.addStretch()
        
        self.quotaValueContainer.setStyleSheet("""
            #quotaValueContainer {
                border-bottom: 1px solid #DDDDDD;
            }
        """)
        
        # 将标签和值容器添加到垂直布局中
        self.quotaContentLayout.addWidget(self.quotaLabel)
        self.quotaContentLayout.addWidget(self.quotaValueContainer)
        self.quotaContentLayout.setSpacing(4)
        
        # 将图标和垂直布局添加到水平布局中
        self.quotaLayout.addWidget(self.quotaIcon)
        self.quotaLayout.addLayout(self.quotaContentLayout)
        self.quotaLayout.addStretch()
        self.accountLayout.addLayout(self.quotaLayout)
        
        # 当前剩余可用算力提示
        self.quotaHint = BodyLabel('当前剩余可用算力额度', self)
        self.quotaHint.setStyleSheet('color: #666666;')
        self.accountLayout.addWidget(self.quotaHint)
        
        # 购买算力按钮
        self.buyButton = PushButton('购买算力', self)
        self.accountLayout.addWidget(self.buyButton)
        
        self.vBoxLayout.addWidget(self.accountCard)
        
        # 使用记录卡片
        self.usageCard = SimpleCardWidget(self)
        self.usageLayout = QVBoxLayout(self.usageCard)
        
        # 使用记录标题
        self.usageTitle = SubtitleLabel('使用记录', self)
        self.usageLayout.addWidget(self.usageTitle)
        
        # 暂无使用记录提示
        self.noUsageHint = BodyLabel('暂无使用记录', self)
        self.noUsageHint.setStyleSheet('color: #666666;')
        self.noUsageHint.setAlignment(Qt.AlignCenter)
        self.usageLayout.addWidget(self.noUsageHint)
        
        self.vBoxLayout.addWidget(self.usageCard)
        self.vBoxLayout.addStretch()