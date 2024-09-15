from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class StatusLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(70, 22)  # 调整宽度和高度
        self.setStyleSheet("""
            QLabel {
                border-radius: 3px;
                font-size: 11px;  # 稍微减小字体大小
            }
        """)

    def set_status(self, status):
        self.setText(status)
        if status == "已完成":
            self.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    border: 1px solid #2196F3;
                    color: #1565C0;
                    border-radius: 3px;
                    font-size: 11px;
                }
                        """)
        elif status == "处理失败":
            self.setStyleSheet("""
                QLabel {
                    background-color: #FFEBEE;
                    border: 1px solid #FF5252;
                    color: #055160;
                    border-radius: 3px;
                    font-size: 11px;
                }
            """)
        elif status == "排队中":
            self.setStyleSheet("""
                QLabel {
                    background-color: #cff4fc;
                    border: 1px solid #0dcaf0;
                    color: #538fa2;
                    border-radius: 3px;
                    font-size: 11px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: #E0E0E0;
                    border: 1px solid #9E9E9E;
                    color: #616161;
                    border-radius: 3px;
                    font-size: 11px;
                }
            """)

