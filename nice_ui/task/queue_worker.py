from agent.common_agent import translate_document
from app.cloud_asr.task_manager import get_task_manager, ASRTaskStatus
from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
from nice_ui.task import WORK_TYPE
from nice_ui.util.tools import VideoFormatInfo, change_job_format
from orm.queries import ToTranslationOrm, ToSrtOrm
from utils import logger
import os
import time


class LinQueue:
    def lin_queue_put(self, take: VideoFormatInfo):
        """
        将任务放入lin_queue队列中,所有任务都放在这音视频转文本,翻译任务
        在Worker中消费
        """
        config.lin_queue.put(take)

    # 消费mp4_to_war_queue

    @staticmethod
    @logger.catch
    def consume_queue():

        # 将mp4转为war,在QueueConsumer中消费
        logger.debug('消费线程工作中')
        task: VideoFormatInfo = config.lin_queue.get_nowait()
        logger.debug(f'获取到任务:{task}')
        if task.work_type == WORK_TYPE.ASR:
            logger.debug('消费srt任务')
            # if task['codec_type'] == 'video':
            # 视频转音频

            final_name = task.wav_dirname
            # 音视频转wav格式
            logger.debug(f'准备音视频转wav格式:{final_name}')
            FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)
            # 处理音频转文本
            srt_orm = ToSrtOrm()
            db_obj = srt_orm.query_data_by_unid(task.unid)
            logger.trace(f"consume_queue_source_language_code: {config.params['source_language_code']}")
            srt_worker = SrtWriter(task.unid, task.wav_dirname, task.raw_noextname, db_obj.source_language_code)
            # srt_worker.factory_whisper(config.params['source_module_name'], config.sys_platform, True)
            srt_worker.funasr_to_srt(db_obj.source_module_name)  # elif task['codec_type'] == 'audio':  #     final_name = f'{task["output"]}/{task["raw_noextname"]}.wav'  #     FFmpegJobs.convert_mp4_to_war(task['raw_name'], final_name)  #     srt_worker = SrtWriter(task['unid'], task["output"], task["raw_basename"], config.params['source_language_code'], )  #     srt_worker.factory_whisper(config.params['source_module_name'], config.sys_platform, config.params['cuda'])

        elif task.work_type == WORK_TYPE.CLOUD_ASR:
            logger.debug('消费云ASR任务')
            # 音视频转wav格式
            final_name = task.wav_dirname
            logger.debug(f'准备音视频转wav格式:{final_name}')
            FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)

            # 获取任务管理器实例
            task_manager = get_task_manager()

            # 获取语言代码
            language_code = config.params["source_language_code"]

            # 获取任务消费的代币数量
            # 获取代币服务
            token_service = ServiceProvider().get_token_service()
            # 从代币服务中获取代币消费量
            token_amount = token_service.get_task_token_amount(task.unid, 10)
            logger.info(f'从代币服务中获取代币消费量: {token_amount}, 任务ID: {task.unid}')

            # 创建ASR任务
            logger.info(f'创建ASR任务: {final_name}, 语言: {language_code}, task_id: {task.unid}, 代币: {token_amount}')
            task_manager.create_task(
                task_id=task.unid,
                audio_file=final_name,
                language=language_code
            )

            # 提交任务到阿里云
            logger.info(f'提交ASR任务到阿里云: {task.unid}')
            task_manager.submit_task(task.unid)

            if config.params.get(
                "cloud_asr_wait_for_completion", False
            ):
                logger.info(f'等待云ASR任务完成: {task.unid}')

                while True:
                    # 获取任务状态
                    asr_task = task_manager.get_task(task.unid)

                    # 检查任务是否完成或失败
                    if asr_task.status == ASRTaskStatus.COMPLETED:
                        logger.info(f'云ASR任务已完成: {task.unid}')
                        break
                    elif asr_task.status == ASRTaskStatus.FAILED:
                        logger.error(f'云ASR任务失败: {task.unid}, 错误: {asr_task.error}')
                        break

                    # 等待一段时间再检查
                    time.sleep(5)

                # 如果任务完成，可以在这里处理结果
                if asr_task.status == ASRTaskStatus.COMPLETED:
                    logger.info('云ASR任务已结束')
            else:
                logger.debug('云ASR任务已提交，在后台处理中')


        elif task.work_type == WORK_TYPE.TRANS:
            logger.debug('消费translate任务')
            agent_type = config.params['translate_channel']
            final_name = task.srt_dirname  # 原始文件名_译文.srt
            logger.trace(f'准备翻译任务:{final_name}')
            logger.trace(f'任务参数:{task.unid}, {task.raw_name}, {final_name}, {agent_type}, {config.params["prompt_text"]}, {config.settings["trans_row"]}, {config.settings["trans_sleep"]}')
            translate_document(task.unid, task.raw_name, final_name, agent_type, config.params['prompt_text'], config.settings['trans_row'],
                               config.settings['trans_sleep'])
        elif task.work_type == WORK_TYPE.ASR_TRANS:
            logger.debug('消费srt+trans任务')

            # 第一步: ASR 任务
            final_name = task.wav_dirname
            logger.debug(f'准备音视频转wav格式:{final_name}')
            FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)
            srt_orm = ToSrtOrm()
            db_obj = srt_orm.query_data_by_unid(task.unid)
            srt_worker = SrtWriter(task.unid, task.wav_dirname, task.raw_noextname, db_obj.source_language_code)
            srt_worker.funasr_to_srt(db_obj.source_module_name)

            logger.debug('ASR 任务完成，准备开始翻译任务')

            # 第二步: 翻译任务
            new_task = change_job_format(task)

            agent_type = config.params['translate_channel']
            final_name = new_task.srt_dirname
            logger.trace(f'准备翻译任务:{final_name}')

            trans_orm = ToTranslationOrm()
            trans_orm.add_data_to_table(
                new_task.unid,
                new_task.raw_name,
                config.params['source_language'],
                config.params["source_language_code"],
                config.params['target_language'],
                config.params['translate_channel'],
                1,
                1,
                new_task.model_dump_json())
            logger.trace(f'任务参数:{new_task.unid}, {new_task.raw_name}, {final_name}, {agent_type}, {config.params["prompt_text"]}, {config.settings["trans_row"]}, {config.settings["trans_sleep"]}')

            translate_document(new_task.unid, new_task.raw_name, final_name, agent_type, config.params['prompt_text'], config.settings['trans_row'],
                               config.settings['trans_sleep'])

            logger.debug('ASR_TRANS 任务全部完成')
