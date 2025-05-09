import asyncio
import httpx

# 接口地址
PROFILE = "http://127.0.0.1:8000/api/user/profile"
check_endpoint = "http://127.0.0.1:8000/api/client/check-version"

# 请求数据
json_data = {
    "platform": "windows",
    "current_version": "0.2.1"
}

# 认证信息
token = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik0wTUYvMFIwemkzVDBWUUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2VmaHRneWZod2F4cWVxdXVuYmhjLnN1cGFiYXNlLmNvL"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# 异步函数实现
async def ask_version():
    """异步获取版本信息"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            check_endpoint,
            headers=headers,
            json=json_data,
            timeout=10
        )
        result = response.json()
        # print("版本信息获取成功:")
        # print(result)
        return result

async def get_profile():
    """异步获取用户资料"""
    # 模拟这个API需要更长的时间
    await asyncio.sleep(2)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            PROFILE,
            headers=headers,
            timeout=10
        )
        result = response.json()
        print("用户资料获取成功:")
        print(result)
        return result

async def main():
    """并发调用API并立即处理结果"""
    # 创建任务
    tasks = [
        ask_version(),
        get_profile()
    ]
    
    # 使用as_completed依次处理完成的任务
    for completed_task in asyncio.as_completed(tasks):
        await completed_task
        # 结果已经在各自的函数中输出
    
    print("所有API调用已完成")

if __name__ == "__main__":
    print("开始并发调用API...")
    asyncio.run(main())
