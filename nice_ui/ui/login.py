from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation, Property, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QApplication

from vendor.qfluentwidgets import (LineEdit, PrimaryPushButton, BodyLabel, TitleLabel, FluentIcon as FIF, InfoBar, InfoBarPosition, TransparentToolButton)


class LoginWindow(QFrame):
    # 添加登录成功信号
    loginSuccessful = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("loginWindow")
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window) # 独立窗口
        self.resize(400, 500)
        self.setWindowTitle("登录")
        self.setWindowIcon(QIcon(FIF.PEOPLE.path()))
        
        self.setStyleSheet("""
            #loginWindow {
                background-color: white;
                border: 1px solid rgb(200, 200, 200);
            }
            QFrame {
                background: transparent;
            }
            #loginCard {
                border: none;
                background-color: rgb(251, 251, 251);
            }
            #closeButton {
                background: transparent;
                border-radius: 12px;
                width: 24px;
                height: 24px;
                margin: 5px;
            }
            #closeButton:hover {
                background: rgba(0, 0, 0, 0.1);
            }
        """)

        # 主布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)

        # 添加关闭按钮
        self.closeButton = TransparentToolButton(FIF.CLOSE, self)
        self.closeButton.setObjectName('closeButton')
        self.closeButton.setFixedSize(24, 24)
        self.closeButton.clicked.connect(self.close)
        
        # 关闭按钮容器
        closeButtonLayout = QHBoxLayout()
        closeButtonLayout.setContentsMargins(0, 0, 0, 0)
        closeButtonLayout.addStretch()
        closeButtonLayout.addWidget(self.closeButton)
        
        # 将关闭按钮添加到主布局
        self.vBoxLayout.addLayout(closeButtonLayout)

        # 标题部分
        self.titleLabel = TitleLabel('欢迎回来', self)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.subtitleLabel = BodyLabel('登录您的账号以继续', self)
        self.subtitleLabel.setAlignment(Qt.AlignCenter)
        self.subtitleLabel.setStyleSheet('color: rgb(100, 100, 100)')

        # 登录表单卡片
        self.loginCard = QFrame()
        self.loginCard.setObjectName('loginCard')
        self.loginLayout = QVBoxLayout(self.loginCard)
        self.loginLayout.setSpacing(20)
        self.loginLayout.setContentsMargins(20, 20, 20, 20)

        # 邮箱输入框
        self.emailInput = LineEdit(self)
        self.emailInput.setPlaceholderText('请输入邮箱')
        # self.emailInput.setIcon(FIF.MAIL)
        self.emailInput.setClearButtonEnabled(True)

        # 密码输入框
        self.passwordInput = LineEdit(self)
        self.passwordInput.setPlaceholderText('请输入密码')
        # self.passwordInput.setIcon(FIF.PASSWORD)
        self.passwordInput.setEchoMode(QLineEdit.Password)
        self.passwordInput.setClearButtonEnabled(True)

        # 登录按钮
        self.loginButton = PrimaryPushButton('登录', self)
        self.loginButton.setFixedHeight(40)

        # 忘记密码按钮
        self.forgotPasswordButton = PrimaryPushButton('忘记密码？', self)
        self.forgotPasswordButton.setFixedHeight(30)
        self.forgotPasswordButton.setStyleSheet("""
            PrimaryPushButton {
                font-size: 13px;
                color: rgb(96, 96, 96);
                padding: 5px 10px;
                border: none;
                border-radius: 5px;
                text-align: center;
            }
            PrimaryPushButton:hover {
                color: rgb(0, 120, 212);
                background-color: rgba(0, 120, 212, 0.1);
            }
            PrimaryPushButton:pressed {
                color: rgb(0, 90, 158);
                background-color: rgba(0, 120, 212, 0.15);
            }
        """)

        # 添加所有控件到布局
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignCenter)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.subtitleLabel, 0, Qt.AlignCenter)
        self.vBoxLayout.addSpacing(30)

        self.loginLayout.addWidget(self.emailInput)
        self.loginLayout.addWidget(self.passwordInput)
        self.loginLayout.addWidget(self.loginButton)
        self.loginLayout.addWidget(self.forgotPasswordButton, 0, Qt.AlignCenter)

        self.vBoxLayout.addWidget(self.loginCard)
        self.vBoxLayout.addStretch()

        # 连接信号
        self.loginButton.clicked.connect(self.handle_login)

    def setup_animation(self):
        # 窗口打开时的动画效果
        self.opacity = 0
        self.animation = QPropertyAnimation(self, b'windowOpacity', self)
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()

    def handle_login(self):
        email = self.emailInput.text()
        password = self.passwordInput.text()

        if not email or not password:
            InfoBar.error(
                title='错误',
                content='请填写完整的登录信息',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # TODO: 在这里添加实际的登录逻辑
        # 这里模拟登录成功
        user_info = {
            'email': email,
            'username': email.split('@')[0],
            'quota': 1000  # 模拟用户额度
        }
        
        # 发送登录成功信号
        self.loginSuccessful.emit(user_info)
        
        # 显示登录成功提示
        InfoBar.success(
            title='成功',
            content='登录成功',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def get_window_opacity(self):
        return self.opacity

    def set_window_opacity(self, opacity):
        self.opacity = opacity
        self.setWindowOpacity(opacity)

    windowOpacity = Property(float, get_window_opacity, set_window_opacity)

    def closeEvent(self, event):
        # 如果用户直接关闭登录窗口，退出应用
        if not self.parent():
            QApplication.quit()
        super().closeEvent(event)