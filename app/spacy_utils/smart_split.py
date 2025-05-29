import os

import spacy
from typing import List, Tuple

from app.spacy_utils.load_nlp_model import init_nlp

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

def smart_split_by_boundaries(text: str, context_words: int = 5, nlp = None) -> List[str]:
    """
    Split text into sentences using both syntactic and semantic boundaries.

    Args:
        text: Input text to split
        context_words: Number of context words to keep around split points
        nlp: spaCy NLP model

    Returns:
        List of split sentences
    """
    doc = nlp(text)
    # 标点算一位
    sentences = [doc.text]

    while True:
        split_occurred = False
        new_sentences = []
        sentences_index = []
        sentences_start = 0
        for sent in sentences:
            doc = nlp(sent)
            start = 0
            for i, token in enumerate(doc):
                # Check both syntactic and semantic boundaries
                syntactic_split_before, syntactic_split_after = analyze_clause_boundary(doc, token)
                semantic_split_before, semantic_split_after = analyze_semantic_boundary(doc, token)

                split_before = syntactic_split_before or semantic_split_before
                split_after = syntactic_split_after or semantic_split_after

                if not (split_before or split_after):
                    continue

                # Get context words
                left_words = doc[max(0, token.i - context_words):token.i]
                left_i = max(0, token.i - context_words)
                right_words = doc[token.i+1:min(len(doc), token.i + context_words + 1)]
                right_i = min(len(doc), token.i + context_words + 1)

                left_words = [word.text for word in left_words if not word.is_punct]
                right_words = [word.text for word in right_words if not word.is_punct]

                if len(left_words) >= context_words and len(right_words) >= context_words:
                    if split_before:
                        # 打印整句话的下标
                        sentence_start_index = start
                        sentence_end_index = token.i
                        print(f"[yellow]✂️  Split before '{token.text}' at index {token.i}: Sentence indices [{sentence_start_index}:{sentence_end_index}] - {' '.join(left_words)}| {token.text} {' '.join(right_words)}[/yellow]")
                        new_sentences.append(doc[start:token.i].text.strip())
                        start = token.i
                    elif split_after:
                        # 打印整句话的下标
                        sentence_start_index = start
                        sentence_end_index = token.i + 1
                        print(f"[yellow]✂️  Split after '{token.text}' at index {token.i}: Sentence indices [{sentence_start_index}:{sentence_end_index}] - {' '.join(left_words)} {token.text}| {' '.join(right_words)}[/yellow]")
                        new_sentences.append(doc[start:token.i + 1].text.strip())
                        start = token.i + 1

                    print(start,token.text)
                    split_occurred = True
                    break

                    split_occurred = True
                    break

            if start < len(doc):
                new_sentences.append(doc[start:].text.strip())

        if not split_occurred:
            break

        sentences = new_sentences
        print(sentences)
        print(sentences_index)
    return sentences

def main():
    nlp = init_nlp()
    with open(SPLIT_BY_COMMA_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    # Process each input sentence
    for sentence in sentences:
        split_sentences = smart_split_by_boundaries(sentence.strip(), nlp = nlp)
        all_split_sentences.extend(split_sentences)

    with open(SPLIT_BY_CONNECTOR_FILE, "w+", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")
        # do not add a newline at the end of the file
        output_file.seek(output_file.tell() - 1, os.SEEK_SET)
        output_file.truncate()


def example():
    nlp = init_nlp()

    # Example usage
    text = "I really encourage you to try and sense your body more and sense the skis on the snow. Because that enables you to then switch off the overcritical part of your brain and really start skiing by feel."
    text2 ='Because that enables you to then switch off the overcritical part of your brain and really start skiing by feel.'
    split_sentences = smart_split_by_boundaries(text, nlp=nlp)

    for i, sent in enumerate(split_sentences, 1):
        print(f"Sentence {i}: {sent}")

if __name__ == "__main__":
    # main()
    example()