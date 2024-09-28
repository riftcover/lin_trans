import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget

from vendor.qfluentwidgets import (NavigationInterface, NavigationItemPosition, NavigationWidget, Theme, setTheme, FluentIcon as FIF, FluentWindow)


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口标题
        self.setWindowTitle("Mac 风格 Fluent UI 示例")

        # 创建堆叠小部件
        self.stackedWidget = QStackedWidget(self)

        # 创建并设置导航界面
        self.navigationInterface = NavigationInterface(self, showMenuButton=True, showReturnButton=True)

        # 添加示例页面
        self.homeWidget = QWidget()
        self.homeWidget.setObjectName("homeWidget")
        self.settingsWidget = QWidget()
        self.settingsWidget.setObjectName("settingsWidget")
        self.stackedWidget.addWidget(self.homeWidget)
        self.stackedWidget.addWidget(self.settingsWidget)

        # 添加导航项
        self.addSubInterface(self.homeWidget, FIF.HOME, "主页")
        self.addSubInterface(self.settingsWidget, FIF.SETTING, "设置")

        # 设置主题
        setTheme(Theme.AUTO)

        # 设置窗口大小
        self.resize(900, 700)

        # 对于 Mac 系统，设置统一的标题栏和工具栏
        if sys.platform == "darwin":
            self.setWindowFlag(Qt.WindowType.WindowFullscreenButtonHint, True)
            self.setUnifiedTitleAndToolBarOnMac(True)  # 设置统一的标题栏和工具栏

        # 初始化界面
        # self.initNavigation()

        self.navigationInterface.setFixedWidth(200)

        # 设置主布局
        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(self.navigationInterface)
        mainLayout.addWidget(self.stackedWidget)
        self.setLayout(mainLayout)

    def addSubInterface(self, widget, icon, text):
        self.navigationInterface.addItem(
            NavigationWidget(
                self,  # 传递父窗口
                icon
            ),
            text,
            NavigationItemPosition.SCROLL
        )
        self.stackedWidget.addWidget(widget)  # 确保将 widget 添加到堆叠小部件中

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())