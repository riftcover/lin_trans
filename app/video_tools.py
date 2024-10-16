from pathlib import Path
import platform

from better_ffmpeg_progress import FfmpegProcess

from utils.log import Logings

logger = Logings().logger



class FFmpegJobs:

    @staticmethod
    def convert_ts_to_mp4(input_path: Path, output_path: Path):
        logger.info(f'convert ts to mp4: {input_path} -> {output_path}')
        # (
        #     ffmpeg
        #     .input(input_file)
        #     .output(output_file)
        #     .run(overwrite_output=True)
        # )
        command = ['ffmpeg', '-i', input_path, '-loglevel', 'warning', output_path]
        ffmpeg_process = FfmpegProcess(command)
        # 执行 FFmpeg 命令并监控进度
        ffmpeg_process.run()

    @staticmethod
    def convert_mp4_to_wav(input_path: Path|str, output_path: Path|str):
        logger.info(f'convert mp4 to wav: {input_path} -> {output_path}')
        command = [
            'ffmpeg',
            '-i', input_path,
            '-loglevel', 'warning',
            '-ar', '16000', # 采样率
            '-ac', '2',  # 声道
            '-c:a', 'pcm_s16le',  # 音频格式
            '-f', 'wav', '-y',  # 覆盖输出
            output_path]
        ffmpeg_process = FfmpegProcess(command)
        # 执行 FFmpeg 命令并监控进度
        ffmpeg_process.run()
        logger.info("转码完成")
