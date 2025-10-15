#!/usr/bin/env python3
"""
全面的带宽限速测试
测试多个限速值的准确性
"""
import time
import requests
import pymysql
import subprocess
import statistics

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

def set_limit_and_restart(user_id, limit_bps):
    """设置限速并重启代理"""
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
    
    # 重启代理
    subprocess.run("killall -9 proxy 2>/dev/null", shell=True)
    time.sleep(1)
    subprocess.run("cd /Users/fwy/code/pub/socks5-app && ./bin/proxy > logs/proxy.log 2>&1 &", shell=True)
    time.sleep(3)

def test_speed_multiple(username, password, size, count=5):
    """多次测试取平均值"""
    proxy = f'socks5://{username}:{password}@127.0.0.1:1082'
    url = f'http://127.0.0.1:8888/bytes/{size}'
    
    session = requests.Session()
    session.proxies = {'http': proxy}
    
    speeds = []
    for i in range(count):
        try:
            start = time.time()
            r = session.get(url, timeout=60)
            elapsed = time.time() - start
            
            if r.status_code == 200 and elapsed > 0:
                speed_bps = len(r.content) / elapsed
                speed_kbps = speed_bps / 1024
                speeds.append(speed_bps)
                print(f"    测试 {i+1}: {len(r.content)} bytes in {elapsed:.2f}s = {speed_kbps:.2f} KB/s")
        except Exception as e:
            print(f"    测试 {i+1}: 错误 - {e}")
    
    if speeds:
        avg_speed = statistics.mean(speeds)
        median_speed = statistics.median(speeds)
        print(f"    平均速度: {avg_speed/1024:.2f} KB/s")
        print(f"    中位数速度: {median_speed/1024:.2f} KB/s")
        return avg_speed, median_speed
    return 0, 0

def main():
    print("="*70)
    print("全面带宽限速测试")
    print("="*70)
    
    user_id = 29
    username = "fwy1014limit"
    password = "fwy1014limit"
    
    # 测试不同的限速值
    test_cases = [
        {"name": "无限制", "limit_bps": 0, "size": 102400},
        {"name": "5 KB/s", "limit_bps": 5120, "size": 51200},    # 下载50KB
        {"name": "10 KB/s", "limit_bps": 10240, "size": 102400},  # 下载100KB
        {"name": "20 KB/s", "limit_bps": 20480, "size": 102400},
        {"name": "50 KB/s", "limit_bps": 51200, "size": 204800},  # 下载200KB
        {"name": "100 KB/s", "limit_bps": 102400, "size": 512000}, # 下载500KB
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{'='*70}")
        print(f"测试: {test_case['name']} (限速 {test_case['limit_bps']/1024:.1f} KB/s)")
        print(f"{'='*70}")
        
        # 设置限速并重启
        set_limit_and_restart(user_id, test_case['limit_bps'])
        
        # 测试速度
        avg_speed, median_speed = test_speed_multiple(
            username, password, test_case['size'], count=5
        )
        
        results.append({
            'name': test_case['name'],
            'limit_bps': test_case['limit_bps'],
            'limit_kbps': test_case['limit_bps'] / 1024,
            'avg_speed_kbps': avg_speed / 1024,
            'median_speed_kbps': median_speed / 1024
        })
    
    # 打印汇总
    print(f"\n{'='*70}")
    print("限速测试汇总报告")
    print(f"{'='*70}")
    print(f"{'测试项':<15} {'设定(KB/s)':<15} {'实际平均(KB/s)':<20} {'实际中位数(KB/s)':<20} {'准确度':<10}")
    print(f"{'-'*70}")
    
    for r in results:
        if r['limit_bps'] == 0:
            accuracy = "N/A"
        else:
            ratio = r['median_speed_kbps'] / r['limit_kbps']
            accuracy = f"{ratio:.1f}x"
        
        print(f"{r['name']:<15} {r['limit_kbps']:<15.1f} {r['avg_speed_kbps']:<20.2f} {r['median_speed_kbps']:<20.2f} {accuracy:<10}")
    
    print(f"\n{'='*70}")
    
    # 分析准确性
    print("准确性分析:")
    print(f"{'-'*70}")
    for r in results:
        if r['limit_bps'] > 0:
            ratio = r['median_speed_kbps'] / r['limit_kbps']
            if 0.8 <= ratio <= 1.2:
                status = "✓ 良好"
            elif 0.5 <= ratio <= 2.0:
                status = "⚠ 可接受"
            else:
                status = "✗ 偏差大"
            
            print(f"{r['name']:<15} 设定={r['limit_kbps']:.1f}, 实际={r['median_speed_kbps']:.2f}, {status}")
    
    print(f"{'='*70}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被中断")

