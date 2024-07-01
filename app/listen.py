import os
import subprocess
from pathlib import Path

import whisper
from whisper.utils import get_writer

from utils.about_time import timeit
from utils.log import Logings
from videotrans.configure import config

logger = Logings().logger


class SrtWriter:

    def __init__(self, input_path: Path, raw_basename:str, ln: str):
        """

        Args:
            input_path: 需要提取文本的音频文件
            ln: 音频文件语言
        """
        self.input_path = input_path
        self.cwd = os.path.dirname(os.getcwd())
        self.srt_name = raw_basename.split('.')[-2]
        self.ln = ln

    def whisper_pt_to_srt(self, model_name: str = 'small') -> None:
        """
        如果有CUDA走这个
        :param model_name:
        :return:
        """

        audio_path = os.path.join(self.input_path, f'{self.srt_name}.wav')  # os.path.join(self.cwd, self.raw_basename)
        logger.info(os.path.isfile(audio_path))
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"The file {audio_path} does not exist.")

        #
        # # todo:添加语言参数
        model: whisper.Whisper = whisper.load_model(name=model_name, download_root=f'{config.root_path}/models')
        translate_options = dict(task="translate", **dict(language=self.ln, beam_size=5, best_of=5))
        result: dict = model.transcribe(audio_path, **translate_options, fp16=False, verbose=False)

        # get srt writer for the current directory
        writer = get_writer("srt", self.input_path)
        # add empty dictionary for 'options'
        writer(result, f"{self.srt_name}.srt", {})

    # @timeit
    def whisper_bin_to_srt(
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
        # cwd_path = os.path.join(self.cwd, whisper_name)

        # 运行 whisper.cpp 的命令
        command = ["./main", "-m", model_path, "-f", audio_path, "-l", self.ln, "-osrt", "-of", audio_srt_path, "-pp"]
        logger.debug("Running command:", " ".join(command))
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            # cwd=cwd_path
        )
    def factory_whisper(self,cuda_status:bool):
        if cuda_status:
            self.whisper_pt_to_srt()
        else:
            self.whisper_bin_to_srt()


if __name__ == '__main__':
    # SrtWriter('tt1.wav').whisperPt_to_srt()
    # SrtWriter('Ski Pole Use 101.wav', 'en').whisperBin_to_srt()
    SrtWriter('tt1.wav', 'en').whisper_pt_to_srt()
