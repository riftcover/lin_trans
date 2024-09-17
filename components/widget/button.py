from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy
from qfluentwidgets import PrimaryPushButton


class DeleteButton(PrimaryPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.updateStyle()

    def initUI(self):
        self.setFixedSize(QSize(60,28))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def updateStyle(self):
        new_style = """
        DeleteButton { 
            background-color: #e74c3c !important;
            border: 1px solid #e74c3c !important;
         }
        DeleteButton:hover { 
            background-color: #f17a6f !important; 
            border: 1px solid #f17a6f !important;
        }
        DeleteButton:pressed { 
            background-color: #c0392b !important; 
        }
        """
        # 合并原有样式和新样式
        self.setStyleSheet(self.styleSheet() + new_style)
