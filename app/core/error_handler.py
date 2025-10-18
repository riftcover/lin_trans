"""
简化的错误处理服务
将 error_code 转换为用户友好的消息（支持多语言）
"""
from app.core.exceptions import APIException


# 错误消息映射表 - 简单的字典，支持多语言
ERROR_MESSAGES = {
    # 认证相关
    "INVALID_CREDENTIALS": {
        "zh": "账号或密码错误",
        "en": "Invalid email or password"
    },
    "AUTHENTICATION_FAILED": {
        "zh": "登录已过期，请重新登录",
        "en": "Authentication failed, please login again"
    },
    "ACCOUNT_DISABLED": {
        "zh": "账号已被禁用，请联系管理员",
        "en": "Account has been disabled"
    },
    "ACCOUNT_NOT_FOUND": {
        "zh": "账号不存在",
        "en": "Account not found"
    },

    # 请求相关
    "TOO_MANY_REQUESTS": {
        "zh": "登录尝试过于频繁，请稍后再试",
        "en": "Too many attempts, please try again later"
    },
    "VALIDATION_ERROR": {
        "zh": "请求参数错误，请检查输入",
        "en": "Invalid request parameters"
    },

    # 服务器相关
    "SERVER_ERROR": {
        "zh": "服务器暂时无法响应，请稍后再试",
        "en": "Server temporarily unavailable"
    },

    # 网络相关
    "NETWORK_ERROR": {
        "zh": "网络连接失败，请检查网络设置",
        "en": "Network connection failed"
    },
    "TIMEOUT": {
        "zh": "请求超时，请检查网络连接",
        "en": "Request timeout"
    },

    # 默认
    "UNKNOWN_ERROR": {
        "zh": "操作失败，请稍后重试",
        "en": "Operation failed"
    }
}


def get_error_message(error: Exception, lang: str = "zh") -> str:
    """获取用户友好的错误消息 - 简化版本

    Args:
        error: 异常对象
        lang: 语言代码（"zh" 或 "en"）

    Returns:
        str: 用户友好的错误消息
    """
    # 如果是结构化异常，直接查找 error_code
    if isinstance(error, APIException):
        messages = ERROR_MESSAGES.get(error.error_code)
        if messages:
            return messages.get(lang, messages["en"])
        return ERROR_MESSAGES["UNKNOWN_ERROR"][lang]

    # 兼容旧代码：解析字符串异常
    error_msg = str(error).lower()

    if "status 401" in error_msg or "invalid login credentials" in error_msg:
        return ERROR_MESSAGES["INVALID_CREDENTIALS"][lang]
    elif "status 403" in error_msg or "disabled" in error_msg:
        return ERROR_MESSAGES["ACCOUNT_DISABLED"][lang]
    elif "status 404" in error_msg or "not found" in error_msg:
        return ERROR_MESSAGES["ACCOUNT_NOT_FOUND"][lang]
    elif "status 429" in error_msg or "too many" in error_msg:
        return ERROR_MESSAGES["TOO_MANY_REQUESTS"][lang]
    elif any(f"status {code}" in error_msg for code in [500, 502, 503]):
        return ERROR_MESSAGES["SERVER_ERROR"][lang]
    elif "connection" in error_msg or "network" in error_msg:
        return ERROR_MESSAGES["NETWORK_ERROR"][lang]
    elif "timeout" in error_msg:
        return ERROR_MESSAGES["TIMEOUT"][lang]
    else:
        return ERROR_MESSAGES["UNKNOWN_ERROR"][lang]

