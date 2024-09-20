from PySide6.QtWidgets import QSplitter


class CustomSplitter(QSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHandleWidth(5)  # 增加宽度到3像素
        self.setStyleSheet("""
            QSplitter::handle {
                background-color: #E0E5EA;
            }
            QSplitter::handle:hover {
                background-color: #B0C4DE;
            }
        """)
