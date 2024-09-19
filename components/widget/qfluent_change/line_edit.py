class PasswordLineEdit(LineEdit):
    """ Password line edit """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.viewButton = LineEditButton(FIF.VIEW, self)
        self._passwordVisible = False  # 新增状态变量

        self.setEchoMode(QLineEdit.Password)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.hBoxLayout.addWidget(self.viewButton, 0, Qt.AlignRight)
        self.setClearButtonEnabled(False)

        self.viewButton.installEventFilter(self)
        self.viewButton.setIconSize(QSize(13, 13))
        self.viewButton.setFixedSize(29, 25)

    def setPasswordVisible(self, isVisible: bool):
        """ set the visibility of password """
        self._passwordVisible = isVisible
        if isVisible:
            self.setEchoMode(QLineEdit.Normal)
            self.viewButton.setIcon(FIF.VIEW.icon())
        else:
            self.setEchoMode(QLineEdit.Password)
            self.viewButton.setIcon(FIF.HIDE.icon())

    def isPasswordVisible(self):
        return self._passwordVisible

    def setClearButtonEnabled(self, enable: bool):
        self._isClearButtonEnabled = enable

        if self.viewButton.isHidden():
            self.setTextMargins(0, 0, 28*enable, 0)
        else:
            self.setTextMargins(0, 0, 28*enable + 30, 0)

    def setViewPasswordButtonVisible(self, isVisible: bool):
        """ set the visibility of view password button """
        self.viewButton.setVisible(isVisible)

    def eventFilter(self, obj, e):
        if obj is not self.viewButton or not self.isEnabled():
            return super().eventFilter(obj, e)

        if e.type() == QEvent.MouseButtonPress:
            self.setPasswordVisible(not self.isPasswordVisible())

        return super().eventFilter(obj, e)

    def inputMethodQuery(self, query: Qt.InputMethodQuery):
        # Disable IME for PasswordLineEdit
        if query == Qt.InputMethodQuery.ImEnabled:
            return False
        else:
            return super().inputMethodQuery(query)

    passwordVisible = Property(bool, isPasswordVisible, setPasswordVisible)