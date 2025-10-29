"""
智能分句处理器 - QEventLoop 版本

重构说明：
- 移除了 NLPAPIClient 中间层
- 使用 simple_api_service + QEventLoop 等待异步结果
- 在 QThread 中执行，不阻塞 UI
- 统一事件循环，自动 token 刷新
- 保持顺序流程，代码可读性高
"""
import os
import json
import time
import httpx
from typing import Tuple, Optional
from PySide6.QtCore import QEventLoop, QThread
from utils import logger
from app.cloud_asr.aliyun_oss_client import upload_file_for_asr
from nice_ui.services.simple_api_service import simple_api_service


class SmartSentenceProcessor:
    """智能分句处理器（QEventLoop 版本）"""

    def __init__(self):
        pass  # 不需要任何实例变量
    
    def check_segment_data_available(self, srt_file_path: str) -> Tuple[bool, str]:
        """
        检查是否有可用的segment_data文件
        
        Args:
            srt_file_path: SRT文件路径
            
        Returns:
            Tuple[bool, str]: (是否可用, segment_data文件路径或错误信息)
        """
        try:
            # 根据SRT文件路径推断metadata文件路径
            base_path = os.path.splitext(srt_file_path)[0]
            metadata_path = f"{base_path}_metadata.json"
            
            if not os.path.exists(metadata_path):
                return False, "未找到metadata文件，智能分句功能不可用"
            
            # 读取metadata文件
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            segment_data_path = metadata.get('segment_data_path')
            segment_language = metadata.get('language')
            # 检查语言是否支持且segment_data文件是否存在
            if (segment_language not in ('zh', 'en', 'ja', 'ko', 'de', 'ru', 'fr') or
                not segment_data_path or not os.path.exists(segment_data_path)):
                return False, "智能分句功能不可用"
            
            return True, segment_data_path
            
        except Exception as e:
            logger.error(f"检查segment_data可用性时发生错误: {str(e)}")
            return False, f"检查失败: {str(e)}"

    def _detect_language_from_metadata(self, srt_file_path: str) -> str:
        """
        从metadata文件或配置中检测语言

        Args:
            srt_file_path: SRT文件路径

        Returns:
            str: 语言代码，默认为'zh'
        """
        try:
            # 1. 尝试从metadata文件获取语言信息
            base_path = os.path.splitext(srt_file_path)[0]
            metadata_path = f"{base_path}_metadata.json"

            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 检查metadata中是否有语言信息
                language = metadata.get('language')
                if language:
                    logger.info(f"从metadata文件检测到语言: {language}")
                    return language

            # 2. 尝试从全局配置获取语言
            try:
                from nice_ui.configure import config
                source_language_code = config.params.get('source_language_code', 'zh')
                logger.info(f"从全局配置检测到语言: {source_language_code}")
                return source_language_code
            except Exception as e:
                logger.warning(f"无法从配置获取语言: {str(e)}")

            # 3. 默认返回中文
            logger.info("使用默认语言: zh")
            return 'zh'

        except Exception as e:
            logger.warning(f"检测语言时发生错误: {str(e)}，使用默认语言: zh")
            return 'zh'

    def process_smart_sentence(self, srt_file_path: str, progress_callback=None) -> Tuple[bool, str]:
        """
        执行智能分句处理（在 QThread 中调用）

        使用 QEventLoop 等待异步结果，保持顺序流程

        Args:
            srt_file_path: SRT文件路径
            progress_callback: 进度回调函数，参数为(progress: int, message: str)

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            # 1. 检测语言（同步）
            if progress_callback:
                progress_callback(5, "检测语言...")

            language = self._detect_language_from_metadata(srt_file_path)
            logger.info(f"智能分句将使用语言: {language}")

            # 2. 检查segment_data文件（同步）
            if progress_callback:
                progress_callback(10, "检查元数据文件...")

            available, segment_data_path = self.check_segment_data_available(srt_file_path)
            if not available:
                return False, segment_data_path

            # 3. 上传segment_data到OSS（同步）
            if progress_callback:
                progress_callback(20, "上传文件...")

            success, oss_url, error = self._upload_segment_data(segment_data_path)
            if not success:
                return False, f"上传失败: {error}"

            # 4. 提交NLP任务（异步 → 同步）
            if progress_callback:
                progress_callback(40, "提交任务...")

            task_id = self._submit_nlp_task_sync(oss_url, language)
            if not task_id:
                return False, "任务提交失败"

            # 5. 等待任务完成（异步轮询 → 同步）
            if progress_callback:
                progress_callback(60, "等待处理完成...")

            result_url = self._wait_for_completion_sync(task_id, progress_callback)
            if not result_url:
                return False, "NLP处理失败"

            # 6. 下载并替换SRT文件（同步）
            if progress_callback:
                progress_callback(90, "下载新的SRT文件...")

            success, error = self._download_and_replace_srt_sync(result_url, srt_file_path)
            if not success:
                return False, f"下载失败: {error}"

            if progress_callback:
                progress_callback(100, "智能分句完成！")

            return True, "智能分句处理成功"

        except Exception as e:
            logger.error(f"智能分句处理时发生异常: {str(e)}")
            return False, f"处理异常: {str(e)}"
    
    def _upload_segment_data(self, segment_data_path: str) -> Tuple[bool, str, str]:
        """上传segment_data文件到OSS"""
        try:
            success, oss_url, error = upload_file_for_asr(segment_data_path)
            if success:
                logger.info(f"segment_data文件上传成功: {oss_url}")
                return True, oss_url, ""
            else:
                logger.error(f"segment_data文件上传失败: {error}")
                return False, "", error
        except Exception as e:
            logger.error(f"上传segment_data文件时发生异常: {str(e)}")
            return False, "", str(e)
    
    def _submit_nlp_task_sync(self, oss_url: str, language: str = 'zh') -> Optional[str]:
        """
        提交NLP处理任务（同步版本）

        使用 QEventLoop 等待 simple_api_service 的回调结果

        Args:
            oss_url: OSS 文件 URL
            language: 语言代码

        Returns:
            Optional[str]: 任务 ID，失败返回 None
        """
        try:
            logger.info(f"提交 NLP 任务: file_url={oss_url}, language={language}")

            # 创建事件循环（在工作线程中）
            loop = QEventLoop()
            result_container = {'task_id': None, 'error': None}

            def on_success(result):
                """成功回调"""
                try:
                    if result.get('code') == 200:
                        data = result.get('data', {})
                        task_id = data.get('task_id')
                        if task_id:
                            logger.info(f"NLP任务提交成功，任务ID: {task_id}，语言: {language}")
                            result_container['task_id'] = task_id
                        else:
                            logger.error("响应中缺少task_id")
                            result_container['error'] = "响应中缺少task_id"
                    else:
                        error_msg = result.get('message', '未知错误')
                        logger.error(f"NLP任务提交失败: {error_msg}")
                        result_container['error'] = error_msg
                except Exception as e:
                    logger.error(f"处理成功回调时发生异常: {str(e)}")
                    result_container['error'] = str(e)
                finally:
                    loop.quit()

            def on_error(error):
                """失败回调"""
                logger.error(f"提交NLP任务失败: {error}")
                result_container['error'] = str(error)
                loop.quit()

            # 调用 simple_api_service（异步）
            simple_api_service.submit_nlp_task(
                oss_url, language,
                callback_success=on_success,
                callback_error=on_error
            )

            # 阻塞等待结果（只阻塞工作线程，不阻塞 UI）
            loop.exec()

            return result_container['task_id']

        except Exception as e:
            logger.error(f"提交NLP任务时发生异常: {str(e)}")
            return None
    
    def _wait_for_completion_sync(self, task_id: str, progress_callback=None) -> Optional[str]:
        """
        等待NLP任务完成（同步版本）

        使用 QEventLoop + QThread.sleep() 轮询任务状态

        Args:
            task_id: 任务 ID
            progress_callback: 进度回调函数

        Returns:
            Optional[str]: 结果 URL，失败返回 None
        """
        try:
            max_wait_time = 300  # 最大等待5分钟
            check_interval = 5   # 每5秒检查一次
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                # 创建事件循环检查状态
                loop = QEventLoop()
                result_container = {'status': None, 'error': None, 'result_url': None}

                def on_status_success(result):
                    """状态查询成功回调"""
                    try:
                        if result.get('code') == 200:
                            task_data = result.get('data', {})
                            status = task_data.get('status')
                            result_container['status'] = status

                            if status == 'failed':
                                error_msg = task_data.get('error_message', '任务处理失败')
                                result_container['error'] = error_msg
                        else:
                            error_msg = result.get('message', '查询失败')
                            logger.warning(f"检查任务状态失败: {error_msg}")
                    except Exception as e:
                        logger.error(f"处理状态回调时发生异常: {str(e)}")
                    finally:
                        loop.quit()

                def on_status_error(error):
                    """状态查询失败回调"""
                    logger.warning(f"检查任务状态失败: {error}")
                    loop.quit()

                # 查询任务状态
                simple_api_service.check_nlp_task_status(
                    task_id,
                    callback_success=on_status_success,
                    callback_error=on_status_error
                )

                # 等待状态查询结果
                loop.exec()

                # 检查状态
                status = result_container['status']

                if status == 'completed':
                    # 任务完成，获取结果 URL
                    return self._get_result_url_sync(task_id)
                elif status == 'failed':
                    logger.error(f"NLP任务失败: {result_container['error']}")
                    return None
                else:
                    # pending, processing, 继续等待
                    logger.info(f"NLP任务进行中，状态: {status}")

                # 更新进度
                if progress_callback:
                    progress = min(60 + (elapsed_time / max_wait_time) * 25, 85)
                    progress_callback(int(progress), f"处理中... ({elapsed_time}s)")

                # 等待一段时间后再次检查（使用 QThread.sleep 不阻塞 UI）
                QThread.sleep(check_interval)
                elapsed_time += check_interval

            logger.error("NLP任务超时")
            return None

        except Exception as e:
            logger.error(f"等待NLP任务完成时发生异常: {str(e)}")
            return None

    def _get_result_url_sync(self, task_id: str) -> Optional[str]:
        """
        获取任务结果 URL（同步版本）

        Args:
            task_id: 任务 ID

        Returns:
            Optional[str]: 结果 URL，失败返回 None
        """
        try:
            loop = QEventLoop()
            result_container = {'result_url': None}

            def on_success(result):
                """成功回调"""
                try:
                    if result.get('code') == 200:
                        srt_url = result.get('data', {}).get('result_url', '')
                        if srt_url:
                            logger.info(f"NLP任务完成，SRT文件URL: {srt_url}")
                            result_container['result_url'] = srt_url
                        else:
                            logger.error("任务完成但未获得结果URL")
                except Exception as e:
                    logger.error(f"处理结果回调时发生异常: {str(e)}")
                finally:
                    loop.quit()

            def on_error(error):
                """失败回调"""
                logger.error(f"获取任务结果失败: {error}")
                loop.quit()

            # 获取任务结果
            simple_api_service.get_nlp_task_result(
                task_id,
                callback_success=on_success,
                callback_error=on_error
            )

            # 等待结果
            loop.exec()

            return result_container['result_url']

        except Exception as e:
            logger.error(f"获取任务结果时发生异常: {str(e)}")
            return None
    
    def _download_and_replace_srt_sync(self, srt_url: str, local_srt_path: str) -> Tuple[bool, str]:
        """
        下载并替换本地SRT文件（同步版本）

        使用同步 HTTP 客户端下载文件

        Args:
            srt_url: SRT 文件 URL
            local_srt_path: 本地 SRT 文件路径

        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            # 构建完整的URL
            from app.core.api_client import api_client

            if srt_url.startswith('/'):
                # 相对URL，需要添加base_url
                full_url = f"{api_client.base_url.replace('/api', '')}{srt_url}"
            else:
                # 绝对URL
                full_url = srt_url

            # 使用同步HTTP客户端下载（不需要认证）
            with httpx.Client(timeout=300.0, follow_redirects=True) as client:
                with client.stream('GET', full_url) as response:
                    response.raise_for_status()
                    with open(local_srt_path, 'wb') as f:
                        for chunk in response.iter_bytes():
                            f.write(chunk)

            logger.info(f"智能分句处理完成，已替换本地SRT文件: {local_srt_path}")
            return True, ""

        except Exception as e:
            error_msg = f"下载并替换SRT文件时发生异常: {str(e)}"
            logger.error(error_msg)
            return False, str(e)


# 创建全局实例
smart_sentence_processor = SmartSentenceProcessor()


def check_smart_sentence_available(srt_file_path: str) -> bool:
    """
    检查指定SRT文件是否支持智能分句功能
    
    Args:
        srt_file_path: SRT文件路径
        
    Returns:
        bool: 是否支持智能分句
    """
    available, _ = smart_sentence_processor.check_segment_data_available(srt_file_path)
    return available


async def process_smart_sentence(srt_file_path: str, progress_callback=None) -> Tuple[bool, str]:
    """
    处理智能分句（异步）

    Args:
        srt_file_path: SRT文件路径
        progress_callback: 进度回调函数

    Returns:
        Tuple[bool, str]: (是否成功, 错误信息)
    """
    return await smart_sentence_processor.process_smart_sentence(srt_file_path, progress_callback)
