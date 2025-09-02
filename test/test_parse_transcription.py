#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试parse_transcription函数
"""

import os
import sys
import json
import time

from utils.file_utils import funasr_write_srt_file

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)
print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[0]}")

from app.cloud_asr.aliyun_asr_client import AliyunASRClient


def test_parse_transcription():
    """测试parse_transcription函数"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建JSON文件路径
    json_file_path = r'D:\dcode\lin_trans\result\9ab3de95796efe9c3f1cc049c682d3a3\测试句末符号_asr_result.json'

    # 读取JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return

    # 创建ASR客户端实例（仅用于调用解析方法）
    client = AliyunASRClient(api_key="dummy_key")  # API密钥在这里不重要，因为我们只使用解析方法

    # 测量解析时间
    print("开始解析JSON数据...")
    start_time = time.time()

    # 解析JSON数据
    parsed_results = client.parse_transcription(json_data)

    # 计算耗时
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"解析完成，总耗时: {elapsed_time:.4f} 秒")

    # 打印解析结果
    print(f"解析结果包含 {len(parsed_results)} 个句子")


    # 测量SRT转换时间
    print("开始转换为SRT文件...")
    start_time = time.time()

    # 转换为SRT文件
    output_srt_path = os.path.join(current_dir, 'ta_asr_result.srt')
    funasr_write_srt_file(parsed_results, output_srt_path)

    # 计算耗时
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"转换完成，总耗时: {elapsed_time:.4f} 秒")
    print(f"已生成SRT文件: {output_srt_path}")




if __name__ == '__main__':
    print("测试parse_transcription函数:")
    test_parse_transcription()
