from typing import List, Tuple
from app.spacy_utils.load_nlp_model import init_nlp
from app.spacy_utils.smart_split import smart_split_by_boundaries


def process_sentence(start_idx: int, end_idx: int, words: List[str], nlp=None) -> List[int]:
    """
    处理单个句子，返回分割后的索引列表
    
    Args:
        start_idx: 句子起始位置
        end_idx: 句子结束位置
        words: 单词列表
        nlp: spaCy NLP模型
        
    Returns:
        List[int]: 分割后的索引列表
    """
    sentence = ' '.join(words[start_idx:end_idx + 1])
    split_sentences, split_indices = smart_split_by_boundaries(sentence, nlp=nlp)
    return split_indices


def set_nlp(text, nlp) -> tuple[List[str],List[int]]:
    """

    Args:
        text: '呃欢迎大家来继续参加我的精益产品探索的课程。'
        nlp:

    Returns:['呃欢迎大家来继续', '参加我的精益产品探索的课程。'] [5]

    """
    split_sentences, split_indices = smart_split_by_boundaries(text=text, nlp=nlp)
    return split_sentences,split_indices


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
    Args:
        current: 当前标点位置
        previous: 前一个标点位置

    Returns:两个标点位置相减，得出句子长度，如果小于5不需要截取。如果大于5则长句变短句

    """
    if previous is None:
        return current >= 5
    return current - previous >= 5


def get_sub_index(punc_index: List[int], words_list: list, nlp) -> list:
    """

    Args:
        punc_index: 标点列表
        words_list: 句子单词列表
        nlp:

    Returns:

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
