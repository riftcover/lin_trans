"""
任务参数模块

管理运行时任务参数，这些参数会在UI交互中被修改。
"""
from pathlib import Path
from typing import Dict, Any, List

from pydantic import BaseModel, Field


class TaskParams(BaseModel):
    """
    任务参数模型
    
    这些参数在运行时会被UI修改，代表当前任务的配置。
    """
    source_mp4: str = ""
    target_dir: Path = Field(default_factory=lambda: Path("result"))
    output_dir: str = ""
    source_language_code: str = "en"
    source_language: str = "英文"
    source_module_status: int = 302
    source_module_name: str = "small"
    source_module_key: str = "中文模型"
    detect_language: str = "en"
    translate_status: bool = False
    target_language: str = "中文"
    translate_channel: str = "通义千问"
    subtitle_language: str = "chi"
    prompt_name: str = "默认"
    prompt_text: str = ""
    cuda: bool = False
    is_separate: bool = False
    voice_role: str = "No"
    voice_rate: str = "0"
    tts_type: str = "edgeTTS"
    tts_type_list: List[str] = Field(default_factory=lambda: [
        "edgeTTS",
        "ChatTTS",
        "gtts",
        "AzureTTS",
        "GPT-SoVITS",
        "clone-voice",
        "openaiTTS",
        "elevenlabsTTS",
        "TTS-API",
    ])
    only_video: bool = False
    subtitle_type: int = 0
    voice_autorate: bool = False
    auto_ajust: bool = True
    
    # 额外的运行时参数（从 setting_cache.py 中发现的）
    video_autorate: bool = False
    append_video: bool = False
    ttsapi_url: str = ""
    ttsapi_extra: str = "linlintrans"
    ttsapi_voice_role: str = ""
    gptsovits_extra: str = "pyvideotrans"
    
    class Config:
        # 允许额外字段
        extra = "allow"
        # 允许任意类型（Path等）
        arbitrary_types_allowed = True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典，用于向后兼容

        注意：Path 对象保持为 Path 类型（不转换为字符串）
        """
        data = self.model_dump()
        # target_dir 保持为 Path 对象，因为代码中很多地方依赖 Path 的方法
        return data


class MutableDict(dict):
    """
    可变字典包装器
    
    允许像普通字典一样修改，同时保持与 Pydantic 模型的同步。
    这是为了向后兼容 config.params["key"] = value 的写法。
    """
    
    def __init__(self, model: TaskParams):
        self._model = model
        super().__init__(model.to_dict())
    
    def __setitem__(self, key, value):
        """设置值时同步到模型"""
        super().__setitem__(key, value)
        # 同步到模型（如果字段存在）
        if hasattr(self._model, key):
            setattr(self._model, key, value)
    
    def __getitem__(self, key):
        """获取值时从模型同步"""
        if hasattr(self._model, key):
            value = getattr(self._model, key)
            # 更新字典中的值
            super().__setitem__(key, value)
            return value
        return super().__getitem__(key)
    
    def get(self, key, default=None):
        """支持 get 方法"""
        try:
            return self[key]
        except KeyError:
            return default
    
    def keys(self):
        """返回所有键"""
        # 合并模型字段和字典键
        model_keys = set(self._model.model_fields.keys())
        dict_keys = set(super().keys())
        return model_keys | dict_keys
    
    def values(self):
        """返回所有值"""
        return [self[k] for k in self.keys()]
    
    def items(self):
        """返回所有键值对"""
        return [(k, self[k]) for k in self.keys()]


def create_task_params(root_path: Path) -> MutableDict:
    """
    创建任务参数实例

    返回一个可变字典，支持向后兼容的访问方式。
    """
    target_dir = root_path / "result"
    model = TaskParams(target_dir=target_dir)
    return MutableDict(model)

