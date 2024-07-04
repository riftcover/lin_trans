import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QFrame, QMainWindow
from PySide6.QtCore import Qt, QMargins
from qfluentwidgets import (TableWidget, setTheme, Theme, CheckBox, ProgressBar, ComboBox,
                            PushButton, LineEdit, InfoBar, InfoBarPosition, FluentIcon,
                            CardWidget, IconWidget, TransparentToolButton, FlowLayout)

class TableApp(CardWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()

    def setupUi(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 顶部布局
        topCard = CardWidget()
        topLayout = QHBoxLayout(topCard)
        topLayout.setSpacing(10)
        topLayout.setContentsMargins(10, 10, 10, 10)

        self.selectAllBtn = CheckBox("全选")
        self.selectAllBtn.stateChanged.connect(self.selectAll)

        self.addRowBtn = PushButton("添加文件")
        self.addRowBtn.setIcon(FluentIcon.ADD)
        self.addRowBtn.clicked.connect(self.addNewRow)

        self.searchInput = LineEdit()
        self.searchInput.setPlaceholderText("搜索文件")
        self.searchInput.textChanged.connect(self.searchFiles)

        topLayout.addWidget(self.selectAllBtn)
        topLayout.addWidget(self.addRowBtn)
        topLayout.addStretch()
        topLayout.addWidget(self.searchInput)

        layout.addWidget(topCard)

        # 创建表格
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # 设置列宽
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)

        layout.addWidget(self.table)

    def selectAll(self, state):
        for row in range(self.table.rowCount()):
            self.table.cellWidget(row, 0).setChecked(state == Qt.Checked)

    def addNewRow(self):
        self.addRow("新文件")
        InfoBar.success(
            title='成功',
            content="新文件已添加",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def addRow(self, filename):
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)

        # 复选框
        chk = CheckBox()
        self.table.setCellWidget(rowPosition, 0, chk)

        # 文件名
        fileNameBtn = TransparentToolButton(filename, self)
        fileNameBtn.setIcon(FluentIcon.DOCUMENT)
        self.table.setCellWidget(rowPosition, 1, fileNameBtn)

        # 进度条
        progressBar = ProgressBar()
        progressBar.setValue(0)
        progressBar.setTextVisible(False)
        self.table.setCellWidget(rowPosition, 2, progressBar)

        # 开始按钮
        startBtn = PushButton("开始")
        startBtn.setIcon(FluentIcon.PLAY)
        self.table.setCellWidget(rowPosition, 3, startBtn)

        # 导出下拉框
        exportCombo = ComboBox()
        exportCombo.addItems(["导出srt", "导出txt"])
        self.table.setCellWidget(rowPosition, 4, exportCombo)

        # 删除按钮
        deleteBtn = PushButton("删除")
        deleteBtn.setIcon(FluentIcon.DELETE)
        deleteBtn.clicked.connect(lambda: self.deleteRow(rowPosition))
        self.table.setCellWidget(rowPosition, 5, deleteBtn)

    def deleteRow(self, row):
        self.table.removeRow(row)
        InfoBar.success(
            title='成功',
            content="文件已删除",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def searchFiles(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 1)
            if text.lower() in item.text().lower():
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('文件处理')
        self.setGeometry(100, 100, 900, 600)
        self.setCentralWidget(TableApp("文件处理"))
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())