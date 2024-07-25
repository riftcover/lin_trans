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
        patt = r'D:\dcode\lin_trans\result\tt1\tt.srt'
        self.subtitleTable = SubtitleTable(patt)
        layout.addWidget(self.subtitleTable)






if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = SubtitleEditPage()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())
