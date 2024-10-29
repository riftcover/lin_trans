from pathlib import Path

import av  # 替换 ffmpeg 导入

from utils.log import Logings

logger = Logings().logger

class FFmpegJobs:
    @staticmethod
    def convert_ts_to_mp4(input_path: Path, output_path: Path):
        """将 TS 文件转换为 MP4 文件"""
        logger.info(f'convert ts to mp4: {input_path} -> {output_path}')
        try:
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 PyAV 进行转换
            with av.open(str(input_path)) as input_container:
                with av.open(str(output_path), 'w') as output_container:
                    # 复制流的参数
                    output_container.metadata.update(input_container.metadata)
                    
                    # 复制所有流
                    for stream in input_container.streams:
                        output_stream = output_container.add_stream(template=stream)
                    
                    # 复制数据包
                    for packet in input_container.demux():
                        output_container.mux(packet)
            
            logger.info("转码完成")
            return True
        except Exception as e:
            logger.error(f"转换失败: {str(e)}")
            return False

    @staticmethod
    def convert_mp4_to_wav(input_path: Path|str, output_path: Path|str):
        """将 MP4 文件转换为 WAV 文件"""
        logger.info(f'convert mp4 to wav: {input_path} -> {output_path}')
        try:
            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 PyAV 进行转换
            with av.open(str(input_path)) as input_container:
                with av.open(str(output_path), 'w') as output_container:
                    # 设置音频流参数
                    output_stream = output_container.add_stream(
                        'pcm_s16le',  # 音频编码格式
                        rate=16000,    # 采样率
                        layout='stereo' # 双声道
                    )
                    
                    # 只处理音频流
                    input_stream = input_container.streams.audio[0]
                    input_stream.codec_context.skip_frame = 'NONKEY'
                    
                    # 转换音频
                    for frame in input_container.decode(input_stream):
                        # 重采样音频
                        frame.pts = None
                        packet = output_stream.encode(frame)
                        output_container.mux(packet)
                    
                    # Flush编码器
                    packet = output_stream.encode(None)
                    if packet:
                        output_container.mux(packet)
            
            logger.info("转码完成")
            return True
        except Exception as e:
            logger.error(f"转换失败: {str(e)}")
            return False
