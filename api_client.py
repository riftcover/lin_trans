import httpx
from typing import Optional, Dict, Callable
from functools import wraps

import asyncio
from concurrent.futures import ThreadPoolExecutor

from utils import logger


class AuthenticationError(Exception):
    """认证错误，用于处理401错误"""
    pass


def to_sync(func: Callable):
    """将异步方法转换为同步方法的装饰器"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        return _run_async(func(self, *args, **kwargs))

    return wrapper


def _get_event_loop():
    """获取或创建事件循环"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _run_async(coro):
    """在线程池中运行异步代码"""
    loop = _get_event_loop()
    return loop.run_until_complete(coro)


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=15.0)
        self._token: Optional[str] = None
        self._executor = ThreadPoolExecutor(max_workers=1)

    def load_token_from_settings(self, settings) -> bool:
        """
        从配置中加载token

        Args:
            settings: QSettings实例

        Returns:
            bool: 是否成功加载token
        """
        token = settings.value('token')
        if token:
            self._token = token
            logger.trace('Token loaded from settings')
            return True
        return False

    def clear_token(self):
        """清除token"""
        self._token = None
        logger.trace('Token cleared')

    @property
    def headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def login(self, email: str, password: str) -> Dict:
        """
        用户登录（异步版本）

        Args:
            email: 用户邮箱
            password: 用户密码

        Returns:
            Dict: 包含用户信息和token的响应数据
        """
        try:
            response = await self.client.post("/auth/login", json={"email": email, "password": password}, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            self._update_token(data)
            return data
        except httpx.HTTPError as e:
            logger.error(f'Login failed: {e}')
            raise Exception(f"登录失败: {str(e)}")

    def _update_token(self, response_data: Dict) -> None:
        """更新token的辅助方法"""
        if 'session' in response_data and 'access_token' in response_data['session']:
            self._token = response_data['session']['access_token']
            # logger.trace('Token saved')
        else:
            logger.warning('No access token found in response')
        # logger.trace(f'Response data: {response_data}')

    @to_sync
    async def login_sync(self, email: str, password: str) -> Dict:
        """用户登录（同步版本）"""
        return await self.login(email, password)

    async def get_balance(self) -> Dict:
        """
        获取用户余额（异步版本）

        Returns:
            Dict: 包含用户余额信息的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        try:
            response = await self.client.get("/transactions/get_balance", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f'Get balance failed: {e}')
            if e.response.status_code == 401:
                logger.warning('Authentication failed (401)')
                raise AuthenticationError("Token已过期，需要重新登录")
            raise Exception(f"获取余额失败: {str(e)}")

    @to_sync
    async def get_balance_sync(self) -> Dict:
        """
        获取用户余额（同步版本）
        """
        return await self.get_balance()

    async def reset_password(self, email: str) -> Dict:
        """
        请求重置密码（异步版本）

        Args:
            email: 用户邮箱

        Returns:
            Dict: API响应数据
        """
        try:
            response = await self.client.post("/auth/reset-password", json={"email": email}, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"重置密码请求失败: {str(e)}")

    @to_sync
    async def reset_password_sync(self, email: str) -> Dict:
        """
        请求重置密码（同步版本）
        """
        return await self.reset_password(email)

    async def get_history(self):
        """
        获取交易历史记录（异步版本）

        Returns:
            Dict: 包含交易历史记录的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        try:
            response = await self.client.get("/transactions/history", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPError as e:
            logger.error(f'Get history failed: {e}')

    @to_sync
    async def get_history_sync(self):
        return await self.get_history()

    def get_id(self) -> str:
        """
        获取当前登录用户的ID（纯同步版本）

        Returns:
            str: 用户ID

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
            Exception: 当获取用户ID失败时抛出
        """
        try:
            with httpx.Client(base_url=self.base_url, timeout=15.0) as client:
                # 发送请求
                response = client.get("/users/profile", headers=self.headers)
                response.raise_for_status()
                data = response.json()

                if "data" in data and "user" in data["data"] and "id" in data["data"]["user"]:
                    return data["data"]["user"]["id"]
                else:
                    logger.error(f"User ID not found in response: {data}")
                    raise Exception("无法获取用户ID：响应数据格式不正确")
        except httpx.HTTPStatusError as e:
            logger.error(f"Get user ID failed: {e}")
            if e.response.status_code == 401:
                logger.warning("Authentication failed (401)")
                raise AuthenticationError("Token已过期，需要重新登录")
            raise Exception(f"获取用户ID失败: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_id_sync: {e}")
            raise Exception(f"获取用户ID失败: {str(e)}")


    async def recharge_tokens(self, user_id: str,amount: int) -> Dict:
        """
        充值代币（异步版本）

        Args:
            user_id: 用户ID
            amount: 充值金额

        Returns:
            Dict: 包含充值结果的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        try:
            import time
            from app.models.security import generate_signature


            # 生成时间戳
            timestamp = int(time.time())

            # 生成订单ID
            order_id = f"recharge_{timestamp}_{user_id}"

            # 生成签名
            sign = generate_signature(
                user_id=user_id,
                amount=amount,
                timestamp=timestamp,
                feature_key=f"recharge_1"  # 充值类型为1的特殊feature_key
            )

            # 构建URL参数
            params = {
                "timestamp": timestamp,
                "sign": sign,
                "order_id": order_id,
            }

            # 构建请求体
            json_data = {
                "racharge_type": 1,  # 充值类型，1表示普通充值
                "token_add": amount,  # 充值金额
                "feature_key": "recharge",
                "token_cost": amount,
                "feature_count": 1
            }

            response = await self.client.post(
                "/transactions/recharge",
                params=params,
                json=json_data,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f'Recharge tokens failed: {e}')
            if e.response.status_code == 401:
                logger.warning('Authentication failed (401)')
                raise AuthenticationError("Token已过期，需要重新登录")
            raise Exception(f"充值失败: {str(e)}")
        except Exception as e:
            logger.error(f'Unexpected error in recharge_tokens: {e}')
            raise Exception(f"充值失败: {str(e)}")

    @to_sync
    async def recharge_tokens_sync(self,us_id:str, amount: int) -> Dict:
        """
        充值代币（同步版本）

        Args:
            us_id: 用户id
            amount: 充值金额

        Returns:
            Dict: 包含充值结果的响应数据
        """
        return await self.recharge_tokens(us_id, amount)

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
        self._executor.shutdown(wait=True)

    @to_sync
    async def close_sync(self):
        """关闭HTTP客户端（同步版本）"""
        await self.close()


# 创建全局API客户端实例
api_client = APIClient()
