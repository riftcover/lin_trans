import sys
import asyncio
import json
from typing import Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                              QVBoxLayout, QLabel, QWidget, QTextEdit,
                              QHBoxLayout, QSplitter, QFrame)
from PySide6.QtCore import QObject, Signal, Slot, Qt, QThread

# 导入API客户端
from concurrent_api_practical import ApiClient

class ApiSignals(QObject):
    """API信号管理"""
    data_received = Signal(str, dict)  # endpoint_name, data
    error_occurred = Signal(str, str)  # endpoint_name, error_message
    all_completed = Signal()

class ApiWorker(QThread):
    """API工作线程"""
    def __init__(self):
        super().__init__()
        self.signals = ApiSignals()
        self.client = ApiClient()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def run(self):
        """运行异步事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._fetch_all_data())
        except Exception as e:
            self.signals.error_occurred.emit("system", str(e))
        finally:
            self.loop.close()

    async def _fetch_all_data(self):
        """获取所有API数据"""
        tasks = {
            "version": asyncio.create_task(self.client.ask_version()),
            "profile": asyncio.create_task(self.client.get_profile())
        }
        
        for name, task in tasks.items():
            try:
                result = await task
                self.signals.data_received.emit(name, result)
            except Exception as e:
                self.signals.error_occurred.emit(name, str(e))
        
        self.signals.all_completed.emit()

class ResultDisplay(QFrame):
    """结果显示组件"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # 文本显示
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        
        layout.addWidget(title_label)
        layout.addWidget(self.text_display)

    def update_content(self, data: dict):
        """更新显示内容"""
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        self.text_display.setText(formatted_json)

    def clear(self):
        """清空显示"""
        self.text_display.clear()

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_api_worker()

    def _setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("异步API调用示例")
        self.setGeometry(100, 100, 800, 600)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 控制区域
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_frame)

        self.fetch_button = QPushButton("获取API数据")
        self.fetch_button.setMinimumHeight(40)
        self.fetch_button.clicked.connect(self._on_fetch_clicked)

        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)

        control_layout.addWidget(self.fetch_button)
        control_layout.addWidget(self.status_label)

        # 结果显示区域
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.version_display = ResultDisplay("版本信息")
        self.profile_display = ResultDisplay("用户资料")

        splitter.addWidget(self.version_display)
        splitter.addWidget(self.profile_display)

        main_layout.addWidget(control_frame)
        main_layout.addWidget(splitter, 1)

    def _setup_api_worker(self):
        """设置API工作线程"""
        self.api_worker = ApiWorker()
        self.api_worker.signals.data_received.connect(self._on_data_received)
        self.api_worker.signals.error_occurred.connect(self._on_error_occurred)
        self.api_worker.signals.all_completed.connect(self._on_all_completed)

    @Slot()
    def _on_fetch_clicked(self):
        """点击获取按钮"""
        self.fetch_button.setEnabled(False)
        self.status_label.setText("正在获取数据...")
        self.version_display.clear()
        self.profile_display.clear()
        self.api_worker.start()

    @Slot(str, dict)
    def _on_data_received(self, endpoint_name: str, data: dict):
        """接收到数据"""
        if endpoint_name == "version":
            self.version_display.update_content(data)
            self.status_label.setText("已获取版本信息")
        else:
            self.profile_display.update_content(data)
            self.status_label.setText("已获取用户资料")

    @Slot(str, str)
    def _on_error_occurred(self, endpoint_name: str, error_msg: str):
        """发生错误"""
        if endpoint_name == "system":
            self.status_label.setText(f"系统错误: {error_msg}")
        else:
            endpoint_name = "版本信息" if endpoint_name == "version" else "用户资料"
            self.status_label.setText(f"{endpoint_name}获取失败: {error_msg}")

    @Slot()
    def _on_all_completed(self):
        """所有请求完成"""
        self.status_label.setText("所有数据获取完成")
        self.fetch_button.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
