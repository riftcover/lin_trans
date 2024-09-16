from PySide6.QtCore import QSize


class GuiSize:
    row_button_icon_size = QSize(20, 20)
    top_button_size = QSize(32, 30)
    row_button_size = QSize(30, 28)



    def _create_action_button(self, icon, tooltip: str, callback: callable, size: QSize):
        """
        创建一个工具按钮，并设置其图标、提示和点击事件。
        参数:
            icon: 按钮的图标。
            tooltip: 鼠标悬停时显示的提示信息。
            callback: 按钮被点击时调用的回调函数。
            size: 按钮的大小，默认值为变量 button_size。

        返回:
            ToolButton 对象，该对象根据提供的参数进行了初始化。

        """
        button = ToolButton(icon)
        button.setFixedSize(size)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        # 设置工具提示立即显示
        button.installEventFilter(ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        button.clicked.connect(callback)
        return button