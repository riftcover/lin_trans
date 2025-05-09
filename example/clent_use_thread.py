import time
import asyncio
import httpx
from typing import Dict, Any
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PySide6.QtCore import QThread, Signal, Slot
import sys

# 接口配置
ENDPOINTS = {
    "profile": {
        "url": "http://127.0.0.1:8000/api/client/tt",
        "method": "GET",
        "name": "Profile接口"
    },
    "version": {
        "url": "http://127.0.0.1:8000/api/client/check-version",
        "method": "POST",
        "name": "Version接口",
        "json": {
            "platform": "windows",
            "current_version": "0.2.1"
        }
    }
}

headers = {
    "Content-Type": "application/json"
}

class AsyncWorker(QThread):
    """异步工作线程"""
    result_ready = Signal(str, str)  # 信号：接口名称, 结果

    def __init__(self):
        super().__init__()
        self.loop = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.fetch_all_data())

    async def make_request(self, client: httpx.AsyncClient, endpoint_config: Dict[str, Any]) -> None:
        try:
            if endpoint_config["method"] == "GET":
                response = await client.get(endpoint_config["url"], headers=headers, timeout=10)
            else:
                response = await client.post(
                    endpoint_config["url"],
                    headers=headers,
                    json=endpoint_config.get("json"),
                    timeout=10
                )
            result = response.json()
            self.result_ready.emit(endpoint_config["name"], str(result))
        except Exception as e:
            self.result_ready.emit(endpoint_config["name"], f"错误: {str(e)}")

    async def fetch_all_data(self):
        async with httpx.AsyncClient() as client:
            tasks = [
                self.make_request(client, config)
                for config in ENDPOINTS.values()
            ]
            await asyncio.gather(*tasks)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("接口数据获取")
        self.setMinimumSize(600, 400)

        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建按钮
        self.fetch_button = QPushButton("获取数据")
        self.fetch_button.clicked.connect(self.start_fetch)
        layout.addWidget(self.fetch_button)

        # 创建文本显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)

        # 创建工作线程
        self.worker = AsyncWorker()
        self.worker.result_ready.connect(self.update_display)

    @Slot()
    def start_fetch(self):
        self.text_display.clear()
        self.fetch_button.setEnabled(False)
        self.text_display.append("正在获取数据...")
        self.worker.start()

    @Slot(str, str)
    def update_display(self, endpoint_name: str, result: str):
        self.text_display.append(f"\n{endpoint_name}:\n{result}")
        # 检查是否所有接口都返回了结果
        if self.text_display.toPlainText().count("接口") >= len(ENDPOINTS):
            self.fetch_button.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()