from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem

from vendor.qfluentwidgets import TransparentPushButton, FluentIcon as FIF


class PaginatedTableWidget(QWidget):
    """分页表格组件

    一个带有分页功能的表格组件，支持上一页/下一页导航和页码显示。
    """

    # 定义信号
    pageChanged = Signal(int)  # 页码改变时发出信号

    def __init__(
        self,
        parent=None,
        page_size=10,
        headers=None,
        column_widths=None,
        stretch_column=None
    ):
        """初始化分页表格组件

        Args:
            parent: 父组件
            page_size: 每页显示的记录数，默认为10
            headers: 表头列表，例如 ['列1', '列2', '列3']
            column_widths: 列宽列表，例如 [100, 200, 300]
            stretch_column: 自适应宽度的列索引
        """
        super().__init__(parent=parent)

        # 分页相关变量
        self.all_items = []      # 存储所有数据项
        self.current_page = 1    # 当前页码
        self.page_size = page_size  # 每页显示的记录数
        self.total_pages = 1     # 总页数

        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # 创建表格
        self.table = QTableWidget(self)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁止编辑
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        # 设置表格样式 - 现代化设计
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                border: none;
                selection-background-color: transparent;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 4px;
                border: none;
                border-bottom: 2px solid #e9ecef;
                border-radius: 0px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
            }
            QTableWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid #f1f3f5;
                color: #212529;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: #212529;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #f8f9fa;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #ced4da;
                min-width: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #adb5bd;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

        # 设置表头
        if headers:
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)

            # 设置列宽
            header = self.table.horizontalHeader()
            if column_widths:
                for i, width in enumerate(column_widths):
                    if width > 0:
                        self.table.setColumnWidth(i, width)
                        header.setSectionResizeMode(i, header.ResizeMode.Fixed)

            # 设置自适应列
            if stretch_column is not None and 0 <= stretch_column < len(headers):
                header.setSectionResizeMode(stretch_column, header.ResizeMode.Stretch)

        # 添加表格到布局
        self.main_layout.addWidget(self.table)

        # 创建分页控件
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setContentsMargins(0, 10, 0, 0)
        self.pagination_layout.setSpacing(15)

        # 上一页按钮
        self.prev_button = TransparentPushButton('', self, FIF.LEFT_ARROW)
        self.prev_button.clicked.connect(self.prev_page)

        # 页码指示器
        self.page_indicator = QLabel('1/1', self)
        self.page_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_indicator.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: 500;
                min-width: 60px;
            }
        """)

        # 下一页按钮
        self.next_button = TransparentPushButton('', self, FIF.RIGHT_ARROW)
        self.next_button.clicked.connect(self.next_page)

        # 添加到分页布局
        self.pagination_layout.addStretch()
        self.pagination_layout.addWidget(self.prev_button)
        self.pagination_layout.addWidget(self.page_indicator)
        self.pagination_layout.addWidget(self.next_button)
        self.pagination_layout.addStretch()

        # 添加分页布局
        self.main_layout.addLayout(self.pagination_layout)

        # 初始化分页控件状态
        self.update_page_indicator()

    def set_data(self, items, reset_page=True):
        """设置表格数据

        Args:
            items: 数据项列表
            reset_page: 是否重置到第一页，默认为True
        """
        self.all_items = items

        # 计算总页数
        self.total_pages = max(1, (len(self.all_items) + self.page_size - 1) // self.page_size)

        # 重置页码或确保当前页码有效
        if reset_page:
            self.current_page = 1
        elif self.current_page > self.total_pages:
            self.current_page = self.total_pages

        # 更新页码指示器
        self.update_page_indicator()

        # 显示当前页数据
        self.display_current_page()

        # 发出页码改变信号
        self.pageChanged.emit(self.current_page)

    def display_current_page(self):
        """显示当前页的数据"""
        # 计算当前页的记录范围
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.all_items))
        current_page_items = self.all_items[start_idx:end_idx]

        # 设置表格行数
        self.table.setRowCount(len(current_page_items))

        # 如果没有记录，显示提示
        if not current_page_items:
            self.table.setRowCount(1)
            empty_item = QTableWidgetItem('暂无记录')
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setSpan(0, 0, 1, self.table.columnCount())  # 合并单元格
            self.table.setItem(0, 0, empty_item)
            return

        # 填充表格数据 - 这个方法需要被子类重写以处理特定的数据格式
        self._populate_table(current_page_items)

    def _populate_table(self, items):
        """填充表格数据

        这个方法应该被子类重写以处理特定的数据格式

        Args:
            items: 当前页的数据项
        """
        pass

    def update_page_indicator(self):
        """更新页码指示器"""
        self.page_indicator.setText(f"{self.current_page}/{self.total_pages}")

        # 更新分页按钮状态
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)

    def prev_page(self):
        """切换到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_page_indicator()
            self.display_current_page()
            self.pageChanged.emit(self.current_page)

    def next_page(self):
        """切换到下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_page_indicator()
            self.display_current_page()
            self.pageChanged.emit(self.current_page)

    def get_current_page(self):
        """获取当前页码"""
        return self.current_page

    def get_total_pages(self):
        """获取总页数"""
        return self.total_pages

    def set_page_size(self, page_size):
        """设置每页显示的记录数

        Args:
            page_size: 每页显示的记录数
        """
        if page_size > 0 and page_size != self.page_size:
            self.page_size = page_size
            # 重新计算总页数并更新显示
            self.set_data(self.all_items, reset_page=False)
