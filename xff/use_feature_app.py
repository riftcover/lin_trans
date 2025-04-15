import httpx
import time
import json
from typing import Dict, Any

from backend.app.core.security import generate_signature


class UseFeatureRequest:
    def __init__(self, feature_key: str, token_cost: int):
        self.feature_key = feature_key
        self.token_cost = token_cost


async def use_feature(request_data: UseFeatureRequest, access_token: str):
    url = "http://localhost:8000/api/transactions/use"

    headers = {
        "Authorization": f"Bearer {access_token}", 
        "Content-Type": "application/json",
    }

    # 获取当前时间戳
    timestamp = int(time.time())

    # 从 JWT token 中解析用户 ID（这里需要实际的用户ID）
    user_id = "99a9e85e-0bbb-4d77-96b8-937e4c5d633c"  # 从 token 中获取或传入

    # 生成签名
    signature = generate_signature(
        user_id=user_id, 
        amount=request_data.token_cost, 
        feature_key=request_data.feature_key, 
        timestamp=timestamp
    )

    # 准备请求参数
    params = {"timestamp": timestamp, "sign": signature}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, 
                params=params, 
                json=request_data.__dict__, 
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            return result
        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_json = e.response.json()
                error_detail = error_json.get('detail', error_text)
                print(f"HTTP错误 {e.response.status_code}: {error_detail}")
            except json.JSONDecodeError:
                print(f"HTTP错误 {e.response.status_code}: {error_text}")
            raise
        except Exception as e:
            print(f"请求错误: {str(e)}")
            raise


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def main():
        # 测试数据
        request_data = UseFeatureRequest(feature_key="xx", token_cost=10)
        access_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik0wTUYvMFIwemkzVDBWUUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2VmaHRneWZod2F4cWVxdXVuYmhjLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5OWE5ZTg1ZS0wYmJiLTRkNzctOTZiOC05MzdlNGM1ZDYzM2MiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQxNDQ2ODMzLCJpYXQiOjE3NDE0NDMyMzMsImVtYWlsIjoidGlhb2Rhbnd1c2hhQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJ0aWFvZGFud3VzaGFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiOTlhOWU4NWUtMGJiYi00ZDc3LTk2YjgtOTM3ZTRjNWQ2MzNjIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NDE0NDMyMzN9XSwic2Vzc2lvbl9pZCI6ImU2NmNhYWM1LThkMWMtNDMzMS1hZmU2LTY0YTkyMzhkZTM5NCIsImlzX2Fub255bW91cyI6ZmFsc2V9.eZ1ZxYak-HC9qDa3rXMcZoViaEWlutgqQ2fBPRaGpJs"

        try:
            result = await use_feature(request_data, access_token)
            print("请求成功:", json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print("错误详情:", str(e))

    asyncio.run(main())