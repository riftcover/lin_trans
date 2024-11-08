import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger

class VideoCompressor:
    def __init__(self):
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg first.")

    def _check_ffmpeg(self) -> bool:
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return True
        except FileNotFoundError:
            return False

    def compress_video(self, 
                      input_path: str, 
                      output_path: Optional[str] = None, 
                      quality: str = "high",
                      use_hardware: bool = True) -> str:
        """
        使用 FFmpeg 压缩视频
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径（可选）
            quality: 质量设置 ("high", "medium", "low")
            use_hardware: 是否使用硬件加速
        """
        try:
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input video not found: {input_path}")

            if output_path is None:
                output_path = input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"
            else:
                output_path = Path(output_path)

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 根据质量设置参数
            quality_settings = {
                "high": {"bitrate": "5000k", "audio_bitrate": "192k"},
                "medium": {"bitrate": "2500k", "audio_bitrate": "128k"},
                "low": {"bitrate": "1000k", "audio_bitrate": "96k"}
            }
            settings = quality_settings.get(quality, quality_settings["high"])

            # 构建基本命令
            command = ['ffmpeg', '-i', str(input_path)]

            # 根据平台和设置选择编码器
            if sys.platform == "darwin" and use_hardware:
                # macOS 硬件加速
                command.extend([
                    '-vcodec', 'h264_videotoolbox',
                    '-b:v', settings["bitrate"],
                    '-maxrate', str(int(float(settings["bitrate"].replace('k', '')) * 1.5)) + 'k',
                    '-bufsize', str(int(float(settings["bitrate"].replace('k', '')) * 2)) + 'k'
                ])
            else:
                # CPU 编码
                command.extend([
                    '-c:v', 'libx264',
                    '-crf', '23' if quality == "high" else ('28' if quality == "medium" else '32'),
                    '-preset', 'medium'
                ])

            # 添加通用设置
            command.extend([
                '-c:a', 'aac',
                '-b:a', settings["audio_bitrate"],
                '-movflags', '+faststart',
                '-loglevel', 'warning',
                str(output_path)
            ])

            # 执行压缩
            logger.info(f"开始压缩视频: {input_path}")
            logger.info(f"使用{'硬件' if use_hardware else 'CPU'}编码")
            process = subprocess.run(command, capture_output=True, text=True)

            if process.returncode != 0:
                raise RuntimeError(f"压缩失败: {process.stderr}")

            # 输出结果
            original_size = input_path.stat().st_size / (1024 * 1024)
            compressed_size = output_path.stat().st_size / (1024 * 1024)
            
            logger.info(f"压缩完成:")
            logger.info(f"原始文件大小: {original_size:.2f}MB")
            logger.info(f"压缩后文件大小: {compressed_size:.2f}MB")
            logger.info(f"压缩率: {(1 - compressed_size/original_size) * 100:.2f}%")

            return str(output_path)

        except Exception as e:
            logger.error(f"视频压缩失败: {str(e)}")
            raise

def compress_video(input_path: str, 
                  output_path: Optional[str] = None, 
                  quality: str = "high",
                  use_hardware: bool = True) -> str:
    compressor = VideoCompressor()
    return compressor.compress_video(input_path, output_path, quality, use_hardware)

if __name__ == '__main__':
    in_p = '/Users/locodol/Movies/ski/纸板漂浮练习/纸板漂浮练习.mp4'
    out_p = '/Users/locodol/Movies/ski/纸板漂浮练习/纸板漂浮练习_sm.mp4'
    compress_video(in_p, out_p,quality="high", use_hardware=True)