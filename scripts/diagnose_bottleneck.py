#!/usr/bin/env python3
"""
诊断SOCKS5代理性能瓶颈
"""

import time
import socket
import socks
import requests

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
PROXY_USER = "admin"
PROXY_PASS = "%VirWorkSocks!"
LOCAL_SERVER = "http://127.0.0.1:8888/test"

def test_direct():
    """直接连接测试"""
    print("测试1: 直接HTTP连接")
    times = []
    for i in range(10):
        start = time.time()
        response = requests.get(LOCAL_SERVER, timeout=5)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  请求 {i+1}: {elapsed*1000:.2f}ms")
    
    print(f"  平均: {sum(times)/len(times)*1000:.2f}ms\n")

def test_socks5_connection():
    """测试SOCKS5连接建立"""
    print("测试2: SOCKS5连接建立")
    times = []
    for i in range(10):
        start = time.time()
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, PROXY_USER, PROXY_PASS)
        s.settimeout(5)
        s.connect(("127.0.0.1", 8888))
        elapsed = time.time() - start
        s.close()
        times.append(elapsed)
        print(f"  连接 {i+1}: {elapsed*1000:.2f}ms")
    
    print(f"  平均: {sum(times)/len(times)*1000:.2f}ms\n")

def test_socks5_http():
    """测试通过SOCKS5的HTTP请求"""
    print("测试3: 通过SOCKS5的HTTP请求")
    
    session = requests.Session()
    session.proxies = {
        'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    }
    
    # 第一个请求（可能较慢）
    start = time.time()
    response = session.get(LOCAL_SERVER, timeout=10)
    first_time = time.time() - start
    print(f"  第一个请求: {first_time*1000:.2f}ms")
    
    # 后续请求（复用连接）
    times = []
    for i in range(10):
        start = time.time()
        response = session.get(LOCAL_SERVER, timeout=10)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  请求 {i+1}: {elapsed*1000:.2f}ms")
    
    print(f"  平均（复用连接）: {sum(times)/len(times)*1000:.2f}ms\n")

def test_with_timing_detail():
    """详细计时分析"""
    print("测试4: 详细计时分析")
    
    session = requests.Session()
    session.proxies = {
        'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    }
    
    import time
    
    # 进行一个请求并分析各阶段
    print("  执行单个请求...")
    t0 = time.time()
    
    try:
        response = session.get(LOCAL_SERVER, timeout=10)
        t1 = time.time()
        
        print(f"  总耗时: {(t1-t0)*1000:.2f}ms")
        print(f"  HTTP状态码: {response.status_code}")
        print(f"  响应大小: {len(response.content)} bytes")
    except Exception as e:
        print(f"  错误: {e}")

def main():
    print("="*60)
    print("SOCKS5代理性能瓶颈诊断")
    print("="*60)
    print()
    
    try:
        test_direct()
        test_socks5_connection()
        test_socks5_http()
        test_with_timing_detail()
        
        print("\n" + "="*60)
        print("诊断建议:")
        print("="*60)
        print("1. 如果'直接HTTP连接'很快（<5ms）但'通过SOCKS5'很慢（>100ms）")
        print("   说明代理内部有瓶颈")
        print()
        print("2. 如果'SOCKS5连接建立'就很慢（>50ms）")
        print("   说明认证或连接建立阶段有问题")
        print()
        print("3. 如果每个请求都慢且时间稳定")
        print("   很可能是流量控制或某个固定的sleep/wait")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

