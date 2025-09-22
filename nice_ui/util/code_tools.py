from nice_ui.configure import config


def language_code(language_name: str) -> str:
    if language_name == '自动检测':
        return 'auto'
    else:
        return config.langlist[language_name]


if __name__ == "__main__":
    print(language_code("自动检测"))
