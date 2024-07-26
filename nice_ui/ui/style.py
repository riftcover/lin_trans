from PySide6.QtCore import Qt, QSettings, QSize, QTime
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication, QTableWidgetItem, QSizePolicy, QTimeEdit, QTextEdit
from PySide6.QtWidgets import QWidget, QButtonGroup
from qfluentwidgets import (CaptionLabel, RadioButton, InfoBarPosition, InfoBar, TableWidget, TransparentToolButton, FluentIcon)
from qfluentwidgets import (CardWidget, LineEdit, PrimaryPushButton, BodyLabel, HyperlinkLabel)

from agent import translate_api_name
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

    def __init__(self, settings: QSettings, lineedit: LineEdit, api_key: str, parent=None):
        super().__init__(parent)
        self.setText("保存")
        self.settings = settings
        self.lineEdit = lineedit
        self.clicked.connect(lambda: self.save_api_key(api_key))

    def save_api_key(self, api_key):
        # 实现保存API Key的逻辑，在主窗口的QSettings中保存
        key_text = self.lineEdit.text()
        self.settings.setValue(api_key, key_text)
        InfoBar.success(title="成功", content="API已保存", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=2000,
                        parent=self.parent().parent(), )


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
        在父窗口中要传入settings，settings是QSettings对象
        """
        # 创建主布局
        main_layout = QVBoxLayout()

        # 第一排布局
        key_name = translate_api_name.get(api_key)
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
        save_button = SaveButton(self.parent().settings, self.api_key_input, api_key)
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
        在父窗口中要传入settings，settings是QSettings对象
        """
        main_layout = QHBoxLayout()
        title_label = BodyLabel(translate_api_name.get(api_key))
        self.api_key_input = KeyLineEdit(self.parent().settings.value(api_key, type=str))
        save_button = SaveButton(self.parent().settings, self.api_key_input, api_key)
        # 将两排布局添加到主布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.api_key_input)
        main_layout.addWidget(save_button)

        # 设置卡片的内容布局
        self.setLayout(main_layout)


