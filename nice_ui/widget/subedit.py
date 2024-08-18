from PySide6.QtWidgets import QApplication, QMainWindow, QTableView, QStyledItemDelegate, QPushButton, QWidget, QVBoxLayout, QStyle, QStyleOptionButton, \
    QStyleOptionSpinBox, QStyleOptionViewItem, QTimeEdit, QTextEdit, QLabel
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize, QRect, QPoint, QTime, QSignalBlocker, QTimer, QAbstractListModel, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QStandardItemModel, QRegion
import sys

from nice_ui.configure import config
from nice_ui.ui.style import LinLineEdit, LTimeEdit
from vendor.qfluentwidgets import FluentIcon, CheckBox, TransparentToolButton, ToolTipFilter, ToolTipPosition

class DataLoader(QThread):
    data_loaded = Signal(list)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        data = self.load_subtitle()
        self.data_loaded.emit(data)

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
                config.logger.error(f"Error parsing time range: {time_range}")
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

class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._persistent_editors = {}

    def createEditor(self, parent, option, index):
        if index.column() == 0:  # 勾选框
            return self.create_checkbox(parent)
        elif index.column() == 1:  # 操作按钮
            return self.create_operation_widget(parent)
        elif index.column() == 2:  # 行号
            return self.create_row_number_label(parent, index.row())
        elif index.column() == 3:  # 时间
            return self.create_time_widget(parent)
        elif index.column() in [4, 5]:  # 原文和译文
            return self.create_text_edit(parent)
        elif index.column() == 6:  # 编辑按钮
            return self.create_edit_widget(parent, index.row())
        return super().createEditor(parent, option, index)

    def create_checkbox(self, parent):
        return CheckBox(parent)

    def create_operation_widget(self, parent):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        button_size = QSize(15, 15)
        play_button = TransparentToolButton(FluentIcon.PLAY)
        cut_button = TransparentToolButton(FluentIcon.CUT)
        play_button.setFixedSize(button_size)
        cut_button.setFixedSize(button_size)

        layout.addWidget(play_button)
        layout.addWidget(cut_button)
        return widget

    def create_row_number_label(self, parent, row):
        label = QLabel(str(row + 1), parent)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0;")
        return label

    def create_time_widget(self, parent):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        start_time = LTimeEdit(parent)
        start_time.setObjectName("start_time")
        end_time = LTimeEdit(parent)
        end_time.setObjectName("end_time")
        layout.addWidget(start_time)
        layout.addWidget(end_time)
        return widget

    def create_text_edit(self, parent):
        text_edit = LinLineEdit(parent)
        text_edit.setFixedSize(QSize(190, 50))
        return text_edit

    def create_edit_widget(self, parent, row):
        widget = QWidget(parent)
        button_size = QSize(15, 15)
        edit_layout = QVBoxLayout(widget)
        edit_layout.setSpacing(2)
        edit_layout.setContentsMargins(2, 2, 2, 2)

        delete_button = TransparentToolButton(FluentIcon.DELETE)
        delete_button.setToolTip("删除本行字幕")
        delete_button.installEventFilter(ToolTipFilter(delete_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        delete_button.setObjectName("delete_button")
        delete_button.clicked.connect(lambda _, r=row: self._delete_row(r))
        add_button = TransparentToolButton(FluentIcon.ADD)
        add_button.setObjectName("add_button")
        add_button.setToolTip("下方添加一行")
        add_button.installEventFilter(ToolTipFilter(add_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        add_button.clicked.connect(lambda _, r=row: self._insert_row_below(r))

        delete_button.setFixedSize(button_size)
        add_button.setFixedSize(button_size)

        # 移动译文上一行、下一行
        down_row_button = TransparentToolButton(FluentIcon.DOWN)
        down_row_button.setObjectName("down_button")
        down_row_button.setToolTip("移动译文到下一行")
        down_row_button.installEventFilter(ToolTipFilter(down_row_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        down_row_button.clicked.connect(lambda _, r=row: self._move_row_down(r))
        up_row_button = TransparentToolButton(FluentIcon.UP)
        up_row_button.setObjectName("up_button")
        up_row_button.setToolTip("移动译文到上一行")
        up_row_button.installEventFilter(ToolTipFilter(up_row_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        up_row_button.clicked.connect(lambda _, r=row: self._move_row_up(r))

        down_row_button.setFixedSize(button_size)
        up_row_button.setFixedSize(button_size)

        edit_layout.addWidget(down_row_button)
        edit_layout.addWidget(up_row_button)

        edit_layout.addWidget(delete_button)
        edit_layout.addWidget(add_button)
        # edit_layout.addStretch()

        return widget

    def create_tool_button(self, icon, tooltip, row):
        button = TransparentToolButton(icon)
        button.setToolTip(tooltip)
        button.installEventFilter(ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        return button

    def setEditorData(self, editor, index):
        if index.column() == 0:
            # 勾选框
            editor.setChecked(index.data(Qt.CheckStateRole) == Qt.Checked)
        elif index.column() == 1:
            # 操作按钮
            pass
        elif isinstance(editor, QLabel) and index.column() == 2:
            # 行号
            editor.setText(str(index.row() + 1))
        elif index.column() == 3:
            # 时间
            times = index.data(Qt.UserRole)
            start_time =editor.findChild(LTimeEdit, "start_time")
            editor.findChild(LTimeEdit, "start_time").initTime(times[0])
            editor.findChild(LTimeEdit, "end_time").initTime(times[1])
        elif index.column() in [4, 5]:
            # 原文和译文
            # print(index.data(Qt.EditRole))
            editor.setText(index.data(Qt.EditRole))
        elif index.column() == 6:
            # 编辑按钮
            pass
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == 0:
            # 勾选框
            model.setData(index, editor.isChecked(), Qt.CheckStateRole)
        elif index.column() == 1:
            # 操作按钮
            pass
        elif index.column() == 2:
            # 行号
            pass
        elif index.column() == 3:
            # 时间
            start_time = editor.findChild(LTimeEdit, "start_time").time().toString()
            end_time = editor.findChild(LTimeEdit, "end_time").time().toString()
            model.setData(index, f"{start_time} - {end_time}",Qt.UserRole)
        elif index.column() in (4, 5):
            # 原文和译文
            model.setData(index, editor.toText(), Qt.EditRole)
        elif index.column() == 6:
            # 编辑按钮
            pass
        else:
            super().setModelData(editor, model, index)

    def paint(self, painter, option, index):
        if index.column() in [0, 1, 2, 3, 4, 5, 6]:
            # 为这些列创建持久化的编辑器
            if index not in self._persistent_editors:
                editor = self.createEditor(self.parent(), option, index)
                self.setEditorData(editor, index)
                self.parent().setIndexWidget(index, editor)
                self._persistent_editors[index] = editor
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        # 返回固定大小以提高性能
        return QSize(50, 80)

    # def sizeHint(self, option, index):  #     if index.column() == 0:  #         return QSize(50, 80)  #     elif index.column() == 1:  #         return QSize(50, 80)  #     elif index.column() == 2:  #         return QSize(50, 80)  #     return super().sizeHint(option, index)

class SubtitleModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent):
        return 7

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 3:  # 时间列
                return f"{self._data[row][0]} - {self._data[row][1]}"
            elif col == 4:  # 原文列
                return self._data[row][2]
            elif col == 5:  # 译文列
                return self._data[row][3]
        elif role == Qt.UserRole:
            if col == 3:  # 时间列
                return (self._data[row][0], self._data[row][1])

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()

        if role == Qt.EditRole:
            if col == 4:  # 原文列
                self._data[row] = (self._data[row][0], self._data[row][1], value, self._data[row][3])
            elif col == 5:  # 译文列
                self._data[row] = (self._data[row][0], self._data[row][1], self._data[row][2], value)
        elif role == Qt.UserRole:
            if col == 3:  # 时间列
                self._data[row] = (value[0], value[1], self._data[row][2], self._data[row][3])

        self.dataChanged.emit(index, index, [role])
        return True

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable
class SubtitleTable(QTableView):
    def __init__(self,file_path: str):
        super().__init__()
        self.file_path = file_path
        self.data_loader = DataLoader(file_path)
        self.data_loader.data_loaded.connect(self.on_data_loaded)
        self.data_loader.start()



    def on_data_loaded(self, data):
        self.all_data = data
        self.model = SubtitleModel(self.all_data)
        # ln = len(self.all_data)
        # self.model = QStandardItemModel(ln,7)
        self.setModel(self.model)
        column_widths = [50, 250, 50, 200, 300, 300, 50]
        for col, width in enumerate(column_widths):
            self.setColumnWidth(col, width)

        for row in range(self.model.rowCount()):
            self.setRowHeight(row, 80)

        self.setItemDelegate(CustomItemDelegate(self))
        # self._add_row(self.all_data)





    def _add_row(self, srt_data):
        # 初始化时加载数据
        for row_position, srt_line in enumerate(srt_data):
            # 第四列：时间
            index_3 = self.model.index(row_position, 3)  # 第4列的索引是3
            start_time = srt_line[0]
            end_time = srt_line[1]
            times = (start_time, end_time)
            self.model.setData(index_3, times, Qt.UserRole)
            # 第五列：原文
            index_4 = self.model.index(row_position, 4)  # 第5列的索引是4
            self.model.setData(index_4, srt_line[2], Qt.EditRole)


if __name__ == "__main__":
    import sys

    patt = r'D:\dcode\lin_trans\result\tt1\如何获取需求.srt'
    # patt =r'D:\dcode\lin_trans\result\tt1\tt.srt'
    app = QApplication(sys.argv)
    table = SubtitleTable(patt)  # 创建10行的表格
    table.resize(800, 600)  # 设置表格大小
    table.show()
    sys.exit(app.exec())
