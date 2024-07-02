import json
import locale
import os
import re
import sys
from pathlib import Path
from queue import Queue

from utils.log import Logings
from videotrans.configure import ModelDict
# logs
logger = Logings().logger

def get_executable_path():
    # 这个函数会返回可执行文件所在的目录
    if getattr(sys, 'frozen', False):
        # 如果程序是被“冻结”打包的，使用这个路径
        return os.path.dirname(sys.executable).replace('\\', '/')
    else:
        return str(Path.cwd()).replace('\\', '/')

# root dir
rootdir = get_executable_path()
root_path = Path(__file__).parent.parent.parent  # 项目目录

# cache tmp
temp_path = root_path / "tmp"
temp_path.mkdir(parents=True, exist_ok=True)
TEMP_DIR = temp_path.as_posix()

# home
homepath = Path.home() / 'Videos/pyvideotrans'
homepath.mkdir(parents=True, exist_ok=True)
homedir = homepath.as_posix()

# home tmp
TEMP_HOME = homedir + "/tmp"
Path(TEMP_HOME).mkdir(parents=True, exist_ok=True)

result_path = root_path / "result"



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
                    if not it or it.startswith(';') or it.startswith('#'):
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
                        settings[key] = str(value.lower()) if value else ""
        except Exception as e:
            logger.error(f'set.ini 中有语法错误:{str(e)}')
        if isinstance(settings['fontsize'], str) and settings['fontsize'].find('px') > 0:
            settings['fontsize'] = int(settings['fontsize'].replace('px', ''))
    return settings


# 语言
try:
    defaulelang = locale.getdefaultlocale()[0][:2].lower()
except Exception:
    defaulelang = "zh"

# 初始化一个字典变量
settings = parse_init()

# default language 如果 ini中设置了，则直接使用，否则自动判断
if settings['lang']:
    defaulelang = settings['lang'].lower()
# 语言代码文件是否存在
lang_path = root_path / f'videotrans/language/{defaulelang}.json'
if not lang_path.exists():
    defaulelang = "en"
    lang_path = root_path / f'videotrans/language/{defaulelang}.json'

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

# 模型列表
model_list: ModelDict = obj["model_code_list"]


def init_model_code_key() -> list:
    # 模型列表
    # todo：应该先读取本地安装的模型，然后修改model_list的值
    code = [key.split('.')[0] for key in model_list.keys()]

    return code


model_code_list = init_model_code_key()

# 工具箱语言
box_lang = obj['toolbox_lang']

# ffmpeg,whisper.cpp
if sys.platform == 'win32':
    PWD = rootdir.replace('/', '\\')
    os.environ['PATH'] = f'{root_path}/plugin/ffmpeg;' + os.environ['PATH']
    os.environ['PATH'] = f'{root_path}/whisper.cpp;' + os.environ['PATH']

else:
    os.environ['PATH'] = f'{root_path}/plugin/ffmpeg:' + os.environ['PATH']
    os.environ['PATH'] = f'{root_path}/whisper.cpp:' + os.environ['PATH']


os.environ['QT_API'] = 'pyside6'
os.environ['SOFT_NAME'] = 'linlintrans'
# spwin主窗口
queue_logs = Queue(1000)
# box窗口
queuebox_logs = Queue(1000)

# video toolbox 状态
box_status = "stop"
# 工具箱 需格式化的文件数量
geshi_num = 0

clone_voicelist = ["clone"]

ChatTTS_voicelist = re.split('\,|，', settings['chattts_voice'])

