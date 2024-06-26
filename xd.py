import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel


class FileSelector(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Selector")
        self.setGeometry(100, 100, 400, 200)

        self.button = QPushButton("Select Files", self)
        self.button.clicked.connect(self.select_files)
        self.button.setGeometry(150, 50, 100, 50)

        self.label = QLabel("No files selected", self)
        self.label.setGeometry(50, 120, 300, 20)

        self.button.setAcceptDrops(True)
        self.button.dragEnterEvent = self.drag_enter_event
        self.button.dropEvent = self.drop_event

        self.file_paths = []

    def select_files(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("*.mp4 *.avi *.mov *.mpg *.mkv")
        file_paths, _ = file_dialog.getOpenFileNames(self, "Select files")
        self.file_paths = file_paths
        self.label.setText("\n".join(self.file_paths))

    def drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drop_event(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.file_paths.append(file_path)
        self.label.setText("\n".join(self.file_paths))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSelector()
    window.show()
    app.exec()
