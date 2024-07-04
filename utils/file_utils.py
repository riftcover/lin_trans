import os


def write_srt_file(segments, srt_file_path):
    with open(srt_file_path, 'w', encoding='utf-8') as srt_file:
        for i, segment in enumerate(segments, 1):
            # 格式化时间
            start_time = segment.start
            end_time = segment.end
            start_hours, start_minutes, start_seconds = int(start_time // 3600), int((start_time % 3600) // 60), start_time % 60
            end_hours, end_minutes, end_seconds = int(end_time // 3600), int((end_time % 3600) // 60), end_time % 60
            start_time_formatted = f"{start_hours:02}:{start_minutes:02}:{start_seconds:06.3f}".replace('.', ',')
            end_time_formatted = f"{end_hours:02}:{end_minutes:02}:{end_seconds:06.3f}".replace('.', ',')

            # 写入SRT文件
            srt_file.write(f"{i}\n")
            srt_file.write(f"{start_time_formatted} --> {end_time_formatted}\n")
            srt_file.write(f"{segment.text}\n\n")

            # 输出每个段的信息
            print(f"[{start_time:.2f}s -> {end_time:.2f}s] {segment.text}")

