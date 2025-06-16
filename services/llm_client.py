import json

import httpx
import json_repair
from openai import OpenAI
from typing import Any, Optional

from .decorators import except_handler
from utils import logger





def get_proxy_from_settings():
    """
    从设置中获取代理配置
    Returns:
        str or None: 代理URL或None
    """
    try:
        # 尝试从nice_ui设置中获取代理配置
        from nice_ui.ui import SettingsManager
        
        settings = SettingsManager.get_instance()
        use_proxy = settings.value("use_proxy", False, type=bool)
        if not use_proxy:
            return None

        proxy_type = settings.value("proxy_type", "http", type=str)
        host = settings.value("proxy_host", "", type=str)
        port = settings.value("proxy_port", 0, type=int)

        return None if not host or port == 0 else f"{proxy_type}://{host}:{port}"
    except ImportError:
        # 如果nice_ui不可用，返回None
        return None


def create_openai_client(api_key: str, base_url: str) -> OpenAI:
    """
    创建支持代理的OpenAI客户端
    
    Args:
        api_key: API密钥
        base_url: API基础URL
        
    Returns:
        OpenAI: 配置好的OpenAI客户端
    """
    proxy = get_proxy_from_settings()
    http_client = httpx.Client(
        proxies=proxy,
        transport=httpx.HTTPTransport(local_address="0.0.0.0")
    ) if proxy else None

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=http_client
    )


@except_handler("GPT request failed", retry=5, delay=1)
def ask_gpt(model_api, prompt: str, resp_type: Optional[str] = None, 
           valid_def: Optional[callable] = None, log_title: str = "default") -> Any:
    """
    通用的GPT API调用函数
    
    Args:
        model_api: 模型API配置对象，包含key, base_url, model属性
        prompt: 提示词
        resp_type: 响应类型，'json'表示期望JSON响应
        valid_def: 验证函数，用于验证响应格式
        log_title: 日志标题
        
    Returns:
        响应内容，如果resp_type='json'则返回解析后的dict，否则返回字符串
    """
    client = create_openai_client(api_key=model_api.key, base_url=model_api.base_url)

    # 设置响应格式
    response_format = None
    if resp_type == "json":
        # 某些模型支持JSON模式
        try:
            response_format = {"type": "json_object"}
        except Exception:
            # 如果不支持，在提示词中要求JSON格式
            if "json" not in prompt.lower():
                prompt += "\n\n请严格按照JSON格式返回，不要添加任何其他文字。"

    messages = [{"role": "user", "content": prompt}]

    params = dict(
        model=model_api.model,
        messages=messages,
        # response_format=response_format,  # 暂时注释掉，避免某些模型不支持
        timeout=300
    )

    resp_raw = client.chat.completions.create(**params)

    # 处理响应内容
    resp_content = resp_raw.choices[0].message.content
    if resp_type == "json":
        resp = json.loads(resp_content)
    else:
        resp = resp_content

    # 验证响应格式
    if valid_def:
        valid_resp = valid_def(resp)
        logger.trace(valid_resp)
        if valid_resp['status'] != 'success':
            error_msg = f"API response validation failed: {valid_resp['message']}"
            logger.error(error_msg)
            raise ValueError(f"API response error: {valid_resp['message']}")

    logger.info(f"GPT调用成功 ({log_title})")
    return resp 