#!/usr/bin/env python3
"""
VideoLingo翻译 - 快速开始示例
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.enhanced_common_agent import translate_document_videolingo


def quick_translation_example():
    """最简单的翻译示例"""
    
    # 基本参数配置
    translate_document_videolingo(
        unid="quick_start_001",                    # 任务ID
        in_document=r"D:\dcode\lin_trans\result\f92f54737832bee014ec51e4a8b523cb\44.srt",                   # 输入文件路径
        out_document=r"D:\dcode\lin_trans\result\f92f54737832bee014ec51e4a8b523cb\44_cn.srt",                 # 输出文件路径
        agent_name="qwen",                         # AI模型（确保在agent_dict中已配置）
        chunk_size=600,                            # 推荐值：600-800
        max_entries=10,                            # 推荐值：8-12
        sleep_time=1,                              # API调用间隔
        max_workers=3,                             # 并发线程数
        target_language="中文",                    # 目标语言
        source_language="English"                  # 源语言
    )


def custom_translation_example():
    """自定义参数的翻译示例"""
    
    # 技术内容翻译配置
    translate_document_videolingo(
        unid="tech_translation",
        in_document="technical_video.srt",
        out_document="technical_video_cn.srt",
        agent_name="qwen",
        chunk_size=800,          # 增大以获得更好上下文
        max_entries=8,           # 减少以提高质量
        sleep_time=2,            # 增加间隔避免限流
        max_workers=2,           # 减少并发提高稳定性
        target_language="中文（简体）",
        source_language="English"
    )


def main(choice: int):
    """选择运行哪个示例"""
    print("VideoLingo翻译快速开始")
    print("1. 基本翻译示例")
    print("2. 自定义翻译示例")
    
    try:
        
        if choice == "1":
            print("运行基本翻译示例...")
            quick_translation_example()
            print("✅ 基本翻译完成")
            
        elif choice == "2":
            print("运行自定义翻译示例...")
            custom_translation_example()
            print("✅ 自定义翻译完成")
            
        else:
            print("无效选择，运行基本示例...")
            quick_translation_example()
            
    except KeyboardInterrupt:
        print("\n❌ 用户取消操作")
    except Exception as e:
        print(f"❌ 翻译失败: {e}")
        print("\n💡 请检查:")
        print("- 输入SRT文件是否存在")
        print("- agent_name是否在agent_dict中配置")
        print("- API密钥是否有效")


if __name__ == "__main__":
    main(1)