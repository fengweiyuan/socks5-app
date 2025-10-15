#!/usr/bin/env python3
"""
创建测试用户
"""
import bcrypt
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

def hash_password(password):
    """密码加密"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_user(username, password):
    """创建用户"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"用户 {username} 已存在，删除后重建...")
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        
        # 创建新用户
        hashed_pwd = hash_password(password)
        sql = """
        INSERT INTO users (username, password, role, status, bandwidth_limit, created_at, updated_at)
        VALUES (%s, %s, 'user', 'active', 0, NOW(), NOW())
        """
        cursor.execute(sql, (username, hashed_pwd))
        conn.commit()
        
        print(f"✓ 用户 {username} 创建成功")
        print(f"  - 用户名: {username}")
        print(f"  - 密码: {password}")
        print(f"  - 角色: user")
        print(f"  - 状态: active")
        print(f"  - 带宽限制: 0 (无限制)")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 创建用户失败: {e}")
        return False

if __name__ == "__main__":
    create_user("fwy1014", "fwy1014")
