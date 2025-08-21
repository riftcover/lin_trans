import os
import tempfile
import threading
import time
from functools import lru_cache
from pathlib import Path

import soundfile as sf  # 用于读取和裁剪音频文件

from app.spacy_utils.load_nlp_model import init_nlp
from app.spacy_utils.sentence_processor import get_sub_index
from nice_ui.configure.signal import data_bridge
from nice_ui.configure import config
from utils import logger
from utils.file_utils import funasr_write_srt_file, Segment, split_sentence
from utils.lazy_loader import LazyLoader

# import whisper
# from faster_whisper import WhisperModel
# from whisper.utils import get_writer, format_timestamp, make_safe

funasr = LazyLoader('funasr')
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


# def capture_whisper_variables(func):
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         captured_data = {"current_segments": None, "content_frames": None, "seek": None, "previous_seek": None, "last_printed_seek": None  # 这个变量来跟踪上次打印的 seek 值
#         }
#
#         def trace(frame, event, arg):
#             """
#             原函数每次执行while seek < content_frames循环时，捕获函数执行过程中的局部变量
#
#             """
#             if event == 'line':
#                 local_vars = frame.f_locals
#                 if 'content_frames' in local_vars:
#                     captured_data['content_frames'] = local_vars['content_frames']
#                 if 'seek' in local_vars:
#                     captured_data['seek'] = local_vars['seek']
#                 if 'previous_seek' in local_vars:
#                     captured_data['previous_seek'] = local_vars['previous_seek']
#                 if 'current_segments' in local_vars:
#                     captured_data['current_segments'] = local_vars['current_segments']
#
#                 # Check if we're at the start of the while loop
#                 if (frame.f_lineno == frame.f_code.co_firstlineno + 66 and  # Adjust this line number,检查行号
#                         captured_data['content_frames'] is not None and captured_data['seek'] is not None and captured_data['previous_seek'] is not None and
#                         captured_data['seek'] != captured_data['last_printed_seek']  # 确保这个 seek 值没有被打印过
#                 ):
#
#                     print("my print===="
#                           f"content_frames: {captured_data['content_frames']}, "
#                           f"seek: {captured_data['seek']}, "
#                           f"previous_seek: {captured_data['previous_seek']}", )
#                     # pbar.update(min(content_frames, seek) - previous_seek)
#                     for segment in captured_data['current_segments']:
#                         start, end, text = segment["start"], segment["end"], segment["text"]
#                         line = f"[{format_timestamp(start)} --> {format_timestamp(end)}] {text}"
#                         print(make_safe(line))
#                     captured_data['last_printed_seek'] = captured_data['seek']
#             return trace
#
#         sys.settrace(trace)
#         try:
#             result = func(*args, **kwargs)
#         finally:
#             sys.settrace(None)
#
#         return result
#
#     return wrapper


# @capture_whisper_variables
# def my_transcribe_function(model, audio, *args, **kwargs):
#     from whisper.transcribe import transcribe
#     return transcribe(model, audio, *args, **kwargs)

@lru_cache(maxsize=None)
def load_model(model_path, model_revision="v2.0.4"):
    from funasr import AutoModel
    return AutoModel(model=model_path, model_revision=model_revision, disable_update=True,disable_pbar=True,disable_log=True)


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
        self.input_file = wav_dirname  #ffz转换后的wav文件路径
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
            time.sleep(1)

    # def whisper_only_to_srt(self, model_name: str = 'small') -> None:
    #     """
    #     如果有CUDA走这个
    #     :param model_name:
    #     :return:
    #     """
    #     logger.debug(f'download_root:{config.root_path}/models')
    #     logger.debug(f'name:{model_name}')
    #     model = whisper.load_model(name=model_name, download_root=f'{config.root_path}/models/whisper')
    #     translate_options = dict(task="translate", **dict(language=self.ln, beam_size=5, best_of=5))
    #
    #     result: dict = my_transcribe_function(model, self.input_file, **translate_options, fp16=False, verbose=True)
    #
    #     # get srt writer for the current directory
    #     writer = get_writer("srt", self.input_dirname)
    #     # add empty dictionary for 'options'
    #     writer(result, f"{self.srt_name}.srt", {})

    # @timeit

    # def whisper_cpp_to_srt(self, model_name: str = 'ggml-medium.en.bin') -> None:
    #     """
    #     如果mac系统或者没有CUDA走这个
    #     :param model_name:
    #     :return:在result文件中输出结果
    #     """
    #
    #     # 定义模型路径和音频文件路径
    #     whisper_name = 'whisper.cpp'
    #     model_rel_path = f'whisper.cpp/models/whisper_cpp/{model_name}'
    #     audio_rel_path = f"data/{self.input_file}"
    #     audio_srt_path = self.input_dirname/self.srt_name
    #     model_path = os.path.join(self.cwd, model_rel_path)
    #     # cwd_path = os.path.join(self.cwd, whisper_name)
    #
    #     # 运行 whisper.cpp 的命令
    #     command = ["./main", "-m", model_path, "-f", self.input_file, "-l", self.ln, "-osrt", "-of", audio_srt_path, "-pp"]
    #     logger.debug("Running command:", " ".join(command))
    #     subprocess.run(command, capture_output=True, text=True,  # cwd=cwd_path
    #                    )
    #
    # def whisper_faster_to_srt(self, model_name: str = 'large-v2', cuda_status: bool = True):
    #     # todo : [0.0 --> 30.0] [30.0 --> 39.92] [40.6 --> 59.64] 1.当前时间戳不精准，2.多句话混在一起
    #     # todo : 3.,就是呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃, 口气词太多了
    #     # 使用faster-whisper进行识别
    #     logger.info(f"Using Faster-Whisper to generate SRT file")
    #     if cuda_status:
    #         model = WhisperModel(model_size_or_path=f'{config.root_path}/models/faster_whisper/{model_name}', device="cuda", local_files_only=True,
    #                              compute_type="float16")
    #     else:
    #         model = WhisperModel(model_size_or_path=f'{config.root_path}/models/faster_whisper/{model_name}', device="cpu", local_files_only=True,
    #                              compute_type="int8")
    #     segments, info = model.transcribe(self.input_file, language=self.ln)
    #
    #     srt_file_path = f"{os.path.splitext(self.input_file)[0]}.srt"
    #     logger.info(f"video_duration: {info.duration}")
    #     logger.info(f"Writing srt file to {srt_file_path}")
    #     for segment in segments:
    #         progress_now = (segment.start / info.duration) * 100
    #         # progress_now 取整
    #         progress_now = round(progress_now, 2)
    #         write_srt_file(segment, srt_file_path)
    #         self.data_bridge.emit_whisper_working(self.unid, progress_now)
    #         logger.info(f"[{segment.start} --> {segment.end}] {segment.text}")
    #
    #     self.data_bridge.emit_whisper_finished(self.unid)

    def funasr_to_srt(self, model_name: str):
        logger.info("使用FunASR开始识别")
        if model_name == 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch':
            self.funasr_zn_model(model_name)

        elif model_name == 'SenseVoiceSmall':
            self.funasr_sense_model(model_name)

        else:
            logger.error(f'模型匹配失败：{model_name}')

    def funasr_zn_model(self, model_name: str):
        from funasr import AutoModel
        logger.info('使用中文模型')

        model_dir = f'{config.funasr_model_path}/{model_name}'
        vad_model_dir = f'{config.funasr_model_path}/speech_fsmn_vad_zh-cn-16k-common-pytorch'
        punc_model_dir = f'{config.funasr_model_path}/punc_ct-transformer_cn-en-common-vocab471067-large'
        spk_model_dir = f'{config.funasr_model_path}/speech_campplus_sv_zh-cn_16k-common'
        model = AutoModel(model=model_dir, model_revision="v2.0.4",
                          vad_model=vad_model_dir, vad_model_revision="v2.0.4",
                          punc_model=punc_model_dir, punc_model_revision="v2.0.4",  # 标点符号
                          spk_model=spk_model_dir, spk_model_revision="v2.0.2",  # 说话人确认
                          vad_kwargs={"max_single_segment_time": 30000},
                          disable_update=True,
                          disable_pbar=True,disable_log=True
                          )
        # 启动进度更新线程
        progress_thread = threading.Thread(target=self._update_progress)
        progress_thread.start()
        try:
            res = model.generate(input=self.input_file, batch_size_s=300,
                                 hotword=None, language=self.ln
                                 )
        finally:
            self._stop_progress_thread = True
            progress_thread.join()  # 模型生成完成，更新进度值到 80
        self.data_bridge.emit_whisper_working(self.unid, 93)
        srt_file_path = f"{os.path.splitext(self.input_file)[0]}.srt"
        segments = res[0]['sentence_info']
        # self.data_bridge.emit_whisper_working(self.unid, 90)
        funasr_write_srt_file(segments, srt_file_path)
        self.data_bridge.emit_whisper_finished(self.unid)

    def funasr_sense_model(self, model_name: str):
        """
        由于直接用model加载音频，显存占用会随着音频长度增加，几何倍增长。
        因此，这里使用VAD模型，将音频分割为多个片段，然后逐个处理。

        Args:
            model_name:

        Returns:

        """
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
        logger.info('使用SenseVoiceSmall')
        model_dir = f'{config.funasr_model_path}/{model_name}'
        # 语音端点检测
        vad_model_dir = f'{config.funasr_model_path}/speech_fsmn_vad_zh-cn-16k-common-pytorch'
        # 标点恢复
        punc_model_dir = f'{config.funasr_model_path}/punc_ct-transformer_cn-en-common-vocab471067-large'

        # 加载模型
        vad_model = load_model(vad_model_dir)
        model = load_model(model_dir)
        # todo： fa-zh模型还是online的
        time_model = load_model("fa-zh")
        punctuation_model = load_model(punc_model_dir)

        # nlp 模型
        nlp = init_nlp()

        # 使用VAD模型处理音频文件
        vad_res = vad_model.generate(
            input=self.input_file,
            cache={},
            max_single_segment_time=30000,  # 最大单个片段时长
        )

        # 从VAD模型的输出中提取每个语音片段的开始和结束时间
        segments = vad_res[0]['value']  # 假设只有一段音频，且其片段信息存储在第一个元素中
        # 加载原始音频数据
        audio_data, sample_rate = sf.read(self.input_file)

        results = []
        self.data_bridge.emit_whisper_working(self.unid, 16)
        total_segments = len(segments)

        for i, segment in enumerate(segments):
            start_time, end_time = segment  # 获取开始和结束时间
            cropped_audio = self.crop_audio(audio_data, start_time, end_time, sample_rate)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, cropped_audio, sample_rate)

                # 输出识别后的纯文本
                res = model.generate(
                    input=temp_file.name,
                    cache={},
                    language=self.ln,
                    batch_size_s=60,
                    merge_vad=True,
                    merge_length_s=10000,
                )

            progress = min(round((i + 1) * 100 / total_segments), 100)
            self.data_bridge.emit_whisper_working(self.unid, progress)

            # 使用自定义函数取消emoji
            text = self.custom_rich_transcription_postprocess(res[0]["text"])
            # 输出字的时间戳
            time_res = time_model.generate(input=(temp_file.name, text), data_type=("sound", "text"))
            logger.info('===time_res===')
            logger.info(time_res)

            # 添加输入验证
            if not text or len(text.strip()) == 0:
                logger.warning("输入文本为空，跳过标点符号处理")
                continue

            # 确保文本转换为正确的类型
            text = text.strip()
            logger.info("===text===")
            logger.info(text)
            try:
                # 添加标点
                punctuation_res = punctuation_model.generate(input=text)
            except RuntimeError as e:
                logger.error(f"标点符号处理失败: {e}")
                continue
            logger.info("===punctuation_res===")
            logger.info(punctuation_res)
            msg = Segment(punctuation_res, time_res)
            punc_list = msg.get_segmented_index()
            logger.info("===punc_list===")
            logger.info(punc_list)
            if not msg.ask_res_len():
                msg.fix_wrong_index()

            # 将长句分割成短句
            words = split_sentence(punctuation_res[0].get('text'))
            split_list =get_sub_index(punc_list,words, nlp)
            # 将字级时间戳拼接成句子

            rrl = msg.create_segmented_transcript(start_time, split_list)
            logger.info("===rrl===")
            logger.info(rrl)
            results.extend(rrl)

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

    # def factory_whisper(self, model_name, system_type: str, cuda_status: bool):
    #     if system_type != 'darwin':
    #         self.whisper_faster_to_srt(model_name, cuda_status)
    #
    #     else:
    #         self.whisper_cpp_to_srt(model_name)


if __name__ == '__main__':
    # SrtWriter('tt1.wav').whisperPt_to_srt()
    # SrtWriter('Ski Pole Use 101.wav', 'en').whisperBin_to_srt()
    output = r'D:\\dcode\lin_trans\\result\\72c63b3fe150d5e95e7b56593d2bb0ac'
    logger.info(output)
    tt1 = r'D:\dcode\lin_trans\result\72c63b3fe150d5e95e7b56593d2bb0ac\33.wav'
    # # output = 'D:/dcode/lin_trans/result/Top 10 Affordable Ski Resorts in Europe/Top 10 Affordable Ski Resorts in Europe.wav'
    # # models = 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch'
    # models = 'speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020'
    models = 'SenseVoiceSmall'
    #
    # # SrtWriter('xxx', output, tt1, 'zh').whisper_faster_to_srt()
    SrtWriter('xxx', tt1, output, 'en').funasr_to_srt(models)
