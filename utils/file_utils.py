from datetime import timedelta
from typing import List, Dict, Union, Any

import unicodedata

from utils.log import Logings

logger = Logings().logger


def format_time(ms: int) -> str:
    """
    将毫秒转换为SRT格式的时间戳

    Args:
        ms: 毫秒时间戳

    Returns            str: SRT格式的时间戳 (HH:MM:SS,mmm)
    """
    seconds, ms = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


def funasr_write_srt_file(segments: List[Dict[str, Any]], srt_file_path: str) -> None:
    """写SRT文件 - 消除了愚蠢的model参数"""

    def _clean_text(text: str) -> str:
        """移除末尾标点符号 - 单一职责"""
        punctuation_marks = {',', '.', '，', '。', '、', '；', ';'}
        return text.strip().rstrip(''.join(punctuation_marks))

    def _normalize_segment(segment: Dict[str, Any]) -> tuple[str, str, str]:
        """标准化segment数据 - 消除数据结构不一致"""
        # 统一字段名映射
        start_key = 'start' if 'start' in segment else 'begin_time'
        end_key = 'end' if 'end' in segment else 'end_time'

        start_time = format_time(segment[start_key])
        end_time = format_time(segment[end_key])
        text = _clean_text(segment['text'])

        return start_time, end_time, text

    with open(srt_file_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(segments, 1):
            start_time, end_time, text = _normalize_segment(segment)
            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")


def funasr_write_txt_file(segments, txt_file_path):
    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(segments)


def write_segment_data_file(segments, segment_data_file_path):
    """
    将 segments 数据写入 segment_data 文件，用于 NLP 任务

    Args:
        segments: FunASR 输出的句子信息列表
        segment_data_file_path: segment_data 文件路径
    """
    import json

    # 确保数据格式适合 NLP 处理
    segment_data = []
    for segment in segments:
        # 提取必要的字段
        data_item = {
            'text': segment.get('text', ''),
            'timestamp': segment.get('timestamp', []),
            'start': segment.get('start'),
            'end': segment.get('end'),
            'spk': segment.get('spk', 0)
        }
        segment_data.append(data_item)

    # 写入 JSON 格式的文件
    with open(segment_data_file_path, "w", encoding="utf-8") as f:
        json.dump(segment_data, f, ensure_ascii=False, indent=2)

    logger.info(f"已写入 segment_data 文件: {segment_data_file_path}, 包含 {len(segment_data)} 个片段")


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


class Segment:
    """
    在使用SenseVoiceSmall模型时调用
    功能：处理时间戳
    """

    def __init__(self, punctuation_res: list, time_res: list):
        """

        Args:
            punctuation_res: 标点模型预测结果
            time_res: 时间模型预测结果
            time_res:
        """
        self.punctuation_info = punctuation_res[0]
        self.time_info = time_res[0]

        self.punc_array = self.punctuation_info['punc_array']
        self.punc_text = split_sentence(self.punctuation_info['text'])
        self.time_text = split_sentence(self.time_info['text'])
        self.time_timestamp = self.time_info['timestamp']

    def get_segmented_index(self) -> List[int]:
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
        return [i for i, value in enumerate(self.punc_array) if value != 1]

    def ask_res_len(self) -> bool:
        """
        判断标点预测结果和时间预测结果长度是否一致
        有些情况下，标点预测结果和时间预测结果长度不一致，时间预测结果会将几个单词合并在一起

        """
        if len(self.punc_array) == len(self.time_timestamp):
            return True
        else:
            logger.error("punc_array length is not equal to time_timestamp length")
            return False

    def fix_wrong_index(self):
        """
        修正标点预测结果和时间预测结果长度不一致的情况
        有些情况下，标点预测结果和时间预测结果长度不一致，时间预测结果会将几个单词合并在一起，导致标点预测结果的索引和时间预测结果的索引不一致。
        该函数通过将标点预测结果的索引和时间预测结果的索引不一致的位置，复制一份合并点的数据，使得标点预测结果和时间预测结果长度一致。
        长度相差多次，就处理几次
        Returns:

        """
        ll = len(self.punc_text)
        turns = len(self.punc_array) - len(self.time_timestamp)
        i = 0
        logger.info(f"fix turns: {turns}")

        for _ in range(turns):
            while i < ll:
                if self.punc_text[i].lower() != self.time_text[i].lower() and self.punc_text[i].lower()[:-1] != self.time_text[i].lower():
                    self.time_text.insert(i, '')  # 添加一组空数据
                    self.time_timestamp.insert(i, self.time_timestamp[i])  # 添加一组i的重复时间
                    logger.error(f"wrong text: {self.punc_text[i - 3:i + 2]}:{self.time_text[i - 3:i + 2]}")
                    i += 1  # 移动到下一个位置
                    break
                i += 1
            if i >= ll:
                break  # 如果已经检查完所有元素，就退出外层循环
            logger.info(f"fix wrong finish")

    def create_segmented_transcript(self, segment_start_time: int, split_index: List[int]) -> List[Dict[str, Union[int, str]]]:
        """
        将字级时间戳，拼接成句子时间戳。
        使用SenseVoiceSmall模型时调用。
        因为SenseVoiceSmall模型输出不带time_stamps,需要额外调用"fa-zh"模型生成
        Args:
            segment_start_time: vad切割音频后，每段的开始时间
            split_index: 标点预测模型输出的punc_array大于1的列表
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
        words = self.punc_text
        for i, end in enumerate(split_index):
            current_segment = {
                "start": self.time_timestamp[begin][0] + segment_start_time,
                "end": self.time_timestamp[end][1] + segment_start_time,
                "text": "",
                "timestamp": []
            }
            # if i == 0:
            #     # 由于模型输出的文本第一个子在key字段中，所以需要额外处理
            #     current_segment["text"] = key_text + " "
            for j, word in enumerate(words[begin:end + 1]):
                # 获取当前字的时间戳索引
                timestamp_index = begin + j
                # 添加字级时间戳到列表中
                current_segment["timestamp"].append([
                    self.time_timestamp[timestamp_index][0] + segment_start_time,
                    self.time_timestamp[timestamp_index][1] + segment_start_time
                ])

                if is_cjk(word[0]):
                    current_segment["text"] += word
                else:
                    current_segment["text"] += word + ' '
            current_segment["text"] = current_segment["text"].strip()


            sentence_info.append(current_segment)
            begin = end + 1
        return sentence_info
