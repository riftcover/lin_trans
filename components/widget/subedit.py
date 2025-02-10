import os
from typing import Tuple, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize, QTimer, Signal, QObject
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QTableView, QStyledItemDelegate, QWidget, QVBoxLayout, QLabel, QHeaderView, QAbstractItemDelegate

from components.resource_manager import StyleManager
from nice_ui.ui.style import LinLineEdit, LTimeEdit
from utils import logger
from vendor.qfluentwidgets import FluentIcon, CheckBox, TransparentToolButton, ToolTipFilter, ToolTipPosition


class OperationType(Enum):
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    AUTO_MOVE = "auto_move"


@dataclass
class Operation:
    type: OperationType
    source_row: int
    target_row: int
    old_text: str
    new_text: str


class CustomItemDelegate(QStyledItemDelegate):
    # 自定义代理项，用于设置单元格的样式

    def __init__(self, parent=None):
        # 构造函数，初始化父类，创建一个持久化编辑器字典
        super().__init__(parent)
        self._play_from_time = None
        self._persistent_editors = {}
        self.signals = VirtualScrollSignals()
        self._delete_clicked = None
        self._insert_clicked = None
        self._move_row_up = None
        self._move_row_down = None
        self._move_row_up_more = None
        self._move_row_down_more = None
        self._play_from_time = None
        self._auto_move = None

    def createEditor(self, parent, option, index):
        """
        创建单元格编辑器，根据单元格的列数不同，创建不同的编辑器
        目前支持的编辑器有：勾选框、操作按钮、行号、时间、原文、译文、编辑按钮
        self.signals.createEditor.emit(index.row(), index.column()) 用来通知哪个单元格需要创建编辑器
        Args:
            parent:
            option:
            index:

        Returns:

        """
        editor = super().createEditor(parent, option, index)
        if index.column() == 0:  # 勾选框
            self.signals.createEditor.emit(index.row(), index.column())
            return self.create_checkbox(parent)
        elif index.column() == 1:  # 操作按钮
            self.signals.createEditor.emit(index.row(), index.column())
            return self.create_operation_widget(parent)
        elif index.column() == 3:  # 时间
            self.signals.createEditor.emit(index.row(), index.column())
            return self.create_time_widget(parent)
        elif index.column() in [4, 5]:  # 原文和译文
            self.signals.createEditor.emit(index.row(), index.column())
            editor = self.create_text_edit(parent)
            if isinstance(editor, LinLineEdit):
                # 为原文和译文列的编辑器添加鼠标点击事件处理
                original_mouse_press_event = editor.mousePressEvent
                editor.mousePressEvent = lambda event: self.editorClicked(event, index, editor, original_mouse_press_event)
            return editor
        elif index.column() == 6:  # 编辑按钮
            return self.create_edit_widget(parent, index)

        return editor

    def editorClicked(self, event, index, editor, original_mouse_press_event):
        """
        处理原文和译文列编辑器的点击事件

        Args:
            event: 鼠标事件
            index: 被点击的单元格索引
            editor: 被点击的编辑器
            original_mouse_press_event: 原始的鼠标按下事件处理函数
        """
        # 发出单元格被点击的信号
        self.parent().cellClicked.emit(index.row(), index.column())
        # 调用原始的鼠标按下事件处理函数，保持原有功能
        original_mouse_press_event(event)

    def destroyEditor(self, editor, index):
        # 用来通知哪个单元格需要销毁编辑器
        if index.column() == 0:  # 只处理第一列的编辑器
            super().destroyEditor(editor, index)
            self.signals.destroyEditor.emit(index.row(), index.column())

    def paint(self, painter, option, index):
        # 保存painter的状态
        painter.save()

        # 调用原有的绘制逻辑
        if index.column() == 2:  # 行号列
            # 使用自定义绘制方法来居中显示行号
            painter.setPen(QColor("#000000"))  # 设置文字颜色
            painter.setFont(option.font)  # 使用默认字体

            # 计算文本
            text = str(index.row() + 1)

            # 计算文本矩形
            text_rect = painter.boundingRect(option.rect, Qt.AlignCenter, text)

            # 绘制居中的文本
            painter.drawText(option.rect, Qt.AlignCenter, text)
        else:
            # 对于其他列，保持原有的逻辑
            pass  # 这里应该是你原有的绘制逻辑

        # 在原有绘制逻辑之后，为所有列添加红色底部边框
        painter.setPen(QColor("#d0d0d0"))
        # if index.column() == 3:  # 第二列
        #     # 为第二列特别处理，确保边框被绘制
        #     painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight() + QPoint(5, 0))
        # else:
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())

        # 恢复painter的状态
        painter.restore()

    def create_checkbox(self, parent) -> CheckBox:
        editor = CheckBox(parent)
        # editor.stateChanged.connect(lambda:self.commitAndCloseEditor(editor, index))
        return editor

    def create_operation_widget(self, parent) -> QWidget:
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        button_size = QSize(15, 15)
        play_button = TransparentToolButton(FluentIcon.PLAY)
        play_button.setToolTip("从当前开始播放")
        play_button.clicked.connect(self._play_from_time)
        auto_move_button = TransparentToolButton(FluentIcon.CHEVRON_DOWN_MED)
        play_button.setFixedSize(button_size)
        auto_move_button.setFixedSize(button_size)
        auto_move_button.setToolTip("当前行到空行间译文下移")
        auto_move_button.clicked.connect(self._auto_move)

        layout.addWidget(play_button, alignment=Qt.AlignCenter)  # 设置水平居中
        layout.addWidget(auto_move_button, alignment=Qt.AlignCenter)
        return widget

    def create_row_number_label(self, parent, row) -> QLabel:
        label = QLabel(str(row + 1), parent)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0;")
        return label

    def create_time_widget(self, parent) -> QWidget:
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        start_time = LTimeEdit(parent)
        start_time.setObjectName("start_time")
        end_time = LTimeEdit(parent)
        end_time.setObjectName("end_time")
        layout.addWidget(start_time)
        layout.addWidget(end_time)
        return widget

    def create_text_edit(self, parent) -> LinLineEdit:
        text_edit = LinLineEdit(parent)
        text_edit.setObjectName("text_edit")
        StyleManager.apply_style(text_edit, 'linlin_edit')
        return text_edit

    def create_edit_widget(self, parent, index) -> QWidget:
        widget = QWidget(parent)
        button_size = QSize(15, 15)
        edit_layout = QVBoxLayout(widget)
        edit_layout.setSpacing(2)
        edit_layout.setContentsMargins(2, 2, 2, 2)

        delete_button = TransparentToolButton(FluentIcon.DELETE)
        delete_button.setToolTip("删除本行字幕")
        delete_button.installEventFilter(ToolTipFilter(delete_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        delete_button.setObjectName("delete_button")
        delete_button.clicked.connect(self._delete_clicked)
        add_button = TransparentToolButton(FluentIcon.ADD)
        add_button.setObjectName("add_button")
        add_button.setToolTip("下方添加一行")
        add_button.installEventFilter(ToolTipFilter(add_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        add_button.clicked.connect(self._insert_clicked)

        delete_button.setFixedSize(button_size)
        add_button.setFixedSize(button_size)

        # 移动译文上一行、下一行
        down_row_button = TransparentToolButton(FluentIcon.DOWN)
        down_row_button.setObjectName("down_button")
        down_row_button.setToolTip("移动译文到下一行")
        down_row_button.installEventFilter(ToolTipFilter(down_row_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        down_row_button.clicked.connect(self._move_row_down)
        up_row_button = TransparentToolButton(FluentIcon.UP)
        up_row_button.setObjectName("up_button")
        up_row_button.setToolTip("移动译文到上一行")
        up_row_button.installEventFilter(ToolTipFilter(up_row_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        up_row_button.clicked.connect(self._move_row_up)

        down_row_button.setFixedSize(button_size)
        up_row_button.setFixedSize(button_size)

        edit_layout.addWidget(down_row_button, alignment=Qt.AlignCenter)
        edit_layout.addWidget(up_row_button, alignment=Qt.AlignCenter)

        edit_layout.addWidget(delete_button, alignment=Qt.AlignCenter)
        edit_layout.addWidget(add_button, alignment=Qt.AlignCenter)

        return widget

    def create_tool_button(self, icon, tooltip: str, row: int) -> TransparentToolButton:
        button = TransparentToolButton(icon)
        button.setToolTip(tooltip)
        button.installEventFilter(ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        return button

    def setEditorData(self, editor, index) -> None:
        # 编辑器数据设置
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
            editor.findChild(LTimeEdit, "start_time")
            # logger.debug(f"setEditorData: start_time: {start_time}, times: {times}")
            editor.findChild(LTimeEdit, "start_time").initTime(times[0])
            editor.findChild(LTimeEdit, "end_time").initTime(times[1])
        elif index.column() in [4, 5]:
            # 原文和译文
            editor.setText(index.data(Qt.EditRole))
            # logger.debug(f"setEditorData: {index.data(Qt.EditRole)}")
        elif index.column() == 6:
            # 编辑按钮
            pass
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        # 编辑器数据保存
        if index.column() == 0:
            # 勾选框
            model.setData(index, Qt.Checked if editor.isChecked() else Qt.Unchecked, Qt.CheckStateRole)
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
            logger.debug(f"setModelData:start_time: {start_time}, end_time: {end_time}")
            model.setData(index, f"{start_time} - {end_time}", Qt.UserRole)
        elif index.column() in (4, 5):
            # 原文和译文
            value = editor.toPlainText()
            model.setData(index, value, Qt.EditRole)
        elif index.column() == 6:
            # 编辑按钮
            pass
        else:
            super().setModelData(editor, model, index)  # def sizeHint(self, option, index):  #     # 返回固定大小以提高性能  #     return QSize(50, 80)

    def commitAndCloseEditor(self, editor, index):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)

    # def sizeHint(self, option, index):    # 返回固定大小以提高性能  #     if index.column() == 0:  #         return QSize(50, 80)  #     elif index.column() == 1:  #         return QSize(50, 80)  #     elif index.column() == 2:  #         return QSize(50, 80)  #     return super().sizeHint(option, index)


class SubtitleModel(QAbstractTableModel):
    dataChangedSignal = Signal()
    subtitleUpdated = Signal()  # 添加新的信号

    # 定义数据模型
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.sub_data = self.load_subtitle()
        self.checked_rows = set()  # 新增：用于存储被选中的行
        self.operation_history: List[Operation] = []
        self.current_operation_index = -1

    def load_subtitle(self) -> List[Tuple[str, str, str, str]]:
        """
        加载字幕文件，返回字幕列表
        :return:[('00:00:00,166', '00:00:01,166', '你好，世界！')]
                [start_time, end_time, content]
        """
        subtitles = []
        if not os.path.isfile(self.file_path):
            logger.error(f"文件:{self.file_path}不存在,无法编辑")
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")

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
                logger.error(f"Error parsing time range: {time_range}")
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
        logger.debug(f"字幕文件行数: {len(subtitles)}")
        return subtitles

    def get_subtitles(self):
        # 返回已加载的字幕数据
        return self.sub_data

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.sub_data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 7

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # 设置表头
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["选择", "操作", "行号", "时间", "原文", "译文", "编辑"]
            return headers[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole) -> Any:
        # 定义数据获取方式
        if not index.isValid() or not (0 <= index.row() < len(self.sub_data)):
            return None

        row = index.row()
        col = index.column()

        if role == Qt.CheckStateRole and col == 0:
            return Qt.Checked if row in self.checked_rows else Qt.Unchecked

        if role in [Qt.DisplayRole, Qt.EditRole]:
            if col == 2:  # 行号列
                return str(row + 1)  # 行号从1开始
            if col == 3:  # 时间列
                return f"{self.sub_data[row][0]} - {self.sub_data[row][1]}"
            elif col == 4:  # 原文列
                return self.sub_data[row][2]
            elif col == 5:  # 译文列
                return self.sub_data[row][3]
        elif role == Qt.UserRole and col == 3:  # 时间列
            return self.sub_data[row][0], self.sub_data[row][1]

        return None

    def setData(self, index, value, role=Qt.EditRole) -> bool:
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()
        # logger.debug(f"setData: {row}, {col}")
        if role == Qt.CheckStateRole and col == 0:
            if value == Qt.Checked:
                # logger.debug(f"setData: 勾选行: {row}")
                self.checked_rows.add(row)
            else:
                # logger.debug(f"setData: 取消勾选行: {row}")
                self.checked_rows.discard(row)
            self.dataChanged.emit(index, index, [role])
            return True

        if role == Qt.EditRole:
            if col == 4:  # 原文列
                set_data = (self.sub_data[row][0], self.sub_data[row][1], value, self.sub_data[row][3])
                self.sub_data[row] = set_data
            elif col == 5:  # 译文列
                self.sub_data[row] = (self.sub_data[row][0], self.sub_data[row][1], self.sub_data[row][2], value)

            # 发出信号通知数据变化
            self.dataChangedSignal.emit()
            self.subtitleUpdated.emit()  # 发出字幕更新信号
        elif role == Qt.UserRole and col == 3:  # 时间列
            self.sub_data[row] = (value[0], value[1], self.sub_data[row][2], self.sub_data[row][3])

            # 发出信号通知数据变化
            self.dataChangedSignal.emit()

        # logger.debug(f"setData 触发信号 dataChanged: {index}")
        self.dataChanged.emit(index, index, [role])
        return True

    def flags(self, index) -> Qt.ItemFlags:
        if index.column() == 0:
            return super().flags(index) | Qt.ItemIsUserCheckable
        return super().flags(index) | Qt.ItemIsEditable

    def removeRow(self, row, parent=QModelIndex()) -> bool:
        # 删除指定行
        logger.debug(f"SubtitleModel.removeRow: 删除行: {row}")
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(parent, row, row)
            del self.sub_data[row]
            self.endRemoveRows()
            return True
        return False

    def insertRow(self, row, parent=QModelIndex()) -> bool:
        """插入新行
        Args:
            row: 在此行后插入新行
            parent: 父索引
        Returns:
            bool: 是否插入成功
        """
        try:
            self.beginInsertRows(parent, row + 1, row + 1)
            # 复制当前行的时间信息作为新行的默认值
            if 0 <= row < len(self.sub_data):
                prev_start, prev_end = self.sub_data[row][0:2]
            else:
                prev_start = prev_end = '00:00:00,000'
            
            # 插入新的空字幕条目
            new_entry = (prev_start, prev_end, "", "")
            self.sub_data.insert(row + 1, new_entry)
            self.endInsertRows()
            
            # 发出数据变化信号
            self.dataChangedSignal.emit()
            return True
        except Exception as e:
            logger.error(f"Insert row failed: {e}")
            return False

    def move_edit_down(self, row) -> bool:
        # 移动原文到下一行
        if row < self.rowCount() - 1:
            current_text = self.data(self.index(row, 5), Qt.EditRole)
            if not current_text:
                return False
            target_text = self.data(self.index(row+1, 5), Qt.EditRole)


            # 记录操作
            operation = Operation(type=OperationType.MOVE_DOWN, source_row=row, target_row=row + 1, old_text=current_text,new_text=target_text)
            self.add_operation(operation)

            # Move current row's text to next row
            self.setData(self.index(row + 1, 5), current_text, Qt.EditRole)

            # Clear current row's text
            self.setData(self.index(row, 5), "", Qt.EditRole)

            self.dataChanged.emit(self.index(row, 5), self.index(row + 1, 5), [Qt.EditRole])
            return True
        return False

    def move_edit_up(self, row) -> bool:
        # 移动原文到上一行
        if row > 0:
            current_text = self.data(self.index(row, 5), Qt.EditRole)
            if not current_text:
                return False
            target_text = self.data(self.index(row - 1, 5), Qt.EditRole)
            # 记录操作
            operation = Operation(type=OperationType.MOVE_UP, source_row=row, target_row=row - 1, old_text=current_text,new_text=target_text)
            self.add_operation(operation)

            # 执行移动
            self.setData(self.index(row - 1, 5), current_text, Qt.EditRole)
            self.setData(self.index(row, 5), "", Qt.EditRole)
            self.dataChanged.emit(self.index(row - 1, 5), self.index(row, 5), [Qt.EditRole])
            return True
        return False

    def save_subtitle(self) -> None:
        subtitles = []
        for row in range(self.rowCount()):
            start_time_edit = self.index(row, 3).data(Qt.UserRole)
            your_text = self.index(row, 4).data(Qt.EditRole)
            translated_text = self.index(row, 5).data(Qt.EditRole)
            subtitles.append((f"{start_time_edit[0]} --> {start_time_edit[1]}", your_text, translated_text))
        # todo: 保存文件路径调整
        with open(self.file_path, 'w', encoding='utf-8') as f:
            for i, j in enumerate(subtitles):
                f.write(f"{i + 1}\n")
                f.write(f"{j[0]}\n")
                if j[2]:
                    f.write(f"{j[1]}\n")
                    f.write(f"{j[2]}\n\n")
                else:
                    f.write(f"{j[1]}\n\n")

    def checkbox_clear(self, row) -> None:
        # 清除勾选框状态
        self.setData(self.index(row, 0), Qt.Unchecked, Qt.CheckStateRole)

    def auto_move_down(self, row) -> None:
        """
        从当前行开始，将译文向下移动直到遇到空行
        Args:
            row: 起始行号
        """
        if row >= self.rowCount() - 1:  # 如果是最后一行，直接返回
            return

        current_text = self.data(self.index(row, 5), Qt.EditRole)
        if not current_text:  # 如果当前行为空，无需移动
            return

        self.setData(self.index(row, 5), "", Qt.EditRole)  

        for i in range(row, self.rowCount()):
            next_text = self.data(self.index(i + 1, 5), Qt.EditRole)
            if next_text == "":
                self.setData(self.index(i + 1, 5), current_text, Qt.EditRole)
                break
            # 否则，交换当前行和下一行的内容
            self.setData(self.index(i + 1, 5), current_text, Qt.EditRole)
            current_text = next_text
            # logger.trace(f'{row}:{current_text}')

        # 发出数据变化信号
        self.dataChanged.emit(self.index(row, 5), self.index(self.rowCount() - 1, 5), [Qt.EditRole])

    def add_operation(self, operation: Operation) -> None:
        # 执行行移动操作时，将旧数据写入operation_history
        # 添加新操作时，清除当前位置之后的所有操作
        if self.current_operation_index < len(self.operation_history) - 1:
            self.operation_history = self.operation_history[:self.current_operation_index + 1]

        self.operation_history.append(operation)
        self.current_operation_index += 1

    def can_undo(self) -> bool:
        return self.current_operation_index >= 0

    def can_redo(self) -> bool:
        return self.current_operation_index < len(self.operation_history) - 1

    def undo(self) -> bool:
        if not self.can_undo():
            return False

        operation = self.operation_history[self.current_operation_index]

        if operation.type == OperationType.MOVE_DOWN:
            # 将文本从目标行移回源行
            self.setData(self.index(operation.source_row, 5), operation.old_text, Qt.EditRole)
            self.setData(self.index(operation.target_row, 5), operation.new_text, Qt.EditRole)
        elif operation.type == OperationType.MOVE_UP:
            # 将文本从目标行移回源行
            self.setData(self.index(operation.source_row, 5), operation.old_text, Qt.EditRole)
            self.setData(self.index(operation.target_row, 5), operation.new_text, Qt.EditRole)
        elif operation.type == OperationType.AUTO_MOVE:
            # 将文本从目标行移回源行
            self.setData(self.index(operation.source_row, 5), operation.old_text, Qt.EditRole)
            self.setData(self.index(operation.target_row, 5), operation.new_text, Qt.EditRole)

        self.current_operation_index -= 1
        self.dataChanged.emit(self.index(0, 5), self.index(self.rowCount() - 1, 5), [Qt.EditRole])
        return True

    def redo(self) -> bool:
        if not self.can_redo():
            return False

        self.current_operation_index += 1
        operation = self.operation_history[self.current_operation_index]

        if operation.type == OperationType.MOVE_DOWN:
            # 重新执行向下移动
            self.setData(self.index(operation.target_row, 5), operation.text, Qt.EditRole)
            self.setData(self.index(operation.source_row, 5), "", Qt.EditRole)
        elif operation.type == OperationType.MOVE_UP:
            # 重新执行向上移动
            self.setData(self.index(operation.target_row, 5), operation.text, Qt.EditRole)
            self.setData(self.index(operation.source_row, 5), "", Qt.EditRole)
        elif operation.type == OperationType.AUTO_MOVE:
            # 重新执行自动移动
            self.setData(self.index(operation.target_row, 5), operation.text, Qt.EditRole)
            self.setData(self.index(operation.source_row, 5), "", Qt.EditRole)

        self.dataChanged.emit(self.index(0, 5), self.index(self.rowCount() - 1, 5), [Qt.EditRole])
        return True


class VirtualScrollSignals(QObject):
    # 使用 VirtualScrollDelegate 来管理编辑器的创建和销毁。
    createEditor = Signal(int, int)
    destroyEditor = Signal(int, int)


class SubtitleTable(QTableView):
    """
    这个实现的主要特点：
        1.使用 VirtualScrollDelegate 来管理编辑器的创建和销毁。
        2.SubtitleTable 类现在维护一个 visible_editors 集合来跟踪当前可见的编辑器。
        3.create_visible_editors 方法只为可见区域创建编辑器。
        4.remove_invisible_editors 方法移除不再可见的编辑器。
        5.on_scroll 方法在滚动时被调用，更新可见的编辑器。
        6.initialize_visible_editors 方法在表格初始化时创建初始可见的编辑器。
    这种实现的优点：
        1.大大减少了内存使用，因为只有可见的单元格才会创建编辑器。
        2.提高了性能，特别是对于大型数据集。
        3.保持了良好的用户体验，因为编辑器会动态创建和销毁。

    遗留问题：当前初始化时会同时调用：resizeEvent和initialize_visible_editors，
    导致编辑器创建函数执行2次，但是好的是会去set（visible_editors）中查找，实际编辑器还只创建了一个

    使用计时器来优化编辑器创建：
        1.在 __init__ 方法中，我们创建了一个 QTimer 对象 self.update_timer。
        2.我们添加了一个新的 delayed_update 方法，它会在计时器触发时调用 create_visible_editors。
        3.在 on_scroll 和 resizeEvent 方法中，我们不再直接调用 create_visible_editors，而是启动计时器。
        4.每次滚动或调整大小时，我们首先停止之前的计时器（如果存在），然后启动一个新的计时器。这确保了在快速连续的滚动或调整大小操作中，只有最后一次操作会触发更新。

    """
    tableChanged = Signal(list)

    # 信号，用于视频控制
    play_from_time_signal = Signal(str)  # 点击播放按钮时发出，用于从特定时间开始播放视频
    seek_to_time_signal = Signal(str)  # 点击原文或译文列时发出，用于将视频跳转到特定时间
    cellClicked = Signal(int, int)  # 用于捕获单元格点击事件

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        if not os.path.isfile(file_path):
            logger.error(f"文件:{file_path}不存在,无法编辑")
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        # 预处理字幕数据 用于和播放器连接给他字幕的
        self.model = SubtitleModel(self.file_path)
        self.delegate = CustomItemDelegate(self)
        self.visible_editors = set()

        # 设置模型和代理
        self.setModel(self.model)
        self.setItemDelegate(self.delegate)

        # 预处理字幕数据
        self.subtitles = self.model.load_subtitle()
        # Load subtitles from model
        # todo：不懂为什用get_subtitles就无法创建编辑器
        # self.subtitles = self.model.get_subtitles()  # Load subtitles from model

        # 初始化一个计时器
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.delayed_update)

        # 连接信号
        self.delegate.signals.createEditor.connect(self.on_editor_created)
        self.delegate.signals.destroyEditor.connect(self.on_editor_destroyed)
        self.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.horizontalScrollBar().valueChanged.connect(self.on_scroll)
        self.cellClicked.connect(self.handle_cell_click)

        self.init_ui()
        # 设置默认行高
        self.default_row_height = 80  # 或者其他合适的值
        self.verticalHeader().setDefaultSectionSize(self.default_row_height)

        self.tablet_action()

        self.process_subtitles()

        self.batch_size = 20  # 每批创建的行数
        self.current_batch = 0  # 当前批次
        self.create_timer = QTimer(self)
        self.create_timer.timeout.connect(self.create_next_batch)

        # 连接信号
        self.model.dataChangedSignal.connect(self.process_subtitles)
        self.delegate._play_from_time = self.play_from_time  # 设置播放按钮的回调函数
        self.cellClicked.connect(self.handle_cell_click)  # 连接单元格点击信号到处理方法

    def init_ui(self) -> None:
        # 设置滚动模式
        self.setVerticalScrollMode(QTableView.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableView.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # 隐藏垂直表头
        self.verticalHeader().hide()

        # 设置表头
        self.setHorizontalHeaderLabels()

        # 设置行高
        self.verticalHeader().setDefaultSectionSize(80)

        # 设置编辑器选择模式：禁用所有选择
        self.setSelectionMode(QTableView.NoSelection)

        # 隐藏网格线
        self.setShowGrid(False)

        StyleManager.apply_style(self, 'subedit_table')

    def play_from_time(self):
        """
        当点击播放按钮时调用此方法
        获取当前行的开始时间，并发出信号以开始播放视频
        """
        logger.trace('点击播放按钮')
        row = self.get_editor_row()
        start_time = self.model.data(self.model.index(row, 3), Qt.UserRole)[0]
        self.play_from_time_signal.emit(start_time)

    def handle_cell_click(self, row, column):
        """
        处理单元格点击事件
        如果点击的是原文或译文列，发出信号以跳转视频进度

        Args:
            row: 被点击的行索引
            column: 被点击的列索引
        """
        if column in [4, 5]:  # 原文或译文列
            start_time = self.model.data(self.model.index(row, 3), Qt.UserRole)[0]
            self.seek_to_time_signal.emit(start_time)

    def setHorizontalHeaderLabels(self):
        # 设置表头样式
        header = self.horizontalHeader()
        # 设置默认对齐方式为居中
        header.setDefaultAlignment(Qt.AlignCenter)
        StyleManager.apply_style(header, 'subedit_head')

        # 设置表头高度
        header.setFixedHeight(30)

        # 设置固定宽度的列
        fixed_widths = [40, 40, 40, 120, 0, 0, 40]  # 0 表示自适应宽度
        for col, width in enumerate(fixed_widths):
            if width > 0:
                header.resizeSection(col, width)
            else:
                header.setSectionResizeMode(col, QHeaderView.Stretch)  # 列会自动调整以填充可用空间

    def delayed_update(self) -> None:
        self.create_visible_editors()

    def on_scroll(self) -> None:
        # on_scroll 方法在滚动时被调用，更新可见的编辑器。
        # logger.debug("Scroll event")
        # 取消之前的计时器（如果存在）
        self.update_timer.stop()
        # 启动新的计时器，200毫秒后更新
        # self.update_timer.start(10)  # self.create_visible_editors()    # self.remove_invisible_editors()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # logger.debug("Resize event")
        # 取消之前的计时器（如果存在）
        # self.update_timer.stop()
        # # 启动新的计时器，200毫秒后更新
        # self.update_timer.start(30)

    def create_visible_editors(self) -> None:
        """初始化创建编辑器"""
        self.current_batch = 0
        self.create_next_batch()

    def create_next_batch(self) -> None:
        """创建下一批编辑器"""
        start_row = self.current_batch * self.batch_size
        end_row = min(start_row + self.batch_size, self.model.rowCount())
        
        for row in range(start_row, end_row):
            for col in range(self.model.columnCount()):
                if col != 2 and (row, col) not in self.visible_editors:  # 跳过行号列（索引2）
                    index = self.model.index(row, col)
                    self.openPersistentEditor(index)
                    self.visible_editors.add((row, col))
        
        self.current_batch += 1
        
        # 检查是否需要继续创建
        if end_row < self.model.rowCount():
            # 使用计时器延迟创建下一批，避免界面卡顿
            self.create_timer.start(10)  # 10ms后创建下一批
        else:
            self.create_timer.stop()
            logger.debug("All editors created")
    
    # def create_visible_editors(self) -> None:
        # 只为可见区域创建编辑器。
        # 获取当前视口（可见区域）的矩形
        visible_rect = self.viewport().rect()
        # visible_rect.topLeft()返回视口矩形的左上角点的坐标。
        # 调用将屏幕坐标转换为表格的行和列索引
        top_left = self.indexAt(visible_rect.topLeft())
        bottom_right = self.indexAt(visible_rect.bottomRight())

        # # 确保我们至少创建一行编辑器，即使表格行数少于窗口高度
        start_row = max(0, top_left.row())
        end_row = self.model.rowCount() - 1  # 默认到最后一行
        if bottom_right.isValid():
            end_row = min(bottom_right.row(), end_row)
        else:
            # 如果 bottom_right 无效，我们估算可见的行数
            visible_height = visible_rect.height()
            row_height = self.default_row_height  # 使用默认行高
            if row_height > 0:
                visible_rows = visible_height // row_height
                end_row = min(start_row + visible_rows, self.model.rowCount() - 1)

        for row in range(start_row, end_row + 1):
            for col in range(self.model.columnCount()):
                if col != 2 and (row, col) not in self.visible_editors:  # 跳过行号列（索引2）
                    index = self.model.index(row, col)
                    self.openPersistentEditor(index)
                    self.visible_editors.add((row, col))
        self.read_visible_editors()

        # self.verify_visible_editors()

    def remove_invisible_editors(self) -> None:
        # remove_invisible_editors 方法移除不再可见的编辑器。
        # 当前如果使用该函数，向下滚动时会销毁编辑器，但是往回滚动时不会重新创建编辑器。所以先屏蔽掉
        visible_rect = self.viewport().rect()
        top_left = self.indexAt(visible_rect.topLeft())
        bottom_right = self.indexAt(visible_rect.bottomRight())

        if not top_left.isValid() or not bottom_right.isValid():
            logger.warning("Invalid index range")
            return

        visible_range = set((row, col) for row in range(top_left.row(), bottom_right.row() + 1) for col in range(self.model.columnCount()))

        to_remove = self.visible_editors - visible_range
        for row, col in to_remove:
            index = self.model.index(row, col)
            self.closePersistentEditor(index)
            logger.debug(f"Removed editor for ({row}, {col})")

    def on_editor_created(self, row: int, col: int) -> None:
        self.visible_editors.add((row, col))

    def on_editor_destroyed(self, row: int, col: int) -> None:
        self.visible_editors.discard((row, col))

    def _verify_visible_editors(self) -> None:
        # 验证 visible_editors，创建的编辑器是否都存在
        visible_rect = self.viewport().rect()
        top_left = self.indexAt(visible_rect.topLeft())
        bottom_right = self.indexAt(visible_rect.bottomRight())

        if not top_left.isValid() or not bottom_right.isValid():
            return

        for row in range(top_left.row(), bottom_right.row() + 1):
            for col in range(self.model.columnCount()):
                if (row, col) not in self.visible_editors:
                    logger.warning(f"Editor missing for visible cell ({row}, {col})")
                    self.openPersistentEditor(self.model.index(row, col))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # 延迟创建编辑器，防止编辑器还没创建完成就开始编辑
        QTimer.singleShot(0, self.create_visible_editors)

    def tablet_action(self) -> None:
        self.delegate._delete_clicked = self.delete_row
        self.delegate._insert_clicked = self.insert_row  # Add this line
        self.delegate._move_row_down = self.move_row_down
        self.delegate._move_row_up = self.move_row_up
        self.delegate._move_row_down_more = self.move_row_down_more
        self.delegate._move_row_up_more = self.move_row_up_more
        self.delegate._auto_move = self.auto_move

    def get_editor_row(self):
        button = self.sender()
        index = self.indexAt(button.parent().pos())  # 由于按钮是放在QWidget中，所以需要调用父组件的pos()方法获取行号
        row = index.row()
        return row

    def read_visible_editors(self):
        # 获取visible_editors存储编辑器的所有行号
        r_list = set()
        for r, c in self.visible_editors:
            r_list.add(r)
        # logger.info(f"read_visible_editors: {r_list}")
        return r_list

    def delete_row(self) -> None:
        row = self.get_editor_row()

        new_visible_editors = set()
        for r, c in self.visible_editors:

            # 从visible_editors中移除被删除行的编辑器，对被删除行以下的编辑器的行号进行调整
            if r < row:
                new_visible_editors.add((r, c))
            elif r > row:
                new_visible_editors.add((r - 1, c))
        self.visible_editors = new_visible_editors
        # 此时visible_editors移除了删除行对应的坐标，但是重新创建编辑器时还是会正确的被创建，没有出现串行，漏行。看不懂？？
        self.read_visible_editors()
        logger.info(f"Delete row called for row: {row}")  # 新增调试信息

        self.model.removeRow(row)
        # 删除后更新可见的编辑器
        self.create_visible_editors()

    def insert_row(self) -> None:
        """插入新行"""
        try:
            row = self.get_editor_row()
            success = self.model.insertRow(row)
            if success:
                # 只为新行创建编辑器
                new_row = row + 1
                for col in range(self.model.columnCount()):
                    if col != 2:  # 跳过行号列
                        index = self.model.index(new_row, col)
                        self.openPersistentEditor(index)
                        self.visible_editors.add((new_row, col))
                
                # 更新后续行的编辑器索引
                updated_editors = set()
                for (r, c) in self.visible_editors:
                    if r > new_row:
                        updated_editors.add((r + 1, c))
                    else:
                        updated_editors.add((r, c))
                self.visible_editors = updated_editors
                
        except Exception as e:
            logger.error(f"Error inserting row: {e}")

    def update_editors(self) -> None:
        """
        更新可见行的编辑器
        我们首先关闭所有持久化的编辑器，并从 visible_editors 集合中移除它们。
        然后，我们调用 create_visible_editors() 来重新创建可见区域的编辑器。
        最后，我们更新可见区域内所有行的行号。我们通过调用 self.update(index) 来触发这些单元格的重绘。

        存在bug：
        在点击最后一行时，创建的行在倒数第二行。
        """
        # Close all persistent editors
        for editor_row, col in list(self.visible_editors):
            self.closePersistentEditor(self.model.index(editor_row, col))
            self.visible_editors.discard((editor_row, col))

        # Recreate visible editors
        self.create_visible_editors()

    def move_row_down(self):
        # 移动原文到下一行
        row = self.get_editor_row()
        self.model.move_edit_down(row)

    def auto_move(self):
        row = self.get_editor_row()
        self.model.auto_move_down(row)

    def move_row_down_more(self):
        logger.debug(f"move_row_down_more {self.model.checked_rows}")
        # Iterate over checked rows in reverse order
        for row in sorted(self.model.checked_rows, reverse=True):
            self.model.move_edit_down(row)
            self.model.checkbox_clear(row)

    def move_row_up(self):
        # 移动原文到上一行
        row = self.get_editor_row()
        self.model.move_edit_up(row)

    def move_row_up_more(self):
        logger.debug(f"move_row_up_more {self.model.checked_rows}")
        for row in sorted(self.model.checked_rows, reverse=True):
            self.model.move_edit_up(row)
            self.model.checkbox_clear(row)

    def save_subtitle(self):
        self.model.save_subtitle()

    def process_subtitles(self):
        """ 预处理字幕数据，用于给播放器连接字幕 """
        self.subtitles.clear()  # 清空现有字幕
        # 从 SubtitleModel 中读取字幕数据
        for row in range(self.model.rowCount()):
            start_time, end_time, first_text, second_text = self.model.sub_data[row]

            # 将时间转换为毫秒
            start_time_ms = self.time_to_milliseconds(start_time)
            end_time_ms = self.time_to_milliseconds(end_time)
            full_text = f'{first_text}\n{second_text}'
            # 添加到字幕列表，选择需要的文本（例如英文文本）
            self.subtitles.append((start_time_ms, end_time_ms, full_text))

        # 按开始时间排序
        self.subtitles.sort(key=lambda x: x[0])

    def time_to_milliseconds(self, time_str):
        """ 将时间字符串转换为毫秒 """
        h, m, s = time_str.split(':')
        s, ms = s.split(',')
        return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

    def undo(self) -> None:
        """撤销上一次移动操作"""
        if self.model.undo():
            self.create_visible_editors()

    def redo(self) -> None:
        """重做上一次移动操作"""
        if self.model.redo():
            self.create_visible_editors()

    def keyPressEvent(self, event) -> None:
        """处理键盘快捷键"""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.undo()
                event.accept()
                return
            elif event.key() == Qt.Key_Y:
                self.redo()
                event.accept()
                return
        super().keyPressEvent(event)


if __name__ == "__main__":
    import sys


    patt = r'D:\dcode\lin_trans\result\tt1\tt.srt'
    app = QApplication(sys.argv)
    table = SubtitleTable(patt)  # 创建10行的表格
    table.resize(800, 600)  # 设置表格大小
    table.show()
    sys.exit(app.exec())

