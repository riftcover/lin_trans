import time
from typing import Optional, Dict

import httpx
from app.core.security import generate_signature
from utils import logger


class AuthenticationError(Exception):
    """认证错误，用于处理401错误"""
    pass





class APIClient:
    def __init__(self, base_url: str = None, timeout: float = None):
        # 从配置管理器获取API配置
        from services.config_manager import get_api_base_url, get_api_timeout

        # 如果没有提供基础URL，从配置中获取
        self.base_url = base_url or get_api_base_url()
        # 如果没有提供超时时间，从配置中获取
        timeout_value = timeout or get_api_timeout()

        logger.info(f"Initializing API client with base_url: {self.base_url}, timeout: {timeout_value}")

        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_value)
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[int] = None  # token过期时间戳

    def load_token_from_settings(self, settings) -> bool:
        """
        从配置中加载token和refresh_token

        Args:
            settings: QSettings实例

        Returns:
            bool: 是否成功加载token
        """
        token = settings.value('token')
        refresh_token = settings.value('refresh_token')
        token_expires_at = settings.value('token_expires_at')

        if token:
            self._token = token
            logger.trace('Token loaded from settings')

            if refresh_token:
                self._refresh_token = refresh_token
                logger.trace('Refresh token loaded from settings')

            if token_expires_at:
                try:
                    self._token_expires_at = int(token_expires_at)
                    logger.trace(f'Token expires at: {time.ctime(self._token_expires_at)}')
                except (ValueError, TypeError):
                    logger.warning('Invalid token expiry time in settings')

            return True
        return False

    def clear_token(self):
        """清除token和refresh_token"""
        self._token = None
        self._refresh_token = None
        self._token_expires_at = None
        logger.trace('Token, refresh token and expiry time cleared')

    @property
    def headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _ensure_valid_token(self) -> bool:
        """
        确保token有效，如果即将过期则自动刷新

        Returns:
            bool: token是否有效
        """
        if not self._token:
            return False

        # 检查token是否即将过期（提前5分钟刷新）
        if self.is_token_expiring_soon(300):
            logger.info("Token即将过期，尝试自动刷新")
            success = await self.refresh_session()
            if not success:
                logger.warning("Token自动刷新失败")
                return False
            logger.info("Token自动刷新成功")

        return True

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
        except httpx.HTTPStatusError as e:
            logger.error(f"Login HTTP error: {e.response.status_code}")
            logger.trace(f"Response text: {e.response.text}")
            raise Exception(f"Login failed with status {e.response.status_code}: {e.response.text}")

    def _update_token(self, response_data: Dict) -> None:
        """更新token和refresh_token的辅助方法"""
        if 'session' in response_data:
            if 'access_token' in response_data['session']:
                self._token = response_data['session']['access_token']
                logger.trace('Access token updated')
            else:
                logger.warning('No access token found in response')

            if 'refresh_token' in response_data['session']:
                self._refresh_token = response_data['session']['refresh_token']
                logger.trace('Refresh token updated')
            else:
                logger.warning('No refresh token found in response')

            # 更新过期时间
            if 'expires_at' in response_data['session']:
                self._token_expires_at = response_data['session']['expires_at']
                logger.trace(f'Token expires at: {time.ctime(self._token_expires_at)}')
            else:
                # 如果没有提供过期时间，假设24小时有效期
                self._token_expires_at = int(time.time()) + 24 * 3600
                logger.trace('No expiry time provided, assuming 24 hours validity')
        else:
            logger.warning('No session data found in response')

    async def refresh_session(self) -> bool:
        """
        刷新会话token（异步版本）

        Returns:
            bool: 刷新是否成功
        """
        if not self._refresh_token:
            logger.warning('No refresh token available for session refresh')
            return False

        try:
            # 调用后端的刷新会话接口
            response = await self.client.post(
                "/auth/refresh",
                json={"refresh_token": self._refresh_token},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()

            # 更新token
            self._update_token(data)
            logger.info('Session refreshed successfully')
            return True
        except Exception as e:
            logger.error(f'Failed to refresh session: {e}')
            return False

    def _refresh_session_sync(self) -> bool:
        """
        刷新会话token（同步版本，仅供内部使用）

        Returns:
            bool: 刷新是否成功
        """
        if not self._refresh_token:
            logger.warning('No refresh token available for session refresh')
            return False

        try:
            # 使用同步HTTP客户端调用后端的刷新会话接口
            with httpx.Client(base_url=self.base_url, timeout=15.0) as client:
                response = client.post(
                    "/auth/refresh",
                    json={"refresh_token": self._refresh_token},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()

                # 更新token
                self._update_token(data)
                logger.info('Session refreshed successfully (sync)')
                return True
        except Exception as e:
            logger.error(f'Failed to refresh session (sync): {e}')
            return False



    def is_token_expired(self) -> bool:
        """检查token是否已过期"""
        if not self._token_expires_at:
            return False
        return int(time.time()) >= self._token_expires_at

    def is_token_expiring_soon(self, threshold_seconds: int = 600) -> bool:
        """
        检查token是否即将过期

        Args:
            threshold_seconds: 提前多少秒认为即将过期，默认10分钟

        Returns:
            bool: 是否即将过期
        """
        if not self._token_expires_at:
            return False
        return (self._token_expires_at - int(time.time())) <= threshold_seconds

    def get_token_expiry_time(self) -> Optional[int]:
        """获取token过期时间戳"""
        return self._token_expires_at



    async def get_balance(self) -> Dict:
        """
        获取用户余额（异步版本）

        Returns:
            Dict: 包含用户余额信息的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        # 确保token有效
        if not await self._ensure_valid_token():
            raise AuthenticationError("Token无效或刷新失败，需要重新登录")

        try:
            response = await self.client.get("/transactions/get_balance", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'Get balance failed: {e}')
            if e.response.status_code == 401:
                logger.warning('Authentication failed (401), attempting to refresh token')
                # 尝试刷新token
                if await self.refresh_session():
                    # 刷新成功，重试请求
                    logger.info('Token refreshed, retrying request')
                    try:
                        response = await self.client.get("/transactions/get_balance", headers=self.headers)
                        response.raise_for_status()
                        return response.json()
                    except Exception as retry_error:
                        logger.error(f'Retry after token refresh failed: {retry_error}')
                        raise AuthenticationError("Token刷新后请求仍然失败，需要重新登录") from retry_error
                else:
                    # 刷新失败
                    logger.warning('Token refresh failed')
                    raise AuthenticationError("Token已过期，需要重新登录")
            raise Exception(f"获取余额失败: {str(e)}")

    def get_balance_sync(self) -> Dict:
        """
        同步获取用户余额

        Returns:
            Dict: 包含用户余额信息的响应数据

        Raises:
            AuthenticationError: 当认证失败时抛出
            Exception: 当其他错误发生时抛出
        """
        try:


            # 检查是否有有效token
            if not self._token:
                raise AuthenticationError("No valid token")

            # 使用同步HTTP客户端
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get(
                    "/transactions/get_balance",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            raise Exception("获取余额超时")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Token已过期")
            else:
                raise Exception(f"获取余额HTTP错误: {e}")
        except Exception as e:
            raise Exception(f"同步获取余额失败: {e}")

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
            raise Exception(f"重置密码请求失败: {str(e)}") from e



    async def get_history(self, page: int = 1, page_size: int = 10, transaction_type: Optional[int] = None,
                          start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        获取交易历史记录（异步版本）

        Args:
            page: 页码，默认为1
            page_size: 每页记录数，默认为10
            transaction_type: 交易类型，可选
            start_date: 开始日期，可选
            end_date: 结束日期，可选

        Returns:
            Dict: 包含交易历史记录的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        try:
            # 构建查询参数
            params = {
                "page": page,
                "page_size": page_size
            }

            # 只在参数有值时添加到请求中
            if transaction_type is not None:
                params["transaction_type"] = transaction_type
            if start_date is not None:
                params["start_date"] = start_date
            if end_date is not None:
                params["end_date"] = end_date

            response = await self.client.get("/transactions/history", params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'Get history failed: {e}')
            if e.response.status_code == 401:
                logger.warning('Authentication failed (401), attempting to refresh token')
                # 尝试刷新token
                if await self.refresh_session():
                    # 刷新成功，重试请求
                    logger.info('Token refreshed, retrying request')
                    try:
                        response = await self.client.get("/transactions/history", params=params, headers=self.headers)
                        response.raise_for_status()
                        return response.json()
                    except Exception as retry_error:
                        logger.error(f'Retry after token refresh failed: {retry_error}')
                        raise AuthenticationError("Token刷新后请求仍然失败，需要重新登录")
                else:
                    # 刷新失败
                    logger.warning('Token refresh failed')
                    raise AuthenticationError("Token已过期，需要重新登录")
            raise ValueError(f"获取交易历史失败: {str(e)}")
        except Exception as e:
            logger.error(f'Unexpected error in get_history: {e}')
            raise ValueError(f"获取交易历史失败: {str(e)}")



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
                logger.error(f"User ID not found in response: {data}")
                raise ValueError("无法获取用户ID：响应数据格式不正确")
        except httpx.HTTPStatusError as e:
            logger.error(f"Get user ID failed: {e}")
            if e.response.status_code == 401:
                logger.warning("Authentication failed (401), attempting to refresh token")
                # 尝试刷新token（同步方式）
                if self._refresh_session_sync():
                    # 刷新成功，重试请求
                    logger.info('Token refreshed, retrying request')
                    try:
                        with httpx.Client(base_url=self.base_url, timeout=15.0) as retry_client:
                            response = retry_client.get("/users/profile", headers=self.headers)
                            response.raise_for_status()
                            data = response.json()

                            if "data" in data and "user" in data["data"] and "id" in data["data"]["user"]:
                                return data["data"]["user"]["id"]
                            logger.error(f"User ID not found in response: {data}")
                            raise ValueError("\u65e0\u6cd5\u83b7\u53d6\u7528\u6237ID\uff1a\u54cd\u5e94\u6570\u636e\u683c\u5f0f\u4e0d\u6b63\u786e")
                    except Exception as retry_error:
                        logger.error(f'Retry after token refresh failed: {retry_error}')
                        raise AuthenticationError("Token刷新后请求仍然失败，需要重新登录")
                else:
                    # 刷新失败
                    logger.warning('Token refresh failed')
                    raise AuthenticationError("Token已过期，需要重新登录")
            raise ValueError(f"获取用户ID失败: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_id_sync: {e}")
            raise ValueError(f"获取用户ID失败: {str(e)}")

    async def recharge_tokens(self, user_id: str, amount: int) -> Dict:
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
            from app.core.security import generate_signature

            # 生成时间戳
            timestamp = int(time.time())

            # 生成订单ID
            order_id = f"recharge_{timestamp}_{user_id}"

            # 生成签名
            sign = generate_signature(
                user_id=user_id,
                amount=amount,
                timestamp=timestamp,
                feature_key="recharge_1"  # 充值类型为1的特殊feature_key
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
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'Recharge tokens failed: {e}')
            if e.response.status_code == 401:
                logger.warning('Authentication failed (401), attempting to refresh token')
                # 尝试刷新token
                if await self.refresh_session():
                    # 刷新成功，重试请求
                    logger.info('Token refreshed, retrying request')
                    try:
                        response = await self.client.post(
                            "/transactions/recharge",
                            params=params,
                            json=json_data,
                            headers=self.headers
                        )
                        response.raise_for_status()
                        return response.json()
                    except Exception as retry_error:
                        logger.error(f'Retry after token refresh failed: {retry_error}')
                        raise AuthenticationError("Token刷新后请求仍然失败，需要重新登录")
                else:
                    # 刷新失败
                    logger.warning('Token refresh failed')
                    raise AuthenticationError("Token已过期，需要重新登录")
            raise ValueError(f"充值失败: {str(e)}")
        except Exception as e:
            logger.error(f'Unexpected error in recharge_tokens: {e}')
            raise ValueError(f"充值失败: {str(e)}") from e



    async def create_recharge_order(self, user_id: str, amount_in_yuan: float, token_amount: int) -> Dict:
        """
        创建充值订单（异步版本）

        Args:
            user_id: 用户ID
            amount_in_yuan: 充值金额，单位为元
            token_amount: 充值代币数量

        Returns:
            Dict: 包含订单信息的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        try:
            timestamp = int(time.time())
            # 签名金额应为整数
            amount_for_signing = int(amount_in_yuan)
            feature_key = "recharge"

            sign = generate_signature(
                user_id=user_id,
                amount=amount_for_signing,
                feature_key=feature_key,
                timestamp=timestamp
            )

            payload = {
                "amount": amount_in_yuan,
                "balance": token_amount,
                "timestamp": timestamp,
                "sign": sign
            }

            response = await self.client.post("/transactions/recharge/create-order", json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'Create recharge order failed: {e}')
            if e.response.status_code == 401:
                logger.warning('Authentication failed (401), attempting to refresh token')
                if await self.refresh_session():
                    logger.info('Token refreshed, retrying request')
                    try:
                        response = await self.client.post("/transactions/recharge/create-order", json=payload, headers=self.headers)
                        response.raise_for_status()
                        return response.json()
                    except Exception as retry_error:
                        logger.error(f'Retry after token refresh failed: {retry_error}')
                        raise AuthenticationError("Token刷新后请求仍然失败，需要重新登录") from retry_error
                else:
                    logger.warning('Token refresh failed')
                    raise AuthenticationError("Token已过期，需要重新登录")
            raise ValueError(f"创建充值订单失败: {str(e)}") from e
        except Exception as e:
            logger.error(f'Unexpected error in create_recharge_order: {e}')
            raise ValueError(f"创建充值订单失败: {str(e)}") from e



    async def get_order_status(self, order_id: str) -> Dict:
        """
        查询充值订单状态（异步版本）

        Args:
            order_id: 订单ID

        Returns:
            Dict: 包含订单状态的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        try:
            response = await self.client.get(f"/transactions/recharge/order-status/{order_id}", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'Get order status for {order_id} failed: {e}')
            if e.response.status_code == 401:
                logger.warning('Authentication failed (401), attempting to refresh token')
                if await self.refresh_session():
                    logger.info('Token refreshed, retrying request')
                    try:
                        response = await self.client.get(f"/transactions/recharge/order-status/{order_id}", headers=self.headers)
                        response.raise_for_status()
                        return response.json()
                    except Exception as retry_error:
                        logger.error(f'Retry after token refresh failed: {retry_error}')
                        raise AuthenticationError("Token刷新后请求仍然失败，需要重新登录") from retry_error
                else:
                    logger.warning('Token refresh failed')
                    raise AuthenticationError("Token已过期，需要重新登录")
            # 假设404表示订单未找到或尚未处理，这不应被视为致命错误
            if e.response.status_code == 404:
                return {"data": {"status": "pending"}}
            raise ValueError(f"查询订单状态失败: {str(e)}") from e
        except Exception as e:
            logger.error(f'Unexpected error in get_order_status: {e}')
            raise ValueError(f"查询订单状态失败: {str(e)}") from e



    async def recharge_packages(self) -> Dict:
        """
        充值套餐（异步版本）
        Returns:

        """
        try:
            with httpx.Client(base_url=self.base_url, timeout=15.0) as client:
                # 发送请求
                response = client.get("/features/recharge-packages", headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'Recharge packages failed: {e}')
            raise ValueError(f"充值套餐失败: {str(e)}") from e
        except Exception as e:
            logger.error(f'Unexpected error in recharge_packages: {e}')
            raise ValueError(f"充值套餐失败: {str(e)}") from e



    async def consume_tokens(self, token_amount: int,file_name:str, feature_key: str = "asr", user_id: Optional[str] = None) -> Dict:
        """
        消费代币

        Args:
            token_amount: 消费的代币数量
            feature_key: 功能标识符，默认为"asr"
            user_id: 用户ID，如果为None，则使用当前登录用户

        Returns:
            Dict: API响应结果
        """
        try:
            # 生成时间戳
            timestamp = int(time.time())

            # 生成签名
            sign = generate_signature(
                user_id=user_id,
                amount=token_amount,
                timestamp=timestamp,
                feature_key=feature_key
            )

            # 构建URL参数
            params = {
                "timestamp": timestamp,
                "sign": sign
            }

            # 构建请求体
            json_data = {
                "feature_key": feature_key,
                "token_cost": token_amount,
                "file_name":file_name
            }

            # 发送请求
            response = await self.client.post(
                "/transactions/use",
                params=params,
                json=json_data,
                headers=self.headers
            )
            response.raise_for_status()

            # 解析响应
            result = response.json()
            logger.info(f"消费代币成功: {result}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f'消费代币失败: {e}')
            raise ValueError(f"消费代币失败: HTTP {e.response.status_code} - {str(e)}") from e
        except Exception as e:
            logger.error(f'消费代币时发生错误: {e}')
            raise ValueError(f"消费代币失败: {str(e)}") from e



    async def get_token_coefficients(self) -> Dict:
        """
        获取代币消耗系数（异步版本）

        Returns:
            Dict: 包含代币消耗系数的响应数据

        Raises:
            AuthenticationError: 当认证失败（401错误）时抛出
        """
        try:
            response = await self.client.get("/features/coefficients", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f'Get token coefficients failed: {e}')
            raise Exception(f"获取代币消耗系数失败: {str(e)}")



    async def check_version(self, platform: str, current_version: str):
        """
        检查客户端版本是否需要更新

        Args:
            platform: 客户端平台
            current_version: 当前版本

        Returns:
            Dict: 包含版本检查结果的响应数据
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/client/check-version",
                    json={"platform": platform, "current_version": current_version},
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f'Check version failed: {e}')
                raise Exception(f"检查版本失败: {str(e)}") from e



    async def get_profile(self):
        """异步获取用户资料"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "/client/tt",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 创建全局API客户端实例
# 使用配置管理器中的设置创建API客户端
api_client = APIClient()

if __name__ == '__main__':
    # 测试代码已移除，请使用异步版本的API方法
    pass