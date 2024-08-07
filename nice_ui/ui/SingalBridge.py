import os

from PySide6.QtCore import Signal, QObject, QSettings

from nice_ui.configure import config


def get_setting_cache(settings: QSettings):
    for k in config.params.keys():
        config.params[k] = settings.value(k, "")

    # 从缓存获取默认配置
    config.params["voice_autorate"] = settings.value("voice_autorate", False, bool)
    config.params["video_autorate"] = settings.value("video_autorate", False, bool)
    config.params["append_video"] = settings.value("append_video", False, bool)
    config.params["auto_ajust"] = settings.value("auto_ajust", True, bool)

    if settings.value("clone_voicelist", ""):
        config.clone_voicelist = settings.value("clone_voicelist", "").split(',')

    config.params["chatgpt_model"] = settings.value("chatgpt_model", config.params['chatgpt_model'])
    config.params["localllm_model"] = settings.value("localllm_model", config.params['localllm_model'])
    config.params["zijiehuoshan_model"] = settings.value("zijiehuoshan_model", config.params['zijiehuoshan_model'])
    os.environ['OPENAI_API_KEY'] = config.params["chatgpt_key"]

    config.params["ttsapi_url"] = settings.value("ttsapi_url", "")
    config.params["ttsapi_extra"] = settings.value("ttsapi_extra", "pyvideotrans")
    config.params["ttsapi_voice_role"] = settings.value("ttsapi_voice_role", "")

    config.params["gptsovits_extra"] = settings.value("gptsovits_extra", "pyvideotrans")
    config.params["azure_model"] = settings.value("azure_model", config.params['azure_model'])

    config.params['translate_type'] = settings.value("translate_type", config.params['translate_type'])
    if config.params['translate_type'] == 'FreeChatGPT':
        config.params['translate_type'] = 'FreeGoogle'
    config.params['subtitle_type'] = settings.value("subtitle_type", config.params['subtitle_type'], int)
    config.proxy = settings.value("proxy", "", str)
    config.params['voice_rate'] = settings.value("voice_rate", config.params['voice_rate'].replace('%', '').replace('+', ''), str)
    config.params['cuda'] = settings.value("cuda", False, bool)
    config.params['only_video'] = settings.value("only_video", False, bool)
    config.params['tts_type'] = settings.value("tts_type", config.params['tts_type'], str) or 'edgeTTS'


def save_setting(settings: QSettings):
    for k, v in config.params.items():
        settings.setValue(k, v)
    settings.setValue("proxy", config.proxy)
    settings.setValue("voice_rate", config.params['voice_rate'].replace('%', '').replace('+', ''))
    settings.setValue("clone_voicelist", ','.join(config.clone_voicelist))

class DataBridge(QObject):
    # 定义信号
    checkbox_b_state_changed = Signal(bool)
    update_table = Signal(dict) # 音视频转文本添加文件的信号，用来更新我的创作页列表
    whisper_working = Signal(str,float)
    whisper_finished = Signal(str)

    def __init__(self):
        super().__init__()
        self._checkbox_b_state = False

    @property
    def checkbox_b_state(self):
        return self._checkbox_b_state

    @checkbox_b_state.setter
    def checkbox_b_state(self, value):
        if self._checkbox_b_state != value:
            self._checkbox_b_state = value
            self.checkbox_b_state_changed.emit(value)

    def emit_update_table(self, obj_format):
        config.logger.info('添加任务到列表')
        self.update_table.emit(obj_format)

    def emit_whisper_working(self, unid, progress:float):
        self.whisper_working.emit(unid, progress)

    def emit_whisper_finished(self, status:str):
        """
        Args:
            status: True 成功 False 失败
        """
        self.whisper_finished.emit(status)