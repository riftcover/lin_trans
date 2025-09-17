#!/usr/bin/env python3
"""
SRT字幕译文删除工具

功能：删除SRT字幕文件中的译文，只保留原文
作者：基于lin_trans项目的SRT处理代码
用法：python remove_srt_translation.py input.srt [output.srt]
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Optional


class SRTTranslationRemover:
    """SRT译文删除器 - Linus风格：简单、直接、有效"""
    
    def __init__(self):
        # SRT条目匹配模式 - 借鉴现有代码的正则表达式
        self.srt_pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
    
    def read_srt_file(self, file_path: str) -> str:
        """读取SRT文件 - 处理编码问题"""
        try:
            # 优先尝试UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # 回退到GBK
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except UnicodeDecodeError as e:
                raise ValueError(f"无法读取文件 {file_path}，编码错误: {e}")
    
    def parse_srt_content(self, content: str) -> List[dict]:
        """解析SRT内容 - 基于现有代码的解析逻辑"""
        matches = re.findall(self.srt_pattern, content, re.DOTALL)
        entries = []
        
        for match in matches:
            index = int(match[0])
            start_time = match[1]
            end_time = match[2]
            text_block = match[3].strip()
            
            # 分割文本块为行
            text_lines = [line.strip() for line in text_block.split('\n') if line.strip()]
            
            entries.append({
                'index': index,
                'start_time': start_time,
                'end_time': end_time,
                'text_lines': text_lines,
                'original_text': text_lines[0] if text_lines else ''
            })
        
        return entries
    
    def remove_translations(self, entries: List[dict]) -> List[dict]:
        """删除译文 - 只保留每个条目的第一行文本"""
        cleaned_entries = []
        
        for entry in entries:
            # 只保留第一行（原文），删除后续行（译文）
            cleaned_entry = {
                'index': entry['index'],
                'start_time': entry['start_time'],
                'end_time': entry['end_time'],
                'text': entry['original_text']
            }
            cleaned_entries.append(cleaned_entry)
        
        return cleaned_entries
    
    def rebuild_srt_content(self, entries: List[dict]) -> str:
        """重建SRT内容 - 标准SRT格式"""
        srt_lines = []
        
        for i, entry in enumerate(entries):
            # 序号
            srt_lines.append(str(entry['index']))
            # 时间戳
            srt_lines.append(f"{entry['start_time']} --> {entry['end_time']}")
            # 文本（只有原文）
            srt_lines.append(entry['text'])
            
            # 添加空行分隔符（除了最后一个条目）
            if i < len(entries) - 1:
                srt_lines.append('')
        
        return '\n'.join(srt_lines)
    
    def process_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """处理SRT文件 - 主要处理流程"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
        
        # 确定输出路径
        if output_path is None:
            input_file = Path(input_path)
            output_path = str(input_file.parent / f"{input_file.stem}_no_translation{input_file.suffix}")
        
        print(f"读取文件: {input_path}")
        content = self.read_srt_file(input_path)
        
        print("解析SRT内容...")
        entries = self.parse_srt_content(content)
        print(f"找到 {len(entries)} 个字幕条目")
        
        print("删除译文...")
        cleaned_entries = self.remove_translations(entries)
        
        print("重建SRT内容...")
        cleaned_content = self.rebuild_srt_content(cleaned_entries)
        
        print(f"保存到: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"✅ 处理完成！译文已删除，原文保留在: {output_path}")
        return output_path



def main(input_path, output_path):
    remover = SRTTranslationRemover()
    output_path = remover.process_file(input_path, output_path)



if __name__ == '__main__':
    a = r'D:\dcode\lin_trans\result\455e303cf02eabaa2c33682f187a523e\SMK 스키 세미나 실전편ㅣ기초 카빙 방향성ㅣ김민수 데몬.srt'
    b = r'D:\dcode\lin_trans\result\455e303cf02eabaa2c33682f187a523e\SMK 스키 세미나 실전편ㅣ기초 카빙 방향성ㅣ김민수 데몬.srt'
    main(a,b)
