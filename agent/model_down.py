#模型下载
from modelscope import snapshot_download
from nice_ui.configure import config
import os
from tqdm import tqdm


#模型下载-中文
def download_model(model_name: str, progress_callback=None):
    download_path = os.path.join(config.root_path, 'models', 'funasr')
    os.makedirs(download_path, exist_ok=True)

    class ProgressBar(tqdm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._current = 0

        def update(self, n):
            super().update(n)
            self._current += n
            if progress_callback:
                progress_callback(int(self._current / self.total * 100))

    with ProgressBar(unit='B', unit_scale=True, miniters=1, desc=model_name) as t:
        snapshot_download(f'iic/{model_name}', cache_dir=download_path)


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
