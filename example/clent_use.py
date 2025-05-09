import time

import httpx

# PROFILE = "http://127.0.0.1:8000/user/profile"
PROFILE = "http://127.0.0.1:8000/api/client/tt"
check_endpoint = "http://127.0.0.1:8000/api/client/check-version"
json_data = {
    "platform": "windows",
    "current_version": "0.2.1"
}
token = "eyJhbGciOiJIUzI1NiIsImtpZCI6Ik0wTUYvMFIwemkzVDBWUUMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2VmaHRneWZod2F4cWVxdXVuYmhjLnN1cGFiYXNlLmNvL"
headers = {
    "Content-Type": "application/json"
}

def ask_version():
    # 发送POST请求
    response = httpx.post(
        check_endpoint,
        headers=headers,
        json=json_data,
        timeout=10  # 10秒超时
    )
    return response.json()

def get_profile():
    # 发送get请求
    response = httpx.get(
        PROFILE,
        headers=headers,
        timeout=10  # 10秒超时
    )
    return response.json()

if __name__ == '__main__':
    print(get_profile())
    # print(ask_version())