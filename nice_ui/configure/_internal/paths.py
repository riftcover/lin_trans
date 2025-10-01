"""
路径配置模块

管理所有应用程序路径，采用延迟初始化策略避免导入时副作用。
"""
import os
import sys
from pathlib import Path
from typing import Optional


def get_executable_path() -> str:
    """获取可执行文件所在目录"""
    if getattr(sys, "frozen", False):
        # 打包后的可执行文件
        return os.path.dirname(sys.executable).replace("\\", "/")
    else:
        return str(Path.cwd()).replace("\\", "/")


class PathConfig:
    """
    路径配置类
    
    所有路径采用延迟初始化，只在首次访问时创建目录。
    这避免了导入时的副作用。
    """
    
    def __init__(self):
        self._initialized = False
        self._rootdir: Optional[str] = None
        self._root_path: Optional[Path] = None
        self._root_same: Optional[Path] = None
        self._models_path: Optional[Path] = None
        self._funasr_model_path: Optional[Path] = None
        self._temp_path: Optional[Path] = None
        self._TEMP_DIR: Optional[str] = None
        self._homepath: Optional[Path] = None
        self._homedir: Optional[str] = None
        self._TEMP_HOME: Optional[str] = None
        self._result_path: Optional[Path] = None
        self._sys_platform: Optional[str] = None
    
    def _ensure_initialized(self):
        """确保路径已初始化"""
        if not self._initialized:
            self._initialize_paths()
            self._initialized = True
    
    def _initialize_paths(self):
        """初始化所有路径（延迟执行）"""
        # 基础路径
        self._rootdir = get_executable_path()
        self._root_path = Path(__file__).parent.parent.parent.parent
        self._sys_platform = sys.platform
        
        # 模型路径
        self._root_same = Path(__file__).parent.parent.parent.parent.parent
        self._models_path = self._root_same / "models"
        
        # 临时路径
        self._temp_path = self._root_path / "tmp"
        
        # 用户主目录
        self._homepath = Path.home() / "Videos/lapped"
        self._homedir = self._homepath.as_posix()
        
        # 结果路径
        self._result_path = self._root_path / "result"
    
    def _ensure_directory(self, path: Path) -> Path:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def rootdir(self) -> str:
        """可执行文件所在目录"""
        self._ensure_initialized()
        return self._rootdir
    
    @property
    def root_path(self) -> Path:
        """项目根目录"""
        self._ensure_initialized()
        return self._root_path
    
    @property
    def sys_platform(self) -> str:
        """系统平台"""
        self._ensure_initialized()
        return self._sys_platform
    
    @property
    def models_path(self) -> Path:
        """模型存储路径"""
        self._ensure_initialized()
        return self._models_path
    
    @models_path.setter
    def models_path(self, value):
        """允许动态设置模型路径"""
        self._models_path = Path(value) if not isinstance(value, Path) else value
    
    @property
    def funasr_model_path(self) -> Path:
        """FunASR模型路径（访问时自动创建）"""
        self._ensure_initialized()
        path = self._models_path / "funasr" / "iic"
        return self._ensure_directory(path)
    
    def update_funasr_path(self) -> Path:
        """
        更新FunASR路径（兼容旧API）
        
        这个方法保持向后兼容，实际上现在通过属性访问自动处理。
        """
        return self.funasr_model_path
    
    @property
    def temp_path(self) -> Path:
        """临时文件路径"""
        self._ensure_initialized()
        return self._ensure_directory(self._temp_path)
    
    @property
    def TEMP_DIR(self) -> str:
        """临时目录（字符串格式）"""
        return self.temp_path.as_posix()
    
    @property
    def homepath(self) -> Path:
        """用户主目录路径"""
        self._ensure_initialized()
        return self._ensure_directory(self._homepath)
    
    @property
    def homedir(self) -> str:
        """用户主目录（字符串格式）"""
        return self.homepath.as_posix()
    
    @property
    def TEMP_HOME(self) -> str:
        """临时主目录"""
        temp_home = f"{self.homedir}/tmp"
        Path(temp_home).mkdir(parents=True, exist_ok=True)
        return temp_home
    
    @property
    def result_path(self) -> Path:
        """结果输出路径"""
        self._ensure_initialized()
        return self._result_path


# 创建全局单例
_path_config = PathConfig()

