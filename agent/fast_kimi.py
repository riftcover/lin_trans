import time

from openai import OpenAI

client = OpenAI(
    api_key="sk-ZBNavwnJtJzolfVLIxCPaBoYEYfwytXk0ezdo49pwQ3frjl6",
    base_url="https://api.moonshot.cn/v1",
)
filter = 'data/5月24日.txt'
out_file='data/finish.txt'
def chat_translate(text):
    completion = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system",
             "content": """
             你是一位精通简体中文的专业翻译，尤其擅长滑雪相关教学的翻译，我会给你一份英文文件，帮我把这段英文翻译成中文，提供给我完整的中文尽量保证中文内容的行数与英文文件一致.
             """},
            # {
            #     "role": "system",
            #     "content": file_content,
            # },
            {"role": "user", "content": text}
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.content


def translate_document(in_document,out_document, chunk_size=30):
    with open(in_document, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]

    with open(out_document, 'a', encoding='utf-8') as output_content:
        for paragraph in chunks:
            print(paragraph)
            translated_paragraph = chat_translate(paragraph)
            print(translated_paragraph)
            output_content.writelines(translated_paragraph)
            time.sleep(32)


#
translation = translate_document(filter,out_file)
print(translation)

