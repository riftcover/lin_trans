import json
from pydantic import BaseModel
import os
import re
import sys
from pathlib import Path
from queue import Queue

from nice_ui.configure import ModelDict
from utils import logger
from utils.crypto_utils import crypto_utils


# ============================================================================
# 路径配置
# ============================================================================

def get_executable_path():
    if getattr(sys, "frozen", False):
        # 如果程序是被“冻结”打包的，使用这个路径
        return os.path.dirname(sys.executable).replace("\\", "/")
    else:
        return str(Path.cwd()).replace("\\", "/")


def get_app_data_dir():
    """
    获取应用数据目录
    用于存储model
    macOS: ~/Library/Application Support/Lapped/
    Windows: 项目根目录（保持原有行为）
    Linux: ~/.local/share/Lapped/
    """
    if sys.platform == "darwin":  # macOS - 使用标准路径
        return Path.home() / "Library" / "Application Support" / "Lapped"
    elif sys.platform == "win32":  # Windows - 保持原有行为
        return Path(__file__).parent.parent.parent
    else:  # Linux
        return Path.home() / ".local" / "share" / "Lapped"


def get_documents_dir():
    """
    获取用户文档目录

    用于存储用户生成的文件（视频、字幕等）

    macOS: ~/Documents/Lapped/
    Windows: 项目根目录/result（保持原有行为）
    Linux: ~/Documents/Lapped/
    """
    if sys.platform == "darwin":  # macOS - 使用标准路径
        return Path.home() / "Documents" / "Lapped"
    elif sys.platform == "win32":  # Windows - 保持原有行为
        return Path(__file__).parent.parent.parent / "result"
    else:  # Linux
        return Path.home() / "Documents" / "Lapped"


# 基础路径
rootdir = get_executable_path()
root_path = Path(__file__).parent.parent.parent  # 项目根目录
sys_platform = sys.platform
app_data_dir = get_app_data_dir()
documents_dir = get_documents_dir()

# 模型路径（全局变量，单一数据源）
models_path = app_data_dir / "models"
funasr_model_path = models_path / "funasr" / "iic"

# 其他路径
temp_path = app_data_dir / "tmp"
TEMP_DIR = temp_path.as_posix()
sys_video = Path.home() / "Videos"
homedir = sys_video.as_posix()
result_path = documents_dir / "result"


def ensure_directories():
    """
    确保所有必需的目录存在

    这个函数在模块导入时调用一次，或者在需要时手动调用。
    """
    app_data_dir.mkdir(parents=True, exist_ok=True)
    documents_dir.mkdir(parents=True, exist_ok=True)
    funasr_model_path.mkdir(parents=True, exist_ok=True)
    temp_path.mkdir(parents=True, exist_ok=True)


# 初始化时创建目录
ensure_directories()

# ============================================================================
# 应用设置 - 从 set.ini 加载
# ============================================================================

defaulelang = "zh"


