#!/usr/bin/env python3
"""
测试 API 接口的脚本
"""

import requests
import json

def test_api():
    """测试 API 接口"""
    base_url = "http://localhost:8012"
    
    # 测试登录
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    print("🔐 测试登录...")
    response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"✅ 登录成功，获得 token: {token[:20]}...")
        
        # 测试流量统计
        print("\n📊 测试流量统计...")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试流量统计 API
        response = requests.get(f"{base_url}/api/v1/traffic", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 流量统计 API 正常")
            print(f"   总发送流量: {data.get('stats', {}).get('totalBytesSent', 0):,} 字节")
            print(f"   总接收流量: {data.get('stats', {}).get('totalBytesRecv', 0):,} 字节")
            print(f"   活跃连接: {data.get('stats', {}).get('activeConnections', 0)}")
            print(f"   在线用户: {data.get('stats', {}).get('onlineUsers', 0)}")
        else:
            print(f"❌ 流量统计 API 失败: {response.status_code}")
            print(f"   响应: {response.text}")
        
        # 测试实时流量 API
        print("\n📈 测试实时流量...")
        response = requests.get(f"{base_url}/api/v1/traffic/realtime", headers=headers)
        if response.status_code == 200:
            data = response.json()
            realtime_data = data.get('realtime_traffic', [])
            print(f"✅ 实时流量 API 正常，数据点: {len(realtime_data)}")
            if realtime_data:
                latest = realtime_data[-1]
                print(f"   最新数据: {latest.get('timestamp')} - 发送: {latest.get('bytes_sent', 0)}, 接收: {latest.get('bytes_recv', 0)}")
        else:
            print(f"❌ 实时流量 API 失败: {response.status_code}")
            print(f"   响应: {response.text}")
        
        # 测试流量日志 API
        print("\n📝 测试流量日志...")
        response = requests.get(f"{base_url}/api/v1/traffic/logs", headers=headers)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            total = data.get('total', 0)
            print(f"✅ 流量日志 API 正常，总记录: {total}, 当前页: {len(logs)}")
            if logs:
                latest = logs[0]
                print(f"   最新日志: {latest.get('timestamp')} - 用户: {latest.get('user', {}).get('username', 'N/A')} - 发送: {latest.get('bytes_sent', 0)}, 接收: {latest.get('bytes_recv', 0)}")
        else:
            print(f"❌ 流量日志 API 失败: {response.status_code}")
            print(f"   响应: {response.text}")
    
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(f"   响应: {response.text}")

if __name__ == '__main__':
    test_api()
