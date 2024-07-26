import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton)
from qfluentwidgets import CardWidget

from nice_ui.ui.style import SubtitleTable


class SubtitleEditPage(CardWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        # 创建并添加CardWidget
        topCard = CardWidget()
        topLayout = QHBoxLayout(topCard)
        topLayout.setSpacing(10)
        topLayout.setContentsMargins(10, 10, 10, 10)

        exportButton = QPushButton("导出")
        exportButton.clicked.connect(self.export_srt)
        saveButton = QPushButton("保存")
        saveButton.clicked.connect(self.save_srt)

        down_rows = QPushButton("下移译文")
        # 创建并添加SubtitleTable
        patt = '/Users/locodol/my_own/code/lin_trans/result/tt1/tt.srt'
        self.subtitleTable = SubtitleTable(patt)
        down_rows.clicked.connect(self.subtitleTable.move_row_down_more)
        # 向下移动按钮
        up_rows = QPushButton("上移译文")
        up_rows.clicked.connect(self.subtitleTable.move_row_up_more)
        # 向上移动按钮


        # 从右向左排列按钮
        topLayout.addStretch(1)
        topLayout.addWidget(down_rows)
        topLayout.addWidget(up_rows)
        topLayout.addWidget(saveButton)
        topLayout.addWidget(exportButton)


        layout.addWidget(topCard)


        layout.addWidget(self.subtitleTable)

    def export_srt(self):
        # todo：导出srt文件
        print("export srt")

    def save_srt(self):
        # todo：保存srt文件
        print("save srt")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleEditPage()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())
