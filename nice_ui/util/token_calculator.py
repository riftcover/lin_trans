"""
代币计算工具函数
集中管理所有代币相关的计算逻辑，避免重复代码
"""
import re
from pathlib import Path
from loguru import logger


def calculate_video_duration(file_path: str) -> float:
    """
    计算视频时长（秒）
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        视频时长（秒）
        
    Raises:
        Exception: 如果无法读取视频文件
    """
    try:
        import av
        with av.open(file_path) as container:
            duration_seconds = float(container.duration) / av.time_base
            return duration_seconds
    except Exception as e:
        logger.error(f"计算视频时长失败: {file_path}, 错误: {str(e)}")
        raise


def calculate_srt_char_count(file_path: str) -> int:
    """
    计算 SRT 文件的字符数（跳过序号和时间戳）
    
    Args:
        file_path: SRT 文件路径
        
    Returns:
        字符数
        
    Raises:
        Exception: 如果无法读取文件
    """
    try:
        total_chars = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                # 跳过序号和时间戳
                if re.match(r"^\d+$", line.strip()) or re.match(
                    r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$",
                    line.strip(),
                ):
                    continue
                total_chars += len(line.strip())
        return total_chars
    except UnicodeDecodeError:
        logger.error(f"文件编码错误: {file_path}")
        raise
    except Exception as e:
        logger.error(f"计算字符数失败: {file_path}, 错误: {str(e)}")
        raise


def format_duration(duration_seconds: float) -> str:
    """
    格式化时长为 HH:MM:SS 格式
    
    Args:
        duration_seconds: 时长（秒）
        
    Returns:
        格式化的时长字符串 (HH:MM:SS)
    """
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


def calculate_asr_tokens(duration_seconds: float) -> int:
    """
    根据视频时长计算 ASR 代币
    
    Args:
        duration_seconds: 视频时长（秒）
        
    Returns:
        ASR 代币数量
    """
    from nice_ui.services.service_provider import ServiceProvider
    token_service = ServiceProvider().get_token_service()
    return token_service.calculate_asr_tokens(duration_seconds)


def calculate_trans_tokens(char_count: int) -> int:
    """
    根据字符数计算翻译代币
    
    Args:
        char_count: 字符数
        
    Returns:
        翻译代币数量
    """
    from nice_ui.services.service_provider import ServiceProvider
    token_service = ServiceProvider().get_token_service()
    return token_service.calculate_trans_tokens(char_count)

