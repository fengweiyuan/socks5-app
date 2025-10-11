#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试URL过滤日志输出
验证当URL被阻止时，日志是否包含详细信息
"""

import pymysql
import socks
import socket
import time
import subprocess
import sys

# 配置
PROXY_HOST = "localhost"
PROXY_PORT = 1082
TEST_USER = "testuser"
TEST_PASSWORD = "testpass"

# MySQL配置
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db',
    'charset': 'utf8mb4'
}


def print_section(title):
    """打印分隔标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def create_filter(pattern, description):
    """创建过滤规则"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    sql = """
        INSERT INTO url_filters (pattern, type, description, enabled, created_at, updated_at)
        VALUES (%s, 'block', %s, 1, NOW(), NOW())
    """
    cursor.execute(sql, (pattern, description))
    conn.commit()
    filter_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return filter_id


def delete_filter(filter_id):
    """删除过滤规则"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM url_filters WHERE id = %s", (filter_id,))
    conn.commit()
    cursor.close()
    conn.close()


def clear_all_filters():
    """清空所有过滤规则"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM url_filters")
    conn.commit()
    cursor.close()
    conn.close()


def test_socks5_connection(target_host, target_port=80):
    """测试通过SOCKS5代理连接"""
    try:
        socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, 
                               username=TEST_USER, password=TEST_PASSWORD)
        socket.socket = socks.socksocket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((target_host, target_port))
        sock.close()
        return True
    except:
        return False
    finally:
        import importlib
        importlib.reload(socket)


def get_latest_log_lines(n=50):
    """获取最新的日志行"""
    try:
        result = subprocess.run(
            ['tail', '-n', str(n), 'logs/proxy.log'],
            capture_output=True,
            text=True,
            cwd='/Users/fwy/code/pub/socks5-app'
        )
        return result.stdout
    except:
        return ""


def main():
    print_section("URL过滤日志测试")
    
    print("\n本测试将验证URL过滤阻止访问时的日志输出")
    
    # 清空现有规则
    print_section("步骤1: 清空现有过滤规则")
    clear_all_filters()
    print("✓ 已清空所有过滤规则")
    
    # 创建测试规则
    print_section("步骤2: 创建测试过滤规则")
    filter_id = create_filter("baidu.com", "测试日志输出 - 阻止百度")
    print(f"✓ 创建过滤规则 ID: {filter_id}")
    print(f"  Pattern: baidu.com")
    print(f"  Type: block")
    print(f"  Description: 测试日志输出 - 阻止百度")
    
    time.sleep(1)
    
    # 清空日志缓冲区（读取当前日志）
    print_section("步骤3: 准备测试环境")
    print("等待服务准备就绪...")
    time.sleep(1)
    
    # 测试访问被阻止的网站
    print_section("步骤4: 尝试访问被阻止的网站")
    print("\n尝试访问 baidu.com (应该被阻止)...")
    result = test_socks5_connection("baidu.com", 80)
    
    if result:
        print("✗ 访问成功（不符合预期，规则未生效）")
    else:
        print("✓ 访问被阻止（符合预期）")
    
    # 等待日志写入
    time.sleep(1)
    
    # 检查日志
    print_section("步骤5: 检查日志输出")
    log_content = get_latest_log_lines(50)
    
    # 查找URL过滤相关的日志
    filter_logs = [line for line in log_content.split('\n') if 'URL过滤' in line or 'URL被过滤' in line]
    
    if filter_logs:
        print(f"\n✓ 找到 {len(filter_logs)} 条URL过滤相关日志:\n")
        for i, log_line in enumerate(filter_logs, 1):
            print(f"日志 {i}:")
            print(f"  {log_line}")
            print()
        
        # 检查日志是否包含关键信息
        print_section("步骤6: 验证日志内容")
        
        has_username = any('用户:' in log or 'Username' in log for log in filter_logs)
        has_target = any('目标地址:' in log or 'baidu.com' in log for log in filter_logs)
        has_pattern = any('Pattern' in log or '匹配规则' in log for log in filter_logs)
        has_description = any('描述:' in log or '测试日志输出' in log for log in filter_logs)
        
        print("\n日志内容检查:")
        print(f"  {'✓' if has_username else '✗'} 包含用户信息")
        print(f"  {'✓' if has_target else '✗'} 包含目标地址")
        print(f"  {'✓' if has_pattern else '✗'} 包含匹配规则")
        print(f"  {'✓' if has_description else '✗'} 包含规则描述")
        
        if all([has_username, has_target, has_pattern, has_description]):
            print("\n✅ 日志输出完整，包含所有必要信息！")
        else:
            print("\n⚠️  日志信息不完整")
    else:
        print("\n✗ 未找到URL过滤相关日志")
        print("\n最近的日志内容:")
        print(log_content[-500:] if log_content else "无法读取日志")
    
    # 清理
    print_section("步骤7: 清理测试数据")
    delete_filter(filter_id)
    print(f"✓ 已删除测试过滤规则 ID: {filter_id}")
    
    print_section("测试完成")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

