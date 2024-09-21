from agent.common_agent import translate_document
from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config
from nice_ui.util.tools import VideoFormatInfo
from utils import logger

class LinQueue:
    def lin_queue_put(self, take: VideoFormatInfo):
        """
        将任务放入lin_queue队列中,所有任务都放在这音视频转文本,翻译任务
        在Worker中消费
        """
        config.lin_queue.put(take)

    # 消费mp4_to_war_queue
    @staticmethod
    def consume_queue():

        # 将mp4转为war,在QueueConsumer中消费
        logger.debug('消费线程工作中')
        task: VideoFormatInfo = config.lin_queue.get_nowait()
        logger.debug(f'获取到任务:{task}')
        if task.job_type == 'asr':
            logger.debug('消费srt任务')
            # if task['codec_type'] == 'video':
            # 视频转音频

            final_name = task.wav_dirname
            # 音视频转wav格式
            logger.debug(f'准备音视频转wav格式:{final_name}')
            FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)
            # 处理音频转文本
            srt_worker = SrtWriter(task.unid, task.wav_dirname, task.raw_noextname, config.params['source_language_code'], )
            # srt_worker.factory_whisper(config.params['source_module_name'], config.sys_platform, True)
            srt_worker.funasr_to_srt()  # elif task['codec_type'] == 'audio':  #     final_name = f'{task["output"]}/{task["raw_noextname"]}.wav'  #     FFmpegJobs.convert_mp4_to_war(task['raw_name'], final_name)  #     srt_worker = SrtWriter(task['unid'], task["output"], task["raw_basename"], config.params['source_language_code'], )  #     srt_worker.factory_whisper(config.params['source_module_name'], config.sys_platform, config.params['cuda'])

        elif task.job_type == 'trans':
            logger.debug('消费translate任务')
            agent_type = config.params['translate_type']
            if agent_type in ('qwen', 'kimi'):
                final_name = f'{task.output}/{task.raw_noextname}_译文.srt'
                logger.trace(f'准备翻译任务:{final_name}')
                logger.trace(f'任务参数:{task.unid}, {task.raw_name}, {final_name}, {agent_type}, {config.params["prompt_text"]}, {config.settings["trans_row"]}, {config.settings["trans_sleep"]}')
                translate_document(task.unid, task.raw_name, final_name, agent_type, config.params['prompt_text'], config.settings['trans_row'],
                                   config.settings['trans_sleep'])
