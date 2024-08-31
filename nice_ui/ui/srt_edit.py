import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QSplitter, QWidget)

from nice_ui.widget.subedit import SubtitleTable
# from nice_ui.ui.style import SubtitleTable
from vendor.qfluentwidgets import CardWidget, ToolTipFilter, ToolTipPosition, TransparentToolButton, FluentIcon
from vendor.qfluentwidgets.multimedia import LinVideoWidget


class AspectRatioWidget(QWidget):
    # 保持视频部件的宽高比
    def __init__(self, widget, aspect_ratio):
        super().__init__()
        self.aspect_ratio = aspect_ratio
        layout = QVBoxLayout(self)
        layout.addWidget(widget)

    def resizeEvent(self, event):
        # 视频媒体部分为16：9，底部bar自身高度为40，
        # 为了保证在编辑器中bar不会超出媒体部分，所以+50
        width = self.width()
        height = int(width / self.aspect_ratio)+50
        self.setFixedHeight(height)
        super().resizeEvent(event)

class SubtitleEditPage(CardWidget):
    def __init__(self, patt):
        super().__init__()
        self.patt = patt
        self.subtitle_table = SubtitleTable(self.patt)
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧部分
        left_widget = self.create_left_widget()
        splitter.addWidget(left_widget)

        # 右侧部分
        right_widget = self.create_right_widget()
        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setStretchFactor(0, 2)  # 左侧部件占2
        splitter.setStretchFactor(1, 1)  # 右侧部件占1

    def create_left_widget(self):
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)

        # 顶部卡片
        top_card = self.create_top_card()
        layout.addWidget(top_card)

        # 字幕表格

        layout.addWidget(self.subtitle_table)

        return left_widget

    def create_top_card(self):
        top_card = CardWidget()
        top_layout = QHBoxLayout(top_card)
        top_layout.setSpacing(10)
        top_layout.setContentsMargins(10, 10, 10, 10)

        # 添加按钮
        buttons = [
            (TransparentToolButton(FluentIcon.DOWN), self.subtitle_table.move_row_down_more, "将勾选的译文整体向下移动"),
            (TransparentToolButton(FluentIcon.UP), self.subtitle_table.move_row_up_more, "将勾选的译文向上移动译文"),
            (TransparentToolButton(FluentIcon.SAVE), self.subtitle_table.save_subtitle, "保存到本地，以免丢失"),
            (TransparentToolButton(FluentIcon.EMBED), self.export_srt, "导出srt格式字幕文件"),
        ]

        top_layout.addStretch(1)
        for button, callback, tooltip in buttons:
            button.clicked.connect(callback)
            button.setToolTip(tooltip)
            button.installEventFilter(ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
            top_layout.addWidget(button)

        return top_card

    def create_right_widget(self):
        right_widget = QWidget()
        video_layout = QVBoxLayout(right_widget)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.videoWidget = LinVideoWidget(self.subtitle_table, self.subtitle_table.subtitles, self)
        self.videoWidget.setVideo(QUrl('D:/dcode/lin_trans/result/tt1/tt.mp4'))
        video_container = AspectRatioWidget(self.videoWidget, 16/9)

        video_layout.addWidget(video_container)
        video_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 视频部件


        return right_widget

    def export_srt(self):
        # todo：导出srt文件
        print("export srt")

    def import_subtitle(self):
        # todo：导入译文
        print("import subtitle")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubtitleEditPage(patt= r'D:\dcode\lin_trans\result\tt1\tt.srt')
    # window = SubtitleEditPage(patt=r'D:\dcode\lin_trans\result\tt1\如何获取需求.srt')
    window.resize(1300, 800)
    window.show()
    sys.exit(app.exec())
