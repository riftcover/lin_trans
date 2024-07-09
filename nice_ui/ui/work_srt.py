import sys

from PySide6.QtCore import Qt, QRect
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QTableWidgetItem, QLabel, \
    QHeaderView
from qfluentwidgets import (PushButton, ComboBox, TableWidget, FluentIcon, MessageBox)

from nice_ui.configure import config
from nice_ui.main_win.secwin import SecWindow
from nice_ui.ui.video2srt import TableWindow
from videotrans.translator import TRANSNAMES


class WorkSrt(QWidget):
    def __init__(self, text: str, parent=None,setting=None):
        super().__init__(parent=parent)
        self.setting = setting
        self.table = TableWindow(self,setting)
        self.util = SecWindow(self)
        self.language_name = config.langnamelist
        self.setObjectName(text.replace(' ', '-'))
        self.setup_ui()
        self.bind_action()
    def setup_ui(self):
        self.setWindowTitle('字幕翻译准备')
        self.setGeometry(QRect(12, 16, 777, 578))

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 文件选择按钮
        self.btn_get_srt = PushButton('选择字幕文件', self)
        self.btn_get_srt.setIcon(FluentIcon.FOLDER)

        main_layout.addWidget(self.btn_get_srt)

        # 下拉框布局
        combo_layout = QHBoxLayout()
        main_layout.addLayout(combo_layout)


        # 原始语种布局
        source_layout = QHBoxLayout()
        source_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        source_language_name = QLabel('原始语种')

        self.source_language_combo = ComboBox(self)
        self.source_language_combo.addItems(self.language_name)
        if config.params['source_language'] and config.params['source_language'] in self.language_name:
            self.source_language_combo.setCurrentText(config.params['source_language'])
        else:
            self.source_language_combo.setCurrentIndex(2)
        source_layout.addWidget(source_language_name)
        source_layout.addWidget(self.source_language_combo)
        combo_layout.addLayout(source_layout)

        # 翻译语种布局
        translate_layout = QHBoxLayout()
        translate_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        translate_language_name = QLabel('翻译语种')

        self.translate_language_combo = ComboBox(self)
        self.translate_language_combo.addItems(self.language_name)
        if config.params['target_language'] and config.params['target_language'] in self.language_name:
            self.translate_language_combo.setCurrentText(config.params['target_language'])

        translate_layout.addWidget(translate_language_name)
        translate_layout.addWidget(self.translate_language_combo)
        combo_layout.addLayout(translate_layout)

        # 翻译引擎布局
        engine_layout = QHBoxLayout()
        engine_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        translate_model_name = QLabel('翻译引擎')

        self.translate_model = ComboBox(self)
        self.translate_model.addItems(TRANSNAMES)
        translate_name = config.params['translate_type'] if config.params['translate_type'] in TRANSNAMES else TRANSNAMES[0]

        self.translate_model.setCurrentText(translate_name)

        engine_layout.addWidget(translate_model_name)
        engine_layout.addWidget(self.translate_model)
        combo_layout.addLayout(engine_layout)


        # 表格
        self.media_table = TableWidget(self)
        self.media_table.setColumnCount(4)
        self.media_table.setHorizontalHeaderLabels(['文件名', '字符数', '算力消耗', '操作'])
        self.media_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.media_table)

        # 开始按钮
        self.start_button = PushButton('开始翻译', self)
        self.start_button.setIcon(FluentIcon.PLAY)

        main_layout.addWidget(self.start_button)

        # 设置接受拖放
        self.setAcceptDrops(True)
    def bind_action(self):
        self.btn_get_srt.clicked.connect(self.select_file)
        self.start_button.clicked.connect(self.start_translation)


    def select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Subtitle files (*.srt *.ass *.vtt)")
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            self.add_files_to_table(files)

    def add_files_to_table(self, files):
        for file in files:
            row_position = self.media_table.rowCount()
            self.media_table.insertRow(row_position)
            self.media_table.setItem(row_position, 0, QTableWidgetItem(file))
            self.media_table.setItem(row_position, 1, QTableWidgetItem('计算中...'))
            self.media_table.setItem(row_position, 2, QTableWidgetItem('计算中...'))
            delete_button = PushButton('删除')
            delete_button.clicked.connect(lambda _, r=row_position: self.media_table.removeRow(r))
            self.media_table.setCellWidget(row_position, 3, delete_button)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.add_files_to_table(files)

    def start_translation(self):
        MessageBox('提示', '翻译准备完成，即将开始翻译...', self).exec()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WorkSrt('字幕翻译')
    window.show()
    sys.exit(app.exec())
