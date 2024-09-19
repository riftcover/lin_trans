from PySide6.QtCore import QSettings
from openai import OpenAI
import httpx


def get_proxy_from_settings():
    settings = QSettings("Locoweed", "LinLInTrans")
    use_proxy = settings.value("use_proxy", False, type=bool)
    if not use_proxy:
        return None

    proxy_type = settings.value("proxy_type", "http", type=str)
    host = settings.value("proxy_host", "", type=str)
    port = settings.value("proxy_port", 0, type=int)

    return None if not host or port == 0 else f"{proxy_type}://{host}:{port}"


def create_openai_client(api_key, base_url):
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
