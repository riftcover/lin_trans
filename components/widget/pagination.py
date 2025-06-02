import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtGui import QIcon
from pathlib import Path

from vendor.qfluentwidgets import TransparentToolButton
from PySide6.QtCore import QFile


class PaginatedTableWidget(QWidget):
    """分页表格组件

    一个带有分页功能的表格组件，支持上一页/下一页导航和页码显示。
    """

    # 定义信号
    pageChanged = Signal(int)  # 页码改变时发出信号

    # 表格样式常量 - 保留表格样式为内联样式，因为它不属于分页控件的一部分
    TABLE_STYLE = """
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
    """

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

        # 分页相关变量初始化
        self._init_variables(page_size)

        # 创建UI组件
        self._init_ui()

        # 设置表头
        self._setup_table_headers(headers, column_widths, stretch_column)

        # 初始化分页控件状态
        self.update_page_indicator()

    def _init_variables(self, page_size):
        """初始化分页相关变量"""
        self.all_items = []      # 存储所有数据项
        self.current_page = 1    # 当前页码
        self.page_size = page_size  # 每页显示的记录数
        self.total_pages = 1     # 总页数
        self.total_records = 0   # 总记录数

    def _init_ui(self):
        """初始化UI组件"""
        # 加载分页控件样式
        self._load_pagination_style()

        # 创建主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)

        # 创建表格
        self._create_table()

        # 创建分页控件
        self._create_pagination_controls()

    def _load_pagination_style(self):
        """加载分页控件样式"""
        # 使用QRC资源加载样式表
        style_file = QFile(":/qss/themes/lin_pagination.qss")
        if style_file.open(QFile.ReadOnly | QFile.Text):
            style_sheet = style_file.readAll().data().decode("utf-8")
            self.setStyleSheet(style_sheet)
            style_file.close()

    def _create_table(self):
        """创建表格"""
        self.table = QTableWidget(self)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁止编辑
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(self.TABLE_STYLE)

        # 添加表格到布局
        self.main_layout.addWidget(self.table)

    def _create_pagination_controls(self):
        """创建分页控件"""
        # 创建分页布局
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setContentsMargins(10, 10, 10, 5)
        self.pagination_layout.setSpacing(8)  # 减小间距使组件更紧凑

        # 创建页码信息标签
        self._create_page_info()

        # 创建分页按钮
        self._create_pagination_buttons()

        # 添加分页布局
        self.main_layout.addLayout(self.pagination_layout)

    def _create_page_info(self):
        """创建页码信息标签"""
        self.page_info = QLabel('共 0 条', self)
        self.page_info.setObjectName("pageInfo")  # 设置对象名称以匹配QSS
        self.pagination_layout.addWidget(self.page_info)
        self.pagination_layout.addStretch(1)  # 左侧信息和分页控件之间的弹性空间

    def _create_pagination_buttons(self):
        """创建分页按钮"""
        # 获取资源路径
        assets_path = self._get_assets_path()

        # 创建分页控件容器
        pagination_controls = QWidget()
        pagination_controls.setObjectName("paginationControls")  # 设置对象名称以匹配QSS
        pagination_controls_layout = QHBoxLayout(pagination_controls)
        pagination_controls_layout.setContentsMargins(0, 0, 0, 0)
        pagination_controls_layout.setSpacing(2)  # 减小间距

        # 创建按钮
        self.first_button = self._create_nav_button(
            '首页',
            self.first_page
        )
        self.first_button.setObjectName("firstButton")  # 设置对象名称以匹配QSS

        self.prev_button = self._create_nav_button(
            '上一页',
            self.prev_page
        )
        self.prev_button.setObjectName("prevButton")  # 设置对象名称以匹配QSS

        # 页码指示器
        self.page_indicator = QLabel('1/1', self)
        self.page_indicator.setObjectName("pageIndicator")  # 设置对象名称以匹配QSS
        self.page_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_button = self._create_nav_button(
            '下一页',
            self.next_page
        )
        self.next_button.setObjectName("nextButton")  # 设置对象名称以匹配QSS

        self.last_button = self._create_nav_button(
            '末页',
            self.last_page
        )
        self.last_button.setObjectName("lastButton")  # 设置对象名称以匹配QSS


        # 添加分页控件到容器
        pagination_controls_layout.addWidget(self.first_button)
        pagination_controls_layout.addWidget(self.prev_button)
        pagination_controls_layout.addWidget(self.page_indicator)
        pagination_controls_layout.addWidget(self.next_button)
        pagination_controls_layout.addWidget(self.last_button)

        # 将分页控件容器添加到主分页布局
        self.pagination_layout.addWidget(pagination_controls)

    def _get_assets_path(self):
        """获取资源路径"""
        # 使用相对路径，更好的跨平台支持
        return str(Path(__file__).parent.parent / 'assets')

    def _create_nav_button(self, tooltip, callback):
        """创建导航按钮

        Args:
            tooltip: 提示文本
            callback: 点击回调函数

        Returns:
            TransparentToolButton: 创建的按钮
        """
        button = TransparentToolButton()
        button.setFixedSize(32, 32)  # 设置为正方形
        button.clicked.connect(callback)
        button.setToolTip(tooltip)
        button.setProperty("class", "NavButton")  # 设置类名以匹配QSS
        return button

    def _setup_table_headers(self, headers, column_widths, stretch_column):
        """设置表头

        Args:
            headers: 表头列表
            column_widths: 列宽列表
            stretch_column: 自适应宽度的列索引
        """
        if not headers:
            return

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

    def set_data(self, items, reset_page=True, total_pages=None, total_records=None):
        """设置表格数据

        Args:
            items: 数据项列表
            reset_page: 是否重置到第一页，默认为True
            total_pages: 可选，直接设置总页数
            total_records: 可选，总记录数
        """
        self.all_items = items

        # 更新分页信息
        self._update_pagination_info(reset_page, total_pages, total_records)

        # 更新页码指示器
        self.update_page_indicator()

        # 显示当前页数据
        self.display_current_page()

        # 发出页码改变信号
        self.pageChanged.emit(self.current_page)

    def _update_pagination_info(self, reset_page, total_pages, total_records):
        """更新分页信息

        Args:
            reset_page: 是否重置到第一页
            total_pages: 总页数
            total_records: 总记录数
        """
        # 如果提供了总页数，直接使用；否则根据当前数据计算
        if total_pages is not None:
            self.total_pages = max(1, total_pages)
        else:
            # 计算总页数
            self.total_pages = max(1, (len(self.all_items) + self.page_size - 1) // self.page_size)

        # 重置页码或确保当前页码有效
        if reset_page:
            self.current_page = 1
        elif self.current_page > self.total_pages:
            self.current_page = self.total_pages

        # 更新总记录数
        if total_records is not None:
            self.total_records = total_records

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
        """更新页码指示器和页面信息"""
        # 更新页码指示器
        self.page_indicator.setText(f"{self.current_page}/{self.total_pages}")

        # 计算当前页的记录范围
        total_items = len(self.all_items)
        start_idx = (self.current_page - 1) * self.page_size + 1 if total_items > 0 else 0
        end_idx = min(start_idx + self.page_size - 1, total_items)

        # 更新页面信息标签
        if hasattr(self, 'total_records') and self.total_records > 0:
            self.page_info.setText(f"共 {self.total_records} 条记录")
        elif total_items > 0:
            self.page_info.setText(f"显示 {start_idx}-{end_idx} 条，共 {total_items} 条")
        else:
            self.page_info.setText("暂无记录")

        # 更新分页按钮状态
        has_prev = self.current_page > 1
        has_next = self.current_page < self.total_pages

        self.first_button.setEnabled(has_prev)
        self.prev_button.setEnabled(has_prev)
        self.next_button.setEnabled(has_next)
        self.last_button.setEnabled(has_next)

    def prev_page(self):
        """切换到上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            # 只更新页码指示器，不显示数据，等待API获取新页数据
            self.update_page_indicator()
            # 发出页码改变信号，由外部处理获取新页数据
            self.pageChanged.emit(self.current_page)

    def next_page(self):
        """切换到下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            # 只更新页码指示器，不显示数据，等待API获取新页数据
            self.update_page_indicator()
            # 发出页码改变信号，由外部处理获取新页数据
            self.pageChanged.emit(self.current_page)

    def first_page(self):
        """切换到第一页"""
        if self.current_page > 1:
            self.current_page = 1
            # 只更新页码指示器，不显示数据，等待API获取新页数据
            self.update_page_indicator()
            # 发出页码改变信号，由外部处理获取新页数据
            self.pageChanged.emit(self.current_page)

    def last_page(self):
        """切换到最后一页"""
        if self.current_page < self.total_pages:
            self.current_page = self.total_pages
            # 只更新页码指示器，不显示数据，等待API获取新页数据
            self.update_page_indicator()
            # 发出页码改变信号，由外部处理获取新页数据
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

    def clear(self):
        """清空表格并重置分页状态

        这个方法会清空表格中的所有数据，并将分页状态重置为初始状态。
        """
        # 清空数据列表
        self.all_items = []

        # 清空表格内容
        self.table.clearContents()
        self.table.setRowCount(0)

        # 重置分页状态
        self.current_page = 1
        self.total_pages = 1

        # 更新页码指示器
        self.update_page_indicator()

        # 发出页码改变信号
        self.pageChanged.emit(self.current_page)

    def set_pagination_info(self, total_records, page_size=None):
        """设置分页信息

        Args:
            total_records: 总记录数
            page_size: 可选，每页记录数，如果不提供则使用当前值

        Returns:
            int: 计算出的总页数
        """
        # 更新总记录数
        self.total_records = total_records

        # 如果提供了page_size，则更新
        if page_size is not None:
            self.page_size = page_size

        # 计算总页数，向上取整
        self.total_pages = (self.total_records + self.page_size - 1) // self.page_size
        self.total_pages = max(1, self.total_pages)  # 确保至少有一页

        # 更新页码指示器
        self.update_page_indicator()

        return self.total_pages

    def update_with_data(self, items, current_page, total_pages=None, total_records=None):
        """使用新数据更新表格和分页状态

        这个方法会清空表格并设置新数据，同时更新分页状态。

        Args:
            items: 当前页的数据项列表
            current_page: 当前页码
            total_pages: 可选，总页数，如果提供了total_records则忽略此参数
            total_records: 可选，总记录数，如果提供则自动计算total_pages
        """
        # 清空表格并设置新数据
        self.table.clearContents()
        self.table.setRowCount(len(items))

        # 设置当前页的数据
        self.all_items = items

        # 设置当前页码
        self.current_page = current_page

        # 如果提供了总记录数，则计算总页数
        if total_records is not None:
            self.set_pagination_info(total_records)
        # 否则使用提供的总页数
        elif total_pages is not None:
            self.total_pages = max(1, total_pages)
            self.update_page_indicator()

        # 填充表格数据
        self._populate_table(items)
