from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import sys
import os

class MyDragDropButton(QPushButton):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.parent().handle_dropped_files(files)

class MyTableWindow(QTableWidget):
    files_added = Signal(list)

    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['文件名', '时长', '算力消耗', '操作'])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def select_files(self):
        file_dialog = QFileDialog()
        files, _ = file_dialog.getOpenFileNames(self, "选择文件")
        self.add_files_to_table(files)

    def add_files_to_table(self, files):
        for file_path in files:
            file_name = os.path.basename(file_path)
            self.add_row_to_table(file_name, '', '', '')
        self.files_added.emit(files)

    def add_row_to_table(self, file_name, duration, compute_power, operation):
        row_position = self.rowCount()
        self.insertRow(row_position)
        self.setItem(row_position, 0, QTableWidgetItem(file_name))
        self.setItem(row_position, 1, QTableWidgetItem(duration))
        self.setItem(row_position, 2, QTableWidgetItem(compute_power))
        self.setItem(row_position, 3, QTableWidgetItem(operation))


