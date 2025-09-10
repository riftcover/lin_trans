from typing import List

from PySide6.QtCore import QObject, Signal

from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
from nice_ui.task import WORK_TYPE
from nice_ui.task.queue_worker import LinQueue
from nice_ui.util import tools
from nice_ui.util.tools import set_process, VideoFormatInfo
from orm.queries import ToSrtOrm, ToTranslationOrm
from utils import logger

work_queue = LinQueue()


class TaskHandler:
    """
    任务处理器基类，负责处理不同类型的任务
    """
    def __init__(self, data_bridge_instance):
        self.data_bridge = data_bridge_instance

    def process_task(self, task_item: str, work_type: WORK_TYPE) -> VideoFormatInfo:
        """
        处理单个任务项
        """
        # 格式化任务信息
        obj_format = self._format_task(task_item, work_type)

        # 添加到工作队列
        work_queue.lin_queue_put(obj_format)

        # 添加文件到我的创作页表格中
        self.data_bridge.emit_update_table(obj_format)

        return obj_format

    def _format_task(self, task_item: str, work_type: WORK_TYPE) -> VideoFormatInfo:
        """
        格式化任务信息
        """
        logger.debug(f"检查target_dir:{config.params['target_dir']}")
        obj_format = tools.format_job_msg(task_item, config.params["target_dir"], work_type)
        target_path = f"{obj_format.output}/{obj_format.raw_noextname}.mp4"

        if len(target_path) >= 250:
            raise ValueError(f"文件路径过长: {target_path}")

        return obj_format


class ASRTaskHandler(TaskHandler):
    """
    ASR任务处理器
    """
    def process_tasks(self, task_items: List[str]) -> None:
        """
        处理ASR任务列表
        """
        srt_orm = ToSrtOrm()

        for item in task_items:
            logger.debug(f"处理ASR任务: {item}")

            # 处理任务并获取格式化后的任务信息
            obj_format = self.process_task(item, WORK_TYPE.ASR)

            # 添加任务到数据库
            self._add_to_database(srt_orm, obj_format)

            logger.debug("ASR任务添加完成")

    def _add_to_database(self, orm: ToSrtOrm, obj_format: VideoFormatInfo) -> None:
        """
        将ASR任务添加到数据库
        """
        orm.add_data_to_table(
            obj_format.unid,
            obj_format.raw_name,
            config.params["source_language"],
            config.params["source_language_code"],
            config.params["source_module_status"],
            config.params["source_module_name"],
            config.params["translate_status"],
            config.params["cuda"],
            obj_format.raw_ext,
            1,
            obj_format.model_dump_json(),
        )


class TransTaskHandler(TaskHandler):
    """
    翻译任务处理器
    """
    def process_tasks(self, task_items: List[str]) -> None:
        """
        处理翻译任务列表
        """
        trans_orm = ToTranslationOrm()
        token_service = ServiceProvider().get_token_service()

        for item in task_items:
            logger.debug(f"处理翻译任务: {item}")

            # 处理任务并获取格式化后的任务信息
            obj_format = self.process_task(item, WORK_TYPE.TRANS)

            # 将文件路径与unid关联起来
            token_service.transfer_task_key(item, obj_format.unid)
            logger.info(f"将文件路径与unid关联: {item} -> {obj_format.unid}")

            # 设置输出文件名
            obj_format.srt_dirname = f"{obj_format.output}/{obj_format.raw_noextname}_译文.srt"

            # 添加任务到数据库
            self._add_to_database(trans_orm, obj_format)

            logger.debug("翻译任务添加完成")

    def _add_to_database(self, orm: ToTranslationOrm, obj_format: VideoFormatInfo) -> None:
        """
        将翻译任务添加到数据库
        """
        orm.add_data_to_table(
            obj_format.unid,
            obj_format.raw_name,
            config.params["source_language"],
            config.params["source_language_code"],
            config.params["target_language"],
            config.params["translate_channel"],
            2,
            1,
            obj_format.model_dump_json(),
        )


