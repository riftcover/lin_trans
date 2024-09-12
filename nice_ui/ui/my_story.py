import json
import os
import shutil
import sys
from enum import Enum, auto, IntEnum

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QMainWindow, QLabel, QFileDialog, QSizePolicy, QWidget, QTableWidgetItem
from pydantic import BaseModel, Field

from nice_ui.configure import config
from nice_ui.task import WORK_TYPE
from nice_ui.task.main_worker import work_queue
from nice_ui.ui.srt_edit import SubtitleEditPage
from nice_ui.util import tools
from orm.queries import ToSrtOrm, ToTranslationOrm
from vendor.qfluentwidgets import (TableWidget, CheckBox, PushButton, InfoBar, InfoBarPosition, FluentIcon, CardWidget, SearchLineEdit, ToolButton,
                                   ToolTipPosition, ToolTipFilter)

button_size = QSize(32, 30)


class ButtonType(Enum):
    START = auto()
    EXPORT = auto()
    EDIT = auto()
    DELETE = auto()


class TableWidgetColumn(IntEnum):
    CHECKBOX = 0
    FILENAME = 1
    JOB_STATUS = 2
    BUTTON_WIDGET = 3
    UNID = 4
    JOB_OBJ = 5


class SrtEditDict(BaseModel):
    """
    定义数据格式，在column：5中传递的，用来在删除，编辑使用编辑器读取信息，使用SrtEditDictRole 角色存储信息
    """
    unid: str = Field(default="", description="文件指纹")
    media_path: str = Field(default="", description="媒体文件路径")
    srt_path: str = Field(default="", description="SRT文件路径")
    job_type: WORK_TYPE = Field(default="", description="任务类型")
    raw_noextname: str = Field(default="", description="无扩展名的原始文件名")


# 定义一个自定义角色用于存储 SrtEditDict 对象
SrtEditDictRole = Qt.UserRole + 1


