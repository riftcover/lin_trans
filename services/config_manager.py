#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块
负责加载和管理应用程序配置
"""

import logging
from typing import Dict, Any
from pathlib import Path

import yaml

# 获取logger
logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器类"""

    _instance = None  # 单例实例

    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_dir: str = None, env: str = None):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config文件夹
            env: 环境名称，默认从环境变量APP_ENV获取，如果未设置则使用配置文件中的default
        """
        # 避免重复初始化
        if getattr(self, '_initialized', False):
            return

        # 确定配置文件目录
        if config_dir is None:
            # 获取项目根目录
            root_dir = self._get_project_root()
            config_dir = root_dir / 'config'

        self.config_dir = Path(config_dir)

        # 确定当前环境
        if env is None:
            import os
            env = os.environ.get('APP_ENV')

        self.env = env
        self.configs = {}
        self._initialized = True

        # 加载API配置
        self.load_api_config()

    def _get_project_root(self) -> Path:
        """获取项目根目录

        Returns:
            Path: 项目根目录的路径
        """
        # 当前文件所在目录
        current_file = Path(__file__).resolve()
        # 项目根目录（假设utils是项目根目录的直接子目录）
        return current_file.parent.parent

    def load_api_config(self) -> Dict[str, Any]:
        """加载API配置

        Returns:
            Dict[str, Any]: API配置字典
        """
        api_config_path = self.config_dir / 'api_config.yaml'

        try:
            if not api_config_path.exists():
                logger.warning(f"API配置文件不存在: {api_config_path}")
                # 创建默认配置
                self._create_default_api_config(api_config_path)

            with open(api_config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 确定使用哪个环境的配置
            env = self.env
            if env is None or env not in config_data:
                # 如果未指定环境或指定的环境不存在，使用默认环境
                env = config_data.get('default', 'production')
                if env not in config_data:
                    # 如果默认环境也不存在，使用第一个环境
                    env = next(iter([k for k in config_data.keys() if k != 'default' and k != 'common']), None)
                    if env is None:
                        raise ValueError("配置文件中没有有效的环境配置")

            logger.info(f"使用环境: {env}")
            self.current_env = env

            # 获取环境特定的配置
            env_config = config_data[env]

            # 获取共享配置（如果存在）
            common_config = config_data.get('common', {})

            # 合并共享配置和环境特定配置（环境特定配置优先）
            api_config = {}
            api_config |= common_config
            api_config.update(env_config)  # 再添加环境特定配置（会覆盖同名项）

            # 处理web_paths（如果存在）
            if 'web_paths' in common_config and 'web_base_url' in env_config:
                # 创建web_urls字典
                web_urls = {'base_url': env_config['web_base_url']}

                # 添加web_paths中的路径
                for path_name, path in common_config['web_paths'].items():
                    web_urls[path_name] = path

                # 将web_urls添加到api_config
                api_config['web_urls'] = web_urls

            self.configs['api'] = api_config
            return api_config

        except Exception as e:
            logger.error(f"加载API配置失败: {e}")
            # 返回默认配置
            default_config = {
                'api_base_url': 'http://127.0.0.1:8000/api',
                'timeout': 15.0,
                'retry_attempts': 3,
                'retry_backoff': 0.5,
                'web_urls': {
                    'base_url': 'http://localhost:4000',
                    'forgot_password': '/forgot-password',
                    'register': '/register',
                    'terms': '/terms',
                    'privacy': '/privacy',
                    'help': '/help'
                }
            }
            self.configs['api'] = default_config
            return default_config

    def _create_default_api_config(self, config_path: Path) -> None:
        """创建默认API配置文件

        Args:
            config_path: 配置文件路径
        """
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            # 共享配置
            'common': {
                'timeout': 15.0,
                'retry_attempts': 3,
                'retry_backoff': 0.5,
                'web_paths': {
                    'forgot_password': '/forgot-password',
                    'register': '/register',
                    'terms': '/terms',
                    'privacy': '/privacy',
                    'help': '/help'
                },

            },

            # 高级翻译配置
            'translator': {
                'summary_length': 8000,
                'max_split_length': 20,
                'reflect_translate': True,
                'subtitle_max_length': 75,
                'target_multiplier': 1.2,
                'min_subtitle_duration': 2.5,
                'min_trim_duration': 3.5
            },
            # 环境特定配置 - 只包含URL
            'development': {
                'api_base_url': 'http://127.0.0.1:8000/api',
                'web_base_url': 'http://localhost:4000'
            },
            'production': {
                'api_base_url': 'http://123.57.206.182:8000/api',
                'web_base_url': 'http://www.example.com'
            },
            'default': 'development'
        }

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"已创建默认API配置文件: {config_path}")
        except Exception as e:
            logger.error(f"创建默认API配置文件失败: {e}")

    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置

        Returns:
            Dict[str, Any]: API配置字典
        """
        if 'api' not in self.configs:
            return self.load_api_config()
        return self.configs['api']

    def get_api_base_url(self) -> str:
        """获取API基础URL

        Returns:
            str: API基础URL
        """
        api_config = self.get_api_config()
        return api_config.get('api_base_url')
    
    def get_nlp_api_url(self) -> str:
        """获取NLP API URL

        Returns:
            str: NLP API URL
        """
        api_config = self.get_api_config()
        return api_config.get('nlp_api_url')

    def get_api_timeout(self) -> float:
        """获取API超时时间

        Returns:
            float: API超时时间（秒）
        """
        api_config = self.get_api_config()
        return api_config.get('timeout')

    def get_web_urls(self) -> Dict[str, str]:
        """获取网页URL配置

        Returns:
            Dict[str, str]: 网页URL配置字典
        """
        api_config = self.get_api_config()
        return api_config.get('web_urls')

    def get_web_url(self, url_name: str) -> str:
        """获取指定的网页URL

        Args:
            url_name: URL名称，如'forgot_password'

        Returns:
            str: 完整的URL地址
        """
        web_urls = self.get_web_urls()
        base_url = web_urls.get('base_url')

        if url_name == 'base_url':
            return base_url

        path = web_urls.get(url_name, '')
        if not path:
            return base_url

        # 确保路径以/开头
        if not path.startswith('/'):
            path = f'/{path}'

        return base_url + path

    def set_environment(self, env: str) -> None:
        """设置当前环境

        Args:
            env: 环境名称
        """
        if env != self.env:
            self.env = env
            # 重新加载配置
            self.load_api_config()
            logger.info(f"已切换到环境: {env}")

    def reload_configs(self) -> None:
        """重新加载所有配置"""
        self.load_api_config()
        logger.info("已重新加载所有配置")

    def get_translator_config(self) -> Dict[str, Any]:
        """获取高级翻译相关配置

        Returns:
            Dict[str, Any]: 翻译配置字典
        """
        api_config = self.get_api_config()
        return api_config.get('translator', {})
    
    def get_summary_length(self) -> int:
        """获取术语上下文最大长度

        Returns:
            int: 最大长度，默认8000
        """
        translator_config = self.get_translator_config()
        return translator_config.get('summary_length', 8000)
    
    def get_max_split_length(self) -> int:
        """获取最大分割长度

        Returns:
            int: 最大分割长度，默认20
        """
        translator_config = self.get_translator_config()
        return translator_config.get('max_split_length', 20)
    
    def get_reflect_translate(self) -> bool:
        """获取是否启用二次优化翻译

        Returns:
            bool: 是否启用二次优化，默认True
        """
        translator_config = self.get_translator_config()
        return translator_config.get('reflect_translate', True)
    
    def get_subtitle_max_length(self) -> int:
        """获取字幕行最大长度

        Returns:
            int: 字幕行最大长度，默认75
        """
        translator_config = self.get_translator_config()
        return translator_config.get('subtitle_max_length', 75)
    
    def get_target_multiplier(self) -> float:
        """获取目标语言文本长度乘数

        Returns:
            float: 目标语言乘数，默认1.2
        """
        translator_config = self.get_translator_config()
        return translator_config.get('target_multiplier', 1.2)
    
    def get_min_subtitle_duration(self) -> float:
        """获取最小字幕持续时间

        Returns:
            float: 最小字幕持续时间（秒），默认2.5
        """
        translator_config = self.get_translator_config()
        return translator_config.get('min_subtitle_duration', 2.5)
    
    def get_min_trim_duration(self) -> float:
        """获取最小修剪持续时间

        Returns:
            float: 最小修剪持续时间（秒），默认3.5
        """
        translator_config = self.get_translator_config()
        return translator_config.get('min_trim_duration', 3.5)

    def get_chunk_size(self):
        """获取每个块的字符数限制"""
        translator_config = self.get_translator_config()
        return translator_config.get('chunk_size', 600)

    def get_max_entries(self):
        """获取每个块的最大条目数"""
        translator_config = self.get_translator_config()
        return translator_config.get('max_entries', 10)
    
    def get_sleep_time(self):
        """翻译API调用间隔"""
        translator_config = self.get_translator_config()
        return translator_config.get('sleep_time', 1)
        



