import sys

from PySide6.QtWidgets import QApplication

from nice_ui.ui.MainWindow import Window



app = QApplication(sys.argv)
w = Window()
w.show()
app.exec()



