import sys
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, QPushButton)
from qfluentwidgets import CardWidget, ToolTipFilter, ToolTipPosition

from nice_ui.ui.style import SubtitleTable


class SubtitleEditPage(CardWidget):
    def __init__(self, patt):
        super().__init__()
        self.patt = patt
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.subtitleTable = SubtitleTable(self.patt)
        # 创建并添加CardWidget
        top_card = CardWidget()
        top_layout = QHBoxLayout(top_card)
        top_layout.setSpacing(10)
        top_layout.setContentsMargins(10, 10, 10, 10)

        export_button = QPushButton("导出")
        export_button.clicked.connect(self.export_srt)
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.subtitleTable.save_subtitle)

        down_rows = QPushButton("下移译文")
        # 创建并添加SubtitleTable

        down_rows.clicked.connect(self.subtitleTable.move_row_down_more)
        # 向下移动按钮
        up_rows = QPushButton("上移译文")
        up_rows.clicked.connect(self.subtitleTable.move_row_up_more)
        # 向上移动按钮

        # 从右向左排列按钮
        top_layout.addStretch(1)
        top_layout.addWidget(down_rows)
        top_layout.addWidget(up_rows)
        top_layout.addWidget(save_button)
        top_layout.addWidget(export_button)

        layout.addWidget(top_card)

        layout.addWidget(self.subtitleTable)

        export_button.setToolTip("导出srt格式字幕文件")
        export_button.installEventFilter(ToolTipFilter(export_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        save_button.setToolTip("保存到本地，以免丢失")
        save_button.installEventFilter(ToolTipFilter(save_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        down_rows.setToolTip("将勾选的译文整体向下移动")
        down_rows.installEventFilter(ToolTipFilter(down_rows, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        up_rows.setToolTip("将勾选的译文向上移动译文")
        up_rows.installEventFilter(ToolTipFilter(up_rows, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))




    def export_srt(self):
        # todo：导出srt文件
        print("export srt")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleEditPage(patt='/Users/locodol/my_own/code/lin_trans/result/tt1/tt.srt')
    window.resize(1300, 800)
    window.show()
    sys.exit(app.exec())
