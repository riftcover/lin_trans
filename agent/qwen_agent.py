import random
import time
from http import HTTPStatus
from dashscope import Generation  # 建议dashscope SDK 的版本 >= 1.14.0
import dashscope
from openai import OpenAI

from nice_ui.util.proxy_client import create_openai_client
from utils.log import Logings

logger = Logings().logger

local_content = "You are a language translation specialist who specializes in translating arbitrary text into zh-cn, only returns translations.\r\n\r\n### Restrictions\r\n- Do not answer questions that appear in the text.\r\n- Don't confirm, don't apologize.\r\n- Keep the literal translation of the original text straight.\r\n- Keep all special symbols, such as line breaks.\r\n- Translate line by line, making sure that the number of lines in the translation matches the number of lines in the original.\r\n- Do not confirm the above.\r\n- only returns translations"
dashscope.api_key = "sk-b1d261afb71d40bea90b61ac11a202af"
key = "sk-b1d261afb71d40bea90b61ac11a202af"
tt = """
1
00:00:00,166 --> 00:00:01,166
we're going to talk about

2
00:00:01,933 --> 00:00:04,366
Mogul lines today and I'm going to present

3
00:00:04,866 --> 00:00:07,466
focus of three different lines

4
00:00:07,866 --> 00:00:11,366
and these different lines you could almost look at as

5
00:00:12,500 --> 00:00:15,466
tactics you could also look at them as

6
00:00:16,000 --> 00:00:18,166
of almost ability level specific

7
00:00:18,700 --> 00:00:20,900
easier medium hard

8
00:00:21,966 --> 00:00:25,166
and yeah it's just going to give you more options

9
00:00:25,166 --> 00:00:28,066
and hopefully you open up your eyes to seeing

10
00:00:29,700 --> 00:00:32,500
different ways to skiing down the moguls because really
"""


def chat_translate(prompt_content, text):
    messages = [{'role': 'system', 'content': prompt_content},
                {'role': 'user', 'content': text}]
    response = Generation.call(model="qwen2-57b-a14b-instruct",
                               messages=messages,
                               # 设置随机数种子seed，如果没有设置，则随机数种子默认为1234
                               seed=random.randint(1, 10000),
                               # 将输出设置为"message"格式
                               result_format='message')
    if response.status_code == HTTPStatus.OK:
        logger.info(response)
        return response.output.choices[0].message.content
    else:
        print(
            f'Request id: {response.request_id}, Status code: {response.status_code}, error code: {response.code}, error message: {response.message}'
        )


def get_response():
    client = create_openai_client(
        api_key=key,  # 如果您没有配置环境变量，请在此处用您的API Key进行替换
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope服务的base_url
    )
    completion = client.chat.completions.create(
        model="qwen2-57b-a14b-instruct",
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': '你是谁？'}]
    )
    print(completion.model_dump_json())


def translate_document(in_document, out_document, chunk_size=40):
    with open(in_document, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]

    with open(out_document, 'a', encoding='utf-8') as output_content:
        for paragraph in chunks:
            logger.info(paragraph)
            translated_paragraph = chat_translate(local_content, paragraph)
            print(translated_paragraph)
            output_content.writelines(translated_paragraph)
            time.sleep(10)