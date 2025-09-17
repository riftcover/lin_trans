import json
import os
import shutil
from enum import Enum, auto, IntEnum
from typing import Optional, Tuple, Literal

from PySide6.QtCore import Qt, QThread, Slot
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget, QTableWidgetItem, QHeaderView, QDialog, QCheckBox, )
from pydantic import ValidationError

from components import LinIcon, GuiSize
from components.widget import StatusLabel
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from nice_ui.task.main_worker import work_queue, QueueConsumer
from nice_ui.task.orm_factory import OrmFactory
from nice_ui.ui import SUBTITLE_EDIT_DIALOG_SIZE
from nice_ui.ui.srt_edit import SubtitleEditPage, ExportSubtitleDialog
from nice_ui.util.tools import VideoFormatInfo
from orm.queries import ToSrtOrm, ToTranslationOrm
from utils import logger
from vendor.qfluentwidgets import (TableWidget, CheckBox, InfoBar, InfoBarPosition, FluentIcon, CardWidget, SearchLineEdit, ToolButton, ToolTipPosition,
                                   ToolTipFilter, TransparentToolButton, )
from nice_ui.task import WORK_TYPE, WORK_TYPE_NAME

JOB_STATUS = Literal[0, 1, 2, 3, 4]


class ButtonType(Enum):
    START = auto()
    EXPORT = auto()
    EDIT = auto()
    DELETE = auto()


class TableWidgetColumn(IntEnum):
    CHECKBOX = 0
    FILENAME = 1
    TASK_TYPE = 2
    CREATE_TIME = 3
    JOB_STATUS = 4
    BUTTON_WIDGET = 5
    UNID = 6
    JOB_OBJ = 7


# 定义一个自定义角色用于存储 VideoFormatInfo 对象
VideoFormatInfoRole = Qt.UserRole + 1