class LTimeEdit(QTimeEdit):
    def __init__(self, time_str, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("hh:mm:ss,zzz")
        time = QTime.fromString(time_str, "hh:mm:ss,zzz")
        self.setTime(time)

    def stepBy(self, steps):
        current_time = self.time()
        new_time = current_time.addMSecs(steps * 500)  # 每次调整500毫秒
        self.setTime(new_time)


class LinLineEdit(QTextEdit):
    """
    字幕文本编辑组件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)  # 初始设置为只读
        self.setLineWrapMode(QTextEdit.WidgetWidth)  # 设置自动换行模式
        self.setAcceptRichText(False)  # 禁用富文本，只接受纯文本
        self.mousePressEvent = self.on_mouse_press  # 重写鼠标点击事件

    def on_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.setReadOnly(False)  # 点击后设置为可编辑
        super().mousePressEvent(event)


class SubtitleTable(TableWidget):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

        self.initUI()

    def load_subtitle(self):
        """
        加载字幕文件，返回字幕列表
        :return:[('00:00:00,166', '00:00:01,166', '你好，世界！')]
                [start_time, end_time, content]
        """
        subtitles = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            # 跳过行号
            if lines[i].strip().isdigit():
                i += 1

            # 读取时间范围
            time_range = lines[i].strip()
            try:
                start_time, end_time = time_range.split(' --> ')
            except ValueError:
                print(f"Error parsing time range: {time_range}")
                i += 1
                continue
            i += 1

            # 读取字幕内容
            english_content = []
            if i < len(lines) and lines[i].strip():
                english_content.append(lines[i].strip())
                i += 1

            chinese_content = []
            if i < len(lines) and lines[i].strip():
                chinese_content.append(lines[i].strip())
                i += 1

            english_content_str = ' '.join(english_content)
            chinese_content_str = ' '.join(chinese_content)

            # 添加到字幕列表
            subtitles.append((start_time, end_time, english_content_str, chinese_content_str))

            # 跳过空行
            while i < len(lines) and not lines[i].strip():
                i += 1
        config.logger.debug(f"字幕文件行数: {len(subtitles)}")
        return subtitles

    def initUI(self):
        self.setColumnCount(6)
        # self.setHorizontalHeaderLabels(["操作", "行号", "时间", "时长", "原文", "译文", "编辑"])
        self.setHorizontalHeaderLabels(["操作", "行号", "时间", "原文", "译文", "编辑"])

        self.setColumnWidth(0, 50)
        self.setColumnWidth(1, 50)
        self.setColumnWidth(2, 200)
        self.setColumnWidth(3, 300)
        self.setColumnWidth(4, 300)
        self.setColumnWidth(5, 50)

        # 设置表格样式
        # self.setShowGrid(False)
        # self.verticalHeader().setVisible(False)

        # 加载字幕文件
        for i, j in enumerate(self.load_subtitle()):
            self._add_row(i, j)

    def _add_row(self, rowPosition: int = None, srt_data: tuple = None):

        self.insertRow(rowPosition)

        # 第一列：操作按钮
        operationLayout = QVBoxLayout()
        operationLayout.setSpacing(2)
        operationLayout.setContentsMargins(2, 2, 2, 2)

        playButton = TransparentToolButton(FluentIcon.PLAY)
        cutButton = TransparentToolButton(FluentIcon.CUT)

        # 设置按钮的固定大小
        button_size = QSize(24, 24)
        playButton.setFixedSize(button_size)
        cutButton.setFixedSize(button_size)

        operationLayout.addWidget(playButton)
        operationLayout.addWidget(cutButton)
        operationLayout.addStretch()

        operationWidget = QWidget()
        operationWidget.setLayout(operationLayout)
        operationWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.setCellWidget(rowPosition, 0, operationWidget)

        # 第二列：行号
        self.setItem(rowPosition, 1, QTableWidgetItem(str(rowPosition + 1)))

        # 第三列：时间
        timeLayout = QVBoxLayout()
        startTime = LTimeEdit(srt_data[0], self)
        startTime.setObjectName("startTime")
        endTime = LTimeEdit(srt_data[1], self)
        endTime.setObjectName("endTime")
        timeLayout.addWidget(startTime)
        timeLayout.addWidget(endTime)
        timeWidget = QWidget()
        timeWidget.setLayout(timeLayout)
        self.setCellWidget(rowPosition, 2, timeWidget)

        # # 第四列：时长
        # self.setItem(rowPosition, 3, QTableWidgetItem("0.0s"))

        # 第五列：原文
        # 设置按钮的固定大小
        your_text = LinLineEdit()
        your_text.setText(srt_data[2])
        text_size = QSize(190, 50)
        your_text.setFixedSize(text_size)
        self.setCellWidget(rowPosition, 3, your_text)

        # 第六列：译文
        #todo: 待添加
        translated_text = LinLineEdit()
        translated_text.setText(srt_data[3])
        translated_text.setFixedSize(text_size)
        self.setCellWidget(rowPosition, 4, translated_text)

        # 第七列：编辑按钮
        editLayout = QVBoxLayout()
        editLayout.setSpacing(2)
        editLayout.setContentsMargins(2, 2, 2, 2)

        deleteButton = TransparentToolButton(FluentIcon.DELETE)
        deleteButton.setObjectName("deleteButton")
        deleteButton.clicked.connect(lambda _, r=rowPosition: self._delete_row(r))
        addButton = TransparentToolButton(FluentIcon.ADD)
        addButton.setObjectName("addButton")
        addButton.clicked.connect(lambda _, r=rowPosition: self._insert_row_below(r))

        deleteButton.setFixedSize(button_size)
        addButton.setFixedSize(button_size)

        editLayout.addWidget(deleteButton)
        editLayout.addWidget(addButton)
        editLayout.addStretch()

        editWidget = QWidget()
        editWidget.setLayout(editLayout)
        editWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.setCellWidget(rowPosition, 5, editWidget)

        # 设置每行的高度为90
        self.setRowHeight(rowPosition, 90)

    def update_row_numbers(self):
        # 更新行号
        for row in range(self.rowCount()):
            item = self.item(row, 1)
            if item:
                item.setText(str(row + 1))

            editWidget = self.cellWidget(row, 5)
            if editWidget:
                deleteButton = editWidget.findChild(TransparentToolButton, "deleteButton")
                addButton = editWidget.findChild(TransparentToolButton, "addButton")
                if deleteButton:
                    deleteButton.clicked.disconnect()
                    deleteButton.clicked.connect(lambda _, r=row: self._delete_row(r))
                if addButton:
                    addButton.clicked.disconnect()
                    addButton.clicked.connect(lambda _, r=row: self._insert_row_below(r))

    def _delete_row(self, row):
        self.removeRow(row)
        self.update_row_numbers()

    def _insert_row_below(self, row):
        new_row_position = row + 1
        end_time_edit = self.cellWidget(row, 2).findChild(LTimeEdit, "endTime")
        config.logger.debug(f"end_time_edit: {end_time_edit}")
        if end_time_edit:
            # 获取当前行的结束时间
            current_row_end_time = end_time_edit.time()
        else:
            current_row_end_time = QTime(0, 0)
            config.logger.error("Warning: Could not find endTime widget")
        # 将结束时间转换为字符串
        start_time_str = current_row_end_time.toString("hh:mm:ss,zzz")
        config.logger.debug(f"start_time_str: {start_time_str}")

        # 计算新的结束时间（加500毫秒）
        new_end_time = current_row_end_time.addMSecs(500)
        end_time_str = new_end_time.toString("hh:mm:ss,zzz")

        # 创建新的srt_data元组
        new_srt_data = (start_time_str, end_time_str, '')

        # 在当前行下方插入新行
        self._add_row(new_row_position, new_srt_data)

        # 更新行号
        self.update_row_numbers()


if __name__ == '__main__':
    import sys

    patt = r'D:\dcode\lin_trans\result\tt1\tt.srt'
    app = QApplication(sys.argv)
    card = SubtitleTable(patt)
    # print(card.load_subtitle())
    card.show()
    sys.exit(app.exec())
