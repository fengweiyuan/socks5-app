#!/usr/bin/env python3
"""
测试前端修改是否生效
"""

import requests
import json

def test_api_endpoints():
    """测试API端点是否正常工作"""
    base_url = "http://127.0.0.1:8012"
    
    # 1. 测试登录
    print("🔐 测试登录...")
    login_data = {
        "username": "testuser2",
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            token = result.get("token")
            print(f"✅ 登录成功，获取到token: {token[:20]}...")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False
    
    # 2. 测试获取带宽限制
    print("\n📋 测试获取带宽限制...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/v1/traffic/limits", headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取带宽限制成功，共 {result.get('total', 0)} 条记录")
            
            # 检查是否还有period字段
            if result.get('data'):
                for limit in result['data']:
                    if 'period' in limit:
                        print(f"⚠️  警告: 发现period字段: {limit.get('period')}")
                    else:
                        print(f"✅ 确认: 无period字段，只有limit: {limit.get('limit')}")
        else:
            print(f"❌ 获取带宽限制失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 获取带宽限制异常: {e}")
    
    # 3. 测试设置带宽限制（不包含period）
    print("\n🔧 测试设置带宽限制（无period参数）...")
    try:
        limit_data = {
            "user_id": 5,  # testuser2
            "limit": 1024  # 1KB/s
        }
        response = requests.post(f"{base_url}/api/v1/traffic/limit", json=limit_data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 设置带宽限制成功: {result.get('message', '成功')}")
        else:
            print(f"❌ 设置带宽限制失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 设置带宽限制异常: {e}")
    
    # 4. 测试更新带宽限制（不包含period）
    print("\n🔄 测试更新带宽限制（无period参数）...")
    try:
        update_data = {
            "limit": 2048  # 2KB/s
        }
        response = requests.put(f"{base_url}/api/v1/traffic/limits/5", json=update_data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 更新带宽限制成功: {result.get('message', '成功')}")
        else:
            print(f"❌ 更新带宽限制失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 更新带宽限制异常: {e}")
    
    # 5. 再次获取带宽限制确认修改
    print("\n📋 再次获取带宽限制确认修改...")
    try:
        response = requests.get(f"{base_url}/api/v1/traffic/limits", headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取带宽限制成功，共 {result.get('total', 0)} 条记录")
            
            # 查找testuser2的记录
            for limit in result.get('data', []):
                if limit.get('user_id') == 5:
                    print(f"📊 testuser2的带宽限制: {limit.get('limit')} 字节/秒")
                    if 'period' in limit:
                        print(f"⚠️  警告: 仍然存在period字段: {limit.get('period')}")
                    else:
                        print(f"✅ 确认: 无period字段，纯速度限制")
                    break
        else:
            print(f"❌ 获取带宽限制失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 获取带宽限制异常: {e}")
    
    print("\n🎉 前端修改测试完成！")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 前端修改测试 - 删除限制周期相关功能")
    print("=" * 60)
    
    test_api_endpoints()
