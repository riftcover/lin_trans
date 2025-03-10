import httpx
from typing import Optional, Dict

import asyncio
from concurrent.futures import ThreadPoolExecutor

from utils import logger


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
            response = await self.client.post(
                "/auth/login",
                json={"email": email, "password": password},
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            # 从返回的数据中获取access_token并保存
            if 'session' in data and 'access_token' in data['session']:
                self._token = data['session']['access_token']
                logger.trace(f'Token saved')
            else:
                logger.warning('No access token found in response')
            logger.trace(f'Response data: {data}')
            
            # # 登录成功后立即获取余额
            # if self._token:
            #     balance_data = await self.get_balance()
            #     data.update(balance_data)
                
            return data
        except httpx.HTTPError as e:
            logger.error(f'Login failed: {e}')
            raise Exception(f"登录失败: {str(e)}")

    def login_sync(self, email: str, password: str) -> Dict:
        """
        用户登录（同步版本）
        """
        return _run_async(self.login(email, password))

    async def get_balance(self) -> Dict:
        """
        获取用户余额（异步版本）
        
        Returns:
            Dict: 包含用户余额信息的响应数据
        """
        try:
            response = await self.client.get("/transactions/get_balance", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            logger.trace(f'Balance data: {data}')
            return data
        except httpx.HTTPError as e:
            logger.error(f'Get balance failed: {e}')
            raise Exception(f"获取余额失败: {str(e)}")

    def get_balance_sync(self) -> Dict:
        """
        获取用户余额（同步版本）
        """
        return _run_async(self.get_balance())

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

    def reset_password_sync(self, email: str) -> Dict:
        """
        请求重置密码（同步版本）
        """
        return _run_async(self.reset_password(email))

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
        self._executor.shutdown(wait=True)

    def close_sync(self):
        """关闭HTTP客户端（同步版本）"""
        _run_async(self.close())


# 创建全局API客户端实例
api_client = APIClient()
