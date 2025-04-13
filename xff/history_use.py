import httpx
import json

access_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik0wTUYvMFIwemkzVDBWUUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2VmaHRneWZod2F4cWVxdXVuYmhjLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI5OWE5ZTg1ZS0wYmJiLTRkNzctOTZiOC05MzdlNGM1ZDYzM2MiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQwMjQzMzM0LCJpYXQiOjE3NDAyMzk3MzQsImVtYWlsIjoidGlhb2Rhbnd1c2hhQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWwiOiJ0aWFvZGFud3VzaGFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwic3ViIjoiOTlhOWU4NWUtMGJiYi00ZDc3LTk2YjgtOTM3ZTRjNWQ2MzNjIn0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NDAyMzk3MzR9XSwic2Vzc2lvbl9pZCI6IjRiMjY4NGE0LTUxZTEtNDFjZS1hOTNhLWFlZGI4ODU2MzMzMiIsImlzX2Fub255bW91cyI6ZmFsc2V9.1YOyXDh6U3P-VbcYFjNw_MiY1r4fnBwXSnsjKz6I_3w"


async def fetch_transaction_history(user_id, page=1, page_size=10, transaction_type=None, start_date=None, end_date=None):
    url = "http://localhost:8000/api/transactions/history"
    
    # 创建基础参数字典
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

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"请求失败: {response.status_code} - {response.text}")


# 示例调用
# 你可以在异步环境中调用这个函数，例如在一个异步的主函数中

if __name__ == "__main__":
    import asyncio

    user_id = "99a9e85e-0bbb-4d77-96b8-937e4c5d633c"  # 从 token 中获取或传入


    async def main():
        # 测试数据

        try:
            result = await fetch_transaction_history(user_id)
            print("请求成功:", json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print("错误详情:", str(e))


    asyncio.run(main())
