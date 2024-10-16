import os
import re

import unicodedata
from datetime import timedelta

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

def funasr_write_srt_file(segments, srt_file_path):
    with open(srt_file_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments, 1):
            start_time = format_time(segment['start'] / 1000)  # Convert milliseconds to seconds
            end_time = format_time(segment['end'] / 1000)  # Convert milliseconds to seconds
            text = segment['text'].strip()
            
            srt_file.write(f"{i}\n")
            srt_file.write(f"{start_time} --> {end_time}\n")
            srt_file.write(f"{text}\n\n")

def funasr_format_time(seconds):
    """将秒数转换为SRT格式的时间字符串"""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def is_cjk(char):
    """检查字符是否是中日韩文字"""
    return 'CJK' in unicodedata.name(char, '')

def split_sentence(sentence):
    words = sentence.split()
    result = []
    for word in words:
        if is_cjk(word[0]):
            # 如果单词包含中日韩字符，则拆分成单个字符
            result.extend(list(word))
        else:
            # 否则保持为单词
            result.append(word)
    return result

def get_segment_timestamps(result:list,time_threshold:float=0.2):
    """

    Args:
        result: 语音识别后的文本
        time_threshold: 将字拼接成句子，判断2个字之间时间间隔，单位是秒

    Returns:

    """
    segments_list = []
    current_segment = {"start": None, "end": None, "text": ""}
    ll = 0
    for item in result:
        text = item['text']
        timestamps = item['timestamp']
        # 将时间戳从毫秒转换为秒
        timestamps = [[start / 1000, end / 1000] for start, end in timestamps]
        word = split_sentence(text)
        for i, ((start, end), char) in enumerate(zip(timestamps, word)):
            if current_segment["start"] is None:
                current_segment["start"] = start

            current_segment["end"] = end
            if is_cjk(char[0]):
                current_segment["text"] += char

            else:
                # 否则添加空格
                current_segment["text"] += char+' '
            ll += 1
            # 检查是否到达句子末尾
            if i < len(timestamps) - 1:
                next_start = timestamps[i + 1][0]
                if (next_start - end) > time_threshold or ll == 10:
                    # 如果下一个词的开始时间距离当前词的结束时间超过阈值，或者当前句子的词数超过10个，则结束当前句子
                    segments_list.append(current_segment)
                    current_segment = {"start": None, "end": None, "text": ""}
                    ll = 0
            else:
                # 处理最后一个字符
                segments_list.append(current_segment)

    if current_segment["text"]:
        segments_list.append(current_segment)

    return segments_list

if __name__ == '__main__':
    a =[{'text': '正是因为存在绝对正义，', 'start': 430, 'end': 2210, 'timestamp': [[430, 670], [670, 810], [810, 1030], [1030, 1130], [1130, 1330], [1330, 1510], [1510, 1670], [1670, 1810], [1810, 1970], [1970, 2210]], 'spk': 0}, {'text': '所以我们接受现实的相对正义，', 'start': 2250, 'end': 4535, 'timestamp': [[2250, 2390], [2390, 2490], [2490, 2570], [2570, 2710], [2710, 2950], [2970, 3210], [3310, 3550], [3570, 3730], [3730, 3830], [3830, 3970], [3970, 4150], [4150, 4270], [4270, 4535]], 'spk': 0}, {'text': '但是不要因为现实的相对正义，', 'start': 5290, 'end': 7490, 'timestamp': [[5290, 5470], [5470, 5610], [5610, 5710], [5710, 5910], [5910, 6070], [6070, 6230], [6230, 6470], [6470, 6650], [6650, 6750], [6750, 6950], [6950, 7130], [7130, 7250], [7250, 7490]], 'spk': 0}, {'text': '我们就认为这个世界没有正义。', 'start': 7490, 'end': 9965, 'timestamp': [[7490, 7590], [7590, 7710], [7710, 7910], [7910, 8070], [8070, 8290], [8290, 8430], [8430, 8550], [8550, 8710], [8710, 8950], [9050, 9290], [9370, 9550], [9550, 9790], [9790, 9965]], 'spk': 0}, {'text': '因为如果当你认为这个世界没有正义，', 'start': 10600, 'end': 12915, 'timestamp': [[10600, 10760], [10760, 10900], [10900, 11120], [11120, 11300], [11300, 11400], [11400, 11580], [11580, 11700], [11700, 11800], [11800, 11920], [11920, 12020], [12020, 12160], [12160, 12320], [12320, 12440], [12440, 12560], [12560, 12740], [12740, 12915]], 'spk': 0}]
    b = funasr_write_srt_file(a, "test.srt")
