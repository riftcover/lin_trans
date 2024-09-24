import copy
import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from nice_ui.configure import config
from utils import logger
from nice_ui.task import WORK_TYPE
from nice_ui.task.queue_worker import LinQueue
from nice_ui.util import tools
from nice_ui.util.tools import set_process, VideoFormatInfo
from orm.queries import ToSrtOrm, ToTranslationOrm

work_queue = LinQueue()


class Worker(QObject):
    finished = Signal()
    error = Signal(str)
    queue_ready = Signal()  # 用于通知队列准备就绪 # 用于通知主线程更新表格
    def __init__(self, queue_copy):
        """
        初始化工作线程
        Args:
            queue_copy: 待处理文件队列的副本
        """
        super().__init__()
        self.queue_copy = queue_copy
        self.data_bridge = config.data_bridge
        logger.debug(f"Worker 初始化，data_bridge id: {id(self.data_bridge)}")
        self.data_bridge.asr_trans_job_asr_finished.connect(self.add_trans_task)
        logger.debug("asr_trans_job_asr_finished 信号已连接到 add_trans_task")


    def do_work(self, work_type: WORK_TYPE):
        """
        点击开始按钮完成后,将需处理的文件放入队列中
        """

        logger.debug(f'do_work()线程开始工作:{self.queue_copy}')
        if work_type == WORK_TYPE.ASR:
            self.asr_work()
        elif work_type == WORK_TYPE.TRANS:
            self.trans_work()
        elif work_type == WORK_TYPE.ASR_TRANS:
            self.asr_trans_work()
        self.queue_ready.emit()
        self.finished.emit()
        logger.debug('do_work() 线程工作完成')

    def asr_work(self):
        srt_orm = ToSrtOrm()
        for it in self.queue_copy:
            logger.debug(f'do_work线线程工作中,处理asr_work任务:{it}')
            # 格式化每个视频信息
            obj_format = self._check_obj(it, WORK_TYPE.ASR)

            # 添加到工作队列
            work_queue.lin_queue_put(obj_format)
            # 添加文件到我的创作页表格中
            self.data_bridge.emit_update_table(obj_format)
            # 添加消息到数据库
            srt_orm.add_data_to_table(obj_format.unid, obj_format.raw_name, config.params['source_language'], config.params['source_module_status'],
                                      config.params['source_module_name'], config.params['translate_status'], config.params['cuda'], obj_format.raw_ext, 1,
                                      obj_format.model_dump_json())
            logger.debug('添加视频消息完成')

    def trans_work(self):
        trans_orm = ToTranslationOrm()
        for it in self.queue_copy:
            logger.debug(f'do_work线线程工作中,处理trans_work任务:{it}')
            # 格式化每个字幕信息
            obj_format = self._check_obj(it, WORK_TYPE.TRANS)
            obj_format.srt_dirname = f'{obj_format.output}/{obj_format.raw_noextname}_译文.srt'  # 原始文件名_译文.srt，用作最终输出文件名
            # 添加到工作队列
            work_queue.lin_queue_put(obj_format)
            # 添加文件到我的创作页表格中
            self.data_bridge.emit_update_table(obj_format)
            # 添加消息到数据库
            trans_orm.add_data_to_table(obj_format.unid, obj_format.raw_name, config.params['source_language'], config.params['target_language'],
                                        config.params['translate_channel'], 2, 1, obj_format.model_dump_json())
            logger.debug('添加翻译消息完成')

    def asr_trans_work(self):
        srt_orm = ToSrtOrm()

        for it in self.queue_copy:
            logger.debug(f'do_work线程工作中,处理asr_trans任务:{it}')

            # 添加ASR任务到工作队列
            obj_format = self._check_obj(it, WORK_TYPE.ASR_TRANS)
            work_queue.lin_queue_put(obj_format)

            # 添加文件到我的创作页表格中
            self.data_bridge.emit_update_table(obj_format)


            # 添加ASR任务到数据库
            srt_orm.add_data_to_table(obj_format.unid, obj_format.raw_name, config.params['source_language'], config.params['source_module_status'],
                                      config.params['source_module_name'], config.params['translate_status'], config.params['cuda'], obj_format.raw_ext, 1,
                                      obj_format.model_dump_json())


            logger.debug('asr_trans任务，添加asr完成')

            # 等待 ASR 任务完成
            # self.data_bridge.asr_trans_job_asr_finished.connect(lambda completed_unid: self.add_trans_task(completed_unid, obj_format, trans_orm))
            self.current_asr_trans_task = obj_format
            logger.debug('添加ASR+翻译任务完成')

    @Slot(str)
    def add_trans_task(self,completed_unid):
        trans_orm = ToTranslationOrm()
        logger.debug(f'asr_trans任务,处理trans任务: {completed_unid}')
        # if hasattr(self, 'current_asr_trans_task') and completed_unid == self.current_asr_trans_task.unid:
        #     # 添加翻译任务到工作队列
        #     trans_task = self.change_job_format(self.current_asr_trans_task)
        #     work_queue.lin_queue_put(trans_task)
        #
        #     # 添加翻译任务到数据库
        #     trans_orm.add_data_to_table(self.current_asr_trans_task.unid, self.current_asr_trans_task.raw_name,
        #                                      config.params['source_language'], config.params['target_language'],
        #                                      config.params['translate_channel'], 1, 1, self.current_asr_trans_task.model_dump_json())
        #
        #     logger.debug(f'已添加翻译任务: {completed_unid}')
    # def add_trans_task(self, completed_unid, obj_format, trans_orm):
        # if completed_unid == obj_format.unid:
        #     # 添加翻译任务到工作队列
        #     logger.debug(f'asr_trans任务,处理trans任务:{obj_format.unid}')
        #     trans_task = self.change_job_format(obj_format)
        #     work_queue.lin_queue_put(trans_task)
        #
        #     # 添加翻译任务到数据库
        #     trans_orm.add_data_to_table(obj_format.unid, obj_format.raw_name, config.params['source_language'], config.params['target_language'],
        #                                 config.params['translate_channel'], 1, 1, obj_format.model_dump_json())
        #     # 断开连接，避免重复添加任务
        #     self.data_bridge.asr_trans_job_asr_finished.disconnect()

    def _check_obj(self, it, job_type: WORK_TYPE) -> Optional[VideoFormatInfo]:
        """
        检查文件是否符合要求,并格式化文件信息
        要求:
        1. 文件名长度不超过250
        2. 文件名中不能包含特殊字
        """
        logger.debug(f"检查target_dir:{config.params['target_dir']}")
        obj_format = tools.format_job_msg(it, config.params['target_dir'], job_type)
        target_path = f"{obj_format.output}/{obj_format.raw_noextname}.mp4"

        if len(target_path) >= 250:
            set_process(config.transobj['chaochu255'] + "\n\n" + it, 'alert')
            self.stop()
            return
        if re.search(r'[\&\+\:\?\|]+', it[2:]):
            set_process(config.transobj['teshufuhao'] + "\n\n" + it, 'alert')
            self.stop()
            return
        return obj_format

    def stop(self):
        set_process("", 'stop')
        # todo: 在翻译任务中,也要清空queue_srt
        config.queue_asr = []
        self.finished.emit()

    @staticmethod
    def change_job_format(asr_task_finished: VideoFormatInfo) -> VideoFormatInfo:
        new_task = copy.deepcopy(asr_task_finished)
        raw_pathlib = Path(asr_task_finished.srt_dirname)
        new_task.raw_name = asr_task_finished.srt_dirname
        new_task.raw_dirname = raw_pathlib.parent.resolve().as_posix()
        new_task.raw_basename = raw_pathlib.name
        new_task.raw_noextname = raw_pathlib.stem
        new_task.raw_ext = raw_pathlib.suffix[1:]
        new_task.job_type = WORK_TYPE.ASR_TRANS
        return new_task


class QueueConsumer(QObject):
    """
    点击开始按钮完成后,开始对队列内消息进行消费
    """
    finished = Signal()
    error = Signal(str)

    def process_queue(self):
        # todo: 添加文件开始后立即点击我的创作页,线程不工作
        logger.debug('通知消费线程')
        config.is_consuming = True
        while not config.lin_queue.empty():
            logger.debug('消费线程开始准备')
            work_queue.consume_queue()
        config.is_consuming = False
        self.finished.emit()