class TableApp(CardWidget):
    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setObjectName(text.replace(' ', '-'))
        self.setupUi()
        self.data_bridge = config.data_bridge
        self._connect_signals()
        self.srt_orm = ToSrtOrm()
        self.trans_orm = ToTranslationOrm()
        self.row_cache = {}
        self._init_table()

    def _connect_signals(self):
        """
        连接信号槽
        """
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

        top_card = CardWidget()
        top_layout = QHBoxLayout(top_card)
        top_layout.setSpacing(10)
        top_layout.setContentsMargins(10, 10, 10, 10)

        self.selectAllBtn = CheckBox("全选")
        self.exportBtn = self._create_button("批量导出", FluentIcon.DOWN, self._export_batch)
        self.deleteBtn = self._create_button("批量删除", FluentIcon.DELETE, self._delete_batch)
        self.searchInput = self._create_search_input()

        top_layout.addWidget(self.selectAllBtn)
        top_layout.addWidget(self.exportBtn)
        top_layout.addWidget(self.deleteBtn)
        top_layout.addStretch()
        top_layout.addWidget(self.searchInput)

        layout.addWidget(top_card)
        self._setup_table(layout)

    @staticmethod
    def _create_button(text, icon, callback):
        """
        生成顶部空间中的按钮
        """
        button = PushButton(text)
        button.setFixedSize(QSize(110, 30))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setIcon(icon)
        button.clicked.connect(callback)
        button.setVisible(False)
        return button

    def _create_search_input(self):
        """

        Returns:生成顶部空间中的搜索框

        """
        search_input = SearchLineEdit()
        search_input.setPlaceholderText("搜索文件")
        search_input.setFixedWidth(200)
        search_input.setAlignment(Qt.AlignRight)
        search_input.textChanged.connect(self.searchFiles)
        return search_input

    def _setup_table(self, layout: QVBoxLayout):
        """
        Returns:设置表格
        """
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self._set_column_widths()
        self.table.setColumnHidden(4, True)
        self.table.setColumnHidden(5, True)
        layout.addWidget(self.table)

    def _set_column_widths(self):
        widths = [50, 200, 150, 150, 200]  # 调整列宽
        for i, width in enumerate(widths):
            self.table.setColumnWidth(i, width)

    def _selectAll(self):
        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)
            if chk.isEnabled():
                chk.setChecked(self.selectAllBtn.isChecked())

    def _init_table(self):
        # 初始化列表数据：srt文件任务和翻译字幕任务
        self._load_data(self.srt_orm, 0)
        self._load_data(self.trans_orm, 1)

    def _choose_sql_orm(self, row: int):
        item = self.table.item(row, 5)
        # work_obj 取值是_load_data中srt_edit_dict
        work_obj = item.data(SrtEditDictRole)

        work_type = work_obj.job_type
        if work_type == 'asr':
            return self.srt_orm
        elif work_type == 'trans':
            return self.trans_orm
        else:
            config.logger.error(f'任务类型:{work_type}不存在')

    def _load_data(self, orm, st: int):
        """
        加载数据到表格
        Args:
            orm: 表名

        Returns:
            item: 数据库查询返回的项目对象
            srt_edit_dict: 字幕编辑器的字典
            filename_without_extension: 无扩展的文件名
        """
        srt_edit_dict = SrtEditDict()
        # file_path 在srt_orm是mp4，mp3名，在trans_orm是srt名
        all_data = orm.query_data_format_unid_path()
        for item in all_data:
            try:
                obj_data: dict = json.loads(item.obj)
            except json.decoder.JSONDecodeError as e:
                config.logger.error(f'{item.unid} 该数据 obj解析失败: {e}')
            srt_edit_dict.job_type = obj_data.get('job_type', '')
            srt_edit_dict.raw_noextname = obj_data.get('raw_noextname', '')
            srt_edit_dict.unid = obj_data.get('unid', '')
            if st == 0:
                # todo：拼完了测试一下
                srt_path = obj_data.get('srt_dirname', '')
                srt_edit_dict.srt_path = srt_path

            elif st == 1:
                srt_edit_dict.srt_path = item.path

            filename_without_extension: str = obj_data.get('raw_noextname', '')
            config.logger.debug(f"文件:{filename_without_extension} 状态:{item.job_status}")
            self._process_item(item, srt_edit_dict)

    def _create_action_button(self, icon, tooltip, callback, size=button_size):
        """
        创建一个工具按钮，并设置其图标、提示和点击事件。
        参数:
            icon: 按钮的图标。
            tooltip: 鼠标悬停时显示的提示信息。
            callback: 按钮被点击时调用的回调函数。
            size: 按钮的大小，默认值为变量 button_size。

        返回:
            ToolButton 对象，该对象根据提供的参数进行了初始化。

        """
        button = ToolButton(icon)
        button.setFixedSize(size)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        # 设置工具提示立即显示
        button.installEventFilter(ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT))
        button.clicked.connect(callback)
        return button

    def _set_row_buttons(self, row, button_types):
        # 4个按钮创建并添加到表格的第4列
        button_layout = QHBoxLayout()
        button_layout.setSpacing(2)  # 设置按钮之间的间距
        button_layout.setContentsMargins(0, 0, 0, 0)

        # 添加一个伸缩项,将按钮推到右侧
        button_layout.addStretch()

        for button_type in button_types:

            if button_type == ButtonType.EXPORT:
                button = self._create_action_button(FluentIcon.DOWN, "导出字幕", self._export_row)
            elif button_type == ButtonType.EDIT:
                button = self._create_action_button(FluentIcon.EDIT, "编辑字幕", self._edit_row)
            elif button_type == ButtonType.START:
                button = self._create_action_button(FluentIcon.PLAY, "开始任务", self._start_row)
            elif button_type == ButtonType.DELETE:
                button = self._create_action_button(FluentIcon.DELETE, "删除字幕", self._delete_row)
            button_layout.addWidget(button)

        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        self.table.setCellWidget(row, 3, button_widget)

    def _process_item(self, item, edit_dict: SrtEditDict):
        """
        处理单个项目并更新表格。

        :param item: 数据库查询返回的项目对象
        :param edit_dict: srt_edit_dict = {"media_path":"", "srt_path":"", "job_type":"","raw_noextname":""}

        """
        if item.job_status in (0, 1):
            if item.job_status == 1:
                self._update_job_status(item)

            self.table_row_init(edit_dict, 0)
        elif item.job_status == 2:
            self.addRow_init_all(edit_dict)

    def _update_job_status(self, item):
        new_status = 0
        # todo：?? row呢
        # orm_table = self._choose_sql_orm(row)
        self.srt_orm.update_table_unid(item.unid, job_status=new_status)

    def table_row_init(self, obj_format: SrtEditDict, job_status: int = 1):
        if job_status == 1:
            config.logger.debug(f"添加新文件:{obj_format['raw_noextname']} 到我的创作列表")
        filename = obj_format.raw_noextname
        unid = obj_format.unid
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
        file_unid.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 4, file_unid)

        # 隐藏列数据:文件名
        file_full = QTableWidgetItem()
        file_full.setData(SrtEditDictRole, obj_format)
        self.table.setItem(row_position, 5, file_full)

    def table_row_working(self, unid: str, progress: float):
        if unid in self.row_cache:
            row = self.row_cache[unid]
            config.logger.debug(f"找到文件:{unid}的行索引:{row}")
        else:
            config.logger.warning(f"未找到文件:{unid}的行索引,尝试从缓存中查找")
            row = self.find_row_by_identifier(unid)
            if row is not None:
                self.row_cache[unid] = row
            else:
                return

        progress_bar = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
        config.logger.info(f"更新文件:{unid}的进度条:{progress}")
        progress_bar.setText(f"处理中 {progress}")

    def find_row_by_identifier(self, unid):
        # 此函数用于根据唯一标识符（unid）在表格中查找行索引
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, TableWidgetColumn.UNID)
            if item and item.text() == unid:
                return row
        config.logger.error(f"未找到文件:{unid}的行索引,也未缓存,直接返回")
        return None

    def table_row_finish(self, unid):
        config.logger.info(f"文件处理完成:{unid},更新表单")

        if unid in self.row_cache:
            row = self.row_cache[unid]
            item = self.table.cellWidget(row, TableWidgetColumn.UNID)
            progress_bar = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
            progress_bar.setText("已完成")
            # todo：row呢
            # orm_table = self._choose_sql_orm(row)
            self.srt_orm.update_table_unid(unid, job_status=2)

            if unid in item.text():
                self._set_row_buttons(row, [ButtonType.EDIT, ButtonType.EXPORT, ButtonType.START, ButtonType.DELETE])
            else:
                config.logger.error(f"文件:{unid}的行索引,缓存中未找到,缓存未更新")

    def addRow_init_all(self, edit_dict: SrtEditDict):
        filename_without_extension = edit_dict.raw_noextname
        unid = edit_dict.unid
        config.logger.info(f"添加已完成:{filename_without_extension} 到我的创作列表")
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        chk = CheckBox()
        chk.stateChanged.connect(self._update_buttons_visibility)
        self.table.setCellWidget(row_position, 0, chk)

        file_name = QLabel()
        file_name.setText(filename_without_extension)
        file_name.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 1, file_name)

        file_stat = QLabel()
        file_stat.setText("已完成")
        file_stat.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 2, file_stat)

        self._set_row_buttons(row_position, [ButtonType.EXPORT, ButtonType.EDIT, ButtonType.START, ButtonType.DELETE])

        # 隐藏列数据:unid
        file_unid = QLabel()
        file_unid.setText(unid)
        file_unid.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, 4, file_unid)

        # 隐藏列数据:文件名
        file_full = QTableWidgetItem()
        file_full.setData(SrtEditDictRole, edit_dict)
        self.table.setItem(row_position, 5, file_full)

    def _start_row(self):
        # todo 从数据库中获取数据，传到work_queue中的数据格式需要调整
        # 1.和consume_mp4_queue接受的一样
        # 2.检查一下config.params的值是否和旧任务时一样,不一样也需要存到库中,再加载出来
        row = self._get_row()
        unid_item = self.table.cellWidget(row, TableWidgetColumn.UNID)
        orm_table = self._choose_sql_orm(row)
        job_path = orm_table.query_data_by_unid(unid_item).path
        if not os.path.isfile(job_path):
            config.logger.error(f"文件:{job_path}不存在,无法开始处理")
            raise FileNotFoundError(f"The file {job_path} does not exist.")
        tools.format_video(job_path.replace('\\', '/'), config.params['target_dir'])
        work_queue.lin_queue_put(job_path)

    def _delete_row(self):
        button_row = self._get_row()
        unid_item = self.table.cellWidget(button_row, TableWidgetColumn.UNID)
        """
        删除这三步是有先后顺序的,先删除文件,再删除数据库中的数据,再删除表格行,最后清除缓存索引
        删除result中对应文件
        """

        text = unid_item.text()
        config.logger.info(f"删除文件所在行:{button_row + 1} | unid:{text} ")
        orm_table = self._choose_sql_orm(button_row)
        if text:
            job_obj = json.loads(orm_table.query_data_by_unid(text).obj)
            result_dir = job_obj["output"]
            try:
                # 删除本地文件
                shutil.rmtree(result_dir)
                config.logger.info(f"删除目录:{result_dir} 成功")
            except Exception as e:
                config.logger.error(f"删除目录:{result_dir} 失败:{e}")
        # 在数据库中删除对应数据
        orm_table.delete_table_unid(text)
        # 删除表格行
        self.table.removeRow(button_row)
        # 清除缓存索引
        config.logger.info(f'row_cache before deletion :{self.row_cache}')
        self.row_cache.pop(text, None)  # 如果键不存在，返回 None 而不是引发异常
        InfoBar.success(title='成功', content="文件已删除", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                        parent=self)

    def _get_row(self):
        # 获取操作所在行
        button = self.sender()
        return self.table.indexAt(button.parent().pos()).row()

    def _delete_batch(self):
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, TableWidgetColumn.CHECKBOX).isChecked():
                self._delete_row()

    def searchFiles(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, TableWidgetColumn.FILENAME)
            config.logger.info(f"item:{item.text()}")
            if text.lower() in item.text().lower():
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def _export_batch(self):
        # 打开系统文件夹选择框
        # todo: 导出换成srt_edit文件中函数
        job_path, file_path = None, None
        options = QFileDialog.Options()
        file_dir = QFileDialog.getExistingDirectory(self, "选择文件夹", "", options=options)

        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 4):
                unid_item = self.table.cellWidget(row, TableWidgetColumn.UNID)
                orm_table = self._choose_sql_orm(row)
                job_obj = json.loads(orm_table.query_data_by_unid(unid_item.text()).obj)
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

    def _export_row(self):
        row = self._get_row()
        options = QFileDialog.Options()
        item = self.table.cellWidget(row, TableWidgetColumn.FILENAME)
        config.logger.info(f"文件所在行:{row + 1} 文件名:{item.text()}")
        export_name = f"{item.text()}.srt"
        file_path, _ = QFileDialog.getSaveFileName(self, "导出文件", export_name, options=options)
        if file_path:
            orm_table = self._choose_sql_orm(row)
            unid_item = self.table.cellWidget(row, TableWidgetColumn.UNID)
            config.logger.info(f"unid_item:{unid_item}")
            config.logger.info(f"导出文件:{unid_item.text()} 成功")
            job_obj = json.loads(orm_table.query_data_by_unid(unid_item.text()).obj)
            config.logger.info(f"job_obj:{job_obj}")
            job_path = f'{job_obj["output"]}/{job_obj["raw_noextname"]}.srt'
            config.logger.info(f"导出文件:{job_path}到{file_path}")
            shutil.copy(job_path, file_path)
            InfoBar.success(title='成功', content="文件已导出", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                            parent=self)

    def _update_buttons_visibility(self):
        # 检查所有行的复选框状态，如果有任何一个被勾选，则显示按钮
        any_checked = any(self.table.cellWidget(row, TableWidgetColumn.CHECKBOX).isChecked() for row in range(self.table.rowCount()))
        self.deleteBtn.setVisible(any_checked)
        self.exportBtn.setVisible(any_checked)

    def _edit_row(self):
        """打开字幕编辑页面"""
        row = self._get_row()
        file_path: dict = eval(self.table.cellWidget(row, TableWidgetColumn.JOB_OBJ).text())  # 获取文件名
        if not os.path.isfile(file_path['srt_path']):
            config.logger.error(f"The file {file_path['srt_path']} does not exist.")
            InfoBar.error(title='错误', content="文件不存在", orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2000,
                          parent=self)
            raise FileNotFoundError(f"The file {file_path['srt_path']} does not exist.")

        config.logger.info(f"打开文件:{file_path}的字幕编辑页面")
        # 创建并显示字幕编辑页面
        edit_page = SubtitleEditPage(file_path['srt_path'], file_path['media_path'], self.settings, parent=self)
        edit_page.show()


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
