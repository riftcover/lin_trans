"""
应用设置模块

从 set.ini 文件加载应用配置，采用延迟加载策略。
"""
import re
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field
from utils import logger





class AppSettings(BaseModel):
    """
    应用设置模型
    
    从 set.ini 文件加载，提供类型安全的配置访问。
    """
    lang: str = "zh"
    dubbing_thread: int = 3
    trans_row: int = 40
    trans_sleep: int = 22
    agent_rpm: int = 2
    cuda_com_type: str = "float16"
    whisper_threads: int = 4
    whisper_worker: int = 1
    beam_size: int = 1
    best_of: int = 1
    vad: bool = True
    temperature: int = 1
    condition_on_previous_text: bool = False
    crf: int = 13
    video_codec: int = 264
    retries: int = 2
    separate_sec: int = 600
    audio_rate: float = 1.5
    video_rate: int = 20
    initial_prompt_zh: str = "Please break sentences correctly and retain punctuation"
    fontsize: int = 16
    fontname: str = "黑体"
    fontcolor: str = "&HFFFFFF"
    fontbordercolor: str = "&H000000"
    subtitle_bottom: int = 0
    voice_silence: int = 200
    interval_split: int = 6
    cjk_len: int = 24
    other_len: int = 36
    backaudio_volume: float = 0.5
    overall_silence: int = 2100
    overall_maxsecs: int = 3
    overall_threshold: float = 0.5
    overall_speech_pad_ms: int = 100
    remove_srt_silence: bool = False
    remove_silence: bool = True
    remove_white_ms: int = 100
    vsync: str = "passthrough"
    force_edit_srt: bool = True
    loop_backaudio: bool = False
    chattts_voice: str = "1111,2222,3333,4444,5555,6666,7777,8888,9999,4099,5099,6653,7869"
    cors_run: bool = True
    
    class Config:
        # 允许额外字段，保持灵活性
        extra = "allow"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于向后兼容"""
        return self.model_dump()


class SettingsLoader:
    """
    设置加载器
    
    负责从 set.ini 文件加载配置，采用延迟加载策略。
    """
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self._settings: Optional[AppSettings] = None
    
    def _parse_ini_file(self) -> Dict[str, Any]:
        """解析 set.ini 文件"""
        # 默认设置
        init_settings = AppSettings().to_dict()
        
        file = self.root_path / "nice_ui/set.ini"
        if not file.exists():
            return init_settings
        
        try:
            with file.open("r", encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    
                    # 跳过空行和注释
                    if not line or line.startswith(";") or line.startswith("#"):
                        continue
                    
                    # 解析键值对
                    if "=" not in line:
                        continue
                    
                    key, value = line.split("=", maxsplit=1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 类型转换
                    if re.match(r"^\d+$", value):
                        init_settings[key] = int(value)
                    elif re.match(r"^\d+\.\d+$", value):
                        init_settings[key] = round(float(value), 1)
                    elif value.lower() == "true":
                        init_settings[key] = True
                    elif value.lower() == "false":
                        init_settings[key] = False
                    else:
                        init_settings[key] = str(value.lower()) if value else ""
        
        except Exception as e:
            logger.error(f"set.ini 中有语法错误:{str(e)}")
        
        # 处理特殊情况：fontsize
        if (
            isinstance(init_settings.get("fontsize"), str)
            and "px" in init_settings["fontsize"]
        ):
            init_settings["fontsize"] = int(init_settings["fontsize"].replace("px", ""))
        
        return init_settings
    
    def get_settings(self) -> AppSettings:
        """获取设置（延迟加载）"""
        if self._settings is None:
            settings_dict = self._parse_ini_file()
            self._settings = AppSettings(**settings_dict)
        return self._settings
    
    def to_dict(self) -> Dict[str, Any]:
        """获取设置字典（用于向后兼容）"""
        return self.get_settings().to_dict()


# 全局加载器将在 config.py 中初始化
_settings_loader: Optional[SettingsLoader] = None


def get_settings_loader(root_path: Path) -> SettingsLoader:
    """获取设置加载器单例"""
    global _settings_loader
    if _settings_loader is None:
        _settings_loader = SettingsLoader(root_path)
    return _settings_loader

