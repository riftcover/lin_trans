from PySide6.QtWidgets import QApplication, QMainWindow, QTableView, QStyledItemDelegate, QPushButton, QWidget, QVBoxLayout, QStyle, QStyleOptionButton, \
    QStyleOptionSpinBox, QStyleOptionViewItem, QTimeEdit, QTextEdit, QLabel, QSizePolicy, QHeaderView
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSize, QRect, QPoint, QTime, QSignalBlocker, QTimer, QAbstractListModel, QThread, Signal, \
    QElapsedTimer, QObject, QRunnable, Slot, QThreadPool
from PySide6.QtGui import QBrush, QColor, QStandardItemModel, QRegion
import sys

from nice_ui.configure import config
from nice_ui.ui.style import LinLineEdit, LTimeEdit
from vendor.qfluentwidgets import FluentIcon, CheckBox, TransparentToolButton, ToolTipFilter, ToolTipPosition


class CustomItemDelegate(QStyledItemDelegate):
    # 自定义代理项，用于设置单元格的样式

    def __init__(self, parent=None):
        # 构造函数，初始化父类，创建一个持久化编辑器字典
        super().__init__(parent)
        self._persistent_editors = {}
        self.signals = VirtualScrollSignals()

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
        if index.column() == 0:  # 勾选框
            self.signals.createEditor.emit(index.row(), index.column())
            return self.create_checkbox(parent)
        elif index.column() == 1:  # 操作按钮
            self.signals.createEditor.emit(index.row(), index.column())
            return self.create_operation_widget(parent)
        # elif index.column() == 2:  # 行号
        #     self.signals.createEditor.emit(index.row(), index.column())
        #     # return self.create_row_number_label(parent, index.row())
    
        elif index.column() == 3:  # 时间
            self.signals.createEditor.emit(index.row(), index.column())
            return self.create_time_widget(parent)
        elif index.column() in [4, 5]:  # 原文和译文
            self.signals.createEditor.emit(index.row(), index.column())
            return self.create_text_edit(parent)
        elif index.column() == 6:  # 编辑按钮
            return self.create_edit_widget(parent, index.row())

        return super().createEditor(parent, option, index)

    def destroyEditor(self, editor, index):
        # 用来通知哪个单元格需要销毁编辑器
        if index.column() == 0:  # 只处理第一列的编辑器
            super().destroyEditor(editor, index)
            self.signals.destroyEditor.emit(index.row(), index.column())

    def paint(self, painter, option, index):
        if index.column() == 2:  # 行号列
            # 使用默认绘制方法
            super().paint(painter, option, index)
        else:
            # 对于其他列，保持原有的逻辑
            pass
    # def paint(self, painter, option, index):
    """
    在使用openPersistentEditor时会持久化创建编辑器，就不需要使用print函数了
    使用print函数会导致窗口闪烁
    """

    #     # 绘制单元格
    #     timer = QElapsedTimer()
    #     timer.start()
    #
    #     table_view = self.parent()
    #     visible_range = table_view.viewport().rect()
    #     row_height = table_view.rowHeight(0)
    #
    #     # 计算可见行的范围
    #     first_visible_row = table_view.rowAt(visible_range.top())
    #     last_visible_row = table_view.rowAt(visible_range.bottom())
    #     config.logger.debug(f"index: {index.row()}, first_visible_row: {first_visible_row}, last_visible_row: {last_visible_row}")
    #     if index.column() in [0, 1, 2, 3, 4, 5, 6]:
    #         if index not in self._persistent_editors:
    #             editor = self.createEditor(self.parent(), option, index)
    #             self.setEditorData(editor, index)
    #             self.parent().setIndexWidget(index, editor)
    #             self._persistent_editors[index] = editor
    #     else:
    #         super().paint(painter, option,index)
    #         # print('======')
    #         # print(len(self._persistent_editors))
    #         # print(self._persistent_editors)
    #         # print(f"Paint time: {timer.elapsed()} ms")

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
        delete_button.clicked.connect(lambda _, r=row:self._delete_row(r))
        add_button = TransparentToolButton(FluentIcon.ADD)
        add_button.setObjectName("add_button")
        add_button.setToolTip("下方添加一行")
        add_button.installEventFilter(ToolTipFilter(add_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        add_button.clicked.connect(lambda _, r=row:self._insert_row_below(r))

        delete_button.setFixedSize(button_size)
        add_button.setFixedSize(button_size)

        # 移动译文上一行、下一行
        down_row_button = TransparentToolButton(FluentIcon.DOWN)
        down_row_button.setObjectName("down_button")
        down_row_button.setToolTip("移动译文到下一行")
        down_row_button.installEventFilter(ToolTipFilter(down_row_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        down_row_button.clicked.connect(lambda _, r=row:self._move_row_down(r))
        up_row_button = TransparentToolButton(FluentIcon.UP)
        up_row_button.setObjectName("up_button")
        up_row_button.setToolTip("移动译文到上一行")
        up_row_button.installEventFilter(ToolTipFilter(up_row_button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        up_row_button.clicked.connect(lambda _, r=row:self._move_row_up(r))

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
            start_time = editor.findChild(LTimeEdit, "start_time")
            config.logger.debug(f"start_time: {start_time}, times: {times}")
            editor.findChild(LTimeEdit, "start_time").initTime(times[0])
            editor.findChild(LTimeEdit, "end_time").initTime(times[1])
        elif index.column() in [4, 5]:
            # 原文和译文
            editor.setText(index.data(Qt.EditRole))
        elif index.column() == 6:
            # 编辑按钮
            pass
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        # 编辑器数据保存
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
            model.setData(index, f"{start_time} - {end_time}", Qt.UserRole)
        elif index.column() in (4, 5):
            # 原文和译文
            model.setData(index, editor.toPlainText(), Qt.EditRole)
        elif index.column() == 6:
            # 编辑按钮
            pass
        else:
            super().setModelData(editor, model, index)

    # def sizeHint(self, option, index):
    #     # 返回固定大小以提高性能
    #     return QSize(50, 80)

    # def sizeHint(self, option, index):    # 返回固定大小以提高性能
    #     if index.column() == 0:
    #         return QSize(50, 80)
    #     elif index.column() == 1:
    #         return QSize(50, 80)
    #     elif index.column() == 2:
    #         return QSize(50, 80)
    #     return super().sizeHint(option, index)


class SubtitleModel(QAbstractTableModel):
    # 定义数据模型
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._data = self.load_subtitle()

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

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return 7

    def data(self, index, role=Qt.DisplayRole):
        # 定义数据获取方式
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == 2:  # 行号列
                return str(row + 1)  # 行号从1开始
            if col == 3:  # 时间列
                return f"{self._data[row][0]} - {self._data[row][1]}"
            elif col == 4:  # 原文列
                return self._data[row][2]
            elif col == 5:  # 译文列
                return self._data[row][3]
        elif role == Qt.UserRole and col == 3:  # 时间列
                return self._data[row][0], self._data[row][1]

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
        elif role == Qt.UserRole and col == 3: # 时间列
                self._data[row] = (value[0], value[1], self._data[row][2], self._data[row][3])

        self.dataChanged.emit(index, index, [role])
        return True

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable


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

    """

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.visible_editors = set()
        self.on_data_loaded()

    def on_data_loaded(self):
        self.model = SubtitleModel(self.file_path)
        self.setModel(self.model)

        self.delegate = CustomItemDelegate(self)
        self.setItemDelegate(self.delegate)

        self.delegate.signals.createEditor.connect(self.on_editor_created)
        self.delegate.signals.destroyEditor.connect(self.on_editor_destroyed)

        self.setVerticalScrollMode(QTableView.ScrollPerPixel)
        self.setHorizontalScrollMode(QTableView.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.verticalHeader().setDefaultSectionSize(80)
        column_widths = [50, 55, 30, 100, 250, 250, 55]
        for col, width in enumerate(column_widths):
            self.setColumnWidth(col, width)

        # 设置最后一列自动拉伸
        self.horizontalHeader().setStretchLastSection(False)

        #  # 设置表格的固定大小
        # self.setFixedWidth(total_width + self.verticalScrollBar().width() + 20)  # +2 for borders

        self.setEditTriggers(QTableView.NoEditTriggers)
        self.setSelectionMode(QTableView.NoSelection)

        # # 连接滚动信号
        self.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.horizontalScrollBar().valueChanged.connect(self.on_scroll)

        QTimer.singleShot(0, self.initialize_visible_editors)

    def initialize_visible_editors(self):
        # 在表格初始化时创建初始可见的编辑器。
        config.logger.debug("Initializing visible event")
        self.create_visible_editors()

    def create_visible_editors(self):
        # 只为可见区域创建编辑器。
        visible_rect = self.viewport().rect()
        top_left = self.indexAt(visible_rect.topLeft())
        bottom_right = self.indexAt(visible_rect.bottomRight())
        config.logger.debug(f"Visible rect: {visible_rect}")
        config.logger.debug(f"Top left index: {top_left.row()}")
        config.logger.debug(f"Bottom right index: {bottom_right.row()}")

        # 确保我们至少创建一行编辑器，即使表格行数少于窗口高度
        start_row = 0 if not top_left.isValid() else top_left.row()
        end_row = self.model.rowCount() - 1 if not bottom_right.isValid() else bottom_right.row()
        start_col = max(0, top_left.column())
        end_col = min(self.model.columnCount() - 1, bottom_right.column())

        config.logger.debug(f"Creating editors for rows {start_row} to {end_row}, columns {start_col} to {end_col}")

        # 确保 end_row 不小于 start_row
        end_row = max(start_row, end_row)

        config.logger.debug(f"Creating editors for rows {start_row} to {end_row}")
        config.logger.debug(f"Visible editors: {self.visible_editors}")

        for row in range(start_row, end_row + 1):  # 判断纵向可见
            for col in range(start_col, end_col + 1):  # 判断横向可见窗口
                if col != 2 and (row, col) not in self.visible_editors:  # 跳过行号列（索引2）
                    index = self.model.index(row, col)
                    self.openPersistentEditor(index)
                    config.logger.debug(f"Created editor for ({row}, {col})")

        # self.verify_visible_editors()

    def remove_invisible_editors(self):
        # remove_invisible_editors 方法移除不再可见的编辑器。
        # 当前如果使用该函数，向下滚动时会销毁编辑器，但是往回滚动时不会重新创建编辑器。所以先屏蔽掉
        visible_rect = self.viewport().rect()
        top_left = self.indexAt(visible_rect.topLeft())
        bottom_right = self.indexAt(visible_rect.bottomRight())

        if not top_left.isValid() or not bottom_right.isValid():
            config.logger.warning("Invalid index range")
            return

        visible_range = set((row, col) for row in range(top_left.row(), bottom_right.row() + 1) for col in range(self.model.columnCount()))

        to_remove = self.visible_editors - visible_range
        for row, col in to_remove:
            index = self.model.index(row, col)
            self.closePersistentEditor(index)
            config.logger.debug(f"Removed editor for ({row}, {col})")

    def on_scroll(self):
        # on_scroll 方法在滚动时被调用，更新可见的编辑器。
        config.logger.debug("Scroll event")
        self.create_visible_editors()  # self.remove_invisible_editors()

    def on_editor_created(self, row, col):
        self.visible_editors.add((row, col))

    def on_editor_destroyed(self, row, col):
        self.visible_editors.discard((row, col))

    def verify_visible_editors(self):
        # 验证 visible_editors，创建的编辑器是否都存在
        visible_rect = self.viewport().rect()
        top_left = self.indexAt(visible_rect.topLeft())
        bottom_right = self.indexAt(visible_rect.bottomRight())

        if not top_left.isValid() or not bottom_right.isValid():
            return

        for row in range(top_left.row(), bottom_right.row() + 1):
            for col in range(self.model.columnCount()):
                if (row, col) not in self.visible_editors:
                    config.logger.warning(f"Editor missing for visible cell ({row}, {col})")
                    self.openPersistentEditor(self.model.index(row, col))

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.create_visible_editors)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        config.logger.debug("Resize event")
        self.create_visible_editors()


if __name__ == "__main__":
    import sys

    patt = r'D:\dcode\lin_trans\result\tt1\如何获取需求.srt'
    # patt =r'D:\dcode\lin_trans\result\tt1\tt1.srt'
    app = QApplication(sys.argv)
    table = SubtitleTable(patt)  # 创建10行的表格
    table.resize(800, 600)  # 设置表格大小
    table.show()
    sys.exit(app.exec())
