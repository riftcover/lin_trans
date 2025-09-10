import functools
import time
from utils import logger


def except_handler(error_msg: str, retry: int = 0, delay: float = 1, default_return=None):
    """
    异常处理装饰器，提供重试机制
    
    Args:
        error_msg: 错误消息前缀
        retry: 重试次数
        delay: 重试延迟时间（秒），每次重试会指数增长
        default_return: 失败时的默认返回值
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for i in range(retry + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"{error_msg}: {e}, retry: {i+1}/{retry}")
                    if i == retry:
                        if default_return is not None:
                            return default_return
                        raise last_exception
                    # 指数退避延迟
                    time.sleep(delay * (2**i))
            return None
        return wrapper
    return decorator


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"{func.__name__} completed in {elapsed_time:.2f} seconds")
        return result

    return wrapper