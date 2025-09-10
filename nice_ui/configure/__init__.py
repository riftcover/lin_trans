from typing import Dict, TypedDict


class ModelInfo(TypedDict):
    status: int
    model_name: str

# {'云模型': {'status': 1, 'model_name': 'small.en'}, '中文模型': {'status': 302, 'model_name': 'speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch'}, '多语言模型': {'status': 303, 'model_name': 'SenseVoiceSmall'}}
ModelDict = Dict[str, ModelInfo]
