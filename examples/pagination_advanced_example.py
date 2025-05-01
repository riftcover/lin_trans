import sys
import json
import random
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QHBoxLayout, QComboBox, QPushButton, QLabel, 
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor

# 导入分页表格组件
from components.widget.pagination import PaginatedTableWidget
from vendor.qfluentwidgets import (
    PrimaryPushButton, ComboBox, LineEdit, 
    SearchLineEdit, InfoBar, InfoBarPosition
)


class MockApiClient:
    """模拟API客户端，用于模拟网络请求"""
    
    def __init__(self):
        # 生成模拟数据
        self.all_data = self._generate_mock_data(200)
        
    def _generate_mock_data(self, count):
        """生成模拟数据"""
        data = []
        status_options = ["待处理", "处理中", "已完成", "已取消"]
        
        # 生成随机日期，最近30天内
        now = datetime.now()
        
        for i in range(1, count + 1):
            # 随机日期
            days_ago = random.randint(0, 30)
            random_date = now - timedelta(days=days_ago)
            date_str = random_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # 随机状态
            status = random.choice(status_options)
            
            # 随机金额
            amount = round(random.uniform(10, 1000), 2)
            
            # 创建一条记录
            record = {
                "id": i,
                "order_number": f"ORD-{i:06d}",
                "date": date_str,
                "customer": f"客户{i % 20 + 1}",
                "amount": amount,
                "status": status
            }
            data.append(record)
        
        return data
    
    def get_orders(self, page=1, page_size=10, status_filter=None):
        """
        获取订单数据
        
        Args:
            page: 页码，从1开始
            page_size: 每页记录数
            status_filter: 状态过滤条件
            
        Returns:
            dict: 包含分页数据和总记录数
        """
        # 模拟网络延迟
        QTimer.singleShot(random.randint(300, 800), lambda: None)
        
        # 过滤数据
        filtered_data = self.all_data
        if status_filter and status_filter != "全部":
            filtered_data = [item for item in self.all_data if item["status"] == status_filter]
        
        # 计算总记录数
        total_records = len(filtered_data)
        
        # 计算总页数
        total_pages = (total_records + page_size - 1) // page_size
        
        # 计算当前页的数据范围
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_records)
        
        # 获取当前页的数据
        page_data = filtered_data[start_idx:end_idx]
        
        # 返回结果
        return {
            "data": page_data,
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": page
        }


