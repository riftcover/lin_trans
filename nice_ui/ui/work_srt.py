import os
import re

import path
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QTableWidget, QAbstractItemView, QTableWidgetItem, QHeaderView, )

from agent import get_translate_code
from components.widget import DeleteButton, TransComboBox
from nice_ui.configure import config
from nice_ui.main_win.secwin import SecWindow
from orm.queries import PromptsOrm
from utils import logger
from vendor.qfluentwidgets import (PushButton, TableWidget, FluentIcon, InfoBar, InfoBarPosition, BodyLabel, CardWidget, )


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
        self.btn_get_srt = PushButton("选择字幕文件或拖放至此")

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
        source_layout.setSpacing(5)
        source_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        source_language_name = BodyLabel("原始语种")

        self.source_language_combo = TransComboBox(self)
        self.source_language_combo.setFixedWidth(98)
        self.source_language_combo.addItems(self.language_name)
        if (
            config.params["source_language"]
            and config.params["source_language"] in self.language_name
        ):
            self.source_language_combo.setCurrentText(config.params["source_language"])
        else:
            self.source_language_combo.setCurrentIndex(2)
        source_layout.addWidget(source_language_name)
        source_layout.addWidget(self.source_language_combo)
        combo_layout.addLayout(source_layout)

        # 翻译语种布局
        translate_layout = QHBoxLayout()
        translate_layout.setSpacing(5)
        translate_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        translate_language_name = BodyLabel("翻译语种")

        self.translate_language_combo = TransComboBox(self)
        self.translate_language_combo.setFixedWidth(117)
        self.translate_language_combo.addItems(self.language_name)
        if (
            config.params["target_language"]
            and config.params["target_language"] in self.language_name
        ):
            self.translate_language_combo.setCurrentText(
                config.params["target_language"]
            )

        translate_layout.addWidget(translate_language_name)
        translate_layout.addWidget(self.translate_language_combo)
        combo_layout.addLayout(translate_layout)

        # 翻译引擎布局
        engine_layout = QHBoxLayout()
        engine_layout.setSpacing(5)
        engine_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        translate_model_name = BodyLabel("翻译引擎")

        self.translate_model = TransComboBox(self)
        self.translate_model.setFixedWidth(117)
        # todo: 翻译引擎列表需调整
        translate_list = get_translate_code()
        self.translate_model.addItems(translate_list)
        translate_name = config.params["translate_channel"]
        logger.info(f"translate_name: {translate_name}")
        self.translate_model.setCurrentText(translate_name)

        engine_layout.addWidget(translate_model_name)
        engine_layout.addWidget(self.translate_model)
        combo_layout.addLayout(engine_layout)

        # todo: 只有选择ai时才显示
        prompt_layout = QHBoxLayout()
        prompt_layout.setSpacing(5)
        prompt_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        ai_prompt_name = BodyLabel("提示词")
        self.ai_prompt = TransComboBox(self)
        self.ai_prompt.setFixedWidth(98)
        self.ai_prompt.addItems(self._get_ai_prompt())
        self.ai_prompt.setCurrentText(config.params["prompt_name"])
        prompt_layout.addWidget(ai_prompt_name)
        prompt_layout.addWidget(self.ai_prompt)
        main_layout.addLayout(prompt_layout)

        # 媒体表格卡片
        table_card = CardWidget(self)
        table_layout = QVBoxLayout(table_card)

        self.media_table = TableWidget(self)
        self.media_table.setColumnCount(5)
        self.media_table.setHorizontalHeaderLabels(
            ["文件名", "字符数", "算力消耗", "操作", "文件路径"]
        )

        self.media_table.verticalHeader().setVisible(False)  # 隐藏行号
        # 设置表头样式
        header = self.media_table.horizontalHeader()
        header.setStyleSheet(
            """
            QHeaderView::section {
                background-color: white;
                border: none;
                border-bottom: 1px solid #E0E0E0;
                padding: 4px;
            }
        """
        )
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 文件名列自适应宽度
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.media_table.setColumnWidth(0, 400)
        self.media_table.setColumnWidth(1, 100)
        self.media_table.setColumnWidth(2, 100)
        self.media_table.setColumnWidth(3, 100)
        self.media_table.setColumnWidth(4, 100)
        # self.media_table.setColumnHidden(2, True)  # 隐藏算力消耗列
        self.media_table.setColumnHidden(4, True)  # 隐藏文件路径列
        self.media_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止编辑

        table_layout.addWidget(self.media_table)
        main_layout.addWidget(table_card)

        # 开始按钮
        self.start_btn = PushButton("开始", self)
        self.start_btn.setIcon(FluentIcon.PLAY)
        self.start_btn.setFixedSize(200, 50)

        main_layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)

    def bind_action(self):
        # 选择文件,并显示路径
        self.btn_get_srt.clicked.connect(
            lambda: self.table.select_files(self.media_table)
        )

        # 设置拖放功能
        self.btn_get_srt.setAcceptDrops(True)
        self.btn_get_srt.dragEnterEvent = self.table.drag_enter_event
        self.btn_get_srt.dropEvent = lambda event: self.table.drop_event(
            self.media_table, event
        )

        self.start_btn.clicked.connect(self.on_start_clicked)

    def on_start_clicked(self):
        # 显示成功提示
        InfoBar.success(
            title="成功",
            content="任务已添加，在我的创作中查看结果",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self,
        )

        self.util.check_translate()

    def add_queue_srt(self):
        srt_list = [
            self.media_table.item(i, 4).text()
            for i in range(self.media_table.rowCount())
        ]
        config.queue_trans.extend(srt_list)
        logger.info(f"queue_srt: {config.queue_trans}")

    def _get_ai_prompt(self) -> list:
        # 获取AI提示列表
        prompt_names = self.prompts_orm.get_prompt_name()
        return [i.prompt_name for i in prompt_names]


