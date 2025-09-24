#!/usr/bin/env python3
"""
测试同步余额获取功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_token_service_import():
    """测试TokenService导入"""
    try:
        from nice_ui.services.service_provider import ServiceProvider
        print("✅ ServiceProvider导入成功")
        
        service_provider = ServiceProvider()
        token_service = service_provider.get_token_service()
        print("✅ TokenService获取成功")
        
        return token_service
    except Exception as e:
        print(f"❌ TokenService导入失败: {e}")
        return None

def test_auth_service_import():
    """测试AuthService导入"""
    try:
        from nice_ui.services.service_provider import ServiceProvider
        service_provider = ServiceProvider()
        auth_service = service_provider.get_auth_service()
        print("✅ AuthService获取成功")
        
        return auth_service
    except Exception as e:
        print(f"❌ AuthService导入失败: {e}")
        return None

def test_balance_sync_method(token_service):
    """测试同步余额获取方法"""
    if not token_service:
        print("❌ TokenService不可用，跳过余额测试")
        return

    try:
        # 测试get_user_balance方法
        if hasattr(token_service, 'get_user_balance'):
            print("✅ get_user_balance方法存在")
        else:
            print("❌ get_user_balance方法不存在")
            return

        print("✅ 余额相关方法检查通过")

    except Exception as e:
        print(f"❌ 余额方法测试失败: {e}")

def test_api_client_sync_method():
    """测试api_client中的同步余额方法"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from api_client import api_client

        # 测试get_balance_sync方法是否存在
        if hasattr(api_client, 'get_balance_sync'):
            print("✅ api_client.get_balance_sync方法存在")
        else:
            print("❌ api_client.get_balance_sync方法不存在")
            return

        print("✅ api_client同步余额方法检查通过")

    except Exception as e:
        print(f"❌ api_client方法测试失败: {e}")

def test_auth_check_login_status(auth_service):
    """测试登录状态检查方法"""
    if not auth_service:
        print("❌ AuthService不可用，跳过登录状态测试")
        return
    
    try:
        # 测试check_login_status方法是否存在
        if hasattr(auth_service, 'check_login_status'):
            print("✅ check_login_status方法存在")
        else:
            print("❌ check_login_status方法不存在")
            return
            
        print("✅ 登录状态检查方法存在")
        
    except Exception as e:
        print(f"❌ 登录状态方法测试失败: {e}")

def main():
    """主测试函数"""
    print("🔧 开始测试同步余额获取功能...")
    print("=" * 50)
    
    # 测试服务导入
    token_service = test_token_service_import()
    auth_service = test_auth_service_import()
    
    print("\n" + "=" * 50)
    
    # 测试方法存在性
    test_balance_sync_method(token_service)
    test_auth_check_login_status(auth_service)
    test_api_client_sync_method()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")

if __name__ == "__main__":
    main()
