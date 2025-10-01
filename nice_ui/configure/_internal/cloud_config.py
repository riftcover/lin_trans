"""
云服务配置模块

管理云服务相关的配置，包括加密凭证的加载。
"""
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

# 延迟导入，避免循环依赖
try:
    from utils import logger
    from utils.crypto_utils import crypto_utils
except ImportError:
    # 如果依赖不可用，使用后备方案
    class FallbackLogger:
        @staticmethod
        def error(msg):
            print(f"ERROR: {msg}")
    logger = FallbackLogger()
    crypto_utils = None


class PplSdkConfig(BaseModel):
    """PPL SDK 配置"""
    aki: str = ""
    aks: str = ""
    region: str = "cn-beijing"
    bucket: str = "asr-file-tth"
    asr_api_key: str = ""
    asr_model: str = "paraformer-v2"
    gladia_api_key: str = ""


class CloudConfig(BaseModel):
    """云服务配置"""
    ppl_sdk: PplSdkConfig


class CloudConfigLoader:
    """
    云服务配置加载器
    
    负责从加密文件加载云服务凭证，采用延迟加载策略。
    """
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self._config: Optional[CloudConfig] = None
    
    def _load_cloud_config(self) -> Optional[CloudConfig]:
        """
        获取云服务配置

        优先从加密文件加载，如果不存在则使用环境变量
        """
        # 如果 crypto_utils 不可用，返回 None
        if crypto_utils is None:
            return None

        try:
            # 初始化加密工具
            crypto_utils.initialize()

            # 获取凭证文件路径
            credentials_file = crypto_utils.get_credentials_file_path(self.root_path)

            # 如果凭证文件存在，从文件中加载
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
    
    def get_config(self) -> Optional[CloudConfig]:
        """获取云配置（延迟加载）"""
        if self._config is None:
            self._config = self._load_cloud_config()
        return self._config


# 全局加载器将在 config.py 中初始化
_cloud_config_loader: Optional[CloudConfigLoader] = None


def get_cloud_config_loader(root_path: Path) -> CloudConfigLoader:
    """获取云配置加载器单例"""
    global _cloud_config_loader
    if _cloud_config_loader is None:
        _cloud_config_loader = CloudConfigLoader(root_path)
    return _cloud_config_loader

