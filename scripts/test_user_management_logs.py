#!/usr/bin/env python3
"""
测试用户管理操作的日志审计功能
"""

import requests
import json
import time
from datetime import datetime

# 配置
API_BASE = "http://localhost:8012/api/v1"

def login_and_get_token():
    """登录并获取token"""
    print("🔐 登录获取token...")
    login_data = {
        "username": "testuser2",  # 使用管理员用户
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ 登录成功，获取到token")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

# 全局变量存储测试用户名
test_username = ""

def create_user(token):
    """创建用户"""
    global test_username
    print("\n👤 测试创建用户...")
    test_username = "log_test_user_" + str(int(time.time()))
    user_data = {
        "username": test_username,
        "email": "logtest@example.com",
        "password": "testpass123",
        "role": "user",
        "bandwidth_limit": 1024
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{API_BASE}/users", json=user_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 201:
            print("✅ 用户创建成功")
            return True
        else:
            print("❌ 用户创建失败")
            return False
    except Exception as e:
        print(f"❌ 创建用户请求失败: {e}")
        return False

def update_user(token):
    """更新用户"""
    global test_username
    print("\n✏️ 测试更新用户...")
    
    # 先获取用户ID
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            target_user = None
            for user in users:
                if user.get('username') == test_username:
                    target_user = user
                    break
            
            if not target_user:
                print("❌ 找不到测试用户")
                return False
            
            user_id = target_user['id']
            print(f"找到测试用户，ID: {user_id}")
            
            # 更新用户信息
            update_data = {
                "email": "updated@example.com",
                "role": "user",  # 保持用户角色，避免删除时出现问题
                "status": "active",
                "bandwidth_limit": 2048
            }
            
            response = requests.put(f"{API_BASE}/users/{user_id}", 
                                 json=update_data, headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
            if response.status_code == 200:
                print("✅ 用户更新成功")
                return True
            else:
                print("❌ 用户更新失败")
                return False
                
        else:
            print(f"❌ 获取用户列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 更新用户请求失败: {e}")
        return False

def delete_user(token):
    """删除用户"""
    global test_username
    print("\n🗑️ 测试删除用户...")
    
    # 先获取用户ID
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            target_user = None
            for user in users:
                if user.get('username') == test_username:
                    target_user = user
                    break
            
            if not target_user:
                print("❌ 找不到测试用户")
                return False
            
            user_id = target_user['id']
            print(f"找到测试用户，ID: {user_id}")
            
            # 删除用户
            response = requests.delete(f"{API_BASE}/users/{user_id}", headers=headers)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
            if response.status_code == 200:
                print("✅ 用户删除成功")
                return True
            else:
                print("❌ 用户删除失败")
                return False
                
        else:
            print(f"❌ 获取用户列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 删除用户请求失败: {e}")
        return False

def check_logs(token):
    """检查日志"""
    print("\n📋 检查操作日志...")
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_BASE}/logs?pageSize=10", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            
            print(f"✅ 获取到 {len(logs)} 条日志记录")
            
            # 显示最近的用户操作日志
            user_operation_logs = []
            for log in logs:
                user_agent = log.get('user_agent', '')
                # 检查用户管理相关的操作
                if (any(op in user_agent for op in ['CREATE_USER', 'UPDATE_USER', 'DELETE_USER']) or 
                    log.get('target_url', '').endswith('/users')):
                    user_operation_logs.append(log)
            
            if user_operation_logs:
                print(f"\n🔍 找到 {len(user_operation_logs)} 条用户操作日志:")
                for i, log in enumerate(user_operation_logs, 1):
                    user_agent = log.get('user_agent', '')
                    operation = ""
                    if 'CREATE_USER' in user_agent:
                        operation = "创建用户"
                    elif 'UPDATE_USER' in user_agent:
                        operation = "更新用户"
                    elif 'DELETE_USER' in user_agent:
                        operation = "删除用户"
                    
                    print(f"\n{i}. {operation}")
                    print(f"   操作用户: {log.get('user', {}).get('username', 'N/A')}")
                    print(f"   目标URL: {log.get('target_url', 'N/A')}")
                    print(f"   方法: {log.get('method', 'N/A')}")
                    print(f"   状态: {log.get('status', 'N/A')}")
                    print(f"   时间: {log.get('timestamp', 'N/A')}")
                    print(f"   详情: {user_agent}")
            else:
                print("❌ 没有找到用户操作日志")
                
        else:
            print(f"❌ 获取日志失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查日志请求失败: {e}")

def main():
    print("=" * 80)
    print("🧪 用户管理操作日志审计测试")
    print("=" * 80)
    
    # 登录获取token
    token = login_and_get_token()
    if not token:
        return
    
    # 执行用户管理操作
    operations_success = []
    
    # 1. 创建用户
    operations_success.append(create_user(token))
    time.sleep(1)  # 等待1秒确保日志记录
    
    # 2. 更新用户
    operations_success.append(update_user(token))
    time.sleep(1)
    
    # 3. 删除用户
    operations_success.append(delete_user(token))
    time.sleep(1)
    
    # 检查日志
    check_logs(token)
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结:")
    print(f"- 创建用户: {'✅ 成功' if operations_success[0] else '❌ 失败'}")
    print(f"- 更新用户: {'✅ 成功' if operations_success[1] else '❌ 失败'}")
    print(f"- 删除用户: {'✅ 成功' if operations_success[2] else '❌ 失败'}")
    
    success_count = sum(operations_success)
    print(f"\n总操作成功: {success_count}/3")
    
    if success_count == 3:
        print("🎉 所有用户管理操作测试通过！")
        print("💡 请登录Web界面查看日志审计页面确认日志记录")
    else:
        print("⚠️ 部分操作失败，请检查日志")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
