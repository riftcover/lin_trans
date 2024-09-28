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
    download_path = os.path.join(config.root_path, 'models', 'funasr', 'iic', model_name)
    os.makedirs(download_path, exist_ok=True)

    start_time = time.time()
    #todo： 这里是多语言模型大小，其他两种没他大，并且相差不大就不改了
    total_size = 940016365  # 这是一个估计值，您可能需要根据实际情况调整
    last_downloaded_size = 0

    def check_download_progress():
        nonlocal total_size, last_downloaded_size
        current_size = 0
        for root, dirs, files in os.walk(download_path):
            for file in files:
                current_size += os.path.getsize(os.path.join(root, file))
        if current_size > total_size:
            total_size = current_size

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
        snapshot_download(f'iic/{model_name}', cache_dir=download_path)
    finally:
        # 停止进度检查线程
        stop_event.set()
        progress_thread.join()

    # 确保进度达到100%
    if progress_callback:
        progress_callback(100)

    logger.info(f"模型 {model_name} 下载完成，用时 {time.time() - start_time:.2f} 秒")
    return download_path


# download_model('iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch')

# #模型下载-英语
#
# model_dir = snapshot_download('iic/speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020')
#
# #模型下载-全语言
# model_dir = snapshot_download('iic/SenseVoiceSmall')
if __name__ == '__main__':
    # model_info = config.model_list.get('多语言模型', {})
    # print(config.model_list)
    # print(model_info)
    download_model('SenseVoiceSmall')
