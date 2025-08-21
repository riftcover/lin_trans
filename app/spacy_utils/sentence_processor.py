from typing import List
from app.spacy_utils.smart_split import smart_split_by_boundaries
from utils.file_utils import split_sentence


# 处理句子工具文件

def process_sentence(start_idx: int, end_idx: int, words: List[str], nlp=None) -> List[int]:
    """
    处理单个句子，返回分割后的索引列表,英文用
    
    Args:
        start_idx: 句子起始位置
        end_idx: 句子结束位置
        words: 单词列表
        nlp: spaCy NLP模型
        
    Returns:
        List[int]: 分割后的索引列表
        bool: True为中文类字符，False英文类字符
    """
    sentence = ' '.join(words[start_idx:end_idx + 1])
    split_sentences, split_indices = smart_split_by_boundaries(sentence, nlp=nlp)

    return split_indices


def set_nlp(text, nlp) -> tuple[List[str], List[int]]:
    """
    本地中文模型，云模型用
    Args:
        text:完整句子，例如： '呃欢迎大家来继续参加我的精益产品探索的课程。'
        nlp:

    Returns:['呃欢迎大家来继续', '参加我的精益产品探索的课程。'] [5]

    """
    split_sentences, split_indices = smart_split_by_boundaries(text=text, nlp=nlp)
    return split_sentences, split_indices


def update_sub_list(split_indices: List[int], prev_end_idx: int) -> List[int]:
    """
    更新sub_list，处理分割后的索引
    
    Args:
        split_indices: 分割后的索引列表
        prev_end_idx: 前一个句子的结束位置
        
    Returns:
        List[int]: 更新后的索引列表
    """
    if not split_indices:
        return [prev_end_idx]
    return [prev_end_idx + idx for idx in split_indices]


def is_split_needed(current, previous=None) -> bool:
    """
    句子长度大于5，则返回True，用于长句变短句
    Args:c
        current: 当前标点位置
        previous: 前一个标点位置

    Returns:两个标点位置相减，得出句子长度，如果小于5不需要截取。如果大于5则长句变短句

    """
    if previous is None:
        return current >= 5
    return current - previous >= 5


def get_sub_index(punc_index: List[int], words_list: list, nlp) -> list:
    """
    本地英文模型用
    Args:
        punc_index: 标点列表
        words_list: 句子单词列表, get_sub_index返回结果，是完整句子
        nlp:

    Returns:
        bool: True为中文类字符，False英文类字符
    """
    sub_list = []

    # 处理每个句子
    prev_end_idx = -1  # 用于记录前一个句子的结束位置
    for end_idx in punc_index:
        # 处理当前句子
        split_indices = process_sentence(prev_end_idx + 1, end_idx, words_list, nlp)

        # 更新sub_list
        if not split_indices:
            sub_list.append(end_idx)
        elif prev_end_idx == -1:  # 第一个句子
            sub_list.extend(split_indices)
            sub_list.append(end_idx)
        else:
            sub_list.extend(update_sub_list(split_indices, prev_end_idx))
            sub_list.append(end_idx)

        prev_end_idx = end_idx
    return sub_list


def split_segments_by_boundaries(segments, nlp):
    """
    按照自然语言边界分割文本段落，并重新分配时间戳,适用于本地zh模型，云模型
    
    对每个segment中的文本使用NLP模型进行智能分割，如果文本可以分割成多个部分，
    则根据分割结果创建新的segments并重新分配相应的时间戳。
    
    Args:
        segments: 包含文本和时间戳信息的段落列表
        nlp: spaCy NLP模型，用于进行智能文本分割

        例如：segments = [{'text': 'Picture a winter wonderland,', 'timestamp': [
            [
                0,
                478
            ],
            [
                478,
                717
            ],
            [
                717,
                1196
            ],
            [
                1196,
                1913
            ]
        ]
    }]
        
    Returns:
        List: 处理后的新segments列表，每个segment包含text、start、end字段
        形如：[{'text':'aa','start':22,'end':33}]
    """
    segments_new = []
    for segment in segments:
        split_text_list, split_index = set_nlp(segment['text'], nlp)
        timestamp = segment.get('timestamp')
        if len(split_text_list) <= 1:
            segments_new.append({
                'text': split_text_list[0],
                'start': timestamp[0][0],
                'end': timestamp[0][1]
            })
        else:
            split_len = len(split_text_list)

            start = 0
            for i in range(split_len):
                segment_dict = {}
                # 使用split_sentence函数准确计算文本长度
                split_words = split_sentence(split_text_list[i])
                ll = len(split_words)
                end = start + ll - 1
                if i < split_len - 1:
                    segment_dict = {
                        'text': split_text_list[i],
                        'start': timestamp[start][0],
                        'end': timestamp[end][1]
                    }

                else:
                    segment_dict = {
                        'text': split_text_list[i],
                        'start': timestamp[start + 1][0],
                        'end': timestamp[-1][1]
                    }
                start = end

                segments_new.append(segment_dict)

    return segments_new
