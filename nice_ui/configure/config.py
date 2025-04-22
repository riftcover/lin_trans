import json
import os
import re
import sys
from pathlib import Path
from queue import Queue

from nice_ui.configure import ModelDict
from nice_ui.ui.SingalBridge import DataBridge
from utils import logger


# from utils.log import Logings
#
# logger = Logings().logger

#asr模型算力消耗（算力/秒）
asr_qps = 4
# 翻译模型算力消耗（算力/字）
trans_qps = 2

def get_executable_path():
    # 这个函数会返回可执行文件所在的目录
    if getattr(sys, "frozen", False):
        # 如果程序是被“冻结”打包的，使用这个路径
        return os.path.dirname(sys.executable).replace("\\", "/")
    else:
        return str(Path.cwd()).replace("\\", "/")


# root dir
rootdir = get_executable_path()
root_path = Path(__file__).parent.parent.parent  # 项目目录
sys_platform = sys.platform

# models_path = os.path.join(root_path,'models')
root_same = Path(__file__).parent.parent.parent.parent
models_path = root_same / "models"
funasr_model_path = models_path/"funasr"/"iic"
funasr_model_path.mkdir(parents=True, exist_ok=True)

# 修改为函数，方便动态更新
def update_funasr_path():
    global funasr_model_path
    funasr_model_path = Path(models_path)/"funasr"/"iic"
    funasr_model_path.mkdir(parents=True, exist_ok=True)
    return funasr_model_path

# 初始化 funasr_model_path
funasr_model_path = update_funasr_path()

temp_path = root_path / "tmp"
temp_path.mkdir(parents=True, exist_ok=True)
TEMP_DIR = temp_path.as_posix()

# home
homepath = Path.home() / "Videos/linlin"
homepath.mkdir(parents=True, exist_ok=True)
homedir = homepath.as_posix()

# home tmp
TEMP_HOME = homedir + "/tmp"
Path(TEMP_HOME).mkdir(parents=True, exist_ok=True)

result_path = root_path / "result"

# defaulelang = locale.getlocale()[0][:2].lower()  # 获取本地语言

defaulelang = "zh"


def parse_init():
    # 加载init
    init_settings = {
        "lang": defaulelang,
        "dubbing_thread": 3,
        "trans_row": 40,  # 每次翻译的行数
        "trans_sleep": 22,
        "agent_rpm": 2,  # api每分钟请求次数
        "cuda_com_type": "float16",
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
        "zijiehuoshan_model": "",
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
        "chattts_voice": "1111,2222,3333,4444,5555,6666,7777,8888,9999,4099,5099,6653,7869",
        "cors_run": True,
    }
    file = root_path / "nice_ui/set.ini"
    if file.exists():
        try:
            with file.open("r", encoding="utf-8") as f:
                # 遍历.ini文件中的每个section
                for it in f.readlines():

                    it = it.strip()
                    if not it or it.startswith(";") or it.startswith("#"):
                        continue
                    key, value = it.split("=", maxsplit=1)
                    # 遍历每个section中的每个option
                    key = key.strip()
                    value = value.strip()
                    if re.match(r"^\d+$", value):
                        init_settings[key] = int(value)
                    elif re.match(r"^\d+\.\d$", value):
                        init_settings[key] = round(float(value), 1)
                    elif value.lower() == "true":
                        init_settings[key] = True
                    elif value.lower() == "false":
                        init_settings[key] = False
                    else:
                        init_settings[key] = str(value.lower()) if value else ""
        except Exception as e:
            logger.error(f"set.ini 中有语法错误:{str(e)}")
        if (
            isinstance(init_settings["fontsize"], str)
            and init_settings["fontsize"].find("px") > 0
        ):
            init_settings["fontsize"] = int(init_settings["fontsize"].replace("px", ""))
    return init_settings


# 初始化一个字典变量
settings = parse_init()

# default language 如果 ini中设置了，则直接使用，否则自动判断
if settings["lang"]:
    defaulelang = settings["lang"].lower()
# 语言代码文件是否存在
lang_path = root_path / f"nice_ui/language/{defaulelang}.json"
if not lang_path.exists():
    defaulelang = "en"
    lang_path = root_path / f"nice_ui/language/{defaulelang}.json"

obj = json.load(lang_path.open("r", encoding="utf-8"))
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

# 模型列表
model_list: ModelDict = obj["model_code_list"]


def init_model_code_key() -> list:
    """
    模型列表的key值
    example: ['多语言模型', '中文模型', '英语模型']
    """

    # todo：应该先读取本地安装的模型，然后修改model_list的值
    code = [key.split(".")[0] for key in model_list.keys()]

    return code


model_code_list = init_model_code_key()

# 工具箱语言
box_lang = obj["toolbox_lang"]

# whisper.cpp
# if sys.platform == "win32":
#     PWD = rootdir.replace("/", "\\")
#     os.environ["PATH"] = f"{root_path}/whisper.cpp;" + os.environ["PATH"]
#
# else:
#     os.environ["PATH"] = f"{root_path}/whisper.cpp:" + os.environ["PATH"]

os.environ["QT_API"] = "pyside6"
os.environ["SOFT_NAME"] = "linlintrans"
# spwin主窗口
queue_logs = Queue(1000)
# box窗口
queuebox_logs = Queue(1000)

# video toolbox 状态
box_status = "stop"
# 工具箱 需格式化的文件数量
geshi_num = 0

clone_voicelist = ["clone"]

ChatTTS_voicelist = re.split("\,|，", settings["chattts_voice"])

