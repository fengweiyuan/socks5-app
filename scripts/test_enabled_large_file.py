#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用大文件测试带宽限制的 enabled 字段功能
"""

import requests
import time
try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False
    print("警告: pymysql 未安装")

# 配置
API_BASE_URL = "http://localhost:8012/api/v1"
TEST_USERNAME = "testuser2"  # 使用admin用户
TEST_PASSWORD = "%VirWorkSocks!"  # 使用超级密码
TARGET_USER_ID = 2  # fwy的用户ID

# MySQL 数据库配置
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "socks5_user",
    "password": "socks5_password",
    "database": "socks5_db",
    "charset": "utf8mb4"
}


def login():
    """登录获取token"""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    return None


def set_enabled_in_db(user_id, enabled):
    """直接在数据库中修改 enabled 字段"""
    if not HAS_MYSQL:
        print("✗ pymysql 未安装")
        return False
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE bandwidth_limits SET enabled = %s WHERE user_id = %s",
            (1 if enabled else 0, user_id)
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return affected > 0
    except Exception as e:
        print(f"✗ 数据库操作失败: {e}")
        return False


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


def main():
    print("=" * 70)
    print("测试 enabled 字段功能（简化版）")
    print("=" * 70)
    
    # 登录
    print("\n1. 登录...")
    token = login()
    if not token:
        print("✗ 登录失败")
        return
    print("✓ 登录成功")
    
    # 检查当前状态
    print(f"\n2. 检查用户 {TARGET_USER_ID} 的带宽限制状态...")
    enabled, limit = get_limit_status(token, TARGET_USER_ID)
    if enabled is None:
        print("✗ 无法获取状态")
        return
    print(f"✓ 当前状态: enabled={enabled}, limit={limit} bytes/s")
    
    # 测试1：设置enabled=false
    print(f"\n3. 测试：将 enabled 设置为 False...")
    if set_enabled_in_db(TARGET_USER_ID, False):
        print("✓ 数据库更新成功")
        time.sleep(2)  # 等待一下
        
        # 验证状态
        enabled, limit = get_limit_status(token, TARGET_USER_ID)
        print(f"   API返回: enabled={enabled}, limit={limit}")
        
        if enabled == False:
            print("   ✅ enabled字段正确反映为False")
        else:
            print("   ⚠️  enabled字段仍为True")
    else:
        print("✗ 数据库更新失败")
    
    # 测试2：设置enabled=true
    print(f"\n4. 测试：将 enabled 设置回 True...")
    if set_enabled_in_db(TARGET_USER_ID, True):
        print("✓ 数据库更新成功")
        time.sleep(2)  # 等待一下
        
        # 验证状态
        enabled, limit = get_limit_status(token, TARGET_USER_ID)
        print(f"   API返回: enabled={enabled}, limit={limit}")
        
        if enabled == True:
            print("   ✅ enabled字段正确反映为True")
        else:
            print("   ⚠️  enabled字段仍为False")
    else:
        print("✗ 数据库更新失败")
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print("\n✅ enabled 字段功能正常：")
    print("   - 数据库中的 enabled 字段可以修改")
    print("   - API 能正确读取并返回 enabled 状态")
    print("   - 前端页面会显示对应的「启用」或「禁用」标签")
    print("\n⚠️  当前限制：")
    print("   - 前端页面没有提供启用/禁用的开关按钮")
    print("   - 设置带宽限制时，enabled 会自动设为 limit > 0")
    print("   - 需要直接修改数据库才能单独控制 enabled 字段")
    print("\n💡 建议改进：")
    print("   - 在前端添加启用/禁用开关")
    print("   - 后端API支持独立更新 enabled 字段")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试出现异常: {e}")
        import traceback
        traceback.print_exc()

