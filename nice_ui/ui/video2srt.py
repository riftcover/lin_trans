import os
import subprocess

from PySide6.QtCore import (Qt, Slot, QSize)
from PySide6.QtGui import (QDragEnterEvent, QDropEvent, QColor, QPalette)
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QSizePolicy, QTableWidget, QVBoxLayout, QWidget, QAbstractItemView, QTableWidgetItem, QHeaderView,
                               QStyle)

from nice_ui.configure import config
from nice_ui.main_win.secwin import SecWindow
from vendor.qfluentwidgets import PushButton, FluentIcon, TableWidget, ComboBox, CheckBox, BodyLabel, CardWidget, TableItemDelegate, InfoBar, InfoBarPosition


class CustomTableItemDelegate(TableItemDelegate):
    def paint(self, painter, option, index):
        if option.state & QStyle.State_MouseOver:
            option.palette.setColor(QPalette.Highlight, QColor(230, 230, 230))
        super().paint(painter, option, index)


class Video2SRT(QWidget):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.table = TableWindow(self, settings)
        self.util = SecWindow(self)
        self.language_name = config.langnamelist
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()
        self.bind_action()

    def setupUi(self):

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 导入文件
        self.btn_get_video = PushButton("导入音视频文件", self)
        self.btn_get_video.setIcon(FluentIcon.VIDEO)
        self.btn_get_video.setFixedHeight(100)

        main_layout.addWidget(self.btn_get_video)

        # 下拉框布局
        combo_layout = QHBoxLayout()
        main_layout.addLayout(combo_layout)

        # 原始语种布局
        source_layout = QHBoxLayout()
        source_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        source_language_label = BodyLabel("原始语种")
        # source_language_label.setMinimumSize(QSize(0, 35))

        self.source_language = ComboBox()
        self.source_language.setStyleSheet("""
            QComboBox {
                background-color: #3E3E42;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #555555;
                border-left-style: solid;
            }
        """)
        self.source_language.addItems(config.langnamelist)
        # self.source_language.setMinimumSize(QSize(0, 35))
        if config.params['source_language'] and config.params['source_language'] in self.language_name:
            self.source_language.setCurrentText(config.params['source_language'])
        else:
            self.source_language.setCurrentIndex(2)

        source_layout.addWidget(source_language_label)
        source_layout.addWidget(self.source_language)
        combo_layout.addLayout(source_layout)

        # 识别引擎布局

        recognition_layout = QHBoxLayout()
        recognition_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # 识别引擎
        recognition_label = BodyLabel("识别引擎")

        self.source_model = ComboBox()
        model_type = self.settings.value('model_type', type=int)
        config.logger.info(f"获取model_type: {model_type}")
        model_list = config.model_code_list[:4]
        if model_type == 1:
            model_list.extend(config.model_code_list[4:9])
        elif model_type == 2:
            model_list.extend(config.model_code_list[9:14])
        self.source_model.addItems(model_list)
        # sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        # sizePolicy3.setHorizontalStretch(0)
        # sizePolicy3.setVerticalStretch(0)
        # sizePolicy3.setHeightForWidth(self.source_model.sizePolicy().hasHeightForWidth())
        # self.source_model.setSizePolicy(sizePolicy3)
        # self.source_model.setMinimumSize(QSize(0, 35))
        recognition_layout.addWidget(recognition_label)
        recognition_layout.addWidget(self.source_model)
        combo_layout.addLayout(recognition_layout)

        combo_layout.addStretch()
        self.check_fanyi = CheckBox("字幕翻译")
        self.check_fanyi.setMinimumSize(QSize(0, 35))
        combo_layout.addWidget(self.check_fanyi)

        # 翻译语言布局
        translate_language_layout = QHBoxLayout()
        translate_language_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        translate_language_label = BodyLabel("翻译语种")
        self.translate_language = ComboBox()
        self.translate_language.addItems(self.language_name)
        if config.params['target_language'] and config.params['target_language'] in self.language_name:
            self.translate_language.setCurrentText(config.params['target_language'])
        translate_language_layout.addWidget(translate_language_label)
        translate_language_layout.addWidget(self.translate_language)
        combo_layout.addLayout(translate_language_layout)

        # 翻译引擎布局
        translate_engine_layout = QHBoxLayout()
        translate_engine_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 媒体表格卡片
        table_card = CardWidget(self)
        table_layout = QVBoxLayout(table_card)

        self.media_table = TableWidget(self)
        self.media_table.setColumnCount(4)
        self.media_table.setHorizontalHeaderLabels(['文件名', '时长', '算力消耗', '操作'])

        self.media_table.verticalHeader().setVisible(False)  # 隐藏行号

        # 设置表头样式
        header = self.media_table.horizontalHeader()
        # 设置列宽
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 文件名列自适应宽度
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.media_table.setColumnWidth(1, 100)  # 时长列
        self.media_table.setColumnWidth(2, 100)  # 算力消耗列
        self.media_table.setColumnWidth(3, 100)  # 操作列
        self.media_table.setColumnHidden(2, True)  # 隐藏算力消耗列

        self.media_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止编辑

        table_layout.addWidget(self.media_table)
        main_layout.addWidget(table_card)

        # 开始按钮
        self.start_btn = PushButton("开始", self)
        self.start_btn.setIcon(FluentIcon.PLAY)
        self.start_btn.setFixedSize(200, 50)

        main_layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)

    def bind_action(self):
        self.check_fanyi.stateChanged.connect(lambda:print(self.check_fanyi.isChecked()))
        self.start_btn.clicked.connect(self.util.check_start)
        self.act_btn_get_video()

    def act_btn_get_video(self):
        # 选择文件,并显示路径
        self.btn_get_video.clicked.connect(lambda:self.table.select_files(self.media_table))
        self.btn_get_video.setAcceptDrops(True)
        self.btn_get_video.dragEnterEvent = self.table.drag_enter_event
        self.btn_get_video.dropEvent = lambda event:self.table.drop_event(self.media_table, event)

    def add_queue_mp4(self):
        # 获取self.main.media_table中第4列的数据
        srt_list = []
        for i in range(self.media_table.rowCount()):
            # 获取self.media_table第i行第4列的数据
            config.logger.info(self.media_table.item(i, 4).text())
            srt_list.append(self.media_table.item(i, 4).text())
        config.queue_asr.extend(srt_list)
        config.logger.info(f'queue_srt: {config.queue_asr}')




