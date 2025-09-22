from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import QStringListModel

from vendor.qfluentwidgets import ComboBox, EditableComboBox
from components.resource_manager import StyleManager

class TransComboBox(ComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        StyleManager.apply_style(self, 'combo_box')


class SearchableComboBox(EditableComboBox):
    """支持搜索的下拉框组件"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 存储所有项目文本，用于自动完成
        self._all_texts = []

        # 设置占位符文本
        self.setPlaceholderText("搜索语言...")

        # 创建自动完成器
        self._completer = QCompleter()
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self.setCompleter(self._completer)

        # 禁用回车键添加新选项的功能
        self.returnPressed.disconnect()
        self.returnPressed.connect(self._onReturnPressed)

        # 重新应用自定义样式，覆盖 EditableComboBox 的默认样式
        StyleManager.apply_style(self, 'searchable_combo_box')

    def addItem(self, text, icon=None, userData=None):
        """添加项目到下拉框"""
        super().addItem(text, icon, userData)
        # 添加到文本列表
        self._all_texts.append(text)
        # 更新自动完成器
        self._update_completer()

    def addItems(self, texts):
        """批量添加项目"""
        for text in texts:
            self.addItem(text)

    def clear(self):
        """清空所有项目"""
        super().clear()
        self._all_texts.clear()
        self._update_completer()

    def _update_completer(self):
        """更新自动完成器的数据"""
        model = QStringListModel(self._all_texts)
        self._completer.setModel(model)

    def _onReturnPressed(self):
        """重写回车键处理，只允许选择现有选项，不允许添加新选项"""
        if not self.text():
            return

        current_text = self.text()

        # 查找完全匹配的选项
        index = self.findText(current_text)
        if index >= 0 and index != self.currentIndex():
            # 如果找到完全匹配项，选择它
            self._currentIndex = index
            self.currentIndexChanged.emit(index)
        elif index == -1:
            # 如果没有找到完全匹配，尝试找到部分匹配
            best_match = None
            best_match_index = -1

            for i, text in enumerate(self._all_texts):
                if current_text.lower() in text.lower():
                    best_match = text
                    best_match_index = i
                    break

            if best_match:
                # 找到部分匹配，设置为该选项
                self.setText(best_match)
                self._currentIndex = best_match_index
                self.currentIndexChanged.emit(best_match_index)
            else:
                # 没有找到任何匹配，恢复到之前的选择或清空
                if self.currentIndex() >= 0:
                    self.setText(self.itemText(self.currentIndex()))
                else:
                    self.setText("")

    def setCurrentText(self, text):
        """设置当前文本"""
        # 直接设置文本
        super().setText(text)

        # 查找匹配的索引并设置
        index = self.findText(text)
        if index >= 0:
            self._currentIndex = index

