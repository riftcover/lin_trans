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
    home_path = '/Users/locodol/Movies/ski/别人的教学视频/big picture/基本姿势'
    input_file = f'{home_path}/How To Use Your Ski Poles - Make Your Skiing Look And Feel Better.webm'
    output_file = '../data/Ski Pole Use 101.wav'

    convert_mp4_to_war(input_file, output_file)