openaiTTS_rolelist = "alloy,echo,fable,onyx,nova,shimmer"
chatgpt_model_list = [it.strip() for it in settings["chatgpt_model"].split(",")]
localllm_model_list = [it.strip() for it in settings["localllm_model"].split(",")]
zijiehuoshan_model_list = [
    it.strip() for it in settings["zijiehuoshan_model"].split(",")
]
# 存放 edget-tts 角色列表
edgeTTS_rolelist = None
AzureTTS_rolelist = None
proxy = None

# 配置
params = {  # 操作系统类型:win32、linux、darwin
    "source_mp4": "",  # 需要进行处理的文件
    "target_dir": root_path / "result",  # result文件夹
    "output_dir": "",  # 导出文件夹
    "source_language_code": "en",  # 原语言
    "source_language": "英文",
    "source_module_status": 302,  # 语音转文本模型
    "source_module_name": "small",
    "source_module_key":"中文模型",
    "detect_language": "en",
    "translate_status": False,
    "target_language": "zh-cn",
    "translate_channel": "通义千问",
    "subtitle_language": "chi",
    "prompt_name": "默认",
    "prompt_text": "",
    "cuda": False,
    "is_separate": False,
    "voice_role": "No",
    "voice_rate": "0",
    "tts_type": "edgeTTS",  # 所选的tts==edge-tts:openaiTTS|coquiTTS|elevenlabsTTS
    "tts_type_list": [
        "edgeTTS",
        "ChatTTS",
        "gtts",
        "AzureTTS",
        "GPT-SoVITS",
        "clone-voice",
        "openaiTTS",
        "elevenlabsTTS",
        "TTS-API",
    ],
    "only_video": False,
    "subtitle_type": 0,  # embed soft
    "voice_autorate": False,
    "auto_ajust": True,
    "deepl_authkey": "",
    "deepl_api": "",
    "deeplx_address": "",
    "ott_address": "",
    "tencent_SecretId": "",
    "tencent_SecretKey": "",
    "baidu_appid": "",
    "baidu_miyue": "",
    "coquitts_role": "",
    "coquitts_key": "",
    "elevenlabstts_role": [],
    "elevenlabstts_key": "",
    "clone_api": "",
    "zh_recogn_api": "",
    "chatgpt_api": "",
    "chatgpt_key": "",
    "localllm_api": "",
    "localllm_key": "",
    "zijiehuoshan_key": "",
    "chatgpt_model": chatgpt_model_list[0],
    "localllm_model": localllm_model_list[0],
    "zijiehuoshan_model": zijiehuoshan_model_list[0],
    "chatgpt_template": "",
    "localllm_template": "",
    "zijiehuoshan_template": "",
    "azure_api": "",
    "azure_key": "",
    "azure_model": "gpt-3.5-turbo",
    "azure_template": "",
    "openaitts_role": openaiTTS_rolelist,
    "gemini_key": "",
    "gemini_template": "",
    "ttsapi_url": "",
    "ttsapi_voice_role": "",
    "ttsapi_extra": "linlin",
    "trans_api_url": "",
    "trans_secret": "",
    "azure_speech_region": "",
    "azure_speech_key": "",
    "gptsovits_url": "",
    "gptsovits_role": "",
    "gptsovits_extra": "linlin",
    # 阿里云ASR配置
    "aliyun_asr_api_key": "sk-b1d261afb71d40bea90b61ac11a202af",
    "aliyun_asr_model":"paraformer-v2"
}

chatgpt_path = root_path / "nice_ui/chatgpt.txt"
localllm_path = root_path / "nice_ui/localllm.txt"
zijiehuoshan_path = root_path / "nice_ui/zijie.txt"
azure_path = root_path / "nice_ui/azure.txt"
gemini_path = root_path / "nice_ui/gemini.txt"

# params['localllm_template'] = localllm_path.read_text(encoding='utf-8').strip() + "\n"
# params['zijiehuoshan_template'] = zijiehuoshan_path.read_text(encoding='utf-8').strip() + "\n"
# params['chatgpt_template'] = chatgpt_path.read_text(encoding='utf-8').strip() + "\n"
# params['azure_template'] = azure_path.read_text(encoding='utf-8').strip() + "\n"
# params['gemini_template'] = gemini_path.read_text(encoding='utf-8').strip() + "\n"

agent_settings = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen2-57b-a14b-instruct",
    },
    "kimi": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
}
# 存放一次性多选的视频
queue_asr = []
# 存放视频分离为无声视频进度，noextname为key，用于判断某个视频是否是否已预先创建好 novice_mp4, “ing”=需等待，end=成功完成，error=出错了
queue_novice = {}

# 存放一次性多选的srt
queue_trans = []

# 倒计时
task_countdown = 60
# 获取的视频信息 全局缓存
video_cache = {}

# youtube是否取消了下载
canceldown = False
# 工具箱翻译进行状态,ing进行中，其他停止
box_trans = "stop"

# 中断win背景分离
separate_status = "stop"
# 最后一次打开的目录
last_opendir = homedir
# 软件退出
exit_soft = False

lin_queue = Queue()  # 任务队列

is_consuming = False


class SingletonDataBridge:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DataBridge()
        return cls._instance


data_bridge = SingletonDataBridge.get_instance()

# 全局错误
errorlist = {}

# 当前可用编码 libx264 h264_qsv h264_nvenc 等
video_codec = None

# 视频慢速时最小间隔毫秒，默认50ms，小于这个值的视频片段将舍弃，避免出错
video_min_ms = 50