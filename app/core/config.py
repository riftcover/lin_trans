import os
import secrets  # 用于生成安全的随机字符串
from typing import List

from pydantic_settings import BaseSettings


def get_cors_origins():
    return ["http://localhost:3000"]


def generate_secret_key():
    """生成一个安全的随机密钥"""
    return secrets.token_hex(32)  # 生成64个字符的十六进制字符串


class Settings(BaseSettings):
    PROJECT_NAME: str = "Lapped AI API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # 从环境变量获取，如果没有则生成一个新的
    RECHARGE_SECRET_KEY: str = os.getenv(
        "RECHARGE_SECRET_KEY", 
        "cbb5eb43a99a541ec1d59324c3d3b560146c5d4d985cc8528f0e0aa682a3c162"  # 示例密钥
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


settings = Settings()