# 创建全局配置管理器实例
config_manager = ConfigManager()


# 导出便捷函数
def get_api_base_url() -> str:
    """获取API基础URL"""
    return config_manager.get_api_base_url()


def get_api_timeout() -> float:
    """获取API超时时间"""
    return config_manager.get_api_timeout()


def get_web_urls() -> Dict[str, str]:
    """获取网页URL配置"""
    return config_manager.get_web_urls()


def get_web_url(url_name: str) -> str:
    """获取指定的网页URL"""
    return config_manager.get_web_url(url_name)


def set_environment(env: str) -> None:
    """设置当前环境"""
    config_manager.set_environment(env)


def reload_configs() -> None:
    """重新加载所有配置"""
    config_manager.reload_configs()


# translator相关配置的便捷函数
def get_summary_length() -> int:
    """获取术语上下文最大长度"""
    return config_manager.get_summary_length()


def get_max_split_length() -> int:
    """获取最大分割长度"""
    return config_manager.get_max_split_length()


def get_reflect_translate() -> bool:
    """获取是否反思翻译结果"""
    return config_manager.get_reflect_translate()


def get_subtitle_max_length() -> int:
    """获取字幕最大长度"""
    return config_manager.get_subtitle_max_length()


def get_target_multiplier() -> float:
    """获取目标语言乘数"""
    return config_manager.get_target_multiplier()


def get_min_subtitle_duration() -> float:
    """获取最小字幕持续时间"""
    return config_manager.get_min_subtitle_duration()


def get_min_trim_duration() -> float:
    """获取最小修剪持续时间"""
    return config_manager.get_min_trim_duration()


def get_translator_config() -> Dict[str, Any]:
    """获取高级翻译相关配置"""
    return config_manager.get_translator_config()


def get_chunk_size() -> int:
    """获取每个块的字符数限制"""
    return config_manager.get_chunk_size()


def get_max_entries() -> int:
    """获取每个块的最大条目数"""
    return config_manager.get_max_entries()

def get_sleep_time() -> int:
    """翻译API调用间隔"""
    return config_manager.get_sleep_time()

if __name__ == '__main__':
    print(get_chunk_size())
    print(get_max_entries())
    print(get_sleep_time())
