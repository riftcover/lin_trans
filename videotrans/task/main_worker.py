import copy
import os
import shutil
import time
from PySide6.QtCore import QObject, Signal

from videotrans.configure import config
from videotrans.task.queue_worker import LinQueue
# from videotrans.task.trans_create import TransCreate
from videotrans.util import tools
from videotrans.util.tools import set_process, send_notification
from pathlib import Path
import re

work_queue = LinQueue()


class Worker(QObject):
    finished = Signal()
    error = Signal(str)
    queue_ready = Signal()  # 新信号，用于通知队列准备就绪

    def __init__(self, queue_mp4_copy):
        super().__init__()
        self.queue_mp4_copy = queue_mp4_copy

    def do_work(self):
        """
        点击开始按钮完成后,将需处理的文件放入队列中
        """
        config.logger.debug('线程开始工作')
        for it in self.queue_mp4_copy:
            config.logger.debug('线程工作中')
            # 格式化每个视频信息
            obj_format = tools.format_video(it.replace('\\', '/'), config.params['target_dir'])
            target_dir_mp4 = obj_format['output'] + f"/{obj_format['raw_noextname']}.mp4"

            if len(target_dir_mp4) >= 250:
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
            # 添加到工作队列
            work_queue.to_war_queue_put(obj_format)
            # 添加进度按钮 unid
            set_process(obj_format['unid'], 'add_process', btnkey=obj_format['unid'])
        self.queue_ready.emit()
        self.finished.emit()

    def stop(self):
        set_process("", 'stop')
        config.queue_mp4 = []
        self.finished.emit()


class QueueConsumer(QObject):
    """
    点击开始按钮完成后,开始对队列内消息进行消费
    """
    finished = Signal()
    error = Signal(str)

    def process_queue(self):
        config.logger.debug('消费线程开始工作')
        config.is_consuming = True
        # while not self.queue.empty():
        while not config.mp4_to_war_queue.empty():
            work_queue.consume_mp4_queue()
        config.is_consuming = False
        self.finished.emit()


if __name__ == '__main__':
        Worker().do_work()