class TableWindow:
    def __init__(self, main, settings):
        self.main = main
        self.settings = settings

    # 列表的操作
    @Slot()
    def select_files(self, ui_table: QTableWidget):
        # 选择文件
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_paths, _ = QFileDialog.getOpenFileNames(self.main, config.transobj['selectmp4'], config.last_opendir,
                                                     "Video files(*.mp4 *.avi *.mov *.mpg *.mkv *.mp3 *.wav *.flac)")

        if file_paths:
            for file_path in file_paths:
                self.add_file_to_table(ui_table, file_path)

            config.last_opendir = os.path.dirname(file_paths[0])
            self.settings.setValue("last_dir", config.last_opendir)

    def add_file_to_table(self, ui_table: TableWidget, file_path: str):
        # 添加文件到表格
        config.logger.info(f'add_file_to_table: {file_path}')
        row_position = ui_table.rowCount()
        file_duration = self.get_video_duration(file_path)  # 获取视频时长
        if file_duration:
            ui_table.insertRow(row_position)
            file_name = os.path.basename(file_path)
            # 文件名
            ui_table.setItem(row_position, 0, QTableWidgetItem(file_name))
            # 时长
            ui_table.setItem(row_position, 1, QTableWidgetItem(file_duration))
            # 算力消耗
            ui_table.setItem(row_position, 2, QTableWidgetItem("未知"))
            # 操作
            delete_button = PushButton("删除")
            delete_button.setFixedSize(QSize(80, 30))
            delete_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
            # todo 修改样式
            delete_button.setStyleSheet("background-color: #FF6C64; color: white;")
            ui_table.setCellWidget(row_position, 3, delete_button)
            delete_button.clicked.connect(lambda row=row_position:self.delete_file(ui_table, row))

            # 文件路径
            ui_table.setItem(row_position, 4, QTableWidgetItem(file_path))
        else:
            InfoBar.error(title='失败', content="文件内容错误，请检查文件内容", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT,
                          duration=2000, parent=self.main)

    @Slot()
    def delete_file(self, ui_table: QTableWidget, row: int):
        # Confirm delete action

        ui_table.removeRow(row)
        # Update the delete buttons' connections
        self.update_delete_buttons(ui_table)

    def update_delete_buttons(self, ui_table: QTableWidget):
        for row in range(ui_table.rowCount()):
            delete_button = ui_table.cellWidget(row, 3)
            delete_button.clicked.disconnect()
            delete_button.clicked.connect(lambda r=row:self.delete_file(ui_table, r))

    def get_video_duration(self, file: str):
        # Use ffprobe to get video duration
        cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{file}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        duration_seconds = float(result.stdout.strip())
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def drag_enter_event(self, event: QDragEnterEvent):
        # 接受拖入
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drop_event(self, ui_table: QTableWidget, event: QDropEvent):
        # 拖出
        file_urls = event.mimeData().urls()
        config.logger.info(f"file_urls: {file_urls}")
        if file_urls:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.add_file_to_table(ui_table, file_path)
        event.accept()

    def clear_table(self, ui_table: QTableWidget):
        # 清空表格
        ui_table.setRowCount(0)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings

    app = QApplication(sys.argv)
    window = Video2SRT('字幕翻译', settings=QSettings("Locoweed", "LinLInTrans"))
    window.show()
    sys.exit(app.exec())
