"""
NLP API 客户端，用于调用服务端的 spacy 分句处理服务
"""
import time
from typing import Optional, Tuple
import httpx

from services.config_manager import ConfigManager
from utils import logger


class NLPAPIClient:
    """NLP API 客户端"""

    def __init__(self, api_base_url: str, api_key: Optional[str] = None, timeout: int = 300):
        """
        初始化 NLP API 客户端
        
        Args:
            api_base_url: API 基础 URL
            api_key: API 密钥（如果需要）
            timeout: 请求超时时间（秒）
        """
        self.api_base_url = api_base_url.rstrip('/')
        #todo token 未添加
        self.timeout = timeout

        # 创建 HTTP 客户端
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer'

        self.client = httpx.Client(
            timeout=timeout,
            headers=headers,
            follow_redirects=True
        )

    def submit_nlp_task(self, oss_file_url: str, language: str = 'zh') -> Tuple[bool, str, str]:
        """
        提交 NLP 处理任务
        
        Args:
            oss_file_url: OSS 文件 URL
            language: 语言代码
            
        Returns:
            Tuple[bool, str, str]: (是否成功, 任务ID或结果, 错误信息)
        """
        try:
            url = f"{self.api_base_url}/nlp/process"
            data = {
                'file_url': oss_file_url,
                'language': language,
                'task_type': 'sentence_split'
            }

            logger.info(f"提交 NLP 任务: {url}")

            # 设置请求头
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            if self.api_key:
                request_headers['Authorization'] = f'Bearer {self.api_key}'

            response = self.client.post(url, json=data, headers=request_headers)
            response.raise_for_status()

            # 尝试解析JSON响应
            try:
                result = response.json()

                # 检查标准响应格式: {code: 200, data: {task_id: "xxx"}, message: "xxx"}
                if 'code' in result and result.get('code') == 200:
                    data = result.get('data', {})
                    if 'task_id' in data:
                        task_id = data['task_id']
                        message = result.get('message', '任务创建成功')
                        logger.info(f"NLP 任务提交成功: {message}")
                        return True, task_id, ""
                    else:
                        error_msg = result.get('message', '响应中缺少task_id')
                        logger.error(f"NLP 任务提交失败: {error_msg}")
                        return False, "", error_msg

                # 检查是否有success字段（备用格式）
                elif 'success' in result:
                    if result.get('success', False):
                        task_id = result.get('task_id')
                        logger.info(f"NLP 任务提交成功，任务ID: {task_id}")
                        return True, task_id, ""
                    else:
                        error_msg = result.get('message', '未知错误')
                        logger.error(f"NLP 任务提交失败: {error_msg}")
                        return False, "", error_msg

                # 检查是否有task_id字段（直接成功响应）
                elif 'task_id' in result:
                    task_id = result.get('task_id')
                    logger.info(f"NLP 任务提交成功，任务ID: {task_id}")
                    return True, task_id, ""

                else:
                    # 如果响应格式不符合预期
                    logger.error(f"未知的响应格式: {result}")
                    return False, "", f"未知的响应格式: {result}"

            except ValueError as json_error:
                # 如果不是JSON响应，检查文本内容
                response_text = response.text
                if '成功' in response_text or 'success' in response_text.lower():
                    logger.info(f"NLP 任务提交成功: {response_text}")
                    task_id = f"task_{int(time.time())}"
                    return True, task_id, ""
                else:
                    logger.error(f"NLP 任务提交失败，无法解析响应: {response_text}")
                    return False, "", f"响应解析错误: {str(json_error)}"

        except Exception as e:
            error_msg = f"提交 NLP 任务时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg

    def check_task_status(self, task_id: str) -> Tuple[bool, dict, str]:
        """
        检查任务状态

        Args:
            task_id: 任务ID

        Returns:
            Tuple[bool, dict, str]: (是否成功, 任务状态数据, 错误信息)
        """
        try:
            url = f"{self.api_base_url}/nlp/status/{task_id}"
            response = self.client.get(url)
            response.raise_for_status()

            result = response.json()
            task_data = result.get('data', {})
            status = task_data.get('status')

            if status == 'completed':
                # 获取结果URL
                result_url = f"{self.api_base_url}/nlp/result/{task_id}"
                result_response = self.client.get(result_url)
                result_response.raise_for_status()
                result_data = result_response.json()
                srt_file_url = result_data.get('data', {}).get('result_url', '')

                return True, {
                    'status': 'completed',
                    'result_url': srt_file_url
                }, ""
            elif status == 'failed':
                error_msg = task_data.get('error_message', '任务处理失败')
                return True, {
                    'status': 'failed',
                    'error': error_msg
                }, ""
            elif status in ['pending', 'processing']:
                return True, {
                    'status': status
                }, ""
            else:
                return True, {
                    'status': status or 'unknown'
                }, ""

        except Exception as e:
            error_msg = f"查询任务状态时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg

    def wait_for_completion(self, task_id: str, max_wait_time: int = 300, poll_interval: int = 5) -> Tuple[bool, str, str]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            Tuple[bool, str, str]: (是否成功, SRT文件URL或内容, 错误信息)
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                url = f"{self.api_base_url}/nlp/status/{task_id}"
                response = self.client.get(url)
                response.raise_for_status()

                result = response.json()
                task_data = result.get('data', {})
                status = task_data.get('status')

                if status == 'completed':
                    # 从result端点获取SRT文件URL
                    result_url = f"{self.api_base_url}/nlp/result/{task_id}"
                    result_response = self.client.get(result_url)
                    result_response.raise_for_status()
                    result_data = result_response.json()
                    srt_file_url = result_data.get('data', {}).get('result_url', '')
                    logger.info(f"NLP 任务完成，获取到SRT文件URL: {srt_file_url}")
                    return True, srt_file_url, ""
                elif status == 'failed':
                    error_msg = task_data.get('error_message', '任务处理失败')
                    logger.error(f"NLP 任务失败: {error_msg}")
                    return False, "", error_msg
                elif status in ['pending', 'processing']:
                    logger.info(f"NLP 任务进行中，状态: {status}")
                    time.sleep(poll_interval)
                else:
                    logger.warning(f"未知任务状态: {status}")
                    time.sleep(poll_interval)

            except Exception as e:
                logger.error(f"查询任务状态时发生错误: {str(e)}")
                time.sleep(poll_interval)

        # 超时
        error_msg = f"等待任务完成超时（{max_wait_time}秒）"
        logger.error(error_msg)
        return False, "", error_msg

    def download_srt_file(self, srt_url: str, local_path: str) -> Tuple[bool, str]:
        """
        从URL下载 SRT 文件

        Args:
            srt_url: SRT 文件 URL
            local_path: 本地保存路径

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            logger.info(f"下载 SRT 文件: {srt_url} -> {local_path}")

            # 构建完整的URL
            if srt_url.startswith('/'):
                # 相对URL，需要添加base_url
                full_url = f"{self.api_base_url.replace('/api', '')}{srt_url}"
            else:
                # 绝对URL
                full_url = srt_url

            response = self.client.get(full_url)
            response.raise_for_status()

            # 保存SRT内容到文件
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(response.text)

            logger.info(f"SRT 文件下载成功: {local_path}")
            return True, ""

        except Exception as e:
            error_msg = f"下载 SRT 文件时发生错误: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def process_segments(self, oss_file_url: str, local_srt_path: str, language: str = 'zh') -> Tuple[bool, str]:
        """
        完整的处理流程：提交任务 -> 等待完成 -> 下载结果
        
        Args:
            oss_file_url: OSS 文件 URL
            local_srt_path: 本地 SRT 文件保存路径
            language: 语言代码
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        # 1. 提交任务
        success, task_id, error = self.submit_nlp_task(oss_file_url, language)
        if not success:
            return False, error

        # 2. 等待完成
        success, srt_url, error = self.wait_for_completion(task_id)
        if not success:
            return False, error

        # 3. 下载结果
        success, error = self.download_srt_file(srt_url, local_srt_path)
        return success, error

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'client'):
            self.client.close()


def create_nlp_client() -> Optional[NLPAPIClient]:
    """
    创建 NLP API 客户端实例

    Returns:
        NLPAPIClient: NLP API 客户端实例，如果配置不完整则返回 None
    """
    try:
        # 从配置中获取 NLP API 设置
        from nice_ui.configure import config

        api_base_url = ConfigManager().get_api_base_url()
        api_key = config.params.get('nlp_api_key')

        if not api_base_url:
            logger.error("NLP API URL 未配置")
            return None

        return NLPAPIClient(api_base_url, api_key)

    except Exception as e:
        logger.error(f"创建 NLP API 客户端失败: {str(e)}")
        return None
