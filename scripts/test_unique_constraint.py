#!/usr/bin/env python3
"""
测试唯一约束是否在API层面生效
"""

import requests
import json

def test_unique_constraint():
    """测试唯一约束在API层面的行为"""
    base_url = "http://127.0.0.1:8012"
    
    # 1. 登录
    print("🔐 登录...")
    login_data = {
        "username": "testuser2",
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            token = result.get("token")
            print(f"✅ 登录成功")
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 获取当前带宽限制
    print("\n📋 获取当前带宽限制...")
    try:
        response = requests.get(f"{base_url}/api/v1/traffic/limits", headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 当前有 {result.get('total', 0)} 条带宽限制记录")
            
            # 显示每个用户的限制
            for limit in result.get('data', []):
                print(f"   用户 {limit.get('user_id')}: {limit.get('limit')} 字节/秒")
        else:
            print(f"❌ 获取带宽限制失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取带宽限制异常: {e}")
    
    # 3. 尝试为已存在的用户设置带宽限制
    print("\n🔧 尝试为已存在的用户设置带宽限制...")
    try:
        # 为testuser2 (user_id=5) 设置新的带宽限制
        limit_data = {
            "user_id": 5,  # testuser2已经存在
            "limit": 4096  # 4KB/s
        }
        response = requests.post(f"{base_url}/api/v1/traffic/limit", json=limit_data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 设置成功: {result.get('message', '成功')}")
            print("   注意: 这应该是更新操作，而不是插入新记录")
        else:
            print(f"❌ 设置失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 设置异常: {e}")
    
    # 4. 验证更新后的限制
    print("\n📋 验证更新后的限制...")
    try:
        response = requests.get(f"{base_url}/api/v1/traffic/limits", headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 更新后有 {result.get('total', 0)} 条带宽限制记录")
            
            # 查找testuser2的记录
            for limit in result.get('data', []):
                if limit.get('user_id') == 5:
                    print(f"📊 testuser2的带宽限制: {limit.get('limit')} 字节/秒")
                    break
        else:
            print(f"❌ 获取带宽限制失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取带宽限制异常: {e}")
    
    # 5. 测试数据库层面的唯一约束
    print("\n🗄️ 测试数据库层面的唯一约束...")
    print("   现在尝试通过API为同一用户创建重复记录...")
    
    try:
        # 再次为testuser2设置限制，这次应该更新而不是创建新记录
        limit_data = {
            "user_id": 5,  # 同一个用户
            "limit": 8192  # 8KB/s
        }
        response = requests.post(f"{base_url}/api/v1/traffic/limit", json=limit_data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 操作成功: {result.get('message', '成功')}")
            print("   这应该是更新操作，不会创建重复记录")
        else:
            print(f"❌ 操作失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 操作异常: {e}")
    
    # 6. 最终验证
    print("\n📋 最终验证...")
    try:
        response = requests.get(f"{base_url}/api/v1/traffic/limits", headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 最终有 {result.get('total', 0)} 条带宽限制记录")
            
            # 统计每个用户的记录数
            user_counts = {}
            for limit in result.get('data', []):
                user_id = limit.get('user_id')
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
            
            print("📊 每个用户的记录数:")
            for user_id, count in user_counts.items():
                print(f"   用户 {user_id}: {count} 条记录")
                if count > 1:
                    print(f"   ⚠️  警告: 用户 {user_id} 有 {count} 条记录，违反了唯一约束！")
                else:
                    print(f"   ✅ 用户 {user_id} 只有 1 条记录，符合唯一约束")
        else:
            print(f"❌ 获取带宽限制失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取带宽限制异常: {e}")
    
    print("\n🎉 唯一约束测试完成！")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 唯一约束测试 - 确保一个用户只有一条带宽限制记录")
    print("=" * 60)
    
    test_unique_constraint()
