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
        self.emailLabel = BodyLabel('邮箱地址', self)
        self.emailValue = BodyLabel('user@example.com', self)
        self.emailLayout.addWidget(self.emailIcon)
        self.emailLayout.addWidget(self.emailLabel)
        self.emailLayout.addStretch()
        self.emailLayout.addWidget(self.emailValue)
        self.accountLayout.addLayout(self.emailLayout)
        
        # 算力额度
        self.quotaLayout = QHBoxLayout()
        self.quotaIcon = IconWidget(FIF.SPEED_HIGH, self)
        self.quotaLabel = BodyLabel('算力额度', self)
        self.quotaValue = SubtitleLabel('1000', self)
        self.quotaUnit = BodyLabel('点数', self)
        self.quotaLayout.addWidget(self.quotaIcon)
        self.quotaLayout.addWidget(self.quotaLabel)
        self.quotaLayout.addStretch()
        self.quotaLayout.addWidget(self.quotaValue)
        self.quotaLayout.addWidget(self.quotaUnit)
        self.accountLayout.addLayout(self.quotaLayout)
        
        # 当前剩余可用算力提示
        self.quotaHint = BodyLabel('当前剩余可用算力额度', self)
        self.quotaHint.setStyleSheet('color: #666666;')
        self.accountLayout.addWidget(self.quotaHint)
        
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
        
        # 暂无使用记录提示
        self.noUsageHint = BodyLabel('暂无使用记录', self)
        self.noUsageHint.setStyleSheet('color: #666666;')
        self.noUsageHint.setAlignment(Qt.AlignCenter)
        self.usageLayout.addWidget(self.noUsageHint)
        
        self.vBoxLayout.addWidget(self.usageCard)
        self.vBoxLayout.addStretch()
        
        # 设置样式
        self.setStyleSheet("""
            QFrame {
                background-color: rgb(243, 243, 243);
            }
            
            SimpleCardWidget {
                background-color: white;
                border: none;
                border-radius: 10px;
                padding: 20px;
            }
            
            SubtitleLabel {
                font-size: 18px;
                font-weight: bold;
                padding-bottom: 10px;
            }
            
            BodyLabel {
                font-size: 14px;
            }
            
            PrimaryPushButton {
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
            }
            
            PushButton {
                border: 1px solid #DDDDDD;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                margin-top: 10px;
            }
        """)
