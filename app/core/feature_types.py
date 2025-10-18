"""
功能类型定义模块
"""
from typing import Literal


"""
功能键类型定义，
api key和云翻译都走cloud_trans，都走扣费流程，api key消费0，跳过扣分
"""
FeatureKey = Literal["cloud_trans", "asr_trans", "cloud_asr_trans", "cloud_asr"]

