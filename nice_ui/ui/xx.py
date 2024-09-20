class ProxyTestWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.handle_response)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.test_button = QPushButton("测试代理", self)
        self.test_button.clicked.connect(self.test_proxy)
        self.response_text = QTextEdit(self)
        self.response_text.setReadOnly(True)

        layout.addWidget(self.test_button)
        layout.addWidget(self.response_text)

    def test_proxy(self):
        url = QUrl("http://www.google.com")
        request = QNetworkRequest(url)
        self.network_manager.get(request)

    def handle_response(self, reply):
        if reply.error() == QNetworkReply.NoError:
            content = reply.readAll()
            self.response_text.setPlainText(str(content, encoding='utf-8'))
            InfoBar.success(
                title="成功",
                content=f"测试成功: 状态码 {reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        else:
            error_msg = reply.errorString()
            self.response_text.setPlainText(f"错误: {error_msg}")
            InfoBar.error(
                title="错误",
                content=f"测试失败: {error_msg}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )

        reply.deleteLater()