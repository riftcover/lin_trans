import time
from abc import ABC, abstractmethod

from services.config_manager import get_chunk_size, get_max_entries, get_sleep_time
from agent.enhanced_common_agent import translate_document
from app.cloud_asr.gladia_task_manager import get_gladia_task_manager, TaskStatus
from app.cloud_trans.task_manager import get_trans_task_manager
from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
from nice_ui.services.service_provider import ServiceProvider
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
            self._wait_for_task_completion(task_manager, task.unid)
        else:
            logger.debug('云ASR任务已提交，在后台处理中')

    def _wait_for_task_completion(self, task_manager, task_id):
        """等待任务完成"""
        while True:
            # 获取任务状态
            asr_task = task_manager.get_task(task_id)

            # 检查任务是否完成或失败
            if asr_task.status == TaskStatus.COMPLETED:
                logger.info(f'云ASR任务已完成: {task_id}')
                break
            elif asr_task.status == TaskStatus.FAILED:
                logger.error(f'云ASR任务失败: {task_id}, 错误: {asr_task.error}')
                # 通知UI任务失败，而不是抛出异常
                from nice_ui.ui.SingalBridge import data_bridge
                data_bridge.emit_task_error(task_id, asr_task.error or "未知错误")
                break

            # 等待一段时间再检查
            time.sleep(5)


class TranslationTaskProcessor(TaskProcessor):
    """翻译任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理翻译任务"""
        logger.debug('处理翻译任务')

        try:
            agent_type = config.params['translate_channel']
            final_name = task.srt_dirname  # 原始文件名_译文.srt
            chunk_size_int = get_chunk_size()
            max_entries_int = get_max_entries()  # 推荐值：8-12
            sleep_time_int = get_sleep_time()  # API调用间隔
            logger.trace(f'准备翻译任务:{final_name}')
            logger.trace(
                f'任务参数:{task.unid}, {task.raw_name}, {final_name}, {agent_type},{chunk_size_int},{max_entries_int},{sleep_time_int},{config.params["target_language"]},{config.params["source_language"]}')

            translate_document(
                unid=task.unid,
                in_document=task.raw_name,
                out_document=final_name,
                agent_name=agent_type,
                chunk_size=chunk_size_int,  # 推荐值：600-800
                max_entries=max_entries_int,  # 推荐值：8-12
                sleep_time=sleep_time_int,  # API调用间隔
                target_language=config.params["target_language"],  # 目标语言
                source_language=config.params["source_language"]  # 源语言
            )

            logger.info('翻译任务执行完成')

            # 翻译成功后扣费并刷新使用记录
            trans_task_manager = get_trans_task_manager()
            billing_success = trans_task_manager.consume_tokens_for_task(task.unid,task.raw_noextname, "cloud_trans")

            if billing_success:
                # 任务完成后刷新使用记录
                trans_task_manager.refresh_usage_records_after_task_completion(task.unid)
            else:
                data_bridge.emit_task_error(task.unid, "翻译完成但扣费失败")
                raise Exception(f"翻译任务扣费失败: {task.unid}")

        except ValueError as e:
            # 检查是否是API密钥缺失的错误
            if "请填写API密钥" in str(e):
                logger.error(f"翻译任务失败 - API密钥缺失: {task.unid}")
                data_bridge.emit_task_error(task.unid, "填写key")
            else:
                logger.error(f"翻译任务失败: {task.unid}, 错误: {e}")
                data_bridge.emit_task_error(task.unid, str(e))
            raise e
        except Exception as e:
            logger.error(f"翻译任务失败: {task.unid}, 错误: {e}")
            data_bridge.emit_task_error(task.unid, str(e))
            raise e




