from pathlib import Path

from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config


class LinQueue:
    def to_war_queue_put(self, take):
        config.mp4_to_war_queue.put(take)

    def tts_queue_put(self, take: Path):
        config.tts_queue.put(take)

    def trans_queue_put(self, take: Path):
        config.trans_queue.put(take)

    # 消费mp4_to_war_queue
    def consume_mp4_queue(self):

        # 将mp4转为war
        # try:
        task = config.mp4_to_war_queue.get_nowait()
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
    # except Exception as e:
    #     config.logger.error(f"Error processing task: {e}")
    #     config.mp4_to_war_queue.task_done()
