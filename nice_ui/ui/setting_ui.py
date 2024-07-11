import os
import re
import sys

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QTabWidget, QTableWidgetItem, QApplication, QFileDialog, QMessageBox
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit
from qfluentwidgets import (PushButton, TableWidget, BodyLabel, CaptionLabel, RadioButton, LineEdit, HyperlinkLabel)

from nice_ui.configure import config
from nice_ui.ui.style import AppCardContainer, LLMKeySet, TranslateKeySet
from nice_ui.util import tools


class LocalModelPage(QWidget):
    def __init__(self, setting, parent=None):
        super().__init__(parent=parent)
        self.setting = setting
        self.setup_ui()
        self.bind_action()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 本地识别引擎选择
        self.appCardContainer = AppCardContainer(self)
        self.whisper_cpp_card = self.appCardContainer.addAppCard("Whisper.Cpp", "支持 apple 芯片加速", True)
        self.faster_whisper_card = self.appCardContainer.addAppCard("FasterWhisper", "时间更精确，支持 cuda 加速")

        # "Whisper.Cpp"被点击时显示"Whisper.Cpp 模型列表"，"FasterWhisper"被点击时显示"FasterWhisper 模型列表"
        self.whisper_cpp_card.radioButton.clicked.connect(lambda: self.show_model_list("Whisper.Cpp"))
        self.faster_whisper_card.radioButton.clicked.connect(lambda: self.show_model_list("FasterWhisper"))

        layout.addWidget(self.appCardContainer)
        # 模型存储路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(BodyLabel("模型存储路径:"))  # Windows
        config.logger.info(f"模型存储路径: {config.models_path}")

        self.path_input = QLineEdit(str(config.models_path))
        self.path_change_btn = PushButton("更换路径")
        self.path_open_btn = PushButton("打开目录")
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.path_change_btn)
        path_layout.addWidget(self.path_open_btn)
        layout.addLayout(path_layout)

        tips1 = CaptionLabel("提示: 请确保模型存储路径存在且有足够的磁盘空间。")
        layout.addWidget(tips1)

        # Whisper.Cpp 模型列表
        self.cpp_model_title = BodyLabel("Whisper.Cpp 模型列表")
        self.cpp_model_table = TableWidget(self)
        self.cpp_model_table.setColumnCount(6)
        self.cpp_model_table.setHorizontalHeaderLabels(["模型", "语言支持", "准确度", "模型大小", "运行内存", "识别速度"])
        self.cpp_model_table.verticalHeader().setVisible(False)

        # FasterWhisper 模型列表
        self.faster_model_title = BodyLabel("FasterWhisper 模型列表")
        self.faster_model_table = TableWidget(self)
        self.faster_model_table.setColumnCount(6)
        self.faster_model_table.setHorizontalHeaderLabels(["模型", "语言支持", "准确度", "模型大小", "运行内存", "识别速度"])
        self.faster_model_table.verticalHeader().setVisible(False)

        layout.addWidget(self.cpp_model_title)
        layout.addWidget(self.cpp_model_table)
        layout.addWidget(self.faster_model_title)
        layout.addWidget(self.faster_model_table)

        # 初始化显示 Whisper.Cpp 模型列表
        self.show_model_list("Whisper.Cpp")

        tips1 = CaptionLabel("不同引擎的模型准确度和识别速度可能会有所差异，由于文件比较大，请手动下载，并放到上面的模型存储路径中。")
        layout.addWidget(tips1)

    def bind_action(self):
        self.path_open_btn.clicked.connect(self.open_directory)
        self.path_change_btn.clicked.connect(self.change_path)

    def open_directory(self):
        # 打开目录
        path = self.path_input.text()
        if os.path.exists(path):
            # 用 os.startfile (Windows) 或 os.system('open ...') (macOS/Linux) 来打开文件夹。
            os.startfile(path) if sys.platform == "win32" else os.system(f'open "{path}"')

        else:
            config.logger.error(f"路径不存在: {path}")

    def change_path(self):
        # 选择路径
        if new_path := QFileDialog.getExistingDirectory(self, "选择模型存储路径"):
            self.path_input.setText(new_path)
            # config.logger.info(f"new_path type: {type(new_path)}")
            config.models_path = new_path
            self.setting.setValue("models_path", config.models_path)

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

    def show_model_list(self, engine):
        if engine == "Whisper.Cpp":
            self.cpp_model_title.show()
            self.cpp_model_table.show()
            self.faster_model_title.hide()
            self.faster_model_table.hide()
            # 填充 Whisper.Cpp 模型数据
            cpp_models = [("全语言大模型", "多语言", 5, "2.88 GB", "4.50 GB", 2), ("全语言中模型", "多语言", 4, "1.43 GB", "2.80 GB", 3), ("全语言小模型", "多语言", 3, "465.01 MB", "1.00 GB", 5),
                          ("英语大模型", "英语", 5, "1.43 GB", "2.80 GB", 3), ("英语小模型", "英语", 4, "465.03 MB", "1.00 GB", 5), ]
            self.populate_model_table(self.cpp_model_table, cpp_models)
        else:
            self.cpp_model_title.hide()
            self.cpp_model_table.hide()
            self.faster_model_title.show()
            self.faster_model_table.show()
            # 填充 FasterWhisper 模型数据
            faster_models = [("全语言大模型", "多语言", 5, "2.88 GB", "4.50 GB", 2), ("全语言中模型", "多语言", 4, "1.43 GB", "2.80 GB", 3), ("全语言小模型", "多语言", 3, "463.69 MB", "1.00 GB", 5),
                             ("英语大模型", "英语", 5, "1.43 GB", "2.80 GB", 3), ("英语小模型", "英语", 4, "463.58 MB", "1.00 GB", 5), ]

            self.populate_model_table(self.faster_model_table, faster_models)


class LLMConfigPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # 创建垂直布局来容纳所有组件
        cards_layout = QVBoxLayout()

        # 创建两个 OpenAIApiKeyCard 实例
        kimi_card = LLMKeySet('kimi api', 'hurl')

        zhipu_card = LLMKeySet('智谱AI api', 'zhipu')

        # 将所有组件添加到垂直布局中
        cards_layout.addWidget(kimi_card)
        cards_layout.addWidget(zhipu_card)
        # 添加一些垂直间距
        cards_layout.addStretch(1)

        # 将垂直布局添加到主布局中
        main_layout.addLayout(cards_layout, 1)

        # 添加一个水平伸缩项，使卡片占用左半部分
        main_layout.addStretch(1)

        self.setLayout(main_layout)


class TranslationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        tips_label = CaptionLabel("请填写服务商提供的API Key，在翻译任务中可以免除算力，所有Key只会保存在本地。")
        main_layout.addWidget(tips_label)

        title_layout = QHBoxLayout()
        title_label = BodyLabel("翻译API Key")
        tutorial_link = HyperlinkLabel("设置教程")
        tutorial_link.setUrl('xdd')

        title_layout.addWidget(title_label)
        title_layout.addWidget(tutorial_link)
        main_layout.addLayout(title_layout)

        self.baidu_key = TranslateKeySet("百度翻译")
        self.deepl_key = TranslateKeySet("DeepL翻译")
        self.google_key = TranslateKeySet("谷歌翻译")
        self.microsoft_key = TranslateKeySet("微软翻译")
        main_layout.addWidget(self.baidu_key)
        main_layout.addWidget(self.deepl_key)
        main_layout.addWidget(self.google_key)
        main_layout.addWidget(self.microsoft_key)

        self.setLayout(main_layout)


class ProxyPage(QWidget):
    def __init__(self,setting, parent=None):
        super().__init__(parent=parent)
        self.setting = setting
        self.setup_ui()

    def setup_ui(self):
        # 添加代理设置
        main_layout = QVBoxLayout()
        self.no_proxy_radio = RadioButton("无代理", self)
        self.use_proxy_radio = RadioButton("使用代理", self)
        # self.use_proxy_radio.toggled.connect(self.save_proxy)

        # 默认选中"无代理"
        self.no_proxy_radio.setChecked(True)

        main_layout.addWidget(self.no_proxy_radio)
        main_layout.addStretch(1)
        main_layout.addWidget(self.use_proxy_radio)

        self.proxy_address = LineEdit(self)
        self.proxy_address.setPlaceholderText("代理地址，比如http://127.0.0.1:8087")
        self.save_btn = PushButton("保存")
        self.save_btn.clicked.connect(self.save_proxy)
        main_layout.addWidget(self.proxy_address)
        main_layout.addStretch(1)
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)

    def save_proxy(self):
        if self.no_proxy_radio.isChecked():
            config.proxy = None
        else:
            proxy = self.proxy_address.text()
            if not re.match(r'^(http|sock)', proxy, re.I):
                proxy = f'http://{proxy}'
            if not re.match(r'^(http|sock)(s|5)?://(\d+\.){3}\d+:\d+', proxy, re.I):
                question = tools.show_popup('请确认代理地址是否正确？' if config.defaulelang == 'zh' else 'Please make sure the proxy address is correct', """你填写的网络代理地址似乎不正确
            一般代理/vpn格式为 http://127.0.0.1:数字端口号
            如果不知道什么是代理请勿随意填写
            如果确认代理地址无误，请点击 Yes 继续执行""" if config.defaulelang == 'zh' else 'The network proxy address you fill in seems to be incorrect, the general proxy/vpn format is http://127.0.0.1:port, if you do not know what is the proxy please do not fill in arbitrarily, ChatGPT and other api address please fill in the menu - settings - corresponding configuration. If you confirm that the proxy address is correct, please click Yes to continue.')
                if question != QMessageBox.Yes:
                    self.update_status('stop')
                    return
            config.proxy = proxy
        self.setting.setValue("proxy", config.proxy)
        config.logger.info(f"proxy/use_proxy: {self.use_proxy_radio.isChecked()}")
        config.logger.info(f"proxy/address: {config.proxy}")


class SettingInterface(QWidget):
    def __init__(self, text: str, setting, parent=None):
        super().__init__(parent=parent)
        self.setting = setting
        self.setObjectName(text.replace(' ', '-'))
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.localModelPage = LocalModelPage(setting=self.setting)
        self.llmConfigPage = LLMConfigPage(self)
        self.translationPage = TranslationPage(self)
        self.proxyPage = ProxyPage(setting=self.setting)

        self.tabs.addTab(self.localModelPage, "本地模型")
        self.tabs.addTab(self.llmConfigPage, "LLM配置")
        self.tabs.addTab(self.translationPage, "翻译配置")
        self.tabs.addTab(self.proxyPage, "代理设置")

        layout.addWidget(self.tabs)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingInterface('setting', setting=QSettings("Locoweed", "LinLInTrans"))
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
