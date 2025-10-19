import time
from abc import ABC, abstractmethod

from app.cloud_asr.gladia_task_manager import get_gladia_task_manager, TaskStatus
from app.cloud_trans.task_manager import get_trans_task_manager
from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from nice_ui.task import WORK_TYPE
from nice_ui.util.tools import VideoFormatInfo, change_job_format
from orm.queries import ToSrtOrm
from utils import logger


class TaskProcessor(ABC):
    """任务处理器抽象基类，定义了处理任务的接口"""

    @abstractmethod
    def process(self, task: VideoFormatInfo):
        """处理任务的抽象方法"""
        pass

    # ==================== 通用工具方法 ====================

    def _convert_to_wav(self, task: VideoFormatInfo) -> str:
        """
        音视频转 WAV 格式（通用方法）

        Args:
            task: 任务对象

        Returns:
            str: WAV 文件路径
        """
        final_name = task.wav_dirname
        logger.debug(f'准备音视频转wav格式:{final_name}')
        FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)
        return final_name

    def _wait_for_cloud_asr_completion(self, task_manager, task_id: str, raise_on_error: bool = False):
        """
        等待云 ASR 任务完成（通用方法）

        Args:
            task_manager: ASR 任务管理器
            task_id: 任务 ID
            raise_on_error: 失败时是否抛出异常（默认 False，只通知 UI）
        """
        while True:
            # 获取任务状态
            asr_task = task_manager.get_task(task_id)

            # 检查任务是否完成或失败
            if asr_task.status == TaskStatus.COMPLETED:
                logger.info(f'云ASR任务已完成: {task_id}')
                break
            elif asr_task.status == TaskStatus.FAILED:
                logger.error(f'云ASR任务失败: {task_id}, 错误: {asr_task.error}')
                if raise_on_error:
                    raise Exception(f"云ASR任务失败: {asr_task.error}")
                # 通知UI任务失败
                data_bridge.emit_task_error(task_id, asr_task.error or "未知错误")
                break

            # 等待一段时间再检查
            time.sleep(5)


class ASRTaskProcessor(TaskProcessor):
    """ASR任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理ASR任务"""
        logger.debug('处理ASR任务')

        # 音视频转wav格式
        self._convert_to_wav(task)

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
        final_name = self._convert_to_wav(task)

        # 获取任务管理器实例
        task_manager = get_gladia_task_manager()

        # 获取语言代码
        language_code = config.params["source_language_code"]

        # 创建ASR任务
        logger.info(f'创建ASR任务: {final_name}, 语言: {language_code}, task_id: {task.unid}')
        task_manager.create_task(
            task_id=task.unid,
            audio_file=final_name,
            language=language_code
        )

        # 提交任务到Gladia
        logger.info(f'提交ASR任务到云: {task.unid}')
        task_manager.submit_task(task.unid)

        # 是否等待任务完成
        if config.params.get("cloud_asr_wait_for_completion", False):
            logger.info(f'等待云ASR任务完成: {task.unid}')
            self._wait_for_cloud_asr_completion(task_manager, task.unid, raise_on_error=False)
        else:
            logger.debug('云ASR任务已提交，在后台处理中')


class TranslationTaskProcessor(TaskProcessor):
    """翻译任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理翻译任务"""
        logger.debug('处理翻译任务')

        # 获取翻译任务管理器
        trans_task_manager = get_trans_task_manager()

        # 计算并设置翻译代币（基于输入的SRT文件）
        trans_task_manager.calculate_and_set_translation_tokens_from_srt(task.unid, task.raw_name)

        # 执行翻译
        trans_task_manager.execute_translation(
            task=task,
            in_document=task.raw_name,
            out_document=task.srt_dirname,
            feature_key="cloud_trans"
        )


class ASRTransTaskProcessor(TaskProcessor):
    """ASR+翻译组合任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理ASR+翻译任务"""
        logger.debug('处理ASR+翻译任务')

        # 获取翻译任务管理器
        trans_task_manager = get_trans_task_manager()

        # 第一步: ASR 任务
        self._convert_to_wav(task)

        srt_orm = ToSrtOrm()
        db_obj = srt_orm.query_data_by_unid(task.unid)
        srt_worker = SrtWriter(task.unid, task.wav_dirname, task.raw_noextname, db_obj.source_language_code)
        srt_worker.funasr_to_srt(db_obj.source_module_name)

        logger.debug('ASR 任务完成，准备开始翻译任务')

        # 第二步: 翻译任务
        new_task = change_job_format(task)
        srt_name = new_task.srt_dirname

        # 计算并设置翻译算力（基于ASR生成的SRT文件）
        trans_task_manager.calculate_and_set_translation_tokens_from_srt(new_task.unid, srt_name)

        # 添加翻译任务到数据库
        trans_task_manager.add_translation_task_to_database(
            new_task.unid,
            new_task.raw_name,
            new_task.model_dump_json()
        )

        # 执行翻译并扣费
        trans_task_manager.execute_translation(
            task=new_task,
            in_document=srt_name,
            out_document=srt_name,
            feature_key="asr_trans"
        )

        logger.debug('ASR_TRANS 任务全部完成')


class CloudASRTransTaskProcessor(TaskProcessor):
    """云ASR+云翻译任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理云ASR+云翻译任务"""
        logger.debug('处理云ASR+云翻译')

        # 第一步: 云ASR 任务
        final_name = self._convert_to_wav(task)

        # 使用Gladia ASR任务管理器
        asr_task_manager = get_gladia_task_manager()

        # 获取语言代码
        language_code = config.params["source_language_code"]

        # 创建ASR任务（组合任务，禁用自动扣费）
        logger.info(f'创建ASR任务: {final_name}, 语言: {language_code}, task_id: {task.unid}')
        asr_task_manager.create_task(
            task_id=task.unid,
            audio_file=final_name,
            language=language_code,
            auto_billing=False  # 组合任务禁用ASR自动扣费
        )

        # 提交任务到Gladia
        logger.trace(f'提交ASR任务到云: {task.unid}')
        asr_task_manager.submit_task(task.unid)

        # 云ASR+翻译任务必须等待ASR完成，因为翻译需要SRT文件
        logger.info(f'等待云ASR任务完成: {task.unid}')
        self._wait_for_cloud_asr_completion(asr_task_manager, task.unid, raise_on_error=True)

        # 第二步: 翻译任务
        new_task = change_job_format(task)
        srt_name = new_task.srt_dirname

        logger.trace(f'准备云翻译任务:{srt_name}')

        # 获取翻译任务管理器
        trans_task_manager = get_trans_task_manager()

        # 计算并设置翻译算力（基于云ASR生成的SRT文件）
        trans_task_manager.calculate_and_set_translation_tokens_from_srt(new_task.unid, srt_name)

        # 添加翻译任务到数据库
        trans_task_manager.add_translation_task_to_database(
            new_task.unid,
            new_task.raw_name,
            new_task.model_dump_json()
        )

        # 执行翻译并扣费
        trans_task_manager.execute_translation(
            task=new_task,
            in_document=srt_name,
            out_document=srt_name,
            feature_key="cloud_asr_trans"
        )

        logger.debug('CLOUD_ASR_TRANS 任务全部完成')


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
        elif work_type == WORK_TYPE.CLOUD_ASR_TRANS:
            return CloudASRTransTaskProcessor()
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
