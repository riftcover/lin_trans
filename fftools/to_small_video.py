from better_ffmpeg_progress import FfmpegProcess


def compress_video(input_file, output_file, bitrate='4000k', audio_bitrate='200k'):
    """
    Compress a video file using VideoToolbox hardware acceleration with progress monitoring.

    Args:
    input_file (str): Path to the input video file.
    output_file (str): Path to the output compressed video file.
    bitrate (str): Target video bitrate, defaults to '4000k'.
    audio_bitrate (str): Target audio bitrate, defaults to '200k'.

    Returns:
    None
    """
    # 构建 FFmpeg 命令
    command = [
        'ffmpeg',
        '-i', input_file,
        '-vcodec', 'h264_videotoolbox',
        '-b:v', bitrate,
        '-b:a', audio_bitrate,
        '-loglevel', 'warning',
        output_file
    ]

    # 创建 FfmpegProcess 实例
    ffmpeg_process = FfmpegProcess(command)

    # 执行 FFmpeg 命令并监控进度
    ffmpeg_process.run()


if __name__ == '__main__':
    video_path = '/Users/locodol/Movies/5月8日/'
    input_video_path = video_path + '5月8日.mp4'
    output_video_path = video_path + 'tt1.mp4'

    compress_video(input_video_path, output_video_path)
