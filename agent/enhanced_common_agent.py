import time
import concurrent.futures
from typing import List
from difflib import SequenceMatcher

from nice_ui.configure.signal import data_bridge
from utils import logger
from utils.agent_dict import agent_msg, AgentConfig

from .srt_translator_adapter import create_trans_compatible_data
from .videolingo_translator import VideoLingoTranslator, search_things_to_note_in_prompt
from .terminology_manager import TerminologyManager


def similar(a, b):
    """计算相似度"""
    return SequenceMatcher(None, a, b).ratio()


def translate_document_videolingo(unid: str, in_document: str, out_document: str,
                                  agent_name: str,
                                  chunk_size: int = 600, max_entries: int = 10,
                                  sleep_time: int = 1, max_workers: int = 3,
                                  target_language: str = "中文",
                                  source_language: str = "English"):
    """
    使用VideoLingo高级翻译逻辑翻译SRT文件
    
    Args:
        unid: 任务ID
        in_document: 输入SRT文件路径
        out_document: 输出SRT文件路径
        agent_name: API提供方名称
        chunk_size: 每个块的字符数限制
        max_entries: 每个块的最大条目数
        sleep_time: 翻译间隔时间
        max_workers: 并发工作线程数
        target_language: 目标语言
        source_language: 源语言
    """
    agent: AgentConfig = agent_msg[agent_name]
    logger.info(f'翻译开始 - chunk_size: {chunk_size}, max_entries: {max_entries}')

    # 读取SRT文件
    with open(in_document, 'r', encoding='utf-8') as file:
        srt_content = file.read()

    # 使用适配器处理SRT内容
    compat_data = create_trans_compatible_data(srt_content, chunk_size, max_entries)
    original_entries = compat_data['original_entries']
    entry_chunks = compat_data['entry_chunks']
    text_chunks = compat_data['text_chunks']
    terminology_context = compat_data['terminology_context']
    adapter = compat_data['adapter']

    # 创建术语管理器并生成terminology
    terminology_manager = TerminologyManager(f"custom_terms_{unid}.xlsx")

    # 使用AI生成主题和术语
    terminology_data = terminology_manager.generate_summary_and_terminology(
        terminology_context, agent_name, target_language
    )
    theme_prompt = terminology_data.get("theme", "General subtitle content")

    # 保存术语数据
    terminology_file = f"terminology_{unid}.json"
    terminology_manager.save_terminology(terminology_file)

    # 创建翻译器
    translator = VideoLingoTranslator(agent, target_language, source_language)

    # 将术语管理器传递给翻译器（用于术语搜索）
    translator.terminology_manager = terminology_manager

    duration = len(text_chunks)
    logger.info(f"共{duration}个翻译块，开始翻译...")

    # 使用并发翻译
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for i, chunk_text in enumerate(text_chunks):
            # 获取上下文
            previous_context, after_context = adapter.get_context_for_chunk(entry_chunks, i)

            # 创建翻译任务
            future = executor.submit(
                translate_chunk_enhanced,
                translator, chunk_text, previous_context, after_context,
                theme_prompt, i
            )
            futures.append(future)

        # 收集结果
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                result = future.result()
                results.append(result)

                progress_now = int((i + 1) / duration * 100)
                data_bridge.emit_whisper_working(unid, progress_now)
                logger.info(f"翻译进度: {i + 1}/{duration}")

                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Translation task failed: {e}")
                raise e

    # 按原始顺序排序结果
    results.sort(key=lambda x: x[0])

    # 匹配翻译结果到原始条目
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

    # 重建SRT文件
    final_srt = adapter.rebuild_srt_from_translations(original_entries, all_translations)

    # 保存结果
    with open(out_document, 'w', encoding='utf-8') as output_file:
        output_file.write(final_srt)

    data_bridge.emit_whisper_finished(unid)
    logger.info("翻译完成")


def translate_chunk_enhanced(translator: VideoLingoTranslator, chunk_text: str,
                             previous_context: List[str], after_context: List[str],
                             theme_prompt: str, chunk_index: int) -> tuple:
    """增强版块翻译函数"""
    try:
        # 使用术语管理器搜索相关术语
        if hasattr(translator, 'terminology_manager') and translator.terminology_manager:
            things_to_note_prompt = translator.terminology_manager.search_terms_in_sentence(chunk_text)
            if not things_to_note_prompt:
                things_to_note_prompt = "Please pay attention to technical terms, proper nouns, and maintain consistency in translation style."
        else:
            # 回退到原始方法
            things_to_note_prompt = search_things_to_note_in_prompt(chunk_text)

        translation, original = translator.translate_lines(
            chunk_text,
            previous_context,
            after_context,
            things_to_note_prompt,
            theme_prompt,
            chunk_index
        )

        return chunk_index, original, translation

    except Exception as e:
        logger.error(f"Enhanced translation error for chunk {chunk_index}: {e}")
        raise e
