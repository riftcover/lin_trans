import sys

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, )
from qfluentwidgets import (PushButton, FluentIcon, )

from nice_ui.ui.style import SubtitleTable


class SubtitleEditPage(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        # 创建并添加SubtitleTable
        self.subtitleTable = SubtitleTable(self)
        layout.addWidget(self.subtitleTable)

        # 添加示例行
        self.subtitleTable.addRow()

        # 添加新行按钮
        addButton = PushButton("添加新行", self, icon=FluentIcon.ADD)
        addButton.clicked.connect(self.subtitleTable.addRow)
        layout.addWidget(addButton)






if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleEditPage()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())
