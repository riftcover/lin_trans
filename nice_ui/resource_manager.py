from PySide6.QtCore import QFile, QTextStream
from tmp import lin_resource_rc

class StyleManager:
    _instance = None
    _styles = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StyleManager, cls).__new__(cls)
            cls._instance._load_all_styles()
        return cls._instance

    def _load_all_styles(self):
        # 加载所有样式
        self._styles['time_edit'] = self._load_stylesheet(":/qss/themes/lin_time_edit.qss")
        # 添加其他样式...

    def _load_stylesheet(self, resource_path):
        file = QFile(resource_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            return stream.readAll()
        return ""

    def get_style(self, style_name):
        return self._styles.get(style_name, "")

    @staticmethod
    def apply_style(widget, style_name):
        style = StyleManager().get_style(style_name)
        widget.setStyleSheet(style)