import os

from PySide6.QtCore import QFile, QTextStream, QDir
from components import lin_resource_rc


class StyleManager:
    """
    1. lin_resource.qrc中添加相关路径
    2. pyside6-rcc lin_resource.qrc -o lin_resource_rc.py生成二进制文件
    3. resource_manager.py中_load_all_styles添加对应映射
    """
    _instance = None
    _styles = {}

    def __new__(cls):
        # 单例模式
        if cls._instance is None:
            cls._instance = super(StyleManager, cls).__new__(cls)
            cls._instance._load_all_styles()
        return cls._instance

    def _load_all_styles(self):
        # 加载所有样式
        qss_dir = ":/qss/themes/"

        # 获取目录中的所有文件
        qss_path = QDir(qss_dir)
        files = qss_path.entryList(["*.qss"], QDir.Files)

        for file_name in files:
            style_name = os.path.splitext(file_name)[0]  # 移除.qss扩展名
            full_path = f"{qss_dir}{file_name}"
            self._styles[style_name] = self._load_stylesheet(full_path)

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

if __name__ == '__main__':
    # 测试
    style_manager = StyleManager()
    print(style_manager.get_style('delete_button'))
