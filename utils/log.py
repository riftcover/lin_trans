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
        log_path = os.path.join(os.path.dirname(os.getcwd()), "logs")  # 拼接指定路径
        # 判断目录是否存在，不存在则创建新的目录
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        self.logger.configure(handlers=[{"sink": sys.stderr, "level": "TRACE"},
                                        {"sink": f'{log_path}/{DATE}.log', "level": "TRACE", "rotation": "1 day",
                                         "retention": 1, "encoding": 'utf-8', "backtrace": True, "diagnose": True,
                                         "enqueue": True}])


if __name__ == '__main__':
    logger = Logings().logger
    logger.trace("这是一条追踪日志")
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.success("这是一条成功日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")
