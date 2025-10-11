#!/usr/bin/env python3
"""
测试会话过期后的401错误和自动跳转功能
"""

import requests
import time
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8012"
API_BASE = f"{BASE_URL}/api/v1"

def test_session_expiry():
    """测试会话过期功能"""
    print("=" * 60)
    print("测试会话过期后的401错误和自动跳转")
    print("=" * 60)
    
    # 1. 首先登录获取token
    print("\n1. 登录获取token...")
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ 登录成功，获取到token: {token[:20]}...")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return
    
    # 2. 使用有效token访问用户列表
    print("\n2. 使用有效token访问用户列表...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        if response.status_code == 200:
            print("✅ 成功访问用户列表")
        else:
            print(f"❌ 访问用户列表失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 3. 创建一个过期的token（修改过期时间）
    print("\n3. 模拟过期token...")
    import jwt
    
    # 解码token获取claims
    try:
        # 注意：这里需要JWT密钥，我们使用配置中的密钥
        jwt_secret = "your-secret-key-change-this-in-production"
        decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        
        # 修改过期时间为过去的时间
        decoded['exp'] = int(time.time()) - 3600  # 1小时前过期
        
        # 重新签名
        expired_token = jwt.encode(decoded, jwt_secret, algorithm="HS256")
        print(f"✅ 创建了过期token: {expired_token[:20]}...")
        
    except Exception as e:
        print(f"❌ 创建过期token失败: {e}")
        return
    
    # 4. 使用过期token访问用户列表
    print("\n4. 使用过期token访问用户列表...")
    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    
    try:
        response = requests.get(f"{API_BASE}/users", headers=expired_headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 401:
            print("✅ 正确返回401错误（会话过期）")
        else:
            print("❌ 应该返回401错误但没有返回")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 5. 测试创建用户接口
    print("\n5. 使用过期token尝试创建用户...")
    create_user_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "testpass123",
        "role": "user",
        "status": "active"
    }
    
    try:
        response = requests.post(f"{API_BASE}/users", 
                               json=create_user_data, 
                               headers=expired_headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 401:
            print("✅ 正确返回401错误（会话过期）")
        else:
            print("❌ 应该返回401错误但没有返回")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_session_expiry()
