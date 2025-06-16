import httpx
from openai import OpenAI
import json_repair
from nice_ui.ui import SettingsManager
from utils import logger
from utils.decorators import except_handler


def get_proxy_from_settings():
    """
    get proxy from settings.
    通过settings获取gui程序QNetworkProxy.setApplicationProxy设置的代理
    Returns:

    """
    settings = SettingsManager.get_instance()
    use_proxy = settings.value("use_proxy", False, type=bool)
    if not use_proxy:
        return None

    proxy_type = settings.value("proxy_type", "http", type=str)
    host = settings.value("proxy_host", "", type=str)
    port = settings.value("proxy_port", 0, type=int)

    return None if not host or port == 0 else f"{proxy_type}://{host}:{port}"


def create_openai_client(api_key: str, base_url: str):
    """
    由于OpenAI client不会自动读取gui设置的系统代理，所以创建使用代理的client
    because the openai client doesn't support proxy, we need to create our own client with proxy support.
    Args:
        api_key:  String, the api key of openai.
        base_url:   String, the base url of openai.

    Returns:

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

# @except_handler("GPT request failed", retry=5, delay=1)
def ask_gpt(model_api,prompt, resp_type=None, valid_def=None, log_title="default"):

    # if 'ark' in base_url:
    #     base_url = "https://ark.cn-beijing.volces.com/api/v3"  # huoshan base url
    # elif 'v1' not in base_url:
    #     base_url = base_url.strip('/') + '/v1'
    client = create_openai_client(api_key=model_api.key, base_url=model_api.base_url)
    # response_format = {"type": "json_object"} if resp_type == "json" and load_key("api.llm_support_json") else None
    # 设置响应格式
    response_format = None
    if resp_type == "json":
        # 某些模型支持JSON模式
        try:
            response_format = {"type": "json_object"}
        except:
            # 如果不支持，在提示词中要求JSON格式
            if "json" not in prompt.lower():
                prompt += "\n\n请严格按照JSON格式返回，不要添加任何其他文字。"

    messages = [{"role": "user", "content": prompt}]

    params = dict(
        model=model_api.model,
        messages=messages,
        # response_format=response_format,
        timeout=300
    )
    resp_raw = client.chat.completions.create(**params)

    # process and return full result
    resp_content = resp_raw.choices[0].message.content
    if resp_type == "json":
        resp = json_repair.loads(resp_content)
    else:
        resp = resp_content

    # check if the response format is valid
    valid_resp = valid_def(resp)
    logger.trace(valid_resp)
    if valid_def:
        valid_resp = valid_def(resp)
        if valid_resp['status'] != 'success':
            error_msg = f"API response validation failed: {valid_resp['message']}"
            logger.error(error_msg)
            raise ValueError(f"API response error: {valid_resp['message']}")

    logger.info(f"GPT调用成功 ({log_title})")
    return resp
