import os

import yaml

from utils.config_manager import ConfigManager


def init_config_key() -> dict:
    config_manager = ConfigManager()

    # 获取当前配置
    api_config_path = os.path.join(config_manager.config_dir, 'key_config.yaml')

    with open(api_config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    return config_data


init_config = init_config_key()


def load_key(feat, key) -> str:
    a = init_config.get(feat)
    return a.get(key)


if __name__ == '__main__':
    print(load_key('spacy_model_map', 'en'))
