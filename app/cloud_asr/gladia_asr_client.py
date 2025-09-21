"""
"""

import os
import time

import requests
from pydantic import HttpUrl
from typing import Dict, List, Optional

from app.cloud_asr import cloud_sdk
from utils import logger
from app.cloud_asr.aliyun_oss_client import upload_file_for_asr


class GladiaASRClient:
    """Gladia ASR API 客户端 """

    def __init__(self, api_key: str, base_url: str = "https://api.gladia.io"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

        logger.trace(f"Gladia ASR客户端初始化完成")
    
    def upload_audio_direct(self, file_path: str) -> str:
        """
        直接上传音频文件到Gladia（备用方案）

        Args:
            file_path: 本地音频文件路径

        Returns:
            str: Gladia的音频文件URL
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"直接上传音频文件到Gladia: {file_path}")

        with open(file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(file_path)
        files = [("audio", (filename, file_content, "wav"))]

        headers = {
            "x-gladia-key": self.api_key,
            "accept": "application/json"
        }

        response = requests.post(f"{self.base_url}/v2/upload/", headers=headers, files=files)
        response.raise_for_status()

        result = response.json()
        audio_url = result["audio_url"]
        logger.info(f"Gladia直接上传成功: {audio_url}")
        return audio_url

    def upload_audio_oss(self, file_path: str) -> str:
        """
        通过阿里云OSS中转上传音频文件
        流程：
        1. 上传文件到阿里云OSS
        2. 获取OSS公网URL
        3. 返回OSS URL供Gladia使用

        Args:
            file_path: 本地音频文件路径
        Returns:
            str: 阿里云OSS的音频文件URL
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        logger.info(f"开始通过OSS中转上传音频文件: {file_path}")

        # 第一步：上传到阿里云OSS
        success, oss_url, error = upload_file_for_asr(
            local_file_path=file_path,
            expires=24 * 3600  # 24小时有效期
        )

        if not success:
            raise Exception(f"上传到阿里云OSS失败: {error}")

        logger.info(f"OSS上传成功，URL: {oss_url}")

        # 第二步：返回OSS URL，Gladia将直接使用这个URL
        return oss_url

    def upload_audio(self, file_path: str, use_oss: bool = True) -> str:
        """
        智能上传音频文件

        Args:
            file_path: 本地音频文件路径
            use_oss: 是否使用OSS中转，默认True（推荐）

        Returns:
            str: 音频文件URL
        """
        if use_oss:
            return self.upload_audio_oss(file_path)
        else:
            return self.upload_audio_direct(file_path)
    
    def submit_transcription(self, audio_url: str, config: Dict = None) -> str:
        """提交转录任务，返回result_url"""
        data = {
            "audio_url": audio_url,
            "custom_vocabulary": False,
            "translation": False,
            "custom_spelling": False,
            "language_config": {},
            "diarization": False,
            "name_consistency": False,
            "punctuation_enhanced": False
        }

        if config:
            data.update(config)

        headers = {
            "x-gladia-key": self.api_key,
            "Content-Type": "application/json"
        }

        logger.info("提交转录任务")
        response = requests.post(f"{self.base_url}/v2/pre-recorded/", headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        result_url = result["result_url"]
        logger.info(f"任务提交成功: {result_url}")
        return result_url
    
    def get_result(self, result_url: str) -> Dict:
        """获取转录结果"""
        headers = {
            "x-gladia-key": self.api_key,
            "accept": "application/json"
        }

        response = requests.get(result_url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, result_url: str, max_wait_time: int = 600) -> Dict:
        """等待转录完成"""
        logger.info("等待转录完成...")
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            result = self.get_result(result_url)
            status = result.get('status')

            logger.info(f"状态: {status}")

            if status == 'done':
                logger.info("转录完成！")
                return result
            elif status == 'error':
                error_msg = result.get('error', '未知错误')
                raise Exception(f"转录失败: {error_msg}")

            time.sleep(1)

        raise TimeoutError(f"转录超时，超过 {max_wait_time} 秒")
    
    def transcribe_file(self, file_path: str, config: Dict = None, use_oss: bool = True) -> Dict:
        """
        完整的转录流程：上传 -> 提交 -> 等待完成

        Args:
            file_path: 音频文件路径
            config: 转录配置
            use_oss: 是否使用OSS中转上传，默认True

        Returns:
            Dict: 转录结果
        """
        logger.info(f"开始转录文件: {file_path}")

        # 1. 上传音频文件
        audio_url = self.upload_audio(file_path, use_oss=use_oss)

        # 2. 提交转录任务
        result_url = self.submit_transcription(audio_url, config)

        # 3. 等待完成
        result = self.wait_for_completion(result_url)

        logger.info("转录流程完成")
        return result
    
    def get_segments(self, result: Dict) -> List[Dict]:
        """
        获取语音片段，转换为项目内部使用的segments格式

        将Gladia API返回的utterances格式转换为与阿里云ASR兼容的segments格式，
        包含text、timestamp、start、end、spk等字段。

        Args:
            result: Gladia API返回的完整结果

        Returns:
            List[Dict]: 转换后的segments列表，格式为:
            [
                {
                    "text": "Do you think that you're a better skier than you actually are?",
                    "timestamp": [[388, 508], [589, 709], [829, 1089], ...],
                    "start": 388,
                    "end": 4012,
                    "spk": 0
                },
                ...
            ]
        """
        utterances = result.get('result', {}).get('transcription', {}).get('utterances', [])
        logger.trace('utterances')
        logger.trace(utterances)

        segments = []
        for utterance in utterances:
            # 提取基本信息
            start_time = int(utterance.get('start', 0) * 1000)  # 转换为毫秒
            end_time = int(utterance.get('end', 0) * 1000)      # 转换为毫秒
            text = utterance.get('text', '').strip()
            speaker = utterance.get('speaker', 0)

            # 提取词级时间戳
            words = utterance.get('words', [])
            timestamp = []

            for word in words:
                word_start = int(word.get('start', 0) * 1000)  # 转换为毫秒
                word_end = int(word.get('end', 0) * 1000)      # 转换为毫秒
                timestamp.append([word_start, word_end])

            # 构建segment对象，与阿里云ASR格式兼容
            segment = {
                'text': text,
                'timestamp': timestamp,
                'start': start_time,
                'end': end_time,
                'spk': speaker  # 使用spk字段保持与阿里云ASR一致
            }

            segments.append(segment)

        logger.info(f"成功转换了{len(segments)}个segments")
        return segments
    
    def get_transcript(self, result: Dict) -> str:
        """获取完整转录文本"""
        return result.get('result', {}).get('transcription', {}).get('full_transcript', '')

    def get_language(self, result: Dict) -> Optional[str]:
        """获取检测到的语言"""
        return result.get('result', {}).get('metadata', {}).get('detected_language')

def creat_gladia_asr_client() -> Optional[GladiaASRClient]:
    """从配置中创建Gladia ASR客户端实例"""
    api_key = cloud_sdk.gladia_api_key
    if not api_key:
        logger.warning("Gladia API Key未配置")
        return None
    return GladiaASRClient(api_key)

def create_config(diarization: bool = False, translation: bool = False) -> Dict:
    """创建简单配置"""
    return {
        "diarization": diarization,
        "translation": translation,
        "custom_vocabulary": False,
        "custom_spelling": False,
        "language_config": {},
        "name_consistency": False,
        "punctuation_enhanced": False
    }


# 使用示例
if __name__ == "__main__":
    audio_file = "F://测试音频//韩语.WAV"

    if os.path.exists(audio_file):
        client = creat_gladia_asr_client()

        try:
            # 转录文件
            result = client.transcribe_file(audio_file, create_config(diarization=True))

            # 获取结果
            transcript = client.get_transcript(result)
            language = client.get_language(result)
            segments = client.get_segments(result)

            print(f"语言: {language}")
            print(f"片段数: {len(segments)}")
            print(f"文本: {transcript[:200]}...")

        except Exception as e:
            print(f"转录失败: {e}")
    else:
        print("文件不存在")