class LTableWindow:
    def __init__(self, main, settings):
        self.main = main
        self.settings = settings

    # 列表的操作
    @Slot()
    def select_files(self, ui_table: QTableWidget):
        # 选择文件
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.main,
            config.transobj["selectsrt"],
            config.last_opendir,
            "Srt files(*.srt)",
        )

        if file_paths:
            for file_path in file_paths:
                self.add_file_to_table(ui_table, file_path)

            config.last_opendir = os.path.dirname(file_paths[0])
            self.settings.setValue("last_dir", config.last_opendir)

    def add_file_to_table(self, ui_table: TableWidget, file_path: str):
        # 添加文件到表格
        logger.info(f"add_file_to_table: {file_path}")
        row_position = ui_table.rowCount()
        if file_character_count := self.get_file_character_count(file_path):
            ui_table.insertRow(row_position)
            file_name = os.path.basename(file_path)
            logger.info(f"file_name type: {type(file_name)}")
            logger.info(f"file_name: {file_name}")
            logger.info(f"file_character_count: {file_character_count}")
            logger.info(f"file_path: {file_path}")
            # 文件名
            ui_table.setItem(row_position, 0, QTableWidgetItem(file_name))
            # 字符数
            ui_table.setItem(
                row_position, 1, QTableWidgetItem(str(file_character_count))
            )
            # 算力消耗
            ui_table.setItem(row_position, 2, QTableWidgetItem("未知"))
            # 操作
            delete_button = DeleteButton("删除")
            ui_table.setCellWidget(row_position, 3, delete_button)
            delete_button.clicked.connect(
                lambda row=row_position: self.delete_file(ui_table, row)
            )
            # 文件路径
            ui_table.setItem(row_position, 4, QTableWidgetItem(file_path))
        else:
            InfoBar.error(
                title="失败",
                content="文件内容错误，请检查文件内容",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self.main,
            )

    # 获取文件字符数
    def get_file_character_count(self, file_path: path) -> int | bool:
        # 输入srt格式的文件，获取里面的字符数量，不计算序号，不计算时间戳
        character_count = 0
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                lines = f.readlines()
            except UnicodeDecodeError:
                logger.error(f"文件{file_path}编码错误，请检查文件编码格式")
                return False
            for line in lines:
                # 跳过序号和时间戳
                if re.match(r"^\d+$", line.strip()) or re.match(
                    r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$",
                    line.strip(),
                ):
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
            delete_button.clicked.connect(lambda r=row: self.delete_file(ui_table, r))

    def drag_enter_event(self, event: QDragEnterEvent):
        # 接受拖入
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drop_event(self, ui_table: QTableWidget, event: QDropEvent):
        # 拖出
        file_urls = event.mimeData().urls()
        logger.info(f"file_urls: {file_urls}")
        if file_urls:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.add_file_to_table(ui_table, file_path)
        event.accept()

    def clear_table(self, ui_table: QTableWidget):
        # 清空表格
        ui_table.setRowCount(0)