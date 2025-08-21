from datetime import timedelta
from typing import List, Dict, Union

import unicodedata

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
        # 定义多语言标点符号
        punctuation_marks = [',', '.', '，', '。', '、', '；', ';']
        
        for i, segment in enumerate(segments, 1):
            start_time = format_time(segment['start'] / 1000)  # Convert milliseconds to seconds
            end_time = format_time(segment['end'] / 1000)  # Convert milliseconds to seconds
            text = segment['text'].strip()
            
            # 处理句子结尾的标点符号
            while text and text[-1] in punctuation_marks:
                text = text[:-1]

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
                "text": ""
            }
            # if i == 0:
            #     # 由于模型输出的文本第一个子在key字段中，所以需要额外处理
            #     current_segment["text"] = key_text + " "
            for word in words[begin:end + 1]:
                if is_cjk(word[0]):
                    current_segment["text"] += word
                else:
                    current_segment["text"] += word + ' '
            current_segment["text"] = current_segment["text"].strip()


            sentence_info.append(current_segment)
            begin = end + 1
        return sentence_info
