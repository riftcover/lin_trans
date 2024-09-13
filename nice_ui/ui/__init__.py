# 将修改后的库路径添加到sys.path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vendor'))


# 我也不知道为什么为啥不生效，网上说这样做可以使得库的优先级高于系统的库，这样就可以覆盖系统的库了。
# import qfluentwidgets
# 在 __init__.py 文件中

from PySide6.QtCore import QSize

# 字幕编辑窗口大小
SUBTITLE_EDIT_DIALOG_SIZE = QSize(1300, 800)
# 主窗口大小
MAIN_WINDOW_SIZE = QSize(900, 700)
TABLE_ROW_HEIGHT = 40
# ...其他常量