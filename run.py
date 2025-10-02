import sys

from PySide6.QtWidgets import QApplication

from nice_ui.ui.MainWindow import Window


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    import multiprocessing

    # macOS + PyInstaller 必须设置 multiprocessing 启动方法
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # 已经设置过了，忽略

    # 冻结支持：防止 multiprocessing 在 PyInstaller 打包后无限启动新进程
    multiprocessing.freeze_support()
    main()
