import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout,
                               QFileDialog, QAbstractItemView, QMessageBox, QHeaderView, QListWidget)
from PySide6.QtCore import Qt, Slot


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("File Selection Example")
        self.setGeometry(300, 100, 800, 600)


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # Create file selection button
        self.select_button = QPushButton("选择文件")
        self.select_button.clicked.connect(self.select_files)
        self.layout.addWidget(self.select_button)

        # Create file list table
        self.file_table = QTableWidget(0, 4)
        self.file_table.setHorizontalHeaderLabels(["文件名", "时长", "消耗算力", "操作"])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.layout.addWidget(self.file_table)

    @Slot()
    def select_files(self):
        file_dialog = QFileDialog()
        files, _ = file_dialog.getOpenFileNames(self, "选择文件")

        for file in files:
            self.add_file_to_table(file)

    def add_file_to_table(self, file):
        duration = self.get_video_duration(file)
        row_position = self.file_table.rowCount()
        self.file_table.insertRow(row_position)

        file_name_item = QTableWidgetItem(file)
        duration_item = QTableWidgetItem(duration)
        computation_item = QTableWidgetItem("N/A")  # Placeholder for computation cost
        delete_button = QPushButton("删除")
        delete_button.setStyleSheet("background-color: red; color: white;")

        self.file_table.setItem(row_position, 0, file_name_item)
        self.file_table.setItem(row_position, 1, duration_item)
        self.file_table.setItem(row_position, 2, computation_item)
        self.file_table.setCellWidget(row_position, 3, delete_button)

        delete_button.clicked.connect(lambda _, row=row_position: self.delete_file(row))

    def get_video_duration(self, file):
        # Use ffprobe to get video duration
        cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{file}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        duration_seconds = float(result.stdout.strip())
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    # def get_2(self):
    #     import subprocess
    #     import json
    #
    #     def get_video_duration_ffprobe(filename):
    #
    #         cmd = f"ffprobe -v error -show_format -print_format json {filename}"
    #
    #         try:
    #
    #             result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #
    #             result_json = json.loads(result.stdout)
    #
    #             duration = float(result_json['format']['duration'])
    #
    #             return duration
    #
    #
    #         except subprocess.CalledProcessError:
    #
    #             return "Error: ffprobe command fAIled."
    #
    #     video_duration_ffprobe = get_video_duration_ffprobe('your_video.mp4')
    #
    #     print(f"The duration of the video is: {video_duration_ffprobe} seconds.")

    @Slot()
    def delete_file(self, row):
        # Confirm delete action
        reply = QMessageBox.question(self, '确认', '你确定要删除这个文件吗?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.file_table.removeRow(row)
            # Update the delete buttons' connections
            self.update_delete_buttons()

    def update_delete_buttons(self):
        for row in range(self.file_table.rowCount()):
            delete_button = self.file_table.cellWidget(row, 3)
            delete_button.clicked.disconnect()
            delete_button.clicked.connect(lambda _, r=row: self.delete_file(r))


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
