import asyncio

from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation, Property, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QApplication

from vendor.qfluentwidgets import (LineEdit, PrimaryPushButton, BodyLabel, TitleLabel, FluentIcon as FIF, InfoBar, InfoBarPosition, TransparentToolButton,
                                   CheckBox)
from nice_ui.services.simple_api_service import simple_api_service


class LoginWindow(QFrame):
    # 添加登录成功信号
    loginSuccessful = Signal(dict)

    def __init__(self, parent=None,settings=None):
        super().__init__(parent=parent)
        self.setObjectName("loginWindow")
        self.settings = settings
        self.setup_ui()
        self.setup_animation()
        self.load_saved_email()

        # 移除事件循环引用，使用ApiService管理异步调用

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

        # 记住账号复选框
        self.rememberCheckBox = CheckBox('记住账号', self)
        self.rememberCheckBox.setChecked(bool(self.settings.value('remember_email', False)))

        # 登录按钮
        self.loginButton = PrimaryPushButton('登录', self)
        self.loginButton.setFixedHeight(40)

        # 忘记密码和注册按钮的样式
        self.linkButtonStyle = """
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
        """

        # 忘记密码按钮
        self.forgotPasswordButton = PrimaryPushButton('忘记密码？', self)
        self.forgotPasswordButton.setFixedHeight(30)
        self.forgotPasswordButton.setStyleSheet(self.linkButtonStyle)

        # 注册按钮
        self.registerButton = PrimaryPushButton('注册账号', self)
        self.registerButton.setFixedHeight(30)
        self.registerButton.setStyleSheet(self.linkButtonStyle)

        # 添加所有控件到布局
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignCenter)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.subtitleLabel, 0, Qt.AlignCenter)
        self.vBoxLayout.addSpacing(30)

        self.loginLayout.addWidget(self.emailInput)
        self.loginLayout.addWidget(self.passwordInput)
        self.loginLayout.addWidget(self.rememberCheckBox)
        self.loginLayout.addWidget(self.loginButton)

        # 创建水平布局放置忘记密码和注册按钮
        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonsLayout.setSpacing(10)
        self.buttonsLayout.addWidget(self.forgotPasswordButton)
        self.buttonsLayout.addWidget(self.registerButton)

        # 将水平布局添加到登录卡片布局
        self.loginLayout.addLayout(self.buttonsLayout)

        self.vBoxLayout.addWidget(self.loginCard)
        self.vBoxLayout.addStretch()

        # 连接信号
        self.loginButton.clicked.connect(self.handle_login)
        self.forgotPasswordButton.clicked.connect(self.handle_forgot_password)
        self.registerButton.clicked.connect(self.handle_register)

        # 确保登录按钮始终可用 - 修复Token过期时按钮无法点击的问题
        self.loginButton.setEnabled(True)

    def setup_animation(self):
        # 窗口打开时的动画效果
        self.opacity = 0
        self.animation = QPropertyAnimation(self, b'windowOpacity', self)
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()

    def showEvent(self, event):
        """窗口显示时的事件处理 - 确保登录按钮可用"""
        super().showEvent(event)
        # 重置按钮状态，修复Token过期时按钮无法点击的问题
        if hasattr(self, 'loginButton'):
            self.loginButton.setEnabled(True)
            self.loginButton.setText('登录')

    def load_saved_email(self):
        """加载保存的邮箱账号"""
        if bool(self.settings.value('remember_email', False)):
            if saved_email := self.settings.value('email', ''):
                self.emailInput.setText(saved_email)

    def save_email(self, email):
        """保存邮箱账号"""
        if self.rememberCheckBox.isChecked():
            self.settings.setValue('remember_email', True)
            self.settings.setValue('email', email)
        else:
            self.settings.setValue('remember_email', False)
            self.settings.remove('email')
        self.settings.sync()



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

        # 临时禁用按钮防止重复点击，但确保在完成后重新启用
        self.loginButton.setEnabled(False)
        self.loginButton.setText('登录中...')

        # 异步登录
        self._perform_async_login(email, password)

    def handle_forgot_password(self):
        # 使用QDesktopServices打开浏览器并跳转到忘记密码页面
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.config_manager import get_web_url

        # 尝试获取邮箱地址，如果有的话可以作为参数传递
        email = self.emailInput.text()

        # 从配置中获取忘记密码页面的URL
        forgot_password_url = get_web_url('forgot_password')

        # 打开浏览器并跳转到指定的URL
        QDesktopServices.openUrl(QUrl(forgot_password_url))

        # 显示提示信息
        InfoBar.success(
            title='成功',
            content='已打开密码重置页面',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def handle_register(self):
        # 使用QDesktopServices打开浏览器并跳转到注册页面
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        from services.config_manager import get_web_url

        # 从配置中获取注册页面的URL
        register_url = get_web_url('register')

        # 打开浏览器并跳转到指定的URL
        QDesktopServices.openUrl(QUrl(register_url))

        # 显示提示信息
        InfoBar.success(
            title='成功',
            content='已打开注册页面',
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

    def _perform_async_login(self, email, password):
        """执行异步登录 - 简化版本

        Token 保存由 api_client._update_token() 自动完成，不需要手动保存
        """
        def on_success(result):
            if result:
                # 保存邮箱账号（记住账号功能）
                self.save_email(email)

                # Token 已经由 api_client._update_token() 自动保存到 QSettings
                # 不需要手动调用 save_login_state()

                user_info = {'email': result['user']['email']}
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

            # 重新启用按钮
            self.loginButton.setEnabled(True)
            self.loginButton.setText('登录')

        def on_error(error):
            # 使用简化的错误处理器
            from app.core.error_handler import get_error_message
            from utils import logger

            # 获取用户友好的消息（支持多语言）
            # TODO: 从设置中读取用户选择的语言
            lang = "zh"  # 默认中文，未来可以改为 settings.value('language', 'zh')
            user_message = get_error_message(error, lang)

            # 在日志中保留原始错误信息
            logger.warning(f"登录失败: {error}")

            InfoBar.error(
                title='登录失败',
                content=user_message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            # 重新启用按钮
            self.loginButton.setEnabled(True)
            self.loginButton.setText('登录')

        # 使用简化的API服务
        simple_api_service.login(
            email, password,
            callback_success=on_success,
            callback_error=on_error
        )