import hashlib
from pathlib import Path

from PySide6.QtCore import QSize, QSettings

# ...其他常量
__version__ = "0.3.3"
# 字幕编辑窗口大小
SUBTITLE_EDIT_DIALOG_SIZE = QSize(1300, 800)
# 主窗口大小
MAIN_WINDOW_SIZE = QSize(1000, 700)
TABLE_ROW_HEIGHT = 40
LANGUAGE_WIDTH = 140


class SettingsManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # 使用项目根目录的绝对路径生成唯一标识
            # 这样即使两个项目目录名称相同，也不会冲突
            project_root = Path.cwd().resolve()

            # 生成路径的短哈希（取前8位，足够区分不同项目）
            path_hash = hashlib.md5(str(project_root).encode()).hexdigest()[:8]

            # 应用名称格式：LinLInTrans_<目录名>_<路径哈希>
            # 例如：LinLInTrans_lin_trans_a1b2c3d4
            app_name = f"LappedAI_{path_hash}"

            cls._instance = QSettings("Locoweed3", app_name)
        return cls._instance
