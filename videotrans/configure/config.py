import datetime
import json
import os
import locale

import re
import sys
from queue import Queue
from pathlib import Path

from utils.log import Logings

logger = Logings().logger


root_path = Path(__file__).parent.parent.parent  # 项目目录
rootdir =root_path
logger.debug(root_path)

defaulelang = locale.getdefaultlocale()[0][:2].lower()  # 获取本地语言
def parse_init():
    # 加载init
    settings = {
        "lang": defaulelang,
        "dubbing_thread": 3,
        "trans_thread": 15,
        "countdown_sec": 30,
        "cuda_com_type": "float32",
        "whisper_threads": 4,
        "whisper_worker": 1,
        "beam_size": 1,
        "best_of": 1,
        "vad": True,
        "temperature": 1,
        "condition_on_previous_text": False,
        "crf": 13,
        "video_codec": 264,
        "retries": 2,
        "chatgpt_model": "gpt-3.5-turbo,gpt-4,gpt-4-turbo-preview,qwen",
        "localllm_model": "qwen",
        "separate_sec": 600,
        "audio_rate": 1.5,
        "video_rate": 20,
        "initial_prompt_zh": "Please break sentences correctly and retain punctuation",
        "fontsize": 16,
        "fontname": "黑体",
        "fontcolor": "&HFFFFFF",
        "fontbordercolor": "&H000000",
        "subtitle_bottom": 0,
        "voice_silence": 200,
        "interval_split": 6,
        "cjk_len": 24,
        "other_len": 36,
        "backaudio_volume": 0.5,
        "overall_silence": 2100,
        "overall_maxsecs": 3,
        "overall_threshold": 0.5,
        "overall_speech_pad_ms": 100,
        "remove_srt_silence": False,
        "remove_silence": True,
        "remove_white_ms": 100,
        "vsync": "passthrough",
        "force_edit_srt": True,
        "loop_backaudio": False,
        "chattts_voice": '1111,2222,3333,4444,5555,6666,7777,8888,9999,4099,5099,6653,7869',
        "cors_run": True
    }
    file = root_path / 'videotrans/set.ini'
    if file.exists():
        try:
            with file.open('r', encoding="utf-8") as f:
                # 遍历.ini文件中的每个section
                for it in f.readlines():

                    it = it.strip()
                    if not it or it.startswith(';'):
                        continue
                    key, value = it.split('=', maxsplit=1)
                    # 遍历每个section中的每个option
                    key = key.strip()
                    value = value.strip()
                    if re.match(r'^\d+$', value):
                        settings[key] = int(value)
                    elif re.match(r'^\d+\.\d$', value):
                        settings[key] = round(float(value), 1)
                    elif value.lower() == 'true':
                        settings[key] = True
                    elif value.lower() == 'false':
                        settings[key] = False
                    else:
                        settings[key] = str(value.lower()) if value else None
        except Exception as e:
            logger.error(f'set.ini 中有语法错误:{str(e)}')
        if isinstance(settings['fontsize'], str) and settings['fontsize'].find('px') > 0:
            settings['fontsize'] = int(settings['fontsize'].replace('px', ''))
    return settings


lang_path=root_path/f'videotrans/language/{defaulelang}.json'

obj = json.load(lang_path.open('r', encoding='utf-8'))
# 交互语言代码
transobj = obj["translate_language"]
# 软件界面
uilanglist = obj["ui_lang"]
# 语言代码:语言显示名称
langlist: dict = obj["language_code_list"]
# 语言显示名称：语言代码
rev_langlist = {code_alias: code for code, code_alias in langlist.items()}
# 语言显示名称 list
langnamelist = list(langlist.values())
# 工具箱语言
box_lang = obj['toolbox_lang']

if __name__ == '__main__':
    logger.info(lang_path)
    logger.info(obj)