import os

from PySide6.QtCore import QSettings

from nice_ui.configure import config


def get_setting_cache(settings: QSettings):
    for k in config.params.keys():
        config.params[k] = settings.value(k, config.params[k])

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
    config.params["ttsapi_extra"] = settings.value("ttsapi_extra", "linlintrans")
    config.params["ttsapi_voice_role"] = settings.value("ttsapi_voice_role", "")

    config.params["gptsovits_extra"] = settings.value("gptsovits_extra", "pyvideotrans")
    config.params["azure_model"] = settings.value("azure_model", config.params['azure_model'])

    config.params['translate_channel'] = settings.value("translate_channel", config.params['translate_channel'])
    if config.params['translate_channel'] == 'FreeChatGPT':
        config.params['translate_channel'] = 'FreeGoogle'
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
