"""
语言数据模块

从语言配置文件加载语言和模型信息，采用延迟加载策略。
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from nice_ui.configure import ModelDict


class LanguageData:
    """
    语言数据加载器
    
    负责从语言JSON文件加载配置，采用延迟加载避免导入时副作用。
    """
    
    def __init__(self, root_path: Path, default_lang: str = "zh"):
        self.root_path = root_path
        self.default_lang = default_lang
        self._current_lang: Optional[str] = None
        self._obj: Optional[Dict[str, Any]] = None
    
    def _load_language_file(self, lang: str) -> Dict[str, Any]:
        """加载指定语言的配置文件"""
        lang_path = self.root_path / f"nice_ui/language/{lang}.json"
        
        # 如果文件不存在，回退到英语
        if not lang_path.exists():
            lang = "en"
            lang_path = self.root_path / f"nice_ui/language/{lang}.json"
        
        with lang_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def _ensure_loaded(self):
        """确保语言数据已加载"""
        if self._obj is None:
            self._current_lang = self.default_lang
            self._obj = self._load_language_file(self._current_lang)
    
    def set_language(self, lang: str):
        """设置当前语言"""
        if lang != self._current_lang:
            self._current_lang = lang
            self._obj = self._load_language_file(lang)
    
    @property
    def transobj(self) -> Dict[str, str]:
        """交互语言代码"""
        self._ensure_loaded()
        return self._obj["translate_language"]
    
    @property
    def uilanglist(self) -> Dict[str, str]:
        """软件界面语言"""
        self._ensure_loaded()
        return self._obj["ui_lang"]
    
    @property
    def langlist(self) -> Dict[str, str]:
        """语言显示名称:语言代码"""
        self._ensure_loaded()
        return self._obj["language_code_list"]
    
    @property
    def langnamelist(self) -> List[str]:
        """语言显示名称列表"""
        return list(self.langlist.keys())
    
    @property
    def model_list(self) -> ModelDict:
        """模型列表"""
        self._ensure_loaded()
        return self._obj["model_code_list"]
    
    @property
    def model_code_list(self) -> List[str]:
        """
        模型列表的key值
        
        example: ['多语言模型', '中文模型', '英语模型']
        """
        # TODO: 应该先读取本地安装的模型，然后修改model_list的值
        return [key.split(".")[0] for key in self.model_list.keys()]
    
    @property
    def box_lang(self) -> Dict[str, str]:
        """工具箱语言"""
        self._ensure_loaded()
        return self._obj["toolbox_lang"]


# 全局实例将在 config.py 中初始化
_language_data: Optional[LanguageData] = None


def get_language_data(root_path: Path, lang: str = "zh") -> LanguageData:
    """获取语言数据单例"""
    global _language_data
    if _language_data is None:
        _language_data = LanguageData(root_path, lang)
    return _language_data

