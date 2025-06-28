import requests
import json
import time
import hmac
import hashlib

from app.core.security import generate_signature

# --- 1. 配置 (请根据你的实际情况修改) ---
BASE_URL = "http://127.0.0.1:8000"
API_ENDPOINT = "/api/transactions/recharge/create-order"

# --- 2. 用户认证信息 (需要手动填写) ---
# 重要: 你需要先通过登录接口获取一个有效的JWT Access Token
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik0wTUYvMFIwemkzVDBWUUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2VmaHRneWZod2F4cWVxdXVuYmhjLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5OWE5ZTg1ZS0wYmJiLTRkNzctOTZiOC05MzdlNGM1ZDYzM2MiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUwOTQ3MTczLCJpYXQiOjE3NTA5NDM1NzMsImVtYWlsIjoidGlhb2Rhbnd1c2hhQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJ0aWFvZGFud3VzaGFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiOTlhOWU4NWUtMGJiYi00ZDc3LTk2YjgtOTM3ZTRjNWQ2MzNjIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTA5NDM1NzN9XSwic2Vzc2lvbl9pZCI6IjMzNzlmNGRlLTNkNDQtNGI0Zi1iNmE4LTViMjFiZjYwZTQwZCIsImlzX2Fub255bW91cyI6ZmFsc2V9.xMBfG04IyQATgPDsK51ZsqUHht6s26Yyg6N3P-77MRQ"
# 重要: 这是你登录用户的UUID (或ID)，需要与Token对应
USER_ID = "99a9e85e-0bbb-4d77-96b8-937e4c5d633c"


def call_create_recharge_order_api():
    """
    调用创建充值订单的API。
    """


    # --- 3. 准备请求数据 ---
    # 充值金额，单位为元
    amount_in_yuan = 0.1
    bc =200
    # 签名时使用的金额，根据后端逻辑，你之前改为了整数，这里假设是直接取整
    amount_for_signing = int(amount_in_yuan)

    # 获取当前时间戳 (秒)
    current_timestamp = int(time.time())

    # 固定的feature_key
    feature_key = "recharge"

    # 生成签名
    sign = generate_signature(
        user_id=USER_ID,
        amount=amount_for_signing,
        feature_key=feature_key,
        timestamp=current_timestamp
    )

    # 构造请求体
    payload = {
        "amount": amount_in_yuan,
        "balance":bc,
        "timestamp": current_timestamp,
        "sign": sign
    }

    # --- 4. 发起API调用 ---
    url = f"{BASE_URL}{API_ENDPOINT}"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    print("\n--- 准备发起API请求 ---")
    print(f"URL: {url}")
    print(f"请求头: {headers}")
    print(f"请求体: {json.dumps(payload)}")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        response_data = response.json()
        print("\n--- 请求成功 ---")
        print(json.dumps(response_data, indent=4, ensure_ascii=False))

        if response_data.get("data"):
            order_data = response_data["data"]
            print("\n--------------------------------------------------")
            print(f"✅ 成功创建充值订单！")
            print(f"   订单号: {order_data.get('order_id')}")
            print(f"   请将以下链接复制到浏览器中打开以完成支付:")
            print(f"   {order_data.get('payment_url')}")
            print("--------------------------------------------------")

    except requests.exceptions.HTTPError as e:
        print("\n--- 请求失败 ---")
        print("HTTP错误:", e)
        print("响应状态码:", e.response.status_code)
        try:
            print("错误详情:", json.dumps(e.response.json(), indent=4, ensure_ascii=False))
        except json.JSONDecodeError:
            print("错误内容:", e.response.text)
    except Exception as e:
        print(f"\n发生未知错误: {e}")


if __name__ == "__main__":
    call_create_recharge_order_api()

