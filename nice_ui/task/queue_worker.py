from pathlib import Path

from agent.common_agent import translate_document
from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config
from nice_ui.util.tools import ObjFormat


class LinQueue:
    def lin_queue_put(self, take: ObjFormat):
        """
        将任务放入lin_queue队列中,所有任务都放在这音视频转文本,翻译任务
        在Worker中消费
        """
        config.lin_queue.put(take)

    # def tts_queue_put(self, take: Path):
    #     """
    #     将任务放入tts_queue队列,在Worker中消费
    #     """
    #     config.tts_queue.put(take)
    #
    # def trans_queue_put(self, take:ObjFormat):
    #     """
    #     将任务放入trans_queue队列,在Worker中消费
    #     """
    #     config.trans_queue.put(take)

    # 消费mp4_to_war_queue
    @staticmethod
    def consume_queue():

        # 将mp4转为war,在QueueConsumer中消费
        task = config.lin_queue.get_nowait()
        if task['job_type'] == 'srt':
            if task['codec_type'] == 'video':
                # 视频转音频
                final_name = f'{task["output"]}/{task["raw_noextname"]}.wav'
                FFmpegJobs.convert_mp4_to_war(task['raw_name'], final_name)
                # 处理音频转文本
                srt_worker = SrtWriter(task['unid'], task["output"], task["raw_basename"], config.params['source_language_code'], )
                srt_worker.factory_whisper(config.params['source_module_name'], config.sys_platform, True)
            elif task['codec_type'] == 'audio':
                final_name = f'{task["output"]}/{task["raw_noextname"]}.wav'
                FFmpegJobs.convert_mp4_to_war(task['raw_name'], final_name)
                srt_worker = SrtWriter(task['unid'], task["output"], task["raw_basename"], config.params['source_language_code'], )
                srt_worker.factory_whisper(config.params['source_module_name'], config.sys_platform, config.params['cuda'])

        elif task['job_type'] == 'trans':
            agent_type = config.params['translate_type']
            if agent_type in ('qwen','kimi'):
                final_name = f'{task["output"]}/{task["raw_noextname_译文"]}.srt'
                translate_document(task['unid'],task['raw_name'], final_name, agent_type,config.params['prompt_text'],config.settings['trans_row'],config.settings['trans_sleep'] )
