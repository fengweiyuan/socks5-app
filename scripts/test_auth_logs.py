#!/usr/bin/env python3
"""
测试登录和退出操作的日志审计功能
"""

import requests
import json
import time
from datetime import datetime

# 配置
API_BASE = "http://localhost:8012/api/v1"

def test_login_logout_logs():
    """测试登录和退出日志"""
    print("=" * 80)
    print("🔐 登录和退出操作日志审计测试")
    print("=" * 80)
    
    # 1. 测试登录
    print("\n1️⃣ 测试登录操作...")
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print("✅ 登录成功")
            print(f"用户: {data.get('user', {}).get('username')}")
            print(f"角色: {data.get('user', {}).get('role')}")
        else:
            print(f"❌ 登录失败: {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return
    
    # 等待1秒确保日志记录
    time.sleep(1)
    
    # 2. 测试退出
    print("\n2️⃣ 测试退出操作...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{API_BASE}/auth/logout", headers=headers)
        print(f"退出状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 退出成功")
        else:
            print(f"❌ 退出失败: {response.text}")
    except Exception as e:
        print(f"❌ 退出请求失败: {e}")
    
    # 等待1秒确保日志记录
    time.sleep(1)
    
    # 3. 检查日志
    print("\n3️⃣ 检查认证操作日志...")
    try:
        response = requests.get(f"{API_BASE}/logs?pageSize=10", headers=headers)
        print(f"日志查询状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            
            print(f"✅ 获取到 {len(logs)} 条日志记录")
            
            # 查找认证相关的日志
            auth_logs = []
            for log in logs:
                url = log.get('target_url', '')
                if '/auth/login' in url or '/auth/logout' in url:
                    auth_logs.append(log)
            
            if auth_logs:
                print(f"\n🔍 找到 {len(auth_logs)} 条认证操作日志:")
                for i, log in enumerate(auth_logs, 1):
                    url = log.get('target_url', '')
                    operation = "登录" if '/login' in url else "退出"
                    
                    print(f"\n{i}. {operation}操作")
                    print(f"   操作用户: {log.get('user', {}).get('username', 'N/A')}")
                    print(f"   目标URL: {log.get('target_url', 'N/A')}")
                    print(f"   方法: {log.get('method', 'N/A')}")
                    print(f"   状态: {log.get('status', 'N/A')}")
                    print(f"   客户端IP: {log.get('client_ip', 'N/A')}")
                    print(f"   用户代理: {log.get('user_agent', 'N/A')}")
                    print(f"   时间: {log.get('timestamp', 'N/A')}")
            else:
                print("❌ 没有找到认证操作日志")
        else:
            print(f"❌ 获取日志失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查日志请求失败: {e}")

def test_multiple_login_logout():
    """测试多次登录退出操作"""
    print("\n" + "=" * 80)
    print("🔄 多次登录退出操作测试")
    print("=" * 80)
    
    for i in range(3):
        print(f"\n--- 第 {i+1} 次操作 ---")
        
        # 登录
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }
        
        try:
            response = requests.post(f"{API_BASE}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                print(f"✅ 第{i+1}次登录成功")
                
                # 退出
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.post(f"{API_BASE}/auth/logout", headers=headers)
                if response.status_code == 200:
                    print(f"✅ 第{i+1}次退出成功")
                else:
                    print(f"❌ 第{i+1}次退出失败")
            else:
                print(f"❌ 第{i+1}次登录失败")
        except Exception as e:
            print(f"❌ 第{i+1}次操作失败: {e}")
        
        time.sleep(0.5)  # 短暂等待
    
    # 检查所有认证日志
    print("\n📋 检查所有认证操作日志...")
    try:
        # 使用一个有效的token来查询日志
        login_data = {"username": "testuser", "password": "testpass"}
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get('token')
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(f"{API_BASE}/logs?pageSize=20", headers=headers)
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                
                # 查找认证相关的日志
                auth_logs = []
                for log in logs:
                    url = log.get('target_url', '')
                    if '/auth/login' in url or '/auth/logout' in url:
                        auth_logs.append(log)
                
                print(f"✅ 总共找到 {len(auth_logs)} 条认证操作日志")
                
                # 按时间排序显示
                auth_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                for i, log in enumerate(auth_logs[:10], 1):  # 显示最近10条
                    url = log.get('target_url', '')
                    operation = "登录" if '/login' in url else "退出"
                    timestamp = log.get('timestamp', '')
                    username = log.get('user', {}).get('username', 'N/A')
                    
                    print(f"{i:2d}. {operation} - {username} - {timestamp}")
                    
    except Exception as e:
        print(f"❌ 检查日志失败: {e}")

def main():
    # 基础测试
    test_login_logout_logs()
    
    # 多次操作测试
    test_multiple_login_logout()
    
    print("\n" + "=" * 80)
    print("✅ 登录退出日志审计测试完成")
    print("💡 请登录Web界面查看日志审计页面确认日志记录")
    print("=" * 80)

if __name__ == "__main__":
    main()
