import os
import shutil

from PySide6.QtCore import QUrl, Qt, QSize, QSettings, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QLineEdit, QPushButton, QRadioButton, QFileDialog,
                               QDialog, QLabel, QGridLayout, QFrame)
from PySide6.QtGui import QColor, QIcon

from components.widget.custom_splitter import CustomSplitter
from nice_ui.util.tools import get_default_documents_path
from utils import logger
from vendor.qfluentwidgets import (CardWidget, ToolTipFilter, ToolTipPosition, TransparentToolButton, FluentIcon as FIF,
                                   PushButton, InfoBar, InfoBarPosition, PrimaryPushButton, RadioButton, LineEdit,
                                   BodyLabel, StrongBodyLabel, SubtitleLabel)
from vendor.qfluentwidgets.common.style_sheet import FluentStyleSheet
from vendor.qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase
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
        height = int(width / self.aspect_ratio) + 50
        self.setFixedHeight(height)
        super().resizeEvent(event)


class SubtitleEditPage(QWidget):

    def __init__(
            self, patt: str, med_path: str, settings: QSettings = None, parent=None
    ):
        from components.widget import SubtitleTable

        """

        Args:
            patt: srt文件路径
            med_path: 视频文件路径
            settings: settings
            parent:
        """
        super().__init__(parent=parent)
        self.settings = settings
        self.patt = patt
        self.media_path = med_path
        self.subtitle_table = SubtitleTable(self.patt)
        self.subtitle_table.play_from_time_signal.connect(self.play_video_from_time)
        self.subtitle_table.seek_to_time_signal.connect(self.seek_video_to_time)  # 新增连接

        self.subtitle_table.model.subtitleUpdated.connect(self.update_video_subtitle) #字幕更新信号

        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除布局边距
        splitter = CustomSplitter(Qt.Horizontal)
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
        top_layout.setContentsMargins(15, 10, 15, 10)

        # 添加按钮
        buttons = [
            (
                TransparentToolButton(FIF.DOWN),
                self.move_row_down_more,
                "将勾选的译文整体向下移动",
            ),
            (
                TransparentToolButton(FIF.UP),
                self.move_row_up_more,
                "将勾选的译文向上移动译文",
            ),
            (
                TransparentToolButton(FIF.SAVE),
                self.save_srt,
                "保存到本地，以免丢失",
            ),
            (
                TransparentToolButton(FIF.EMBED),
                self.export_srt,
                "导出srt格式字幕文件",
            ),
        ]

        top_layout.addStretch(1)
        for button, callback, tooltip in buttons:
            button.setIconSize(QSize(20, 20))
            button.setFixedSize(QSize(30, 30))
            button.clicked.connect(callback)
            button.setToolTip(tooltip)
            button.installEventFilter(
                ToolTipFilter(
                    button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT
                )
            )
            top_layout.addWidget(button)

        return top_card

    def create_right_widget(self):
        right_widget = QWidget()
        video_layout = QVBoxLayout(right_widget)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.videoWidget = LinVideoWidget(
            self.subtitle_table, self.subtitle_table.subtitles, self
        )  # Pass subtitles here
        self.videoWidget.setVideo(QUrl(self.media_path))
        video_container = AspectRatioWidget(self.videoWidget, 16 / 9)

        video_layout.addWidget(video_container)
        video_layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # 视频部件

        return right_widget

    def clear_table_focus(self):
        """
        在这个Widget中点击按钮（上下移动，保存等）时，subtitle_table 中的所有编辑器的焦点默认不会被清除，
        导致进行上下移动等操作，subtitle_table中最后一条没有被setdata
        因此，需要在按钮点击时，先清除所有编辑器的焦点，然后再重新设置焦点到 ListTableView。
        1. connect_buttons 方法：在 MainWindow 初始化时，连接按钮的点击信号到 clear_table_focus 槽函数。
        2. clear_table_focus 方法：清除 ListTableView 中的所有编辑器的焦点，并重新设置焦点到 ListTableView。
        """
        self.subtitle_table.clearFocus()
        self.subtitle_table.setFocus(Qt.OtherFocusReason)

    def update_video_subtitle(self):
        """
        当字幕内容更新时，更新视频播放器中的字幕显示
        """
        if hasattr(self, 'videoWidget'):
            current_position = self.videoWidget.player.position()
            self.videoWidget.update_subtitle_at_position(current_position)

    def move_row_down_more(self):
        self.clear_table_focus()
        self.subtitle_table.move_row_down_more()

    def move_row_up_more(self):
        self.clear_table_focus()
        self.subtitle_table.move_row_up_more()

    def play_video_from_time(self, start_time: str):
        """
        从指定时间开始播放视频

        这个方法在用户点击字幕表格中的播放按钮时被调用。
        它将视频播放器的位置设置到指定的开始时间，然后开始播放。

        Args:
            start_time (str): 开始播放的时间，格式为 "HH:MM:SS,mmm"
        """
        if hasattr(self, 'videoWidget'):
            time_ms = self.convert_time_to_ms(start_time)
            self.videoWidget.player.setPosition(time_ms)
            self.videoWidget.play()

    def seek_video_to_time(self, start_time: str):
        """
        将视频跳转到指定时间

        这个方法在用户点击字幕表格中的原文或译文列时被调用。
        它只将视频播放器的位置设置到指定的时间，但不开始播放。

        Args:
            start_time (str): 跳转的目标时间，格式为 "HH:MM:SS,mmm"
        """
        if hasattr(self, 'videoWidget'):
            time_ms = self.convert_time_to_ms(start_time)
            self.videoWidget.player.setPosition(time_ms+1)
            # 不调用 play() 方法，所以视频不会开始播放

    @staticmethod
    def convert_time_to_ms(time_str: str) -> int:
        """
        将时间字符串转换为毫秒

        Args:
            time_str (str): 时间字符串，格式为 "HH:MM:SS,mmm"

        Returns:
            int: 转换后的毫秒数
        """
        h, m, s = time_str.split(':')
        s, ms = s.split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

    def export_srt(self):
        dialog = ExportSubtitleDialog([self.patt], self)
        dialog.exec()

    def save_srt(self):
        self.clear_table_focus()
        self.subtitle_table.save_subtitle()

    def import_subtitle(self):
        # todo：导入译文
        print("import subtitle")

    def stop_video(self):
        """停止视频播放"""
        if hasattr(self, 'videoWidget'):
            self.videoWidget.stop()

    def closeEvent(self, event):
        """在窗口关闭时停止视频播放"""
        self.stop_video()
        super().closeEvent(event)


