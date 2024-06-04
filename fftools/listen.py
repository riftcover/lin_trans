import whisper
from whisper.utils import get_writer

import subprocess
import os



class SrtWriter:

    def __init__(self,input_file):
        self.input_file = input_file
        self.cwd = os.getcwd()
        self.srt_name = input_file.split('.')[-2]
    def whisperPt_to_srt(self,model_name='small'):
        """
        如果有CUDA走这个
        :param model_name:
        :return:
        """
        audio_rel_path = f"data/{self.input_file}"
        os.path.join(self.cwd, audio_rel_path)
        audio_path = os.path.join(self.cwd, audio_rel_path)
        model = whisper.load_model(
            name=model_name,
            download_root='models')
        result = model.transcribe(audio_path)
        writer = get_writer("srt", './result')  # get srt writer for the current directory
        writer(result, f"{self.srt_name}.srt",{})  # add empty dictionary for 'options'





    def whisperBin_to_srt(self, model_name='ggml-medium.en.bin'):
        """
        如果mac系统或者没有CUDA走这个
        :param model_name:
        :return:
        """

        # 定义模型路径和音频文件路径
        whisper_name = 'whisper.cpp'
        model_rel_path = f'whisper.cpp/models/{model_name}'
        audio_rel_path = f"data/{self.input_file}"
        audio_srt_path = os.path.join(self.cwd,f"result/{self.srt_name}")
        print(audio_srt_path)

        model_path = os.path.join(self.cwd, model_rel_path)
        audio_path = os.path.join(self.cwd, audio_rel_path)
        cwd_path = os.path.join(self.cwd, whisper_name)

        # 运行 whisper.cpp 的命令
        result = subprocess.run(
            ["./main", "-m", model_path, "-f", audio_path, "-l", "en","-osrt","-of", audio_srt_path],
            capture_output=True,
            text=True,
            cwd=cwd_path
        )


if __name__ == '__main__':
    # SrtWriter('tt1.wav').whisperPt_to_srt()
    a = SrtWriter('tt1.wav').whisperBin_to_srt()
