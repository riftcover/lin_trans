import re
import time
from pathlib import Path

from openai import OpenAI, AuthenticationError

from nice_ui.configure.signal import data_bridge
from nice_ui.configure import config
from nice_ui.util.proxy_client import create_openai_client
from utils import logger
from utils.agent_dict import agent_settings, AgentDict

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
        # logger.info(completion.usage)
        return completion.choices[0].message.content
    except AuthenticationError as e:
        logger.error(f"AuthenticationError: {e}")


def translate_document(unid, in_document, out_document, agent_name, prompt, chunk_size=20, sleep_time=10):
    """
    翻译srt文件
    Args:
        unid: 任务id
        in_document: 需要翻译的文件
        out_document: 翻译完成后的文件
        agent_name: 所选api提供方:qwen,kimi等等
        chunk_size: 每次翻译行数
        prompt: 翻译提示
        sleep_time: 2次翻译间隔时间,根据各api提供方限流来设置
    """
    agent: AgentDict = agent_msg[agent_name]
    logger.trace(f'chunk_size: {chunk_size}, sleep_time: {sleep_time}')
    with open(in_document, 'r', encoding='utf-8') as file:
        content = file.read()

    # 使用正则表达式匹配SRT格式，包括序号和时间戳
    pattern = r'(\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n)(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    # 将匹配结果分成chunks
    chunks = [matches[i:i + chunk_size] for i in range(0, len(matches), chunk_size)]

    duration = len(chunks)
    logger.info(f"共{duration}个chunk, 开始翻译...")

    with open(out_document, 'w', encoding='utf-8') as output_content:
        for i, chunk in enumerate(chunks):
            # 提取当前chunk中所有的文本并合并为一个字符串
            texts_to_translate = "\n".join([match[1].strip() for match in chunk])

            # 这里应该调用批量翻译函数，现在只是模拟
            translated_text = chat_translate(agent, prompt, texts_to_translate)

            # 模拟翻译，实际使用时替换为真正的批量翻译
            # translated_text = texts_to_translate

            logger.trace(f"翻译进度: {i + 1}/{duration}")
            # logger.trace(f'原文: {texts_to_translate}')
            # logger.trace(f"译文: {translated_text}")

            # 将翻译后的文本拆分回单独的句子
            translated_sentences = translated_text.split("\n")

            translated_chunk = []
            for j, (header, original_text) in enumerate(chunk):
                translated_sentence = translated_sentences[j] if j < len(translated_sentences) else ""
                translated_chunk.append(f"{header}{original_text}\n{translated_sentence}\n\n")

            output_content.write("".join(translated_chunk))

            progress_now = int((i + 1) / duration * 100)
            data_bridge.emit_whisper_working(unid, progress_now)
            if i == duration - 1:
                time.sleep(sleep_time)

    data_bridge.emit_whisper_finished(unid)
