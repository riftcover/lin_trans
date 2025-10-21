from pathlib import Path

import av
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QColor, QPalette
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QTableWidget, QVBoxLayout, QWidget, QAbstractItemView, QTableWidgetItem, QHeaderView, QStyle, )

from agent import get_translate_code, translate_api_name
from components.widget import DeleteButton, SearchableComboBox, TransComboBox
from nice_ui.configure import config
from nice_ui.main_win.secwin import SecWindow
from nice_ui.services.service_provider import ServiceProvider
from nice_ui.ui import LANGUAGE_WIDTH
from nice_ui.util.code_tools import language_code
from nice_ui.util.tools import start_tools
from nice_ui.util.token_calculator import calculate_video_duration, format_duration, calculate_asr_tokens
from orm.queries import PromptsOrm
from utils import logger
from utils.agent_dict import agent_settings
from vendor.qfluentwidgets import (PushButton, FluentIcon, TableWidget, CheckBox, BodyLabel, CardWidget, TableItemDelegate, InfoBar, InfoBarPosition, )


class CustomTableItemDelegate(TableItemDelegate):
    def paint(self, painter, option, index):
        if option.state & QStyle.State_MouseOver:
            option.palette.setColor(QPalette.Highlight, QColor(230, 230, 230))
        super().paint(painter, option, index)


