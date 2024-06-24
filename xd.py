from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QListWidget, QStackedWidget
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        """
        帮我创建一个页面，要求如下：
1、左侧是一个侧边栏，侧边栏中有选项：音视频转字幕，字幕翻译，编辑字幕，我的设置
2、点击侧边栏中的选项，右侧可以显示不同的页面内容
3、我的设置在侧边栏最下方
        """
        super(MainWindow, self).__init__()
        self.setWindowTitle("Sidebar Example")
        self.setGeometry(300, 100, 800, 600)

        # 创建主窗口的中央小部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 创建侧边栏
        self.sidebar = QListWidget()
        self.sidebar.insertItem(0, "音视频转字幕")
        self.sidebar.insertItem(1, "字幕翻译")
        self.sidebar.insertItem(2, "编辑字幕")
        self.sidebar.setFixedWidth(150)

        # 创建 QStackedWidget 来显示不同页面
        self.stack = QStackedWidget()
        self.stack.setFixedWidth(650)

        # 创建每个页面的内容
        self.page1 = QWidget()
        self.page2 = QWidget()
        self.page3 = QWidget()
        self.page4 = QWidget()
        self.setup_pages()

        # 添加页面到 QStackedWidget
        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)
        self.stack.addWidget(self.page3)
        self.stack.addWidget(self.page4)

        # 布局
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)

        # 连接信号
        self.sidebar.currentRowChanged.connect(self.display_page)

        # 将 "我的设置" 移动到侧边栏最下方
        self.sidebar.setLayout(QVBoxLayout())
        self.sidebar.layout().addStretch()
        self.sidebar.layout().addWidget(QPushButton("我的设置"))

    def setup_pages(self):
        # 页面1: 音视频转字幕
        layout1 = QVBoxLayout()
        layout1.addWidget(QLabel("这里是音视频转字幕页面"))
        self.page1.setLayout(layout1)

        # 页面2: 字幕翻译
        layout2 = QVBoxLayout()
        layout2.addWidget(QLabel("这里是字幕翻译页面"))
        self.page2.setLayout(layout2)

        # 页面3: 编辑字幕
        layout3 = QVBoxLayout()
        layout3.addWidget(QLabel("这里是编辑字幕页面"))
        self.page3.setLayout(layout3)


    def display_page(self, index):
        self.stack.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
