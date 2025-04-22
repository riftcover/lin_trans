import hmac
import hashlib
from ..core.config import settings
from base64 import b64encode


def generate_signature(user_id: str, amount: int, feature_key: str, timestamp: int) -> str:
    """生成代币签名，充值、消费"""
    # 按字典序拼接参数
    params = f"amount={amount}&feature_key={feature_key}&timestamp={timestamp}&user_id={user_id}"

    # 使用HMAC-SHA256算法生成签名
    key = settings.RECHARGE_SECRET_KEY.encode('utf-8')
    message = params.encode('utf-8')
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def get_encryption_key() -> bytes:
    """获取或生成加密密钥"""
    # 使用 RECHARGE_SECRET_KEY 生成一个 32 字节的密钥
    key = hashlib.sha256(settings.RECHARGE_SECRET_KEY.encode()).digest()
    return b64encode(key)


def verify_feature_signature(user_id: str, amount: int, timestamp: int, sign: str, feature_key: str) -> bool:
    """验证功能使用签名

    Args:
        user_id: 用户ID
        amount: 代币数量
        timestamp: 时间戳
        sign: 待验证的签名
        feature_key: 功能键名

    Returns:
        bool: 签名是否有效
    """
    expected_signature = generate_signature(user_id, amount, feature_key, timestamp)

    return hmac.compare_digest(sign, expected_signature)


def generate_transaction_id(timestamp: int, user_id: str, feature_key: str) -> str:
    """生成交易ID

    Args:
        timestamp: 时间戳
        user_id: 用户ID
        feature_key: 功能键名

    Returns:
        str: 交易ID
    """
    return f"USE_{timestamp}_{user_id}_{feature_key}"
