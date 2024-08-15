#模型下载
from modelscope import snapshot_download
# paraformer-zh
# model_dir = snapshot_download('iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch')
# SenseVoiceSmall
# model_dir = snapshot_download('iic/SenseVoiceSmall')

#模型下载
model_dir = snapshot_download('iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch')