import asyncio

from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation, Property, Signal, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QApplication, QStackedWidget

from vendor.qfluentwidgets import (LineEdit, PrimaryPushButton, BodyLabel, TitleLabel, FluentIcon as FIF, InfoBar, InfoBarPosition, TransparentToolButton,
                                   CheckBox, SegmentedWidget, PushButton)
from nice_ui.services.simple_api_service import simple_api_service


class LoginWindow(QFrame):
    # 添加登录成功信号
    loginSuccessful = Signal(dict)

    def __init__(self, parent=None,settings=None):
        super().__init__(parent=parent)
        self.setObjectName("loginWindow")
        self.settings = settings

        # 倒计时相关
        self.countdown_timer = QTimer(self)
        self.countdown_seconds = 0
        self.countdown_timer.timeout.connect(self._update_countdown)

        self.setup_ui()
        self.setup_animation()
        self.load_saved_credentials()

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

        # 登录方式切换
        self.loginTypeSegmented = SegmentedWidget(self)
        self.loginTypeSegmented.addItem('email', '邮箱登录', lambda: self.switch_login_type(0))
        self.loginTypeSegmented.addItem('phone', '手机登录', lambda: self.switch_login_type(1))
        self.loginTypeSegmented.setCurrentItem('email')

        # 登录表单卡片
        self.loginCard = QFrame()
        self.loginCard.setObjectName('loginCard')
        self.loginLayout = QVBoxLayout(self.loginCard)
        self.loginLayout.setSpacing(20)
        self.loginLayout.setContentsMargins(20, 20, 20, 20)

        # 创建堆叠窗口用于切换邮箱/手机登录
        self.loginStack = QStackedWidget(self)

        # === 邮箱登录页面 ===
        self.emailLoginWidget = QFrame()
        self.emailLoginLayout = QVBoxLayout(self.emailLoginWidget)
        self.emailLoginLayout.setSpacing(15)
        self.emailLoginLayout.setContentsMargins(0, 0, 0, 0)

        # 邮箱输入框
        self.emailInput = LineEdit(self)
        self.emailInput.setPlaceholderText('请输入邮箱')
        self.emailInput.setClearButtonEnabled(True)

        # 密码输入框
        self.passwordInput = LineEdit(self)
        self.passwordInput.setPlaceholderText('请输入密码')
        self.passwordInput.setEchoMode(QLineEdit.Password)
        self.passwordInput.setClearButtonEnabled(True)

        # 记住账号复选框
        self.rememberCheckBox = CheckBox('记住账号', self)
        self.rememberCheckBox.setChecked(bool(self.settings.value('remember_email', False)))

        self.emailLoginLayout.addWidget(self.emailInput)
        self.emailLoginLayout.addWidget(self.passwordInput)
        self.emailLoginLayout.addWidget(self.rememberCheckBox)

        # === 手机登录页面 ===
        self.phoneLoginWidget = QFrame()
        self.phoneLoginLayout = QVBoxLayout(self.phoneLoginWidget)
        self.phoneLoginLayout.setSpacing(15)
        self.phoneLoginLayout.setContentsMargins(0, 0, 0, 0)

        # 手机号输入框
        self.phoneInput = LineEdit(self)
        self.phoneInput.setPlaceholderText('请输入手机号')
        self.phoneInput.setClearButtonEnabled(True)

        # 密码输入框（手机登录）
        self.phonePasswordInput = LineEdit(self)
        self.phonePasswordInput.setPlaceholderText('请输入密码')
        self.phonePasswordInput.setEchoMode(QLineEdit.Password)
        self.phonePasswordInput.setClearButtonEnabled(True)

        # 记住手机号复选框
        self.rememberPhoneCheckBox = CheckBox('记住手机号', self)
        self.rememberPhoneCheckBox.setChecked(bool(self.settings.value('remember_phone', False)))

        self.phoneLoginLayout.addWidget(self.phoneInput)
        self.phoneLoginLayout.addWidget(self.phonePasswordInput)
        self.phoneLoginLayout.addWidget(self.rememberPhoneCheckBox)

        # 添加到堆叠窗口
        self.loginStack.addWidget(self.emailLoginWidget)
        self.loginStack.addWidget(self.phoneLoginWidget)
        self.loginStack.setCurrentIndex(0)

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
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.loginTypeSegmented, 0, Qt.AlignCenter)
        self.vBoxLayout.addSpacing(20)

        self.loginLayout.addWidget(self.loginStack)
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

    def switch_login_type(self, index):
        """切换登录方式"""
        self.loginStack.setCurrentIndex(index)
        # 重置按钮状态
        self.loginButton.setEnabled(True)
        self.loginButton.setText('登录')

    def load_saved_credentials(self):
        """加载保存的账号信息"""
        # 加载邮箱
        if bool(self.settings.value('remember_email', False)):
            if saved_email := self.settings.value('email', ''):
                self.emailInput.setText(saved_email)

        # 加载手机号
        if bool(self.settings.value('remember_phone', False)):
            if saved_phone := self.settings.value('phone', ''):
                self.phoneInput.setText(saved_phone)

    def save_email(self, email):
        """保存邮箱账号"""
        if self.rememberCheckBox.isChecked():
            self.settings.setValue('remember_email', True)
            self.settings.setValue('email', email)
        else:
            self.settings.setValue('remember_email', False)
            self.settings.remove('email')
        self.settings.sync()

    def save_phone(self, phone):
        """保存手机号"""
        if self.rememberPhoneCheckBox.isChecked():
            self.settings.setValue('remember_phone', True)
            self.settings.setValue('phone', phone)
        else:
            self.settings.setValue('remember_phone', False)
            self.settings.remove('phone')
        self.settings.sync()

    def _update_countdown(self):
        """更新倒计时"""
        self.countdown_seconds -= 1
        if self.countdown_seconds <= 0:
            self.countdown_timer.stop()
            self.sendCodeButton.setEnabled(True)
            self.sendCodeButton.setText('获取验证码')
        else:
            self.sendCodeButton.setText(f'{self.countdown_seconds}秒后重试')



    def handle_login(self):
        """处理登录"""
        current_index = self.loginStack.currentIndex()

        if current_index == 0:
            # 邮箱登录
            self._handle_email_login()
        else:
            # 手机号登录
            self._handle_phone_login()

    def _handle_email_login(self):
        """处理邮箱登录"""
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
        self._perform_async_email_login(email, password)

    def _handle_phone_login(self):
        """处理手机号登录"""
        phone = self.phoneInput.text()
        password = self.phonePasswordInput.text()

        if not phone or not password:
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

        # 验证手机号格式
        if len(phone) != 11 or not phone.isdigit():
            InfoBar.error(
                title='错误',
                content='请输入正确的手机号',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 临时禁用按钮防止重复点击
        self.loginButton.setEnabled(False)
        self.loginButton.setText('登录中...')

        # 异步登录
        self._perform_async_phone_login(phone, password)

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

    def _perform_async_email_login(self, email, password):
        """执行异步邮箱登录"""
        def on_success(result):
            if result:
                # 保存邮箱账号（记住账号功能）
                self.save_email(email)

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
            self._handle_login_error(error)

        # 使用简化的API服务
        simple_api_service.login(
            email, password,
            callback_success=on_success,
            callback_error=on_error
        )

    def _perform_async_phone_login(self, phone, password):
        """执行异步手机号登录"""
        def on_success(result):
            if result:
                # 保存手机号（记住账号功能）
                self.save_phone(phone)

                # 获取用户信息（手机号登录返回的是phone字段）
                user_phone = result['user'].get('phone', phone)
                user_info = {'phone': user_phone}

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
            self._handle_login_error(error)

        # 使用简化的API服务
        simple_api_service.phone_login(
            phone, password,
            callback_success=on_success,
            callback_error=on_error
        )

    def _handle_login_error(self, error):
        """处理登录错误"""
        from app.core.error_handler import get_error_message
        from utils import logger

        # 获取用户友好的消息（支持多语言）
        lang = "zh"  # 默认中文
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