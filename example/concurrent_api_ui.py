import sys
import asyncio
import threading
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                              QVBoxLayout, QLabel, QWidget, QTextEdit,
                              QHBoxLayout, QSplitter, QFrame)
from PySide6.QtCore import QObject, Signal, Slot, Qt

# 导入API客户端
from concurrent_api_practical import ApiClient

# 信号类，用于在线程间通信
class ApiSignals(QObject):
    # 定义信号
    version_received = Signal(dict)
    profile_received = Signal(dict)
    api_error = Signal(str)
    all_completed = Signal()

class AsyncApiHandler:
    """处理异步API调用的类"""

    def __init__(self):
        """初始化"""
        self.signals = ApiSignals()
        self.client = ApiClient()  # 仍然使用ApiClient类来调用API方法
        self.loop = None
        self.thread = None

    def start_api_calls(self):
        """开始API调用"""
        # 创建并启动线程
        self.thread = threading.Thread(target=self._run_async_loop)
        self.thread.daemon = True
        self.thread.start()

    def _run_async_loop(self):
        """在新线程中运行异步事件循环"""
        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 运行异步任务
        try:
            self.loop.run_until_complete(self._fetch_all_data())
        except Exception as e:
            self.signals.api_error.emit(f"API调用出错: {str(e)}")
        finally:
            self.loop.close()

    async def _fetch_all_data(self):
        """获取所有API数据"""
        try:
            # 创建任务字典，存储任务和名称的映射
            tasks = {
                "version": asyncio.create_task(self.client.ask_version()),
                "profile": asyncio.create_task(self.client.get_profile())
            }

            # 使用as_completed依次处理完成的任务
            for task_name, task in tasks.items():
                try:
                    result = await task
                    # 根据任务名称发送对应的信号
                    if task_name == "version":
                        self.signals.version_received.emit(result)
                    else:
                        self.signals.profile_received.emit(result)
                except Exception as e:
                    self.signals.api_error.emit(f"{task_name} 调用失败: {str(e)}")

            # 发出所有任务完成的信号
            self.signals.all_completed.emit()
        except Exception as e:
            self.signals.api_error.emit(f"API调用出错: {str(e)}")

class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()

        # 设置窗口属性
        self.setWindowTitle("异步API调用示例")
        self.setGeometry(100, 100, 800, 600)

        # 创建API处理器
        self.api_handler = AsyncApiHandler()

        # 连接信号
        self.api_handler.signals.version_received.connect(self.on_version_received)
        self.api_handler.signals.profile_received.connect(self.on_profile_received)
        self.api_handler.signals.api_error.connect(self.on_api_error)
        self.api_handler.signals.all_completed.connect(self.on_all_completed)

        # 设置UI
        self._setup_ui()

    def _setup_ui(self):
        """设置UI界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建顶部控制区域
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_frame)

        # 创建按钮和状态标签
        self.fetch_button = QPushButton("获取API数据")
        self.fetch_button.setMinimumHeight(40)
        self.fetch_button.clicked.connect(self.on_fetch_clicked)

        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)

        # 添加到控制布局
        control_layout.addWidget(self.fetch_button)
        control_layout.addWidget(self.status_label)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 创建左侧版本信息区域
        version_frame = QFrame()
        version_frame.setFrameShape(QFrame.StyledPanel)
        version_layout = QVBoxLayout(version_frame)

        version_label = QLabel("版本信息")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.version_text = QTextEdit()
        self.version_text.setReadOnly(True)

        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_text)

        # 创建右侧用户资料区域
        profile_frame = QFrame()
        profile_frame.setFrameShape(QFrame.StyledPanel)
        profile_layout = QVBoxLayout(profile_frame)

        profile_label = QLabel("用户资料")
        profile_label.setAlignment(Qt.AlignCenter)
        profile_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.profile_text = QTextEdit()
        self.profile_text.setReadOnly(True)

        profile_layout.addWidget(profile_label)
        profile_layout.addWidget(self.profile_text)

        # 添加到分割器
        splitter.addWidget(version_frame)
        splitter.addWidget(profile_frame)

        # 添加到主布局
        main_layout.addWidget(control_frame)
        main_layout.addWidget(splitter, 1)  # 1是拉伸因子，让分割器占据更多空间

    @Slot()
    def on_fetch_clicked(self):
        """点击获取按钮的处理函数"""
        # 更新UI状态
        self.fetch_button.setEnabled(False)
        self.status_label.setText("正在获取数据...")
        self.version_text.clear()
        self.profile_text.clear()

        # 开始API调用
        self.api_handler.start_api_calls()

    @Slot(dict)
    def on_version_received(self, data):
        """接收到版本信息的处理函数"""
        # 格式化JSON并显示
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        print(f"formatted_json:{formatted_json}")
        self.version_text.setText(formatted_json)
        self.status_label.setText("已获取版本信息")

    @Slot(dict)
    def on_profile_received(self, data):
        """接收到用户资料的处理函数"""
        # 格式化JSON并显示
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        print(f'formatted_json:{formatted_json}')
        self.profile_text.setText(formatted_json)
        self.status_label.setText("已获取用户资料")

    @Slot(str)
    def on_api_error(self, error_msg):
        """API错误处理函数"""
        self.status_label.setText(error_msg)
        self.fetch_button.setEnabled(True)

    @Slot()
    def on_all_completed(self):
        """所有API调用完成的处理函数"""
        self.status_label.setText("所有数据获取完成")
        self.fetch_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
