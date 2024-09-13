import os
import re
import sys

import path
from PySide6.QtCore import Qt, Slot, QSettings, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QTableWidget, QApplication, QAbstractItemView, QTableWidgetItem, QSizePolicy,
                               QFormLayout, )

from agent import get_translate_code
from nice_ui.configure import config
from nice_ui.main_win.secwin import SecWindow
from orm.queries import PromptsOrm
from vendor.qfluentwidgets import PushButton, TableWidget, FluentIcon, InfoBar, InfoBarPosition, ComboBox, BodyLabel


class WorkSrt(QWidget):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.prompts_orm = PromptsOrm()
        self.table = LTableWindow(self, settings)
        self.util = SecWindow(self)
        self.language_name = config.langnamelist
        self.setObjectName(text.replace(" ", "-"))
        self.setup_ui()
        self.bind_action()

    def setup_ui(self):

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 文件选择按钮
        self.btn_get_srt = PushButton("拖拽拖拽文件到页面，选择字幕文件")
        self.btn_get_srt.setIcon(FluentIcon.FOLDER)
        self.btn_get_srt.setFixedHeight(100)  # 增加按钮的高度
        main_layout.addWidget(self.btn_get_srt)

        # self.add_queue_btn = PushButton("添加到队列")
        # main_layout.addWidget(self.add_queue_btn)

        # 下拉框布局
        combo_layout = QHBoxLayout()
        main_layout.addLayout(combo_layout)

        # 原始语种布局
        source_layout = QHBoxLayout()
        source_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        source_language_name = BodyLabel("原始语种")

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
        translate_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        translate_language_name = BodyLabel("翻译语种")

        self.translate_language_combo = ComboBox(self)
        self.translate_language_combo.addItems(self.language_name)
        if config.params['target_language'] and config.params['target_language'] in self.language_name:
            self.translate_language_combo.setCurrentText(config.params['target_language'])

        translate_layout.addWidget(translate_language_name)
        translate_layout.addWidget(self.translate_language_combo)
        combo_layout.addLayout(translate_layout)

        # 翻译引擎布局
        engine_layout = QHBoxLayout()
        engine_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        translate_model_name = BodyLabel("翻译引擎")

        self.translate_model = ComboBox(self)
        # todo: 翻译引擎列表需调整
        translate_list = get_translate_code()
        self.translate_model.addItems(translate_list)
        translate_name = config.params["translate_type"]
        config.logger.info(f"translate_name: {translate_name}")
        self.translate_model.setCurrentText(translate_name)

        engine_layout.addWidget(translate_model_name)
        engine_layout.addWidget(self.translate_model)
        combo_layout.addLayout(engine_layout)

        # todo: 只有选择ai时才显示
        prompt_layout = QHBoxLayout()
        prompt_layout.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        ai_prompt_name = BodyLabel("提示词")
        self.ai_prompt = ComboBox(self)
        self.ai_prompt.addItems(self._get_ai_prompt())
        self.ai_prompt.setCurrentText(config.params["prompt_name"])
        prompt_layout.addWidget(ai_prompt_name)
        prompt_layout.addWidget(self.ai_prompt)
        main_layout.addLayout(prompt_layout)

        # 表格
        media_table_layout = QHBoxLayout()
        media_table_layout.setContentsMargins(60, -1, 60, -1)
        self.media_table = TableWidget(self)
        self.media_table.setColumnCount(5)
        self.media_table.setHorizontalHeaderLabels(['文件名', '字符数', '算力消耗', '操作', '文件路径'])
        self.media_table.setColumnWidth(0, 400)
        self.media_table.setColumnWidth(1, 100)
        self.media_table.setColumnWidth(2, 100)
        self.media_table.setColumnWidth(3, 100)
        self.media_table.setColumnWidth(4, 100)
        # self.media_table.setShowGrid(False) #隐藏网格线
        self.media_table.setColumnHidden(2, True)  # 隐藏操作列
        self.media_table.setColumnHidden(4, True)  # 隐藏操作列
        self.media_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        media_table_layout.addWidget(self.media_table)
        main_layout.addLayout(media_table_layout)

        # 开始按钮
        self.formLayout_5 = QFormLayout()
        self.formLayout_5.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formLayout_5.setContentsMargins(-1, -1, -1, 20)
        self.start_button = PushButton("开始", self)
        self.start_button.setIcon(FluentIcon.PLAY)

        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.start_button.sizePolicy().hasHeightForWidth())
        self.start_button.setSizePolicy(sizePolicy5)
        self.start_button.setMinimumSize(QSize(200, 50))
        self.formLayout_5.setWidget(0, QFormLayout.LabelRole, self.start_button)

        main_layout.addLayout(self.formLayout_5)

        # # 设置接受拖放  # self.setAcceptDrops(True) #不知道为啥不好使了

    def bind_action(self):

        # 选择文件,并显示路径
        self.btn_get_srt.clicked.connect(self.table.select_file)
        self.btn_get_srt.setAcceptDrops(True)
        self.btn_get_srt.dragEnterEvent = self.table.drag_enter_event
        self.btn_get_srt.dropEvent = lambda event:self.table.drop_event(self.media_table, event)
        # self.add_queue_btn.clicked.connect(self.add_queue_srt)
        self.start_button.clicked.connect(self.util.check_translate)

    def add_queue_srt(self):
        # 获取self.main.media_table中第4列的数据
        srt_list = []
        for i in range(self.media_table.rowCount()):
            srt_list.append(self.media_table.item(i, 4).text())
        config.queue_trans.extend(srt_list)
        config.logger.info(f"queue_srt: {config.queue_trans}")

    def _get_ai_prompt(self) -> list:
        # 获取AI提示列表
        prompt_names = self.prompts_orm.get_prompt_name()
        prompt_name_list = []
        for i in prompt_names:
            prompt_name_list.append(i.prompt_name)
        return prompt_name_list


