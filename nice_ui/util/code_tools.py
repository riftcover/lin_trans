from nice_ui.configure import config


def language_code(language_name: str) -> str:
    return config.langlist[language_name]


if __name__ == "__main__":
    print(language_code("英语"))
