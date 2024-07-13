import os
import re
import sys

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtNetwork import QNetworkProxy, QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QTabWidget, QTableWidgetItem, QApplication, QFileDialog, QAbstractItemView, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (TableWidget, BodyLabel, CaptionLabel, HyperlinkLabel, SubtitleLabel, ToolButton, RadioButton, LineEdit, PushButton, InfoBar, InfoBarPosition, FluentIcon)

from nice_ui.configure import config
from nice_ui.ui.style import AppCardContainer, LLMKeySet, TranslateKeySet
from nice_ui.util import tools
from orm.queries import PromptsOrm


class LocalModelPage(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
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
        self.cpp_model_table.setEditTriggers(QAbstractItemView.NoEditTriggers)


        # FasterWhisper 模型列表
        self.faster_model_title = BodyLabel("FasterWhisper 模型列表")
        self.faster_model_table = TableWidget(self)
        self.faster_model_table.setColumnCount(6)
        self.faster_model_table.setHorizontalHeaderLabels(["模型", "语言支持", "准确度", "模型大小", "运行内存", "识别速度"])
        self.faster_model_table.verticalHeader().setVisible(False)
        self.faster_model_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

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
            self.settings.setValue("models_path", config.models_path)

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
    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setup_ui()
        self.prompts_orm = PromptsOrm()
        self._init_table()

    def setup_ui(self):
        # 创建垂直布局来容纳所有组件
        main_layout = QVBoxLayout()
        card_api_layout = QHBoxLayout()


        api_key_title = SubtitleLabel("API Key")
        main_layout.addWidget(api_key_title)

        cards_layout = QVBoxLayout()

        # 创建两个 OpenAIApiKeyCard 实例
        kimi_card = LLMKeySet('kimi', 'hurl',self)
        zhipu_card = LLMKeySet('zhipu', 'zhipu',self)
        qwen_card = LLMKeySet('qwen', 'qwen',self)

        # 将所有组件添加到垂直布局中
        cards_layout.addWidget(kimi_card)
        cards_layout.addWidget(zhipu_card)
        cards_layout.addWidget(qwen_card)
        # 添加一些垂直间距
        cards_layout.addStretch(1)

        # 将垂直布局添加到主布局中
        card_api_layout.addLayout(cards_layout, 1)

        # 添加一个水平伸缩项，使卡片占用左半部分
        card_api_layout.addStretch(1)

        main_layout.addLayout(card_api_layout)
        prompts_layout =QHBoxLayout()
        prompts_title = SubtitleLabel("提示词")
        # 刷新提示词

        refresh_btn = ToolButton("刷新")
        refresh_btn.setIcon(FluentIcon.ROTATE)

        refresh_btn.clicked.connect(self._refresh_table_data)
        prompts_layout.addWidget(prompts_title)
        prompts_layout.addWidget(refresh_btn)

        main_layout.addLayout(prompts_layout)
        # 创建一个table

        self.prompts_table = TableWidget(self)
        self.prompts_table.setColumnCount(5)
        self.prompts_table.setHorizontalHeaderLabels(["主键id", "提示词名字", "提示词", "修改", "删除"])
        self.prompts_table.verticalHeader().setVisible(False)
        self.prompts_table.setColumnWidth(0, 150)  # 设置第一列宽度
        self.prompts_table.setColumnWidth(1, 150)  # 设置第二列宽度
        self.prompts_table.setColumnWidth(2, 150)  # 设置第三列宽度
        self.prompts_table.setColumnWidth(3, 100)  # 设置第四列宽度
        self.prompts_table.setColumnWidth(4, 100)  # 设置第五列宽度
        self.prompts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 设置表格为不可编辑状态
        # self.prompts_table.setSelectionBehavior(self.prompts_table.SelectRows)  # 设置表格的选择行为为选择整行，用户在选择表格中的某个单元格时，整行都会被选中。
        main_layout.addWidget(self.prompts_table)
        self.setLayout(main_layout)

    def _init_table(self):
        all_prompts = self.prompts_orm.get_data_with_id_than_one()
        for prompt in all_prompts:
            self.add_prompt(prompt_id=prompt.id, prompt_name=prompt.prompt_name, prompt_content=prompt.prompt_content)


    def add_prompt(self, prompt_id, prompt_name, prompt_content):
        row = self.prompts_table.rowCount()
        self.prompts_table.insertRow(row)
        self.prompts_table.setItem(row, 0, QTableWidgetItem(str(prompt_id)))
        self.prompts_table.setItem(row, 1, QTableWidgetItem(str(prompt_name)))
        self.prompts_table.setItem(row, 2, QTableWidgetItem(str(prompt_content)))
        edit_btn = PushButton("修改")
        edit_btn.clicked.connect(self._edit_prompt(edit_btn))
        self.prompts_table.setCellWidget(row, 3, edit_btn)
        delete_btn = PushButton("删除")
        delete_btn.clicked.connect(self._delete_row(delete_btn))
        self.prompts_table.setCellWidget(row, 4, delete_btn)

    def _refresh_table_data(self):
        self.prompts_table.setRowCount(0)  # 清空表格
        all_prompts = self.prompts_orm.get_data_with_id_than_one()  # 获取最新数据
        for prompt in all_prompts:
            self.add_prompt(prompt_id=prompt.id, prompt_name=prompt.prompt_name, prompt_content=prompt.prompt_content)  #

    def _delete_row(self, button):
        def delete_row():
            button_row = self.prompts_table.indexAt(button.pos()).row()
            print(f"删除第{button_row}行数据")
            key_id = self.prompts_table.item(button_row, 0).text()
            self.prompts_orm.delete_table_prompt(key_id)
            self.prompts_table.removeRow(button_row)
        return delete_row


    def _edit_prompt(self, button):
        def edit_row():
            button_row = self.prompts_table.indexAt(button.pos()).row()
            config.logger.info(f"编辑prompt,所在行:{button_row} ")
            key_id = self.prompts_table.item(button_row, 0).text()
            prompt_name = self.prompts_table.item(button_row, 1).text()
            prompt_content = self.prompts_table.item(button_row, 2).text()
            # todo: 弹出编辑对话框，修改后回写入数据库
            # prompt_name, prompt_content = tools.edit_prompt(prompt_name, prompt_content)


        return edit_row



class TranslationPage(QWidget):
    def __init__(self,settings, parent=None):
        super().__init__(parent=parent)
        self.settings = settings
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

        self.baidu_key = TranslateKeySet("baidu",self)
        self.deepl_key = TranslateKeySet("deepl",self)
        self.google_key = TranslateKeySet("google",self)
        main_layout.addWidget(self.baidu_key)
        main_layout.addWidget(self.deepl_key)
        main_layout.addWidget(self.google_key)


        self.setLayout(main_layout)


class ProxyPage(QWidget):
    def __init__(self, setting, parent=None):
        super().__init__(parent=parent)
        self.settings = setting
        self.setup_ui()

    def setup_ui(self):
        # 添加代理设置
        layout = QVBoxLayout()

        # 创建单选框
        self.no_proxy_radio = RadioButton("无代理")
        self.use_proxy_radio = RadioButton("使用代理")

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.no_proxy_radio)
        radio_layout.addWidget(self.use_proxy_radio)
        layout.addLayout(radio_layout)

        # 创建代理输入框
        self.proxy_input = LineEdit()
        self.proxy_input.setPlaceholderText("输入代理地址 (例如: http://127.0.0.1:8080)")
        layout.addWidget(self.proxy_input)

        # 创建应用代理按钮
        self.apply_button = PushButton("保存")
        self.apply_button.clicked.connect(self.apply_proxy)
        layout.addWidget(self.apply_button)

        # 创建显示当前代理设置按钮
        self.show_settings_button = PushButton("显示当前代理设置")
        self.show_settings_button.clicked.connect(self.show_current_settings)
        layout.addWidget(self.show_settings_button)

        # 添加测试按钮
        self.test_button = PushButton("测试代理", self)
        self.test_button.clicked.connect(self.test_proxy)
        layout.addWidget(self.test_button)

        self.setLayout(layout)

        # 加载保存的设置
        self.load_settings()

        # 连接单选框信号
        self.no_proxy_radio.toggled.connect(self.toggle_proxy_input)
        self.use_proxy_radio.toggled.connect(self.toggle_proxy_input)

    def load_settings(self):
        use_proxy = self.settings.value("use_proxy", False, type=bool)
        proxy = self.settings.value("proxy", "", type=str)  # 实际使用的
        proxy_text = self.settings.value("proxy_text", "", type=str)  # 仅做文本显示

        if use_proxy:
            self.use_proxy_radio.setChecked(True)
        else:
            self.no_proxy_radio.setChecked(True)

        self.proxy_input.setText(proxy_text)
        self.toggle_proxy_input()

    def toggle_proxy_input(self):
        self.proxy_input.setEnabled(self.use_proxy_radio.isChecked())

    def apply_proxy(self):
        use_proxy = self.use_proxy_radio.isChecked()

        if use_proxy:
            proxy = self.proxy_input.text()
            if not re.match(r'^(http|sock)', proxy, re.I):
                proxy = f'http://{proxy}'
            if not re.match(r'^(http|sock)(s|5)?://(\d+\.){3}\d+:\d+', proxy, re.I):
                question = tools.show_popup('请确认代理地址是否正确？' if config.defaulelang == 'zh' else 'Please make sure the proxy address is correct', """你填写的网络代理地址似乎不正确
                       一般代理/vpn格式为 http://127.0.0.1:数字端口号
                       如果不知道什么是代理请勿随意填写
                       如果确认代理地址无误，请点击 Yes 继续执行""" if config.defaulelang == 'zh' else 'The network proxy address you fill in seems to be incorrect, the general proxy/vpn format is http://127.0.0.1:port, if you do not know what is the proxy please do not fill in arbitrarily, ChatGPT and other api address please fill in the menu - settings - corresponding configuration. If you confirm that the proxy address is correct, please click Yes to continue.')

            if not proxy:
                InfoBar.warning(title="警告", content="请输入有效的代理地址", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=2000, parent=self, )
                return
            self.settings.setValue("use_proxy", use_proxy)
            self.settings.setValue("proxy", proxy)
            self.settings.setValue("proxy_text", proxy)
        else:
            proxy = ""
            self.settings.setValue("use_proxy", use_proxy)
            self.settings.setValue("proxy", proxy)
        # 保存设置

        # 应用代理设置到应用程序
        try:
            if use_proxy:
                # 解析代理地址
                protocol, address = proxy.split("://")
                host, port = address.split(":")
                port = int(port)

                # 设置全局代理
                proxy_obj = QNetworkProxy()
                if protocol.lower() == "http":
                    proxy_obj.setType(QNetworkProxy.HttpProxy)
                elif protocol.lower() == "socks5":
                    proxy_obj.setType(QNetworkProxy.Socks5Proxy)
                else:
                    raise ValueError("Unsupported proxy protocol")

                proxy_obj.setHostName(host)
                proxy_obj.setPort(port)
                QNetworkProxy.setApplicationProxy(proxy_obj)
            else:
                # 这里添加取消代理的代码
                QNetworkProxy.setApplicationProxy(QNetworkProxy.NoProxy)

            InfoBar.success(title="成功", content="代理设置已保存", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=2000, parent=self, )
        except Exception as e:
            InfoBar.error(title="错误", content=f"设置代理时出错: {str(e)}", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=2000, parent=self, )

    def show_current_settings(self):
        use_proxy = self.settings.value("use_proxy", False, type=bool)
        proxy = self.settings.value("proxy", "", type=str)

        if use_proxy:
            message = f"当前使用代理: {proxy}"
        else:
            message = "当前未使用代理"

        InfoBar.info(title="当前代理设置", content=message, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=self, )

    def test_proxy(self):
        manager = QNetworkAccessManager(self)
        manager.finished.connect(self.handle_response)

        request = QNetworkRequest(QUrl("https://www.google.com/"))
        manager.get(request)

    def handle_response(self, reply):
        if reply.error():
            InfoBar.error(title='错误', content=f"测试失败: {reply.errorString()}", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=self)
        else:
            response = reply.readAll().data().decode()
            InfoBar.success(title='成功', content=f"测试成功: {response}", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=self)


class SettingInterface(QWidget):
    def __init__(self, text: str, parent=None,settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setObjectName(text.replace(' ', '-'))
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        self.localModelPage = LocalModelPage(settings=self.settings)
        self.llmConfigPage = LLMConfigPage(settings=self.settings)
        self.translationPage = TranslationPage(settings=self.settings)
        self.proxyPage = ProxyPage(setting=self.settings)

        self.tabs.addTab(self.localModelPage, "本地模型")
        self.tabs.addTab(self.llmConfigPage, "LLM配置")
        self.tabs.addTab(self.translationPage, "翻译配置")
        self.tabs.addTab(self.proxyPage, "代理设置")

        layout.addWidget(self.tabs)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingInterface('setting', settings=QSettings("Locoweed", "LinLInTrans"))
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
