import re
from typing import Optional

from PySide6.QtCore import QObject, Signal

from nice_ui.configure import config
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
        super().__init__()
        self.queue_copy = queue_copy
        self.data_bridge = config.data_bridge

    def do_work(self, work_type: WORK_TYPE):
        """
        点击开始按钮完成后,将需处理的文件放入队列中
        """

        config.logger.debug(f'do_work()线程开始工作:{self.queue_copy}')
        if work_type == 'asr':
            self.asr_work()
        elif work_type == 'trans':
            self.trans_work()
        self.queue_ready.emit()
        self.finished.emit()
        config.logger.debug('do_work() 线程工作完成')

    def asr_work(self):
        srt_orm = ToSrtOrm()
        for it in self.queue_copy:
            config.logger.debug(f'do_work()线线程工作中,处理asr_work任务:{it}')
            # 格式化每个视频信息
            obj_format = self._check_obj(it)
            obj_format.job_type = 'asr'
            # 添加到工作队列
            work_queue.lin_queue_put(obj_format)
            # 添加文件到我的创作页表格中
            self.data_bridge.emit_update_table(obj_format,1)
            # 添加消息到数据库
            srt_orm.add_data_to_table(obj_format.unid, obj_format.raw_name, config.params['source_language'], config.params['source_module_status'],
                                      config.params['source_module_name'], config.params['translate_status'], config.params['cuda'], obj_format.raw_ext, 1,
                                      obj_format.model_dump_json())
            config.logger.debug('添加视频消息完成')

    def trans_work(self):
        trans_orm = ToTranslationOrm()
        for it in self.queue_copy:
            config.logger.debug(f'do_work()线线程工作中,处理trans_work任务:{it}')
            # 格式化每个字幕信息
            obj_format = self._check_obj(it)
            obj_format.job_type = 'trans'
            # 添加到工作队列
            work_queue.lin_queue_put(obj_format)
            # 添加文件到我的创作页表格中
            self.data_bridge.emit_update_table(obj_format,1)
            # 添加消息到数据库
            trans_orm.add_data_to_table(obj_format.unid, obj_format.raw_name, config.params['source_language'], config.params['target_language'],
                                        config.params['translate_type'], 2, 1, obj_format.model_dump_json())
            config.logger.debug('添加翻译消息完成')

    def _check_obj(self, it) -> Optional[VideoFormatInfo]:
        obj_format = tools.format_video(it, config.params['target_dir'])
        target_path = f"{obj_format.output}/{obj_format.raw_noextname}.mp4"

        if len(target_path) >= 250:
            # 调用 set_process() 函数，将提示信息 config.transobj['chaochu255'] 和 it 的值拼接在一起，并将提示级别设置为 'alert'。
            # set_process() 函数会在主线程中显示提示信息。
            # self.stop() 函数会在主线程中停止程序运行。
            set_process(config.transobj['chaochu255'] + "\n\n" + it, 'alert')
            self.stop()
            return
        if re.search(r'[\&\+\:\?\|]+', it[2:]):
            set_process(config.transobj['teshufuhao'] + "\n\n" + it, 'alert')
            self.stop()
            return
        config.logger.debug(f'obj_format:{obj_format}')
        return obj_format

    def stop(self):
        set_process("", 'stop')
        # todo: 在翻译任务中,也要清空queue_srt
        config.queue_asr = []
        self.finished.emit()


class QueueConsumer(QObject):
    """
    点击开始按钮完成后,开始对队列内消息进行消费
    """
    finished = Signal()
    error = Signal(str)

    def process_queue(self):
        # todo: 添加文件开始后立即点击我的创作页,线程不工作
        config.logger.debug('通知消费线程')
        config.is_consuming = True
        while not config.lin_queue.empty():
            config.logger.debug('消费线程开始准备')
            work_queue.consume_queue()
        config.is_consuming = False
        self.finished.emit()

if __name__ == '__main__':
    print(111)