class AdvancedPaginationExample(QMainWindow):
    """高级分页表格示例，包含搜索、过滤和异步加载数据"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("高级分页表格示例")
        self.resize(1000, 700)
        
        # 创建API客户端
        self.api_client = MockApiClient()
        
        # 当前过滤条件
        self.current_status_filter = "全部"
        
        # 创建UI
        self._setup_ui()
        
        # 加载初始数据
        self._load_data()
        
    def _setup_ui(self):
        """设置UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建标题
        title_label = QLabel("订单管理系统")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)
        
        # 状态过滤下拉框
        self.status_filter = ComboBox()
        self.status_filter.addItems(["全部", "待处理", "处理中", "已完成", "已取消"])
        self.status_filter.setCurrentText("全部")
        self.status_filter.setMinimumWidth(120)
        self.status_filter.currentTextChanged.connect(self._on_filter_changed)
        
        # 搜索框
        self.search_box = SearchLineEdit()
        self.search_box.setPlaceholderText("搜索订单号或客户名称")
        self.search_box.textChanged.connect(self._on_search_text_changed)
        
        # 刷新按钮
        self.refresh_button = PrimaryPushButton("刷新")
        self.refresh_button.clicked.connect(self._load_data)
        
        # 添加到工具栏布局
        toolbar_layout.addWidget(QLabel("状态:"))
        toolbar_layout.addWidget(self.status_filter)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.search_box)
        toolbar_layout.addWidget(self.refresh_button)
        
        # 添加工具栏到主布局
        main_layout.addLayout(toolbar_layout)
        
        # 创建分页表格组件
        headers = ["订单号", "日期", "客户", "金额", "状态", "操作"]
        column_widths = [150, 180, 120, 100, 100, 0]  # 最后一列自适应宽度
        
        self.table_widget = OrderTableWidget(
            parent=self,
            page_size=10,
            headers=headers,
            column_widths=column_widths,
            stretch_column=5  # 第6列自适应宽度
        )
        
        # 连接页码变化信号
        self.table_widget.pageChanged.connect(self._on_page_changed)
        
        # 添加表格到主布局
        main_layout.addWidget(self.table_widget)
    
    def _load_data(self):
        """加载数据"""
        # 显示加载中提示
        InfoBar.info(
            title="加载中",
            content="正在加载数据，请稍候...",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
        # 禁用刷新按钮，防止重复点击
        self.refresh_button.setEnabled(False)
        
        # 模拟网络请求延迟
        QTimer.singleShot(800, self._fetch_data)
    
    def _fetch_data(self):
        """获取数据"""
        try:
            # 获取当前页码
            current_page = self.table_widget.get_current_page()
            
            # 调用API获取数据
            result = self.api_client.get_orders(
                page=current_page,
                page_size=10,
                status_filter=self.current_status_filter
            )
            
            # 更新表格数据
            self.table_widget.update_with_data(
                items=result["data"],
                current_page=result["current_page"],
                total_pages=result["total_pages"],
                total_records=result["total_records"]
            )
            
            # 显示成功提示
            InfoBar.success(
                title="加载成功",
                content=f"共加载 {result['total_records']} 条记录",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            # 显示错误提示
            InfoBar.error(
                title="加载失败",
                content=f"数据加载失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        finally:
            # 恢复刷新按钮
            self.refresh_button.setEnabled(True)
    
    def _on_page_changed(self, page):
        """页码变化处理"""
        self._load_data()
    
    def _on_filter_changed(self, status):
        """过滤条件变化处理"""
        self.current_status_filter = status
        # 重置到第一页
        self.table_widget.current_page = 1
        self.table_widget.update_page_indicator()
        # 重新加载数据
        self._load_data()
    
    def _on_search_text_changed(self, text):
        """搜索文本变化处理"""
        # 这里简化处理，实际应用中可能需要更复杂的搜索逻辑
        # 例如，延迟搜索、服务器端搜索等
        pass
    
    def _on_view_details(self, order_id):
        """查看订单详情"""
        InfoBar.info(
            title="查看详情",
            content=f"查看订单 {order_id} 的详情",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def _on_edit_order(self, order_id):
        """编辑订单"""
        InfoBar.info(
            title="编辑订单",
            content=f"编辑订单 {order_id}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )


class OrderTableWidget(PaginatedTableWidget):
    """订单表格组件"""
    
    # 自定义信号
    viewDetailsClicked = Signal(str)  # 查看详情按钮点击信号
    editOrderClicked = Signal(str)    # 编辑订单按钮点击信号
    
    def __init__(self, parent=None, page_size=10, headers=None, column_widths=None, stretch_column=None):
        super().__init__(parent, page_size, headers, column_widths, stretch_column)
        
        # 连接信号到父窗口的槽函数
        if parent:
            self.viewDetailsClicked.connect(parent._on_view_details)
            self.editOrderClicked.connect(parent._on_edit_order)
    
    def _populate_table(self, items):
        """填充表格数据"""
        # 设置表格行数
        self.table.setRowCount(len(items))
        
        # 填充数据
        for row, item in enumerate(items):
            # 订单号
            self.table.setItem(row, 0, self._create_table_item(item["order_number"]))
            
            # 日期
            self.table.setItem(row, 1, self._create_table_item(item["date"]))
            
            # 客户
            self.table.setItem(row, 2, self._create_table_item(item["customer"]))
            
            # 金额
            amount_item = self._create_table_item(f"¥{item['amount']:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, amount_item)
            
            # 状态
            status_item = self._create_table_item(item["status"])
            # 根据状态设置不同的颜色
            if item["status"] == "已完成":
                status_item.setForeground(QColor("#28a745"))
            elif item["status"] == "处理中":
                status_item.setForeground(QColor("#007bff"))
            elif item["status"] == "待处理":
                status_item.setForeground(QColor("#ffc107"))
            elif item["status"] == "已取消":
                status_item.setForeground(QColor("#dc3545"))
            self.table.setItem(row, 4, status_item)
            
            # 操作按钮
            self._create_action_buttons(row, 5, item["order_number"])
    
    def _create_table_item(self, text):
        """创建表格项"""
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def _create_action_buttons(self, row, col, order_id):
        """创建操作按钮"""
        # 创建按钮容器
        from PySide6.QtWidgets import QWidget, QHBoxLayout
        
        # 创建按钮布局
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 2, 5, 2)
        button_layout.setSpacing(10)
        
        # 查看详情按钮
        view_button = QPushButton("查看")
        view_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 8px;
                color: #007bff;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        view_button.clicked.connect(lambda: self.viewDetailsClicked.emit(order_id))
        
        # 编辑按钮
        edit_button = QPushButton("编辑")
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px 8px;
                color: #28a745;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        edit_button.clicked.connect(lambda: self.editOrderClicked.emit(order_id))
        
        # 添加按钮到布局
        button_layout.addWidget(view_button)
        button_layout.addWidget(edit_button)
        button_layout.addStretch()
        
        # 设置单元格部件
        self.table.setCellWidget(row, col, button_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedPaginationExample()
    window.show()
    sys.exit(app.exec())
