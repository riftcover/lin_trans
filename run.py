import sys
import contextlib
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from nice_ui.ui.MainWindow import Window
# 导入资源文件
import components.lin_resource_rc


def set_windows_taskbar_icon():
    """
    设置 Windows 任务栏图标

    在 Windows 上，Python 应用默认会被归为同一个应用组，
    导致任务栏显示默认的 Python 图标。
    通过设置 AppUserModelID 可以让应用独立显示自定义图标。

    注意：必须在创建 QApplication 之前调用
    """
    if sys.platform == "win32":
        try:
            import ctypes
            # 设置唯一的 AppUserModelID
            # 格式：CompanyName.ProductName.SubProduct.VersionInformation
            # 使用固定的 ID，确保每次运行都是同一个应用
            app_id = "Locoweed3.LappedAI"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            return True
        except Exception as e:
            print(f"警告: 无法设置任务栏图标: {e}")
            return False
    return True


def main():
    # Windows 任务栏图标设置（必须在创建 QApplication 之前调用）
    set_windows_taskbar_icon()

    app = QApplication(sys.argv)
    tray_icon = QSystemTrayIcon(QIcon(":/icon/assets/lapped.png"), app)
    # 创建托盘菜单
    menu = QMenu()
    action = menu.addAction("Exit")
    tray_icon.setContextMenu(menu)

    # 显示任务栏图标
    tray_icon.show()

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
