#!/usr/bin/env python3
"""
测试历史流量查询 API
"""

import requests
import json

def test_historical_traffic():
    """测试历史流量查询"""
    base_url = "http://localhost:8012"
    
    # 测试登录
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    print("🔐 登录...")
    response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ 登录成功")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试历史流量查询 API
        print("\n📈 测试历史流量查询...")
        
        # 测试基本查询
        response = requests.get(f"{base_url}/api/v1/traffic/historical", headers=headers)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            stats = data.get('stats', {})
            total = data.get('total', 0)
            
            print(f"   总记录数: {total}")
            print(f"   当前页记录数: {len(logs)}")
            print(f"   统计信息: 总发送 {stats.get('total_sent', 0):,} 字节, 总接收 {stats.get('total_recv', 0):,} 字节")
            
            if logs:
                print(f"   最新记录: {logs[0].get('timestamp')} - 用户: {logs[0].get('user', {}).get('username', 'N/A')} - 发送: {logs[0].get('bytes_sent', 0)} 字节")
        else:
            print(f"   ❌ API 调用失败: {response.status_code}")
            print(f"   响应: {response.text}")
        
        # 测试按用户查询
        print("\n📈 测试按用户查询...")
        response = requests.get(f"{base_url}/api/v1/traffic/historical?username=fwy&pageSize=5", headers=headers)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            total = data.get('total', 0)
            
            print(f"   fwy 用户记录数: {total}")
            print(f"   当前页记录数: {len(logs)}")
            
            if logs:
                print(f"   最新记录: {logs[0].get('timestamp')} - 发送: {logs[0].get('bytes_sent', 0)} 字节")
        else:
            print(f"   ❌ API 调用失败: {response.status_code}")
    
    else:
        print(f"❌ 登录失败: {response.status_code}")

if __name__ == '__main__':
    test_historical_traffic()
