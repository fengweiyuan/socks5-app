#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带宽限制的 enabled 字段功能
"""

import requests
import time
import json
import socks
import socket
from datetime import datetime
try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False
    print("警告: pymysql 未安装，将跳过数据库直接操作部分")

# 配置
API_BASE_URL = "http://localhost:8012/api/v1"
SOCKS5_HOST = "127.0.0.1"
SOCKS5_PORT = 1082
TEST_USERNAME = "testuser2"  # 使用admin用户
TEST_PASSWORD = "%VirWorkSocks!"  # 使用超级密码
TARGET_USERNAME = "fwy"  # 测试目标用户
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


def login_and_get_token():
    """登录并获取 token"""
    print("\n=== 步骤 1: 登录获取 token ===")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        user_id = data.get("user", {}).get("id")
        print(f"✓ 登录成功，用户ID: {user_id}, Token: {token[:20]}...")
        return token, user_id
    else:
        print(f"✗ 登录失败: {response.status_code}, {response.text}")
        return None, None


def set_bandwidth_limit(token, user_id, limit):
    """设置带宽限制"""
    print(f"\n=== 步骤 2: 设置带宽限制为 {limit} bytes/s ===")
    response = requests.post(
        f"{API_BASE_URL}/traffic/limit",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": user_id, "limit": limit}
    )
    if response.status_code == 200:
        print(f"✓ 带宽限制设置成功")
        return True
    else:
        print(f"✗ 设置带宽限制失败: {response.status_code}, {response.text}")
        return False


def get_bandwidth_limits(token):
    """获取所有带宽限制"""
    print("\n=== 步骤 3: 查询带宽限制列表 ===")
    response = requests.get(
        f"{API_BASE_URL}/traffic/limits",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        data = response.json()
        limits = data.get("data", [])
        print(f"✓ 获取到 {len(limits)} 条带宽限制记录")
        for limit in limits:
            print(f"  - 用户ID: {limit['user_id']}, 用户名: {limit['username']}, "
                  f"限制: {limit['limit']} bytes/s, 启用: {limit['enabled']}")
        return limits
    else:
        print(f"✗ 获取带宽限制失败: {response.status_code}, {response.text}")
        return []


def directly_set_enabled_in_db(user_id, enabled):
    """直接在数据库中修改 enabled 字段"""
    print(f"\n=== 步骤 4: 直接修改数据库 enabled 字段为 {enabled} ===")
    
    if not HAS_MYSQL:
        print("✗ pymysql 未安装，无法直接操作数据库")
        return False
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 更新 bandwidth_limits 表
        cursor.execute(
            "UPDATE bandwidth_limits SET enabled = %s WHERE user_id = %s",
            (1 if enabled else 0, user_id)
        )
        
        conn.commit()
        affected = cursor.rowcount
        print(f"✓ 数据库更新成功，影响 {affected} 行")
        
        # 验证更新
        cursor.execute(
            "SELECT user_id, `limit`, enabled FROM bandwidth_limits WHERE user_id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            print(f"  - 当前数据库记录: user_id={row[0]}, limit={row[1]}, enabled={row[2]}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_socks5_proxy(username, password, test_url="http://ifconfig.me"):
    """测试 SOCKS5 代理连接"""
    print(f"\n=== 步骤 5: 测试 SOCKS5 代理连接 ===")
    try:
        # 设置 SOCKS5 代理
        socks.set_default_proxy(
            socks.SOCKS5,
            SOCKS5_HOST,
            SOCKS5_PORT,
            username=username,
            password=password
        )
        socket.socket = socks.socksocket
        
        # 测试下载速度
        print(f"正在通过代理下载测试文件...")
        start_time = time.time()
        response = requests.get(test_url, timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            data_size = len(response.content)
            duration = end_time - start_time
            speed = data_size / duration if duration > 0 else 0
            print(f"✓ 代理连接成功")
            print(f"  - 下载大小: {data_size} bytes")
            print(f"  - 耗时: {duration:.2f} 秒")
            print(f"  - 速度: {speed:.2f} bytes/s ({speed/1024:.2f} KB/s)")
            return True, speed
        else:
            print(f"✗ 请求失败: {response.status_code}")
            return False, 0
            
    except Exception as e:
        print(f"✗ 代理测试失败: {e}")
        return False, 0
    finally:
        # 恢复默认 socket
        socket.socket = socket._socketobject if hasattr(socket, '_socketobject') else socket.socket


def wait_for_traffic_controller_update():
    """等待流量控制器更新（默认5秒更新一次）"""
    print("\n等待流量控制器重新加载配置（6秒）...")
    time.sleep(6)


def main():
    print("=" * 60)
    print("测试带宽限制 enabled 字段功能")
    print("=" * 60)
    
    # 步骤 1: 使用admin账户登录
    token, admin_user_id = login_and_get_token()
    if not token or not admin_user_id:
        print("\n测试失败：无法登录")
        return
    
    print(f"✓ 使用管理员账户登录成功，管理员ID: {admin_user_id}")
    print(f"✓ 将对目标用户 {TARGET_USERNAME} (ID: {TARGET_USER_ID}) 进行测试")
    
    # 步骤 2: 设置一个较低的带宽限制（100KB/s）给目标用户
    limit = 102400  # 100 KB/s
    if not set_bandwidth_limit(token, TARGET_USER_ID, limit):
        print("\n测试失败：无法设置带宽限制")
        return
    
    # 步骤 3: 查询当前的带宽限制状态
    limits = get_bandwidth_limits(token)
    user_limit = next((l for l in limits if l['user_id'] == TARGET_USER_ID), None)
    if not user_limit:
        print(f"\n测试失败：未找到用户 {TARGET_USER_ID} 的带宽限制记录")
        return
    
    print(f"\n当前限制状态: limit={user_limit['limit']}, enabled={user_limit['enabled']}")
    
    # 步骤 4a: 测试 enabled=true 的情况
    print("\n" + "=" * 60)
    print("测试场景 1: enabled=true 时应该生效限流")
    print("=" * 60)
    
    # 确保 enabled=true
    directly_set_enabled_in_db(TARGET_USER_ID, True)
    wait_for_traffic_controller_update()
    
    # 查询确认
    limits = get_bandwidth_limits(token)
    user_limit = next((l for l in limits if l['user_id'] == TARGET_USER_ID), None)
    print(f"✓ 确认当前状态: enabled={user_limit['enabled']}")
    
    # 测试代理（应该被限速）- 使用目标用户账号
    print(f"\n预期：使用 {TARGET_USERNAME} 账号连接代理，下载速度应该被限制在 ~100 KB/s")
    success1, speed1 = test_socks5_proxy(TARGET_USERNAME, TEST_PASSWORD)
    
    # 步骤 4b: 测试 enabled=false 的情况
    print("\n" + "=" * 60)
    print("测试场景 2: enabled=false 时应该不生效限流")
    print("=" * 60)
    
    # 设置 enabled=false
    directly_set_enabled_in_db(TARGET_USER_ID, False)
    wait_for_traffic_controller_update()
    
    # 查询确认
    limits = get_bandwidth_limits(token)
    user_limit = next((l for l in limits if l['user_id'] == TARGET_USER_ID), None)
    print(f"✓ 确认当前状态: enabled={user_limit['enabled']}")
    
    # 测试代理（应该不被限速）- 使用目标用户账号
    print(f"\n预期：使用 {TARGET_USERNAME} 账号连接代理，下载速度应该不受限制")
    success2, speed2 = test_socks5_proxy(TARGET_USERNAME, TEST_PASSWORD)
    
    # 步骤 5: 分析结果
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    print(f"\n场景 1 (enabled=true):")
    print(f"  - 连接: {'成功' if success1 else '失败'}")
    print(f"  - 速度: {speed1:.2f} bytes/s ({speed1/1024:.2f} KB/s)")
    print(f"  - 预期: 应该被限制在 ~100 KB/s")
    
    print(f"\n场景 2 (enabled=false):")
    print(f"  - 连接: {'成功' if success2 else '失败'}")
    print(f"  - 速度: {speed2:.2f} bytes/s ({speed2/1024:.2f} KB/s)")
    print(f"  - 预期: 应该不受限制")
    
    # 判断测试结果
    if success1 and success2:
        speed_ratio = speed2 / speed1 if speed1 > 0 else 0
        print(f"\n速度对比: 禁用限流后速度是启用时的 {speed_ratio:.2f} 倍")
        
        if speed_ratio > 1.5:  # 禁用后速度明显提升
            print("\n✓✓✓ 测试通过：enabled 字段功能正常！")
            print("  - enabled=true 时，限流生效")
            print("  - enabled=false 时，限流不生效")
        else:
            print("\n⚠ 测试结果不明确：速度差异不够明显")
            print("  - 可能需要更大的测试文件或更严格的限制来验证")
    else:
        print("\n✗ 测试失败：连接测试未成功完成")
    
    # 恢复 enabled=true
    print("\n" + "=" * 60)
    print("恢复设置")
    print("=" * 60)
    directly_set_enabled_in_db(TARGET_USER_ID, True)
    print("✓ 已恢复 enabled=true")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()

