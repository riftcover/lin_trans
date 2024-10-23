from typing import List, Dict, Tuple, Union

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

def funasr_write_txt_file(segments, txt_file_path):
    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(segments)


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


def get_segment_timestamps(result: list, time_threshold: float = 0.2):
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
                current_segment["text"] += char + ' '
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


def get_segmented_index(punc_array: List[int]) -> List[int]:
    """
    根据标点符号数组，获取非1的索引，即带标点的单词的索引
    by the punc_array, get the index of the non-1, which is the index of the word with punctuation
    Args:
        punc_array: 标点符号数组,不为1的是带标点的单词
    Returns:
        标点符合所在单词的索引

    Examples:
        c = [{'key': "today's",
      'text': " Podcast is about modifying ski bootss, and you're going to hear from my guest lou rosenfeld, who owned a successful ski shop in calgary for many years.",
      'punc_array': [1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1,
                     1, 1, 3]}]
    """
    return [i for i, value in enumerate(punc_array) if value != 1]


def create_segmented_transcript(time_stamps: List[Tuple[int, int]], text: str, key_text: str, split_indices: List[int]) -> List[Dict[str, Union[int, str]]]:
    """
    使用SenseVoiceSmall模型时调用。因为SenseVoiceSmall模型输出不带time_stamps,需要额外调用"fa-zh"模型生成
    将字级时间戳，拼接成句子时间戳
    Args:
        time_stamps: "fa-zh"模型输出的字级时间戳,timestamp字段
        text: 标点预测模型输出的文本text字段
        key_text: 标点预测模型输出的文本key字段
        split_indices: 标点预测模型输出的punc_array大于1的列表
    Examples:
        a = "today's podcast is about modifying ski bootss and you're going to hear from my guest lou rosenfeld who owned a successful ski shop in calgary for many years"
        b = [{'key': "today's",
              'text': "podcast is about modifying ski BOOTSS and you're going to hear from my guest lou rosenfeld who owned a successful ski shop in calgary for many years",
              'timestamp': [[270, 830], [830, 910], [910, 990], [990, 2310], [2310, 2690], [2710, 3370], [3870, 3890], [3890, 4090], [4090, 4250], [4250, 4390],
                            [4390, 4610], [4610, 4710], [4710, 4950], [5010, 5090], [5090, 5410], [5410, 5790], [5790, 5970], [5970, 6810], [6810, 6970], [6970, 7470],
                            [7470, 7630], [7630, 7930], [7930, 8029], [8029, 8330], [8330, 8450], [8450, 8690], [8730, 9075]]}]
        c = [{'key': "today's",
              'text': " Podcast is about modifying ski bootss, and you're going to hear from my guest lou rosenfeld, who owned a successful ski shop in calgary for many years.",
              'punc_array': [1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1,
                             1, 1, 3]}]
    Returns:[ {'start': 270, 'end': 3370, 'text': "today's Podcast is about modifying ski bootss,"}]

    """
    sentence_info = []
    begin = 0
    words = split_sentence(text)
    for i, end in enumerate(split_indices):
        current_segment = {
            "start": time_stamps[begin][0],
            "end": time_stamps[end][1],
            "text": ""
        }
        if i == 0:
            # 由于模型输出的文本第一个子在key字段中，所以需要额外处理
            current_segment["text"] = key_text + " "

        for word in words[begin:end + 1]:
            if is_cjk(word[0]):
                current_segment["text"] += word
            else:
                current_segment["text"] += word + ' '
        current_segment["text"] = current_segment["text"].strip()

        sentence_info.append(current_segment)
        begin = end + 1
    return sentence_info
