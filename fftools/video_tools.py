from better_ffmpeg_progress import FfmpegProcess
def convert_ts_to_mp4(input_file, output_file):
    # (
    #     ffmpeg
    #     .input(input_file)
    #     .output(output_file)
    #     .run(overwrite_output=True)
    # )
    command =[
        'ffmpeg',
        '-i', input_file,
        '-loglevel', 'warning',
        output_file
    ]
    ffmpeg_process = FfmpegProcess(command)
    # 执行 FFmpeg 命令并监控进度
    ffmpeg_process.run()
def convert_mp4_to_war(input_file, output_file):

    command =[
        'ffmpeg',
        '-i', input_file,
        '-loglevel', 'warning',
        '-ar', '16000',
        '-ac','2',
        # '-c:a','pcm_s16le',
        '-f', 'wav',
        output_file
    ]
    ffmpeg_process = FfmpegProcess(command)
    # 执行 FFmpeg 命令并监控进度
    ffmpeg_process.run()

if __name__ == '__main__':
    # Example usage
    input_file = '../data/tt1.mp4'
    output_file = '../data/tt1.wav'

    convert_mp4_to_war(input_file, output_file)
