import sys
import contextlib

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from nice_ui.ui.MainWindow import Window
# 导入资源文件
import components.lin_resource_rc


def main():
    app = QApplication(sys.argv)
    if sys.platform == "darwin":
        app.setWindowIcon(QIcon(":/icon/assets/lapped.png"))
    else:
        app.setWindowIcon(QIcon(":icon/assets/lapped.ico"))

    window = Window()
    window.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    import multiprocessing

    # macOS + PyInstaller 必须设置 multiprocessing 启动方法
    with contextlib.suppress(RuntimeError):
        multiprocessing.set_start_method("spawn", force=True)
    # 冻结支持：防止 multiprocessing 在 PyInstaller 打包后无限启动新进程
    multiprocessing.freeze_support()
    main()
