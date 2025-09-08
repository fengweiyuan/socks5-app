#!/usr/bin/env python3
"""
创建测试用户脚本
"""

import bcrypt
import pymysql

def create_test_user():
    """创建测试用户"""
    # 连接数据库
    connection = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='socks5_user',
        password='socks5_password',
        database='socks5_db',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # 创建测试用户
            username = 'testuser'
            password = 'testpass'
            
            # 使用 bcrypt 加密密码
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # 插入或更新用户
            sql = """
            INSERT INTO users (username, password, email, role, status, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE 
            password = VALUES(password),
            status = VALUES(status),
            updated_at = NOW()
            """
            
            cursor.execute(sql, (username, hashed_password, 'test@example.com', 'user', 'active'))
            connection.commit()
            
            print(f"✅ 测试用户创建成功:")
            print(f"   用户名: {username}")
            print(f"   密码: {password}")
            print(f"   加密密码: {hashed_password}")
            
            # 验证用户
            cursor.execute("SELECT id, username, status FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                print(f"   用户ID: {user[0]}")
                print(f"   状态: {user[2]}")
            
    except Exception as e:
        print(f"❌ 创建用户失败: {str(e)}")
    finally:
        connection.close()

if __name__ == '__main__':
    create_test_user()
