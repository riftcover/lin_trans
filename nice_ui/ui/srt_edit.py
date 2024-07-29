import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout)
from qfluentwidgets import CardWidget, ToolTipFilter, ToolTipPosition, TransparentToolButton, FluentIcon
from vendor.qfluentwidgets.multimedia import LinVideoWidget
from nice_ui.ui.style import SubtitleTable


class SubtitleEditPage(CardWidget):
    def __init__(self, patt):
        super().__init__()
        self.patt = patt
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.subtitleTable = SubtitleTable(self.patt)
        # 创建并添加CardWidget
        top_card = CardWidget()
        top_layout = QHBoxLayout(top_card)
        top_layout.setSpacing(10)
        top_layout.setContentsMargins(10, 10, 10, 10)

        export_button = TransparentToolButton(FluentIcon.EMBED)
        export_button.clicked.connect(self.export_srt)
        save_button = TransparentToolButton(FluentIcon.SAVE)
        save_button.clicked.connect(self.subtitleTable.save_subtitle)

        # 向下移动按钮
        down_rows = TransparentToolButton(FluentIcon.DOWN)
        down_rows.clicked.connect(self.subtitleTable.move_row_down_more)
        # 向上移动按钮
        up_rows = TransparentToolButton(FluentIcon.UP)
        up_rows.clicked.connect(self.subtitleTable.move_row_up_more)
        # 导入译文

        import_button = TransparentToolButton(FluentIcon.LABEL)
        import_button.clicked.connect(self.import_subtitle)

        # 从右向左排列按钮
        top_layout.addStretch(1)
        # top_layout.addWidget(import_button)
        top_layout.addWidget(down_rows)
        top_layout.addWidget(up_rows)
        top_layout.addWidget(save_button)
        top_layout.addWidget(export_button)

        self.videoWidget = LinVideoWidget(self.subtitleTable,self.subtitleTable.subtitles,self)
        # self.videoWidget.setVideo(QUrl('/Users/locodol/my_own/code/lin_trans/result/tt1/vv2.mp4'))
        self.videoWidget.setVideo(QUrl('/Users/locodol/my_own/code/lin_trans/result/tt1/tt1.mp4'))

        layout.addWidget(top_card)
        layout.addWidget(self.subtitleTable)

        # 水平布局
        h_layout = QHBoxLayout()
        h_layout.addLayout(layout,3)
        h_layout.addWidget(self.videoWidget,1)

        #设置布局
        self.setLayout(h_layout)

        export_button.setToolTip("导出srt格式字幕文件")
        export_button.installEventFilter(ToolTipFilter(export_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        save_button.setToolTip("保存到本地，以免丢失")
        save_button.installEventFilter(ToolTipFilter(save_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        down_rows.setToolTip("将勾选的译文整体向下移动")
        down_rows.installEventFilter(ToolTipFilter(down_rows, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        up_rows.setToolTip("将勾选的译文向上移动译文")
        up_rows.installEventFilter(ToolTipFilter(up_rows, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        import_button.setToolTip("导入译文")
        import_button.installEventFilter(ToolTipFilter(import_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))



    def export_srt(self):
        # todo：导出srt文件
        print("export srt")

    def import_subtitle(self):
        # todo：导入译文
        print("import subtitle")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleEditPage(patt='/Users/locodol/my_own/code/lin_trans/result/tt1/tt.srt')
    window.resize(1300, 800)
    window.show()
    sys.exit(app.exec())
