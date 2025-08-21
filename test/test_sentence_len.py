# 测试不同类型的文本
from utils.file_utils import split_sentence

texts = [
    "Picture a winter wonderland",  # 纯英文
    "你好世界",                     # 纯中文
    "Hello 你好 world",            # 混合文本
    "COVID-19 疫情防控"            # 数字+中英混合
]

for text in texts:
    words = split_sentence(text)
    print(f"'{text}' → {words} → length={len(words)}")