#!/usr/bin/env python3
"""
简单的限速测试
"""
import time
import requests
import pymysql

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

def set_limit(user_id, limit_bps):
    """设置带宽限制"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bandwidth_limits WHERE user_id = %s", (user_id,))
    if limit_bps > 0:
        cursor.execute(
            "INSERT INTO bandwidth_limits (user_id, `limit`, enabled, created_at, updated_at) VALUES (%s, %s, 1, NOW(), NOW())",
            (user_id, limit_bps)
        )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✓ 设置限速: {limit_bps} B/s ({limit_bps/1024:.1f} KB/s)")

def test_speed(username, password, size=102400):
    """测试下载速度"""
    proxy = f'socks5://{username}:{password}@127.0.0.1:1082'
    url = f'http://127.0.0.1:8888/bytes/{size}'
    
    session = requests.Session()
    session.proxies = {'http': proxy}
    
    start = time.time()
    r = session.get(url, timeout=30)
    elapsed = time.time() - start
    
    if r.status_code == 200:
        speed_bps = len(r.content) / elapsed
        speed_kbps = speed_bps / 1024
        print(f"  下载 {len(r.content)} bytes in {elapsed:.2f}s = {speed_kbps:.2f} KB/s")
        return speed_bps
    return 0

print("="*60)
print("限速功能测试")
print("="*60)

user_id = 29
username = "fwy1014limit"
password = "fwy1014limit"

print(f"\n用户: {username} (ID: {user_id})")

# 测试1: 10 KB/s限速
print(f"\n测试1: 10 KB/s限速")
print(f"-"*60)
set_limit(user_id, 10240)
print("重启代理让配置生效...")
import subprocess
subprocess.run("killall -9 proxy; sleep 1; cd /Users/fwy/code/pub/socks5-app && ./bin/proxy > logs/proxy.log 2>&1 &", shell=True)
time.sleep(3)
print("开始测试...")
for i in range(3):
    print(f"测试 {i+1}:")
    test_speed(username, password, 102400)

# 测试2: 50 KB/s限速
print(f"\n测试2: 50 KB/s限速")
print(f"-"*60)
set_limit(user_id, 51200)
subprocess.run("killall -9 proxy; sleep 1; cd /Users/fwy/code/pub/socks5-app && ./bin/proxy > logs/proxy.log 2>&1 &", shell=True)
time.sleep(3)
print("开始测试...")
for i in range(3):
    print(f"测试 {i+1}:")
    test_speed(username, password, 102400)

# 测试3: 无限制
print(f"\n测试3: 无限制")
print(f"-"*60)
set_limit(user_id, 0)
subprocess.run("killall -9 proxy; sleep 1; cd /Users/fwy/code/pub/socks5-app && ./bin/proxy > logs/proxy.log 2>&1 &", shell=True)
time.sleep(3)
print("开始测试...")
for i in range(3):
    print(f"测试 {i+1}:")
    test_speed(username, password, 102400)

print(f"\n{'='*60}")
print("测试完成")
print(f"{'='*60}")

