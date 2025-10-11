#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的URL过滤功能测试脚本
专门测试：设置baidu.com过滤后，163.com是否能访问
"""

import requests
import socks
import socket
import time
import sys
import pymysql

# 配置
API_BASE_URL = "http://localhost:8012/api/v1"
PROXY_HOST = "localhost"
PROXY_PORT = 1082

# 管理员凭证
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"

# 测试用户凭证
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


def check_mysql_connection():
    """检查MySQL连接"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        print("✓ MySQL连接成功")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ MySQL连接失败: {e}")
        return False


def get_filters_from_db():
    """从数据库直接查询过滤规则"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM url_filters WHERE enabled = 1")
        filters = cursor.fetchall()
        cursor.close()
        conn.close()
        return filters
    except Exception as e:
        print(f"查询过滤规则失败: {e}")
        return []


def create_filter_in_db(pattern, filter_type, description):
    """直接在数据库中创建过滤规则"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        sql = """
            INSERT INTO url_filters (pattern, type, description, enabled, created_at, updated_at)
            VALUES (%s, %s, %s, 1, NOW(), NOW())
        """
        cursor.execute(sql, (pattern, filter_type, description))
        conn.commit()
        filter_id = cursor.lastrowid
        cursor.close()
        conn.close()
        print(f"✓ 过滤规则创建成功 ID: {filter_id}")
        return filter_id
    except Exception as e:
        print(f"✗ 创建过滤规则失败: {e}")
        return None


def delete_filter_from_db(filter_id):
    """从数据库中删除过滤规则"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM url_filters WHERE id = %s", (filter_id,))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✓ 过滤规则删除成功 ID: {filter_id}")
        return True
    except Exception as e:
        print(f"✗ 删除过滤规则失败: {e}")
        return False


def clear_all_filters():
    """清空所有过滤规则"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM url_filters")
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        print(f"✓ 已清空所有过滤规则 (删除了 {affected} 条)")
        return True
    except Exception as e:
        print(f"✗ 清空过滤规则失败: {e}")
        return False


def test_socks5_connection(target_host, target_port=80, timeout=10):
    """测试通过SOCKS5代理连接目标主机"""
    try:
        # 配置SOCKS5代理
        socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, 
                               username=TEST_USER, password=TEST_PASSWORD)
        socket.socket = socks.socksocket
        
        # 尝试连接
        print(f"  尝试连接: {target_host}:{target_port} ...", end=" ")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((target_host, target_port))
        sock.close()
        
        print(f"✓ 成功")
        return True
        
    except socks.ProxyConnectionError as e:
        print(f"✗ 被代理拒绝")
        return False
    except socket.timeout:
        print(f"✗ 连接超时")
        return False
    except Exception as e:
        print(f"✗ 失败: {type(e).__name__}")
        return False
    finally:
        # 重置socket
        import importlib
        importlib.reload(socket)


def main():
    """主测试函数"""
    print_section("URL过滤功能测试 - baidu.com vs 163.com")
    
    # 检查MySQL连接
    if not check_mysql_connection():
        print("\n请确保MySQL服务正在运行，并且配置正确")
        return 1
    
    print("\n测试目标：")
    print("  1. 设置URL过滤规则阻止 baidu.com")
    print("  2. 验证访问 baidu.com 会被阻止")
    print("  3. 验证访问 www.163.com 可以成功")
    
    try:
        # 步骤1: 清空现有过滤规则
        print_section("步骤1: 清空现有过滤规则")
        clear_all_filters()
        
        # 步骤2: 测试无过滤规则时的访问情况
        print_section("步骤2: 测试无过滤规则时的访问（基准测试）")
        print("\n没有任何过滤规则时的访问测试：")
        result_baidu_before = test_socks5_connection("baidu.com", 80)
        result_163_before = test_socks5_connection("www.163.com", 80)
        
        if not result_baidu_before and not result_163_before:
            print("\n⚠️  警告：在没有过滤规则时，两个网站都无法访问")
            print("这可能是网络问题或代理服务问题，而非过滤规则问题")
            return 1
        
        # 步骤3: 创建block规则
        print_section("步骤3: 创建过滤规则 - Block baidu.com")
        filter_id = create_filter_in_db("baidu.com", "block", "测试：阻止访问百度")
        
        if not filter_id:
            print("创建过滤规则失败")
            return 1
        
        # 等待规则生效
        print("\n等待2秒让规则生效...")
        time.sleep(2)
        
        # 查看当前规则
        filters = get_filters_from_db()
        print(f"\n当前启用的过滤规则 ({len(filters)} 条):")
        for f in filters:
            print(f"  - ID: {f['id']}, Pattern: '{f['pattern']}', Type: '{f['type']}', Enabled: {f['enabled']}")
        
        # 步骤4: 测试有过滤规则时的访问情况
        print_section("步骤4: 测试设置过滤规则后的访问情况")
        print("\n设置了 block baidu.com 规则后的访问测试：")
        result_baidu_after = test_socks5_connection("baidu.com", 80)
        result_163_after = test_socks5_connection("www.163.com", 80)
        
        # 步骤5: 分析结果
        print_section("步骤5: 测试结果分析")
        
        print("\n访问 baidu.com:")
        print(f"  无规则时: {'✓ 成功' if result_baidu_before else '✗ 失败'}")
        print(f"  有规则时: {'✓ 成功' if result_baidu_after else '✗ 失败 (符合预期)'}")
        baidu_blocked = result_baidu_before and not result_baidu_after
        print(f"  结论: {'✓ baidu.com 被正确阻止' if baidu_blocked else '⚠️  规则未生效或其他问题'}")
        
        print("\n访问 www.163.com:")
        print(f"  无规则时: {'✓ 成功' if result_163_before else '✗ 失败'}")
        print(f"  有规则时: {'✓ 成功' if result_163_after else '✗ 失败'}")
        
        # 关键判断
        print("\n" + "="*70)
        print("【核心问题答案】")
        print("="*70)
        print(f"\n问题: 设置URL过滤 baidu.com 后，www.163.com 能否访问？")
        
        if result_163_after:
            print(f"\n答案: ✓ 可以访问")
            print("\n说明:")
            print("  • www.163.com 可以正常访问")
            print("  • URL过滤规则只阻止匹配的域名（baidu.com）")
            print("  • 其他域名不受影响")
            print("\n如果您遇到'设置过滤后内网地址无法访问'的问题，可能原因：")
            print("  1. 过滤规则的 pattern 设置过于宽泛（如只写了一个通配符）")
            print("  2. 过滤规则的 type 设置错误")
            print("  3. 需要检查数据库中实际保存的规则内容")
        else:
            print(f"\n答案: ✗ 无法访问")
            print("\n说明:")
            print("  • 这个结果不符合代码逻辑的预期")
            print("  • 当前代码应该只阻止包含 'baidu.com' 的地址")
            print("  • 建议检查：")
            print("    1. 数据库中的过滤规则是否正确")
            print("    2. checkURLFilter 函数的实现逻辑")
            print("    3. 是否有其他配置影响了访问")
        
        # 步骤6: 清理
        print_section("步骤6: 清理测试数据")
        delete_filter_from_db(filter_id)
        
        print("\n" + "="*70)
        print("测试完成")
        print("="*70)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

