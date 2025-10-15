#!/usr/bin/env python3
"""
测试限速功能是否正常工作
"""
import time
import requests
import pymysql
import bcrypt

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
TEST_URL = "http://127.0.0.1:8888/bytes/102400"  # 下载100KB数据

def create_test_user():
    """创建测试用户"""
    print("步骤1: 创建测试用户...")
    print("="*60)
    
    username = "fwy1014limit"
    password = "fwy1014limit"
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除已存在的用户
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        cursor.execute("DELETE FROM bandwidth_limits WHERE user_id IN (SELECT id FROM users WHERE username = %s)", (username,))
        
        # 创建新用户
        hashed_pwd = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        sql = """
        INSERT INTO users (username, password, role, status, bandwidth_limit, created_at, updated_at)
        VALUES (%s, %s, 'user', 'active', 0, NOW(), NOW())
        """
        cursor.execute(sql, (username, hashed_pwd))
        conn.commit()
        
        # 获取用户ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]
        
        print(f"✓ 用户创建成功")
        print(f"  用户名: {username}")
        print(f"  用户ID: {user_id}")
        print(f"  密码: {password}")
        
        cursor.close()
        conn.close()
        
        return user_id, username, password
    except Exception as e:
        print(f"✗ 创建用户失败: {e}")
        return None, None, None

def set_bandwidth_limit(user_id, limit_bps):
    """设置用户带宽限制"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除旧的限制
        cursor.execute("DELETE FROM bandwidth_limits WHERE user_id = %s", (user_id,))
        
        # 插入新限制
        if limit_bps > 0:
            sql = """
            INSERT INTO bandwidth_limits (user_id, `limit`, enabled, created_at, updated_at)
            VALUES (%s, %s, 1, NOW(), NOW())
            """
            cursor.execute(sql, (user_id, limit_bps))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if limit_bps > 0:
            print(f"✓ 设置带宽限制: {limit_bps} B/s ({limit_bps/1024:.1f} KB/s)")
        else:
            print(f"✓ 移除带宽限制（无限制）")
        return True
    except Exception as e:
        print(f"✗ 设置带宽限制失败: {e}")
        return False

def test_download_speed(username, password, test_name):
    """测试下载速度"""
    proxy_url = f'socks5://{username}:{password}@{PROXY_HOST}:{PROXY_PORT}'
    
    session = requests.Session()
    session.proxies = {'http': proxy_url}
    
    # 下载多次取平均值
    speeds = []
    for i in range(3):
        try:
            start = time.time()
            response = session.get(TEST_URL, timeout=30)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                bytes_received = len(response.content)
                speed_bps = bytes_received / elapsed
                speed_kbps = speed_bps / 1024
                speeds.append(speed_bps)
                print(f"  测试 {i+1}: {bytes_received} bytes in {elapsed:.2f}s = {speed_kbps:.2f} KB/s")
            else:
                print(f"  测试 {i+1}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  测试 {i+1}: 错误 - {e}")
    
    if speeds:
        avg_speed = sum(speeds) / len(speeds)
        avg_kbps = avg_speed / 1024
        print(f"  平均速度: {avg_kbps:.2f} KB/s ({avg_speed:.0f} B/s)")
        return avg_speed
    return 0

def main():
    print("="*60)
    print("带宽限速功能测试")
    print("="*60)
    
    # 1. 创建测试用户
    user_id, username, password = create_test_user()
    if not user_id:
        return
    
    # 等待用户缓存刷新（最多120秒）
    print("\n等待5秒让代理加载新用户...")
    time.sleep(5)
    
    # 2. 测试不同的限速值
    test_cases = [
        {"name": "无限制", "limit_bps": 0, "expected": "无限制"},
        {"name": "10KB/s限速", "limit_bps": 10240, "expected": "~10KB/s"},
        {"name": "50KB/s限速", "limit_bps": 51200, "expected": "~50KB/s"},
        {"name": "100KB/s限速", "limit_bps": 102400, "expected": "~100KB/s"},
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {test_case['name']}")
        print(f"{'='*60}")
        
        # 设置限速
        if not set_bandwidth_limit(user_id, test_case['limit_bps']):
            continue
        
        # 等待限速配置刷新（120秒刷新周期）
        print("等待3秒让限速配置生效...")
        time.sleep(3)
        
        # 测试下载速度
        print(f"\n测试下载速度（预期: {test_case['expected']}）:")
        actual_speed = test_download_speed(username, password, test_case['name'])
        
        results.append({
            'name': test_case['name'],
            'limit': test_case['limit_bps'],
            'expected': test_case['expected'],
            'actual_bps': actual_speed,
            'actual_kbps': actual_speed / 1024
        })
    
    # 3. 打印汇总报告
    print(f"\n{'='*60}")
    print("限速测试汇总")
    print(f"{'='*60}")
    print(f"{'测试项':<15} {'设定限速':<15} {'实际速度':<20} {'符合预期':<10}")
    print(f"{'-'*60}")
    
    for r in results:
        limit_str = f"{r['limit']/1024:.0f} KB/s" if r['limit'] > 0 else "无限制"
        actual_str = f"{r['actual_kbps']:.2f} KB/s"
        
        # 判断是否符合预期
        if r['limit'] == 0:
            # 无限制，速度应该很快
            符合 = "✓" if r['actual_kbps'] > 50 else "✗"
        else:
            # 有限制，实际速度应该接近限制值（允许±30%误差）
            expected_kbps = r['limit'] / 1024
            ratio = r['actual_kbps'] / expected_kbps
            符合 = "✓" if 0.7 <= ratio <= 1.3 else "✗"
        
        print(f"{r['name']:<15} {limit_str:<15} {actual_str:<20} {符合:<10}")
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")

