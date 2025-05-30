import os
import unicodedata
import spacy
from typing import List, Tuple

from app.spacy_utils.load_nlp_model import init_nlp
from utils import logger

SPLIT_BY_COMMA_FILE = 'D:\dcode\VideoLingo\output\log\split_by_comma.txt'
SPLIT_BY_CONNECTOR_FILE ='D:\dcode\VideoLingo\output\log\split_by_connector.txt'
def analyze_clause_boundary(doc, token) -> Tuple[bool, bool]:
    """
    Analyze if a token marks a clause boundary using dependency parsing and clause analysis.
    
    Returns:
        Tuple[bool, bool]: (split_before, split_after)
    """
    # Check for subordinating conjunctions
    if token.dep_ == "mark" and token.head.pos_ == "VERB":
        return True, False
        
    # Check for coordinating conjunctions between independent clauses
    if token.dep_ == "cc" and token.head.pos_ == "VERB":
        # Check if this is connecting two main clauses
        for child in token.head.children:
            if child.dep_ == "conj" and child.pos_ == "VERB":
                return True, False
                
    # Check for relative clauses
    if token.dep_ == "relcl" and token.head.pos_ in ["NOUN", "PROPN"]:
        return True, False
        
    # Check for adverbial clauses
    if token.dep_ == "advcl" and token.head.pos_ == "VERB":
        return True, False
        
    # Check for complement clauses
    if token.dep_ == "ccomp" and token.head.pos_ == "VERB":
        return True, False
        
    return False, False

def analyze_semantic_boundary(doc, token) -> Tuple[bool, bool]:
    """
    Analyze semantic boundaries using semantic role labeling and discourse markers.
    """
    # Check for discourse markers
    discourse_markers = {
        "en": ["however", "therefore", "thus", "moreover", "furthermore", "consequently"],
        "zh": ["然而", "因此", "所以", "此外", "而且", "因此"],
        "ja": ["しかし", "したがって", "そのため", "さらに", "また", "よって"],
        "fr": ["cependant", "donc", "ainsi", "de plus", "en outre", "par conséquent"],
        "ru": ["однако", "следовательно", "таким образом", "более того", "кроме того", "в результате"],
        "es": ["sin embargo", "por lo tanto", "así", "además", "por otra parte", "en consecuencia"],
        "de": ["jedoch", "daher", "somit", "außerdem", "ferner", "folglich"],
        "it": ["tuttavia", "quindi", "così", "inoltre", "per di più", "di conseguenza"]
    }
    
    lang = doc.lang_
    if lang in discourse_markers and token.text.lower() in discourse_markers[lang]:
        return True, False
        
    # Check for semantic role changes
    if token.dep_ in ["ROOT", "ccomp", "xcomp"] and token.pos_ == "VERB":
        # Check if this verb starts a new semantic unit
        for child in token.children:
            if child.dep_ in ["nsubj", "nsubjpass"]:
                return True, False
                
    return False, False

def get_split_index_type(doc) -> bool:
    """
    根据文本特征决定使用词下标还是字符下标
    
    Args:
        doc: spaCy文档对象
        
    Returns:
        bool: True表示使用字符下标，False表示使用词下标
    """
    # 1. 检查是否包含CJK字符
    has_cjk = any('CJK' in unicodedata.name(char, '') for char in doc.text)
    if has_cjk:
        return True
        
    # 2. 检查词的平均长度
    if len(doc) > 0:
        avg_word_length = sum(len(token.text) for token in doc) / len(doc)
        # 如果平均词长度接近1，可能是字符语言
        if avg_word_length < 1.5:
            return True
            
    # 3. 默认使用词下标
    return False

def smart_split_by_boundaries(text: str, context_words: int = 5, nlp = None) -> tuple[List[str],List[int]]:
    """
    Split text into sentences using both syntactic and semantic boundaries.
    
    Args:
        text: Input text to split
        context_words: Number of context words to keep around split points
        nlp: spaCy NLP model
        
    Returns:
        Tuple of (List of split sentences, List of split indices)
        - 对于使用词的语言（如英语、德语等），返回词的下标
        - 对于使用字符的语言（如中文、日语等），返回字符的下标

    输入："I really encourage you to try and sense your body more and sense the skis on the snow."
    输出：
        ['I really encourage you to try', 'and sense your body more', 'and sense the skis on the snow']
        [6, 11]

    输入："欢迎参加我的课程。"
    输出：
        ['欢迎参加', '我的课程。']
        [4, 7]  # 字符位置
    """
    doc = nlp(text)
    sentences = [doc.text]
    split_indices = []
    current_offset = 0
    use_char_index = get_split_index_type(doc)  # 根据语言类型决定使用哪种下标

    while True:
        split_occurred = False
        new_sentences = []
        last_start = 0
        
        for sent in sentences:
            doc = nlp(sent)
            start = 0
            for i, token in enumerate(doc):
                syntactic_split_before, syntactic_split_after = analyze_clause_boundary(doc, token)
                semantic_split_before, semantic_split_after = analyze_semantic_boundary(doc, token)

                split_before = syntactic_split_before or semantic_split_before
                split_after = syntactic_split_after or semantic_split_after

                if not (split_before or split_after):
                    continue

                left_words = doc[max(0, token.i - context_words):token.i]
                right_words = doc[token.i+1:min(len(doc), token.i + context_words + 1)]

                left_words = [word.text for word in left_words if not word.is_punct]
                right_words = [word.text for word in right_words if not word.is_punct]

                if len(left_words) >= context_words and len(right_words) >= context_words:
                    if split_before:
                        # 根据语言类型选择使用词下标还是字符下标
                        split_idx = token.idx if use_char_index else token.i
                        new_sentences.append(doc[start:token.i].text.strip())
                        split_indices.append(current_offset + split_idx)
                        start = token.i
                        last_start = token.i
                    elif split_after:
                        # 根据语言类型选择使用词下标还是字符下标
                        split_idx = token.idx + len(token.text) if use_char_index else token.i + 1
                        new_sentences.append(doc[start:token.i + 1].text.strip())
                        split_indices.append(current_offset + split_idx)
                        start = token.i + 1
                        last_start = token.i + 1

                    split_occurred = True
                    break

            if start < len(doc):
                new_sentences.append(doc[start:].text.strip())

        if not split_occurred:
            break

        sentences = new_sentences
        current_offset += last_start
    return sentences, split_indices


def main():
    nlp = init_nlp()
    with open(SPLIT_BY_COMMA_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    # Process each input sentence
    for sentence in sentences:
        split_sentences, split_indices = smart_split_by_boundaries(sentence.strip(), nlp = nlp)
        all_split_sentences.extend(split_sentences)

    with open(SPLIT_BY_CONNECTOR_FILE, "w+", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")
        # do not add a newline at the end of the file
        output_file.seek(output_file.tell() - 1, os.SEEK_SET)
        output_file.truncate()


def example():
    nlp = init_nlp('zh')
    # nlp = init_nlp('en')

    # Example usage
    # text = "I really encourage you to try and sense your body more and sense the skis on the snow"
    text ='呃欢迎VIP来继续参加我的精益产品探索的课程。'
    

    
    # 使用原始函数获取分割后的句子
    split_sentences, b = smart_split_by_boundaries(text, nlp=nlp)
    # for i, sent in enumerate(split_sentences, 1):
    #     print(f"Sentence {i}: {sent}")
    print(split_sentences)
    print(b)

if __name__ == "__main__":
    # main()
    example()
    # main()