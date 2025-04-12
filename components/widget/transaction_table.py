from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import Qt
from datetime import datetime

from utils import logger
from .pagination import PaginatedTableWidget


class TransactionTableWidget(PaginatedTableWidget):
    """交易记录分页表格组件"""

    def __init__(self, parent=None, page_size=10):
        """初始化交易记录分页表格

        Args:
            parent: 父组件
            page_size: 每页显示的记录数，默认为10
        """
        # 设置表头和列宽
        headers = ['时间', '算力', '订单号']
        column_widths = [280, 200, 300]  # -1表示自适应


        super().__init__(
            parent=parent,
            page_size=page_size,
            headers=headers,
            column_widths=column_widths,
            stretch_column=2  # 订单号列自适应
        )

        # 隐藏网格线和行号
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

    def _populate_table(self, transactions):
        """填充交易记录表格

        Args:
            transactions: 当前页的交易记录列表
        """
        for row, transaction in enumerate(transactions):
            # 时间
            created_at = transaction.get('created_at', '')
            if created_at:
                try:
                    # 处理ISO 8601格式的时间字符串
                    dt = datetime.fromisoformat(created_at)
                    # 转换为QDateTime
                    qdt = QDateTime.fromString(dt.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss")
                    time_str = qdt.toString("yyyy-MM-dd HH:mm:ss")
                except Exception as e:
                    logger.error(f"时间格式转换失败: {e}")
                    # 简单的字符串处理方法作为最后的备选
                    try:
                        simple_time = created_at.replace('T', ' ').split('.')[0]
                        time_str = simple_time
                    except:
                        time_str = created_at
            else:
                time_str = '未知时间'
            self.table.setItem(row, 0, QTableWidgetItem(time_str))

            # 使用额度
            amount = str(transaction.get('amount', 0))
            self.table.setItem(row, 1, QTableWidgetItem(amount))

            # 订单号
            order_id = transaction.get('order_id', '未知')
            self.table.setItem(row, 2, QTableWidgetItem(str(order_id)))
