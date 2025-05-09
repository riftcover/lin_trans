import httpx
import json
import time
import hmac
import hashlib
from backend.app.core.security import generate_signature
from backend.app.models.schemas import RechargeRequest

access_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik0wTUYvMFIwemkzVDBWUUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2VmaHRneWZod2F4cWVxdXVuYmhjLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5OWE5ZTg1ZS0wYmJiLTRkNzctOTZiOC05MzdlNGM1ZDYzM2MiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQxNDQ2ODMzLCJpYXQiOjE3NDE0NDMyMzMsImVtYWlsIjoidGlhb2Rhbnd1c2hhQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJ0aWFvZGFud3VzaGFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiOTlhOWU4NWUtMGJiYi00ZDc3LTk2YjgtOTM3ZTRjNWQ2MzNjIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NDE0NDMyMzN9XSwic2Vzc2lvbl9pZCI6ImU2NmNhYWM1LThkMWMtNDMzMS1hZmU2LTY0YTkyMzhkZTM5NCIsImlzX2Fub255bW91cyI6ZmFsc2V9.eZ1ZxYak-HC9qDa3rXMcZoViaEWlutgqQ2fBPRaGpJs"


class RechargeRequestClass:
    def __init__(self, racharge_type: int, token_add: int):
        self.racharge_type = racharge_type
        self.token_add = token_add


async def recharge_tokens(user_id: str, request: RechargeRequest):
    """充值代币"""
    url = "http://localhost:8000/api/transactions/recharge"
    
    # 生成当前时间戳
    timestamp = int(time.time())
    
    # 生成订单ID
    order_id = f"recharge_{timestamp}_{user_id}"
    
    # 生成签名
    sign = generate_signature(
        user_id=user_id,
        amount=request.token_add,
        timestamp=timestamp,
        feature_key=f"recharge_{request.racharge_type}"
    )
    
    # 构建请求参数
    params = {
        "timestamp": timestamp,
        "sign": sign,
        "order_id": order_id,
    }
    
    # 修改请求体结构以匹配API期望
    json_data = {
        "feature_key": "recharge",
        "token_cost": request.token_add,  # 使用token_add作为充值金额
        "feature_count": 1,
        "racharge_type": request.racharge_type,
        "token_add": request.token_add
    }

    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("充值成功:", json.dumps(result, indent=2, ensure_ascii=False))
                return result
            elif response.status_code == 401:
                print("认证失败: token可能已过期")
                return None
            else:
                try:
                    error_detail = response.json().get('detail', str(response.status_code))
                except:
                    error_detail = str(response.status_code)
                print(f"充值失败: {response.status_code} - {error_detail}")
                return None
                
        except httpx.HTTPStatusError as e:
            print(f"HTTP错误: {e.response.status_code} - {str(e)}")
            return None
            
        except httpx.RequestError as e:
            print(f"请求错误: {str(e)}")
            return None
            
        except Exception as e:
            print(f"未知错误: {str(e)}")
            return None


if __name__ == "__main__":
    import asyncio
    
    # 测试参数
    user_id = "99a9e85e-0bbb-4d77-96b8-937e4c5d633c"
    # 创建RechargeRequest实例
    recharge_request = RechargeRequest(
        racharge_type=1,
        token_add=20
    )
    
    async def main():
        result = await recharge_tokens(user_id, recharge_request)
        if result:
            print("充值处理完成")
    
    asyncio.run(main())
