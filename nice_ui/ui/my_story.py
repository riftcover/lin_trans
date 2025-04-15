import json
import os
import shutil
from enum import Enum, auto, IntEnum
from typing import Optional, Tuple, Literal

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget, QTableWidgetItem, QHeaderView, QDialog, )
from pydantic import ValidationError

from components import LinIcon, GuiSize
from components.widget import StatusLabel
from nice_ui.configure import config
from nice_ui.task import WORK_TYPE
from nice_ui.task.main_worker import work_queue, QueueConsumer
from nice_ui.ui import SUBTITLE_EDIT_DIALOG_SIZE
from nice_ui.ui.srt_edit import SubtitleEditPage, ExportSubtitleDialog
from nice_ui.util.tools import VideoFormatInfo
from orm.queries import ToSrtOrm, ToTranslationOrm
from utils import logger
from vendor.qfluentwidgets import (TableWidget, CheckBox, InfoBar, InfoBarPosition, FluentIcon, CardWidget, SearchLineEdit, ToolButton, ToolTipPosition,
                                   ToolTipFilter, TransparentToolButton, )

JOB_STATUS = Literal[0, 1, 2, 3, 4]


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


# 定义一个自定义角色用于存储 VideoFormatInfo 对象
VideoFormatInfoRole = Qt.UserRole + 1


