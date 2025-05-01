import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

# 导入分页表格组件
from components.widget.pagination import PaginatedTableWidget


class PaginationExample(QMainWindow):
    """PaginatedTableWidget组件使用示例"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("分页表格示例")
        self.resize(800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建分页表格组件
        # 设置表头和列宽
        headers = ["ID", "姓名", "年龄", "职业"]
        column_widths = [80, 150, 80, 0]  # 最后一列自适应宽度
        
        self.table_widget = CustomPaginatedTable(
            parent=self,
            page_size=10,  # 每页显示10条记录
            headers=headers,
            column_widths=column_widths,
            stretch_column=3  # 第4列自适应宽度
        )
        
        # 添加到主布局
        main_layout.addWidget(self.table_widget)
        
        # 生成示例数据
        self.generate_sample_data()
        
    def generate_sample_data(self):
        """生成示例数据"""
        # 创建100条示例数据
        data = []
        for i in range(1, 101):
            # 根据ID生成不同的职业
            profession = "工程师" if i % 3 == 0 else "设计师" if i % 3 == 1 else "产品经理"
            
            # 创建一条记录
            record = {
                "id": i,
                "name": f"用户{i}",
                "age": 20 + (i % 30),  # 20-49岁
                "profession": profession
            }
            data.append(record)
        
        # 设置表格数据
        self.table_widget.set_data(data)


class CustomPaginatedTable(PaginatedTableWidget):
    """自定义分页表格，实现数据填充逻辑"""
    
    def _populate_table(self, items):
        """
        实现父类的抽象方法，填充表格数据
        
        Args:
            items: 当前页的数据项列表
        """
        # 设置表格行数
        self.table.setRowCount(len(items))
        
        # 填充数据
        for row, item in enumerate(items):
            # 设置ID列
            self.table.setItem(row, 0, self._create_table_item(str(item["id"])))
            
            # 设置姓名列
            self.table.setItem(row, 1, self._create_table_item(item["name"]))
            
            # 设置年龄列
            self.table.setItem(row, 2, self._create_table_item(str(item["age"])))
            
            # 设置职业列
            self.table.setItem(row, 3, self._create_table_item(item["profession"]))
    
    def _create_table_item(self, text):
        """创建表格项并设置对齐方式"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PaginationExample()
    window.show()
    sys.exit(app.exec())
