from typing import TypedDict, Dict

from PySide6.QtCore import QSettings


class AgentDict(TypedDict):
    key: str
    base_url: str
    model: str


AgentSettings = Dict[str, AgentDict]

qwen_msg: dict[str, str] = {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen2-57b-a14b-instruct"}

kimi_msg = {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"}


def agent_settings() -> AgentSettings:
    # todo 智普
    gui_settings = QSettings("Locoweed", "LinLInTrans")
    qwen_key = {"key": gui_settings.value("qwen")}
    qwen_msg.update(qwen_key)
    kimi_key = {"key": gui_settings.value("kimi")}
    kimi_msg.update(kimi_key)
    return {"qwen": qwen_msg, "kimi": kimi_msg}
