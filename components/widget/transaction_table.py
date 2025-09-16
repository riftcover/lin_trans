import pytz
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
        headers = ['时间','任务','算力', '订单号']
        column_widths = [220,200, 100, 250]  # -1表示自适应

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
            # 时间 - 处理毫秒级时间戳
            timestamp_ms = transaction.get('created_at', 0)
            if timestamp_ms:
                try:
                    # 将毫秒时间戳转换为秒
                    timestamp_sec = timestamp_ms / 1000
                    # 创建UTC时间
                    utc_time = datetime.fromtimestamp(timestamp_sec, pytz.UTC)

                    # 转换为中国时区
                    china_tz = pytz.timezone('Asia/Shanghai')
                    china_time = utc_time.astimezone(china_tz)

                    # 格式化为指定格式
                    formatted_time = china_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logger.error(f"时间戳转换错误: {e}, timestamp_ms={timestamp_ms}")
                    formatted_time = '时间格式错误'
            else:
                formatted_time = '未知时间'
            self.table.setItem(row, 0, QTableWidgetItem(formatted_time))

            # 任务类型
            description = str(transaction.get('description', ''))
            description_item = QTableWidgetItem(description)
            description_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, description_item)

            # 使用额度
            amount = str(transaction.get('amount', 0))
            amount_item = QTableWidgetItem(amount)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, amount_item)

            # 订单号
            order_id = transaction.get('order_id', '未知')
            self.table.setItem(row, 3, QTableWidgetItem(str(order_id)))
