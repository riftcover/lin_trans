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

        # 获取应用程序根目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            app_root = Path(sys.executable).parent
        else:
            # 如果是开发环境
            app_root = Path(__file__).parent.parent

        # 创建日志目录
        log_path = app_root / "logs"
        log_path.mkdir(parents=True, exist_ok=True)

        # 配置日志
        log_file = log_path / f"{DATE}.log"
        self.logger.configure(handlers=[
            # {"sink": sys.stderr, "level": "TRACE"},
            {"sink": str(log_file),
             "level": "TRACE",
             "rotation": "1 day",
             "retention": "1 week",
             "encoding": 'utf-8',
             "backtrace": True,
             "diagnose": True,
             "enqueue": True}
        ])

        # 添加一条日志，确认日志系统已经初始化
        self.logger.info("日志系统已初始化")

    def get_logger(self):
        return self.logger
