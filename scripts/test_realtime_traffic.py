#!/usr/bin/env python3
"""
测试实时流量监控的脚本
"""

import requests
import json
import time

def test_realtime_traffic():
    """测试实时流量监控"""
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
        print("\n📈 测试实时流量监控...")
        for i in range(3):
            print(f"\n第 {i+1} 次测试:")
            response = requests.get(f"{base_url}/api/v1/traffic/realtime", headers=headers)
            if response.status_code == 200:
                data = response.json()
                realtime_data = data.get('realtime_traffic', [])
                print(f"   数据点数量: {len(realtime_data)}")
                if realtime_data:
                    # 显示最新的几个数据点
                    latest_data = realtime_data[-3:] if len(realtime_data) >= 3 else realtime_data
                    for j, item in enumerate(latest_data):
                        timestamp = item.get('timestamp', 'N/A')
                        bytes_sent = item.get('bytes_sent', 0)
                        bytes_recv = item.get('bytes_recv', 0)
                        print(f"   数据点 {len(realtime_data)-len(latest_data)+j+1}: {timestamp} - 发送: {bytes_sent}, 接收: {bytes_recv}")
                else:
                    print("   无实时数据")
            else:
                print(f"   ❌ API 调用失败: {response.status_code}")
            
            if i < 2:  # 不是最后一次
                print("   等待 5 秒...")
                time.sleep(5)
    
    else:
        print(f"❌ 登录失败: {response.status_code}")

if __name__ == '__main__':
    test_realtime_traffic()
