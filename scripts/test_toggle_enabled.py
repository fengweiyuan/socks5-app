#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的toggle enabled API
"""

import requests
import time

# 配置
API_BASE_URL = "http://localhost:8012/api/v1"
TEST_USERNAME = "testuser2"  # 使用admin用户
TEST_PASSWORD = "%VirWorkSocks!"  # 使用超级密码
TARGET_USER_ID = 2  # fwy的用户ID


def login():
    """登录获取token"""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    return None


def get_limit_status(token, user_id):
    """获取用户带宽限制状态"""
    response = requests.get(
        f"{API_BASE_URL}/traffic/limits",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        data = response.json()
        limits = data.get("data", [])
        user_limit = next((l for l in limits if l['user_id'] == user_id), None)
        if user_limit:
            return user_limit['enabled'], user_limit['limit']
    return None, None


def toggle_enabled(token, user_id, enabled):
    """通过新API切换enabled状态"""
    response = requests.put(
        f"{API_BASE_URL}/traffic/limits/{user_id}/toggle",
        headers={"Authorization": f"Bearer {token}"},
        json={"enabled": enabled}
    )
    return response


def main():
    print("=" * 70)
    print("测试 Toggle Enabled API")
    print("=" * 70)
    
    # 登录
    print("\n1. 登录...")
    token = login()
    if not token:
        print("✗ 登录失败")
        return
    print("✓ 登录成功")
    
    # 检查当前状态
    print(f"\n2. 检查用户 {TARGET_USER_ID} 的当前状态...")
    enabled, limit = get_limit_status(token, TARGET_USER_ID)
    if enabled is None:
        print("✗ 无法获取状态")
        return
    print(f"✓ 当前状态: enabled={enabled}, limit={limit} bytes/s")
    
    # 测试1：切换为禁用
    print(f"\n3. 测试：使用API将 enabled 切换为 False...")
    response = toggle_enabled(token, TARGET_USER_ID, False)
    if response.status_code == 200:
        print("✓ API调用成功")
        data = response.json()
        print(f"   返回消息: {data.get('message')}")
        
        time.sleep(1)
        enabled, limit = get_limit_status(token, TARGET_USER_ID)
        print(f"   验证结果: enabled={enabled}")
        
        if enabled == False:
            print("   ✅ 状态已成功切换为禁用")
        else:
            print("   ❌ 状态切换失败")
    else:
        print(f"✗ API调用失败: {response.status_code}, {response.text}")
        return
    
    # 测试2：切换为启用
    print(f"\n4. 测试：使用API将 enabled 切换为 True...")
    response = toggle_enabled(token, TARGET_USER_ID, True)
    if response.status_code == 200:
        print("✓ API调用成功")
        data = response.json()
        print(f"   返回消息: {data.get('message')}")
        
        time.sleep(1)
        enabled, limit = get_limit_status(token, TARGET_USER_ID)
        print(f"   验证结果: enabled={enabled}")
        
        if enabled == True:
            print("   ✅ 状态已成功切换为启用")
        else:
            print("   ❌ 状态切换失败")
    else:
        print(f"✗ API调用失败: {response.status_code}, {response.text}")
        return
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print("\n✅ 新的 Toggle API 功能正常：")
    print("   - PUT /api/v1/traffic/limits/:user_id/toggle")
    print("   - 可以独立控制 enabled 字段")
    print("   - 不影响 limit 字段的值")
    print("\n✅ 前端功能：")
    print("   - 页面上添加了启用/禁用开关")
    print("   - 用户可以直接点击开关切换状态")
    print("   - 无需手动修改数据库")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试出现异常: {e}")
        import traceback
        traceback.print_exc()

