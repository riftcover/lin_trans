import time
from functools import wraps

from utils.log import Logings

logger = Logings().logger


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"{func.__name__} completed in {elapsed_time:.2f} seconds")
        return result

    return wrapper
