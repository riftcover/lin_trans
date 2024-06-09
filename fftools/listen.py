import os
import subprocess

import whisper
from whisper.utils import get_writer

from tools.about_time import timeit
from tools.log import Logings

logger = Logings().logger


class SrtWriter:

    def __init__(self, input_file: str, ln: str):
        """

        Args:
            input_file: 需要提取文本的音频文件
            ln: 音频文件语言
        """
        self.input_file = input_file
        self.cwd = os.path.dirname(os.getcwd())
        self.srt_name = input_file.split('.')[-2]
        self.ln = ln

    @timeit
    def whisperPt_to_srt(self, model_name: str = 'small') -> None:
        """
        如果有CUDA走这个
        :param model_name:
        :return:
        """
        audio_rel_path = f"data/{self.input_file}"

        audio_path = os.path.join(self.cwd, audio_rel_path)
        #
        # # todo:添加语言参数
        model: whisper.Whisper = whisper.load_model(name=model_name, download_root=f'{self.cwd}/models')
        translate_options = dict(task="translate", **dict(language=self.ln, beam_size=5, best_of=5))
        result: dict = model.transcribe(audio_path, **translate_options, fp16=False, verbose=False)

        # get srt writer for the current directory
        writer = get_writer("srt", '../result')
        # add empty dictionary for 'options'
        writer(result, f"{self.srt_name}.srt", {})

    @timeit
    def whisperBin_to_srt(
            self,
            model_name: str = 'ggml-medium.en.bin') -> None:
        """
        如果mac系统或者没有CUDA走这个
        :param model_name:
        :return:在result文件中输出结果
        """

        # 定义模型路径和音频文件路径
        whisper_name = 'whisper.cpp'
        model_rel_path = f'whisper.cpp/models/{model_name}'
        audio_rel_path = f"data/{self.input_file}"
        audio_srt_path = os.path.join(self.cwd, f"result/{self.srt_name}")
        model_path = os.path.join(self.cwd, model_rel_path)
        audio_path = os.path.join(self.cwd, audio_rel_path)
        cwd_path = os.path.join(self.cwd, whisper_name)

        # 运行 whisper.cpp 的命令
        command = ["./main", "-m", model_path, "-f", audio_path, "-l", self.ln, "-osrt", "-of", audio_srt_path, "-pp"]
        logger.debug("Running command:", " ".join(command))
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=cwd_path
        )


if __name__ == '__main__':
    # SrtWriter('tt1.wav').whisperPt_to_srt()
    a = SrtWriter('Ski Pole Use 101.wav', 'en').whisperBin_to_srt()
    # a = SrtWriter('lfasr_涉政.wav', 'en').whisperPt_to_srt()
