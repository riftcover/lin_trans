import datetime
import os
import sys

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
        # 项目路径下创建log目录保存日志文件
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(app_root, "logs")  # 拼接指定路径
        # 判断目录是否存在，不存在则创建新的目录
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        self.logger.configure(handlers=[{"sink": sys.stderr, "level": "TRACE"},
                                        {"sink": f'{log_path}/{DATE}.log', "level": "TRACE", "rotation": "1 day",
                                         "retention": 1, "encoding": 'utf-8', "backtrace": True, "diagnose": True,
                                         "enqueue": True}])

