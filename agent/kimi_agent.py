import time

from PySide6.QtCore import QSettings
from openai import OpenAI

settings = QSettings("Locoweed", "LinLInTrans")
kimi_key = settings.value("kimi", type=str)
kimi_key = "sk-sPxaILKN9LDvVsybCzFMTiDZMxMmFRJTTDoBW5ACDbRsYpqF"



local_content = """
             你是一位精通简体中文的专业翻译，尤其擅长滑雪相关教学的翻译，我会给你一份英文文件，帮我把这段英文翻译成中文，提供给我完整的中文尽量保证中文内容的行数与英文文件一致.
             """

def chat_translate(prompt_content,text):
    client = OpenAI(api_key = kimi_key, base_url="https://api.moonshot.cn/v1", )
    completion = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system",
             "content": prompt_content},
            # {
            #     "role": "system",
            #     "content": file_content,
            # },
            {"role": "user", "content": text}
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.content


def translate_document(in_document, out_document, chunk_size=40):
    with open(in_document, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]

    with open(out_document, 'a', encoding='utf-8') as output_content:
        for paragraph in chunks:
            print(paragraph)
            translated_paragraph = chat_translate(local_content, paragraph)
            print(translated_paragraph)
            output_content.writelines(translated_paragraph)
            time.sleep(32)


if __name__ == '__main__':
    filter = r'D:\dcode\lin_trans\result\tt1\Mogul Lines Webinar.srt'
    out_file = r'D:\dcode\lin_trans\result\tt1\finish_kimi.srt'
    translation = translate_document(filter, out_file)

