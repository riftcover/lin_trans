from PySide6.QtCore import QSize

from vendor.qfluentwidgets import ComboBox
from components.resource_manager import StyleManager

class TransComboBox(ComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        StyleManager.apply_style(self, 'combo_box')

    """
    下面的内容是，组件宽度自动根据下拉框宽度设置，会有部分性能损耗，因此注释掉
    在使用时，请根据实际情况手动填写固定值
    """
        # self.setMaximumWidth(200)  # 设置最大宽度


    # def sizeHint(self):
    #     # 获取下拉列表中最长项的宽度
    #     width = max(
    #         self.fontMetrics().boundingRect(self.itemText(i)).width()
    #         for i in range(self.count())
    #     )
    #     # 添加一些填充和箭头的宽度
    #     width += 42  # 根据需要调整这个值
    #
    #     # 获取单个项目的高度
    #     height = self.fontMetrics().height() + 10  # 添加一些垂直填充
    #     # 计算弹出框的高度
    #     print(f"TransComboBox 宽度: {width} 高度: {height}")
    #     return QSize(width, height)
    #
    # def showPopup(self):
    #     # 显示弹出框前更新尺寸
    #     self.updateGeometry()
    #     super().showPopup()
    #
    # def hidePopup(self):
    #     # 隐藏弹出框后更新尺寸
    #     self.updateGeometry()
    #     super().hidePopup()