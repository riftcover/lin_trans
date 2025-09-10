import os
from typing import Optional

from PySide6.QtCore import QThread, Signal, Qt, QUrl, QSize, QTimer, Slot
from PySide6.QtNetwork import (QNetworkProxy, QNetworkAccessManager, QNetworkRequest, QNetworkReply, )
from PySide6.QtWidgets import (QTabWidget, QTableWidgetItem, QFileDialog, QAbstractItemView, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout,
                               QSizePolicy, QTextEdit, QHeaderView, QButtonGroup, QPushButton, QSpacerItem, QProgressBar, )

from nice_ui.configure import config
from nice_ui.task.api_thread import ApiWorker
from nice_ui.ui import __version__
from nice_ui.ui.style import LLMKeySet, TranslateKeySet
from nice_ui.util.tools import start_tools
from orm.queries import PromptsOrm
from utils import logger
from vendor.qfluentwidgets import (TableWidget, BodyLabel, CaptionLabel, HyperlinkLabel, SubtitleLabel, ToolButton, RadioButton, LineEdit, PushButton, InfoBar,
                                   InfoBarPosition, FluentIcon, PrimaryPushButton, CardWidget, StrongBodyLabel, TransparentToolButton, SpinBox, MessageBox,
                                   )


class DownloadThread(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(bool)

    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name

    def run(self):
        try:
            from agent.model_down import download_model
            download_model(self.model_name, progress_callback=self.update_progress)
            self.finished_signal.emit(True)
        except Exception as e:
            logger.error(f"下载模型时发生错误: {str(e)}")
            self.finished_signal.emit(False)

    def update_progress(self, progress):
        self.progress_signal.emit(progress)


class LocalModelPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setup_ui()
        self.bind_action()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 本地识别引擎选择
        # self.appCardContainer = AppCardContainer(self)
        # self.whisper_cpp_card = self.appCardContainer.addAppCard("Whisper.Cpp", "支持 apple 芯片加速", True)
        # self.faster_whisper_card = self.appCardContainer.addAppCard("FasterWhisper", "时间更精确，支持 cuda 加速")
        #
        # # "Whisper.Cpp"被点击时显示"Whisper.Cpp 模型列表"，"FasterWhisper"被点击时显示"FasterWhisper 模型列表"
        # self.whisper_cpp_card.radioButton.clicked.connect(lambda: self.show_model_list("Whisper.Cpp"))
        # self.whisper_cpp_card.radioButton.clicked.connect(lambda: self.model_type(1))
        # self.faster_whisper_card.radioButton.clicked.connect(lambda: self.show_model_list("FasterWhisper"))
        # self.faster_whisper_card.radioButton.clicked.connect(lambda: self.model_type(2))

        # layout.addWidget(self.appCardContainer)
        # 模型存储路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(BodyLabel("模型存储路径:"))  # Windows
        logger.info(f"模型存储路径: {config.models_path}")

        self.path_input = QLineEdit(str(config.models_path))
        self.path_change_btn = PushButton("更换路径")
        self.path_open_btn = PushButton("打开目录")
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.path_change_btn)
        path_layout.addWidget(self.path_open_btn)
        layout.addLayout(path_layout)

        tips1 = CaptionLabel("提示: 请确保模型存储路径存在且有足够的磁盘空间。更换存储目录后，请重新启动程序。")
        layout.addWidget(tips1)

        # Whisper.Cpp 模型列表
        # self.cpp_model_title = BodyLabel("Whisper.Cpp 模型列表")
        # self.cpp_model_table = TableWidget(self)
        # self.cpp_model_table.setColumnCount(6)
        # self.cpp_model_table.setHorizontalHeaderLabels(["模型", "语言支持", "准确度", "模型大小", "运行内存", "识别速度"])
        # self.cpp_model_table.verticalHeader().setVisible(False)
        # self.cpp_model_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #
        # # FasterWhisper 模型列表
        # self.faster_model_title = BodyLabel("FasterWhisper 模型列表")
        # self.faster_model_table = TableWidget(self)
        # self.faster_model_table.setColumnCount(6)
        # self.faster_model_table.setHorizontalHeaderLabels(["模型", "语言支持", "准确度", "模型大小", "运行内存", "识别速度"])
        # self.faster_model_table.verticalHeader().setVisible(False)
        # self.faster_model_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.funasr_model_title = BodyLabel("模型列表")
        self.funasr_model_table = TableWidget(self)
        self.funasr_model_table.setColumnCount(3)
        self.funasr_model_table.setHorizontalHeaderLabels(
            ["模型", "模型大小", "安装状态"]
        )
        # 设置label的宽度
        self.funasr_model_table.setColumnWidth(0, 150)
        self.funasr_model_table.setColumnWidth(1, 100)
        self.funasr_model_table.setColumnWidth(2, 130)
        self.funasr_model_table.verticalHeader().setVisible(False)
        self.funasr_model_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # layout.addWidget(self.cpp_model_title)
        # layout.addWidget(self.cpp_model_table)
        # layout.addWidget(self.faster_model_title)
        # layout.addWidget(self.faster_model_table)
        layout.addWidget(self.funasr_model_title)
        layout.addWidget(self.funasr_model_table)
        self.show_funasr_table(self.funasr_model_table)

        # 初始化显示 Whisper.Cpp 模型列表
        # self.show_model_list("Whisper.Cpp")

        tips1 = CaptionLabel(
            "不同引擎的模型准确度和识别速度可能会有所差异，由于文件比较大，请耐心等待下载完成。"
        )
        layout.addWidget(tips1)

    def bind_action(self):
        self.path_open_btn.clicked.connect(self.open_directory)
        self.path_change_btn.clicked.connect(self.change_path)

    def open_directory(self):
        # 打开目录
        path = self.path_input.text()
        if os.path.exists(path):
            # 用 os.startfile (Windows) 或 os.system('open ...') (macOS/Linux) 来打开文件夹。
            (
                os.startfile(path)
                if sys.platform == "win32"
                else os.system(f'open "{path}"')
            )

        else:
            logger.error(f"路径不存在: {path}")

    def change_path(self):
        # 选择路径
        if new_path := QFileDialog.getExistingDirectory(self, "选择模型存储路径"):
            self.path_input.setText(new_path)
            # logger.info(f"new_path type: {type(new_path)}")
            config.models_path = new_path
            self.settings.setValue(
                "models_path", config.models_path
            )

            # 重新检查模型安装状态
            self.show_funasr_table(self.funasr_model_table)
            # self.settings.sync()

    def populate_model_table(self, table, models):
        table.setRowCount(len(models))
        for row, model in enumerate(models):
            for col, value in enumerate(model):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                if col in [2, 5]:  # 准确度列
                    item.setText("★" * value)
                elif col == 6:  # 状态列
                    btn = PushButton(value)
                    if value == "已安装":
                        btn.setEnabled(False)
                    table.setCellWidget(row, col, btn)
                    continue
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        table.setColumnWidth(0, 150)  # 设置第一列宽度

    # def show_model_list(self, engine):
    #     if engine == "Whisper.Cpp":
    #         self.cpp_model_title.show()
    #         self.cpp_model_table.show()
    #         self.faster_model_title.hide()
    #         self.faster_model_table.hide()
    #         # 填充 Whisper.Cpp 模型数据
    #         cpp_models = [("全语言大模型", "多语言", 5, "2.88 GB", "4.50 GB", 2), ("全语言中模型", "多语言", 4, "1.43 GB", "2.80 GB", 3),
    #                       ("全语言小模型", "多语言", 3, "465.01 MB", "1.00 GB", 5), ("英语大模型", "英语", 5, "1.43 GB", "2.80 GB", 3),
    #                       ("英语小模型", "英语", 4, "465.03 MB", "1.00 GB", 5), ]
    #         self.populate_model_table(self.cpp_model_table, cpp_models)
    #     elif engine == "FasterWhisper":
    #         self.cpp_model_title.hide()
    #         self.cpp_model_table.hide()
    #         self.faster_model_title.show()
    #         self.faster_model_table.show()
    #         # 填充 FasterWhisper 模型数据
    #         faster_models = [("全语言大模型", "多语言", 5, "2.88 GB", "4.50 GB", 2), ("全语言中模型", "多语言", 4, "1.43 GB", "2.80 GB", 3),
    #                          ("全语言小模型", "多语言", 3, "463.69 MB", "1.00 GB", 5), ("英语大模型", "英语", 5, "1.43 GB", "2.80 GB", 3),
    #                          ("英语小模型", "英语", 4, "463.58 MB", "1.00 GB", 5), ]
    #
    #         self.populate_model_table(self.faster_model_table, faster_models)

    def show_funasr_table(self, table):
        faster_models = [
            # ("多语言模型", "940 MB"),
            ("中文模型", "909.6 MB"),
            ("多语言模型", "880 MB"),
        ]
        model_list = config.model_list

        table.setRowCount(len(faster_models))
        for row, model in enumerate(faster_models):
            model_name, model_size = model
            model_info = model_list.get(model_name, {})
            model_folder = model_info.get("model_name", "")

            """
            检查模型是否已安装,因为下载过程可能会中断，下载支持断点续传，
            所有下载完成的判断根据是最后一个文件是否存在来判断，
            最后下载的是文件是tokens.json
            """
            rr_dir = os.path.join(config.funasr_model_path, model_folder, "tokens.json")

            is_installed = os.path.exists(
                rr_dir
            )

            for col, value in enumerate([model_name, model_size]):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)

            # 添加安装状态或安装按钮
            if is_installed:
                status_item = QTableWidgetItem("已安装")
                status_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 2, status_item)
            else:
                install_btn = QPushButton("安装")
                install_btn.clicked.connect(
                    lambda _, r=row, m=model_folder: self.install_model(r, m)
                )
                table.setCellWidget(row, 2, install_btn)

        table.resizeColumnsToContents()
        table.setColumnWidth(0, 150)  # 设置第一列宽度

    def install_model(self, row, model_folder):
        model_cn_name = self.funasr_model_table.item(row, 0).text()
        logger.info(f'row: {row}, model: {model_cn_name}')
        model_name = start_tools.match_model_name(model_cn_name)
        logger.info(f'model_name: {model_name}')

        if not model_name:
            InfoBar.error(
                title="错误",
                content="无法获取模型ID",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return

        # 创建进度条
        progress_bar = QProgressBar(self)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        self.funasr_model_table.setCellWidget(row, 2, progress_bar)

        # 创建下载线程
        self.download_thread = DownloadThread(model_name)
        self.download_thread.progress_signal.connect(progress_bar.setValue)
        self.download_thread.finished_signal.connect(
            lambda success: self.download_finished(success, row, model_folder)
        )

        # 开始下载
        self.download_thread.start()

    def download_finished(self, success, row, model_folder):
        # 移除进度条
        self.funasr_model_table.removeCellWidget(row, 2)

        if success:
            logger.success(f"模型安装成功: {model_folder}")
            InfoBar.success(
                title="成功",
                content="模型安装完成",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            self.update_model_status(row, True)
        else:
            logger.error(f"模型安装失败: {model_folder}")
            InfoBar.error(
                title="错误",
                content="模型安装失败",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            self.update_model_status(row, False)

    def update_model_status(self, row, is_installed):
        if is_installed:
            status_item = QTableWidgetItem("已安装")
            status_item.setTextAlignment(Qt.AlignCenter)
            self.funasr_model_table.setItem(row, 2, status_item)
        else:
            install_btn = QPushButton("安装")
            install_btn.clicked.connect(
                lambda _, r=row, m=self.get_model_folder(row): self.install_model(r, m)
            )
            self.funasr_model_table.setCellWidget(row, 2, install_btn)

    def get_model_folder(self, row):
        model_name = self.funasr_model_table.item(row, 0).text()
        return config.model_list.get(model_name, {}).get("model_name", "")

    def model_type(self, param: int):
        """
        设置模型类型，1为Whisper.Cpp，2为FasterWhisper
        """
        config.model_type = param
        logger.info(f"设置模型类型: {config.model_type}")
        self.settings.setValue("model_type", param)


class PopupWidget(QWidget):
    def __init__(
            self, key_id: Optional[int], prompt_name: str, prompt_msg: str, parent=None
    ):
        super().__init__(parent=parent)
        self.key_id = key_id
        self.name = prompt_name
        self.msg = prompt_msg
        self.resize(460, 330)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setup_ui()

    # def event(self, event):
    #     """
    #     重写事件过滤器，打印窗口大小
    #     检查事件类型是否为 QEvent.Move，这是窗口移动事件。
    #     如果是移动事件，调用 self.print_window_size() 方法打印窗口大小。
    #     调用 super().event(event) 以确保其他事件也能被正确处理。
    #     """
    #
    #     if event.type() == QEvent.Move:
    #         self.print_window_size()
    #     return super().event(event)
    #
    # def print_window_size(self):
    #     size = self.size()
    #     print(f"窗口大小: 宽度={size.width()}, 高度={size.height()}")

    def setup_ui(self):
        layout = QVBoxLayout()
        self.name_input = None

        if self.key_id is not None:
            # 编辑提示词
            self.setWindowTitle("编辑提示词")
            self.name_input = LineEdit()
            self.name_input.setText(self.name)
            # 不可编辑
            self.name_input.setReadOnly(True)
        else:
            # 新增提示词
            self.setWindowTitle("新增提示词")
            self.name_input = LineEdit()
            self.name_input.setPlaceholderText("请输入提示词名称")
            self.name_input.setClearButtonEnabled(True)

        self.label = QTextEdit()
        self.label.setPlainText(self.msg)
        close_button = PushButton("取消")
        close_button.clicked.connect(self.close)
        enter_button = PrimaryPushButton("确定")
        enter_button.clicked.connect(self.save_prompt)
        button_layout = QHBoxLayout()
        button_layout.addStretch(4)
        button_layout.addWidget(enter_button)
        button_layout.addWidget(close_button)

        layout.addWidget(self.name_input)
        layout.addWidget(self.label)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save_prompt(self):
        # 保存提示词到数据库
        new_name = self.name_input.text()
        new_content = self.label.toPlainText()
        if not new_name or not new_content:
            logger.error("提示词不能为空")
            InfoBar.error(
                title="错误",
                content="提示词不能为空",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return
        if self.key_id is None:
            # 添加新提示词
            logger.info(f"添加新提示词: 名称={new_name}, 内容={new_content}")
            if _ := self.parent().prompts_orm.insert_table_prompt(
                    prompt_name=new_name, prompt_content=new_content
            ):
                logger.success(f"新提示词已添加: {new_name}")
                InfoBar.success(
                    title="成功",
                    content="新提示词已添加",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.parent(),
                )
            else:
                logger.error(f"添加新提示词失败: {new_name}")
                InfoBar.error(
                    title="错误",
                    content="添加新提示词失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.parent(),
                )
        else:
            # 更新现有提示词
            logger.info(
                f"修改提示词: id={self.key_id}, 名称={new_name}, 内容={new_content}"
            )
            success: bool = self.parent().prompts_orm.update_table_prompt(
                key_id=self.key_id, prompt_name=new_name, prompt_content=new_content
            )
            logger.success(f"提示词已更新: {new_name}")
            if success:
                InfoBar.success(
                    title="成功",
                    content="提示词已更新",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.parent(),
                )
            else:
                logger.error(f"更新提示词失败: {new_name}")
                InfoBar.error(
                    title="错误",
                    content="更新提示词失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self.parent(),
                )

        self.close()
        self.parent().refresh_table_data()


class LLMConfigPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.prompts_orm = PromptsOrm()
        self.setup_ui()
        self._init_table()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 10, 20, 10)

        # API Key Section
        api_key_card = CardWidget(self)
        api_key_layout = QVBoxLayout(api_key_card)
        api_key_layout.addWidget(SubtitleLabel("API Key"))

        api_key_content_layout = QHBoxLayout()  # 新增：水平布局来容纳卡片和伸缩

        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(0)

        kimi_card = LLMKeySet("kimi", "https://platform.moonshot.cn/console/api-keys", self)
        zhipu_card = LLMKeySet("zhipu", "https://open.bigmodel.cn/usercenter/apikeys", self)
        qwen_card = LLMKeySet("qwen", "https://bailian.console.aliyun.com/?tab=model#/api-key", self)
        deepseek_card = LLMKeySet("deepseek", "https://platform.deepseek.com/api_keys", self)

        cards_layout.addWidget(kimi_card)
        cards_layout.addWidget(zhipu_card)
        cards_layout.addWidget(qwen_card)
        cards_layout.addWidget(deepseek_card)

        api_key_content_layout.addLayout(cards_layout, 1)
        api_key_content_layout.addStretch(1)  # 添加水平伸缩

        api_key_layout.addLayout(api_key_content_layout)
        main_layout.addWidget(api_key_card)

        # # Prompts Section
        # prompts_card = CardWidget(self)
        # prompts_layout = QVBoxLayout(prompts_card)
        # # prompts_layout.setSpacing(10)
        #
        # prompts_header = QHBoxLayout()
        # prompts_header.addWidget(SubtitleLabel("提示词"))
        # prompts_header.addStretch()
        # refresh_btn = ToolButton(FluentIcon.ROTATE)
        # refresh_btn.setToolTip("刷新提示词")
        # refresh_btn.clicked.connect(self.refresh_table_data)
        #
        # add_btn = ToolButton(FluentIcon.CHAT)
        # add_btn.setToolTip("新增提示词")
        # add_btn.clicked.connect(self._add_prompt)
        # prompts_header.addWidget(add_btn, alignment=Qt.AlignRight)
        # prompts_header.addWidget(refresh_btn, alignment=Qt.AlignRight)
        # prompts_layout.addLayout(prompts_header)
        #
        # # 创建一个水平布局来容纳表格和左右间距
        #
        # self.prompts_table = TableWidget(self)
        # # 设置表格为交替行颜色
        # self.prompts_table.setAlternatingRowColors(True)
        # self.prompts_table.verticalHeader().setDefaultSectionSize(
        #     40
        # )  # 设置默认行高为 40
        # self.prompts_table.verticalHeader().setSectionResizeMode(
        #     QHeaderView.Fixed
        # )  # 固定行高
        #
        # # 不显示表头
        # self.prompts_table.horizontalHeader().setVisible(False)
        #
        # self.prompts_table.setColumnCount(4)
        # self.prompts_table.setHorizontalHeaderLabels(
        #     ["主键id", "提示词名称", "提示词内容", "操作"]
        # )
        # self.prompts_table.verticalHeader().setVisible(False)
        # self.prompts_table.setColumnWidth(0, 50)
        # self.prompts_table.setColumnWidth(1, 150)
        # self.prompts_table.setColumnWidth(3, 70)
        # self.prompts_table.setColumnHidden(0, True)
        #
        # # 让第三列（索引为2）占据剩余空间
        # self.prompts_table.horizontalHeader().setSectionResizeMode(
        #     2, QHeaderView.Stretch
        # )
        #
        # # 其他列保持固定宽度
        # self.prompts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        # self.prompts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        #
        # self.prompts_table.setEditTriggers(
        #     QAbstractItemView.NoEditTriggers
        # )  # 设置表格为不可编辑
        #
        # prompts_layout.addWidget(self.prompts_table)
        #
        # main_layout.addWidget(prompts_card)
        main_layout.addStretch(1)

    def _init_table(self):
        all_prompts = self.prompts_orm.get_data_with_id_than_one()
        for prompt in all_prompts:
            self._init_prompt(
                prompt_id=prompt.id,
                prompt_name=prompt.prompt_name,
                prompt_content=prompt.prompt_content,
            )

    def _init_prompt(self, prompt_id, prompt_name, prompt_content):
        row = self.prompts_table.rowCount()
        self.prompts_table.insertRow(row)
        self.prompts_table.setItem(row, 0, QTableWidgetItem(str(prompt_id)))
        self.prompts_table.setCellWidget(row, 1, StrongBodyLabel(str(prompt_name)))
        self.prompts_table.setItem(row, 2, QTableWidgetItem(str(prompt_content)))

        # 创建一个包含两个按钮的widget
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(5, 2, 5, 2)
        buttons_layout.setSpacing(2)

        edit_btn = TransparentToolButton(FluentIcon.EDIT)
        edit_btn.setFixedSize(QSize(30, 28))
        edit_btn.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )  # 设置大小策略为Fixed
        edit_btn.clicked.connect(self._edit_prompt(edit_btn))
        buttons_layout.addWidget(edit_btn)

        delete_btn = TransparentToolButton(FluentIcon.DELETE)
        delete_btn.setFixedSize(QSize(30, 28))
        delete_btn.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )  # 设置大小策略为Fixed
        delete_btn.clicked.connect(self._delete_row(delete_btn))
        buttons_layout.addWidget(delete_btn)

        self.prompts_table.setCellWidget(row, 3, buttons_widget)

    def refresh_table_data(self):
        self.prompts_table.setRowCount(0)  # 清空表格
        all_prompts = self.prompts_orm.get_data_with_id_than_one()  # 获取最新数据
        for prompt in all_prompts:
            self._init_prompt(
                prompt_id=prompt.id,
                prompt_name=prompt.prompt_name,
                prompt_content=prompt.prompt_content,
            )  #

    def _delete_row(self, button):
        def delete_row():
            button_row = self.prompts_table.indexAt(button.pos()).row()
            key_id = self.prompts_table.item(button_row, 0).text()
            self.prompts_orm.delete_table_prompt(key_id)
            self.prompts_table.removeRow(button_row)

        return delete_row

    def _edit_prompt(self, button):
        def edit_row():
            button_row = self.prompts_table.indexAt(button.pos()).row()
            logger.debug(f"编辑prompt,所在行:{button_row} ")
            key_id = self.prompts_table.item(button_row, 0).text()
            logger.debug(f"编辑prompt,key_id:{key_id} ")
            prompt_name = self.prompts_table.cellWidget(button_row, 1).text()
            prompt_content = self.prompts_table.item(button_row, 2).text()
            self.popup = PopupWidget(int(key_id), prompt_name, prompt_content, self)
            self.popup.show()

        return edit_row

    def _add_prompt(self):
        self.popup = PopupWidget(
            key_id=None, prompt_name="", prompt_msg="", parent=self
        )
        self.popup.show()


class TranslationPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        tips_label = CaptionLabel(
            "请填写服务商提供的API Key，在翻译任务中可以免除算力，所有Key只会保存在本地。"
        )
        main_layout.addWidget(tips_label)

        title_layout = QHBoxLayout()
        title_label = BodyLabel("翻译API Key")
        tutorial_link = HyperlinkLabel("设置教程")
        tutorial_link.setUrl("xdd")

        title_layout.addWidget(title_label)
        title_layout.addWidget(tutorial_link)
        main_layout.addLayout(title_layout)

        self.baidu_key = TranslateKeySet("baidu", self)
        self.deepl_key = TranslateKeySet("deepl", self)
        self.google_key = TranslateKeySet("google", self)
        main_layout.addWidget(self.baidu_key)
        main_layout.addWidget(self.deepl_key)
        main_layout.addWidget(self.google_key)

        self.setLayout(main_layout)


class ProxyTestWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.handle_response)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.test_button = QPushButton("检查代理", self)
        self.test_button.clicked.connect(self.ask_proxy)
        self.response_text = QTextEdit(self)
        self.response_text.setReadOnly(True)

        layout.addWidget(self.test_button)
        layout.addWidget(self.response_text)

    def ask_proxy(self):
        url = QUrl("http://www.google.com")
        request = QNetworkRequest(url)
        request.setAttribute(
            QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork
        )
        request.setAttribute(
            QNetworkRequest.RedirectPolicyAttribute,
            QNetworkRequest.NoLessSafeRedirectPolicy,
        )
        request.setTransferTimeout(10000)  # 设置 10 秒超时
        self.network_manager.get(request)

    def handle_response(self, reply):
        if reply.error() == QNetworkReply.NoError:
            content = reply.readAll()
            self.response_text.setPlainText(str(content, encoding="utf-8"))
            InfoBar.success(
                title="成功",
                content=f"测试成功: 状态码 {reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        else:
            error_msg = reply.errorString()
            self.response_text.setPlainText(f"错误: {error_msg}")
            InfoBar.error(
                title="错误",
                content=f"测试失败: {error_msg}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )

        reply.deleteLater()


def print_height_difference(widget1, widget2):
    # 确保窗口已经完成布局
    QTimer.singleShot(0, lambda: _print_height_difference(widget1, widget2))


def _print_height_difference(widget1, widget2):
    pos1 = widget1.mapToGlobal(widget1.rect().topLeft())
    pos2 = widget2.mapToGlobal(widget2.rect().topLeft())

    y1 = pos1.y()
    height1 = widget1.height()
    y2 = pos2.y()

    difference = y2 - (y1 + height1)

    print(f"Widget 1 ({widget1.__class__.__name__}):")
    print(f"  Y position: {y1}")
    print(f"  Height: {height1}")
    print(f"Widget 2 ({widget2.__class__.__name__}):")
    print(f"  Y position: {y2}")
    print(f"Height difference: {difference}")


class ProxyPage(QWidget):
    def __init__(self, setting, parent=None):
        super().__init__(parent=parent)
        self.settings = setting
        self.setup_ui()
        self.load_settings()  # 在初始化时加载设置

    def setup_ui(self):
        # 定义一个统一的间距值
        UNIFORM_SPACING = 10

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Proxy Settings Card
        proxy_card = CardWidget(self)
        card_layout = QVBoxLayout(proxy_card)
        card_layout.setSpacing(UNIFORM_SPACING)  # 设置卡片内部统一间距
        card_layout.setContentsMargins(20, 20, 20, 20)  # 设置卡片内边距

        # 创建单选框
        self.no_proxy_radio = RadioButton("无代理")
        self.use_proxy_radio = RadioButton("手动代理配置")

        radio_layout = QVBoxLayout()
        radio_layout.setSpacing(UNIFORM_SPACING)
        self.proxy_radio_group = QButtonGroup(radio_layout)
        self.proxy_radio_group.addButton(self.no_proxy_radio)
        self.proxy_radio_group.addButton(self.use_proxy_radio)
        radio_layout.setSpacing(15)
        radio_layout.addWidget(self.no_proxy_radio)
        radio_layout.addWidget(self.use_proxy_radio)
        card_layout.addLayout(radio_layout)

        # 创建代理类型选择
        self.http_radio = RadioButton("HTTP")
        self.socks5_radio = RadioButton("SOCKS5")

        proxy_type_layout = QHBoxLayout()
        self.proxy_type_group = QButtonGroup(proxy_type_layout)
        self.proxy_type_group.addButton(self.http_radio)
        self.proxy_type_group.addButton(self.socks5_radio)
        proxy_type_layout.addSpacing(20)
        proxy_type_layout.addWidget(self.http_radio)
        proxy_type_layout.addWidget(self.socks5_radio)
        proxy_type_layout.addStretch(1)
        card_layout.addLayout(proxy_type_layout)

        # 主机名输入框
        host_layout = QHBoxLayout()
        host_layout.setAlignment(Qt.AlignLeft)
        host_label = BodyLabel("主机名(H):")
        self.host_input = LineEdit()
        self.host_input.setPlaceholderText("127.0.0.1")
        self.host_input.setMinimumWidth(250)  # 设置最小宽度为250像素
        # host_layout.addSpacing(20)
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_input)
        card_layout.addLayout(host_layout)

        # 端口号输入框
        port_layout = QHBoxLayout()
        port_layout.setAlignment(Qt.AlignLeft)
        port_label = BodyLabel("端口号(N):")
        self.port_input = SpinBox()
        self.port_input.setRange(0, 65535)
        self.port_input.setValue(7890)
        self.port_input.setMinimumWidth(150)  # 设置最小宽度为150像素
        # port_layout.addSpacing(20)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        card_layout.addLayout(port_layout)
        card_layout.addStretch(1)

        main_layout.addWidget(proxy_card)

        # Buttons Card

        # 添加一个垂直间隔
        card_layout.addItem(
            QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # 按钮布局
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.apply_button = PrimaryPushButton("保存")
        self.apply_button.setIcon(FluentIcon.SAVE)
        self.apply_button.clicked.connect(self.apply_proxy)

        self.test_button = PushButton("测试代理")
        self.test_button.setIcon(FluentIcon.SYNC)
        self.test_button.clicked.connect(self.test_proxy)

        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.test_button)
        buttons_layout.addWidget(self.apply_button)

        card_layout.addLayout(buttons_layout)

        main_layout.addWidget(proxy_card)

        # 连接单选框信号
        self.proxy_radio_group.buttonClicked.connect(self.toggle_proxy_input)
        self.proxy_type_group.buttonClicked.connect(self.on_proxy_type_changed)

    def load_settings(self):
        use_proxy = self.settings.value("use_proxy", False, type=bool)
        proxy_type = self.settings.value("proxy_type", "http", type=str)
        host = self.settings.value("proxy_host", "", type=str)
        port = self.settings.value("proxy_port", 7890, type=int)

        if use_proxy:
            self.use_proxy_radio.setChecked(True)
        else:
            self.no_proxy_radio.setChecked(True)

        if proxy_type.lower() == "http":
            self.http_radio.setChecked(True)
        else:
            self.socks5_radio.setChecked(True)

        self.host_input.setText(host)
        self.port_input.setValue(port)
        self.toggle_proxy_input()

        # self.apply_proxy() # 自动应用保存的代理设置

    def toggle_proxy_input(self):
        enabled = self.use_proxy_radio.isChecked()
        self.http_radio.setEnabled(enabled)
        self.socks5_radio.setEnabled(enabled)
        self.host_input.setEnabled(enabled)
        self.port_input.setEnabled(enabled)

    def on_proxy_type_changed(self):
        # 确保在选择 HTTP 或 SOCKS 时，"手动代理配置"被选中
        self.use_proxy_radio.setChecked(True)
        self.toggle_proxy_input()

        proxy_type = "http" if self.http_radio.isChecked() else "socks5"
        self.settings.setValue("proxy_type", proxy_type)

    def apply_proxy(self):
        use_proxy = self.use_proxy_radio.isChecked()
        proxy_type = "http" if self.http_radio.isChecked() else "socks5"
        host = self.host_input.text()
        port = self.port_input.value()

        if use_proxy:
            if not host or port == 0:
                InfoBar.warning(
                    title="警告",
                    content="请输入有效的主机名和端口号",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self,
                )
                return

            proxy = f"{proxy_type}://{host}:{port}"
            self.settings.setValue("use_proxy", use_proxy)
            self.settings.setValue("proxy_type", proxy_type)
            self.settings.setValue("proxy_host", host)
            self.settings.setValue("proxy_port", port)
            self.settings.setValue("proxy", proxy)

            try:
                proxy_obj = QNetworkProxy()
                if proxy_type.lower() == "http":
                    proxy_obj.setType(QNetworkProxy.HttpProxy)
                else:
                    proxy_obj.setType(QNetworkProxy.Socks5Proxy)

                proxy_obj.setHostName(host)
                proxy_obj.setPort(port)
                QNetworkProxy.setApplicationProxy(proxy_obj)
                logger.info(f"设置代理: {proxy_obj}")
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"设置代理时出错: {str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self,
                )
                return
        else:
            self.settings.setValue("use_proxy", False)
            self.settings.setValue("proxy", "")
            QNetworkProxy.setApplicationProxy(QNetworkProxy.NoProxy)
            logger.info("禁用代理")

        InfoBar.success(
            title="成功",
            content="代理设置已保存",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def show_current_settings(self):
        use_proxy = self.settings.value("use_proxy", False, type=bool)
        proxy_type = self.settings.value("proxy_type", "http", type=str)
        host = self.settings.value("proxy_host", "", type=str)
        port = self.settings.value("proxy_port", 7890, type=int)

        if use_proxy:
            message = f"当前使用代理: {proxy_type}://{host}:{port}"
        else:
            message = "当前未使用代理"

        InfoBar.info(
            title="当前代理设置",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def test_proxy(self):
        use_proxy = self.use_proxy_radio.isChecked()
        proxy_type = "http" if self.http_radio.isChecked() else "socks5"
        host = self.host_input.text()
        port = self.port_input.value()

        if use_proxy:
            if not host or port == 0:
                InfoBar.warning(
                    title="警告",
                    content="请输入有效的主机名和端口号",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self,
                )
                return

            proxy_obj = QNetworkProxy()
            if proxy_type.lower() == "http":
                proxy_obj.setType(QNetworkProxy.HttpProxy)
            else:
                proxy_obj.setType(QNetworkProxy.Socks5Proxy)

            proxy_obj.setHostName(host)
            proxy_obj.setPort(port)
        else:
            proxy_obj = QNetworkProxy.NoProxy

        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.setProxy(proxy_obj)
        self.network_manager.finished.connect(self.handle_response)

        request = QNetworkRequest(QUrl("http://www.google.com"))
        request.setAttribute(
            QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork
        )
        request.setAttribute(
            QNetworkRequest.RedirectPolicyAttribute,
            QNetworkRequest.NoLessSafeRedirectPolicy,
        )
        request.setTransferTimeout(10000)  # 设置 10 秒超时
        self.network_manager.get(request)

    def handle_response(self, reply):
        if reply.error() == QNetworkReply.NoError:
            reply.readAll()
            InfoBar.success(
                title="成功",
                content=f"测试成功: 状态码 {reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        else:
            error_msg = reply.errorString()
            InfoBar.error(
                title="错误",
                content=f"测试失败: {error_msg}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )

        reply.deleteLater()


class CommonPage(QWidget):
    """关于我们页面"""

    def __init__(self, settings=None, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setup_ui()
        self.bind_actions()
        self._setup_api_worker()

    def setup_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 关于我们卡片
        about_card = CardWidget(self)
        about_layout = QVBoxLayout(about_card)
        about_layout.setSpacing(15)
        about_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = SubtitleLabel("关于我们", about_card)
        about_layout.addWidget(title_label)

        # 软件版本信息
        version_layout = QHBoxLayout()
        version_label = BodyLabel("软件版本:", about_card)
        # 使用项目中的版本号
        version = __version__
        self.version_value = BodyLabel(version, about_card)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_value)
        version_layout.addStretch(1)
        about_layout.addLayout(version_layout)

        # 检查更新按钮
        update_layout = QHBoxLayout()
        self.check_update_button = PrimaryPushButton("检查更新", about_card)
        self.check_update_button.setIcon(FluentIcon.UPDATE)
        update_layout.addWidget(self.check_update_button)
        update_layout.addStretch(1)
        about_layout.addLayout(update_layout)

        # 官网链接
        website_layout = QHBoxLayout()
        website_label = BodyLabel("官方网站:", about_card)
        self.website_link = HyperlinkLabel("访问官网", about_card)
        self.website_link.setUrl("https://www.lapped-ai.com/")  # 设置为实际的官网地址
        website_layout.addWidget(website_label)
        website_layout.addWidget(self.website_link)
        website_layout.addStretch(1)
        about_layout.addLayout(website_layout)

        # 添加描述文本
        description_label = BodyLabel(
            "一款为内容创作者而生的字幕助手",
            about_card
        )
        description_label.setWordWrap(True)
        about_layout.addWidget(description_label)

        # 添加版权信息
        copyright_label = CaptionLabel("© 2025 Lapped AI. 保留所有权利。", about_card)
        about_layout.addWidget(copyright_label, alignment=Qt.AlignBottom)

        # 添加卡片到主布局
        main_layout.addWidget(about_card)
        main_layout.addStretch(1)

    def bind_actions(self):
        """绑定按钮事件"""
        self.check_update_button.clicked.connect(self.check_for_updates)

    def check_for_updates(self):
        """检查更新 - 异步方式"""
        try:
            # 禁用检查更新按钮，直到检查完成
            self.check_update_button.setEnabled(False)

            # 获取当前版本
            current_version = self.version_value.text()

            # 清空之前的任务
            self.api_worker.clear_tasks()

            # 添加版本检查任务
            self.api_worker.add_task(
                "version",
                self.api_worker.client.check_version,
                'windows',
                current_version
            )

            # 启动工作线程
            self.api_worker.start()

            InfoBar.info(
                title="检查更新",
                content="正在检查更新，请稍候...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )

        except Exception as e:
            logger.error(f"检查更新失败: {str(e)}")
            InfoBar.error(
                title="错误",
                content=f"检查更新失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            self.check_update_button.setEnabled(True)

    def handle_version_check_result(self, result):
        """处理版本检查结果"""
        try:
            logger.info(f"版本检查结果: {result}")

            # 解析API返回的结果
            if result.get("code") == 200 and result.get("message") == "success":
                data = result.get("data", {})

                if data.get("need_update", False):
                    # 需要更新
                    self.show_update_available(data)
                else:
                    # 已是最新版本
                    self.show_latest_version()
            else:
                # API返回错误
                data = result.get("data", {})
                if isinstance(data, dict) and "detail" in data:
                    error_msg = data.get("detail")
                else:
                    error_msg = result.get("message", "未知错误")

                self.handle_version_check_error(error_msg)

        except Exception as e:
            logger.error(f"处理版本检查结果出错: {str(e)}")
            self.handle_version_check_error(str(e))

    def handle_version_check_error(self, error_msg):
        """处理版本检查错误"""
        logger.error(f"版本检查错误: {error_msg}")
        InfoBar.error(
            title="检查更新失败",
            content=f"错误: {error_msg}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def show_latest_version(self):
        """显示已是最新版本的对话框"""
        current_version = self.version_value.text()
        dialog = MessageBox(
            "检查更新",
            f"当前版本 {current_version} 已经是最新版本。",
            self
        )
        dialog.yesButton.setText("确定")
        dialog.cancelButton.setVisible(False)  # 隐藏取消按钮
        dialog.exec()

    def show_update_available(self, data):
        """显示有新版本可用的对话框"""
        latest_version = data.get("latest_version", "")
        release_notes = data.get("release_notes", "无发行说明")
        update_url = data.get("update_url", "")

        message = f"发现新版本: {latest_version}\n\n更新内容:\n{release_notes}"

        dialog = MessageBox(
            "发现新版本",
            message,
            self
        )
        dialog.yesButton.setText("前往下载")
        dialog.cancelButton.setText("稍后再说")

        if dialog.exec():
            # 用户点击了"前往下载"
            import webbrowser
            webbrowser.open(update_url)

    def on_version_check_finished(self):
        """版本检查完成时调用"""
        # 重新启用检查更新按钮
        self.check_update_button.setEnabled(True)

    def _setup_api_worker(self):
        """设置API工作线程"""
        self.api_worker = ApiWorker()
        self.api_worker.signals.data_received.connect(self._on_data_received)
        self.api_worker.signals.error_occurred.connect(self._on_error_occurred)
        self.api_worker.signals.all_completed.connect(self._on_all_completed)

    @Slot(str, str)
    def _on_error_occurred(self, endpoint_name: str, error_msg: str):
        """发生错误"""
        logger.error(f"API错误: {endpoint_name} - {error_msg}")
        InfoBar.error(
            title="错误",
            content=f"检查更新失败: {error_msg}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )
        self.check_update_button.setEnabled(True)

    @Slot()
    def _on_all_completed(self):
        """所有请求完成"""
        self.check_update_button.setEnabled(True)

    @Slot(str, dict)
    def _on_data_received(self, endpoint_name: str, result: dict):
        """接收到数据"""
        if endpoint_name == "version":
            """处理版本检查结果"""
            try:
                logger.info(f"版本检查结果: {result}")

                # 解析API返回的结果
                if result.get("code") == 200 and result.get("message") == "success":
                    data = result.get("data", {})

                    if data.get("need_update", False):
                        # 需要更新
                        self.show_update_available(data)
                    else:
                        # 已是最新版本
                        self.show_latest_version()
                else:
                    # API返回错误
                    data = result.get("data", {})
                    if isinstance(data, dict) and "detail" in data:
                        error_msg = data.get("detail")
                    else:
                        error_msg = result.get("message", "未知错误")

                    self.handle_version_check_error(error_msg)

            except Exception as e:
                logger.error(f"处理版本检查结果出错: {str(e)}")
                self.handle_version_check_error(str(e))


class SettingInterface(QWidget):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setObjectName(text.replace(" ", "-"))
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.localModelPage = LocalModelPage(settings=self.settings)
        self.llmConfigPage = LLMConfigPage(settings=self.settings)
        # self.translationPage = TranslationPage(settings=self.settings)
        self.proxyPage = ProxyPage(setting=self.settings)
        self.commonPage = CommonPage(settings=self.settings)

        self.tabs.addTab(self.localModelPage, "本地模型")
        self.tabs.addTab(self.llmConfigPage, "LLM配置")
        # self.tabs.addTab(self.translationPage, "翻译配置")
        self.tabs.addTab(self.proxyPage, "代理设置")
        self.tabs.addTab(self.commonPage, "关于我们")

        layout.addWidget(self.tabs)
        self.setLayout(layout)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings

    app = QApplication(sys.argv)
    window = SettingInterface("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
    window.show()
    sys.exit(app.exec())