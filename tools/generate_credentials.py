#!/usr/bin/env python
"""
生成加密的凭证文件

使用方法:
python generate_credentials.py --aki YOUR_AKI --aks YOUR_AKS [--region REGION] [--bucket BUCKET] [--asr_api_key ASR_API_KEY] [--asr_model ASR_MODEL]

或者直接运行脚本，按照提示输入信息:
python generate_credentials.py
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from nice_ui.util.crypto_utils import crypto_utils


def parse_args():
    parser = argparse.ArgumentParser(description='生成加密的阿里云凭证文件')
    parser.add_argument('--aki', help='阿里云 AccessKey ID')
    parser.add_argument('--aks', help='阿里云 AccessKey Secret')
    parser.add_argument('--region', default='cn-beijing', help='阿里云区域 (默认: cn-beijing)')
    parser.add_argument('--bucket', default='asr-file-tth', help='阿里云存储桶 (默认: asr-file-tth)')
    parser.add_argument('--asr_api_key', help='ASR API 密钥')
    parser.add_argument('--asr_model', default='paraformer-v2', help='ASR 模型 (默认: paraformer-v2)')
    parser.add_argument('--password', help='加密密码 (默认使用环境变量 LINLIN_CRYPTO_KEY 或默认密码)')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # 如果没有提供命令行参数，交互式获取信息
    if not args.aki or not args.aks:
        print("请输入阿里云凭证信息:")
        args.aki = args.aki or input("AccessKey ID: ").strip()
        args.aks = args.aks or input("AccessKey Secret: ").strip()
        args.region = args.region or input(f"区域 (默认: {args.region}): ").strip() or args.region
        args.bucket = args.bucket or input(f"存储桶 (默认: {args.bucket}): ").strip() or args.bucket
        args.asr_api_key = args.asr_api_key or input("ASR API 密钥 (可选): ").strip()
        args.asr_model = args.asr_model or input(f"ASR 模型 (默认: {args.asr_model}): ").strip() or args.asr_model
    
    # 初始化加密工具
    if args.password:
        crypto_utils.initialize(args.password)
    else:
        crypto_utils.initialize()
    
    # 准备凭证数据
    credentials = {
        'ppl_sdk': {
            'aki': args.aki,
            'aks': args.aks,
            'region': args.region,
            'bucket': args.bucket,
            'asr_api_key': args.asr_api_key or '',
            'asr_model': args.asr_model
        }
    }
    
    # 获取凭证文件路径
    credentials_file = crypto_utils.get_credentials_file_path()
    
    # 加密并保存凭证
    crypto_utils.encrypt_to_file(credentials, credentials_file)
    
    print(f"凭证已加密并保存到: {credentials_file}")
    print("您现在可以安全地使用这些凭证了。")
    
    # 提示设置环境变量
    print("\n如果您希望通过环境变量设置凭证，请设置以下环境变量:")
    print(f"ALIYUN_AKI={args.aki}")
    print(f"ALIYUN_AKS={args.aks}")
    print(f"ALIYUN_REGION={args.region}")
    print(f"ALIYUN_BUCKET={args.bucket}")
    if args.asr_api_key:
        print(f"ALIYUN_ASR_API_KEY={args.asr_api_key}")
    print(f"ALIYUN_ASR_MODEL={args.asr_model}")


if __name__ == '__main__':
    main()