class ASRTransTaskHandler(TaskHandler):
    """
    ASR+翻译组合任务处理器
    """
    def process_tasks(self, task_items: List[str]) -> None:
        """
        处理ASR+翻译任务列表
        """
        srt_orm = ToSrtOrm()

        for item in task_items:
            logger.debug(f"处理ASR+翻译任务: {item}")

            # 处理任务并获取格式化后的任务信息
            obj_format = self.process_task(item, WORK_TYPE.ASR_TRANS)

            # 添加任务到数据库
            self._add_to_database(srt_orm, obj_format)

            logger.debug("ASR+翻译任务添加完成")

    def _add_to_database(self, orm: ToSrtOrm, obj_format: VideoFormatInfo) -> None:
        """
        将ASR+翻译任务添加到数据库
        """
        orm.add_data_to_table(
            obj_format.unid,
            obj_format.raw_name,
            config.params["source_language"],
            config.params["source_language_code"],
            config.params["source_module_status"],
            config.params["source_module_name"],
            config.params["translate_status"],
            config.params["cuda"],
            obj_format.raw_ext,
            1,
            obj_format.model_dump_json(),
        )


class CloudASRTaskHandler(TaskHandler):
    """
    云ASR任务处理器
    """
    def process_tasks(self, task_items: List[str]) -> None:
        """
        处理云ASR任务列表
        """
        srt_orm = ToSrtOrm()
        token_service = ServiceProvider().get_token_service()

        for item in task_items:
            logger.debug(f"处理云ASR任务: {item}")

            # 处理任务并获取格式化后的任务信息
            obj_format = self.process_task(item, WORK_TYPE.CLOUD_ASR)

            # 将文件路径与unid关联起来
            token_service.transfer_task_key(item, obj_format.unid)
            logger.info(f"将文件路径与unid关联: {item} -> {obj_format.unid}")

            # 添加任务到数据库
            self._add_to_database(srt_orm, obj_format)

            logger.debug("云ASR任务添加完成")

    def _add_to_database(self, orm: ToSrtOrm, obj_format: VideoFormatInfo) -> None:
        """
        将云ASR任务添加到数据库
        """
        orm.add_data_to_table(
            obj_format.unid,
            obj_format.raw_name,
            config.params["source_language"],
            config.params["source_language_code"],
            config.params["source_module_status"],
            config.params["source_module_name"],
            config.params["translate_status"],
            config.params["cuda"],
            obj_format.raw_ext,
            1,
            obj_format.model_dump_json(),
        )


class Worker(QObject):
    """
    工作线程，负责将任务添加到队列中
    """
    finished = Signal()
    error = Signal(str)
    queue_ready = Signal()  # 用于通知队列准备就绪

    def __init__(self, queue_copy):
        """
        初始化工作线程
        Args:
            queue_copy: 待处理文件队列的副本
        """
        super().__init__()
        self.queue_copy = queue_copy
        self.data_bridge = data_bridge

        # 初始化任务处理器
        self.task_handlers = {
            WORK_TYPE.ASR: ASRTaskHandler(self.data_bridge),
            WORK_TYPE.TRANS: TransTaskHandler(self.data_bridge),
            WORK_TYPE.ASR_TRANS: ASRTransTaskHandler(self.data_bridge),
            WORK_TYPE.CLOUD_ASR: CloudASRTaskHandler(self.data_bridge)
        }

    def do_work(self, work_type: WORK_TYPE):
        """
        点击开始按钮完成后，将需处理的文件放入队列中
        """
        try:
            logger.debug(f"工作线程开始处理任务: {self.queue_copy}")

            # 获取对应的任务处理器
            handler = self.task_handlers.get(work_type)
            if not handler:
                raise ValueError(f"未知的任务类型: {work_type}")

            # 处理任务
            handler.process_tasks(self.queue_copy)

            # 通知队列准备就绪
            self.queue_ready.emit()
            self.finished.emit()
            logger.debug("工作线程处理完成")

        except Exception as e:
            logger.error(f"工作线程处理失败: {str(e)}")
            self.error.emit(str(e))
            self.finished.emit()

    def stop(self):
        """
        停止工作线程
        """
        set_process("", "stop")
        config.queue_asr = []
        self.finished.emit()


class QueueConsumer(QObject):
    """
    队列消费者，负责处理队列中的任务
    """
    finished = Signal()
    error = Signal(str)

    def process_queue(self):
        """
        处理队列中的任务
        """
        try:
            logger.debug("开始消费队列")
            config.is_consuming = True

            while not config.lin_queue.empty():
                logger.debug("消费线程准备处理下一个任务")
                work_queue.consume_queue()

            config.is_consuming = False
            self.finished.emit()
            logger.debug("队列消费完成")

        except Exception as e:
            logger.error(f"队列消费失败: {str(e)}")
            self.error.emit(str(e))
            config.is_consuming = False
            self.finished.emit()
