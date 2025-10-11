#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL过滤日志演示脚本
展示日志输出效果
"""

import pymysql
import socks
import socket
import time
import subprocess

# 配置
PROXY_HOST = "localhost"
PROXY_PORT = 1082
TEST_USER = "testuser"
TEST_PASSWORD = "testpass"

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db',
    'charset': 'utf8mb4'
}


def create_filters():
    """创建多个测试规则"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    filters = [
        ("facebook.com", "阻止访问社交媒体网站"),
        ("twitter.com", "阻止访问Twitter"),
        ("pornhub.com", "禁止访问不良网站"),
    ]
    
    filter_ids = []
    for pattern, desc in filters:
        cursor.execute(
            "INSERT INTO url_filters (pattern, type, description, enabled, created_at, updated_at) "
            "VALUES (%s, 'block', %s, 1, NOW(), NOW())",
            (pattern, desc)
        )
        filter_ids.append(cursor.lastrowid)
    
    conn.commit()
    cursor.close()
    conn.close()
    return filter_ids


def clear_filters():
    """清空过滤规则"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM url_filters")
    conn.commit()
    cursor.close()
    conn.close()


def test_access(target):
    """测试访问"""
    try:
        socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, 
                               username=TEST_USER, password=TEST_PASSWORD)
        socket.socket = socks.socksocket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((target, 80))
        sock.close()
        return True
    except:
        return False
    finally:
        import importlib
        importlib.reload(socket)


def show_logs():
    """显示最新的URL过滤日志"""
    result = subprocess.run(
        ['tail', '-30', 'logs/proxy.log'],
        capture_output=True,
        text=True,
        cwd='/Users/fwy/code/pub/socks5-app'
    )
    
    lines = result.stdout.split('\n')
    filter_logs = [line for line in lines if 'URL过滤' in line]
    
    if filter_logs:
        print("\n📋 最新的URL过滤日志:")
        print("=" * 80)
        for log in filter_logs[-5:]:  # 显示最后5条
            print(log)
        print("=" * 80)


def main():
    print("=" * 80)
    print("  URL过滤日志演示")
    print("=" * 80)
    
    # 清空规则
    print("\n1. 清空现有规则...")
    clear_filters()
    
    # 创建规则
    print("\n2. 创建测试规则...")
    filter_ids = create_filters()
    print(f"   ✓ 创建了 {len(filter_ids)} 条过滤规则")
    
    time.sleep(1)
    
    # 测试访问多个被阻止的网站
    print("\n3. 测试访问被阻止的网站...")
    test_sites = ["facebook.com", "twitter.com", "pornhub.com"]
    
    for site in test_sites:
        print(f"   → 尝试访问 {site}...", end=" ")
        result = test_access(site)
        print("被阻止 ✓" if not result else "未阻止 ✗")
        time.sleep(0.5)
    
    # 显示日志
    print("\n4. 查看日志输出...")
    time.sleep(1)
    show_logs()
    
    # 清理
    print("\n5. 清理测试数据...")
    clear_filters()
    print("   ✓ 已清空所有规则")
    
    print("\n" + "=" * 80)
    print("  演示完成")
    print("=" * 80)
    print("\n💡 提示:")
    print("   - 查看完整日志: tail -f logs/proxy.log")
    print("   - 只看过滤日志: tail -f logs/proxy.log | grep 'URL过滤'")
    print("=" * 80)


if __name__ == "__main__":
    main()

