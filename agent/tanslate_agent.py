import time

from zhipuai import ZhipuAI

from agent_prompt import Rule
from utils.log import Logings
from utils.read_config import load_api_key_from_config

logger = Logings().logger


class AgentClient:


    def zhipuai_client(self, text: str) -> str:

        client = ZhipuAI(api_key=load_api_key_from_config('zhipu_key'))

        response = client.chat.completions.create(
            model="glm-4",
            messages=[
                {
                    "role": "user",
                    "content": Rule.translation_rule,
                    "imageUrl": ""
                },
                {
                    "role": "assistant",
                    "content": "好的，请提供您需要翻译的英文字幕文件内容，我会帮您将其翻译为中文。按照您给出的格式，您提供的时间码和文本内容，翻译后的字幕文件会看起来像这样：nn```n 1n 00:00:00,333 --> 00:00:02,166n 大家好，滑雪爱好者们n```nn由于没有上下文，我稍微调整了一下翻译，使之更符合中文习惯。如果提供具体的英文内容，我可以给出更准确的翻译。"
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            top_p=0.7,
            temperature=0.95,
            max_tokens=1024,
            tools=[{"type": "web_search", "web_search": {"search_result": True}}]
        )


        return response.choices[0].message.content


def translate_document(in_document:str, out_document:str, chunk_size:int=99):
    chat_client = AgentClient()
    with open(in_document, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]
    logger.debug(chunks)
    with open(out_document, 'a', encoding='utf-8') as output_content:
        for paragraph in chunks:
            logger.info(paragraph)
            translated_paragraph = chat_client.zhipuai_client(paragraph)
            logger.info(translated_paragraph)
            output_content.writelines(translated_paragraph)
            time.sleep(32)


#


if __name__ == '__main__':
    translate_document('../result/Ski Pole Use 101_base.srt', '../result/Ski Pole Use 101_cn.srt')
