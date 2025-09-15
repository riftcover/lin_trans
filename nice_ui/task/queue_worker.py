import os
import time
from abc import ABC, abstractmethod

from agent.srt_translator_adapter import SRTTranslatorAdapter
from services.config_manager import get_chunk_size, get_max_entries, get_sleep_time
from agent.enhanced_common_agent import translate_document
from app.cloud_asr.task_manager import get_task_manager, ASRTaskStatus
from app.cloud_trans.task_manager import TransTaskManager
from app.listen import SrtWriter
from app.video_tools import FFmpegJobs
from nice_ui.configure import config
from nice_ui.configure.signal import data_bridge
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
            billing_success = TransTaskManager().consume_tokens_for_task(task.unid)

            if billing_success:
                logger.info(f'✅ 翻译任务完成并扣费成功 - 任务ID: {task.unid}')
                # 任务完成后刷新使用记录
                self._refresh_usage_records_after_task_completion(task.unid)
            else:
                logger.error(f'❌ 翻译任务扣费失败 - 任务ID: {task.unid}')
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

    def _refresh_usage_records_after_task_completion(self, task_id: str) -> None:
        """任务完成后刷新使用记录"""
        try:
            from nice_ui.services.service_provider import ServiceProvider

            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            # 更新余额
            if balance := token_service.get_user_balance():
                logger.info(f"翻译任务完成后更新用户余额: {balance}")
                data_bridge.emit_update_balance(balance)

            # 更新历史记录
            if transactions := token_service.get_user_history():
                logger.info(f"翻译任务完成后更新用户历史记录，记录数: {len(transactions)}")
                data_bridge.emit_update_history(transactions)

        except Exception as e:
            logger.error(f"翻译任务完成后刷新使用记录失败: {task_id}, 错误: {e}")


