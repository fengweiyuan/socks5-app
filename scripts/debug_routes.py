#!/usr/bin/env python3
"""
调试路由的脚本
"""

import requests
import json

def debug_routes():
    """调试路由"""
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
        
        # 测试所有流量相关的路由
        routes = [
            "/api/v1/traffic",
            "/api/v1/traffic/realtime", 
            "/api/v1/traffic/logs",
            "/api/v1/traffic/limits",
            "/api/v1/logs",
        ]
        
        for route in routes:
            print(f"\n🔍 测试路由: {route}")
            response = requests.get(f"{base_url}{route}", headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if 'logs' in data:
                    print(f"   日志数量: {len(data.get('logs', []))}")
                elif 'stats' in data:
                    print(f"   统计数据: {data.get('stats', {})}")
                elif 'realtime_traffic' in data:
                    print(f"   实时数据点: {len(data.get('realtime_traffic', []))}")
                else:
                    print(f"   响应数据: {str(data)[:100]}...")
            else:
                print(f"   错误: {response.text}")
    
    else:
        print(f"❌ 登录失败: {response.status_code}")

if __name__ == '__main__':
    debug_routes()
