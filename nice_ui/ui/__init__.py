import os

from PySide6.QtCore import QSize, QSettings

# ...其他常量
__version__ = "0.2.1"
# 字幕编辑窗口大小
SUBTITLE_EDIT_DIALOG_SIZE = QSize(1300, 800)
# 主窗口大小
MAIN_WINDOW_SIZE = QSize(1000, 700)
TABLE_ROW_HEIGHT = 40
LANGUAGE_WIDTH = 110


class SettingsManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # 获取当前工作目录
            current_directory = os.path.basename(os.getcwd())
            cls._instance = QSettings(
                "Locoweed3",
                f"LinLInTrans_{current_directory}"
            )
        return cls._instance
