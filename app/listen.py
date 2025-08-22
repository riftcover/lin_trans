import os
import tempfile
import threading
import time
from functools import lru_cache
from pathlib import Path

import soundfile as sf  # 用于读取和裁剪音频文件

from app.spacy_utils.load_nlp_model import init_nlp
from app.spacy_utils.sentence_processor import get_sub_index, split_segments_by_boundaries
from nice_ui.configure.signal import data_bridge
from nice_ui.configure import config
from utils import logger
from utils.file_utils import funasr_write_srt_file, Segment, split_sentence, write_segment_data_file
from utils.lazy_loader import LazyLoader
from app.cloud_asr.aliyun_oss_client import upload_file_for_asr
from app.nlp_api import create_nlp_client

funasr = LazyLoader('funasr')
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


@lru_cache(maxsize=None)
def load_model(model_path, model_revision="v2.0.4"):
    from funasr import AutoModel
    return AutoModel(model=model_path, model_revision=model_revision, disable_update=True, disable_pbar=True, disable_log=True)


class SrtWriter:

    def __init__(self, unid: str, wav_dirname: str, raw_noextname: str, ln: str):
        """

        Args:
            input_dirname: 需要提取文本的音频文件
            ln: 音频文件语言
        """
        self.srt_name = raw_noextname
        logger.info(f'wav_dirname : {wav_dirname}')
        if not Path(wav_dirname).is_file():
            logger.error(f"The file {wav_dirname} does not exist.")
            raise FileNotFoundError(f"The file {wav_dirname} does not exist.")
        self.input_file = wav_dirname  # ffz转换后的wav文件路径
        self.ln = ln
        self.data_bridge = data_bridge
        self.unid = unid
        self._stop_progress_thread = False  # 用于停止进度线程，线程是用来更新funasr的进度条的，是一个假的进度条

    # @log_whisper_progress
    def _update_progress(self):
        progress = 0
        while not self._stop_progress_thread:
            self.data_bridge.emit_whisper_working(self.unid, progress)
            progress += 1
            if progress >= 93:
                break
            time.sleep(3)

    def funasr_to_srt(self, model_name: str):
        logger.info("使用FunASR开始识别")
        if model_name == 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch':
            self.funasr_zn_model(model_name)

        elif model_name == 'SenseVoiceSmall':
            self.funasr_sense_model(model_name)

        else:
            logger.error(f'模型匹配失败：{model_name}')

    def funasr_zn_model(self, model_name: str):
        """
        使用FunASR中文模型进行语音识别，支持本地和线上NLP处理

        流程：
        1. ASR识别生成segments
        2. 生成segment_data文件并上传OSS
        3. 调用线上NLP处理（异步）
        4. 生成本地SRT作为降级方案

        错误处理策略：
        - 线上NLP失败 → 使用本地NLP
        - 本地NLP失败 → 生成基础SRT
        - 基础SRT失败 → 记录错误但不中断流程
        """
        logger.info('使用中文模型')

        try:
            # 1. 初始化ASR模型
            model = self._init_asr_model(model_name)

            # 2. 执行ASR识别
            segments = self._run_asr_recognition(model)

            # 3. 生成segment_data文件并上传OSS（失败不影响主流程）
            segment_data_path = None
            oss_url = None
            try:
                segment_data_path = self._create_segment_data_file(segments)
                oss_url = self._upload_segment_data_to_oss(segment_data_path)
            except Exception as e:
                logger.warning(f"segment_data处理失败，跳过线上NLP: {str(e)}")

            # 4. 提交线上NLP任务（异步，失败不影响主流程）
            try:
                self._submit_online_nlp_task(oss_url)
            except Exception as e:
                logger.warning(f"线上NLP任务提交失败: {str(e)}")

            # 5. 生成本地SRT文件（必须成功，否则用户无法获得结果）
            srt_success = self._generate_local_srt(segments)
            if not srt_success:
                logger.error("所有SRT生成方案都失败，用户将无法获得识别结果")
                # 即使失败也要通知完成，避免UI卡死


        except Exception as e:
            logger.error(f"funasr_zn_model执行过程中发生严重错误: {str(e)}")
            # 即使发生严重错误，也要通知UI完成，避免界面卡死
        finally:
            # 无论如何都要通知完成
            self.data_bridge.emit_whisper_finished(self.unid)

    def _init_asr_model(self, model_name: str):
        """初始化ASR模型"""
        model_dir = f'{config.funasr_model_path}/{model_name}'
        vad_model_dir = f'{config.funasr_model_path}/speech_fsmn_vad_zh-cn-16k-common-pytorch'
        punc_model_dir = f'{config.funasr_model_path}/punc_ct-transformer_cn-en-common-vocab471067-large'
        spk_model_dir = f'{config.funasr_model_path}/speech_campplus_sv_zh-cn_16k-common'

        from funasr import AutoModel
        return AutoModel(
            model=model_dir, model_revision="v2.0.4",
            vad_model=vad_model_dir, vad_model_revision="v2.0.4",
            punc_model=punc_model_dir, punc_model_revision="v2.0.4",
            spk_model=spk_model_dir, spk_model_revision="v2.0.2",
            vad_kwargs={"max_single_segment_time": 30000},
            disable_update=True, disable_pbar=True, disable_log=True
        )

    def _run_asr_recognition(self, model):
        """执行ASR识别"""
        progress_thread = threading.Thread(target=self._update_progress)
        progress_thread.start()

        try:
            res = model.generate(
                input=self.input_file,
                batch_size_s=300,
                hotword=None,
                language=self.ln
            )
            self.data_bridge.emit_whisper_working(self.unid, 93)
            return res[0]['sentence_info']
        finally:
            self._stop_progress_thread = True
            progress_thread.join()

    def _create_segment_data_file(self, segments):
        """创建segment_data文件"""
        segment_data_path = f"{os.path.splitext(self.input_file)[0]}_segment_data.json"
        write_segment_data_file(segments, segment_data_path)
        logger.info(f"已创建segment_data文件: {segment_data_path}")
        return segment_data_path

    def _upload_segment_data_to_oss(self, segment_data_path):
        """上传segment_data文件到OSS"""
        logger.info(f"开始上传segment_data文件: {segment_data_path}")
        try:
            success, oss_url, error = upload_file_for_asr(segment_data_path)
            logger.info(f"upload_file_for_asr返回: success={success}, oss_url={oss_url}, error={error}")

            if success:
                logger.info(f"segment_data文件上传成功: {oss_url}")
                return oss_url
            else:
                logger.error(f"segment_data文件上传失败: {error}")
                return None
        except Exception as e:
            logger.error(f"上传segment_data文件时发生异常: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    def _submit_online_nlp_task(self, oss_url):
        """提交线上NLP任务（异步）"""
        if not oss_url:
            logger.warning("OSS URL为空，跳过线上NLP处理")
            return

        # 在后台线程中处理线上NLP任务
        nlp_thread = threading.Thread(
            target=self._process_online_nlp_async,
            args=(oss_url,),
            daemon=False  # 非守护线程，确保任务能完成
        )

        try:
            nlp_thread.start()
            logger.info("已启动线上NLP异步处理线程")
        except Exception as e:
            logger.error(f"启动NLP异步处理线程失败: {str(e)}")

    def _process_online_nlp_async(self, oss_url):
        """异步处理线上NLP任务"""
        try:
            nlp_client = create_nlp_client()
            if not nlp_client:
                logger.error("无法创建NLP客户端，线上NLP处理失败")
                return

            # 1. 提交任务
            success, task_id, error = nlp_client.submit_nlp_task(oss_url, 'zh')
            if not success:
                logger.error(f"线上NLP任务提交失败: {error}")
                return

            logger.info(f"线上NLP任务提交成功，任务ID: {task_id}")

            # 2. 等待任务完成
            success, srt_url, error = nlp_client.wait_for_completion(task_id)
            if not success:
                logger.error(f"线上NLP任务处理失败: {error}")
                return

            logger.info(f"线上NLP任务完成，SRT文件URL: {srt_url}")

            # 3. 下载并替换本地SRT文件
            local_srt_path = f"{os.path.splitext(self.input_file)[0]}.srt"
            success, error = nlp_client.download_srt_file(srt_url, local_srt_path)
            if success:
                logger.info(f"线上NLP处理完成，已替换本地SRT文件: {local_srt_path}")
                # 可以在这里发送通知给UI，告知用户SRT文件已更新
                self._notify_nlp_completion(local_srt_path)
            else:
                logger.error(f"下载线上NLP结果失败: {error}")

        except Exception as e:
            logger.error(f"线上NLP异步处理时发生异常: {str(e)}")

    def _notify_nlp_completion(self, srt_path):
        """通知NLP处理完成"""
        try:
            # 这里可以通过data_bridge发送通知给UI
            # 告知用户线上NLP处理已完成，SRT文件已更新
            logger.info(f"线上NLP处理完成通知: {srt_path}")
            # 如果需要，可以添加UI通知逻辑
            # self.data_bridge.emit_nlp_completed(self.unid, srt_path)
        except Exception as e:
            logger.warning(f"发送NLP完成通知时发生异常: {str(e)}")

    def _generate_local_srt(self, segments):
        """生成本地SRT文件作为降级方案"""
        srt_file_path = f"{os.path.splitext(self.input_file)[0]}.srt"

        try:
            nlp = init_nlp()
            segments_new = split_segments_by_boundaries(segments, nlp)
            funasr_write_srt_file(segments_new, srt_file_path)
            logger.info(f"本地SRT文件生成成功: {srt_file_path}")
            return True
        except Exception as e:
            logger.error(f"本地NLP处理失败: {str(e)}")
            # 如果本地NLP也失败，生成基础SRT文件（不进行句子分割）
            return self._generate_basic_srt(segments, srt_file_path)

    def _generate_basic_srt(self, segments, srt_file_path):
        """生成基础SRT文件（不进行NLP处理的降级方案）"""
        try:
            # 直接使用原始segments生成SRT，不进行句子分割
            basic_segments = []
            for segment in segments:
                if timestamp := segment.get('timestamp', []):
                    basic_segments.append({
                        'text': segment.get('text', ''),
                        'start': timestamp[0][0] if timestamp[0] else 0,
                        'end': timestamp[-1][1] if timestamp[-1] else 0
                    })

            funasr_write_srt_file(basic_segments, srt_file_path)
            logger.info(f"基础SRT文件生成成功（未进行NLP处理）: {srt_file_path}")
            return True
        except Exception as e:
            logger.error(f"生成基础SRT文件也失败: {str(e)}")
            return False

    def _cleanup_temp_files(self, segment_data_path):
        """清理临时文件"""
        try:
            if segment_data_path and os.path.exists(segment_data_path):
                os.unlink(segment_data_path)
                logger.info(f"已清理临时文件: {segment_data_path}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {str(e)}")

    def funasr_sense_model(self, model_name: str):
        """
        使用SenseVoiceSmall模型进行语音识别，将音频分割为多个片段处理

        Args:
            model_name: 模型名称
        """
        logger.info('使用SenseVoiceSmall')

        # 1. 初始化所有需要的模型
        models = self._init_models(model_name)

        # 2. 使用VAD模型分割音频
        segments = self._split_audio_by_vad(models['vad'])

        # 3. 处理每个音频片段
        results = self._process_audio_segments(segments, models)

        # 4. 生成SRT文件
        self._generate_srt_file(results)

    def _init_models(self, model_name: str) -> dict:
        """初始化所有需要的模型"""
        model_dir = f'{config.funasr_model_path}/{model_name}'
        vad_model_dir = f'{config.funasr_model_path}/speech_fsmn_vad_zh-cn-16k-common-pytorch'
        # 标点恢复
        punc_model_dir = f'{config.funasr_model_path}/punc_ct-transformer_cn-en-common-vocab471067-large'

        return {
            'vad': load_model(vad_model_dir),
            'asr': load_model(model_dir),
            # todo： 目前没有下载到本地：speech_timestamp_prediction-v1-16k-offline
            'time': load_model("fa-zh"),
            'punc': load_model(punc_model_dir),
            'nlp': init_nlp()
        }

    def _split_audio_by_vad(self, vad_model) -> list:
        """使用VAD模型分割音频"""
        vad_res = vad_model.generate(
            input=self.input_file,
            cache={},
            max_single_segment_time=30000,  # 最大单个片段时长
        )
        return vad_res[0]['value']

    def _process_audio_segments(self, segments: list, models: dict) -> list:
        """处理每个音频片段
        Return:
            [{'start': 230, 'end': 1230, 'text': 'When you go out there,'},
            {'start': 1230, 'end': 4590, 'text': 'i really encourage you to try and sense your body more'},
            {'start': 4610, 'end': 6770, 'text': 'and sense the skis on the snow,'}]
        """

        audio_data, sample_rate = sf.read(self.input_file)
        results = []
        total_segments = len(segments)

        for i, segment in enumerate(segments):
            # 1. 裁剪音频片段
            cropped_audio = self.crop_audio(audio_data, segment[0], segment[1], sample_rate)

            # 2. 处理音频片段
            segment_results = self._process_single_segment(
                cropped_audio,
                sample_rate,
                segment[0],
                models
            )
            results.extend(segment_results)

            # 3. 更新进度
            progress = min(round((i + 1) * 100 / total_segments), 100)
            self.data_bridge.emit_whisper_working(self.unid, progress)

        return results

    def _process_single_segment(self, audio_data, sample_rate, start_time, models: dict) -> list:
        """处理单个音频片段"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)

            # 1. 识别文本
            text = self._recognize_text(temp_file.name, models['asr'])
            if not text:
                return []

            # 2. 获取时间戳
            time_res = models['time'].generate(
                input=(temp_file.name, text),
                data_type=("sound", "text")
            )

            # 3. 添加标点
            punctuation_res = self._add_punctuation(text, models['punc'])
            if not punctuation_res:
                return []

            # 4. 分割句子
            return self._split_and_align_sentences(
                punctuation_res,
                time_res,
                start_time,
                models['nlp']
            )

    def _recognize_text(self, audio_file: str, model) -> str:
        """识别音频文件中的文本"""
        res = model.generate(
            input=audio_file,
            cache={},
            language=self.ln,
            batch_size_s=60,
            merge_vad=True,
            merge_length_s=10000,
        )
        return self.custom_rich_transcription_postprocess(res[0]["text"])

    def _add_punctuation(self, text: str, model) -> list:
        """为文本添加标点符号"""
        try:
            return model.generate(input=text)
        except RuntimeError as e:
            logger.error(f"标点符号处理失败: {e}")
            return []

    def _split_and_align_sentences(self, punctuation_res: list, time_res: list, start_time: int, nlp) -> list:
        """分割句子并对齐时间戳,返回按照短句切割的list"""
        msg = Segment(punctuation_res, time_res)
        punc_list = msg.get_segmented_index()

        if not msg.ask_res_len():
            msg.fix_wrong_index()

        words = split_sentence(punctuation_res[0].get('text'))
        split_list = get_sub_index(punc_list, words, nlp)

        return msg.create_segmented_transcript(start_time, split_list)

    def _generate_srt_file(self, results: list):
        """生成SRT文件"""
        srt_file_path = f"{os.path.splitext(self.input_file)[0]}.srt"
        funasr_write_srt_file(results, srt_file_path)
        self.data_bridge.emit_whisper_finished(self.unid)

    @staticmethod
    def crop_audio(audio_data, start_time, end_time, sample_rate):
        start_sample = int(start_time * sample_rate / 1000)  # 转换为样本数
        end_sample = int(end_time * sample_rate / 1000)  # 转换为样本数
        return audio_data[start_sample:end_sample]

    def custom_rich_transcription_postprocess(self, s):
        """
        自定义的后处理函数，取消emoji
        基于FunASR的rich_transcription_postprocess函数修改
        """
        from funasr.utils.postprocess_utils import format_str_v2, lang_dict, emo_set, event_set

        def get_emo(s):
            return s[-1] if s[-1] in emo_set else None

        def get_event(s):
            return s[0] if s[0] in event_set else None

        s = s.replace("<|nospeech|><|Event_UNK|>", "❓")
        for lang in lang_dict:
            s = s.replace(lang, "<|lang|>")
        s_list = [format_str_v2(s_i).strip(" ") for s_i in s.split("<|lang|>")]
        new_s = " " + s_list[0]
        cur_ent_event = get_event(new_s)
        for i in range(1, len(s_list)):
            if len(s_list[i]) == 0:
                continue
            if get_event(s_list[i]) == cur_ent_event and get_event(s_list[i]) != None:
                s_list[i] = s_list[i][1:]
            # else:
            cur_ent_event = get_event(s_list[i])
            if get_emo(s_list[i]) != None and get_emo(s_list[i]) == get_emo(new_s):
                new_s = new_s[:-1]
            new_s += s_list[i].strip().lstrip()
        new_s = new_s.replace("The.", " ")
        for emoji in emo_set.union(event_set):
            new_s = new_s.replace(emoji, " ")
        return new_s.strip()


if __name__ == '__main__':
    # SrtWriter('tt1.wav').whisperPt_to_srt()
    # SrtWriter('Ski Pole Use 101.wav', 'en').whisperBin_to_srt()
    output = r'/Users/locodol/my_own/code/lin_trans/result/72c63b3fe150d5e95e7b56593d2bb0ac'
    logger.info(output)
    tt1 = r'/Users/locodol/Movies/test_zh.mp3'
    # # output = 'D:/dcode/lin_trans/result/Top 10 Affordable Ski Resorts in Europe/Top 10 Affordable Ski Resorts in Europe.wav'
    models = 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch'
    # models = 'SenseVoiceSmall'
    #
    # # SrtWriter('xxx', output, tt1, 'zh').whisper_faster_to_srt()
    SrtWriter('xxx', tt1, output, 'zh').funasr_to_srt(models)