class TableApp(CardWidget):
    button_size = GuiSize.row_button_size

    def __init__(self, text: str, parent=None, settings=None):
        super().__init__(parent=parent)
        self.settings = settings
        self.setObjectName(text)
        self.setupUi()
        self.data_bridge = data_bridge
        self._connect_signals()
        # 使用ORM工厂获取ORM实例
        self.orm_factory = OrmFactory()
        self.srt_orm = self.orm_factory.get_srt_orm()
        self.trans_orm = self.orm_factory.get_trans_orm()
        self.row_cache = {}
        self._init_table()

    def _connect_signals(self):
        """
        连接信号槽
        """
        self.data_bridge.update_table.connect(self.table_row_init)
        self.data_bridge.whisper_working.connect(self.table_row_working)
        self.data_bridge.whisper_finished.connect(self.table_row_finish)
        self.data_bridge.task_error.connect(self.table_row_failed)
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
        self.table.setColumnCount(8)

        # 设置表格标题
        headers = ["", "文件名", "任务类型", "创建时间", "状态", "操作", "", ""]
        self.table.setHorizontalHeaderLabels(headers)

        self.table.horizontalHeader().setVisible(True)
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
        self.table.setColumnHidden(6, True)  # UNID列
        self.table.setColumnHidden(7, True)  # JOB_OBJ列
        layout.addWidget(self.table)

    def _set_column_widths(self):
        widths = [50, -1, 100, 140, 120, 160]  # 调整列宽: 复选框, 文件名, 任务类型, 创建时间, 状态, 按钮
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

        # 合并两个数据源并按创建时间倒序排列
        all_data = list(srt_data) + list(trans_data)
        all_data.sort(key=lambda x: x.created_at, reverse=True)

        processed_unids = set()

        for item in all_data:
            if item.unid not in processed_unids:
                self._process_item(item, processed_unids)

    def _choose_sql_orm(self, row: int) -> Optional[ToSrtOrm | ToTranslationOrm]:
        item = self.table.item(row, TableWidgetColumn.JOB_OBJ)
        # work_obj 取值是_load_data中srt_edit_dict
        work_obj = item.data(VideoFormatInfoRole)

        work_type = work_obj.work_type
        # 使用ORM工厂获取对应的ORM
        return self.orm_factory.get_orm_by_work_type(work_type)

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
            created_at=None,
    ) -> Tuple[CheckBox, QLabel]:
        # 添加复选框
        chk = CheckBox()
        chk.stateChanged.connect(self._update_buttons_visibility)
        self.table.setCellWidget(row_position, TableWidgetColumn.CHECKBOX, chk)

        # 添加文件名
        file_name = QLabel(filename)
        file_name.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setCellWidget(row_position, TableWidgetColumn.FILENAME, file_name)

        # 添加任务类型
        task_type = self._format_task_type(obj_format.work_type)
        task_type_label = QLabel(task_type)
        task_type_label.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, TableWidgetColumn.TASK_TYPE, task_type_label)

        # 添加创建时间
        create_time = self._format_create_time(created_at)
        create_time_label = QLabel(create_time)
        create_time_label.setAlignment(Qt.AlignCenter)
        self.table.setCellWidget(row_position, TableWidgetColumn.CREATE_TIME, create_time_label)

        # 添加状态
        file_status = StatusLabel("")
        # 创建一个容器来居中显示StatusLabel
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(file_status)
        self.table.setCellWidget(
            row_position, TableWidgetColumn.JOB_STATUS, status_container
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

    def _format_task_type(self, work_type:WORK_TYPE) -> str:
        """格式化任务类型显示"""
        return "未知" if work_type is None else WORK_TYPE_NAME.get_name(work_type)

    def _format_create_time(self, created_at) -> str:
        """格式化创建时间显示"""
        return "-" if created_at is None else created_at.strftime("%Y-%m-%d %H:%M")

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
        self.table.setCellWidget(row, TableWidgetColumn.BUTTON_WIDGET, button_widget)

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
                    self.table_row_init(obj_data, 0, item.created_at)
                elif item.job_status == 2:
                    self.addRow_init_all(obj_data, item.created_at)
                elif item.job_status == 4:
                    # 失败状态：显示为失败状态的行
                    self.table_row_init(obj_data, 0, item.created_at)
                    # 立即更新为失败状态显示
                    self.table_row_failed(item.unid, "任务执行失败")
            else:
                logger.warning(f"{item.unid} 该数据 obj为空")
        except ValidationError as e:
            logger.error(f"{item.unid} 该数据 obj解析失败: {e}")

    def _update_job_status(self, item, edit_dict):
        new_status = 0
        work_type = edit_dict.work_type
        orm_w = self.orm_factory.set_orm_job_status(work_type)
        orm_w.update_table_unid(item.unid, job_status=new_status)

    def table_row_init(self, obj_format: VideoFormatInfo, job_status: JOB_STATUS = 1, created_at=None):
        if job_status == 1:
            logger.debug(f"添加新文件:{obj_format.raw_noextname} 到我的创作列表")

        # 如果没有传入创建时间，使用当前时间（新建任务的情况）
        if created_at is None:
            from datetime import datetime
            created_at = datetime.now()

        filename = obj_format.raw_noextname
        unid = obj_format.unid
        row_position = 0  # 插入到第一行
        self.table.insertRow(row_position)
        chk, file_status = self._add_common_widgets(
            row_position, filename, unid, job_status, obj_format, created_at
        )
        if job_status == 1:
            chk.setEnabled(False)
            file_status.set_status("排队中")
        elif job_status == 0:
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

        status_container = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
        logger.info(f"更新文件:{unid}的进度条:{progress}")
        # todo: 处理中，删除别的任务，报错AttributeError: 'NoneType' object has no attribute 'setText'
        # 从容器中获取StatusLabel
        if status_container and status_container.layout():
            progress_bar = status_container.layout().itemAt(0).widget()
            if hasattr(progress_bar, 'setText'):
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
        logger.debug(f"缓存:{self.row_cache}")

        if unid in self.row_cache:
            row = self.row_cache[unid]
            item = self.table.cellWidget(row, TableWidgetColumn.UNID)
            status_container = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
            chk = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)
            chk.setEnabled(True)
            # 从容器中获取StatusLabel
            if status_container and status_container.layout():
                progress_bar = status_container.layout().itemAt(0).widget()
                if hasattr(progress_bar, 'set_status'):
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
            logger.error(f'缓存中未找到{unid}的行索引,缓存:{self.row_cache}')

    @Slot(str, str)
    def table_row_failed(self, unid: str, error_message: str):
        """处理任务失败状态"""
        logger.error(f"任务失败: {unid} - {error_message}")

        ask = self.row_cache
        if unid in ask:
            row = self.row_cache[unid]
        else:
            logger.debug(f"缓存未找到文件:{unid}的索引,尝试从列表中查找")
            row = self.find_row_by_identifier(unid)
            if row is not None:
                ask[unid] = row
            else:
                logger.error(f"未找到任务:{unid}的行索引")
                return

        # 更新UI状态
        status_container = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
        chk = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)

        # 安全地更新状态显示
        if status_container:
            # 尝试从容器中获取StatusLabel
            if status_container.layout():
                progress_bar = status_container.layout().itemAt(0).widget()
                if hasattr(progress_bar, 'set_status'):
                    progress_bar.set_status("处理失败")
                elif hasattr(progress_bar, 'setText'):
                    progress_bar.setText("处理失败")
                else:
                    logger.warning(f"无法更新状态显示，未知的组件类型: {type(progress_bar)}")
            else:
                # 直接是StatusLabel的情况
                if hasattr(status_container, 'set_status'):
                    status_container.set_status("处理失败")
                elif hasattr(status_container, 'setText'):
                    status_container.setText("处理失败")
                else:
                    logger.warning(f"无法更新状态显示，未知的组件类型: {type(status_container)}")

        if chk:
            chk.setEnabled(True)

        # 更新数据库状态为失败 (job_status=4表示失败)
        orm_result = self._choose_sql_orm(row)
        if isinstance(orm_result, tuple):
            # ASR_TRANS 任务
            srt_orm, trans_orm = orm_result
            srt_orm.update_table_unid(unid, job_status=4)
            trans_orm.update_table_unid(unid, job_status=4)
        else:
            orm_result.update_table_unid(unid, job_status=4)

        # 设置按钮状态（只显示删除按钮，因为失败的任务可以重新开始）
        self._set_row_buttons(row, [ButtonType.DELETE])

        logger.info(f"已更新任务失败状态: {unid}")

    def addRow_init_all(self, edit_dict: VideoFormatInfo, created_at=None):
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
            row_position, filename_without_extension, unid, 2, edit_dict, created_at
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
        """删除单行 - 通过按钮触发"""
        button_row = self._get_row()
        if delete_info := self._extract_delete_info(button_row):
            success = self._execute_delete(delete_info)
            self._show_delete_result(success, single=True)

    def _extract_delete_info(self, row: int) -> Optional[dict]:
        """提取删除所需的信息"""
        try:
            unid_item = self.table.cellWidget(row, TableWidgetColumn.UNID)
            if not unid_item:
                logger.error(f"无法获取行{row}的UNID")
                return None

            unid = unid_item.text()
            job_obj = self.table.item(row, TableWidgetColumn.JOB_OBJ)
            if not job_obj:
                logger.error(f"无法获取行{row}的任务对象")
                return None

            work_obj = job_obj.data(VideoFormatInfoRole)
            if not work_obj:
                logger.error(f"无法获取行{row}的工作对象")
                return None

            return {
                'row': row,
                'unid': unid,
                'work_obj': work_obj
            }
        except Exception as e:
            logger.error(f"提取删除信息失败: 行{row}, 错误: {e}")
            return None

    def _execute_delete(self, delete_info: dict) -> bool:
        """执行删除操作的核心逻辑"""
        row = delete_info['row']
        unid = delete_info['unid']
        work_obj = delete_info['work_obj']

        logger.info(f"准备删除文件所在行:{row + 1} | unid:{unid}")

        # 1. 删除本地文件
        if not self._delete_local_files(work_obj.output, unid):
            return False

        # 2. 删除数据库记录
        if not self._delete_database_records(row, unid):
            return False

        # 3. 删除表格行和更新缓存
        self.table.removeRow(row)
        self.row_cache.pop(unid, None)
        logger.info(f"已删除 unid:{unid}, row_cache 更新后:{self.row_cache}")

        return True

    def _delete_local_files(self, result_dir: str, unid: str) -> bool:
        """删除本地文件"""
        if not result_dir or not os.path.exists(result_dir):
            return True  # 文件不存在视为删除成功

        try:
            shutil.rmtree(result_dir)
            logger.info(f"删除目录:{result_dir} 成功")
            return True
        except Exception as e:
            logger.error(f"删除目录:{result_dir} 失败:{e}")
            return False

    def _delete_database_records(self, row: int, unid: str) -> bool:
        """删除数据库记录"""
        try:
            orm_result = self._choose_sql_orm(row)
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
            return success
        except Exception as e:
            logger.error(f"删除数据库记录时发生错误: unid:{unid}, 错误: {str(e)}")
            return False

    def _show_delete_result(self, success: bool, single: bool = True, count: int = 0):
        """显示删除结果"""
        if success:
            if single:
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
                InfoBar.success(
                    title="批量删除成功",
                    content=f"已删除 {count} 个任务",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self,
                )
        else:
            error_msg = "删除失败" if single else "没有成功删除任何任务"
            InfoBar.error(
                title="错误",
                content=error_msg,
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
        """批量删除 - 函数式方法：先收集要保留的行，再重建表格"""
        # 收集要保留的行和要删除的项目
        rows_to_keep, items_to_delete = self._partition_rows_by_selection()

        if not items_to_delete:
            self._show_no_selection_warning()
            return

        # 先执行资源清理（文件和数据库）
        successful_deletes = [
            item for item in items_to_delete
            if self._cleanup_item_resources(item)
        ]

        if successful_deletes:
            # 重建表格（只保留未删除的行）
            self._rebuild_table_with_kept_rows(rows_to_keep)

            # 清理缓存
            self._cleanup_cache_for_deleted_items(successful_deletes)

        # 显示结果
        self._show_batch_delete_result(len(successful_deletes), len(items_to_delete))

    def _partition_rows_by_selection(self) -> tuple[list, list]:
        """将表格行分为要保留的和要删除的两部分"""
        rows_to_keep = []
        items_to_delete = []

        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)

            if checkbox_widget and checkbox_widget.isChecked():
                if delete_info := self._extract_delete_info(row):
                    items_to_delete.append(delete_info)
            elif keep_info := self._extract_row_data(row):
                rows_to_keep.append(keep_info)

        return rows_to_keep, items_to_delete

    def _extract_row_data(self, row: int) -> Optional[dict]:
        """提取行的完整数据，用于重建表格"""
        try:
            # 提取所有列的数据
            row_data = {}

            # 复选框状态
            checkbox = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)
            row_data['checkbox_checked'] = checkbox.isChecked() if checkbox else False

            # 文件名
            filename_widget = self.table.cellWidget(row, TableWidgetColumn.FILENAME)
            row_data['filename'] = filename_widget.text() if filename_widget else ""

            # 任务类型
            task_type_widget = self.table.cellWidget(row, TableWidgetColumn.TASK_TYPE)
            row_data['task_type'] = task_type_widget.text() if task_type_widget else ""

            # 创建时间
            create_time_widget = self.table.cellWidget(row, TableWidgetColumn.CREATE_TIME)
            row_data['create_time'] = create_time_widget.text() if create_time_widget else ""

            # 任务状态
            status_widget = self.table.cellWidget(row, TableWidgetColumn.JOB_STATUS)
            row_data['job_status'] = status_widget.text() if status_widget else ""

            # UNID
            unid_widget = self.table.cellWidget(row, TableWidgetColumn.UNID)
            row_data['unid'] = unid_widget.text() if unid_widget else ""

            # 任务对象
            job_obj = self.table.item(row, TableWidgetColumn.JOB_OBJ)
            row_data['work_obj'] = job_obj.data(VideoFormatInfoRole) if job_obj else None

            # 按钮组件（需要重新创建）
            row_data['original_row'] = row

            return row_data
        except Exception as e:
            logger.error(f"提取行数据失败: 行{row}, 错误: {e}")
            return None

    def _cleanup_item_resources(self, item: dict) -> bool:
        """清理单个项目的资源（文件和数据库）"""
        unid = item['unid']
        work_obj = item['work_obj']

        # 删除本地文件
        if not self._delete_local_files(work_obj.output, unid):
            return False

        # 删除数据库记录
        if not self._delete_database_records(item['row'], unid):
            return False

        return True

    def _rebuild_table_with_kept_rows(self, rows_to_keep: list):
        """重建表格，只包含要保留的行"""
        # 清空表格
        self.table.setRowCount(0)

        # 重新添加保留的行
        for i, row_data in enumerate(rows_to_keep):
            self.table.insertRow(i)
            self._populate_table_row(i, row_data)

    def _populate_table_row(self, row: int, row_data: dict):
        """填充表格行数据"""
        try:
            # 复选框
            checkbox = QCheckBox()
            checkbox.setChecked(row_data['checkbox_checked'])
            self.table.setCellWidget(row, TableWidgetColumn.CHECKBOX, checkbox)

            # 文件名
            filename_label = QLabel(row_data['filename'])
            self.table.setCellWidget(row, TableWidgetColumn.FILENAME, filename_label)

            # 任务状态
            status_label = QLabel(row_data['job_status'])
            self.table.setCellWidget(row, TableWidgetColumn.JOB_STATUS, status_label)

            # UNID
            unid_label = QLabel(row_data['unid'])
            self.table.setCellWidget(row, TableWidgetColumn.UNID, unid_label)

            # 任务对象
            job_item = QTableWidgetItem()
            job_item.setData(VideoFormatInfoRole, row_data['work_obj'])
            self.table.setItem(row, TableWidgetColumn.JOB_OBJ, job_item)

            # 重新创建按钮组件
            self._create_row_buttons(row, row_data['work_obj'])

        except Exception as e:
            logger.error(f"填充表格行失败: 行{row}, 错误: {e}")

    def _cleanup_cache_for_deleted_items(self, deleted_items: list):
        """清理已删除项目的缓存"""
        for item in deleted_items:
            unid = item['unid']
            self.row_cache.pop(unid, None)

        logger.info(f"已清理 {len(deleted_items)} 个缓存项, 当前缓存: {self.row_cache}")

    def _show_no_selection_warning(self):
        """显示未选择任何项目的警告"""
        InfoBar.warning(
            title="提示",
            content="请先选择要删除的任务",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self,
        )

    def _show_batch_delete_result(self, successful_count: int, total_count: int):
        """显示批量删除结果"""
        if successful_count == total_count and successful_count > 0:
            # 全部成功
            InfoBar.success(
                title="批量删除成功",
                content=f"已删除 {successful_count} 个任务",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        elif successful_count > 0:
            # 部分成功
            InfoBar.warning(
                title="部分删除成功",
                content=f"成功删除 {successful_count}/{total_count} 个任务",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
        else:
            # 全部失败
            InfoBar.error(
                title="删除失败",
                content="没有成功删除任何任务",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )

    def _create_row_buttons(self, row: int, work_obj):
        """为重建的行创建按钮组件"""
        # 根据任务状态确定按钮类型
        button_types = [ButtonType.EDIT, ButtonType.EXPORT, ButtonType.DELETE]

        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(2)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        button_layout.addStretch()

        # 创建按钮
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
            elif button_type == ButtonType.DELETE:
                button = self._create_action_button(
                    FluentIcon.DELETE, "删除字幕", self._delete_row
                )
            else:
                continue

            button_layout.addWidget(button)

        # 创建按钮容器
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        self.table.setCellWidget(row, TableWidgetColumn.BUTTON_WIDGET, button_widget)

    def _collect_selected_rows(self) -> list:
        """收集所有选中的行信息"""
        rows_to_delete = []

        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, TableWidgetColumn.CHECKBOX)
            if checkbox_widget and checkbox_widget.isChecked():
                if delete_info := self._extract_delete_info(row):
                    rows_to_delete.append(delete_info)

        return rows_to_delete

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


if __name__ == "__main__":
    import sys
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication


    def main():
        app = QApplication(sys.argv)

        window = TableApp("字幕翻译", settings=QSettings("Locoweed", "LinLInTrans"))
        window.show()
        sys.exit(app.exec())


    main()
