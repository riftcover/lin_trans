import spacy


from utils.key_config_utils import load_key
from nice_ui.configure import config


def get_spacy_model(language: str):
    return load_key("spacy_model_map",language)


def init_nlp(ln= None):
    language = None
    if not ln:
        language = config.params.get('source_language_code')
    else:
        language = ln


    model = get_spacy_model(language)
    print(model)

    try:
        nlp = spacy.load(model)
    except :
        from spacy.cli import download
        download(model)
        nlp = spacy.load(model)
    return nlp

# --------------------
# define the intermediate files
# --------------------
SPLIT_BY_COMMA_FILE = "output/log/split_by_comma.txt"
SPLIT_BY_CONNECTOR_FILE = "output/log/split_by_connector.txt"
SPLIT_BY_MARK_FILE = "output/log/split_by_mark.txt"

if __name__ == '__main__':
    init_nlp()
