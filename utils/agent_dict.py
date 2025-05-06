from typing import Dict, Optional, ClassVar, TypedDict, Union
from pydantic import BaseModel, Field

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from app.cloud_asr import aliyun_sdk

class AgentConfig(BaseModel):
    """
    AI代理配置模型

    定义了AI代理的基本配置信息，包括密钥、基础URL和模型名称
    """
    key: Optional[str] = Field(None, description="API密钥")
    base_url: str = Field(..., description="API基础URL")
    model: str = Field(..., description="使用的模型名称")


class AgentRegistry(BaseModel):
    """
    AI代理注册表

    管理所有支持的AI代理配置
    """
    # 预定义的配置
    QWEN_CLOUD_BASE_URL: ClassVar[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_CCLOUD_MODEL: ClassVar[str] = "qwen-plus"
    QWEN_CCLOUD_KEY: ClassVar[str] = aliyun_sdk.asr_api_key

    QWEN_BASE_URL: ClassVar[str] = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: ClassVar[str] = "qwen-plus"

    KIMI_BASE_URL: ClassVar[str] = "https://api.moonshot.cn/v1"
    KIMI_MODEL: ClassVar[str] = "moonshot-v1-8k"

    ZHIPU_BASE_URL: ClassVar[str] = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_MODEL: ClassVar[str] = "glm-4"

    # 存储所有代理配置
    agents: Dict[str, AgentConfig] = Field(default_factory=dict, description="所有AI代理的配置字典")

    def __init__(self):
        """初始化代理注册表并设置默认配置"""
        super().__init__()
        # 初始化默认配置
        self.agents = {
            "qwen_cloud": AgentConfig(base_url=self.QWEN_CLOUD_BASE_URL, model=self.QWEN_CCLOUD_MODEL, key=self.QWEN_CCLOUD_KEY),
            "qwen": AgentConfig(base_url=self.QWEN_BASE_URL, model=self.QWEN_MODEL,key =None),
            "kimi": AgentConfig(base_url=self.KIMI_BASE_URL, model=self.KIMI_MODEL,key =None),
            "zhipu": AgentConfig(base_url=self.ZHIPU_BASE_URL, model=self.ZHIPU_MODEL,key =None)
        }

    def _find_main_window(self):
        """查找主窗口实例

        Returns:
            主窗口实例或None
        """
        for widget in QApplication.topLevelWidgets():
            if widget.objectName() == "MainWindow":
                return widget
        return None

    def load_keys_from_settings(self, settings: Optional[QSettings] = None) -> None:
        """从用户设置中加载API密钥

        Args:
            settings: 可选的QSettings实例，如果提供则使用该实例，否则尝试从MainWindow获取
        """
        # 如果没有提供settings，尝试从MainWindow获取，如果失败则创建新的实例
        if settings is None:
            # 尝试从MainWindow获取settings
            main_window = self._find_main_window()
            if main_window and hasattr(main_window, 'settings'):
                settings = main_window.settings
            else:
                settings = QSettings("Locoweed3", "LinLInTrans")

        # 加载各AI服务的API密钥
        for agent_name in self.agents.keys():
            if key_value := settings.value(agent_name):
                self.agents[agent_name].key = key_value

    def get_all_configs(self, settings: Optional[QSettings] = None) -> Dict[str, AgentConfig]:
        """获取所有已加载密钥的代理配置

        Args:
            settings: 可选的QSettings实例，如果提供则使用该实例

        Returns:
            Dict[str, AgentConfig]: 所有代理配置的字典
        """
        self.load_keys_from_settings(settings)
        return self.agents


def agent_settings(settings: Optional[QSettings] = None) -> dict[str, AgentConfig]:
    """
    获取所有AI代理的配置

    为了保持与旧代码的兼容性，返回字典格式的配置

    Args:
        settings: 可选的QSettings实例，如果提供则使用该实例，否则尝试从MainWindow获取

    Returns:
        AgentSettings: 所有AI代理的配置字典，兼容旧代码的类型
    """
    registry = AgentRegistry()
    return registry.get_all_configs(settings)
agent_msg = agent_settings()

if __name__ == '__main__':
    print(agent_msg)
