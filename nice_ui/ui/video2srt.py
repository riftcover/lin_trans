import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import (QCoreApplication, Qt, Slot, QSize, QSettings)
from PySide6.QtGui import (QDragEnterEvent, QDropEvent)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QTableWidget, QVBoxLayout, QWidget, QHeaderView, QApplication)
from PySide6.QtWidgets import (QFileDialog)
from qfluentwidgets import PushButton, FluentIcon

from nice_ui.configure import config
from nice_ui.main_win.secwin import SecWindow
from videotrans.translator import TRANSNAMES


class Video2SRT(QWidget):
    def __init__(self, text: str, parent=None, setting=None):
        super().__init__(parent=parent)
        self.setting = setting
        self.table =TableWindow(self,setting)
        self.util = SecWindow(self)
        self.language_name = config.langnamelist
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()
        self.initUI()



    def setupUi(self):
        main_layout = QVBoxLayout()

        self.btn_get_video = PushButton("导入音视频文件，自动生成字幕")

        self.btn_get_video.setIcon(FluentIcon.VIDEO)
        self.btn_get_video.setFixedHeight(100)  # 增加按钮的高度
        main_layout.addWidget(self.btn_get_video)

        # 下拉框布局
        combo_layout = QHBoxLayout()
        main_layout.addLayout(combo_layout)

        # 原始语种布局
        source_layout = QHBoxLayout()
        source_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        
        source_language_label = QLabel("原始语种")
        # source_language_label.setMinimumSize(QSize(0, 35))


        self.source_language = QComboBox()
        self.source_language.addItems(config.langnamelist)
        # self.source_language.setMinimumSize(QSize(0, 35))

        source_layout.addWidget(source_language_label)
        source_layout.addWidget(self.source_language)
        combo_layout.addLayout(source_layout)

        # 识别引擎布局

        recognition_layout = QHBoxLayout()
        recognition_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        #识别引擎
        recognition_label =QLabel("识别引擎")

        self.source_model = QComboBox()
        self.source_model.addItems(config.model_code_list)
        # sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        # sizePolicy3.setHorizontalStretch(0)
        # sizePolicy3.setVerticalStretch(0)
        # sizePolicy3.setHeightForWidth(self.source_model.sizePolicy().hasHeightForWidth())
        # self.source_model.setSizePolicy(sizePolicy3)
        # self.source_model.setMinimumSize(QSize(0, 35))
        recognition_layout.addWidget(recognition_label)
        recognition_layout.addWidget(self.source_model)
        combo_layout.addLayout(recognition_layout)


        self.check_fanyi = QCheckBox("字幕翻译")
        self.check_fanyi.setObjectName(u"check_fanyi")
        sizePolicy3.setHeightForWidth(self.check_fanyi.sizePolicy().hasHeightForWidth())
        self.check_fanyi.setSizePolicy(sizePolicy3)
        self.check_fanyi.setMinimumSize(QSize(0, 35))

        self.horizontalLayout.addWidget(self.check_fanyi)

        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_8 = QLabel(self.layoutWidget)
        self.label_8.setObjectName(u"label_8")
        sizePolicy2.setHeightForWidth(self.label_8.sizePolicy().hasHeightForWidth())
        self.label_8.setSizePolicy(sizePolicy2)
        self.label_8.setMinimumSize(QSize(0, 35))

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.label_8)

        self.translate_type = QComboBox(self.layoutWidget)
        self.translate_type.setObjectName(u"translate_type")
        sizePolicy3.setHeightForWidth(self.translate_type.sizePolicy().hasHeightForWidth())
        self.translate_type.setSizePolicy(sizePolicy3)
        self.translate_type.setMinimumSize(QSize(0, 35))

        self.formLayout_3.setWidget(0, QFormLayout.FieldRole, self.translate_type)

        self.horizontalLayout.addLayout(self.formLayout_3)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_4 = QLabel(self.layoutWidget)
        self.label_4.setObjectName(u"label_4")
        sizePolicy2.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy2)
        self.label_4.setMinimumSize(QSize(0, 35))

        self.formLayout_4.setWidget(0, QFormLayout.LabelRole, self.label_4)

        self.translate_language = QComboBox(self.layoutWidget)
        self.translate_language.setObjectName(u"translate_language")
        sizePolicy3.setHeightForWidth(self.translate_language.sizePolicy().hasHeightForWidth())
        self.translate_language.setSizePolicy(sizePolicy3)
        self.translate_language.setMinimumSize(QSize(0, 0))

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.translate_language)

        self.horizontalLayout.addLayout(self.formLayout_4)

        main_layout.addLayout(self.horizontalLayout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(80, -1, 80, -1)
        self.media_table = QTableWidget(self.layoutWidget)
        self.media_table.setColumnCount(4)
        self.media_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.media_table.setObjectName(u"media_table")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.media_table.sizePolicy().hasHeightForWidth())
        self.media_table.setSizePolicy(sizePolicy4)
        self.media_table.setMinimumSize(QSize(0, 300))

        self.verticalLayout.addWidget(self.media_table)

        main_layout.addLayout(self.verticalLayout)

        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.formLayout_5.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_5.setContentsMargins(-1, -1, -1, 20)
        self.startbtn_1 = QPushButton(self.layoutWidget)
        self.startbtn_1.setObjectName(u"startbtn_1")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.startbtn_1.sizePolicy().hasHeightForWidth())
        self.startbtn_1.setSizePolicy(sizePolicy5)
        self.startbtn_1.setMinimumSize(QSize(200, 50))

        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.startbtn_1)

        main_layout.addLayout(self.formLayout_5)

        self.setLayout(main_layout)
        self.lateUI()
        self.initUI()
        self.bind_action()
    def initUI(self):
        self.btn_get_video.setCursor(Qt.PointingHandCursor)

        if config.params['source_language'] and config.params['source_language'] in self.language_name:
            self.source_language.setCurrentText(config.params['source_language'])
        else:
            self.source_language.setCurrentIndex(2)

        self.translate_language.addItems(["-"] + self.language_name)

        # 模型下拉菜单内容

        self.translate_type.addItems(TRANSNAMES)
        translate_name = config.params['translate_type'] if config.params['translate_type'] in TRANSNAMES else TRANSNAMES[0]

        self.translate_type.setCurrentText(translate_name)
        if config.params['target_language'] and config.params['target_language'] in self.language_name:
            self.translate_language.setCurrentText(config.params['target_language'])


    def add_queue_mp4(self):
        # 获取self.main.media_table中第4列的数据
        srt_list = []
        for i in range(self.media_table.rowCount()):
            srt_list.append(self.media_table.cellWidget(i, 4).text())
        config.queue_srt.extend(srt_list)
        config.logger.info(f'queue_srt: {config.queue_mp4}')


    def bind_action(self):
        self.check_fanyi.stateChanged.connect(lambda: print(self.check_fanyi.isChecked()))
        self.startbtn_1.clicked.connect(self.util.check_start)
        self.startbtn_1.clicked.connect(lambda: print("开始"))
        self.act_btn_get_video()

    def act_btn_get_video(self):
        # self.table = TableWindow(self)
        # 选择文件,并显示路径
        self.btn_get_video.clicked.connect(lambda:self.table.select_files(self.media_table))
        self.btn_get_video.setAcceptDrops(True)
        self.btn_get_video.dragEnterEvent = self.table.drag_enter_event
        self.btn_get_video.dropEvent = lambda event: self.table.drop_event(self.media_table, event)

    def lateUI(self):
        self.btn_get_video.setText(QCoreApplication.translate("MainWindow", u"导入音视频文件", None))
        source_language_name.setText(QCoreApplication.translate("MainWindow", u" 原始语种", None))
        # if QT_CONFIG(tooltip)
        self.source_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        # endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"识别引擎", None))
        # if QT_CONFIG(tooltip)
        self.source_model.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        self.check_fanyi.setText(QCoreApplication.translate("MainWindow", u"字幕翻译", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"翻译引擎", None))
        # if QT_CONFIG(tooltip)
        self.translate_type.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        # endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"翻译语种", None))
        # if QT_CONFIG(tooltip)
        self.translate_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        # endif // QT_CONFIG(tooltip)
        # ___qtablewidgetitem = self.media_table.horizontalHeaderItem(0)
        # ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"文件名", None))
        # ___qtablewidgetitem1 = self.media_table.horizontalHeaderItem(1)
        # ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"时长", None))
        # ___qtablewidgetitem2 = self.media_table.horizontalHeaderItem(2)
        # ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"算力消耗", None))
        # ___qtablewidgetitem3 = self.media_table.horizontalHeaderItem(3)
        # ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"操作", None))
        self.startbtn_1.setText(QCoreApplication.translate("MainWindow", u"开始", None))


