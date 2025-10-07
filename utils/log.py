import os
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger


def _get_log_dir() -> Path:
    """获取日志目录路径。开发环境用项目目录，打包环境用用户数据目录。"""
    if getattr(sys, 'frozen', False):
        # 打包环境：用户数据目录
        if sys.platform == "win32":
            base = Path(os.environ.get('LOCALAPPDATA', Path.home()))
        else:
            base = Path.home()
        return base / ".lappedAI" / "logs"

    # 开发环境：项目目录
    return Path(__file__).parent.parent / "logs"


def _setup_logger():
    """配置 loguru logger。只调用一次。"""
    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime('%Y-%m-%d')

    handlers = [
        {
            "sink": log_dir / f"{date}.log",
            "level": "TRACE",
            "rotation": "1 day",
            "retention": "1 day",
            "encoding": "utf-8",
            "backtrace": True,
            "diagnose": True,
        },
        {
            "sink": log_dir / f"error_{date}.log",
            "level": "ERROR",
            "rotation": "1 day",
            "retention": "1 day",
            "encoding": "utf-8",
            "backtrace": True,
            "diagnose": True,
        },
    ]

    # 只在非打包环境下添加控制台输出
    # 打包后的可执行文件不需要控制台日志
    if not getattr(sys, 'frozen', False):
        handlers.append({
            "sink": sys.stderr,
            "level": "TRACE",
            "colorize": True,
        })

    logger.configure(handlers=handlers)


# 初始化
_setup_logger()

if __name__ == '__main__':
    print(_get_log_dir())
