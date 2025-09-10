import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from utils import logger
from services.config_manager import get_summary_length


@dataclass
class SRTEntry:
    """SRT字幕条目"""
    index: int
    start_time: str
    end_time: str
    text: str
    original_header: str  # 保存原始的序号和时间戳行


class SRTTranslatorAdapter:
    """SRT翻译适配器，将SRT格式转换为Translator兼容格式"""

    def __init__(self):
        self.srt_pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'

    def parse_srt_content(self, srt_content: str) -> List[SRTEntry]:
        """解析SRT内容为结构化数据"""
        matches = re.findall(self.srt_pattern, srt_content, re.DOTALL)
        entries = []

        for match in matches:
            index = int(match[0])
            start_time = match[1]
            end_time = match[2]
            text = match[3].strip()
            original_header = f"{index}\n{start_time} --> {end_time}"

            entries.append(SRTEntry(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text,
                original_header=original_header
            ))

        logger.info(f"解析SRT文件，共 {len(entries)} 个字幕条目")
        return entries

    @staticmethod
    def split_entries_into_chunks(entries: List[SRTEntry], chunk_size: int = 600, max_entries: int = 10) -> List[List[SRTEntry]]:
        """将SRT条目分割为适合翻译的块"""
        chunks = []
        current_chunk = []
        current_length = 0

        for entry in entries:
            entry_length = len(entry.text)

            # 检查是否需要开始新块
            if (current_length + entry_length > chunk_size or
                len(current_chunk) >= max_entries) and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [entry]
                current_length = entry_length
            else:
                current_chunk.append(entry)
                current_length += entry_length

        if current_chunk:
            chunks.append(current_chunk)

        logger.info(f"分割为 {len(chunks)} 个翻译块")
        return chunks

    @staticmethod
    def entries_to_text_chunks(entry_chunks: List[List[SRTEntry]]) -> List[str]:
        """将SRT条目块转换为纯文本块"""
        text_chunks = []
        for chunk in entry_chunks:
            text_lines = [entry.text for entry in chunk]
            text_chunks.append('\n'.join(text_lines))
        return text_chunks

    @staticmethod
    def get_context_for_chunk(entry_chunks: List[List[SRTEntry]], chunk_index: int) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """获取指定块的上下文"""
        # 获取前一块的最后3个条目
        previous_context = None
        if chunk_index > 0:
            prev_chunk = entry_chunks[chunk_index - 1]
            previous_context = [entry.text for entry in prev_chunk[-3:]]

        # 获取后一块的前2个条目
        after_context = None
        if chunk_index < len(entry_chunks) - 1:
            next_chunk = entry_chunks[chunk_index + 1]
            after_context = [entry.text for entry in next_chunk[:2]]

        return previous_context, after_context

    @staticmethod
    def rebuild_srt_from_translations(original_entries: List[SRTEntry], translations: List[str]) -> str:
        """将翻译结果重组为SRT格式"""
        if len(original_entries) != len(translations):
            raise ValueError(f"原始条目数量({len(original_entries)})与翻译数量({len(translations)})不匹配")

        srt_lines = []
        for i, (entry, translation) in enumerate(zip(original_entries, translations)):
            srt_lines.extend((entry.original_header, entry.text, translation.strip()))
            # 添加空行分隔符（除了最后一个条目）
            if i < len(original_entries) - 1:
                srt_lines.append("")

        return '\n'.join(srt_lines)

    @staticmethod
    def extract_terminology_context(entries: List[SRTEntry]) -> str:
        """从SRT条目中提取部分文本"""
        # 提取所有文本并清理
        cleaned_sentences = [entry.text.strip() for entry in entries if entry.text.strip()]
        # 用空格连接
        combined_text = ' '.join(cleaned_sentences)

        # 从配置文件获取最大长度
        max_length = get_summary_length()
        if len(combined_text) > max_length:
            combined_text = combined_text[:max_length]
            logger.info(f"术语上下文被截取至 {max_length} 字符")

        return combined_text

    @staticmethod
    def calculate_time_gaps(entries: List[SRTEntry]) -> List[float]:
        """计算字幕之间的时间间隔（用于判断是否需要上下文）"""
        gaps = []
        for _ in range(len(entries) - 1):
            # 这里简化处理，实际可以解析时间戳计算精确间隔
            gaps.append(1.0)  # 默认1秒间隔
        return gaps


def create_trans_compatible_data(srt_content: str, chunk_size: int = 600, max_entries: int = 10) -> Dict:
    """创建trans_agent数据结构"""
    adapter = SRTTranslatorAdapter()

    # 解析SRT内容
    entries = adapter.parse_srt_content(srt_content)

    # 分割为块
    entry_chunks = adapter.split_entries_into_chunks(entries, chunk_size, max_entries)

    # 转换为文本块
    text_chunks = adapter.entries_to_text_chunks(entry_chunks)

    # 截取部分文本
    terminology_context = adapter.extract_terminology_context(entries)

    return {
        'original_entries': entries,
        'entry_chunks': entry_chunks,
        'text_chunks': text_chunks,
        'terminology_context': terminology_context,
        'adapter': adapter
    }