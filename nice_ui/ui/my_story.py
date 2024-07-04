import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QPushButton, QCheckBox, QProgressBar, QComboBox,
                               QLineEdit, QFrame, QMainWindow)
from PySide6.QtCore import Qt
from qfluentwidgets import TableWidget, isDarkTheme, setTheme, Theme, TableView, TableItemDelegate, setCustomStyleSheet, CheckBox, ProgressBar, ComboBox, PushButton, SubtitleLabel, setFont


class TableApp(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()

    def setupUi(self):

        layout = QVBoxLayout()

        # 顶部布局
        topLayout = QHBoxLayout()
        self.selectAllBtn = QCheckBox("全选")
        self.selectAllBtn.stateChanged.connect(self.selectAll)
        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("输入文件名搜索")
        topLayout.addWidget(self.selectAllBtn)
        topLayout.addStretch()
        topLayout.addWidget(self.searchInput)

        layout.addLayout(topLayout)

        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.horizontalHeader().setVisible(False)  # 隐藏表头
        self.table.verticalHeader().setVisible(False)  # 隐藏行号
        self.table.setShowGrid(False)  # 隐藏网格线

        # 设置列宽
        self.table.setColumnWidth(0, 50)  # 复选框列
        self.table.setColumnWidth(1, 200)  # 文件名列
        self.table.setColumnWidth(2, 200)  # 进度条列
        self.table.setColumnWidth(3, 100)  # 开始按钮列
        self.table.setColumnWidth(4, 100)  # 导出下拉框列
        self.table.setColumnWidth(5, 100)  # 删除按钮列

        layout.addWidget(self.table)

        # 添加示例数据
        self.addRow("文本")

        self.setLayout(layout)

    def selectAll(self, state):
        for row in range(self.table.rowCount()):
            self.table.cellWidget(row, 0).setChecked(state == Qt.Checked)

    def addRow(self, filename):
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)

        # 复选框
        chk = QCheckBox()
        chk.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")
        self.table.setCellWidget(rowPosition, 0, chk)

        # 文件名
        self.table.setItem(rowPosition, 1, QTableWidgetItem(filename))

        # 进度条
        progressBar = ProgressBar()
        progressBar.setValue(0)
        progressBar.setTextVisible(False)
        self.table.setCellWidget(rowPosition, 2, progressBar)

        # 开始按钮
        startBtn = PushButton("开始")
        startBtn.setStyleSheet("color: blue;")
        self.table.setCellWidget(rowPosition, 3, startBtn)

        # 导出下拉框
        exportCombo = ComboBox()
        exportCombo.addItems(["导出srt", "导出txt"])
        exportCombo.setStyleSheet("QComboBox { border: 1px solid gray; border-radius: 3px; padding: 1px 18px 1px 3px; min-width: 6em; }")
        self.table.setCellWidget(rowPosition, 4, exportCombo)

        # 删除按钮
        deleteBtn = PushButton("删除")
        deleteBtn.setStyleSheet("color: blue;")
        deleteBtn.clicked.connect(lambda: self.deleteRow(rowPosition))
        self.table.setCellWidget(rowPosition, 5, deleteBtn)

    def deleteRow(self, row):
        self.table.removeRow(row)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('文件处理')
        self.setGeometry(100, 100, 800, 600)
        self.setCentralWidget(TableApp())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())