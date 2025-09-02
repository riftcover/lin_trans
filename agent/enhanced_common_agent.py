import time
from typing import List
from difflib import SequenceMatcher

from nice_ui.configure.signal import data_bridge
from utils import logger
from utils.agent_dict import agent_settings, AgentConfig

from .srt_translator_adapter import create_trans_compatible_data
from .translator import Translator, search_things_to_note_in_prompt
from .terminology_manager import TerminologyManager


def similar(a, b):
    """计算相似度"""
    return SequenceMatcher(None, a, b).ratio()


class DocumentTranslator:
    """文档翻译器"""
    
    def __init__(self, agent_name: str, target_language: str = "中文", 
                 source_language: str = "English"):
        """
        初始化文档翻译器
        
        Args:
            agent_name: API提供方名称
            target_language: 目标语言
            source_language: 源语言
        """
        self.agent_name = agent_name
        self.target_language = target_language
        self.source_language = source_language
        self.translator = None
        self.theme_prompt = None
        self.adapter = None
        self.compat_data = None
    
    def _load_srt_content(self, in_document: str) -> str:
        """加载SRT文件内容"""
        logger.trace('加载SRT文件内容')
        with open(in_document, 'r', encoding='utf-8') as file:
            return file.read()
    
    def _prepare_translation_data(self, srt_content: str, chunk_size: int, max_entries: int):
        """准备翻译数据"""
        self.compat_data = create_trans_compatible_data(srt_content, chunk_size, max_entries)
        self.adapter = self.compat_data['adapter']
    
    def _setup_translator(self):
        """设置翻译器和术语管理器"""
        # 动态获取最新的agent配置，确保能获取到用户刚保存的key
        current_agent_configs = agent_settings()
        agent: AgentConfig = current_agent_configs[self.agent_name]

        # 检查agent.key是否为None
        if agent.key is None:
            error_msg = "请填写API密钥"
            logger.error(f"翻译任务停止: {error_msg}")
            raise ValueError(error_msg)

        # 创建术语管理器并生成terminology
        terminology_manager = TerminologyManager()
        terminology_data = terminology_manager.generate_summary_and_terminology(
            self.compat_data['terminology_context'], self.agent_name, self.target_language
        )
        self.theme_prompt = terminology_data.get("theme", "General subtitle content")

        # 创建翻译器
        self.translator = Translator(agent, self.target_language, self.source_language)
        self.translator.terminology_manager = terminology_manager
    
    def _translate_chunks(self, unid: str, sleep_time: int) -> List:
        """翻译所有文本块"""
        text_chunks = self.compat_data['text_chunks']
        entry_chunks = self.compat_data['entry_chunks']
        duration = len(text_chunks)
        
        logger.info(f"共{duration}个翻译块，开始翻译...")
        
        results = []
        for i, chunk_text in enumerate(text_chunks):
            try:
                # 获取上下文
                previous_context, after_context = self.adapter.get_context_for_chunk(entry_chunks, i)

                # 直接调用翻译函数
                result = self._translate_chunk(
                    chunk_text, previous_context, after_context, i
                )
                results.append(result)

                progress_now = int((i + 1) / duration * 100)
                data_bridge.emit_whisper_working(unid, progress_now)
                logger.info(f"翻译进度: {i + 1}/{duration}")

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Translation task failed: {e}")
                raise e
        
        return results
    
    def _translate_chunk(self, chunk_text: str, previous_context: List[str], 
                        after_context: List[str], chunk_index: int) -> tuple:
        """翻译单个文本块"""
        try:
            # 使用术语管理器搜索相关术语
            if hasattr(self.translator, 'terminology_manager') and self.translator.terminology_manager:
                things_to_note_prompt = self.translator.terminology_manager.search_terms_in_sentence(
                    chunk_text) or "Please pay attention to technical terms, proper nouns, and maintain consistency in translation style."
            else:
                # 回退到原始方法
                things_to_note_prompt = search_things_to_note_in_prompt()

            translation, original = self.translator.translate_lines(
                chunk_text,
                previous_context,
                after_context,
                things_to_note_prompt,
                self.theme_prompt,
                chunk_index
            )

            return chunk_index, original, translation

        except Exception as e:
            logger.error(f"Enhanced translation error for chunk {chunk_index}: {e}")
            raise e
    
    def _match_translations_to_entries(self, results: List) -> List[str]:
        """将翻译结果匹配到原始条目"""
        entry_chunks = self.compat_data['entry_chunks']
        text_chunks = self.compat_data['text_chunks']
        
        # results 已经按照顺序处理，不需要排序
        
        all_translations = []
        for i, chunk_entries in enumerate(entry_chunks):
            chunk_text = text_chunks[i]

            # 找到匹配的翻译结果
            matching_results = [(r, similar(''.join(r[1].split('\n')).lower(), chunk_text.lower()))
                                for r in results]
            best_match = max(matching_results, key=lambda x: x[1])

            if best_match[1] < 0.8:
                logger.warning(f"Low similarity match for chunk {i}: {best_match[1]:.3f}")

            # 将翻译结果分割并匹配到各个条目
            translation_lines = best_match[0][2].split('\n')

            if len(translation_lines) != len(chunk_entries):
                logger.warning(f"Translation lines count mismatch for chunk {i}: {len(translation_lines)} vs {len(chunk_entries)}")
                # 尝试调整
                while len(translation_lines) < len(chunk_entries):
                    translation_lines.append(translation_lines[-1] if translation_lines else "")
                translation_lines = translation_lines[:len(chunk_entries)]

            all_translations.extend(translation_lines)
        
        return all_translations
    
    def _save_translated_srt(self, all_translations: List[str], out_document: str):
        """保存翻译后的SRT文件"""
        original_entries = self.compat_data['original_entries']
        
        # 重建SRT文件
        final_srt = self.adapter.rebuild_srt_from_translations(original_entries, all_translations)

        # 保存结果
        with open(out_document, 'w', encoding='utf-8') as output_file:
            output_file.write(final_srt)
    
    def translate(self, unid: str, in_document: str, out_document: str,
                 chunk_size: int = 600, max_entries: int = 10, sleep_time: int = 1):
        """
        执行翻译
        
        Args:
            unid: 任务ID
            in_document: 输入SRT文件路径
            out_document: 输出SRT文件路径
            chunk_size: 每个块的字符数限制
            max_entries: 每个块的最大条目数
            sleep_time: 翻译间隔时间
        """
        logger.info(f'翻译开始 - chunk_size: {chunk_size}, max_entries: {max_entries}')

        try:
            # 1. 加载和准备数据
            srt_content = self._load_srt_content(in_document)
            self._prepare_translation_data(srt_content, chunk_size, max_entries)
            
            # 2. 设置翻译器
            self._setup_translator()
            
            # 3. 执行翻译
            results = self._translate_chunks(unid, sleep_time)
            
            # 4. 匹配翻译结果
            all_translations = self._match_translations_to_entries(results)
            
            # 5. 保存结果
            self._save_translated_srt(all_translations, out_document)

            data_bridge.emit_whisper_finished(unid)
            logger.info("翻译完成")
            
        except Exception as e:
            logger.error(f"翻译过程出错: {e}")
            raise e


def translate_document(unid: str, in_document: str, out_document: str,
                       agent_name: str,
                       chunk_size: int = 600, max_entries: int = 10,
                       sleep_time: int = 1,
                       target_language: str = "中文",
                       source_language: str = "English"):
    """
    翻译SRT文件（兼容性函数）
    
    Args:
        unid: 任务ID
        in_document: 输入SRT文件路径
        out_document: 输出SRT文件路径
        agent_name: API提供方名称
        chunk_size: 每个块的字符数限制
        max_entries: 每个块的最大条目数
        sleep_time: 翻译间隔时间
        target_language: 目标语言
        source_language: 源语言
    """
    translator = DocumentTranslator(agent_name, target_language, source_language)
    translator.translate(unid, in_document, out_document, chunk_size, max_entries, sleep_time)



