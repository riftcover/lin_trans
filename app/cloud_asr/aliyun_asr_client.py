import time
from http import HTTPStatus
from pathlib import Path
from typing import Dict, Any, List

import dashscope
import requests
from dashscope.audio.asr import Transcription
from pydantic import BaseModel, Field, field_validator

from app.cloud_asr import cloud_sdk
from utils import logger


class ASRRequestError(Exception):
    """ASR请求错误"""
    pass


class LanguageLiteral(BaseModel):
    """语言代码模型，使用Pydantic进行校验"""
    code: str = Field(..., description="语言代码，支持多种语言")

    @field_validator('code')
    def validate_language_code(cls, v):
        # 支持的语言代码列表
        supported_languages = ["zh", "en", "ja", "yue", "ko", "de", "fr", "ru"]
        if v not in supported_languages:
            raise ValueError(f"无效的语言代码: {v}. 支持的语言代码: {', '.join(supported_languages)}")
        return v


class ASRRequestError(Exception):
    """阿里云ASR请求错误"""
    pass



class AliyunASRClient:
    """阿里云语音识别客户端，使用DashScope SDK实现异步提交任务和异步查询结果"""

    def __init__(self, api_key: str):
        """
        初始化阿里云ASR客户端

        Args:
            api_key: 阿里云DashScope API Key
        """
        self.api_key = api_key
        # 设置DashScope API Key
        dashscope.api_key = api_key

    def submit_task(self, audio_file: str, language: str = "zh") -> Any:
        """
        提交语音识别任务

        Args:
            audio_file: 音频文件的URL或本地文件路径
            language: 语音识别的语言，支持多种语言代码，默认为中文 'zh'

        Returns:
            Any: 包含任务ID的响应对象
        """
        transcribe_response = None
        try:
            # 使用Pydantic验证language参数
            language_model = LanguageLiteral(code=language)
            language_hint = language_model.code

            logger.info(f"提交ASR任务，文件: {audio_file}, 语言: {language_hint}")

            # 判断是否为URL
            is_url = audio_file.startswith('http://') or audio_file.startswith('https://') or audio_file.startswith('oss://')

            # 如果不是URL，直接抛出异常并停止后续操作
            if not is_url:
                error_msg = "不支持本地文件，请提供有效的URL地址"
                logger.error(error_msg)
                raise ASRRequestError(error_msg)

            """
            自定义请求头

            如果使用临时存储空间中的文件，
            则必须在请求的header中添加参数:
                X-DashScope-OssResourceResolve: enable。
            只有在满足此条件的情况下，才能从临时存储空间中获取相应的文件以完成调用。
            """
            custom_headers = {
                "X-DashScope-OssResourceResolve": "enable"
            }

            # 使用DashScope SDK提交异步转写任务
            logger.trace(f'aliyun_sdk:{cloud_sdk}')
            transcribe_response = Transcription.async_call(
                model=cloud_sdk.asr_model,  # 使用最新的模型
                file_urls=[audio_file],  # URL地址
                language_hints=[language_hint],  # 语言提示
                headers=custom_headers  # 添加自定义请求头
            )

            if transcribe_response.status_code == HTTPStatus.OK:
                task_id = transcribe_response.output.task_id
                logger.info(f"成功提交ASR任务 - 阿里云ID: {task_id}")
                return transcribe_response
            else:
                logger.error(f"提交ASR任务失败: {transcribe_response.code}, {transcribe_response.message}")

        except Exception as e:
            logger.error(f"提交ASR任务时发生错误: {str(e)}")
            raise

    def query_task(self, task_response: Any) -> Any:
        """
        查询语音识别任务的状态和结果

        Args:
            task_response: 任务响应对象或任务ID

        Returns:
            Any: 任务状态和结果
        """
        try:
            # 如果传入的是任务ID字符串
            if isinstance(task_response, str):
                task_id = task_response
            else:
                task_id = task_response.output.task_id

            logger.info(f"开始查询ASR任务状态 - 阿里云ID: {task_id}")

            # 准备自定义请求头
            custom_headers = {
                "X-DashScope-Custom-Header": "custom-value",  # 自定义请求头示例
                "X-DashScope-Client-Info": "lin_trans-app"  # 客户端信息
            }

            # 使用DashScope SDK查询任务状态
            try:
                transcribe_response = Transcription.fetch(task=task_id, headers=custom_headers)
                logger.info(f"查询ASR任务状态成功 - 阿里云ID: {task_id}, 状态: {transcribe_response.output.task_status}")
                return transcribe_response
            except Exception as api_error:
                logger.error(f"DashScope API调用失败: {str(api_error)}")
                raise

        except Exception as e:
            logger.error(f"查询ASR任务时发生错误: {str(e)}")
            raise

    def wait_for_completion(self, transcribe_response: Any, interval: int = 5) -> Any:
        """
        等待任务完成并返回结果

        Args:
            transcribe_response: 任务响应对象
            interval: 轮询间隔（秒）

        Returns:
            Any: 任务结果
        """
        attempts = 0
        logger.info("ASR任务进度: 等待处理中")
        while transcribe_response.output.task_status not in [
            'SUCCEEDED',
            'FAILED',
        ]:
            time.sleep(interval)
            attempts += 1
            logger.info(f"ASR任务进度: 正在处理中 {attempts * interval} 秒")

            # 查询任务状态
            transcribe_response = self.query_task(transcribe_response)

            # 更新进度信息
            logger.info("ASR任务进度: 处理完成")

        if transcribe_response.output.task_status == 'SUCCEEDED':
            return transcribe_response
        logger.error(f"ASR任务失败: {transcribe_response.output.task_status}, {transcribe_response.output.message}")
        raise ASRRequestError(f"ASR任务失败: {transcribe_response.output.task_status}, {transcribe_response.output.message}")

    def parse_result(self, response: Any) -> str:
        """
        解析ASR结果，提取transcription_url

        Args:
            response: ASR任务结果响应

        Returns:
            str: 转写结果的URL
        """
        if response.status_code != HTTPStatus.OK or response.output.task_status != 'SUCCEEDED':
            raise ASRRequestError(f"无法解析未成功的ASR结果: {response.output.task_status}")

        # 从响应中提取transcription_url
        try:
            transcription_url = response.output.results[0].get('transcription_url')
            if not transcription_url:
                raise ASRRequestError("响应中没有找到transcription_url")

            logger.info(f"ASR结果文件URL: {transcription_url}")
            return transcription_url
        except (AttributeError, IndexError, KeyError) as e:
            logger.error(f"提取transcription_url时出错: {str(e)}")
            raise ASRRequestError(f"无法从响应中提取transcription_url: {str(e)}") from e

    def download_file(self, url: str, save_path: str) -> str:
        """
        下载ASR任务生成的文件

        Args:
            url: 文件的URL
            save_path: 保存路径

        Returns:
            str: 保存的文件路径
        """
        try:
            logger.info(f"开始下载文件: {url}")

            # 创建目录（如果不存在）
            Path(save_path).resolve().parent.mkdir(parents=True, exist_ok=True)

            # 使用流式下载大文件
            with requests.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()  # 检查响应状态

                # 获取文件大小（如果有）
                file_size = int(response.headers.get('content-length', 0))

                # 显示进度
                if file_size > 0:
                    logger.info(f"文件大小: {file_size / 1024 / 1024:.2f} MB")

                # 写入文件
                with open(save_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # 过滤保持活动的断开连接
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 每10MB显示一次进度
                            if downloaded % (10 * 1024 * 1024) < 8192 and file_size > 0:
                                progress = (downloaded / file_size) * 100
                                logger.info(f"下载进度: {progress:.1f}%")

            logger.info(f"文件成功下载到: {save_path}")
            return save_path

        except requests.RequestException as e:
            logger.error(f"下载文件时发生网络错误: {str(e)}")
            raise ASRRequestError(f"下载文件失败: {str(e)}")
        except Exception as e:
            logger.error(f"下载文件时发生未知错误: {str(e)}")
            raise ASRRequestError(f"下载文件失败: {str(e)}") from e

    def parse_transcription(self, json_file_path: dict) -> List[Dict[str, Any]]:
        """
        解析转写结果JSON文件，提取字幕信息
        按照标点符号分割句子，每遇到一个标点符号就分割成一句话

        Args:
            json_file_path: 阿里云ASR返回的JSON数据

        Returns:
            List[Dict[str, Any]]: 解析后的字幕信息列表，每个元素包含begin_time, end_time和text
        """
        # 快速处理空输入情况
        if not json_file_path:
            return []

        # 使用单次遍历和直接索引获取transcripts
        transcript = None
        if 'transcripts' in json_file_path:
            transcripts = json_file_path['transcripts']
            if isinstance(transcripts, list) and transcripts:
                transcript = transcripts[0]
            elif isinstance(transcripts, dict):
                transcript = transcripts

        if not transcript or 'sentences' not in transcript:
            return []

        sentences = transcript['sentences']
        if not sentences:
            return []

        # 预分配结果列表 - 使用更精确的估计

        # 计算所有句子中标点符号的数量
        punctuation_count = 0
        for sentence in sentences:
            if 'words' in sentence:
                for word in sentence['words']:
                    if word.get('punctuation', '').strip():
                        punctuation_count += 1

        # 根据标点符号数量预分配结果数组

        # 每个句子至少有一个标点符号，再加10%的缓冲
        result_capacity = max(punctuation_count, len(sentences)) + len(sentences) // 10
        result = [None] * result_capacity
        result_index = 0

        # 使用单次遍历和直接索引处理所有句子
        for sentence_idx, sentence in enumerate(sentences):
            if 'words' not in sentence or not sentence['words']:
                continue

            words = sentence['words']
            word_count = len(words)

            # 当前句子的起始时间
            current_begin_time = words[0]['begin_time']
            # 使用字符串列表而不是单个字符串，减少内存分配
            current_text_parts = []
            current_text_length = 0

            # 使用单次遍历和直接索引处理所有单词
            i = 0
            while i < word_count:
                word = words[i]
                word_text = word['text']
                punctuation = word.get('punctuation', '')

                # 使用列表收集文本片段，避免频繁的字符串连接
                current_text_parts.append(word_text)
                current_text_length += len(word_text)

                # 如果有标点符号或者是最后一个单词
                if punctuation.strip() or i == word_count - 1:
                    # 添加标点符号到文本
                    if punctuation.strip():
                        current_text_parts.append(punctuation)
                        current_text_length += len(punctuation)

                    # 使用预分配的空间创建新的句子对象
                    if result_index < result_capacity:
                        # 仅当有实际文本时才创建新的句子
                        if current_text_length > 0:
                            # 使用join一次性创建字符串，避免多次连接
                            result[result_index] = {
                                'begin_time': current_begin_time,
                                'end_time': word['end_time'],
                                'text': ''.join(current_text_parts)
                            }
                            result_index += 1

                    # 重置当前句子的状态
                    if i < word_count - 1:
                        current_begin_time = word['end_time']
                        current_text_parts = []
                        current_text_length = 0

                i += 1

        # 只返回实际使用的部分，避免复制整个数组
        return result[:result_index] if result_index > 0 else []

    def convert_to_segments_format(self, json_data: dict) -> List[Dict[str, Any]]:
        """
        将阿里云ASR原始格式转换为项目内部使用的segments格式

        将原始的sentence+words格式转换为按标点符号分割的segments格式，
        每个segment包含text和对应的timestamp数组。

        Args:
            json_data: 阿里云ASR返回的原始JSON数据

        Returns:
            List[Dict[str, Any]]: 转换后的segments列表，格式为:
            [
                {
                    "text": "Picture a winter wonderland,",
                    "timestamp": [[0, 478], [478, 717], [717, 1196], [1196, 1913]]
                },
                ...
            ]
        """
        segments = []

        # 获取转写结果
        if 'transcripts' not in json_data:
            logger.warning("JSON数据中没有找到transcripts字段")
            return segments

        transcripts = json_data['transcripts']
        if isinstance(transcripts, list) and transcripts:
            transcript = transcripts[0]
        elif isinstance(transcripts, dict):
            transcript = transcripts
        else:
            logger.warning("无效的transcripts格式")
            return segments

        if 'sentences' not in transcript:
            logger.warning("transcript中没有找到sentences字段")
            return segments

        sentences = transcript['sentences']

        # 处理每个句子
        for sentence in sentences:
            if 'words' not in sentence or not sentence['words']:
                continue

            words = sentence['words']
            current_text_parts = []
            current_timestamps = []

            for word in words:
                word_text = word.get('text', '')
                punctuation = word.get('punctuation', '').strip()
                begin_time = word.get('begin_time', 0)
                end_time = word.get('end_time', 0)

                # 添加当前词的文本和时间戳
                current_text_parts.append(word_text)
                current_timestamps.append([begin_time, end_time])

                # 如果有标点符号，表示当前segment结束
                if punctuation:
                    # 将标点符号添加到文本末尾
                    if current_text_parts:
                        current_text_parts[-1] = current_text_parts[-1].rstrip() + punctuation

                    # 创建新的segment
                    if current_text_parts and current_timestamps:
                        # 计算segment的开始和结束时间
                        start_time = current_timestamps[0][0] if current_timestamps else 0
                        end_time = current_timestamps[-1][1] if current_timestamps else 0

                        segment = {
                            'text': ''.join(current_text_parts).strip(),
                            'timestamp': current_timestamps.copy(),
                            'start': start_time,
                            'end': end_time,
                            'spk': 0  # 阿里云ASR默认单说话人
                        }
                        segments.append(segment)

                        # 重置当前segment
                        current_text_parts = []
                        current_timestamps = []

            # 处理句子末尾没有标点符号的情况
            if current_text_parts and current_timestamps:
                # 计算segment的开始和结束时间
                start_time = current_timestamps[0][0] if current_timestamps else 0
                end_time = current_timestamps[-1][1] if current_timestamps else 0

                segment = {
                    'text': ''.join(current_text_parts).strip(),
                    'timestamp': current_timestamps.copy(),
                    'start': start_time,
                    'end': end_time,
                    'spk': 0  # 阿里云ASR默认单说话人
                }
                segments.append(segment)

        logger.info(f"成功转换了{len(segments)}个segments")
        return segments

    @staticmethod
    def _format_timestamp(ms: int) -> str:
        """
        将毫秒转换为SRT格式的时间戳

        Args:
            ms: 毫秒时间戳

        Returns            str: SRT格式的时间戳 (HH:MM:SS,mmm)
        """
        seconds, ms = divmod(ms, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"


# 创建客户端实例的工厂函数
def create_aliyun_asr_client() -> AliyunASRClient:
    """
    从配置中创建阿里云ASR客户端实例

    Returns:
        AliyunASRClient: 阿里云ASR客户端实例
    """
    if api_key := cloud_sdk.asr_api_key:
        return AliyunASRClient(api_key)
    else:
        raise ValueError("阿里云ASR配置不完整，请检查配置中的阿里云DashScope API Key")

if __name__ == '__main__':
    client = create_aliyun_asr_client()

    # 示例：提交语音识别任务并等待完成
    audio_file = "oss://dashscope-instant/6ce1b910bd8d28d46d97822fa04e1721/2025-04-22/5f723bc3-1015-94a7-819b-d6a666ba4c2d/tt.war"
    task = client.submit_task(audio_file)
    response = client.wait_for_completion(task)

    parsed_results = client.parse_result(response)
