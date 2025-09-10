import asyncio
import httpx
from typing import Dict, Any, Callable

# 接口地址
PROFILE = "http://127.0.0.1:8000/api/client/tt"
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

class ApiClient:
    """API客户端类，用于并发调用多个API"""

    def __init__(self):
        """初始化API客户端"""
        self.tasks = []
        self.results = {}
        self.client = None

    async def initialize(self):
        """初始化HTTP客户端"""
        self.client = httpx.AsyncClient()

    async def cleanup(self):
        """清理HTTP客户端"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def ask_version(self) -> Dict[str, Any]:
        """异步获取版本信息"""
        if not self.client:
            await self.initialize()
            
        response = await self.client.post(
            check_endpoint,
            headers=headers,
            json=json_data,
            timeout=10
        )
        result = response.json()
        # print("版本信息获取成功:")
        # print(result)
        # 如果有回调函数，在这里调用
        return result

    async def get_profile(self) -> Dict[str, Any]:
        """异步获取用户资料"""
        # 模拟这个API需要更长的时间
        await asyncio.sleep(2)

        if not self.client:
            await self.initialize()
            
        response = await self.client.get(
            PROFILE,
            headers=headers,
            timeout=10
        )
        result = response.json()
        # print("用户资料获取成功")
        # print(result)
        # 如果有回调函数，在这里调用
        return result

    def add_task(self, api_func: Callable, api_name: str, callback: Callable = None):
        """
        添加API任务

        Args:
            api_func: API异步函数
            api_name: API名称，用于标识结果
            callback: 可选的回调函数，接收API结果作为参数
        """
        # 直接添加任务到任务列表
        self.tasks.append(api_func())

    async def run_all(self):
        """
        并发运行所有API任务，立即处理每个完成的任务
        """
        if not self.tasks:
            print("没有添加任何API任务")
            return

        # 使用as_completed依次处理完成的任务
        for completed_task in asyncio.as_completed(self.tasks):
            result = await completed_task
            print(result)
            # 处理结果
            if isinstance(result, dict):
                # 这里可以根据结果内容判断是哪个API的结果
                # 并调用相应的回调函数
                pass

        print("所有API调用已完成")
        return self.results

# 示例用法
async def main():
    # 创建API客户端
    client = ApiClient()

    # 添加API任务
    client.add_task(
        client.ask_version,
        "版本检查",
        lambda result: print(f"版本信息: {result}")
    )

    client.add_task(
        client.get_profile,
        "用户资料",
        lambda result: print(f"用户资料: {result}")
    )

    # 运行所有任务
    await client.run_all()

if __name__ == "__main__":
    print("开始并发调用API...")
    asyncio.run(main())
