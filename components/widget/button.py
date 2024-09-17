from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy
from vendor.qfluentwidgets import PrimaryPushButton

from components.resource_manager import StyleManager


class DeleteButton(PrimaryPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.updateStyle()

    def initUI(self):
        self.setFixedSize(QSize(60,28))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def updateStyle(self):
        # 加载原有样式
        original_style = self.styleSheet()
        new_style = StyleManager().get_style('delete_button')
        # 合并原有样式和新样式
        self.setStyleSheet(original_style + new_style)

if __name__ == '__main__':
    a = DeleteButton()