class ASRTransTaskProcessor(TaskProcessor):
    """ASR+翻译组合任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理ASR+翻译任务"""
        logger.debug('处理ASR+翻译任务')

        # 获取翻译任务管理器
        trans_task_manager = get_trans_task_manager()

        # 检查是否需要翻译算力预估
        video_duration = getattr(task, 'duration', 0) or 60  # 默认60秒
        trans_task_manager.setup_translation_tokens_estimate_if_needed(task.unid, video_duration)

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
        srt_name = new_task.srt_dirname

        logger.trace(f'准备翻译任务:{srt_name}')

        # 计算并设置翻译算力（基于ASR生成的SRT文件）
        trans_task_manager.calculate_and_set_translation_tokens_from_srt(new_task.unid, srt_name)

        # 添加翻译任务到数据库
        trans_task_manager.add_translation_task_to_database(
            new_task.unid,
            new_task.raw_name,
            new_task.model_dump_json()
        )
        chunk_size_int = get_chunk_size()
        max_entries_int = get_max_entries()  # 推荐值：8-12
        sleep_time_int = get_sleep_time()  # API调用间隔
        logger.trace(
            f'任务参数:{task.unid}, {srt_name}, {srt_name}, {agent_type},{chunk_size_int},{max_entries_int},{sleep_time_int},{config.params["target_language"]},{config.params["source_language"]}')

        # 执行翻译
        try:
            translate_document(
                unid=task.unid,
                in_document=srt_name,
                out_document=srt_name,
                agent_name=agent_type,
                chunk_size=chunk_size_int,  # 推荐值：600-800
                max_entries=max_entries_int,  # 推荐值：8-12
                sleep_time=sleep_time_int,  # API调用间隔
                target_language=config.params["target_language"],  # 目标语言
                source_language=config.params["source_language"]  # 源语言
            )

            logger.info(f'ASR+翻译任务执行完成，开始扣费流程，任务ID: {new_task.unid}')

            if billing_success := trans_task_manager.consume_tokens_for_task(
                new_task.unid, task.raw_noextname, "asr_trans"
            ):
                # 任务完成后刷新使用记录
                trans_task_manager.refresh_usage_records_after_task_completion(new_task.unid)
            else:
                data_bridge.emit_task_error(new_task.unid, "翻译完成但扣费失败")
                raise Exception(f"ASR+翻译任务扣费失败: {new_task.unid}")

            logger.debug('ASR_TRANS 任务全部完成')
        except ValueError as e:
            # 检查是否是API密钥缺失的错误
            if "请填写API密钥" in str(e):
                logger.error(f"ASR+翻译任务失败 - API密钥缺失: {task.unid}")
                data_bridge.emit_task_error(task.unid, "填写key")
            else:
                logger.error(f"ASR+翻译任务失败: {task.unid}, 错误: {e}")
                data_bridge.emit_task_error(task.unid, str(e))
            raise e
        except Exception as e:
            logger.error(f"ASR+翻译任务失败: {task.unid}, 错误: {e}")
            data_bridge.emit_task_error(task.unid, str(e))
            raise e




class CloudASRTransTaskProcessor(TaskProcessor):
    """云ASR+云翻译任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理云ASR任务"""
        logger.debug('处理云ASR+云翻译')
        # 第一步: ASR 任务

        # 音视频转wav格式
        final_name = task.wav_dirname
        logger.debug(f'准备音视频转wav格式:{final_name}')
        FFmpegJobs.convert_mp4_to_wav(task.raw_name, final_name)

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
        self._wait_for_task_completion(asr_task_manager, task.unid)

        # 第二步: 翻译任务
        new_task = change_job_format(task)

        agent_type = config.params['translate_channel']
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
        chunk_size_int = get_chunk_size()
        max_entries_int = get_max_entries()  # 推荐值：8-12
        sleep_time_int = get_sleep_time()  # API调用间隔
        logger.trace(
            f'任务参数:{task.unid}, {srt_name}, {srt_name}, {agent_type},{chunk_size_int},{max_entries_int},{sleep_time_int},{config.params["target_language"]},{config.params["source_language"]}')

        # 执行翻译
        try:
            translate_document(
                unid=task.unid,
                in_document=srt_name,
                out_document=srt_name,
                agent_name=agent_type,
                chunk_size=chunk_size_int,  # 推荐值：600-800
                max_entries=max_entries_int,  # 推荐值：8-12
                sleep_time=sleep_time_int,  # API调用间隔
                target_language=config.params["target_language"],  # 目标语言
                source_language=config.params["source_language"]  # 源语言
            )

            logger.info(f'云ASR+翻译任务执行完成，开始扣费流程，任务ID: {new_task.unid}')

            if billing_success := trans_task_manager.consume_tokens_for_task(
                new_task.unid, task.raw_noextname, "cloud_asr_trans"
            ):
                # 任务完成后刷新使用记录
                trans_task_manager.refresh_usage_records_after_task_completion(new_task.unid)
            else:
                data_bridge.emit_task_error(task.unid, "翻译完成但扣费失败")
                raise Exception(f"云ASR+翻译任务扣费失败: {new_task.unid}")

            logger.debug('CLOUD_ASR_TRANS 任务全部完成')
        except ValueError as e:
            # 检查是否是API密钥缺失的错误
            if "请填写API密钥" in str(e):
                logger.error(f"ASR+翻译任务失败 - API密钥缺失: {task.unid}")
                data_bridge.emit_task_error(task.unid, "填写key")
            else:
                logger.error(f"ASR+翻译任务失败: {task.unid}, 错误: {e}")
                data_bridge.emit_task_error(task.unid, str(e))
            raise e
        except Exception as e:
            logger.error(f"ASR+翻译任务失败: {task.unid}, 错误: {e}")
            data_bridge.emit_task_error(task.unid, str(e))
            raise e

    def _wait_for_task_completion(self, asr_task_manager, task_id):
        """等待任务完成"""
        while True:
            # 获取任务状态
            asr_task = asr_task_manager.get_task(task_id)

            # 检查任务是否完成或失败
            if asr_task.status == TaskStatus.COMPLETED:
                logger.info(f'云ASR任务已完成: {task_id}')
                break
            elif asr_task.status == TaskStatus.FAILED:
                logger.error(f'云ASR任务失败: {task_id}, 错误: {asr_task.error}')
                raise Exception(f"云ASR任务失败: {asr_task.error}")

            # 等待一段时间再检查
            time.sleep(5)




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
