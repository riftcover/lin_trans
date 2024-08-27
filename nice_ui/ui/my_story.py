import json
import os
import shutil
import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QMainWindow, QLabel, QFileDialog, QSizePolicy

from nice_ui.configure import config
from nice_ui.task.main_worker import work_queue
from nice_ui.util import tools
from nice_ui.util.tools import ObjFormat
from orm.queries import ToSrtOrm, ToTranslationOrm
from vendor.qfluentwidgets import (TableWidget, CheckBox, PushButton, InfoBar, InfoBarPosition, FluentIcon, CardWidget, SearchLineEdit)


class TableApp(CardWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()
        self.data_bridge = config.data_bridge
        self.data_bridge.update_table.connect(self.table_row_init)
        self.data_bridge.whisper_working.connect(self.table_row_working)
        self.data_bridge.whisper_finished.connect(self.table_row_finish)
        self.srt_orm = ToSrtOrm()
        self.trans_orm = ToTranslationOrm()
        self._init_table()

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
        self.selectAllBtn.stateChanged.connect(self._selectAll)

        # 添加批量导出按钮
        self.exportBtn = PushButton("批量导出")
        self.exportBtn.setFixedSize(QSize(110, 30))
        self.exportBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
        self.exportBtn.setIcon(FluentIcon.DOWN)
        self.exportBtn.clicked.connect(self._export_batch)
        # 初始状态隐藏
        self.exportBtn.setVisible(False)
        # selectAllBtn勾选时，exportBtn显示，否则隐藏
        self.selectAllBtn.stateChanged.connect(self.exportBtn.setVisible)

        # 添加批量删除按钮
        self.deleteBtn = PushButton("批量删除")
        self.deleteBtn.setFixedSize(QSize(110, 30))
        self.deleteBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
        self.deleteBtn.setIcon(FluentIcon.DELETE)
        self.deleteBtn.clicked.connect(self._delete_batch)
        # 初始状态隐藏
        self.deleteBtn.setVisible(False)
        self.selectAllBtn.stateChanged.connect(self.deleteBtn.setVisible)

        # self.addRowBtn = PushButton("添加文件")
        # self.addRowBtn.setFixedSize(QSize(110, 30))
        # self.addRowBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
        # self.addRowBtn.setIcon(FluentIcon.ADD)
        # self.addRowBtn.clicked.connect(self._addNewRow)

        self.searchInput = SearchLineEdit()
        self.searchInput.setPlaceholderText("搜索文件")
        # searchInput固定宽度
        self.searchInput.setFixedWidth(200)
        # 设置为右对齐
        self.searchInput.setAlignment(Qt.AlignRight)
        self.searchInput.textChanged.connect(self.searchFiles)

        topLayout.addWidget(self.selectAllBtn)
        topLayout.addWidget(self.exportBtn)
        topLayout.addWidget(self.deleteBtn)
        # topLayout.addWidget(self.addRowBtn)
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
        self.table.setColumnWidth(6, 200)

        # self.table.setColumnHidden(3, True)
        self.table.setColumnHidden(6, True)
        layout.addWidget(self.table)

    def _selectAll(self):
        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, 0)
            if chk.isEnabled():
                chk.setChecked(self.selectAllBtn.isChecked())

    def _init_table(self):
        # 初始化表格,从数据库中获取数据
        all_srt = self.srt_orm.query_data_format_unid_path()
        all_trans = self.trans_orm.query_data_format_unid_path()
        for srt in all_srt:
            filename = os.path.basename(srt.path)
            # 去掉文件扩展名
            filename_without_extension = os.path.splitext(filename)[0]
            config.logger.debug(f"文件:{filename_without_extension} 状态:{srt.job_status}")

            if srt.job_status in (0, 1):
                if srt.job_status == 1:
                    new_status = 0

                    # 将上次排队中的任务job_status == 1设置为0
                    self.srt_orm.update_table_unid(srt.unid, job_status=new_status)
                # 重新初始化表格,状态显示为未开始
                # config.logger.info(f"文件:{filename_without_extension} 状态更新为未开始")

                obj_format = {'raw_noextname': filename_without_extension, 'unid': srt.unid, }
                self.table_row_init(obj_format, 0)
            elif srt.job_status == 2:
                self.addRow_init_all(filename_without_extension, srt.unid)

        for trans in all_trans:
            filename = os.path.basename(trans.path)
            # 去掉文件扩展名
            filename_without_extension = os.path.splitext(filename)[0]
            config.logger.debug(f"文件:{filename_without_extension} 状态:{trans.job_status}")

            if trans.job_status in (0, 1):
                if trans.job_status == 1:
                    new_status = 0

                    # 将上次排队中的任务job_status == 1设置为0
                    self.trans_orm.update_table_unid(trans.unid, job_status=new_status)
                # 重新初始化表格,状态显示为未开始
                # config.logger.info(f"文件:{filename_without_extension} 状态更新为未开始")

                obj_format = {'raw_noextname': filename_without_extension, 'unid': trans.unid, }
                self.table_row_init(obj_format, 0)
            elif trans.job_status == 2:
                self.addRow_init_all(filename_without_extension, trans.unid)


    def _addNewRow(self):
        self.addRow_init_all("新文件", "tt1")
        InfoBar.success(title='成功', content="新文件已添加", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                        parent=self)

    def table_row_init(self, obj_format: ObjFormat, job_status: int = 1):
        # 添加新文件时，初始化表格包含的元素
        if job_status == 1:
            config.logger.debug(f"添加新文件:{obj_format['raw_noextname']} 到我的创作列表")
        filename = obj_format['raw_noextname']
        unid = obj_format['unid']
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # 复选框
        chk = CheckBox()
        chk.stateChanged.connect(self._update_buttons_visibility)  # 连接状态改变信号到更新按钮可见性的方法
        self.table.setCellWidget(row_position, 0, chk)

        # 文件名
        file_name = QLabel()
        file_name.setText(filename)
        file_name.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 1, file_name)

        # 处理进度
        file_status = QLabel()
        if job_status == 1:
            file_status.setText("排队中")
        elif job_status == 0:
            config.logger.debug(f"文件:{filename} 状态更新为未开始")
            chk.setEnabled(False)  # 设置置灰
            file_status.setText("处理失败")
            # file_status.setStyleSheet("color: #dd3838;")
            file_status.setStyleSheet("color: #FF6C64;")
            # todo 未开始也需要添加开始按钮,目前没写完
            startBtn = PushButton("开始")
            startBtn.setFixedSize(QSize(80, 30))
            startBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
            startBtn.setIcon(FluentIcon.PLAY)
            startBtn.clicked.connect(lambda: self._start_row(row_position))
            self.table.setCellWidget(row_position, 3, startBtn)
        file_status.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 2, file_status)

        # 隐藏列数据
        file_unid = QLabel()
        file_unid.setText(unid)
        self.table.setCellWidget(row_position, 6, file_unid)

    def table_row_working(self, unid, progress: float):
        """
        更新指定行的进度条
        :param unid: 第7列（索引为6）的标识符
        :param progress: 进度值 (0-100)
        """

        if unid in self.row_cache:
            row = self.row_cache[unid]
            config.logger.debug(f"找到文件:{unid}的行索引:{row}")
        else:
            config.logger.info(f"未找到文件:{unid}的行索引,尝试从缓存中查找")
            row = self.find_row_by_identifier(unid)
            if row is not None:
                self.row_cache[unid] = row
            else:
                return  # 如果找不到对应的行，直接返回

        progress_bar = self.table.cellWidget(row, 2)
        # if isinstance(progress_bar, QProgressBar):
        config.logger.info(f"更新文件:{unid}的进度条:{progress}")
        progress_bar.setText(f"处理中 {progress}")  # else:  #     config.logger.error(f"文件:{unid}的进度条不是进度条,无法更新")

    def find_row_by_identifier(self, unid):
        """
        根据标识符查找对应的行
        :param unid: 第7列（索引为6）的标识符
        :return: 找到的行索引，如果没找到返回None
        """

        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, 6)
            if item and item.text() == unid:
                return row
        config.logger.error(f"未找到文件:{unid}的行索引,也未缓存,直接返回")
        return None

    def table_row_finish(self, unid):
        """
        更新指定行的数据
        :param unid: 第7列（索引为6）的标识符
        :param column: 要更新的列索引
        :param data: 要设置的新数据
        """
        config.logger.info(f"文件处理完成:{unid},更新表单")
        if unid in self.row_cache:
            row = self.row_cache[unid]
            item = self.table.cellWidget(row, 6)
            progress_bar = self.table.cellWidget(row, 2)
            # 进度条设置为100
            progress_bar.setText("已完成")
            # 数据库状态更新为已完成
            self.srt_orm.update_table_unid(unid, job_status=2)

            if unid in item.text():
                # 开始按钮
                # todo 目前是任务完成显示按钮,需要修改其他中断的要显示
                startBtn = PushButton("开始")
                startBtn.setFixedSize(QSize(80, 30))
                startBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
                startBtn.setIcon(FluentIcon.PLAY)
                startBtn.clicked.connect(lambda: self._start_row(row))
                self.table.setCellWidget(row, 3, startBtn)

                # 导出下拉框
                # exportCombo = ComboBox()
                # exportCombo.addItems(["导出srt", "导出txt"])
                # self.table.setCellWidget(row, 4, exportCombo)
                exportBtn = PushButton("导出")
                exportBtn.setFixedSize(QSize(80, 30))
                exportBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
                exportBtn.setIcon(FluentIcon.DOWN)
                # config.logger.info(exportBtn.size())
                # config.logger.info(f"Row height of row {row_position}: {ui_table.rowHeight(row_position)}")

                exportBtn.clicked.connect(lambda: self._export_row(row))
                self.table.setCellWidget(row, 4, exportBtn)

                # 删除按钮
                deleteBtn = PushButton("删除")
                deleteBtn.setFixedSize(QSize(80, 30))
                deleteBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
                deleteBtn.setIcon(FluentIcon.DELETE)
                deleteBtn.clicked.connect(self._delete_row(deleteBtn))
                self.table.setCellWidget(row, 5, deleteBtn)

            else:
                config.logger.error(f"文件:{unid}的行索引,缓存中未找到,缓存未更新")

    def addRow_init_all(self, filename, unid):
        config.logger.info(f"添加已完成:{filename} 到我的创作列表")
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        # 复选框
        chk = CheckBox()
        chk.stateChanged.connect(self._update_buttons_visibility)  # 连接状态改变信号到更新按钮可见性的方法
        self.table.setCellWidget(row_position, 0, chk)

        # 文件名
        file_name = QLabel()
        file_name.setText(filename)
        file_name.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 1, file_name)

        # 进度条
        file_name = QLabel()
        file_name.setText("已完成")
        file_name.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 2, file_name)

        # 开始按钮
        start_btn = PushButton("开始")
        start_btn.setFixedSize(QSize(80, 30))
        start_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
        start_btn.setIcon(FluentIcon.PLAY)
        self.table.setCellWidget(row_position, 3, start_btn)

        # 导出下拉框

        # exportCombo = ComboBox()
        # exportCombo.addItems(["导出srt", "导出txt"])
        # self.table.setCellWidget(row_position, 4, exportCombo)
        export_btn = PushButton("导出")
        export_btn.setFixedSize(QSize(80, 30))
        export_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
        export_btn.setIcon(FluentIcon.DOWN)
        export_btn.clicked.connect(lambda: self._export_row(row_position))
        self.table.setCellWidget(row_position, 4, export_btn)

        # 删除按钮
        delete_btn = PushButton("删除")
        delete_btn.setFixedSize(QSize(80, 30))
        delete_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 设置大小策略为Fixed
        delete_btn.setIcon(FluentIcon.DELETE)
        delete_btn.clicked.connect(self._delete_row(delete_btn))
        self.table.setCellWidget(row_position, 5, delete_btn)

        # 隐藏列数据:unid
        file_unid = QLabel()
        file_unid.setText(unid)
        file_unid.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 6, file_unid)

    def _start_row(self, row):
        # todo 从数据库中获取数据，传到work_queue中的数据格式需要调整
        # 1.和consume_mp4_queue接受的一样
        # 2.检查一下config.params的值是否和旧任务时一样,不一样也需要存到库中,再加载出来
        unid_item = self.table.cellWidget(row, 6)
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
            unid_item = self.table.cellWidget(button_row, 6)

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
        job_path,file_path =None,None
        options = QFileDialog.Options()
        file_dir = QFileDialog.getExistingDirectory(self, "选择文件夹", "", options=options)

        for row in range(self.table.rowCount()):
            print(f"{row}:{self.table.cellWidget(row, 4)}")
            if self.table.cellWidget(row, 4):
                unid_item = self.table.cellWidget(row, 6)

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
            unid_item = self.table.cellWidget(row, 6)
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('我的创作列表')
        self.setGeometry(100, 100, 900, 600)
        self.setCentralWidget(TableApp("我的创作列表"))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
