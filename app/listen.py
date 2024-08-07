import functools
import os
import subprocess
import sys
from pathlib import Path

import whisper
from faster_whisper import WhisperModel
from whisper.utils import get_writer, format_timestamp, make_safe

from nice_ui.configure import config
from utils.file_utils import write_srt_file
from utils.log import Logings

logger = Logings().logger

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def capture_whisper_variables(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        captured_data = {
            "current_segments": None,
            "content_frames": None,
            "seek": None,
            "previous_seek": None,
            "last_printed_seek": None  # 这个变量来跟踪上次打印的 seek 值
        }

        def trace(frame, event, arg):
            """
            原函数每次执行while seek < content_frames循环时，捕获函数执行过程中的局部变量

            """
            if event == 'line':
                local_vars = frame.f_locals
                if 'content_frames' in local_vars:
                    captured_data['content_frames'] = local_vars['content_frames']
                if 'seek' in local_vars:
                    captured_data['seek'] = local_vars['seek']
                if 'previous_seek' in local_vars:
                    captured_data['previous_seek'] = local_vars['previous_seek']
                if 'current_segments' in local_vars:
                    captured_data['current_segments'] = local_vars['current_segments']

                # Check if we're at the start of the while loop
                if (frame.f_lineno == frame.f_code.co_firstlineno + 66 and  # Adjust this line number,检查行号
                        captured_data['content_frames'] is not None and
                        captured_data['seek'] is not None and
                        captured_data['previous_seek'] is not None and
                        captured_data['seek'] != captured_data['last_printed_seek']  # 确保这个 seek 值没有被打印过
                ):

                    print("my print===="
                          f"content_frames: {captured_data['content_frames']}, "
                          f"seek: {captured_data['seek']}, "
                          f"previous_seek: {captured_data['previous_seek']}",
                          )
                    # pbar.update(min(content_frames, seek) - previous_seek)
                    for segment in captured_data['current_segments']:
                        start, end, text = segment["start"], segment["end"], segment["text"]
                        line = f"[{format_timestamp(start)} --> {format_timestamp(end)}] {text}"
                        print(make_safe(line))
                    captured_data['last_printed_seek'] = captured_data['seek']
            return trace

        sys.settrace(trace)
        try:
            result = func(*args, **kwargs)
        finally:
            sys.settrace(None)

        return result

    return wrapper


@capture_whisper_variables
def my_transcribe_function(model, audio, *args, **kwargs):
    from whisper.transcribe import transcribe
    return transcribe(model, audio, *args, **kwargs)


class SrtWriter:

    def __init__(self, unid: str, input_dirname: Path, raw_basename: str, ln: str):
        """

        Args:
            input_dirname: 需要提取文本的音频文件
            ln: 音频文件语言
        """
        self.srt_name = raw_basename.rsplit('.',1)[0]

        audio_path = os.path.join(input_dirname, f'{self.srt_name}.wav')  # os.path.join(self.cwd, self.raw_basename)
        if not os.path.isfile(audio_path):
            logger.error(f"The file {audio_path} does not exist.")
            raise FileNotFoundError(f"The file {audio_path} does not exist.")
        self.input_dirname = input_dirname  #文件所在目录
        self.input_file = audio_path  #文件名带上全路径
        self.ln = ln
        self.data_bridge = config.data_bridge
        self.unid = unid

    # @log_whisper_progress

    def whisper_only_to_srt(self, model_name: str = 'small') -> None:
        """
        如果有CUDA走这个
        :param model_name:
        :return:
        """
        logger.debug(f'download_root:{config.root_path}/models')
        logger.debug(f'name:{model_name}')
        model = whisper.load_model(name=model_name, download_root=f'{config.root_path}/models/whisper')
        translate_options = dict(task="translate", **dict(language=self.ln, beam_size=5, best_of=5))

        result: dict = my_transcribe_function(model, self.input_file, **translate_options, fp16=False, verbose=True)

        # get srt writer for the current directory
        writer = get_writer("srt", self.input_dirname)
        # add empty dictionary for 'options'
        writer(result, f"{self.srt_name}.srt", {})

    # @timeit

    def whisper_cpp_to_srt(
            self,
            model_name: str = 'ggml-medium.en.bin') -> None:
        """
        如果mac系统或者没有CUDA走这个
        :param model_name:
        :return:在result文件中输出结果
        """

        # 定义模型路径和音频文件路径
        whisper_name = 'whisper.cpp'
        model_rel_path = f'whisper.cpp/models/whisper_cpp/{model_name}'
        audio_rel_path = f"data/{self.input_file}"
        audio_srt_path = os.path.join(self.input_dirname, self.srt_name)
        model_path = os.path.join(self.cwd, model_rel_path)
        audio_path = os.path.join(self.cwd, audio_rel_path)
        # cwd_path = os.path.join(self.cwd, whisper_name)

        # 运行 whisper.cpp 的命令
        command = ["./main", "-m", model_path, "-f", self.input_file, "-l", self.ln, "-osrt", "-of", audio_srt_path,
                   "-pp"]
        logger.debug("Running command:", " ".join(command))
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            # cwd=cwd_path
        )

    def whisper_faster_to_srt(self, model_name: str = 'large-v2', cuda_status: bool = True):
        # todo : [0.0 --> 30.0] [30.0 --> 39.92] [40.6 --> 59.64] 1.当前时间戳不精准，2.多句话混在一起
        # todo : 3.,就是呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃,呃, 口气词太多了
        # 使用faster-whisper进行识别
        logger.info(f"Using Faster-Whisper to generate SRT file")
        if cuda_status:
            model = WhisperModel(model_size_or_path=f'{config.root_path}/models/faster_whisper/{model_name}',
                                 device="cuda", local_files_only=True, compute_type="float16")
        else:
            model = WhisperModel(model_size_or_path=f'{config.root_path}/models/faster_whisper/{model_name}',
                                 device="cpu", local_files_only=True, compute_type="int8")
        segments, info = model.transcribe(self.input_file, language=self.ln)

        srt_file_path = f"{os.path.splitext(self.input_file)[0]}.srt"
        logger.info(f"video_duration: {info.duration}")
        logger.info(f"Writing srt file to {srt_file_path}")
        for segment in segments:
            progress_now = (segment.start / info.duration) * 100
            write_srt_file(segment, srt_file_path)
            self.data_bridge.emit_whisper_working(self.unid, progress_now)
            logger.info(f"[{segment.start} --> {segment.end}] {segment.text}")

        self.data_bridge.emit_whisper_finished(self.unid)


    def factory_whisper(self, model_name, system_type: str, cuda_status: bool):
        if system_type != 'darwin':
            self.whisper_faster_to_srt(model_name, cuda_status)

        else:
            self.whisper_cpp_to_srt(model_name)


if __name__ == '__main__':
    # SrtWriter('tt1.wav').whisperPt_to_srt()
    # SrtWriter('Ski Pole Use 101.wav', 'en').whisperBin_to_srt()
    output = r'D:\dcode\lin_trans\result\85247cda952a062ae51356699ed9c78b'
    raw_basename = '1.如何获取需求.wav'
    # output = 'D:/dcode/lin_trans/result/Top 10 Affordable Ski Resorts in Europe/Top 10 Affordable Ski Resorts in Europe.wav'
    # models = 'D:\dcode\lin_trans\models\small.pt'

    SrtWriter('xxx',output, raw_basename, 'zh').whisper_faster_to_srt()
