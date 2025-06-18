#!/usr/bin/env python3
"""
翻译 - 快速开始示例
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.enhanced_common_agent import translate_document


def quick_translation_example():
    """最简单的翻译示例"""

    # 基本参数配置
    translate_document(
        unid="f92f54737832bee014ec51e4a8b523cb",  # 任务ID
        in_document=r"D:\dcode\lin_trans\result\f92f54737832bee014ec51e4a8b523cb\44.srt",  # 输入文件路径
        out_document=r"D:\dcode\lin_trans\result\f92f54737832bee014ec51e4a8b523cb\44_cn.srt",  # 输出文件路径
        agent_name="qwen_cloud",  # AI模型（确保在agent_dict中已配置）
        chunk_size=600,  # 推荐值：600-800
        max_entries=10,  # 推荐值：8-12
        sleep_time=1,  # API调用间隔
        target_language="中文",  # 目标语言
        source_language="English"  # 源语言
    )


if __name__ == "__main__":
    quick_translation_example()
