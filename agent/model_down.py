#模型下载
import os
import sys
import time
from contextlib import contextmanager
from io import StringIO

from modelscope import snapshot_download

from nice_ui.configure import config
from utils import logger


@contextmanager
def suppress_console_output():
    """
    抑制控制台输出（开发环境和打包环境都禁用）
    用于屏蔽 modelscope 下载时的进度条输出
    """
    # 重定向所有输出到空设备
    devnull = StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = devnull
        sys.stderr = devnull
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


#模型下载-中文
def download_model(model_name: str, progress_callback=None):
    logger.info(f"开始下载模型: {model_name}")
    download_path = os.path.join(config.funasr_model_path, model_name)
    temp_path = os.path.join(config.models_path, 'funasr', '._____temp', 'iic', model_name)
    funasr_parent_path = os.path.join(config.models_path, 'funasr')
    logger.info(f"下载路径: {download_path}")
    model_dir = os.path.join(config.models_path, 'funasr')
    os.makedirs(download_path, exist_ok=True)
    """
    下载到funasr_model_path的iic目录下，
    由于下载时会自动创建一个iic目录，所以指定下载目录时需要拼接。
    在使用模型目录时，直接使用config.funasr_model_path即可。
    """
    vad_model_path = os.path.join(config.funasr_model_path, 'speech_fsmn_vad_zh-cn-16k-common-pytorch')
    punc_model_path = os.path.join(config.funasr_model_path, 'punc_ct-transformer_cn-en-common-vocab471067-large')
    spk_model_path = os.path.join(config.funasr_model_path, 'speech_campplus_sv_zh-cn_16k-common')
    fa_zh_path = f'{config.funasr_model_path}/speech_timestamp_prediction-v1-16k-offline'
    # 进度监控由调用方（DownloadThread）负责
    logger.info(f"开始下载模型: {model_name}")

    if os.path.exists(vad_model_path):
        logger.info("vad模型已下载，跳过")
    else:
        logger.info("开始下载vad模型")
        with suppress_console_output():
            snapshot_download('iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', cache_dir=model_dir)
        logger.info("vad模型下载完成")

    if os.path.exists(punc_model_path):
        logger.info("标点模型已下载，跳过")
    else:
        logger.info("开始下载标点模型")
        with suppress_console_output():
            snapshot_download('iic/punc_ct-transformer_cn-en-common-vocab471067-large', cache_dir=model_dir)
        logger.info("标点模型下载完成")

    if os.path.exists(spk_model_path):
        logger.info("说话人模型已下载，跳过")
    else:
        logger.info("开始下载说话人模型")
        with suppress_console_output():
            snapshot_download('iic/speech_campplus_sv_zh-cn_16k-common', cache_dir=model_dir)
        logger.info("说话人模型下载完成")

    if os.path.exists(fa_zh_path):
        logger.info("fa_zh模型已下载，跳过")
    else:
        logger.info("开始下载fa_zh模型")
        with suppress_console_output():
            snapshot_download('iic/speech_timestamp_prediction-v1-16k-offline', cache_dir=model_dir)
        logger.info("fa_zh模型下载完成")

    logger.info("开始下载zn模型")
    with suppress_console_output():
        snapshot_download(f'iic/{model_name}', cache_dir=model_dir)
    # logger.info(f"模型 {model_name} 下载完成，用时 {time.time() - start_time:.2f} 秒")
    return download_path


def calculate_directory_size(directory_path):
    """
    计算目录总大小（供外部调用）

    Args:
        directory_path: 目录路径

    Returns:
        int: 目录总大小（字节）
    """
    total_size = 0
    try:
        if os.path.exists(directory_path):
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
    except Exception as e:
        logger.warning(f"计算目录大小时出错: {e}")
    return total_size
