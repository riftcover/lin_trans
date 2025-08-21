import time
from abc import ABC, abstractmethod

from agent.common_agent import translate_document
from app.cloud_asr.task_manager import get_task_manager, ASRTaskStatus
from app.cloud_trans.task_manager import TransTaskManager
from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config
from nice_ui.services.service_provider import ServiceProvider
from nice_ui.task import WORK_TYPE
from nice_ui.util.tools import VideoFormatInfo, change_job_format
from orm.queries import ToTranslationOrm, ToSrtOrm
from utils import logger


class TaskProcessor(ABC):
    """任务处理器抽象基类，定义了处理任务的接口"""

    @abstractmethod
    def process(self, task: VideoFormatInfo):
        """处理任务的抽象方法"""
        pass


class ASRTaskProcessor(TaskProcessor):
    """ASR任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理ASR任务"""
        logger.debug('处理ASR任务')

        # 音视频转wav格式
        final_name = task.wav_dirname
        logger.debug(f'准备音视频转wav格式:{final_name}')
        FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)

        # 处理音频转文本
        srt_orm = ToSrtOrm()
        db_obj = srt_orm.query_data_by_unid(task.unid)
        logger.trace(f"source_language_code: {config.params['source_language_code']}")

        # 创建SRT处理器并执行转换
        srt_worker = SrtWriter(task.unid, task.wav_dirname, task.raw_noextname, db_obj.source_language_code)
        srt_worker.funasr_to_srt(db_obj.source_module_name)


class CloudASRTaskProcessor(TaskProcessor):
    """云ASR任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理云ASR任务"""
        logger.debug('处理云ASR任务')

        # 音视频转wav格式
        final_name = task.wav_dirname
        logger.debug(f'准备音视频转wav格式:{final_name}')
        FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)

        # 获取任务管理器实例
        task_manager = get_task_manager()

        # 获取语言代码
        language_code = config.params["source_language_code"]

        # 获取任务消费的代币数量
        token_service = ServiceProvider().get_token_service()
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

        # 是否等待任务完成
        if config.params.get("cloud_asr_wait_for_completion", False):
            logger.info(f'等待云ASR任务完成: {task.unid}')
            self._wait_for_task_completion(task_manager, task.unid)
        else:
            logger.debug('云ASR任务已提交，在后台处理中')

    def _wait_for_task_completion(self, task_manager, task_id):
        """等待任务完成"""
        while True:
            # 获取任务状态
            asr_task = task_manager.get_task(task_id)

            # 检查任务是否完成或失败
            if asr_task.status == ASRTaskStatus.COMPLETED:
                logger.info(f'云ASR任务已完成: {task_id}')
                break
            elif asr_task.status == ASRTaskStatus.FAILED:
                logger.error(f'云ASR任务失败: {task_id}, 错误: {asr_task.error}')
                break

            # 等待一段时间再检查
            time.sleep(5)


class TranslationTaskProcessor(TaskProcessor):
    """翻译任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理翻译任务"""
        logger.debug('处理翻译任务')

        agent_type = config.params['translate_channel']
        final_name = task.srt_dirname  # 原始文件名_译文.srt

        logger.trace(f'准备翻译任务:{final_name}')
        logger.trace(f'任务参数:{task.unid}, {task.raw_name}, {final_name}, {agent_type}, {config.params["prompt_text"]}, {config.settings["trans_row"]}, {config.settings["trans_sleep"]}')

        # 执行翻译
        translate_document(
            task.unid,
            task.raw_name,
            final_name,
            agent_type,
            config.params['prompt_text'],
            config.settings['trans_row'],
            config.settings['trans_sleep']
        )
        TransTaskManager().consume_tokens_for_task(task.unid)


class ASRTransTaskProcessor(TaskProcessor):
    """ASR+翻译组合任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理ASR+翻译任务"""
        logger.debug('处理ASR+翻译任务')

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

        # 添加翻译任务到数据库
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
            new_task.model_dump_json()
        )

        logger.trace(f'任务参数:{new_task.unid}, {new_task.raw_name}, {final_name}, {agent_type}, {config.params["prompt_text"]}, {config.settings["trans_row"]}, {config.settings["trans_sleep"]}')

        # 执行翻译
        translate_document(
            new_task.unid,
            new_task.raw_name,
            final_name,
            agent_type,
            config.params['prompt_text'],
            config.settings['trans_row'],
            config.settings['trans_sleep']
        )

        logger.debug('ASR_TRANS 任务全部完成')


class TaskProcessorFactory:
    """任务处理器工厂，根据任务类型创建对应的处理器"""

    @staticmethod
    def create_processor(work_type: WORK_TYPE) -> TaskProcessor:
        """创建任务处理器"""
        if work_type == WORK_TYPE.ASR:
            return ASRTaskProcessor()
        elif work_type == WORK_TYPE.CLOUD_ASR:
            return CloudASRTaskProcessor()
        elif work_type == WORK_TYPE.TRANS:
            return TranslationTaskProcessor()
        elif work_type == WORK_TYPE.ASR_TRANS:
            return ASRTransTaskProcessor()
        else:
            raise ValueError(f"未知的任务类型: {work_type}")


class LinQueue:
    """队列管理类，负责任务的入队和处理"""

    def lin_queue_put(self, task: VideoFormatInfo):
        """
        将任务放入lin_queue队列中
        所有任务都放在这里：音视频转文本、翻译任务
        """
        config.lin_queue.put(task)

    @staticmethod
    @logger.catch
    def consume_queue():
        """消费队列中的任务"""
        logger.debug('消费线程工作中')

        # 从队列获取任务
        task: VideoFormatInfo = config.lin_queue.get_nowait()
        logger.debug(f'获取到任务:{task}')

        # 使用工厂创建处理器并处理任务
        processor = TaskProcessorFactory.create_processor(task.work_type)
        logger.debug(f'创建处理器: {processor.__class__.__name__}')

        processor.process(task)
        logger.debug('任务处理完成')
