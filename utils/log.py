import datetime
import os
import sys
from pathlib import Path

from loguru import logger


class Logings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 文件名称，按天创建
        DATE = datetime.datetime.now().strftime('%Y-%m-%d')
        self.logger = logger

        if sys.platform == "win32":
            # Windows: 使用LOCALAPPDATA目录
            user_data_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
            app_root = user_data_dir / "lappedAI"
        else:
            # Linux/macOS: 使用用户主目录下的隐藏文件夹
            app_root = Path.home() / ".lappedAI"

        # 获取应用程序根目录
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件，使用用户数据目录避免权限问题
            if sys.platform == "win32":
                # Windows: 使用LOCALAPPDATA目录
                user_data_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')))
                app_root = user_data_dir / "lappedAI"
            else:
                # Linux/macOS: 使用用户主目录下的隐藏文件夹
                app_root = Path.home() / ".lappedAI"
        else:
            # 开发环境，使用项目目录
            app_root = Path(__file__).parent.parent

        # 创建日志目录
        log_path = app_root / "logs"
        log_path.mkdir(parents=True, exist_ok=True)

        # 配置日志
        log_file = log_path / f"{DATE}.log"
        error_file = log_path / f"error_{DATE}.log"

        handlers = [
            {"sink": str(log_file),
             "level": "TRACE",
             "rotation": "1 day",
             "retention": "1 day",  # 只保留1天的日志
             "encoding": 'utf-8',
             "backtrace": True,
             "diagnose": True,
            },
            {"sink": str(error_file),
             "level": "ERROR",
             "rotation": "1 day",
             "retention": "1 day",  # 错误日志也只保留1天
             "encoding": 'utf-8',
             "backtrace": True,
             "diagnose": True,
             }
        ]

        # 始终尝试添加控制台日志处理器（包括打包后的可执行文件）
        try:
            if sys.stderr is not None:
                handlers.append({"sink": sys.stderr, "level": "TRACE", "colorize": True})
        except Exception:
            pass

        self.logger.configure(handlers=handlers)

    def get_logger(self):
        return self.logger
