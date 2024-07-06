import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QLabel
from PySide6.QtCore import Qt, QMargins
from qfluentwidgets import (TableWidget, setTheme, Theme, CheckBox, ProgressBar, ComboBox,
                            PushButton, LineEdit, InfoBar, InfoBarPosition, FluentIcon,
                            CardWidget, IconWidget, TransparentToolButton, FlowLayout, ProgressBar, SearchLineEdit)


from videotrans.configure import config
class TableApp(CardWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()
        self.data_bridge = config.data_bridge
        self.data_bridge.update_table.connect(self.table_row_init)
        self.data_bridge.whisper_working.connect(self.table_row_working)
        self.data_bridge.whisper_finished.connect(self.table_row_finish)

        # 用于缓存行索引的字典
        self.row_cache = {}

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

        self.searchInput = SearchLineEdit()
        self.searchInput.setPlaceholderText("搜索文件")
        self.searchInput.textChanged.connect(self.searchFiles)


        topLayout.addWidget(self.selectAllBtn)
        topLayout.addWidget(self.addRowBtn)
        topLayout.addStretch()
        topLayout.addWidget(self.searchInput)

        layout.addWidget(topCard)

        # 创建表格
        self.table = TableWidget()
        self.table.setColumnCount(7)
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
        self.table.setColumnWidth(6, 100)
        # 为啥没有呢
        # 设置表头
        self.table.setColumnHidden(6, True)
        layout.addWidget(self.table)

    def selectAll(self, state):
        for row in range(self.table.rowCount()):
            self.table.cellWidget(row, 0).setChecked(state == Qt.Checked)

    def addNewRow(self):
        self.addRow_init_all("新文件","tt1")
        InfoBar.success(
            title='成功',
            content="新文件已添加",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def table_row_init(self, obj_format):
        config.logger.info(f"添加新文件:{obj_format['raw_noextname']} 到我的创作列表")
        filename = obj_format['raw_noextname']
        unid = obj_format['unid']
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)

        # 复选框
        chk = CheckBox()
        self.table.setCellWidget(rowPosition, 0, chk)

        # 文件名
        fileName = QLabel()
        fileName.setText(filename)
        fileName.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(rowPosition, 1, fileName)


        # 进度条
        progressBar = ProgressBar()
        progressBar.setRange(0, 100)
        progressBar.setValue(0)
        progressBar.setTextVisible(False)
        self.table.setCellWidget(rowPosition, 2, progressBar)

        # 隐藏列数据
        file_unid = QLabel()
        file_unid.setText(unid)
        self.table.setCellWidget(rowPosition, 6, file_unid)

    def table_row_working(self, unid, progress):
        """
        更新指定行的进度条
        :param unid: 第7列（索引为6）的标识符
        :param progress: 进度值 (0-100)
        """

        if unid in self.row_cache:
            row = self.row_cache[unid]
        else:
            row = self.find_row_by_identifier(unid)
            if row is not None:
                self.row_cache[unid] = row
            else:
                return  # 如果找不到对应的行，直接返回
        # 根据第7列中名称,更新该行数据
        progress_bar = self.table.cellWidget(row, 2)
        if isinstance(progress_bar, ProgressBar):
            progress_bar.setValue(progress)

    def find_row_by_identifier(self, identifier):
        """
        根据标识符查找对应的行
        :param identifier: 第7列（索引为6）的标识符
        :return: 找到的行索引，如果没找到返回None
        """
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 6)
            if item and item.text() == identifier:
                return row
        return None

    def table_row_finish(self, unid):
        """
        更新指定行的数据
        :param unid: 第7列（索引为6）的标识符
        :param column: 要更新的列索引
        :param data: 要设置的新数据
        """
        config.logger.info(f"文件处理完成:{unid},开始更新表单")
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 6)
            if unid in item.text():
                # 开始按钮
                startBtn = PushButton("开始")
                startBtn.setIcon(FluentIcon.PLAY)
                self.table.setCellWidget(row, 3, startBtn)

                # 导出下拉框
                exportCombo = ComboBox()
                exportCombo.addItems(["导出srt", "导出txt"])
                self.table.setCellWidget(row, 4, exportCombo)

                # 删除按钮
                deleteBtn = PushButton("删除")
                deleteBtn.setIcon(FluentIcon.DELETE)
                deleteBtn.clicked.connect(lambda: self.deleteRow(row))
                self.table.setCellWidget(row, 5, deleteBtn)

    def addRow_init_all(self, filename,unid):
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)
        # 复选框
        chk = CheckBox()
        self.table.setCellWidget(rowPosition, 0, chk)

        # 文件名
        fileName = QLabel()
        fileName.setText(filename)
        fileName.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(rowPosition, 1, fileName)


        # 进度条
        progressBar = ProgressBar()
        progressBar.setRange(0, 100)
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

        # 隐藏列数据
        file_unid = QLabel()
        file_unid.setText(unid)
        file_unid.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(rowPosition, 6, file_unid)


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