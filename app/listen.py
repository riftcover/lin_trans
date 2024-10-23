import os
import sys

import time
from pathlib import Path
import threading

# import whisper
# from faster_whisper import WhisperModel
# from whisper.utils import get_writer, format_timestamp, make_safe

from nice_ui.configure import config
from utils.file_utils import funasr_write_srt_file, funasr_write_txt_file, create_segmented_transcript, get_segmented_index
from utils import logger
from utils.lazy_loader import LazyLoader

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
        self.data_bridge = config.data_bridge
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
        logger.info('使用中文模型')
        from funasr import AutoModel

        model_dir = f'{config.funasr_model_path}/{model_name}'
        vad_model_dir = f'{config.funasr_model_path}/speech_fsmn_vad_zh-cn-16k-common-pytorch'
        model = AutoModel(model=model_dir, model_revision="v2.0.4",
                          vad_model=vad_model_dir, vad_model_revision="v2.0.4",
                          punc_model="ct-punc-c", punc_model_revision="v2.0.4",  # 标点符号
                          spk_model="cam++", spk_model_revision="v2.0.2",  # 说话人确认
                          vad_kwargs={"max_single_segment_time": 30000},
                          disable_update=True)
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
        logger.info('使用SenseVoiceSmall')
        from funasr import AutoModel
        from funasr.utils.postprocess_utils import rich_transcription_postprocess

        model_dir = f'{config.funasr_model_path}/{model_name}'
        vad_model_dir = f'{config.funasr_model_path}/speech_fsmn_vad_zh-cn-16k-common-pytorch'
        model = AutoModel(model=model_dir, model_revision="v2.0.4",
                          vad_model=vad_model_dir, vad_model_revision="v2.0.4",
                          vad_kwargs={"max_single_segment_time": 30000},
                          disable_update=True
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
        self.data_bridge.emit_whisper_working(self.unid, 50)

        txt_file_path = f"{os.path.splitext(self.input_file)[0]}.txt"
        text = rich_transcription_postprocess(res[0]['text'])
        funasr_write_txt_file(text, txt_file_path)
        self.data_bridge.emit_whisper_working(self.unid, 70)
        wav_file = f"{os.path.splitext(self.input_file)[0]}.wav"
        time_model = AutoModel(
            model="fa-zh", model_revision="v2.0.4",
            disable_update=True
        )
        # 修改 generate 方法的调用，同时提供音频和文本文件
        time_res = time_model.generate(input=(wav_file, txt_file_path), data_type=("sound", "text"))

        punctuation_model = AutoModel(model="ct-punc", model_revision="v2.0.4")

        punctuation_res = punctuation_model.generate(input=txt_file_path)
        punctuation_info = punctuation_res[0]
        self.data_bridge.emit_whisper_working(self.unid, 90)
        d = get_segmented_index(punctuation_info['punc_array'])
        # 合并结果
        split_result = create_segmented_transcript(time_res[0]['timestamp'], punctuation_info['text'], punctuation_info['key'], d)

        srt_file_path = f"{os.path.splitext(self.input_file)[0]}.srt"
        funasr_write_srt_file(split_result, srt_file_path)
        self.data_bridge.emit_whisper_finished(self.unid)

    # def factory_whisper(self, model_name, system_type: str, cuda_status: bool):
    #     if system_type != 'darwin':
    #         self.whisper_faster_to_srt(model_name, cuda_status)
    #
    #     else:
    #         self.whisper_cpp_to_srt(model_name)


if __name__ == '__main__':
    # SrtWriter('tt1.wav').whisperPt_to_srt()
    # SrtWriter('Ski Pole Use 101.wav', 'en').whisperBin_to_srt()
    output = r'D:\dcode\lin_trans\result\tt1'
    print(1)
    logger.info(output)
    # tt1 = 'D:/dcode/lin_trans/result/tt1/Top 10 Affordable Ski Resorts in Europe/Top 10 Affordable Ski Resorts in Europe.wav'
    # # output = 'D:/dcode/lin_trans/result/Top 10 Affordable Ski Resorts in Europe/Top 10 Affordable Ski Resorts in Europe.wav'
    # # models = 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch'
    # models = 'speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020'
    #
    # # SrtWriter('xxx', output, tt1, 'zh').whisper_faster_to_srt()
    # SrtWriter('xxx', output, tt1, 'zh').funasr_to_srt(models)
