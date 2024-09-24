#模型下载
from modelscope import snapshot_download
from nice_ui.configure import config
import os


#模型下载-中文
def download_model(model_name:str):
    download_path = os.path.join(config.root_path, 'models', 'funasr')
    os.makedirs(download_path, exist_ok=True)
    snapshot_download(model_name,cache_dir=download_path)

download_model('iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch')

# #模型下载-英语
#
# model_dir = snapshot_download('iic/speech_paraformer-large-vad-punc_asr_nat-en-16k-common-vocab10020')
#
# #模型下载-全语言
# model_dir = snapshot_download('iic/SenseVoiceSmall')