class TableApp(CardWidget):
    button_size = GuiSize.row_button_size

    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setObjectName(text.replace("", "-"))
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
        self.exportBtn = self._create_button(
            LinIcon.EXPORT(), "批量导出", self._export_batch
        )
        self.exportBtn.setIconSize(GuiSize.row_button_icon_size)
        self.deleteBtn = self._create_button(
            FluentIcon.DELETE, "批量删除", self._delete_batch
        )
        self.searchInput = self._create_search_input()

        top_layout.addWidget(self.selectAllBtn)
        top_layout.addWidget(self.exportBtn)
        top_layout.addWidget(self.deleteBtn)
        top_layout.addStretch()
        top_layout.addWidget(self.searchInput)

        layout.addWidget(top_card)
        self._setup_table(layout)

    @staticmethod
    def _create_button(icon, tooltip: str, callback: callable):
        """
        生成顶部空间中的按钮
        """
        button = ToolButton(icon)
        button.setFixedSize(GuiSize.top_button_size)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        button.installEventFilter(
            ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT)
        )
        button.clicked.connect(callback)
        button.setVisible(False)
        return button

    def _create_search_input(self) -> SearchLineEdit:
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
        self.table.setAlternatingRowColors(True)
        # self.table.setStyleSheet("""
        #         QTableWidget {
        #             background-color: transparent;
        #         }
        #         QTableWidget::item {
        #             padding: 5px;
        #         }
        #     """)
        self._set_column_widths()
        self.table.setColumnHidden(4, True)
        self.table.setColumnHidden(5, True)
        layout.addWidget(self.table)

    def _set_column_widths(self):
        widths = [50, -1, 120, 160]  # 调整列宽
        for i, width in enumerate(widths):
            if width == -1:
                self.table.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.Stretch
                )
            else:
                self.table.setColumnWidth(i, width)

    def _selectAll(self):
        for row in range(self.table.rowCount()):
            chk = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)
            if chk.isEnabled():
                chk.setChecked(self.selectAllBtn.isChecked())

    def _init_table(self):
        # 初始化列表数据：srt文件任务和翻译字幕任务
        srt_data = self.srt_orm.query_data_format_unid_path()
        trans_data = self.trans_orm.query_data_format_unid_path()

        processed_unids = set()

        for item in trans_data:
            self._process_item(item, processed_unids)

        for item in srt_data:
            if item not in processed_unids:
                self._process_item(item, processed_unids)

    def _choose_sql_orm(self, row: int) -> Optional[ToSrtOrm | ToTranslationOrm]:
        item = self.table.item(row, TableWidgetColumn.JOB_OBJ)
        # work_obj 取值是_load_data中srt_edit_dict
        work_obj = item.data(VideoFormatInfoRole)

        work_type = work_obj.work_type
        if work_type == WORK_TYPE.ASR:
            return self.srt_orm
        elif work_type == WORK_TYPE.TRANS:
            return self.trans_orm
        elif work_type == WORK_TYPE.ASR_TRANS:
            return self.srt_orm, self.trans_orm

    def _create_action_button(self, icon, tooltip: str, callback: callable):
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
        button = TransparentToolButton(icon)
        button.setFixedSize(GuiSize.row_button_size)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setToolTip(tooltip)
        # 设置工具提示立即显示
        button.installEventFilter(
            ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM_RIGHT)
        )
        button.clicked.connect(callback)
        return button

    def _add_common_widgets(
        self,
        row_position: int,
        filename: str,
        unid: str,
        job_status: JOB_STATUS,
        obj_format: VideoFormatInfo,
    ) -> Tuple[CheckBox, QLabel]:
        # 添加复选框
        chk = CheckBox()
        chk.stateChanged.connect(self._update_buttons_visibility)
        self.table.setCellWidget(row_position, TableWidgetColumn.CHECKBOX, chk)

        # 添加文件名
        file_name = QLabel(filename)
        file_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setCellWidget(row_position, TableWidgetColumn.FILENAME, file_name)

        # 添加状态
        file_status = StatusLabel("")
        file_status.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(
            row_position, TableWidgetColumn.JOB_STATUS, file_status
        )

        # 添加UNID
        file_unid = QLabel(unid)
        file_unid.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, TableWidgetColumn.UNID, file_unid)

        # 隐藏列数据:文件名
        file_full = QTableWidgetItem()
        file_full.setData(VideoFormatInfoRole, obj_format)
        self.table.setItem(row_position, TableWidgetColumn.JOB_OBJ, file_full)

        return chk, file_status

    def _set_row_buttons(self, row, button_types):
        # 4个按钮创建并添加到表格的第4列
        button_layout = QHBoxLayout()
        button_layout.setSpacing(2)  # 设置按钮之间的间距
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 添加一个伸缩项,将按钮推到右侧
        button_layout.addStretch()
        button = None
        for button_type in button_types:

            if button_type == ButtonType.EXPORT:
                button = self._create_action_button(
                    LinIcon.EXPORT(), "导出字幕", self._export_row
                )
                button.setIconSize(GuiSize.row_button_icon_size)
            elif button_type == ButtonType.EDIT:
                button = self._create_action_button(
                    FluentIcon.EDIT, "编辑字幕", self._edit_row
                )
            elif button_type == ButtonType.START:
                button = self._create_action_button(
                    FluentIcon.PLAY, "开始任务", self._start_row
                )
            elif button_type == ButtonType.DELETE:
                button = self._create_action_button(
                    FluentIcon.DELETE, "删除字幕", self._delete_row
                )
            button_layout.addWidget(button)

        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        self.table.setCellWidget(row, 3, button_widget)

    def _process_item(self, item, processed_unids):
        """
        处理单个项目并更新表格。

        :param item: 数据库查询返回的项目对象
        :param edit_dict: srt_edit_dict = {"media_dirname":"", "srt_dirname":"", "work_type":"","raw_noextname":""}

        """
        try:
            obj_data = VideoFormatInfo.model_validate_json(item.obj)
            if obj_data is not None:
                processed_unids.add(item.unid)
                if item.job_status in (0, 1):
                    if item.job_status == 1:
                        self._update_job_status(item, obj_data)
                    self.table_row_init(obj_data, 0)
                elif item.job_status == 2:
                    self.addRow_init_all(obj_data)
            else:
                logger.warning(f"{item.unid} 该数据 obj为空")
        except ValidationError as e:
            logger.error(f"{item.unid} 该数据 obj解析失败: {e}")

    def _update_job_status(self, item, edit_dict):
        new_status = 0
        orm_w = None
        work_type = edit_dict.work_type
        if work_type in (1, 3):
            orm_w = self.srt_orm
        elif work_type in (2, 3):
            orm_w = self.trans_orm

        orm_w.update_table_unid(item.unid, job_status=new_status)

    def table_row_init(self, obj_format: VideoFormatInfo, job_status: JOB_STATUS = 1):
        if job_status == 1:
            logger.debug(f"添加新文件:{obj_format.raw_noextname} 到我的创作列表")
        filename = obj_format.raw_noextname
        unid = obj_format.unid
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        logger.info("我的创作列表中添加新行")
        chk, file_status = self._add_common_widgets(
            row_position, filename, unid, job_status, obj_format
        )
        if job_status == 1:
            chk.setEnabled(False)
            file_status.set_status("排队中")
        elif job_status == 0:
            logger.debug(f"文件:{filename} 状态更新为未开始")
            chk.setEnabled(False)
            file_status.set_status("处理失败")
            # self._set_row_buttons(row_position, [ButtonType.START, ButtonType.DELETE])
            # todo 所有位置屏蔽开始任务按钮，当前trans，ast_trans任务不能开始。
            self._set_row_buttons(row_position, [ButtonType.DELETE])

    def table_row_working(self, unid: str, progress: float):
        ask = self.row_cache
        if unid in ask:
            # logger.debug(f"缓存中找到:{unid}的索引")
            row = self.row_cache[unid]
        else:
            logger.debug(f"缓存未找到文件:{unid}的索引,尝试从列表中查找")
            row = self.find_row_by_identifier(unid)
            if row is not None:
                ask[unid] = row
            else:
                return

        progress_bar = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
        logger.info(f"更新文件:{unid}的进度条:{progress}")
        # todo: 处理中，删除别的任务，报错AttributeError: 'NoneType' object has no attribute 'setText'
        progress_bar.setText(f"处理中 {progress}%")

    def find_row_by_identifier(self, unid: str) -> Optional[int]:
        # 此函数用于根据唯一标识符（unid）在表格中查找行索引
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, TableWidgetColumn.UNID)
            if item and item.text() == unid:
                return row
        logger.error(f"未找到文件:{unid}的行索引,也未缓存,直接返回")
        return None

    def table_row_finish(self, unid: str):
        logger.info(f"文件处理完成:{unid},更新表单")

        if unid in self.row_cache:
            row = self.row_cache[unid]
            item = self.table.cellWidget(row, TableWidgetColumn.UNID)
            progress_bar = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
            chk = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)
            chk.setEnabled(True)
            progress_bar.set_status("已完成")
            orm_result = self._choose_sql_orm(row)

            if isinstance(orm_result, tuple):
                # ASR_TRANS 任务
                srt_orm, trans_orm = orm_result
                srt_orm.update_table_unid(unid, job_status=2)
                trans_orm.update_table_unid(unid, job_status=2)
            else:
                orm_result.update_table_unid(unid, job_status=2)

            if unid in item.text():
                self._set_row_buttons(
                    row,
                    [
                        ButtonType.EDIT,
                        ButtonType.EXPORT,
                        # ButtonType.START,
                        ButtonType.DELETE,
                    ],
                )
            else:
                logger.error(f"文件:{unid}的行索引,缓存中未找到,缓存未更新")

    def addRow_init_all(self, edit_dict: VideoFormatInfo):
        try:
            filename_without_extension = edit_dict.raw_noextname
        except AttributeError:
            logger.error(f"添加行失败, 缺少必要参数: {edit_dict}")
            return
        unid = edit_dict.unid
        # logger.info(f"添加已完成:{filename_without_extension} 到我的创作列表")
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        _, file_status = self._add_common_widgets(
            row_position, filename_without_extension, unid, 2, edit_dict
        )
        file_status.set_status("已完成")

        self._set_row_buttons(
            row_position,
            # [ButtonType.EDIT, ButtonType.EXPORT, ButtonType.START, ButtonType.DELETE],
            [ButtonType.EDIT, ButtonType.EXPORT, ButtonType.DELETE],
        )

    def _start_row(self):
        row = self._get_row()
        unid_item = self.table.cellWidget(row, TableWidgetColumn.UNID)
        orm_result = self._choose_sql_orm(row)

        if isinstance(orm_result, tuple):
            # ASR_TRANS 任务
            srt_orm, trans_orm = orm_result
            job_content = srt_orm.query_data_by_unid(unid_item.text())
            # 可能需要额外处理 trans_orm 的数据
        else:
            job_content = orm_result.query_data_by_unid(unid_item.text())

        if job_content is None:
            logger.error(f"未找到 UNID 为 {unid_item.text()} 的任务")
            return

        try:
            # 将 job_content.obj 从 JSON 字符串转换为 dict
            job_obj_dict = json.loads(job_content.obj)

            # 使用 VideoFormatInfo 的 model_validate 方法将 dict 转换为 VideoFormatInfo 对象
            video_format_info = VideoFormatInfo.model_validate(job_obj_dict)
        except json.JSONDecodeError:
            logger.error(f"解析 job_content.obj 失败: {job_content.obj}")
            return
        except ValidationError as e:
            logger.error(f"验证 VideoFormatInfo 失败: {e}")
            return

        # 现在 video_format_info 是 VideoFormatInfo 类型的对象
        job_path = (
            video_format_info.media_dirname
        )  # 假设 media_dirname 是正确的路径属性

        if not os.path.isfile(job_path):
            logger.error(f"文件:{job_path}不存在,无法开始处理")
            InfoBar.error(
                title="错误",
                content="文件:{job_path}不存在,无法重新开始",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            raise FileNotFoundError(f"The file {job_path} does not exist.")

        # 将任务重新添加到工作队列
        work_queue.lin_queue_put(video_format_info)

        InfoBar.success(
            title="成功",
            content="任务已重新开始",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

        # 如果消费线程未运行，则启动它
        if not config.is_consuming:
            self.start_queue_consumer()

    def start_queue_consumer(self):
        logger.debug(f"检查config.is_consuming:{config.is_consuming}")
        if not config.is_consuming:
            logger.debug("开始消费队列")
            self.queue_consumer_thread = QThread()
            self.queue_consumer = QueueConsumer()
            self.queue_consumer.moveToThread(self.queue_consumer_thread)
            self.queue_consumer_thread.started.connect(
                self.queue_consumer.process_queue
            )
            self.queue_consumer.finished.connect(self.queue_consumer_thread.quit)
            self.queue_consumer.finished.connect(self.queue_consumer.deleteLater)
            self.queue_consumer_thread.finished.connect(
                self.queue_consumer_thread.deleteLater
            )
            self.queue_consumer_thread.start()
        else:
            logger.debug("消费队列正在工作")

    def _delete_row(self):
        button_row = self._get_row()
        unid_item = self.table.cellWidget(button_row, TableWidgetColumn.UNID)
        unid = unid_item.text()

        logger.info(f"准备删除文件所在行:{button_row + 1} | unid:{unid}")

        job_obj = self.table.item(button_row, TableWidgetColumn.JOB_OBJ)
        work_obj: VideoFormatInfo = job_obj.data(VideoFormatInfoRole)

        # 删除本地文件
        result_dir = work_obj.output
        if result_dir and os.path.exists(result_dir):
            try:
                shutil.rmtree(result_dir)
                logger.info(f"删除目录:{result_dir} 成功")
            except Exception as e:
                logger.error(f"删除目录:{result_dir} 失败:{e}")
                return

        # 删除数据库记录
        success = True
        try:
            orm_result = self._choose_sql_orm(button_row)
            if isinstance(orm_result, tuple):
                # ASR_TRANS 任务
                srt_orm, trans_orm = orm_result
                srt_success = srt_orm.delete_table_unid(unid)
                trans_success = trans_orm.delete_table_unid(unid)
                success = srt_success or trans_success
                if not srt_success:
                    logger.error(f"删除 srt 表中的记录失败: unid:{unid}")
                if not trans_success:
                    logger.error(f"删除 translation 表中的记录失败: unid:{unid}")
            else:
                # 单一任务
                success = orm_result.delete_table_unid(unid)
                if not success:
                    logger.error(f"删除数据库记录失败: unid:{unid}")
        except Exception as e:
            success = False
            logger.error(f"删除数据库记录时发生错误: unid:{unid}, 错误: {str(e)}")

        if success:
            # 删除表格行
            self.table.removeRow(button_row)
            # 清除缓存索引
            self.row_cache.pop(unid, None)
            logger.info(f"已删除 unid:{unid}, row_cache 更新后:{self.row_cache}")
            InfoBar.success(
                title="成功",
                content="任务已删除",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        else:
            InfoBar.error(
                title="错误",
                content="删除数据库记录失败",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )

    def _get_row(self):
        # 获取操作所在行
        button = self.sender()
        return self.table.indexAt(button.parent().pos()).row()

    def _delete_batch(self):
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, TableWidgetColumn.CHECKBOX).isChecked():
                self._delete_row()

    def searchFiles(self, text: str):
        for row in range(self.table.rowCount()):
            item = self.table.cellWidget(row, TableWidgetColumn.FILENAME)
            # logger.info(f"item:{item.text()}")
            if text.lower() in item.text().lower():
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def _export_batch(self):
        job_paths = []
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, TableWidgetColumn.CHECKBOX).isChecked():
                job_obj = self.table.item(row, TableWidgetColumn.JOB_OBJ)
                # work_obj 取值是_load_data中srt_edit_dict
                work_obj: VideoFormatInfo = job_obj.data(VideoFormatInfoRole)
                job_paths.append(work_obj.srt_dirname)

        dialog = ExportSubtitleDialog(job_paths, self)
        dialog.exec()

           # 清除所有复选框状态
        self.selectAllBtn.setChecked(False)  # 清除"全选"按钮状态
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)
            if checkbox.isChecked():
                checkbox.setChecked(False)

    def _export_row(self):
        row = self._get_row()
        job_obj = self.table.item(row, TableWidgetColumn.JOB_OBJ)
        # work_obj 取值是_load_data中srt_edit_dict
        work_obj: VideoFormatInfo = job_obj.data(VideoFormatInfoRole)
        logger.trace(f"work_obj:{work_obj}")
        srt_path = work_obj.srt_dirname
        if not os.path.isfile(srt_path):
            logger.error(f"文件:{srt_path}不存在,无法导出")
            InfoBar.error(
                title="错误",
                content="文件不存在",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
            raise FileNotFoundError(f"The file {srt_path} does not exist.")

        logger.info(f"导出字幕:{srt_path}")

        dialog = ExportSubtitleDialog([srt_path], self)
        if dialog.exec() == QDialog.Accepted:  # 如果导出成功
            InfoBar.success(
                title="成功",
                content="文件已导出",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )

    def _update_buttons_visibility(self):
        # 检查所有行的复选框状态，如果有任何一个被勾选，则显示按钮
        any_checked = any(
            self.table.cellWidget(row, TableWidgetColumn.CHECKBOX).isChecked()
            for row in range(self.table.rowCount())
        )
        self.deleteBtn.setVisible(any_checked)
        self.exportBtn.setVisible(any_checked)

    def _edit_row(self):
        row = self._get_row()
        job_obj = self.table.item(row, TableWidgetColumn.JOB_OBJ)
        work_obj: VideoFormatInfo = job_obj.data(VideoFormatInfoRole)
        srt_path = work_obj.srt_dirname
        if not os.path.isfile(srt_path):
            logger.error(f"文件:{srt_path}不存在,无法编辑")
            InfoBar.error(
                title="错误",
                content="文件不存在",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
            raise FileNotFoundError(f"The file {srt_path} does not exist.")

        # 创建一个新的对话框窗口
        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑字幕 - {work_obj.raw_noextname}")
        dialog.resize(SUBTITLE_EDIT_DIALOG_SIZE)  # 设置一个合适的初始大小

        # 创建SubtitleEditPage实例
        subtitle_edit_page = SubtitleEditPage(
            work_obj.srt_dirname, work_obj.media_dirname, self.settings, parent=dialog
        )

        # 创建垂直布局并添加SubtitleEditPage
        layout = QVBoxLayout(dialog)
        layout.addWidget(subtitle_edit_page)

        # 连接对话框的关闭信号
        def on_dialog_finished():
            subtitle_edit_page.deleteLater()  # 确保页面被正确删除

        dialog.finished.connect(on_dialog_finished)

        # 显示对话框
        dialog.exec()

# def main():
#     app = QApplication(sys.argv)
#
#     # 为 Mac 系统设置全局字体
#     if sys.platform == 'darwin':
#         font = app.font()
#         font.setFamily("PingFang SC")  # Mac 系统的默认中文字体
#         app.setFont(font)
#
#         # 设置全局样式表
#         app.setStyleSheet("""
#             * {
#                 font-family: "PingFang SC", "Heiti SC", ".AppleSystemUIFont", sans-serif;
#             }
#             QWidget {
#                 font-family: "PingFang SC", "Heiti SC", ".AppleSystemUIFont", sans-serif;
#             }
#         """)
#
#     window = TableApp("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
#     window.show()
#     sys.exit(app.exec())
#
# if __name__ == "__main__":
#     main()