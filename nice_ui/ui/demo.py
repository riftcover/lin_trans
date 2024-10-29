from PySide6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 示例")

        self.label = QLabel("欢迎使用PySide6!")
        self.button = QPushButton("点击我")
        self.button.clicked.connect(self.update_label)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def update_label(self):
        self.label.setText("按钮被点击了!")