class ExportSubtitleDialog(MaskDialogBase):
    """现代化导出字幕对话框"""
    def __init__(self, paths: list, parent=None):
        super().__init__(parent)
        self.paths = paths if isinstance(paths, list) else [paths]
        self.setWindowTitle("导出字幕")
        self.settings = self.parent().settings

        # 设置对话框属性
        self.widget.setFixedWidth(420)  # 减小宽度
        self.widget.setFixedHeight(280)  # 减小高度
        self.widget.setObjectName("exportDialogWidget")

        # 设置阴影和遮罩效果
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))

        # 创建主布局
        self.mainLayout = QVBoxLayout(self.widget)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)  # 减小边距
        self.mainLayout.setSpacing(16)  # 减小间距

        # 初始化UI
        self._init_ui()

        # 应用样式
        FluentStyleSheet.DIALOG.apply(self)

        # 应用自定义样式
        from components.resource_manager import StyleManager
        StyleManager.apply_style(self, "export_subtitle_dialog")

    def _init_ui(self):
        # 标题 - 简洁标题，无图标
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        title_label = SubtitleLabel("导出字幕", self.widget)
        title_label.setObjectName("dialogTitle")

        title_layout.addWidget(title_label)
        title_layout.addStretch(1)

        self.mainLayout.addLayout(title_layout)

        # 内容卡片
        content_card = CardWidget(self.widget)
        content_card.setObjectName("contentCard")
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(16, 16, 16, 16)  # 减小内边距
        content_layout.setSpacing(12)  # 减小间距

        # 字幕格式选择
        format_layout = QGridLayout()
        format_layout.setColumnStretch(1, 1)
        format_layout.setVerticalSpacing(8)  # 减小垂直间距
        format_layout.setHorizontalSpacing(8)  # 减小水平间距

        format_label = BodyLabel("字幕格式:", content_card)
        format_label.setObjectName("formatLabel")

        format_options = QFrame(content_card)
        format_options.setObjectName("formatOptions")
        format_options_layout = QHBoxLayout(format_options)
        format_options_layout.setContentsMargins(0, 0, 0, 0)
        format_options_layout.setSpacing(10)

        self.srt_radio = RadioButton("SRT", format_options)
        self.txt_radio = RadioButton("TXT", format_options)
        self.srt_radio.setChecked(True)  # 默认选择SRT

        format_options_layout.addWidget(self.srt_radio)
        format_options_layout.addWidget(self.txt_radio)
        format_options_layout.addStretch(1)

        format_layout.addWidget(format_label, 0, 0)
        format_layout.addWidget(format_options, 0, 1)

        # 导出路径
        path_label = BodyLabel("导出路径:", content_card)
        path_label.setObjectName("pathLabel")

        path_input_frame = QFrame(content_card)
        path_input_frame.setObjectName("pathInputFrame")
        path_input_layout = QHBoxLayout(path_input_frame)
        path_input_layout.setContentsMargins(0, 0, 0, 0)
        path_input_layout.setSpacing(8)

        last_export_path = self.settings.value(
            "last_export_path", get_default_documents_path()
        )
        self.path_input = LineEdit(path_input_frame)
        self.path_input.setText(last_export_path)
        self.path_input.setPlaceholderText("选择导出目录...")

        choose_button = PushButton("浏览...", path_input_frame)
        choose_button.clicked.connect(self.choose_path)

        path_input_layout.addWidget(self.path_input)
        path_input_layout.addWidget(choose_button)

        format_layout.addWidget(path_label, 1, 0)
        format_layout.addWidget(path_input_frame, 1, 1)

        content_layout.addLayout(format_layout)

        # 添加内容卡片到主布局
        self.mainLayout.addWidget(content_card)

        # 按钮区域 - 使用更紧凑的按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)  # 减小间距

        cancel_button = PushButton("取消", self.widget)
        cancel_button.setFixedWidth(75)  # 固定宽度
        cancel_button.clicked.connect(self.reject)

        export_button = PrimaryPushButton("导出", self.widget)
        export_button.setFixedWidth(75)  # 固定宽度
        export_button.clicked.connect(self.export_subtitle)

        button_layout.addStretch(1)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(export_button)

        self.mainLayout.addLayout(button_layout)

    def choose_path(self):
        """选择导出路径"""
        if path := QFileDialog.getExistingDirectory(self, "选择导出路径"):
            self.path_input.setText(path)
            # 保存路径到设置
            self.settings.setValue("last_export_path", path)

    def export_subtitle(self):
        """导出字幕文件"""
        export_path = self.path_input.text()
        export_format = "srt" if self.srt_radio.isChecked() else "txt"

        # 检查导出路径是否存在
        if not os.path.exists(export_path):
            logger.error(f"导出目录不存在: {export_path}")
            InfoBar.error(
                title="错误",
                content="导出目录不存在",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.parent(),
            )
            return

        # 检查字幕文件是否存在
        for path in self.paths:
            if not os.path.exists(path):
                logger.error(f"字幕文件被删除: {path}")
                InfoBar.error(
                    title="错误",
                    content="字幕文件被删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.parent(),
                )
                return

            # 导出文件
            try:
                if export_format == "srt":
                    # 复制SRT文件
                    dest_path = os.path.join(export_path, os.path.basename(path))
                    shutil.copy(str(path), dest_path)
                    logger.info(f"已导出SRT文件到: {dest_path}")
                else:
                    # 导出为TXT格式
                    self._export_txt(path, export_path)
            except Exception as e:
                logger.error(f"导出文件失败: {str(e)}")
                InfoBar.error(
                    title="导出失败",
                    content=f"导出文件时发生错误: {str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self.parent(),
                )
                return

        # 导出成功，关闭对话框
        self.accept()

        # 显示成功提示
        InfoBar.success(
            title="导出成功",
            content="字幕文件已成功导出",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self.parent(),
        )

    @staticmethod
    def _export_txt(src_path, export_path: str):
        """将SRT文件导出为TXT格式

        Args:
            src_path: SRT文件路径
            export_path: 导出目录
        """
        try:
            # 读取源文件
            with open(src_path, "r", encoding="utf-8") as src_file:
                lines = src_file.readlines()

            # 提取原文和译文字幕
            original_subtitles = []
            translated_subtitles = []

            i = 0
            while i < len(lines):
                # 跳过序号行和时间戳行
                i += 2

                # 读取原文字幕
                if i < len(lines) and lines[i].strip():
                    original_subtitles.append(lines[i].strip())
                    i += 1

                # 检查是否有译文字幕
                if i < len(lines) and lines[i].strip():
                    translated_subtitles.append(lines[i].strip())
                    i += 1

                # 跳过空行
                while i < len(lines) and not lines[i].strip():
                    i += 1

            # 生成导出文件路径
            export_name = os.path.splitext(os.path.basename(src_path))[0]
            export_file_path = os.path.join(export_path, f"{export_name}.txt")

            # 写入导出文件
            with open(export_file_path, "w", encoding="utf-8") as dest_file:
                # 写入原文字幕
                if original_subtitles:
                    dest_file.write("# 原文\n")
                    dest_file.write("".join(original_subtitles) + "\n\n")

                # 写入译文字幕（如果存在）
                if translated_subtitles:
                    dest_file.write("# 译文\n")
                    dest_file.write("\n".join(translated_subtitles) + "\n")

            logger.info(f"已导出TXT文件到: {export_file_path}")
            return export_file_path

        except Exception as e:
            logger.error(f"导出TXT文件失败: {str(e)}")
            raise
