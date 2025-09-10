"""
智能分句处理器
负责处理用户手动触发的智能分句功能
"""
import os
import json
import time
from typing import Optional, Tuple
from utils import logger
from app.cloud_asr.aliyun_oss_client import upload_file_for_asr
from app.nlp_api import create_nlp_client


class SmartSentenceProcessor:
    """智能分句处理器"""
    
    def __init__(self):
        self.nlp_client = None
    
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
            if not segment_data_path or not os.path.exists(segment_data_path):
                return False, "segment_data文件不存在，智能分句功能不可用"
            
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
        执行智能分句处理
        
        Args:
            srt_file_path: SRT文件路径
            progress_callback: 进度回调函数，参数为(progress: int, message: str)
            
        Returns:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        try:
            # 1. 检测语言
            if progress_callback:
                progress_callback(5, "检测语言...")

            language = self._detect_language_from_metadata(srt_file_path)
            logger.info(f"智能分句将使用语言: {language}")

            # 2. 检查segment_data文件
            if progress_callback:
                progress_callback(10, "检查元数据文件...")

            available, segment_data_path = self.check_segment_data_available(srt_file_path)
            if not available:
                return False, segment_data_path

            # 3. 上传segment_data到OSS
            if progress_callback:
                progress_callback(20, "上传文件...")

            success, oss_url, error = self._upload_segment_data(segment_data_path)
            if not success:
                return False, f"上传失败: {error}"

            # 4. 提交NLP任务（使用检测到的语言）
            if progress_callback:
                progress_callback(40, "提交任务...")

            success, task_id, error = self._submit_nlp_task(oss_url, language)
            if not success:
                return False, f"任务提交失败: {error}"
            
            # 4. 等待任务完成
            if progress_callback:
                progress_callback(60, "等待处理完成...")
            
            success, srt_url, error = self._wait_for_completion(task_id, progress_callback)
            if not success:
                return False, f"NLP处理失败: {error}"
            
            # 5. 下载并替换SRT文件
            if progress_callback:
                progress_callback(90, "下载新的SRT文件...")
            
            success, error = self._download_and_replace_srt(srt_url, srt_file_path)
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
    
    def _submit_nlp_task(self, oss_url: str, language: str = 'zh') -> Tuple[bool, str, str]:
        """提交NLP处理任务"""
        try:
            if not self.nlp_client:
                self.nlp_client = create_nlp_client()
                if not self.nlp_client:
                    return False, "", "无法创建NLP客户端"

            success, task_id, error = self.nlp_client.submit_nlp_task(oss_url, language)
            if success:
                logger.info(f"NLP任务提交成功，任务ID: {task_id}，语言: {language}")
                return True, task_id, ""
            else:
                logger.error(f"NLP任务提交失败: {error}")
                return False, "", error

        except Exception as e:
            logger.error(f"提交NLP任务时发生异常: {str(e)}")
            return False, "", str(e)
    
    def _wait_for_completion(self, task_id: str, progress_callback=None) -> Tuple[bool, str, str]:
        """等待NLP任务完成"""
        try:
            # 使用带进度更新的等待方法
            max_wait_time = 300  # 最大等待5分钟
            check_interval = 5   # 每5秒检查一次
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                # 检查任务状态
                success, result, error = self.nlp_client.check_task_status(task_id)
                if success:
                    if result.get('status') == 'completed':
                        srt_url = result.get('result_url')
                        if srt_url:
                            logger.info(f"NLP任务完成，SRT文件URL: {srt_url}")
                            return True, srt_url, ""
                        else:
                            return False, "", "任务完成但未获得结果URL"
                    elif result.get('status') == 'failed':
                        return False, "", result.get('error', '任务处理失败')
                    # 任务仍在处理中，继续等待
                else:
                    logger.warning(f"检查任务状态失败: {error}")
                
                # 更新进度
                if progress_callback:
                    progress = min(60 + (elapsed_time / max_wait_time) * 25, 85)
                    progress_callback(int(progress), f"处理中... ({elapsed_time}s)")
                
                time.sleep(check_interval)
                elapsed_time += check_interval
            
            return False, "", "任务超时"
            
        except Exception as e:
            logger.error(f"等待NLP任务完成时发生异常: {str(e)}")
            return False, "", str(e)
    
    def _download_and_replace_srt(self, srt_url: str, local_srt_path: str) -> Tuple[bool, str]:
        """下载并替换本地SRT文件"""
        try:
            success, error = self.nlp_client.download_srt_file(srt_url, local_srt_path)
            if success:
                logger.info(f"智能分句处理完成，已替换本地SRT文件: {local_srt_path}")
                return True, ""
            else:
                logger.error(f"下载智能分句结果失败: {error}")
                return False, error
                
        except Exception as e:
            logger.error(f"下载并替换SRT文件时发生异常: {str(e)}")
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


def process_smart_sentence(srt_file_path: str, progress_callback=None) -> Tuple[bool, str]:
    """
    处理智能分句
    
    Args:
        srt_file_path: SRT文件路径
        progress_callback: 进度回调函数
        
    Returns:
        Tuple[bool, str]: (是否成功, 错误信息)
    """
    return smart_sentence_processor.process_smart_sentence(srt_file_path, progress_callback)
