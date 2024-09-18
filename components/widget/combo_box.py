from vendor.qfluentwidgets import ComboBox
from components.resource_manager import StyleManager

class TransComboBox(ComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        StyleManager.apply_style(self, 'combo_box')