#!/usr/bin/env python3
"""
测试流量统计显示
"""

import requests
import json

def test_traffic_stats():
    """测试流量统计"""
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
        
        # 测试流量统计 API
        print("\n📊 测试流量统计...")
        response = requests.get(f"{base_url}/api/v1/traffic", headers=headers)
        if response.status_code == 200:
            data = response.json()
            stats = data.get('stats', {})
            
            print(f"   总发送流量: {stats.get('total_bytes_sent', 0):,} 字节")
            print(f"   总接收流量: {stats.get('total_bytes_recv', 0):,} 字节")
            print(f"   活跃连接: {stats.get('active_connections', 0)}")
            print(f"   在线用户: {stats.get('online_users', 0)}")
            print(f"   总用户数: {stats.get('total_users', 0)}")
            
            # 检查数据是否不为0
            if stats.get('total_bytes_sent', 0) > 0:
                print("   ✅ 总发送流量数据正常")
            else:
                print("   ❌ 总发送流量为0")
                
            if stats.get('total_bytes_recv', 0) > 0:
                print("   ✅ 总接收流量数据正常")
            else:
                print("   ❌ 总接收流量为0")
        else:
            print(f"   ❌ API 调用失败: {response.status_code}")
            print(f"   响应: {response.text}")
    
    else:
        print(f"❌ 登录失败: {response.status_code}")

if __name__ == '__main__':
    test_traffic_stats()