class TableWindow:
    def __init__(self,main,setting):
        self.main = main
        self.setting = setting
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
                file_name = os.path.basename(file_path)
                self.add_file_to_table(ui_table, file_name)

            config.last_opendir = os.path.dirname(file_paths[0])
            self.setting.setValue("last_dir", config.last_opendir)

    def table_set_item(self,ui_table,row_position:int,l0,l1,l2):
        #文件名
        file_name = QLabel()
        file_name.setText(os.path.basename(l0))
        file_name.setAlignment(Qt.AlignCenter)
        ui_table.setCellWidget(row_position, 0, file_name)

        # 时长
        file_duration = QLabel()
        file_duration.setText(l1)
        file_duration.setAlignment(Qt.AlignCenter)
        ui_table.setCellWidget(row_position, 1, file_duration)

        #算力消耗
        locol_value = QLabel()
        locol_value.setText(l2)
        locol_value.setAlignment(Qt.AlignCenter)
        ui_table.setCellWidget(row_position, 2, locol_value)

        #操作
        delete_button = QPushButton("删除")
        delete_button.setStyleSheet("background-color: red; color: white;")  # todo: 调整样式
        ui_table.setCellWidget(row_position, 3, delete_button)
        delete_button.clicked.connect(lambda _, row=row_position: self.delete_file(ui_table, row))

        #文件路径
        file_path = QLabel()
        file_path.setText(l0)
        file_path.setAlignment(Qt.AlignCenter)
        ui_table.setCellWidget(row_position, 4, file_path)

    def add_file_to_table(self, ui_table: QTableWidget, file_path: str):
        # 添加文件到表格

        row_position = ui_table.rowCount()

        ui_table.insertRow(row_position)
        file_duration = "00:00:00"  # todo: 可以使用一个方法来获取实际时长
        # file_duration = self.get_video_duration(file_path)
        self.table_set_item(ui_table, row_position, file_path, file_duration, "0.00")

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
    app = QApplication(sys.argv)
    window = Video2SRT('字幕翻译',setting=QSettings("Locoweed", "LinLInTrans"))
    window.show()
    sys.exit(app.exec())