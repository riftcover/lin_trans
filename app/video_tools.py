from pathlib import Path

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
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            command = [
                'ffmpeg',
                '-i', str(input_path),
                '-loglevel', 'warning',
                '-ar', '16000', # 采样率
                '-ac', '2',  # 声道
                '-c:a', 'pcm_s16le',  # 音频格式
                '-f', 'wav', '-y',  # 覆盖输出
                str(output_path)
            ]
            ffmpeg_process = FfmpegProcess(command)

            # 获取视频总时长
            duration = ffmpeg_process.get_duration()

            def on_progress(progress):
                # 使用logger记录进度，而不是打印到控制台
                logger.debug(f"转换进度: {progress:.2f}%")

            # 执行 FFmpeg 命令并监控进度
            ffmpeg_process.run(on_progress)
            logger.info("转码完成")
            return True
        except Exception as e:
            logger.error(f"转换失败: {str(e)}")
            return False