def parse_init():
    """解析 set.ini 配置文件"""
    init_settings = {
        "lang": defaulelang,
        "dubbing_thread": 3,
        "trans_row": 40,
        "trans_sleep": 22,
        "agent_rpm": 2,
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
                for it in f.readlines():
                    it = it.strip()
                    if not it or it.startswith(";") or it.startswith("#"):
                        continue
                    key, value = it.split("=", maxsplit=1)
                    key = key.strip()
                    value = value.strip()

                    # 类型转换
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
            logger.error(f"set.ini 中有语法错误: {str(e)}")

        # 修正 fontsize
        if isinstance(init_settings["fontsize"], str) and init_settings["fontsize"].find("px") > 0:
            init_settings["fontsize"] = int(init_settings["fontsize"].replace("px", ""))

    return init_settings


# 加载设置
settings = parse_init()

# 更新默认语言
if settings.get("lang"):
    defaulelang = settings["lang"].lower()

# ============================================================================
# 语言和模型数据 - 从 JSON 加载
# ============================================================================

# 语言代码文件
lang_path = root_path / f"nice_ui/language/{defaulelang}.json"
if not lang_path.exists():
    defaulelang = "en"
    lang_path = root_path / "nice_ui/language/{defaulelang}.json"

obj = json.load(lang_path.open("r", encoding="utf-8"))

# 交互语言代码
transobj = obj["translate_language"]
# 软件界面
uilanglist = obj["ui_lang"]
# 语言显示名称:语言代码
langlist: dict = obj["language_code_list"]
# 语言显示名称 list
langnamelist = list(langlist.keys())
# 模型列表
model_list: ModelDict = obj["model_code_list"]


def init_model_code_key() -> list:
    """
    模型列表的key值
    example: ['多语言模型', '中文模型', '英语模型']
    """
    code = [key.split(".")[0] for key in model_list.keys()]
    return code


model_code_list = init_model_code_key()

# 工具箱语言
box_lang = obj["toolbox_lang"]

# ============================================================================
# 环境变量设置
# ============================================================================

os.environ["QT_API"] = "pyside6"
os.environ["SOFT_NAME"] = "Lapped AI"

# ============================================================================
# 运行时状态 - 全局可变状态
# ============================================================================

# 队列
queue_logs = Queue(1000)
queuebox_logs = Queue(1000)
lin_queue = Queue()

# 任务队列
queue_asr = []
queue_trans = []
queue_novice = {}

# 状态标志
box_status = "stop"
box_trans = "stop"
separate_status = "stop"
is_consuming = False
exit_soft = False
canceldown = False

# 计数器
geshi_num = 0
task_countdown = 60

# 缓存
video_cache = {}
errorlist = {}

# 其他状态
last_opendir = homedir
video_codec = None
video_min_ms = 50

# TTS 相关
edgeTTS_rolelist = None
AzureTTS_rolelist = None
proxy = None

# 语音列表
clone_voicelist = ["clone"]
ChatTTS_voicelist = re.split(r",|，", settings.get("chattts_voice", "1111,2222,3333,4444,5555,6666,7777,8888,9999,4099,5099,6653,7869"))
openaiTTS_rolelist = "alloy,echo,fable,onyx,nova,shimmer"

# ============================================================================
# 任务参数 - 运行时可修改的参数
# ============================================================================

params = {
    "source_mp4": "",
    "target_dir": result_path,
    "output_dir": "",
    "source_language_code": "en",
    "source_language": "英语",
    "source_module_status": 302,
    "source_module_name": "small",
    "source_module_key": "云模型",
    "detect_language": "en",
    "translate_status": False,
    "target_language": "中文",
    "translate_channel": "通义千问",
    "subtitle_language": "chi",
    "prompt_name": "默认",
    "prompt_text": "",
    "cuda": False,
    "is_separate": False,
    "voice_role": "No",
    "voice_rate": "0",
    "tts_type": "edgeTTS",
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
    "subtitle_type": 0,
    "voice_autorate": False,
    "auto_ajust": True,
}


# ============================================================================
# 云服务配置 - 加密凭证
# ============================================================================


class PplSdkConfig(BaseModel):
    aki: str = ""
    aks: str = ""
    region: str = "cn-beijing"
    bucket: str = "asr-file-tth"
    asr_api_key: str = ""
    asr_model: str = "paraformer-v2"
    gladia_api_key: str = ""


class CloudConfig(BaseModel):
    ppl_sdk: PplSdkConfig


def get_cloud_config():
    """获取云服务配置，优先从加密文件加载"""
    try:
        crypto_utils.initialize()
        credentials_file = crypto_utils.get_credentials_file_path(root_path)

        if credentials_file.exists():
            try:
                credentials = crypto_utils.decrypt_from_file(credentials_file)
                if isinstance(credentials, dict) and 'ppl_sdk' in credentials:
                    return CloudConfig(**credentials)
            except Exception as e:
                logger.error(f"从加密文件加载凭证失败: {str(e)}")
    except Exception as e:
        logger.error(f"获取云服务配置失败: {str(e)}")

    return None


aa_bb = get_cloud_config()

# ============================================================================
# 代理设置
# ============================================================================

agent_settings = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen2-57b-a14b-instruct",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k"
    },
}

# ============================================================================
# 模板路径
# ============================================================================

chatgpt_path = root_path / "nice_ui/chatgpt.txt"
localllm_path = root_path / "nice_ui/localllm.txt"
zijiehuoshan_path = root_path / "nice_ui/zijie.txt"
azure_path = root_path / "nice_ui/azure.txt"
gemini_path = root_path / "nice_ui/gemini.txt"
