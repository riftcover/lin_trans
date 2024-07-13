import os
from utils.log import Logings

logger = Logings().logger


def write_srt_file(segment, srt_file_path):
    with open(srt_file_path, 'a', encoding='utf-8') as srt_file:
        start_time = segment.start
        end_time = segment.end
        text = segment.text
        srt_file.write(f"{segment.id}\n")
        srt_file.write(f"{format_time(start_time)} --> {format_time(end_time)}\n")
        srt_file.write(f"{text.strip()}\n\n")


def format_time(seconds):
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
