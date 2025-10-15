#!/usr/bin/env python3
"""
验证带宽限制是否正确加载
"""
import pymysql

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

def check_bandwidth_limit(username):
    """检查用户的带宽限制"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 查询用户
        cursor.execute("SELECT id, username, bandwidth_limit FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"用户 {username} 不存在")
            return
        
        user_id, username, user_limit = user
        print(f"用户信息:")
        print(f"  ID: {user_id}")
        print(f"  用户名: {username}")
        print(f"  users表中的bandwidth_limit: {user_limit}")
        
        # 查询bandwidth_limits表
        cursor.execute("SELECT id, `limit`, enabled FROM bandwidth_limits WHERE user_id = %s", (user_id,))
        limit_record = cursor.fetchone()
        
        if limit_record:
            limit_id, limit_value, enabled = limit_record
            print(f"\nbandwidth_limits表记录:")
            print(f"  ID: {limit_id}")
            print(f"  限制值: {limit_value} B/s ({limit_value/1024:.1f} KB/s)")
            print(f"  是否启用: {enabled}")
        else:
            print(f"\n bandwidth_limits表中无记录")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    check_bandwidth_limit("fwy1014limit")

