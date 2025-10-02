import shutil
from pathlib import Path

from PySide6.QtCore import QUrl, Qt, QSize, QSettings, QThread, Signal
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QWidget, QLineEdit, QPushButton, QRadioButton, QFileDialog,
                               QDialog, QLabel, QProgressDialog, )

from components.widget.custom_splitter import CustomSplitter
from nice_ui.util.tools import get_default_documents_path
from utils import logger
from vendor.qfluentwidgets import (CardWidget, ToolTipFilter, ToolTipPosition, TransparentToolButton, FluentIcon, PushButton, InfoBar, InfoBarPosition, )
from vendor.qfluentwidgets.multimedia import LinVideoWidget
from app.smart_sentence_processor import check_smart_sentence_available, process_smart_sentence
from components.widget import SubtitleTable


class SmartSentenceWorker(QThread):
    """智能分句处理工作线程"""
    progress_updated = Signal(int, str)  # 进度和消息
    finished = Signal(bool, str)  # 是否成功和消息

    def __init__(self, srt_file_path: str):
        super().__init__()
        self.srt_file_path = srt_file_path

    def run(self):
        """执行智能分句处理"""

        def progress_callback(progress: int, message: str):
            self.progress_updated.emit(progress, message)

        success, message = process_smart_sentence(self.srt_file_path, progress_callback)
        self.finished.emit(success, message)


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

        self.subtitle_table.model.subtitleUpdated.connect(self.update_video_subtitle)  #字幕更新信号

        # 智能分句相关
        self.smart_sentence_worker = None
        self.progress_dialog = None

        # 视频组件 - 在构造函数中初始化，确保生命周期明确
        self.videoWidget = None

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

    def smart_sentence_process(self):
        """智能分句处理"""
        try:
            # 检查是否支持智能分句
            if not check_smart_sentence_available(self.patt):
                InfoBar.warning(
                    title="提示",
                    content="当前字幕文件不支持智能分句功能",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self,
                )
                return

            # 确保清理之前的资源 - 使用统一的清理方法
            self._cleanup_smart_sentence_resources()

            # 创建进度对话框
            self.progress_dialog = QProgressDialog("正在进行智能分句处理...", "取消", 0, 100, self)
            self.progress_dialog.setWindowTitle("智能分句")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setMinimumDuration(500)  # 延迟500ms显示，避免闪烁
            self.progress_dialog.setValue(0)
            self.progress_dialog.setAutoClose(False)  # 禁止自动关闭
            self.progress_dialog.setAutoReset(False)  # 禁止自动重置

            # 创建工作线程
            self.smart_sentence_worker = SmartSentenceWorker(self.patt)
            self.smart_sentence_worker.progress_updated.connect(self._on_smart_sentence_progress)
            self.smart_sentence_worker.finished.connect(self._on_smart_sentence_finished)

            # 连接取消按钮 - 在显示前连接
            self.progress_dialog.canceled.connect(self._cancel_smart_sentence)

            # 启动处理
            self.smart_sentence_worker.start()

            # 显示进度对话框
            self.progress_dialog.show()

            logger.info("智能分句处理已启动")

        except Exception as e:
            logger.error(f"启动智能分句处理时发生错误: {str(e)}")
            InfoBar.error(
                title="错误",
                content=f"启动智能分句处理失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self,
            )

    def _on_smart_sentence_progress(self, progress: int, message: str):
        """智能分句进度更新"""
        try:
            # 严格检查对话框状态 - 确保对话框存在、未被取消且仍然可见
            if (self.progress_dialog is not None and
                    hasattr(self.progress_dialog, 'setValue') and
                    not self.progress_dialog.wasCanceled() and
                    self.progress_dialog.isVisible()):

                self.progress_dialog.setValue(progress)
                self.progress_dialog.setLabelText(message)
                logger.debug(f"进度更新: {progress}% - {message}")
            else:
                logger.debug(f"进度对话框不可用，跳过更新: {progress}% - {message}")
        except Exception as e:
            logger.debug(f"更新进度时发生错误，跳过: {str(e)}")

    def _on_smart_sentence_finished(self, success: bool, message: str):
        """智能分句处理完成"""
        try:
            logger.info(f"智能分句处理完成: success={success}, message={message}")

            # 使用统一的清理方法
            self._cleanup_smart_sentence_resources()

            if success:
                # 成功时重新加载字幕表格
                try:
                    logger.info("开始刷新字幕表格...")

                    # 1. 重新加载模型数据
                    self.subtitle_table.model.beginResetModel()
                    self.subtitle_table.model.sub_data = self.subtitle_table.model.load_subtitle()
                    self.subtitle_table.model.endResetModel()

                    # 2. 更新字幕表格的内部字幕数据 - 使用get_subtitles方法获取数据副本
                    self.subtitle_table.subtitles = self.subtitle_table.model.get_subtitles().copy()

                    # 3. 重新处理字幕数据用于播放器
                    self.subtitle_table.process_subtitles()

                    # 4. 更新可见的编辑器
                    self.subtitle_table.update_editors()

                    logger.info(f"字幕表格已成功刷新，新的行数: {self.subtitle_table.model.rowCount()}")
                except Exception as e:
                    logger.error(f"刷新字幕表格时发生错误: {str(e)}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")

                InfoBar.success(
                    title="成功",
                    content="智能分句处理完成，字幕已更新",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self,
                )
            else:
                InfoBar.error(
                    title="失败",
                    content=f"智能分句处理失败: {message}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self,
                )

        except Exception as e:
            logger.error(f"处理智能分句完成回调时发生错误: {str(e)}")

    def _cancel_smart_sentence(self):
        """取消智能分句处理"""
        try:
            logger.info("_cancel_smart_sentence被调用")

            # 检查是否真的需要取消
            if not self.smart_sentence_worker:
                logger.warning("没有运行中的智能分句任务，可能是误触发")
                return

            # 使用统一的清理方法
            self._cleanup_smart_sentence_resources()

            logger.info("用户取消了智能分句处理")

            # 显示取消提示
            InfoBar.warning(
                title="已取消",
                content="智能分句处理已取消",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )

        except Exception as e:
            logger.error(f"取消智能分句处理时发生错误: {str(e)}")

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
                TransparentToolButton(FluentIcon.DOWN),
                self.move_row_down_more,
                "将勾选的译文整体向下移动",
            ),
            (
                TransparentToolButton(FluentIcon.UP),
                self.move_row_up_more,
                "将勾选的译文向上移动译文",
            ),
            (
                TransparentToolButton(FluentIcon.SAVE),
                self.save_srt,
                "保存到本地，以免丢失",
            ),
            (
                TransparentToolButton(FluentIcon.EMBED),
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

        # 智能分句按钮（根据可用性决定是否添加）
        """
        todo: 先屏蔽智能分句按钮，等待本地语言和服务端分句支持保证一致再打开
        （auto|不支持的语言：服务端无法处理，分句后时间轴可能还有问题）        
        """
        if 1 == 2:
            # if check_smart_sentence_available(self.patt):
            smart_sentence_btn = TransparentToolButton(FluentIcon.ROBOT)
            smart_sentence_btn.setIconSize(QSize(20, 20))
            smart_sentence_btn.setFixedSize(QSize(30, 30))
            smart_sentence_btn.clicked.connect(self.smart_sentence_process)
            smart_sentence_btn.setToolTip("使用AI智能优化断句")
            smart_sentence_btn.installEventFilter(
                ToolTipFilter(
                    smart_sentence_btn, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT
                )
            )
            top_layout.addWidget(smart_sentence_btn)

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
        if self.videoWidget is not None:
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
        if self.videoWidget is not None:
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
        if self.videoWidget is not None:
            time_ms = self.convert_time_to_ms(start_time)
            self.videoWidget.player.setPosition(time_ms + 1)
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
        if self.videoWidget is not None:
            self.videoWidget.stop()

    def _cleanup_smart_sentence_resources(self):
        """统一清理智能分句相关资源 - Linus式：一个地方处理所有清理"""
        logger.debug("开始清理智能分句资源")

        # 1. 先断开工作线程的信号连接，防止延迟信号到达
        if self.smart_sentence_worker:
            try:
                # 断开所有信号连接
                self.smart_sentence_worker.progress_updated.disconnect()
                self.smart_sentence_worker.finished.disconnect()
                logger.debug("已断开工作线程信号连接")
            except Exception:
                pass  # 信号可能已经断开，忽略错误

            if self.smart_sentence_worker.isRunning():
                logger.debug("终止运行中的智能分句线程")
                self.smart_sentence_worker.terminate()
                self.smart_sentence_worker.wait(3000)  # 最多等待3秒
            self.smart_sentence_worker.deleteLater()
            self.smart_sentence_worker = None

        # 2. 清理进度对话框
        if self.progress_dialog:
            try:
                # 断开所有信号连接
                self.progress_dialog.canceled.disconnect()
            except Exception:
                pass  # 信号可能已经断开，忽略错误

            self.progress_dialog.close()
            self.progress_dialog = None

        logger.debug("智能分句资源清理完成")

    def _cleanup_video_resources(self):
        """清理视频相关资源"""
        if self.videoWidget is not None:
            logger.debug("清理视频组件")
            self.videoWidget.stop()
            self.videoWidget = None

    def closeEvent(self, event):
        """在窗口关闭时清理所有资源"""
        logger.debug("窗口正在关闭，清理资源")

        # 清理智能分句相关资源
        self._cleanup_smart_sentence_resources()

        # 清理视频相关资源
        self._cleanup_video_resources()

        super().closeEvent(event)


class ExportSubtitleDialog(QDialog):
    # 导出字幕弹窗
    def __init__(self, paths: list, parent=None):
        super().__init__(parent)
        self.paths = paths if isinstance(paths, list) else [paths]
        self.setWindowTitle("导出字幕")
        self.setFixedSize(400, 200)
        self.settings = self.parent().settings

        layout = QVBoxLayout(self)

        # 第一行：字幕格式
        format_layout = QHBoxLayout()
        format_label = QLabel("字幕格式:")
        self.srt_radio = QRadioButton("SRT")
        self.txt_radio = QRadioButton("TXT")
        self.srt_radio.setChecked(True)  # 默认选择SRT

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.srt_radio)
        format_layout.addWidget(self.txt_radio)
        format_layout.addStretch(1)  # 添加伸缩空间
        layout.addLayout(format_layout)

        # 第二行：导出路径
        path_layout = QHBoxLayout()
        path_label = QLabel("导出路径:")
        last_export_path = self.settings.value(
            "last_export_path", get_default_documents_path()
        )
        self.path_input = QLineEdit(last_export_path)
        choose_button = QPushButton("选择路径")
        choose_button.clicked.connect(self.choose_path)

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(choose_button)
        layout.addLayout(path_layout)

        # 第三行：导出按钮
        button_layout = QHBoxLayout()
        export_button = PushButton("导出字幕")
        export_button.setFixedSize(QSize(100, 40))  # 设置按钮大小
        export_button.clicked.connect(self.export_subtitle)
        button_layout.addStretch(1)
        button_layout.addWidget(export_button)
        button_layout.addStretch(1)
        layout.addLayout(button_layout)

    def choose_path(self):
        # 选择导出路径
        if path := QFileDialog.getExistingDirectory(self, "选择导出路径"):
            self.path_input.setText(path)
        self.settings.setValue("last_export_path", self.path_input.text())

    def export_subtitle(self):
        # 实现导出逻辑
        export_path = self.path_input.text()
        export_format = "srt" if self.srt_radio.isChecked() else "txt"
        # 检查导出路径是否存在
        if not Path(export_path).exists():
            logger.error(f"导出目录不存在: {export_path}")
            InfoBar.error(
                title="错误",
                content="导出目录不存在",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
            return

        for path in self.paths:
            if not Path(path).exists():
                logger.error(f"字幕文件被删除: {path}")
                InfoBar.error(
                    title="错误",
                    content="字幕文件被删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self,
                )
                return
            if export_format == "srt":
                shutil.copy(str(path), export_path)  # 复制文件
            else:
                self._export_txt(path, export_path)

        self.accept()  # 关闭对话框
        InfoBar.success(
            title="成功",
            content="文件已导出",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    @staticmethod
    def _export_txt(src_path, export_path: str):
        # 实现语种文本提取
        with open(src_path, "r", encoding="utf-8") as src_file:
            lines = src_file.readlines()

        # 提取第一行和第二行字幕
        first_line_subtitles = []
        second_line_subtitles = []

        i = 0
        while i < len(lines):
            # 跳过序号行和时间戳行
            i += 2

            # 读取第一行字幕
            if i < len(lines) and lines[i].strip():
                first_line_subtitles.append(lines[i].strip())
                i += 1

            # 检查是否有第二行字幕
            if i < len(lines) and lines[i].strip():
                second_line_subtitles.append(lines[i].strip())
                i += 1

            # 跳过空行
            while i < len(lines) and not lines[i].strip():
                i += 1

        # 保存提取的文本到 export_path
        export_name = Path(src_path).stem
        output_file = Path(export_path) / f"{export_name}.txt"
        with open(
                output_file, "w", encoding="utf-8"
        ) as dest_file:
            # 写入第一行字幕，每行都换行
            dest_file.write("\n".join(first_line_subtitles) + "\n")
            # 写入第二行字幕（如果存在），每行都换行
            if second_line_subtitles:
                dest_file.write("\n".join(second_line_subtitles) + "\n")
