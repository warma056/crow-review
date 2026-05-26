# 模块用途：读写用户配置文件（API Key 等）
# 打包后保存到 exe 所在目录，确保数据持久化

import json
import os
import sys


def _get_app_dir() -> str:
    """
    获取数据存储目录：
    - 打包为 exe 时：exe 文件所在目录
    - 直接运行 py 时：项目根目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，exe 所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发模式，项目根目录
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')


def _get_config_path() -> str:
    return os.path.join(_get_app_dir(), 'config.json')


DEFAULT_CONFIG = {
    "api_key": "",
    "judge_mode": "strict"
}


def load_config() -> dict:
    path = _get_config_path()
    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for key, val in DEFAULT_CONFIG.items():
            if key not in data:
                data[key] = val
        return data
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> bool:
    try:
        with open(_get_config_path(), 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_api_key() -> str:
    return load_config().get("api_key", "")


def set_api_key(key: str) -> bool:
    config = load_config()
    config["api_key"] = key.strip()
    return save_config(config)
