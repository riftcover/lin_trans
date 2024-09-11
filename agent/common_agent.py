import time
from pathlib import Path

from openai import OpenAI, AuthenticationError

from nice_ui.configure import config
from utils.agent_dict import agent_settings, AgentDict
from utils.log import Logings

logger = Logings().logger

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
    client = OpenAI(api_key=agent['key'], base_url=agent['base_url'], )
    try:
        completion = client.chat.completions.create(model=agent['model'],
                                                    messages=[{"role": "system", "content": prompt_content}, {"role": "user", "content": text}],
                                                    temperature=0.3)
        logger.info(completion.usage)
        return completion.choices[0].message.content
    except AuthenticationError as e:
        logger.error(f"AuthenticationError: {e}")


def translate_document(unid,in_document, out_document, agent_name,prompt, chunk_size=40, sleep_time=22):
    """
    翻译srt文件
    Args:
        unid: 文件指纹
        in_document: 需要翻译的文件
        out_document: 翻译完成后的文件
        agent_name: 所选api提供方:qwen,kimi等等
        chunk_size: 每次翻译行数
        sleep_time: 2次翻译间隔时间,根据各api提供方限流来设置
    """
    agent: AgentDict = agent_msg[agent_name]
    data_bridge = config.data_bridge
    with open(in_document, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # chunks = ["".join(lines[i:i + chunk_size]) for i in range(0, len(lines), chunk_size)]
    chunks = list(range(chunk_size))
    duration = len(chunks)

    with open(out_document, 'a', encoding='utf-8') as output_content:
        for i,paragraph in enumerate(chunks):
            logger.info(paragraph)
            # translated_paragraph = chat_translate(agent, prompt, paragraph)
            # output_content.writelines(translated_paragraph)
            progress_now = int((i+1)/duration*100)
            data_bridge.emit_whisper_working(unid, progress_now)
            time.sleep(sleep_time)
    data_bridge.emit_whisper_finished(unid)


if __name__ == '__main__':
    filter = r'D:\dcode\lin_trans\result\tt1\Mogul Lines Webinar.srt'
    out_file = r'D:\dcode\lin_trans\result\tt1\finish-qwen2-57b-a14b-instruct.srt'
    translate_document('57b-a14b-instruct', filter, out_file)
