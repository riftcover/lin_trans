import os,sys
import datetime

from loguru import logger


class Logings:
    def __init__(self):
        #__instance = None
        # 文件名称，按天创建.
        DATE = datetime.datetime.now().strftime('%Y-%m-%d')
        print(DATE)
        self.logger =logger
        # 项目路径下创建log目录保存日志文件
        logpath = os.path.join(os.path.dirname(os.getcwd()), "logs")  # 拼接指定路径
        print(logpath)
        # 判断目录是否存在，不存在则创建新的目录
        if not os.path.isdir(logpath): os.makedirs(logpath)
        self.logger.remove()  # 删去import logger之后自动产生的handler，不删除的话会出现重复输出的现象
        handler_id = self.logger.add(sys.stderr, level="INFO")  # 控制台日志级别
        self.logger.add('%s/%s.log' % (logpath, DATE),   # 指定文件
                   #format="{time:YYYY-MM-DD HH:mm:ss}  | {level}> {elapsed}  | {message}",
                   encoding='utf-8',
                   retention='1 days',  # 设置历史保留时长
                   backtrace=True,  # 回溯
                   diagnose=True,   # 诊断
                   enqueue=True,   # 异步写入
                   filter="",  # 过滤器
                   level="INFO" # 过滤级别
                   # rotation="5kb",  # 切割，设置文件大小，rotation="12:00"，rotation="1 week"
                   # filter="my_module"  # 过滤模块
                   # compression="zip"   # 文件压缩
                  )



if __name__ == '__main__':
    logs = Logings()
    logger.debug("这是一条debug日志")
    logger.info("这是一条info日志")
    logger.error("error{}" ,233)