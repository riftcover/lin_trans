import json
import os


def load_api_key_from_config(key: str) -> str:
    home_path = os.path.dirname(os.getcwd())

    with open(f'{home_path}/config.json', 'r') as file:
        config = json.load(file)
    if key not in config:
        raise KeyError(f"Key '{key}' not found in the configuration file.")
    return config.get(key)


if __name__ == '__main__':
    print(load_api_key_from_config('zhipu_key'))
