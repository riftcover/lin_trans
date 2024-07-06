import os
import subprocess
from pathlib import Path

from PySide6.QtCore import (QCoreApplication, QRect,Qt, Slot,
                            QSize)
from PySide6.QtGui import (QDragEnterEvent, QDropEvent)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout,
                               QHBoxLayout, QLabel, QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)
from PySide6.QtWidgets import (QFileDialog)

from nice_ui.configure import config
from videotrans.mainwin.secwin import SecWindow
from videotrans.translator import TRANSNAMES


class Video2SRT(QWidget):
    def __init__(self, text: str, parent=None, setting=None):
        super().__init__(parent=parent)
        self.setting = setting
        self.table =TableWindow(self,setting)
        self.util = SecWindow(self)
        self.languagename = config.langnamelist
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()
        self.initUI()



    def setupUi(self):
        self.layoutWidget = QWidget(self)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(12, 16, 777, 578))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.btn_get_video = QPushButton(self.layoutWidget)
        self.btn_get_video.setObjectName(u"btn_get_video")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_get_video.sizePolicy().hasHeightForWidth())
        self.btn_get_video.setSizePolicy(sizePolicy1)
        self.btn_get_video.setMinimumSize(QSize(300, 150))

        self.verticalLayout_4.addWidget(self.btn_get_video)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_2 = QLabel(self.layoutWidget)
        self.label_2.setObjectName(u"label_2")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)
        self.label_2.setMinimumSize(QSize(0, 35))

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label_2)

        self.source_language = QComboBox(self.layoutWidget)
        self.source_language.setObjectName(u"source_language")
        sizePolicy1.setHeightForWidth(self.source_language.sizePolicy().hasHeightForWidth())
        self.source_language.setSizePolicy(sizePolicy1)
        self.source_language.setMinimumSize(QSize(0, 35))

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.source_language)

        self.horizontalLayout.addLayout(self.formLayout)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_3 = QLabel(self.layoutWidget)
        self.label_3.setObjectName(u"label_3")
        sizePolicy2.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy2)
        self.label_3.setMinimumSize(QSize(0, 35))

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.label_3)

        self.source_model = QComboBox(self.layoutWidget)
        self.source_model.setObjectName(u"source_model")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.source_model.sizePolicy().hasHeightForWidth())
        self.source_model.setSizePolicy(sizePolicy3)
        self.source_model.setMinimumSize(QSize(0, 35))

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.source_model)

        self.horizontalLayout.addLayout(self.formLayout_2)

        self.check_fanyi = QCheckBox(self.layoutWidget)
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

        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(80, -1, 80, -1)
        self.media_table = QTableWidget(self.layoutWidget)
        if (self.media_table.columnCount() < 4):
            self.media_table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.media_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.media_table.setObjectName(u"media_table")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.media_table.sizePolicy().hasHeightForWidth())
        self.media_table.setSizePolicy(sizePolicy4)
        self.media_table.setMinimumSize(QSize(0, 300))

        self.verticalLayout.addWidget(self.media_table)

        self.verticalLayout_4.addLayout(self.verticalLayout)

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

        self.verticalLayout_4.addLayout(self.formLayout_5)
        self.lateUI()
        self.initUI()
        self.bind_action()
    def initUI(self):
        self.btn_get_video.setCursor(Qt.PointingHandCursor)
        self.source_language.addItems(config.langnamelist)
        if config.params['source_language'] and config.params['source_language'] in self.languagename:
            self.source_language.setCurrentText(config.params['source_language'])
        else:
            self.source_language.setCurrentIndex(2)

        self.translate_language.addItems(["-"] + self.languagename)

        # 模型下拉菜单内容
        self.source_model.addItems(config.model_code_list)
        self.translate_type.addItems(TRANSNAMES)
        translate_name = config.params['translate_type'] if config.params['translate_type'] in TRANSNAMES else TRANSNAMES[0]

        self.translate_type.setCurrentText(translate_name)
        if config.params['target_language'] and config.params['target_language'] in self.languagename:
            self.translate_language.setCurrentText(config.params['target_language'])


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
        self.label_2.setText(QCoreApplication.translate("MainWindow", u" 原始语种", None))
        # if QT_CONFIG(tooltip)
        self.source_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        # endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"识别引擎", None))
        # if QT_CONFIG(tooltip)
        self.source_model.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        # endif // QT_CONFIG(tooltip)
        # if QT_CONFIG(tooltip)
        self.check_fanyi.setToolTip(QCoreApplication.translate("MainWindow", u"必须确定有NVIDIA显卡且正确配置了CUDA环境，否则勿选", None))
        # endif // QT_CONFIG(tooltip)
        self.check_fanyi.setText(QCoreApplication.translate("MainWindow", u"字幕翻译", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"翻译引擎", None))
        # if QT_CONFIG(tooltip)
        self.translate_type.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        # endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"翻译语种", None))
        # if QT_CONFIG(tooltip)
        self.translate_language.setToolTip(QCoreApplication.translate("MainWindow", u"原视频发音所用语言", None))
        # endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem = self.media_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"文件名", None))
        ___qtablewidgetitem1 = self.media_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"时长", None))
        ___qtablewidgetitem2 = self.media_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"算力消耗", None))
        ___qtablewidgetitem3 = self.media_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"操作", None))
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
                                                     "Video files(*.mp4 *.avi *.mov *.mpg *.mkv)")

        if file_paths:
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                self.add_file_to_table(ui_table, file_name)
            config.last_opendir = os.path.dirname(file_paths[0])
            self.setting.setValue("last_dir", config.last_opendir)
            config.queue_mp4.extend(file_paths)

    def add_file_to_table(self, ui_table: QTableWidget, file_name: str):
        # 添加文件到表格

        row_position = ui_table.rowCount()

        ui_table.insertRow(row_position)
        file_duration = "00:00:00"  # todo: 可以使用一个方法来获取实际时长
        # file_duration = self.get_video_duration(file_path)
        delete_button = QPushButton("删除")
        delete_button.setStyleSheet("background-color: red; color: white;")  # todo: 调整样式
        ui_table.setItem(row_position, 0, QTableWidgetItem(file_name))
        ui_table.setItem(row_position, 1, QTableWidgetItem(file_duration))
        ui_table.setItem(row_position, 2, QTableWidgetItem("未知"))
        ui_table.setCellWidget(row_position, 3, delete_button)

        delete_button.clicked.connect(lambda _, row=row_position: self.delete_file(ui_table, row))

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
        file_paths = []
        if file_urls:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                file_paths.append(file_path)
                config.logger.info(f'file_path: {file_path}')
                file_name = os.path.basename(file_path)
                config.logger.info(f'file_name: {file_name}')
                self.add_file_to_table(ui_table, file_name)
            config.queue_mp4.extend(file_paths)
        event.accept()
        # ui_table.setText("\n".join(self.file_paths))

    def clearTable(self, ui_table: QTableWidget):
        # 清空表格
        ui_table.setRowCount(0)