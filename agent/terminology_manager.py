import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from services.llm_client import ask_gpt
from utils import logger
from utils.agent_dict import agent_msg, AgentConfig


class TerminologyManager:
    """术语管理器"""

    def __init__(self, custom_terms_path: str = "custom_terms.xlsx"):
        # 当前未使用自定义术语功能，后期添加后打开
        # self.custom_terms_path = custom_terms_path
        self.terminology_data = {
            "theme": "",
            "terms": []
        }

    def load_custom_terms(self) -> Dict[str, Any]:
        """加载自定义术语文件"""
        # if not os.path.exists(self.custom_terms_path):
        #     # 创建示例文件
        #     self._create_sample_custom_terms()

        # try:
        # custom_terms = pd.read_excel(self.custom_terms_path)
        # custom_terms_json = {
        #     "terms": [
        #         {
        #             "src": str(row.iloc[0]) if pd.notna(row.iloc[0]) else "",
        #             "tgt": str(row.iloc[1]) if pd.notna(row.iloc[1]) else "",
        #             "note": str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
        #         }
        #         for _, row in custom_terms.iterrows()
        #         if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip()
        #     ]
        # }
        #     custom_terms_json = {
        #         "src Term": "",
        #         "tgt": "",
        #         "Note": ""
        #     }
        #     print(f"📖 Custom Terms Loaded: {len(custom_terms_json['terms'])} terms")
        #     return custom_terms_json
        # except Exception as e:
        #     print(f"⚠️ Failed to load custom terms: {e}")
        return {"terms": []}

    def generate_summary_and_terminology(self, content: str, agent_name: str,
                                         target_language: str = "中文") -> Dict[str, Any]:
        """生成内容总结和术语提取"""

        # 限制内容长度
        content = content[:2000]

        # 加载自定义术语
        custom_terms = self.load_custom_terms()

        # 生成总结和术语提取的提示
        summary_prompt = self._get_summary_prompt(content, custom_terms, target_language)

        # 调用AI生成总结
        agent_config: AgentConfig = agent_msg[agent_name]

        # 定义验证函数
        def valid_summary(response_data):
            required_keys = {'src', 'tgt', 'note'}
            if 'terms' not in response_data:
                return {"status": "error", "message": "Missing 'terms' key in response"}
            if 'theme' not in response_data:
                return {"status": "error", "message": "Missing 'theme' key in response"}
            for term in response_data['terms']:
                if any(key not in term for key in required_keys):
                    return {"status": "error", "message": f"Missing required keys in term: {required_keys}"}
            return {"status": "success", "message": "Summary completed"}

        try:
            # ask_gpt调用
            summary_data = ask_gpt(
                agent_config,
                summary_prompt,
                resp_type='json',
                valid_def=valid_summary,
                log_title='terminology_summary'
            )

            # 验证响应格式
            if not self._validate_summary_response(summary_data):
                raise ValueError("Invalid summary response format")

            # 合并自定义术语
            if custom_terms["terms"]:
                summary_data["terms"].extend(custom_terms["terms"])

            self.terminology_data = summary_data
            logger.info(f"Generated summary with {len(summary_data['terms'])} terms")
            logger.info("===summary_data===")
            logger.info(summary_data)
            return summary_data

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # 返回默认结构
            default_summary = {
                "theme": f"This appears to be {target_language} subtitle content",
                "terms": custom_terms["terms"]
            }
            self.terminology_data = default_summary
            return default_summary

    def _get_summary_prompt(self, content: str, custom_terms: Dict, target_language: str) -> str:
        """生成总结提示词"""
        custom_terms_text = ""
        if custom_terms["terms"]:
            custom_terms_text = "\n\n已知术语参考：\n"
            for term in custom_terms["terms"]:
                custom_terms_text += f"- {term['src']} → {term['tgt']} ({term['note']})\n"

        prompt = f"""请分析以下字幕内容，提取关键术语并生成主题描述。

内容：
{content}

{custom_terms_text}

请按以下JSON格式返回：
{{
    "theme": "内容主题的简短描述（用{target_language}）",
    "terms": [
        {{
            "src": "源语言术语",
            "tgt": "{target_language}翻译",
            "note": "术语说明或上下文"
        }}
    ]
}}

要求：
1. theme应该是对内容主题的简洁描述
2. 提取5-15个重要术语
3. 术语应包括专业词汇、人名、地名、品牌名等
4. 翻译要准确且符合{target_language}习惯
5. note提供必要的上下文说明

请确保返回有效的JSON格式。"""

        return prompt

    def _validate_summary_response(self, response_data: Any) -> bool:
        """验证总结响应格式"""
        if not isinstance(response_data, dict):
            return False

        if "theme" not in response_data or "terms" not in response_data:
            return False

        if not isinstance(response_data["terms"], list):
            return False

        required_keys = {"src", "tgt", "note"}
        for term in response_data["terms"]:
            if not isinstance(term, dict):
                return False
            if not all(key in term for key in required_keys):
                return False

        return True

    def search_terms_in_sentence(self, sentence: str) -> Optional[str]:
        """在句子中搜索相关术语（模拟search_things_to_note_in_prompt）"""
        if not self.terminology_data["terms"]:
            return None

        found_terms = []
        sentence_lower = sentence.lower()

        for term in self.terminology_data["terms"]:
            src_term = term["src"].lower()
            if src_term in sentence_lower:
                found_terms.append(term)

        if found_terms:
            prompt_lines = []
            for i, term in enumerate(found_terms):
                prompt_lines.append(
                    f'{i + 1}. "{term["src"]}": "{term["tgt"]}", meaning: {term["note"]}'
                )
            return '\n'.join(prompt_lines)

        return None

    def save_terminology(self, filepath: str):
        """保存术语数据到文件"""
        try:
            filepath_obj = Path(filepath)
            # 确保父目录存在
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath_obj, 'w', encoding='utf-8') as f:
                json.dump(self.terminology_data, f, ensure_ascii=False, indent=4)
            logger.info(f"术语数据已保存到: {filepath_obj}")
        except Exception as e:
            logger.error(f"保存术语数据失败: {e}")

    def load_terminology(self, filepath: str) -> bool:
        """从文件加载术语数据"""
        try:
            filepath_obj = Path(filepath)
            if filepath_obj.exists():
                with open(filepath_obj, 'r', encoding='utf-8') as f:
                    self.terminology_data = json.load(f)
                logger.info(f"📖 术语数据已从文件加载: {filepath_obj}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 加载术语数据失败: {e}")
            return False

    def get_theme(self) -> str:
        """获取内容主题"""
        return self.terminology_data.get("theme", "")

    def get_terms(self) -> List[Dict[str, str]]:
        """获取所有术语"""
        return self.terminology_data.get("terms", [])

    def add_custom_term(self, src: str, tgt: str, note: str = ""):
        """添加自定义术语"""
        new_term = {"src": src, "tgt": tgt, "note": note}
        self.terminology_data["terms"].append(new_term)

    # def update_custom_terms_file(self, terms: List[Dict[str, str]]):
    #     """更新自定义术语文件"""
    #     try:
    #         df_data = {
    #             "Source Term": [term["src"] for term in terms],
    #             "Target Translation": [term["tgt"] for term in terms],
    #             "Note": [term["note"] for term in terms]
    #         }
    #         df = pd.DataFrame(df_data)
    #         df.to_excel(self.custom_terms_path, index=False)
    #         print(f"💾 Updated custom terms file: {self.custom_terms_path}")
    #     except Exception as e:
    #         print(f"❌ Failed to update custom terms file: {e}")


def create_terminology_for_content(content: str, agent_name: str,
                                   target_language: str = "中文",
                                   custom_terms_path: str = "custom_terms.xlsx") -> TerminologyManager:
    """为内容创建术语管理器的便捷函数"""
    manager = TerminologyManager(custom_terms_path)
    manager.generate_summary_and_terminology(content, agent_name, target_language)
    return manager


if __name__ == "__main__":
    # 测试示例
    sample_content = """
    Welcome to this machine learning tutorial. Today we'll discuss neural networks,
    artificial intelligence, and deep learning algorithms. We'll cover topics like
    gradient descent, backpropagation, and convolutional neural networks.
    """

    manager = create_terminology_for_content(
        content=sample_content,
        agent_name="qwen_cloud",
        target_language="中文"
    )

    # 测试术语搜索
    # test_sentence = "Neural networks are fundamental to artificial intelligence"
    # terms_prompt = manager.search_terms_in_sentence(test_sentence)
    # if terms_prompt:
    #     print("Found terms:")
    #     print(terms_prompt)
