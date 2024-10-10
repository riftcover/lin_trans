#模型下载
from modelscope import snapshot_download
from nice_ui.configure import config
import os
import time
import threading

from utils import logger


#模型下载-中文
def download_model(model_name: str, progress_callback=None):
    logger.info(f"开始下载模型: {model_name}")
    download_path = os.path.join(config.funasr_model_path, model_name)
    temp_path = os.path.join(config.models_path, 'funasr', '._____temp', 'iic', model_name)
    logger.info(f"下载路径: {download_path}")
    model_dir = os.path.join(config.root_path, 'models', 'funasr')
    os.makedirs(download_path, exist_ok=True)
    """
    下载到funasr_model_path的iic目录下，
    由于下载时会自动创建一个iic目录，所以指定下载目录时需要拼接。
    在使用模型目录时，直接使用config.funasr_model_path即可。
    """
    vad_model_path = os.path.join(config.funasr_model_path, 'speech_fsmn_vad_zh-cn-16k-common-pytorch')
    if os.path.exists(vad_model_path):
        logger.info("vad模型已下载，跳过")
    else:
        logger.info("开始下载vad模型")
        snapshot_download('iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', cache_dir=download_path)
        logger.info("vad模型下载完成")

    start_time = time.time()
    #todo： 这里是多语言模型大小，其他两种没他大，并且相差不大就不改了
    total_size = 940016365  # 这是一个估计值，您可能需要根据实际情况调整
    last_downloaded_size = 0

    def check_download_progress():
        nonlocal total_size, last_downloaded_size
        current_size = 0
        # 因为.PT模型文件会先放在temp目录缓存，所以需要遍历两个目录
        for path in [download_path, temp_path]:
            for root, dirs, files in os.walk(path):
                for file in files:
                    current_size += os.path.getsize(os.path.join(root, file))
        if current_size > total_size:
            total_size = current_size
        logger.info(f"当前下载大小：{current_size}字节")
        if total_size > 0:
            progress = int((current_size / total_size) * 100)
            if progress_callback:
                progress_callback(progress)

        downloaded_size = current_size - last_downloaded_size
        last_downloaded_size = current_size
        logger.info(f"下载进度：{progress}%，已下载：{current_size}字节")

        return downloaded_size

    # 创建一个事件来控制进度检查线程
    stop_event = threading.Event()

    def progress_checker():
        while not stop_event.is_set():
            check_download_progress()
            time.sleep(1)  # 每秒检查一次进度

    # 启动进度检查线程
    progress_thread = threading.Thread(target=progress_checker)
    progress_thread.start()

    try:
        # 开始下载
        snapshot_download(f'iic/{model_name}', cache_dir=model_dir)
    finally:
        # 停止进度检查线程
        stop_event.set()
        progress_thread.join()

    # 确保进度达到100%
    if progress_callback:
        progress_callback(100)

    logger.info(f"模型 {model_name} 下载完成，用时 {time.time() - start_time:.2f} 秒")
    return download_path
