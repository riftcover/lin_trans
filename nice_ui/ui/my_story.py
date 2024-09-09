import json
import os
import shutil
import sys
from enum import Enum, auto

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QMainWindow, QLabel, QFileDialog, QSizePolicy, QWidget

from nice_ui.configure import config
from nice_ui.task.main_worker import work_queue
from nice_ui.util import tools
from nice_ui.util.tools import ObjFormat
from orm.queries import ToSrtOrm, ToTranslationOrm
from vendor.qfluentwidgets import (TableWidget, CheckBox, PushButton, InfoBar, InfoBarPosition, FluentIcon, CardWidget, SearchLineEdit, ToolButton)

button_size = QSize(32, 30)


class ButtonType(Enum):
    START = auto()
    EXPORT = auto()
    EDIT = auto()
    DELETE = auto()


class TableApp(CardWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()
        self.data_bridge = config.data_bridge
        self._connect_signals()
        self.srt_orm = ToSrtOrm()
        self.trans_orm = ToTranslationOrm()
        self.row_cache = {}
        self._init_table()

    def _connect_signals(self):
        self.data_bridge.update_table.connect(self.table_row_init)
        self.data_bridge.whisper_working.connect(self.table_row_working)
        self.data_bridge.whisper_finished.connect(self.table_row_finish)
        self.selectAllBtn.stateChanged.connect(self._selectAll)
        self.selectAllBtn.stateChanged.connect(self.exportBtn.setVisible)
        self.selectAllBtn.stateChanged.connect(self.deleteBtn.setVisible)

    def setupUi(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        topCard = CardWidget()
        topLayout = QHBoxLayout(topCard)
        topLayout.setSpacing(10)
        topLayout.setContentsMargins(10, 10, 10, 10)

        self.selectAllBtn = CheckBox("全选")
        self.exportBtn = self._create_button("批量导出", FluentIcon.DOWN, self._export_batch)
        self.deleteBtn = self._create_button("批量删除", FluentIcon.DELETE, self._delete_batch)
        self.searchInput = self._create_search_input()

        topLayout.addWidget(self.selectAllBtn)
        topLayout.addWidget(self.exportBtn)
        topLayout.addWidget(self.deleteBtn)
        topLayout.addStretch()
        topLayout.addWidget(self.searchInput)

        layout.addWidget(topCard)
        self._setup_table(layout)

    @staticmethod
    def _create_button(text, icon, callback):
        button = PushButton(text)
        button.setFixedSize(QSize(110, 30))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setIcon(icon)
        button.clicked.connect(callback)
        button.setVisible(False)
        return button

    def _create_search_input(self):
        search_input = SearchLineEdit()
        search_input.setPlaceholderText("搜索文件")
        search_input.setFixedWidth(200)
        search_input.setAlignment(Qt.AlignRight)
        search_input.textChanged.connect(self.searchFiles)
        return search_input

    def _setup_table(self, layout):
        self.table = TableWidget()
        self.table.setColumnCount(5)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self._set_column_widths()
        # self.table.setColumnHidden(8, True)
        layout.addWidget(self.table)

    def _set_column_widths(self):
        widths = [50, 200, 150, 150, 200]  # 调整列宽
        for i, width in enumerate(widths):
            self.table.setColumnWidth(i, width)

    def _selectAll(self):
        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, 0)
            if chk.isEnabled():
                chk.setChecked(self.selectAllBtn.isChecked())

    def _init_table(self):
        self._load_data(self.srt_orm)
        self._load_data(self.trans_orm)

    def _load_data(self, orm):
        all_data = orm.query_data_format_unid_path()
        for item in all_data:
            filename = os.path.basename(item.path)
            filename_without_extension = os.path.splitext(filename)[0]
            config.logger.debug(f"文件:{filename_without_extension} 状态:{item.job_status}")
            self._process_item(item, filename_without_extension)

    @staticmethod
    def _create_action_button(icon, tooltip, callback, size=button_size):
        button = ToolButton(icon)
        button.setFixedSize(size)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        # 设置工具提示立即显示
        button.setToolTipDuration(0)
        button.clicked.connect(callback)
        return button

    def _set_row_buttons(self, row, button_types):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(2)  # 设置按钮之间的间距
        button_layout.setContentsMargins(0, 0, 0, 0)

        # 添加一个伸缩项,将按钮推到右侧
        button_layout.addStretch()

        for button_type in button_types:

            if button_type == ButtonType.EXPORT:
                button = self._create_action_button(FluentIcon.DOWN, "导出字幕", lambda:self._export_row(row))
            elif button_type == ButtonType.EDIT:
                button = self._create_action_button(FluentIcon.EDIT, "编辑字幕", lambda:self._edit_row(row))
            elif button_type == ButtonType.START:
                button = self._create_action_button(FluentIcon.PLAY, "开始任务", lambda:self._start_row(row))
            elif button_type == ButtonType.DELETE:
                button = self._create_action_button(FluentIcon.DELETE, "删除字幕", self._delete_row(row))
            button_layout.addWidget(button)

        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        self.table.setCellWidget(row, 3, button_widget)

    def _process_item(self, item, filename_without_extension):
        if item.job_status in (0, 1):
            if item.job_status == 1:
                self._update_job_status(item)
            obj_format = {'raw_noextname':filename_without_extension, 'unid':item.unid}
            self.table_row_init(obj_format, 0)
        elif item.job_status == 2:
            self.addRow_init_all(filename_without_extension, item.unid)

    def _update_job_status(self, item):
        new_status = 0
        self.srt_orm.update_table_unid(item.unid, job_status=new_status)

    def _addNewRow(self):
        self.addRow_init_all("新文件", "tt1")
        InfoBar.success(title='成功', content="新文件已添加", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                        parent=self)

    def table_row_init(self, obj_format: ObjFormat, job_status: int = 1):
        if job_status == 1:
            config.logger.debug(f"添加新文件:{obj_format['raw_noextname']} 到我的创作列表")
        filename = obj_format['raw_noextname']
        unid = obj_format['unid']
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        chk = CheckBox()
        chk.stateChanged.connect(self._update_buttons_visibility)
        self.table.setCellWidget(row_position, 0, chk)

        file_name = QLabel()
        file_name.setText(filename)
        file_name.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 1, file_name)

        file_status = QLabel()
        if job_status == 1:
            file_status.setText("排队中")
        elif job_status == 0:
            config.logger.debug(f"文件:{filename} 状态更新为未开始")
            chk.setEnabled(False)
            file_status.setText("处理失败")
            file_status.setStyleSheet("color: #FF6C64;")
            self._set_row_buttons(row_position, [ButtonType.START, ButtonType.DELETE])
        file_status.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 2, file_status)

        file_unid = QLabel()
        file_unid.setText(unid)
        self.table.setCellWidget(row_position, 7, file_unid)

    def table_row_working(self, unid, progress: float):
        if unid in self.row_cache:
            row = self.row_cache[unid]
            config.logger.debug(f"找到文件:{unid}的行索引:{row}")
        else:
            config.logger.info(f"未找到文件:{unid}的行索引,尝试从缓存中查找")
            row = self.find_row_by_identifier(unid)
            if row is not None:
                self.row_cache[unid] = row
            else:
                return

        progress_bar = self.table.cellWidget(row, 2)
        config.logger.info(f"更新文件:{unid}的进度条:{progress}")
        progress_bar.setText(f"处理中 {progress}")

    def find_row_by_identifier(self, unid):
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 6)
            if item and item.text() == unid:
                return row
        config.logger.error(f"未找到文件:{unid}的行索引,也未缓存,直接返回")
        return None

    def table_row_finish(self, unid):
        config.logger.info(f"文件处理完成:{unid},更新表单")

        if unid in self.row_cache:
            row = self.row_cache[unid]
            item = self.table.cellWidget(row, 6)
            progress_bar = self.table.cellWidget(row, 2)
            progress_bar.setText("已完成")
            self.srt_orm.update_table_unid(unid, job_status=2)

            if unid in item.text():
                self._set_row_buttons(row, [ButtonType.EDIT, ButtonType.EXPORT, ButtonType.START, ButtonType.DELETE])
            else:
                config.logger.error(f"文件:{unid}的行索引,缓存中未找到,缓存未更新")

    def addRow_init_all(self, filename, unid):
        config.logger.info(f"添加已完成:{filename} 到我的创作列表")
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        chk = CheckBox()
        chk.stateChanged.connect(self._update_buttons_visibility)
        self.table.setCellWidget(row_position, 0, chk)

        file_name = QLabel()
        file_name.setText(filename)
        file_name.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 1, file_name)

        file_name = QLabel()
        file_name.setText("已完成")
        file_name.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 2, file_name)

        self._set_row_buttons(row_position, [ButtonType.EXPORT, ButtonType.EDIT, ButtonType.START, ButtonType.DELETE])

        # 隐藏列数据:unid
        file_unid = QLabel()
        file_unid.setText(unid)
        file_unid.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 7, file_unid)

    def _start_row(self, row):
        # todo 从数据库中获取数据，传到work_queue中的数据格式需要调整
        # 1.和consume_mp4_queue接受的一样
        # 2.检查一下config.params的值是否和旧任务时一样,不一样也需要存到库中,再加载出来
        unid_item = self.table.cellWidget(row, 7)
        job_path = self.srt_orm.query_data_by_unid(unid_item).path
        if not os.path.isfile(job_path):
            config.logger.error(f"文件:{job_path}不存在,无法开始处理")
            raise FileNotFoundError(f"The file {job_path} does not exist.")
        obj_format = tools.format_video(job_path.replace('\\', '/'), config.params['target_dir'])
        work_queue.lin_queue_put(job_path)

    def _delete_row(self, button):
        #todo： 删除的行好像是错的，删除的是下一行。style中SubtitleTable中_delete_row,update_row_numbers貌似是对的

        def delete_row_callback():
            button_row = self.table.indexAt(button.pos()).row()
            config.logger.info(f"删除文件所在行:{button_row} ")
            unid_item = self.table.cellWidget(button_row, 7)

            # 删除这三步是有先后顺序的,先删除文件,再删除数据库中的数据,再删除表格行,最后清除缓存索引
            # 删除result中对应文件
            text = unid_item.text()
            if text:
                job_obj = json.loads(self.srt_orm.query_data_by_unid(text).obj)
                result_dir = job_obj["output"]
                config.logger.info(f"删除目录:{text} 成功")
                try:
                    shutil.rmtree(result_dir)
                    config.logger.info(f"删除目录:{result_dir} 成功")
                except Exception as e:
                    config.logger.error(f"删除目录:{result_dir} 失败:{e}")
            # 在数据库中删除对应数据
            self.srt_orm.delete_table_unid(text)
            # 删除表格行
            self.table.removeRow(button_row)
            # 清除缓存索引
            self.row_cache.clear()
            InfoBar.success(title='成功', content="文件已删除", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                            parent=self)

        return delete_row_callback

    def _delete_batch(self):
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 0).isChecked():
                self._delete_row(row)

    def searchFiles(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 1)
            config.logger.info(f"item:{item.text()}")
            if text.lower() in item.text().lower():
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def _export_batch(self):
        # 打开系统文件夹选择框
        job_path, file_path = None, None
        options = QFileDialog.Options()
        file_dir = QFileDialog.getExistingDirectory(self, "选择文件夹", "", options=options)

        for row in range(self.table.rowCount()):
            print(f"{row}:{self.table.cellWidget(row, 4)}")
            if self.table.cellWidget(row, 4):
                unid_item = self.table.cellWidget(row, 7)

                job_obj = json.loads(self.srt_orm.query_data_by_unid(unid_item.text()).obj)
                config.logger.info(f"job_obj:{job_obj}")
                job_path = f'{job_obj["output"]}/{job_obj["raw_noextname"]}.srt'
                file_path = f'{file_dir}/{job_obj["raw_noextname"]}.srt'
                config.logger.info(f"导出文件:{job_path} 到 {file_path}")
            try:
                shutil.copy(job_path, file_path)
            except Exception as e:
                config.logger.error(f"导出文件失败:{e}")
                InfoBar.error(title='错误', content="导出文件失败", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                              parent=self)
                return

        InfoBar.success(title='成功', content="文件已导出", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                        parent=self)

    def _export_row(self, row):
        options = QFileDialog.Options()
        item = self.table.cellWidget(row, 1)
        config.logger.info(f"文件所在行:{row} 文件名:{item.text()}")
        export_name = f"{item.text()}.srt"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出文件", export_name, options=options)
        if file_path:
            unid_item = self.table.cellWidget(row, 7)
            config.logger.info(f"unid_item:{unid_item}")
            config.logger.info(f"导出文件:{unid_item.text()} 成功")
            job_obj = json.loads(self.srt_orm.query_data_by_unid(unid_item.text()).obj)
            config.logger.info(f"job_obj:{job_obj}")
            job_path = f'{job_obj["output"]}/{job_obj["raw_noextname"]}.srt'
            config.logger.info(f"导出文件:{job_path}到{file_path}")
            shutil.copy(job_path, file_path)
            InfoBar.success(title='成功', content="文件已导出", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                            parent=self)

    def _update_buttons_visibility(self):
        # 检查所有行的复选框状态，如果有任何一个被勾选，则显示按钮
        any_checked = any(self.table.cellWidget(row, 0).isChecked() for row in range(self.table.rowCount()))
        self.deleteBtn.setVisible(any_checked)
        self.exportBtn.setVisible(any_checked)

    def _edit_row(self, row):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('我的创作列表')
        self.setGeometry(100, 100, 900, 600)
        self.setCentralWidget(TableApp("我的创作列表"))


if __name__ == '__main__':
    print("我的创作列表")
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
