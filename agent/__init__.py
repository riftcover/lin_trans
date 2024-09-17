# -*- coding: utf-8 -*-


SRT_NAME = "srt"
# 翻译通道
translate_api_name = {'qwen': '通义千问','google': '谷歌翻译', 'deepl': 'DeepL翻译', 'deeplx': 'DeepL翻译X', 'tencent': '腾讯翻译', 'baidu': '百度翻译' ,
    'zhipu': '智谱', 'chatgpt': 'ChatGPT', 'kimi': 'Kimi', 'openai': 'OpenAI', }
#
LANG_CODE = {
    "zh-cn": [
        "zh-cn",  # google通道
        "chi",  # 字幕嵌入语言
        "zh",  # 百度通道
        "ZH",  # deepl deeplx通道
        "zh",  # 腾讯通道
        "zh",  # OTT通道
        "zh-Hans",# 微软翻译
        "Simplified Chinese" #AI翻译
    ],
    "zh-tw": [
        "zh-tw",
        "chi",
        "cht",
        "ZH",
        "zh-TW",
        "zt",
        "zh-Hant",
        "Traditional Chinese"
    ],
    "en": [
        "en",
        "eng",
        "en",
        "EN",
        "en",
        "en",
        "en",
        "English language"
    ],
    "fr": [
        "fr",
        "fre",
        "fra",
        "FR",
        "fr",
        "fr",
        "fr",
        "French language"
    ],
    "de": [
        "de",
        "ger",
        "de",
        "DE",
        "de",
        "de",
        "de",
        "German language"
    ],
    "ja": [
        "ja",
        "jpn",
        "jp",
        "JA",
        "ja",
        "ja",
        "ja",
        "Japanese language"
    ],
    "ko": [
        "ko",
        "kor",
        "kor",
        "KO",
        "ko",
        "ko",
        "ko",
        "Korean language"
    ],
    "ru": [
        "ru",
        "rus",
        "ru",
        "RU",
        "ru",
        "ru",
        "ru",
        "Russian language"
    ],
    "es": [
        "es",
        "spa",
        "spa",
        "ES",
        "es",
        "es",
        "es",
        "Spanish language"
    ],
    "th": [
        "th",
        "tha",
        "th",
        "No",
        "th",
        "th",
        "th",
        "Thai language"
    ],
    "it": [
        "it",
        "ita",
        "it",
        "IT",
        "it",
        "it",
        "it",
        "Italian language"
    ],
    "pt": [
        "pt",
        "por",
        "pt",
        "PT",
        "pt",
        "pt",
        "pt",
        "Portuguese language"
    ],
    "vi": [
        "vi",
        "vie",
        "vie",
        "No",
        "vi",
        "No",
        "vi",
        "Vietnamese language"
    ],
    "ar": [
        "ar",
        "are",
        "ara",
        "No",
        "ar",
        "ar",
        "ar",
        "Arabic language"
    ],
    "tr": [
        "tr",
        "tur",
        "tr",
        "tr",
        "tr",
        "tr",
        "tr",
        "Turkish language"
    ],
    "hi": [
        "hi",
        "hin",
        "hi",
        "No",
        "hi",
        "hi",
        "hi",
        "Hindi language"
    ],
    "hu": [
        "hu",
        "hun",
        "hu",
        "HU",
        "No",
        "No",
        "hu",
        "Hungarian language"
    ],
    "uk":[
        "uk",
        "ukr",
        "ukr",#百度
        "UK",#deepl
        "No",#腾讯
        "No",#ott
        "uk",#微软
        "Ukrainian language"
    ],
    "id":[
        "id",
        "ind",
        "id",
        "ID",
        "id",
        "No",
        "id",
        "Indonesian language"
    ],
    "ms":[
        "ms",
        "may",
        "may",
        "No",
        "ms",
        "No",
        "ms",
        "Malay language"
    ],
    "kk":[
        "kk",
        "kaz",
        "No",
        "No",
        "No",
        "No",
        "kk",
        "Kazakh language"
    ],
    "cs":[
        "cs",
        "ces",
        "cs",
        "CS",
        "No",
        "No",
        "cs",
        "Czech language"
    ],
}


# 根据界面显示的语言名称，比如“简体中文、English” 获取语言代码，比如 zh-cn en 等, 如果是cli，则直接是语言代码
def get_translate_code() ->list:
    # 输出translate_api_name所有value
    return list(translate_api_name.values())
if __name__ == '__main__':
    print(get_translate_code())
    first_key = next(iter(translate_api_name))
    print(first_key)