#!/usr/bin/env python3
"""
测试用户流量聚合的脚本
"""

import requests
import json

def test_user_traffic():
    """测试用户流量聚合"""
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
        
        # 测试实时流量 API
        print("\n📈 测试用户流量聚合...")
        response = requests.get(f"{base_url}/api/v1/traffic/realtime", headers=headers)
        if response.status_code == 200:
            data = response.json()
            realtime_data = data.get('realtime_traffic', [])
            user_data = data.get('user_traffic', [])
            
            print(f"   总体数据点数量: {len(realtime_data)}")
            print(f"   用户数量: {len(user_data)}")
            
            if user_data:
                print("\n   TOP 用户流量统计:")
                for i, user in enumerate(user_data[:5]):  # 显示前5个用户
                    total_traffic = user.get('total_sent', 0) + user.get('total_recv', 0)
                    print(f"   {i+1}. {user.get('username', 'N/A')}: 发送 {user.get('total_sent', 0):,} 字节, 接收 {user.get('total_recv', 0):,} 字节, 总计 {total_traffic:,} 字节")
                    print(f"      数据点: {len(user.get('traffic', []))} 个")
            else:
                print("   无用户流量数据")
        else:
            print(f"   ❌ API 调用失败: {response.status_code}")
            print(f"   响应: {response.text}")
    
    else:
        print(f"❌ 登录失败: {response.status_code}")

if __name__ == '__main__':
    test_user_traffic()