class ASRTransTaskProcessor(TaskProcessor):
    """ASR+翻译组合任务处理器"""

    def process(self, task: VideoFormatInfo):
        """处理ASR+翻译任务"""
        logger.debug('处理ASR+翻译任务')

        # 检查是否需要翻译算力预估
        self._setup_translation_tokens_estimate_if_needed(task)

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
        self._calculate_and_set_translation_tokens_for_asr_trans(new_task, srt_name)

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

            # 翻译成功后才扣费
            token_service = ServiceProvider().get_token_service()

            # 使用两阶段算力管理获取总算力
            total_tokens = token_service.get_total_task_tokens(new_task.unid)
            logger.info(f'ASR+翻译任务总算力检查 - 算力: {total_tokens}, 任务ID: {new_task.unid}')

            if total_tokens > 0:
                # 尝试统一扣费
                billing_success = token_service.consume_task_tokens(new_task.unid, "asr_trans")

                if billing_success:
                    logger.info(f'✅ ASR+翻译任务完成并扣费成功 - 任务ID: {new_task.unid}')
                    # 任务完成后刷新使用记录
                    self._refresh_usage_records_after_task_completion(new_task.unid)
                else:
                    logger.error(f'❌ ASR+翻译任务扣费失败 - 任务ID: {new_task.unid}')
                    # 翻译成功但扣费失败，这是一个严重问题
                    data_bridge.emit_task_error(new_task.unid, "翻译完成但扣费失败")
                    raise Exception(f"ASR+翻译任务扣费失败: {new_task.unid}")
            else:
                logger.info(f'✅ ASR+翻译任务完成（无需扣费）- 任务ID: {new_task.unid}')

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

    def _setup_translation_tokens_estimate_if_needed(self, task: VideoFormatInfo) -> None:
        """为ASR+翻译任务设置翻译算力预估（如果使用云翻译）"""
        try:
            # 检查翻译引擎是否为云翻译
            translate_engine = config.params.get('translate_channel', '')
            if translate_engine != 'qwen_cloud':
                logger.info(f"非云翻译引擎({translate_engine})，跳过翻译算力预估")
                return

            # 获取视频时长进行翻译算力预估
            token_service = ServiceProvider().get_token_service()

            # 获取视频时长（如果有的话）
            video_duration = getattr(task, 'duration', 0) or 60  # 默认60秒

            # 预估翻译算力（基于视频时长）
            trans_tokens_estimated = token_service.estimate_translation_tokens_by_duration(video_duration)

            # 设置翻译算力预估（ASR算力为0，因为本地ASR不消耗算力）
            token_service.set_task_tokens_estimate(task.unid, 0, trans_tokens_estimated)

            logger.info(f'ASR+翻译任务算力预估 - ASR: 0（本地）, 翻译预估: {trans_tokens_estimated}, 任务ID: {task.unid}')

        except Exception as e:
            logger.error(f'设置ASR+翻译任务算力预估失败: {task.unid}, 错误: {e}')

    def _refresh_usage_records_after_task_completion(self, task_id: str) -> None:
        """任务完成后刷新使用记录"""
        try:
            from nice_ui.services.service_provider import ServiceProvider

            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            # 更新余额
            if balance := token_service.get_user_balance():
                logger.info(f"任务完成后更新用户余额: {balance}")
                data_bridge.emit_update_balance(balance)

            # 更新历史记录
            if transactions := token_service.get_user_history():
                logger.info(f"任务完成后更新用户历史记录，记录数: {len(transactions)}")
                data_bridge.emit_update_history(transactions)

        except Exception as e:
            logger.error(f"任务完成后刷新使用记录失败: {task_id}, 错误: {e}")

    def _calculate_and_set_translation_tokens_for_asr_trans(self, new_task, srt_file_path: str) -> None:
        """为ASR+翻译任务计算并设置翻译算力"""
        try:
            # 检查翻译引擎是否为云翻译
            translate_engine = config.params.get('translate_channel', '')
            if translate_engine != 'qwen_cloud':
                logger.info(f"非云翻译引擎({translate_engine})，跳过算力计算")
                return

            # 检查SRT文件是否存在
            if not os.path.exists(srt_file_path):
                logger.warning(f"SRT文件不存在，无法计算翻译算力: {srt_file_path}")
                # 设置默认翻译算力
                token_service = ServiceProvider().get_token_service()
                token_service.set_translation_tokens_for_task(new_task.unid, 10)
                return

            # 使用SRT适配器解析内容并计算字数
            with open(srt_file_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()

            adapter = SRTTranslatorAdapter()
            entries = adapter.parse_srt_content(srt_content)

            # 计算总字符数
            total_chars = sum(len(entry.text) for entry in entries)

            # 使用TokenService计算翻译算力
            token_service = ServiceProvider().get_token_service()
            trans_tokens = token_service.calculate_trans_tokens(total_chars)

            # 设置实际翻译算力（两阶段算力管理）
            token_service.set_translation_tokens_for_task(new_task.unid, trans_tokens)

            logger.info(f'ASR+翻译任务实际翻译算力计算 - 字符数: {total_chars}, 算力: {trans_tokens}, 任务ID: {new_task.unid}')

        except Exception as e:
            logger.error(f'计算ASR+翻译任务算力失败: {str(e)}')
            # 设置默认翻译算力
            token_service = ServiceProvider().get_token_service()
            token_service.set_task_token_amount(new_task.unid, 10)


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

        # 获取任务管理器实例
        task_manager = get_task_manager()

        # 获取语言代码
        language_code = config.params["source_language_code"]

        # # 获取任务消费的代币数量
        token_service = ServiceProvider().get_token_service()
        token_amount = token_service.get_task_token_amount(task.unid, 10)
        # token_service.set_ast_tokens_for_task(task.unid, token_amount)
        # logger.info(f'从代币服务中获取代币消费量: {token_amount}, 任务ID: {task.unid}')

        # 创建ASR任务
        # logger.info(f'创建ASR任务: {final_name}, 语言: {language_code}, task_id: {task.unid}, 代币: {token_amount}')
        task_manager.create_task(
            task_id=task.unid,
            audio_file=final_name,
            language=language_code
        )

        # 提交任务到阿里云
        logger.info(f'提交ASR任务到阿里云: {task.unid}')
        task_manager.submit_task(task.unid)

        # 云ASR+翻译任务必须等待ASR完成，因为翻译需要SRT文件
        logger.info(f'等待云ASR任务完成: {task.unid}')
        self._wait_for_task_completion(task_manager, task.unid)

        # 第二步: 翻译任务
        new_task = change_job_format(task)

        agent_type = config.params['translate_channel']
        srt_name = new_task.srt_dirname

        logger.trace(f'准备云翻译任务:{srt_name}')

        # 计算并设置翻译算力（基于云ASR生成的SRT文件）
        self._calculate_and_set_translation_tokens_for_cloud_asr_trans(new_task, srt_name)

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

            # 翻译成功后才扣费
            token_service = ServiceProvider().get_token_service()

            # 使用两阶段算力管理获取总算力
            total_tokens = token_service.get_total_task_tokens(new_task.unid)
            logger.info(f'云ASR+翻译任务总算力检查 - 算力: {total_tokens}, 任务ID: {new_task.unid}')

            if total_tokens > 0:
                # 尝试统一扣费
                billing_success = token_service.consume_task_tokens(new_task.unid, "cloud_asr_trans")

                if billing_success:
                    logger.info(f'✅ 云ASR+翻译任务完成并扣费成功 - 任务ID: {new_task.unid}')
                    # 任务完成后刷新使用记录
                    self._refresh_usage_records_after_task_completion(new_task.unid)
                else:
                    logger.error(f'❌ 云ASR+翻译任务扣费失败 - 任务ID: {new_task.unid}')
                    # 翻译成功但扣费失败，这是一个严重问题
                    data_bridge.emit_task_error(new_task.unid, "翻译完成但扣费失败")
                    raise Exception(f"云ASR+翻译任务扣费失败: {new_task.unid}")
            else:
                logger.info(f'✅ 云ASR+翻译任务完成（无需扣费）- 任务ID: {new_task.unid}')

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
                raise Exception(f"云ASR任务失败: {asr_task.error}")

            # 等待一段时间再检查
            time.sleep(5)

    def _calculate_and_set_translation_tokens_for_cloud_asr_trans(self, new_task, srt_file_path: str) -> None:
        """为云ASR+翻译任务计算并设置翻译算力"""
        try:
            # 检查翻译引擎是否为云翻译
            translate_engine = config.params.get('translate_channel', '')
            if translate_engine != 'qwen_cloud':
                logger.info(f"非云翻译引擎({translate_engine})，跳过翻译算力计算")
                return

            # 检查SRT文件是否存在（云ASR完成后应该存在）
            if not os.path.exists(srt_file_path):
                logger.error(f"云ASR完成后SRT文件仍不存在: {srt_file_path}")
                # 设置默认翻译算力
                token_service = ServiceProvider().get_token_service()
                token_service.set_translation_tokens_for_task(new_task.unid, 10)
                return

            # 使用SRT适配器解析内容并计算字数
            with open(srt_file_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()

            adapter = SRTTranslatorAdapter()
            srt_entries = adapter.parse_srt_content(srt_content)

            # 计算总字符数
            total_chars = sum(len(entry.text) for entry in srt_entries)

            # 计算翻译算力
            token_service = ServiceProvider().get_token_service()
            trans_tokens = token_service.calculate_trans_tokens(total_chars)

            # 设置实际翻译算力
            token_service.set_translation_tokens_for_task(new_task.unid, trans_tokens)

            logger.info(f'云ASR+翻译任务实际翻译算力计算 - 字符数: {total_chars}, 算力: {trans_tokens}, 任务ID: {new_task.unid}')

        except Exception as e:
            logger.error(f'计算云ASR+翻译任务翻译算力失败: {new_task.unid}, 错误: {e}')
            # 设置默认翻译算力
            token_service = ServiceProvider().get_token_service()
            token_service.set_translation_tokens_for_task(new_task.unid, 10)

    def _refresh_usage_records_after_task_completion(self, task_id: str) -> None:
        """任务完成后刷新使用记录"""
        try:
            from nice_ui.services.service_provider import ServiceProvider

            # 获取代币服务
            token_service = ServiceProvider().get_token_service()

            # 更新余额
            if balance := token_service.get_user_balance():
                logger.info(f"云ASR+翻译任务完成后更新用户余额: {balance}")
                data_bridge.emit_update_balance(balance)

            # 更新历史记录
            if transactions := token_service.get_user_history():
                logger.info(f"云ASR+翻译任务完成后更新用户历史记录，记录数: {len(transactions)}")
                data_bridge.emit_update_history(transactions)

        except Exception as e:
            logger.error(f"云ASR+翻译任务完成后刷新使用记录失败: {task_id}, 错误: {e}")


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