class Video2SRT(QWidget):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.prompts_orm = PromptsOrm()
        self.settings = settings
        self.table = TableWindow(self, settings)
        self.util = SecWindow(self)
        self.language_name = config.langnamelist
        self.setObjectName(text)
        self.setupUi()
        self.bind_action()

    def setupUi(self):

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 导入文件
        self.btn_get_video = PushButton("选择音视频文件或拖放至此", self)
        self.btn_get_video.setIcon(FluentIcon.VIDEO)
        self.btn_get_video.setFixedHeight(100)

        main_layout.addWidget(self.btn_get_video)

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

        source_language_label = BodyLabel("原始语种")

        self.source_language = SearchableComboBox()
        self.source_language.addItem("自动检测")
        # todo:添加云图标
        for lang_name in config.langnamelist:
            if lang_name in ["法语", "French", "俄语"]:
                # 使用专业云服务图标
                self.source_language.addItem(f'{lang_name} (云)')
            else:
                self.source_language.addItem(lang_name, )

        self.source_language.setFixedWidth(LANGUAGE_WIDTH)

        self.source_language.setCurrentText(config.params["source_language"])

        source_layout.addWidget(source_language_label)
        source_layout.addWidget(self.source_language)
        source_layout.addStretch()
        combo_layout.addLayout(source_layout)

        # 识别引擎布局

        recognition_layout = QHBoxLayout()
        recognition_layout.setSpacing(5)
        recognition_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        # 识别引擎
        recognition_label = BodyLabel("识别引擎")

        self.source_model = TransComboBox()
        self.source_model.setFixedWidth(131)
        model_type = self.settings.value("source_module_status", type=int)
        self.source_model.addItems(config.model_code_list)
        self.source_model.setCurrentText(config.params["source_module_key"])
        recognition_layout.addWidget(recognition_label)
        recognition_layout.addWidget(self.source_model)
        recognition_layout.addStretch()
        combo_layout.addLayout(recognition_layout)

        combo_layout.addStretch()
        self.check_fanyi = CheckBox("字幕翻译")
        self.check_fanyi.setMinimumSize(QSize(0, 35))
        combo_layout.addWidget(self.check_fanyi)

        # 翻译语言布局
        translate_language_layout = QHBoxLayout()
        translate_language_layout.setSpacing(5)
        translate_language_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        translate_language_label = BodyLabel("翻译语种")
        self.translate_language_combo = SearchableComboBox()
        self.translate_language_combo.setFixedWidth(LANGUAGE_WIDTH)
        self.translate_language_combo.addItems(self.language_name)
        self.translate_language_combo.setCurrentText(config.params["target_language"])
        translate_language_layout.addWidget(translate_language_label)
        translate_language_layout.addWidget(self.translate_language_combo)
        translate_language_layout.addStretch()
        combo_layout.addLayout(translate_language_layout)

        # 翻译引擎布局
        translate_engine_layout = QHBoxLayout()
        translate_engine_layout.setSpacing(5)
        translate_engine_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        translate_model_name = BodyLabel("翻译引擎")

        self.translate_model = TransComboBox()
        self.translate_model.setFixedWidth(117)

        translate_list = get_translate_code()
        self.translate_model.addItems(translate_list)
        translate_name = config.params["translate_channel"]
        self.translate_model.setCurrentText(translate_name)

        translate_engine_layout.addWidget(translate_model_name)
        translate_engine_layout.addWidget(self.translate_model)
        translate_engine_layout.addStretch()
        combo_layout.addLayout(translate_engine_layout)

        prompt_layout = QHBoxLayout()
        prompt_layout.setSpacing(5)
        prompt_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        ai_prompt_name = BodyLabel("提示词")
        self.ai_prompt = SearchableComboBox(self)
        self.ai_prompt.setFixedWidth(98)
        self.ai_prompt.addItems(self._get_ai_prompt())
        self.ai_prompt.setCurrentText(config.params["prompt_name"])
        prompt_layout.addWidget(ai_prompt_name)
        prompt_layout.addWidget(self.ai_prompt)
        combo_layout.addLayout(prompt_layout)

        ai_prompt_name.hide()
        self.ai_prompt.hide()

        # 媒体表格卡片
        table_card = CardWidget(self)
        table_layout = QVBoxLayout(table_card)

        self.media_table = TableWidget(self)
        # 设置表格表头不显示网格线
        self.media_table.setColumnCount(5)
        self.media_table.setHorizontalHeaderLabels(
            ["文件名", "时长", "算力消耗", "操作", "文件路径"]
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
        # 设置列宽
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 文件名列自适应宽度
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.media_table.setColumnWidth(1, 100)  # 时长列
        self.media_table.setColumnWidth(2, 100)  # 算力消耗列
        self.media_table.setColumnWidth(3, 100)  # 操作列
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
        self.check_fanyi.stateChanged.connect(
            lambda: print(self.check_fanyi.isChecked())
        )
        self.start_btn.clicked.connect(self.on_start_clicked)
        self.act_btn_get_video()

        # 添加识别引擎切换事件
        self.source_model.currentTextChanged.connect(self._on_model_changed)

    def on_start_clicked(self):
        # 获取识别引擎代码
        model_key = self.source_model.currentText()
        model_info = start_tools.match_source_model(model_key)
        model_status = model_info["status"]

        translate_status = True
        # todo： model_status 调整为translate_api_name中的值
        if self.check_fanyi.isChecked() == True and translate_status < 100:
            #todo： 支持云识别+翻译后取消这个
            InfoBar.warning(
                title="提示",
                content="使用云模型识别字幕后，算力消耗在任务结束后扣费",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self,
            )
        #     return

        # 如果勾选了翻译，检查API密钥
        if self.check_fanyi.isChecked() and not self._check_api_key():
            return

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

        # 保存媒体列表
        self.add_queue_mp4()
        # 是否需要翻译
        translate_status = self.check_fanyi.isChecked()
        config.params["translate_status"] = translate_status
        logger.trace(f"translate_status type: {type(translate_status)}")
        language_name = self.source_language.currentText()
        logger.debug(f"==========language_name:{language_name}")
        config.params["source_language"] = language_name
        config.params["source_language_code"] = language_code(language_name)
        if model_status > 100:
            # 本地引擎
            self.util.check_asr()
        elif model_status < 100:
            # 云引擎
            self.util.check_cloud_asr()

    def act_btn_get_video(self):
        # 选择文件,并显示路径
        self.btn_get_video.clicked.connect(
            lambda: self.table.select_files(self.media_table)
        )
        self.btn_get_video.setAcceptDrops(True)
        self.btn_get_video.dragEnterEvent = self.table.drag_enter_event
        self.btn_get_video.dropEvent = lambda event: self.table.drop_event(
            self.media_table, event
        )

    def add_queue_mp4(self):
        # 获取self.main.media_table中第4列的数据
        srt_list = []
        for i in range(self.media_table.rowCount()):
            # 获取self.media_table第i行第4列的数据
            logger.info(self.media_table.item(i, 4).text())
            srt_list.append(self.media_table.item(i, 4).text())
        config.queue_asr.extend(srt_list)
        logger.info(f"queue_asr: {config.queue_asr}")

    def _get_ai_prompt(self):
        prompt_names = self.prompts_orm.get_prompt_name()
        return [i.prompt_name for i in prompt_names]

    def _on_model_changed(self):
        """当识别引擎切换时的处理"""
        # 更新原始语种列表
        self._update_source_language_list()
        # 重新计算算力消耗
        self.recalculate_computing_power()

    def _update_source_language_list(self):
        """根据当前识别引擎更新原始语种列表"""
        # 保存当前选择
        current_selection = self.source_language.currentText()

        # 清空列表
        self.source_language.clear()

        # 获取当前识别引擎
        model_key = self.source_model.currentText()
        model_info = start_tools.match_source_model(model_key)
        model_status = model_info["status"]

        if model_status < 100:
            # 云模型 - 支持所有语言
            self.source_language.addItem("自动检测")
            self.source_language.addItems(config.langnamelist)
        else:
            # 中文模型 - 仅支持中文和英语
            supported_languages = ["中文", "英语"]
            for lang_name in config.langnamelist:
                if lang_name in supported_languages:
                    self.source_language.addItem(lang_name)

        # 尝试恢复之前的选择
        index = self.source_language.findText(current_selection)
        if index >= 0:
            self.source_language.setCurrentIndex(index)
        else:
            # 如果之前的选择不在新列表中，尝试使用配置中的默认值
            default_lang = config.params.get("source_language", "")
            index = self.source_language.findText(default_lang)
            if index >= 0:
                self.source_language.setCurrentIndex(index)
            else:
                # 都找不到就选第一个
                self.source_language.setCurrentIndex(0)

    def recalculate_computing_power(self):
        """当切换识别引擎时，重新计算所有文件的算力消耗"""
        # 遍历表格中的所有行
        for row in range(self.media_table.rowCount()):
            # 获取当前行的时长字符串
            duration_str = self.media_table.item(row, 1).text()
            if duration_str:
                # 将时长字符串转换为秒数
                h, m, s = map(int, duration_str.split(':'))
                duration_seconds = h * 3600 + m * 60 + s
                logger.info(f"computing_power: {duration_seconds}")

                # 重新计算算力消耗
                ds_count = str(self.table._calc_ds(duration_seconds))

                # 更新表格中的算力消耗
                self.media_table.item(row, 2).setText(ds_count)

    def _check_api_key(self) -> bool:
        """检查当前选择的翻译引擎是否配置了API密钥"""
        # 获取当前选择的翻译引擎
        translate_engine = self.translate_model.currentText()
        logger.debug(f"检查翻译引擎: {translate_engine}")

        # 使用现有的逻辑：通过translate_api_name映射获取agent名称
        agent_name = next(
            (
                key
                for key, value in translate_api_name.items()
                if value == translate_engine
            ),
            None,
        )
        if not agent_name:
            # 如果不是我们管理的AI代理，可能是其他翻译服务，暂时允许通过
            logger.debug(f"未知的翻译引擎: {translate_engine}，跳过密钥检查")
            return True

        # 检查agent是否存在且有密钥 - 动态获取最新配置
        current_agent_configs = agent_settings()
        if agent_name in current_agent_configs:
            agent = current_agent_configs[agent_name]

            if agent.key is None:
                # 显示错误提示
                InfoBar.error(
                    title="配置错误",
                    content="填写key",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self,
                )
                logger.error(f"翻译引擎 {translate_engine} ({agent_name}) 未配置API密钥")
                return False

        return True


class TableWindow:
    def __init__(self, main, settings):
        self.duration_seconds = None  #视频时长，秒
        self.main = main
        self.settings = settings
        self.file_duration = None

    # 列表的操作
    @Slot()
    def select_files(self, ui_table: QTableWidget):
        # 选择文件
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.main,
            config.transobj["selectmp4"],
            config.last_opendir,
            "Video files(*.mp4 *.avi *.mov *.mpg *.mkv *.mp3 *.wav *.flac)",
        )

        if file_paths:
            for file_path in file_paths:
                self.add_file_to_table(ui_table, file_path)

            config.last_opendir = str(Path(file_paths[0]).parent)
            self.settings.setValue("last_dir", config.last_opendir)

    def add_file_to_table(self, ui_table: TableWidget, file_path: str):
        # 添加文件到表格

        # 不加这个log，mac系统上在check_asr函数中中target_dir就是空值
        # logger.trace("config.params:")
        # logger.trace(config.params)
        row_position = ui_table.rowCount()
        self.file_duration = self.get_video_duration(file_path)  # 获取视频时长
        ds_count = str(self._calc_ds(self.duration_seconds))
        if self.file_duration:
            ui_table.insertRow(row_position)
            file_name = Path(file_path).name
            # 文件名
            ui_table.setItem(row_position, 0, QTableWidgetItem(file_name))
            # 时长
            ui_table.setItem(row_position, 1, QTableWidgetItem(self.file_duration))
            # 算力消耗
            ui_table.setItem(row_position, 2, QTableWidgetItem(ds_count))
            # 操作
            delete_button = DeleteButton("删除")
            ui_table.setCellWidget(row_position, 3, delete_button)
            delete_button.clicked.connect(
                lambda checked=False, btn=delete_button: self.delete_file(ui_table, btn)
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

    @Slot()
    def delete_file(self, ui_table: QTableWidget, button):
        """通过按钮对象动态查找并删除对应行"""
        # 遍历所有行，找到包含这个按钮的行
        for row in range(ui_table.rowCount()):
            if ui_table.cellWidget(row, 3) == button:
                ui_table.removeRow(row)
                break

    def get_video_duration(self, file: str):
        # Use ffprobe to get video duration

            # 使用工具函数计算时长
        self.duration_seconds = calculate_video_duration(file)
        # 使用工具函数格式化
        return format_duration(self.duration_seconds)

    def drag_enter_event(self, event: QDragEnterEvent):
        # 接受拖入
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drop_event(self, ui_table: QTableWidget, event: QDropEvent):
        # 拖出
        file_urls = event.mimeData().urls()
        # logger.info(f"file_urls: {file_urls}")
        if file_urls:
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                self.add_file_to_table(ui_table, file_path)
        event.accept()

    def clear_table(self, ui_table: QTableWidget):
        # 清空表格
        ui_table.setRowCount(0)

    def _calc_ds(self, video_long: float) -> int:
        # 计算代币消耗
        # 获取当前选择的识别引擎
        model_key = self.main.source_model.currentText()
        model_info = start_tools.match_source_model(model_key)
        model_status = model_info["status"]
        # 根据不同的识别引擎设置不同的算力消耗系数
        # 算力总消耗
        amount = 0
        if model_status < 100:
            # 云模型，消耗算力
            # 使用工具函数计算代币
            asr_amount = calculate_asr_tokens(video_long)
            amount = asr_amount
            logger.info(f'ASR代币消耗: {asr_amount}')

        return amount


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings

    app = QApplication(sys.argv)
    window = Video2SRT("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
    window.show()
    sys.exit(app.exec())
