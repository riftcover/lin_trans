import sys
import os
from PySide6.QtWidgets import QApplication

from nice_ui.ui.MainWindow import Window


# 将当前目录添加到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 打印 sys.path 以进行调试
print("sys.path:", sys.path)

app = QApplication(sys.argv)
w = Window()
w.show()
app.exec()
