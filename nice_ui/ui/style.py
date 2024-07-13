from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication
from PySide6.QtWidgets import QWidget, QButtonGroup
from qfluentwidgets import (CaptionLabel, RadioButton)
from qfluentwidgets import (CardWidget, LineEdit, PrimaryPushButton, BodyLabel, HyperlinkLabel)

from nice_ui.configure import config


# 这里放的是自定义样式组件

class AppCard(CardWidget):
    """ App card
    用在本地识别页，创建whisper选择卡片
     """

    def __init__(self, title, content, button_status: bool = False, parent=None):
        super().__init__(parent)

        self.radioButton = RadioButton(title, self)
        self.contentLabel = CaptionLabel(content, self)
        self.radioButton.setChecked(button_status)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(73)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")

        self.hBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.hBoxLayout.setSpacing(15)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.radioButton, 0, Qt.AlignVCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignVCenter)
        self.vBoxLayout.setAlignment(Qt.AlignVCenter)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.addStretch(1)


class AppCardContainer(QWidget):
    """ Container for App cards """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QHBoxLayout(self)
        self.buttonGroup = QButtonGroup(self)
        self.buttonGroup.setExclusive(True)  # 确保只有一个按钮可以被选中

    def addAppCard(self, title, content, button_status=False):
        card = AppCard(title, content, button_status, self)
        self.layout.addWidget(card)
        self.buttonGroup.addButton(card.radioButton)
        return card


class KeyLineEdit(LineEdit):
    """ Key Line Edit
    用在llm配置页 创建api key 输入框
    """

    def __init__(self, edit_text, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("请输入Api Key")
        self.setClearButtonEnabled(True)
        self.setText(edit_text)


class SaveButton(PrimaryPushButton):
    """ Key Button
    用在llm配置页 创建api key 按钮
    """

    def __init__(self, setting: QSettings, lineedit: LineEdit, api_key: str, parent=None):
        super().__init__(parent)
        self.setText("保存")
        self.lineEdit = lineedit
        self.clicked.connect(lambda: self.save_api_key(api_key))

    def save_api_key(self, api_key):
        # 实现保存API Key的逻辑，在主窗口的QSettings中保存
        key_text = self.lineEdit.text()
        self.parent().settings.setValue(api_key, key_text)


class LLMKeySet(QWidget):
    """ LLM Key Set
    用在llm配置页 创建api key 卡片
    """

    def __init__(self, api_key: str, url: str, parent=None):
        super().__init__(parent)
        """
        key_name，api_key是在config.translate_api_name中配对的值{api_key：key_name}
        key_name: 显示在卡片上的API名称
        api_key: 保存到QSettings中的API名称
        url: 教程链接
        """
        # 创建主布局
        main_layout = QVBoxLayout()

        # 第一排布局
        key_name = config.translate_api_name.get(api_key)
        config.logger.debug(f"key_name: {key_name}")
        title_layout = QHBoxLayout()
        title_label = BodyLabel(key_name)
        tutorial_link = HyperlinkLabel("设置教程")
        tutorial_link.setUrl(url)
        # tutorial_link.setIcon(FluentIcon.QUESTION)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(tutorial_link)

        # 第二排布局
        input_layout = QHBoxLayout()
        self.api_key_input = KeyLineEdit(self.parent().settings.value(api_key, type=str))
        save_button = SaveButton(self.parent().settings, self.api_key_input, api_key, self)
        input_layout.addWidget(self.api_key_input)
        input_layout.addWidget(save_button)

        # 将两排布局添加到主布局
        main_layout.addLayout(title_layout)
        main_layout.addLayout(input_layout)

        # 设置卡片的内容布局
        self.setLayout(main_layout)



class TranslateKeySet(QWidget):
    """ Translate Key Set
    用在翻译页 创建api key 卡片

    """

    def __init__(self, api_key: str, parent=None):
        super().__init__(parent)
        """
        key_name，api_key是在config.translate_api_name中配对的值{api_key：key_name}
        key_name: 显示在卡片上的API名称
        api_key: 保存到QSettings中的API名称
        """
        main_layout = QHBoxLayout()
        title_label = BodyLabel(config.translate_api_name.get(api_key))
        self.api_key_input = KeyLineEdit(self.parent().settings.value(api_key, type=str))
        save_button = SaveButton(self.parent().settings, self.api_key_input, api_key, self)
        # 将两排布局添加到主布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.api_key_input)
        main_layout.addWidget(save_button)

        # 设置卡片的内容布局
        self.setLayout(main_layout)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    card = LLMKeySet()
    card.show()
    sys.exit(app.exec())
