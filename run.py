import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from videotrans.ui.en import Ui_MainWindow


# longin是".ui"文件转换为".py"文件的文件名
# ui_From来自.ui转.py的文件中第一个类的类名

class MyWindow(QMainWindow):  # 需要和ui创建时的窗体一致
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = MyWindow()
    demo.show()
    sys.exit(app.exec())


