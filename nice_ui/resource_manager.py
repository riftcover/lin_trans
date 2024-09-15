from PySide6.QtCore import QFile, QTextStream


class StyleManager:
    """
    1. lin_resource.qrc中添加相关路径
    2. pyside6-rcc lin_resource.qrc -o lin_resource_rc.py生成二进制文件
    3. resource_manager.py中_load_all_styles添加对应映射
    """
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
        self._styles['status_label'] = self._load_stylesheet(":/qss/themes/lin_status_label.qss")
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