from nice_ui.configure import config


def language_code(language_name:str) -> str:
    for k,v in config.langlist.items():
        if v == language_name:
            return k

if __name__ == '__main__':
    print(language_code('英语'))