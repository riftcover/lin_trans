"""
极简异常类 - 只保留必要的异常

Linus 原则：
- "简单就是美"
- "不要为假想的需求过度设计"
- UI 层不关心异常类型，只关心错误消息
- error_handler 可以从字符串中解析错误类型

因此，只保留 2 个真正需要的异常类：
1. AuthenticationError - Token 过期，需要重新登录（特殊处理）
2. InvalidCredentialsError - 账号密码错误（登录时）
"""


class APIException(Exception):
    """API 异常基类

    简单设计：只包含 error_code 和 detail
    error_code 用于 UI 层查找用户友好的消息
    detail 用于日志记录
    """

    def __init__(self, error_code: str, detail: str = ""):
        self.error_code = error_code
        self.detail = detail
        super().__init__(f"[{error_code}] {detail}")


class InvalidCredentialsError(APIException):
    """账号或密码错误（登录时）"""
    def __init__(self, detail: str = ""):
        super().__init__("INVALID_CREDENTIALS", detail)


class AuthenticationError(APIException):
    """认证失败（Token 已过期或无效）- 需要重新登录"""
    def __init__(self, detail: str = ""):
        super().__init__("AUTHENTICATION_FAILED", detail)