class LTableWindow:
    def __init__(self, main, settings):
        self.main = main
        self.settings = settings

    def select_file(self):
        file_paths = QFileDialog()
        file_paths.setFileMode(QFileDialog.ExistingFiles)
        file_paths.setNameFilter("Subtitle files (*.srt)")
        # file_paths.setNameFilter("Subtitle files (*.srt *.ass *.vtt)")
        file_paths, _ = QFileDialog.getOpenFileNames(self.main, config.transobj['selectsrt'], config.last_opendir, "Srt files(*.srt)")

        if file_paths:
            for file_path in file_paths:
                self.add_file_to_table(self.main.media_table, file_path)
        config.last_opendir = os.path.dirname(file_paths[0])
        self.settings.setValue("last_dir", config.last_opendir)

    # 列表的操作

    def add_file_to_table(self, ui_table: TableWidget, file_path: str):
        # 添加文件到表格
        row_position = ui_table.rowCount()
        file_character_count = self.get_file_character_count(file_path)
        if file_character_count:
            ui_table.insertRow(row_position)
            file_name = os.path.basename(file_path)
            config.logger.info(f"file_name type: {type(file_name)}")
            config.logger.info(f"file_name: {file_name}")
            config.logger.info(f"file_character_count: {file_character_count}")
            config.logger.info(f"file_path: {file_path}")
            # todo: 算力消耗
            # 文件名
            ui_table.setItem(row_position, 0, QTableWidgetItem(file_name))
            # 字符数
            ui_table.setItem(row_position, 1, QTableWidgetItem(str(file_character_count)))
            # 算力消耗
            ui_table.setItem(row_position, 2, QTableWidgetItem("未知"))
            # 操作
            delete_button = PushButton("删除")
            delete_button.setFixedSize(QSize(80, 30))
            delete_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed

            delete_button.setStyleSheet("background-color: #FF6C64; color: white;")
            ui_table.setCellWidget(row_position, 3, delete_button)
            delete_button.clicked.connect(lambda row=row_position:self.delete_file(ui_table, row))
            # 文件路径
            ui_table.setItem(row_position, 4, QTableWidgetItem(file_path))
        else:
            InfoBar.error(title='失败', content="文件内容错误，请检查文件内容", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT,
                          duration=2000, parent=self.main)

    # 获取文件字符数
    def get_file_character_count(self, file_path: path) -> int | bool:
        # 输入srt格式的文件，获取里面的字符数量，不计算序号，不计算时间戳
        character_count = 0
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                lines = f.readlines()
            except UnicodeDecodeError:
                config.logger.error(f"文件{file_path}编码错误，请检查文件编码格式")
                return False
            for line in lines:
                # 跳过序号和时间戳
                if re.match(r"^\d+$", line.strip()) or re.match(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$", line.strip(), ):
                    continue
                character_count += len(line.strip())
        return character_count

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
    app = QApplication(sys.argv)
    window = WorkSrt("字幕翻译", setting=QSettings("Locoweed", "LinLInTrans"))
    window.show()
    sys.exit(app.exec())
