import json
from typing import Dict, List, Optional, Tuple

from services.llm_client import ask_gpt
from utils import logger
from utils.agent_dict import AgentConfig


class Translator:
    """翻译器"""

    def __init__(self, agent: AgentConfig, target_language: str = "中文", source_language: str = "English"):
        self.agent = agent
        self.target_language = target_language
        self.source_language = source_language
        self.reflect_translate = True  # 是否使用两步翻译
        self.terminology_manager = None  # 术语管理器，由外部设置

    def generate_shared_prompt(self, previous_content_prompt: Optional[List[str]],
                               after_content_prompt: Optional[List[str]],
                               summary_prompt: str,
                               things_to_note_prompt: str) -> str:
        """生成共享提示"""
        previous_content = ""
        if previous_content_prompt:
            previous_content = "\n".join(previous_content_prompt)

        after_content = ""
        if after_content_prompt:
            after_content = "\n".join(after_content_prompt)

        return f'''### Context Information
<previous_content>
{previous_content}
</previous_content>

<subsequent_content>
{after_content}
</subsequent_content>

### Content Summary
{summary_prompt}

### Points to Note
{things_to_note_prompt}'''

    def get_prompt_faithfulness(self, lines: str, shared_prompt: str) -> str:
        """获取忠实翻译提示"""
        line_splits = lines.split('\n')

        json_dict = {}
        for i, line in enumerate(line_splits, 1):
            json_dict[f"{i}"] = {"origin": line, "direct": f"direct {self.target_language} translation {i}."}
        json_format = json.dumps(json_dict, indent=2, ensure_ascii=False)

        prompt_faithfulness = f'''
## Role
You are a professional Netflix subtitle translator, fluent in both {self.source_language} and {self.target_language}, as well as their respective cultures. 
Your expertise lies in accurately understanding the semantics and structure of the original {self.source_language} text and faithfully translating it into {self.target_language} while preserving the original meaning.

## Task
We have a segment of original {self.source_language} subtitles that need to be directly translated into {self.target_language}. These subtitles come from a specific context and may contain specific themes and terminology.

1. Translate the original {self.source_language} subtitles into {self.target_language} line by line
2. Ensure the translation is faithful to the original, accurately conveying the original meaning
3. Consider the context and professional terminology

{shared_prompt}

<translation_principles>
1. Faithful to the original: Accurately convey the content and meaning of the original text, without arbitrarily changing, adding, or omitting content.
2. Accurate terminology: Use professional terms correctly and maintain consistency in terminology.
3. Understand the context: Fully comprehend and reflect the background and contextual relationships of the text.
</translation_principles>

## INPUT
<subtitles>
{lines}
</subtitles>

## Output in only JSON format and no other text
```json
{json_format}
```

Note: Start you answer with ```json and end with ```, do not add any other text.
'''
        return prompt_faithfulness.strip()

    def get_prompt_expressiveness(self, faithfulness_result: Dict, lines: str, shared_prompt: str) -> str:
        """获取表达优化提示"""
        json_format = {
            key: {
                "origin": value["origin"],
                "direct": value["direct"],
                "reflect": "your reflection on direct translation",
                "free": "your free translation"
            }
            for key, value in faithfulness_result.items()
        }
        json_format = json.dumps(json_format, indent=2, ensure_ascii=False)

        prompt_expressiveness = f'''
## Role
You are a professional Netflix subtitle translator and language consultant.
Your expertise lies not only in accurately understanding the original {self.source_language} but also in optimizing the {self.target_language} translation to better suit the target language's expression habits and cultural background.

## Task
We already have a direct translation version of the original {self.source_language} subtitles.
Your task is to reflect on and improve these direct translations to create more natural and fluent {self.target_language} subtitles.

1. Analyze the direct translation results line by line, pointing out existing issues
2. Provide detailed modification suggestions
3. Perform free translation based on your analysis
4. Do not add comments or explanations in the translation, as the subtitles are for the audience to read
5. Do not leave empty lines in the free translation, as the subtitles are for the audience to read

{shared_prompt}

<Translation Analysis Steps>
Please use a two-step thinking process to handle the text line by line:

1. Direct Translation Reflection:
   - Evaluate language fluency
   - Check if the language style is consistent with the original text
   - Check the conciseness of the subtitles, point out where the translation is too wordy

2. {self.target_language} Free Translation:
   - Aim for contextual smoothness and naturalness, conforming to {self.target_language} expression habits
   - Ensure it's easy for {self.target_language} audience to understand and accept
   - Adapt the language style to match the theme (e.g., use casual language for tutorials, professional terminology for technical content, formal language for documentaries)
</Translation Analysis Steps>
   
## INPUT
<subtitles>
{lines}
</subtitles>

## Output in only JSON format and no other text
```json
{json_format}
```

Note: Start you answer with ```json and end with ```, do not add any other text.
'''
        return prompt_expressiveness.strip()

    def valid_translate_result(self, result: dict, required_keys: list, required_sub_keys: list) -> Dict[str, str]:
        """验证翻译结果"""
        # 检查所需键
        if any(key not in result for key in required_keys):
            return {"status": "error", "message": f"Missing required key(s): {', '.join(set(required_keys) - set(result.keys()))}"}

        # 检查所有项目中的所需子键
        for key in result:
            if not all(sub_key in result[key] for sub_key in required_sub_keys):
                return {"status": "error",
                        "message": f"Missing required sub-key(s) in item {key}: {', '.join(set(required_sub_keys) - set(result[key].keys()))}"}

        return {"status": "success", "message": "Translation completed"}

    def translate_lines(self, lines: str, previous_content_prompt: Optional[List[str]],
                        after_content_prompt: Optional[List[str]],
                        things_to_note_prompt: str,
                        summary_prompt: str,
                        index: int = 0) -> Tuple[str, str]:
        """翻译文本行"""
        shared_prompt = self.generate_shared_prompt(previous_content_prompt, after_content_prompt, summary_prompt, things_to_note_prompt)

        # 翻译函数
        def translate_with_validation(prompt: str, length: int, step_name: str):
            def valid_faith(response_data):
                return self.valid_translate_result(response_data, [str(i) for i in range(1, length + 1)], ['direct'])

            def valid_express(response_data):
                return self.valid_translate_result(response_data, [str(i) for i in range(1, length + 1)], ['free'])

            try:
                # 使用ask_gpt函数，它自带重试机制
                result = ask_gpt(
                    model_api=self.agent,
                    prompt=prompt,
                    resp_type='json',
                    valid_def=valid_faith if step_name == 'faithfulness' else valid_express,
                    log_title=f'translate_{step_name}_{index}'
                )

                # 验证结果长度
                expected_length = len(lines.split('\n'))
                if expected_length != len(result):
                    error_msg = f'{step_name.capitalize()} translation length mismatch: expected {expected_length}, got {len(result)}'
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                return result

            except Exception as e:
                logger.error(f'Block {index} {step_name} translation failed: {e}')
                raise e

        # 第一步：忠实翻译
        prompt1 = self.get_prompt_faithfulness(lines, shared_prompt)
        faith_result = translate_with_validation(prompt1, len(lines.split('\n')), 'faithfulness')
        logger.trace(f"Block {index} - Using faithfulness")
        logger.trace(faith_result)

        for i in faith_result:
            faith_result[i]["direct"] = faith_result[i]["direct"].replace('\n', ' ')

        # 如果不使用反思翻译，直接使用忠实翻译
        if not self.reflect_translate:
            translate_result = "\n".join([faith_result[i]["direct"].strip() for i in faith_result])
            logger.info(f"Block {index} - Using direct translation only")
            return translate_result, lines

        # 第二步：表达优化
        prompt2 = self.get_prompt_expressiveness(faith_result, lines, shared_prompt)
        express_result = translate_with_validation(prompt2, len(lines.split('\n')), 'expressiveness')
        logger.trace(f"Block {index} - Using expressiveness")
        logger.trace(express_result)

        translate_result = "\n".join([express_result[i]["free"].replace('\n', ' ').strip() for i in express_result])

        if len(lines.split('\n')) != len(translate_result.split('\n')):
            logger.error(f'Translation of block {index} failed, Length Mismatch')
            raise ValueError(f'Origin: {lines}, but got: {translate_result}')

        logger.info(f"Block {index} - Two-step translation completed")
        return translate_result, lines


def search_things_to_note_in_prompt() -> str:
    """搜索需要注意的事项（简化版本）"""
    # 这里可以根据需要实现更复杂的术语识别逻辑
    # 目前返回基本的注意事项
    return "Please pay attention to technical terms, proper nouns, and maintain consistency in translation style."
