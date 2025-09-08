#!/usr/bin/env python3
"""
重置 fwy 用户密码的脚本
"""

import pymysql
import bcrypt

def reset_fwy_password():
    """重置 fwy 用户密码为 'fwy'"""
    try:
        # 连接数据库
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='socks5_user',
            password='socks5_password',
            database='socks5_db',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 生成新密码的哈希
            password = 'fwy'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # 更新密码
            cursor.execute(
                "UPDATE users SET password = %s WHERE username = %s",
                (password_hash, 'fwy')
            )
            
            connection.commit()
            print(f"✅ 已重置 fwy 用户密码为: {password}")
            print(f"密码哈希: {password_hash}")
            
    except Exception as e:
        print(f"❌ 重置密码失败: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    reset_fwy_password()
