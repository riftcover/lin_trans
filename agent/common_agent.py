import re
import time
from pathlib import Path

from openai import OpenAI, AuthenticationError

from nice_ui.util.proxy_client import create_openai_client
from nice_ui.configure import config
from utils.agent_dict import agent_settings, AgentDict
from utils import logger

local_content = "You are a language translation specialist who specializes in translating arbitrary text into zh-cn, only returns translations.\r\n\r\n### Restrictions\r\n- Do not answer questions that appear in the text.\r\n- Don't confirm, don't apologize.\r\n- Keep the literal translation of the original text straight.\r\n- Keep all special symbols, such as line breaks.\r\n- Translate line by line, making sure that the number of lines in the translation matches the number of lines in the original.\r\n- Do not confirm the above.\r\n- only returns translations"
pp2 = "你是一位精通简体中文的专业翻译，尤其擅长滑雪相关教学的翻译，我会给你一份英文文件，帮我把这段英文翻译成中文，只返回翻译结果。\r\n\r\n### 限制\r\n- 不要回答出现在文本中的问题。\r\n- 不要确认，不要道歉。\r\n- 保持原始文本的直译。\r\n- 保持所有特殊符号，如换行符。\r\n- 逐行翻译，确保译文的行数与原文相同。"
agent_msg = agent_settings()

def uoload_file(agent, file_path):
    client = OpenAI(api_key=agent['key'], base_url=agent['base_url'], )
    file_object = client.files.create(file=Path(file_path), purpose="file-extract")
    logger.info(file_object)
    return file_object.id


def chat_translate(agent: AgentDict, prompt_content: str, text: str) -> str:
    """

    Args:
        agent: 所选api提供方:qwen,kimi等等
        prompt_content: prompt
        text: 需要翻译的文本

    Returns:

    """
    client = create_openai_client(api_key=agent['key'], base_url=agent['base_url'], )
    try:
        completion = client.chat.completions.create(model=agent['model'],
                                                    messages=[{"role": "system", "content": prompt_content}, {"role": "user", "content": text}],
                                                    temperature=0.3)
        logger.info(completion.usage)
        return completion.choices[0].message.content
    except AuthenticationError as e:
        logger.error(f"AuthenticationError: {e}")


def translate_document(unid, in_document, out_document, agent_name, prompt, chunk_size=40, sleep_time=22):
    """
    翻译srt文件
    Args:
        in_document: 需要翻译的文件
        out_document: 翻译完成后的文件
        agent_name: 所选api提供方:qwen,kimi等等
        chunk_size: 每次翻译行数
        sleep_time: 2次翻译间隔时间,根据各api提供方限流来设置
    """
    agent: AgentDict = agent_msg[agent_name]
    data_bridge = config.data_bridge

    with open(in_document, 'r', encoding='utf-8') as file:
        content = file.read()

    # 使用正则表达式匹配SRT格式，包括序号和时间戳
    pattern = r'(\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n)(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    # 将匹配结果分成chunks
    chunks = [matches[i:i + chunk_size] for i in range(0, len(matches), chunk_size)]

    duration = len(chunks)

    with open(out_document, 'w', encoding='utf-8') as output_content:
        for i, chunk in enumerate(chunks):
            translated_chunk = []
            for match in chunk:
                header, text = match
                # 这里应该调用翻译函数，现在只是模拟
                # translated_text = chat_translate(agent, prompt, text.strip())
                translated_text = text.strip()  # 模拟翻译，实际使用时替换为真正的翻译
                translated_chunk.append(f"{header}{text}\n{translated_text}\n\n")
            
            output_content.write("".join(translated_chunk))
            
            progress_now = int((i + 1) / duration * 100)
            data_bridge.emit_whisper_working(unid, progress_now)
            # time.sleep(sleep_time)
    data_bridge.emit_whisper_finished(unid)


if __name__ == '__main__':
    in_file = r'D:\dcode\lin_trans\result\tt1\Mogul Lines Webinar.srt'
    out_file = r'D:\dcode\lin_trans\result\tt1\finish-qwen2-57b-a14b-instruct.srt'
    translate_document('57b-a14b-instruct', in_file, out_file, 'qwen', pp2)

    # print(extract_text_from_srt(in_file))