openaiTTS_rolelist = "alloy,echo,fable,onyx,nova,shimmer"
chatgpt_model_list = [it.strip() for it in settings['chatgpt_model'].split(',')]
localllm_model_list = [it.strip() for it in settings['localllm_model'].split(',')]
zijiehuoshan_model_list = [it.strip() for it in settings['zijiehuoshan_model'].split(',')]
# 存放 edget-tts 角色列表
edgeTTS_rolelist = None
AzureTTS_rolelist = None
proxy = None
# 配置
params = {
    "source_mp4": "", # 需要进行处理的文件
    "target_dir": root_path / "result",  # 结果缓存文件夹
    "output_dir": "",  # 导出文件夹

    "source_language": "en",
    "source_module_status": 4, #语音转文本模型
    "source_module_name": "small",
    "detect_language": "en",

    "translate_status": False,
    "target_language": "zh-cn",
    "translate_type": "google",
    "subtitle_language": "chi",

    "cuda": False,
    "is_separate": False,

    "voice_role": "No",
    "voice_rate": "0",

    "listen_text_zh-cn": "你好啊，我亲爱的朋友，希望你的每一天都是美好愉快的！",
    "listen_text_zh-tw": "你好啊，我親愛的朋友，希望你的每一天都是美好愉快的！",
    "listen_text_en": "Hello, my dear friend. I hope your every day is beautiful and enjoyable!",
    "listen_text_fr": "Bonjour mon cher ami. J'espère que votre quotidien est beau et agréable !",
    "listen_text_de": "Hallo mein lieber Freund. Ich hoffe, dass Ihr Tag schön und angenehm ist!",
    "listen_text_ja": "こんにちは私の親愛なる友人。 あなたの毎日が美しく楽しいものでありますように！",
    "listen_text_ko": "안녕, 내 사랑하는 친구. 당신의 매일이 아름답고 즐겁기를 바랍니다!",
    "listen_text_ru": "Привет, мой дорогой друг. Желаю, чтобы каждый твой день был прекрасен и приятен!",
    "listen_text_es": "Hola mi querido amigo. ¡Espero que cada día sea hermoso y agradable!",
    "listen_text_th": "สวัสดีเพื่อนรัก. ฉันหวังว่าทุกวันของคุณจะสวยงามและสนุกสนาน!",
    "listen_text_it": "Ciao caro amico mio. Spero che ogni tuo giorno sia bello e divertente!",
    "listen_text_pt": "Olá meu querido amigo. Espero que todos os seus dias sejam lindos e agradáveis!",
    "listen_text_vi": "Xin chào người bạn thân yêu của tôi. Tôi hy vọng mỗi ngày của bạn đều đẹp và thú vị!",
    "listen_text_ar": "مرحبا صديقي العزيز. أتمنى أن يكون كل يوم جميلاً وممتعًا!",
    "listen_text_tr": "Merhaba sevgili arkadaşım. Umarım her gününüz güzel ve keyifli geçer!",
    "listen_text_hi": "नमस्ते मेरे प्यारे दोस्त। मुझे आशा है कि आपका हर दिन सुंदर और आनंददायक हो!!",
    "listen_text_hu": "Helló kedves barátom. Remélem minden napod szép és kellemes!",

    "tts_type": "edgeTTS",  # 所选的tts==edge-tts:openaiTTS|coquiTTS|elevenlabsTTS
    "tts_type_list": ["edgeTTS", "ChatTTS", "gtts", "AzureTTS", "GPT-SoVITS", "clone-voice", "openaiTTS",
                      "elevenlabsTTS", "TTS-API"],

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
    "ttsapi_extra": "pyvideotrans",

    "trans_api_url": "",
    "trans_secret": "",

    "azure_speech_region": "",
    "azure_speech_key": "",

    "gptsovits_url": "",
    "gptsovits_role": "",
    "gptsovits_extra": "pyvideotrans"

}

chatgpt_path = root_path / 'videotrans/chatgpt.txt'
localllm_path = root_path / 'videotrans/localllm.txt'
zijiehuoshan_path = root_path / 'videotrans/zijie.txt'
azure_path = root_path / 'videotrans/azure.txt'
gemini_path = root_path / 'videotrans/gemini.txt'

params['localllm_template'] = localllm_path.read_text(encoding='utf-8').strip() + "\n"
params['zijiehuoshan_template'] = zijiehuoshan_path.read_text(encoding='utf-8').strip() + "\n"
params['chatgpt_template'] = chatgpt_path.read_text(encoding='utf-8').strip() + "\n"
params['azure_template'] = azure_path.read_text(encoding='utf-8').strip() + "\n"
params['gemini_template'] = gemini_path.read_text(encoding='utf-8').strip() + "\n"

# 存放一次性多选的视频
queue_mp4 = []
# 存放视频分离为无声视频进度，noextname为key，用于判断某个视频是否是否已预先创建好 novice_mp4, “ing”=需等待，end=成功完成，error=出错了
queue_novice = {}

# 倒计时
task_countdown = 60
# 获取的视频信息 全局缓存
video_cache = {}

# youtube是否取消了下载
canceldown = False
# 工具箱翻译进行状态,ing进行中，其他停止
box_trans = "stop"

# 中断win背景分离
separate_status = 'stop'
# 最后一次打开的目录
last_opendir = homedir
# 软件退出
exit_soft = False

mp4_to_war_queue = Queue()  # 视频转音频队列
tts_queue = Queue()  # 音频转文本队列
trans_queue = Queue()
is_consuming = False

# 视频转音频队列
mp4_queue = []
# # 音频转文本队列
# tts_queue = []
# # 翻译队列
# trans_queue = []
# 配音队列
dubb_queue = []
# 识别队列
regcon_queue = []
# 合成队列
compose_queue = []
# 全局任务id列表
unidlist = []
# 全局错误
errorlist = {}

# 当前可用编码 libx264 h264_qsv h264_nvenc 等
video_codec = None

# 视频慢速时最小间隔毫秒，默认50ms，小于这个值的视频片段将舍弃，避免出错
video_min_ms = 50

if __name__ == '__main__':
    # logger.info(lang_path)
    # logger.info(obj)
    logger.info(model_code_list)
