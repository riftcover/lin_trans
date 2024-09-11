import os
import subprocess
from pathlib import Path

from PySide6.QtCore import (Qt, Slot, QSize)
from PySide6.QtGui import (QDragEnterEvent, QDropEvent)
from PySide6.QtWidgets import (QFileDialog, QFormLayout, QHBoxLayout, QSizePolicy, QTableWidget, QVBoxLayout, QWidget, QAbstractItemView, QTableWidgetItem)

from nice_ui.configure import config
from nice_ui.main_win.secwin import SecWindow
from vendor.qfluentwidgets import PushButton, FluentIcon, TableWidget, ComboBox, CheckBox, BodyLabel
from videotrans.translator import TRANSNAMES


class Video2SRT(QWidget):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.table = TableWindow(self, settings)
        self.util = SecWindow(self)
        self.language_name = config.langnamelist
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()

    def setupUi(self):
        main_layout = QVBoxLayout()

        self.btn_get_video = PushButton("导入音视频文件，自动生成字幕")
        self.btn_get_video.setCursor(Qt.PointingHandCursor)
        self.btn_get_video.setIcon(FluentIcon.VIDEO)
        self.btn_get_video.setFixedHeight(100)  # 增加按钮的高度
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

        translate_model_label = BodyLabel("翻译引擎")

        self.translate_type = ComboBox()
        # todo: 翻译引擎列表需调整
        # 模型下拉菜单内容
        self.translate_type.addItems(TRANSNAMES)
        # 模型默认值
        translate_name = config.params['translate_type'] if config.params['translate_type'] in TRANSNAMES else TRANSNAMES[0]
        self.translate_type.setCurrentText(translate_name)
        translate_engine_layout.addWidget(translate_model_label)
        translate_engine_layout.addWidget(self.translate_type)
        combo_layout.addLayout(translate_engine_layout)

        media_table_layout = QVBoxLayout()
        media_table_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        media_table_layout.setContentsMargins(60, -1, 60, -1)
        self.media_table = TableWidget(self)
        self.media_table.setColumnCount(5)
        self.media_table.setHorizontalHeaderLabels(['文件名', '时长', '算力消耗', '操作', '文件路径'])

        self.media_table.verticalHeader().setVisible(False) #隐藏行头

        self.media_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.media_table.setColumnWidth(0, 400)
        self.media_table.setColumnWidth(1, 100)
        self.media_table.setColumnWidth(2, 100)
        self.media_table.setColumnWidth(3, 100)
        self.media_table.setColumnWidth(4, 0)

        # self.media_table.setShowGrid(False) #隐藏网格线
        self.media_table.setColumnHidden(2, True)  # 隐藏操作列
        self.media_table.setColumnHidden(4, True)  # 隐藏操作列
        # self.media_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.media_table.setObjectName(u"media_table")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.media_table.sizePolicy().hasHeightForWidth())
        self.media_table.setSizePolicy(sizePolicy4)
        self.media_table.setMinimumSize(QSize(0, 300))
        media_table_layout.addWidget(self.media_table)
        main_layout.addLayout(media_table_layout)

        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_5.setContentsMargins(-1, -1, -1, 20)
        self.startbtn_1 = PushButton("开始")
        self.startbtn_1.setIcon(FluentIcon.PLAY)
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.startbtn_1.sizePolicy().hasHeightForWidth())
        self.startbtn_1.setSizePolicy(sizePolicy5)
        self.startbtn_1.setMinimumSize(QSize(200, 50))

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.startbtn_1)

        main_layout.addLayout(self.formLayout_5)

        self.setLayout(main_layout)
        self.bind_action()

    def add_queue_mp4(self):
        # 获取self.main.media_table中第4列的数据
        srt_list = []
        for i in range(self.media_table.rowCount()):
            # 获取self.media_table第i行第4列的数据
            config.logger.info(self.media_table.item(i, 4).text())
            srt_list.append(self.media_table.item(i, 4).text())
        config.queue_mp4.extend(srt_list)
        config.logger.info(f'queue_srt: {config.queue_mp4}')

    def bind_action(self):
        self.check_fanyi.stateChanged.connect(lambda: print(self.check_fanyi.isChecked()))
        self.startbtn_1.clicked.connect(self.util.check_start)
        self.act_btn_get_video()

    def act_btn_get_video(self):
        # self.table = TableWindow(self)
        # 选择文件,并显示路径
        self.btn_get_video.clicked.connect(lambda: self.table.select_files(self.media_table))
        self.btn_get_video.setAcceptDrops(True)
        self.btn_get_video.dragEnterEvent = self.table.drag_enter_event
        self.btn_get_video.dropEvent = lambda event: self.table.drop_event(self.media_table, event)

    # def lateUI(self):  #     self.btn_get_video.setText(QCoreApplication.translate("MainWindow", u"导入音视频文件", None))  #     source_language_name.setText(QCoreApplication.translate("MainWindow", u" 原始语种", None))  #     # if QT_CONFIG(tooltip)  #     self.source_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))  #     # endif // QT_CONFIG(tooltip)  #     self.label_3.setText(QCoreApplication.translate("MainWindow", u"识别引擎", None))  #     # if QT_CONFIG(tooltip)  #     self.source_model.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))  #     self.check_fanyi.setText(QCoreApplication.translate("MainWindow", u"字幕翻译", None))  #     self.translate_model.setText(QCoreApplication.translate("MainWindow", u"翻译引擎", None))  #     # if QT_CONFIG(tooltip)  #     self.translate_type.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))  #     # endif // QT_CONFIG(tooltip)  #     self.label_4.setText(QCoreApplication.translate("MainWindow", u"翻译语种", None))  #     # if QT_CONFIG(tooltip)  #     self.translate_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))


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
        file_paths, _ = QFileDialog.getOpenFileNames(self.main, config.transobj['selectmp4'], config.last_opendir, "Video files(*.mp4 *.avi *.mov *.mpg *.mkv *.mp3 *.wav *.flac)")

        if file_paths:
            for file_path in file_paths:
                self.add_file_to_table(ui_table, file_path)

            config.last_opendir = os.path.dirname(file_paths[0])
            self.settings.setValue("last_dir", config.last_opendir)

    def add_file_to_table(self, ui_table: QTableWidget, file_path: Path):
        # 添加文件到表格
        config.logger.info(f'add_file_to_table: {file_path}')
        row_position = ui_table.rowCount()

        ui_table.insertRow(row_position)
        file_duration = self.get_video_duration(file_path)
        # self.table_set_item(ui_table, row_position, file_path, file_duration, "0.00")
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
        config.logger.info(delete_button.size())
        config.logger.info(f"Row height of row {row_position}: {ui_table.rowHeight(row_position)}")

        delete_button.setStyleSheet("background-color: #FF6C64; color: white;")
        ui_table.setCellWidget(row_position, 3, delete_button)
        delete_button.clicked.connect(lambda _, row=row_position: self.delete_file(ui_table, row))

        # 文件路径
        ui_table.setItem(row_position, 4, QTableWidgetItem(file_path))


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
            delete_button.clicked.connect(lambda _, r=row: self.delete_file(ui_table, r))

    def get_video_duration(self, file: Path):
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
        config.logger.info(f'file_urls: {file_urls}')
        if file_urls:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.add_file_to_table(ui_table, file_path)
        event.accept()

    def clear_table(self, ui_table: QTableWidget):
        # 清空表格
        ui_table.setRowCount(0)


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings
    app = QApplication(sys.argv)
    window = Video2SRT('字幕翻译', settings=QSettings("Locoweed", "LinLInTrans"))
    window.show()
    sys.exit(app.exec())
    # a =TableWindow(None, None)
    # print(a.get_video_duration(r'F:\pm_data\2\1.需求\1.需求挖掘与分析\1.如何获取需求.mp4'))