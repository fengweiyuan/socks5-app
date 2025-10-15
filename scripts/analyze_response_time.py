#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析代理响应时间，找出瓶颈
"""

import requests
import time
import socket

# SOCKS5代理配置
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1082
PROXY_USER = 'admin'
PROXY_PASS = '%VirWorkSocks!'

proxies = {
    'http': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    'https': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
}

test_urls = [
    'http://www.sina.com.cn',
    'https://www.sina.com.cn',
    'http://www.baidu.com',
    'https://www.baidu.com',
    'http://httpbin.org/get',
    'https://httpbin.org/get',
]

def test_dns_speed(domain):
    """测试DNS解析速度"""
    start = time.time()
    try:
        ip = socket.gethostbyname(domain)
        elapsed = time.time() - start
        return elapsed, ip
    except Exception as e:
        return -1, str(e)

def test_with_proxy(url, timeout=20):
    """通过代理测试，记录详细的时间分解"""
    print(f"\n{'='*70}")
    print(f"测试: {url}")
    print(f"{'='*70}")
    
    # 1. 测试DNS解析
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc
    
    dns_start = time.time()
    dns_time, ip = test_dns_speed(domain)
    if dns_time > 0:
        print(f"1. DNS解析: {dns_time*1000:.1f}ms -> {ip}")
    else:
        print(f"1. DNS解析失败: {ip}")
    
    # 2. 测试通过代理访问
    total_start = time.time()
    
    try:
        response = requests.get(url, proxies=proxies, timeout=timeout, allow_redirects=True)
        total_elapsed = time.time() - total_start
        
        print(f"2. 总响应时间: {total_elapsed:.2f}秒")
        print(f"3. 状态码: {response.status_code}")
        print(f"4. 内容大小: {len(response.content)} 字节")
        
        if response.history:
            print(f"5. 重定向次数: {len(response.history)}")
            for i, hist in enumerate(response.history):
                print(f"   - 重定向{i+1}: {hist.status_code} -> {hist.headers.get('Location', 'N/A')}")
        
        # 分析时间分布
        if total_elapsed > 10:
            print(f"\n⚠️  响应时间较长 ({total_elapsed:.2f}秒)，可能原因:")
            print(f"   - 目标服务器响应慢")
            print(f"   - 网络延迟高")
            if response.history:
                print(f"   - 有{len(response.history)}次重定向增加了时间")
        
        return True, total_elapsed
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - total_start
        print(f"✗ 超时 ({elapsed:.2f}秒)")
        return False, elapsed
        
    except Exception as e:
        elapsed = time.time() - total_start
        print(f"✗ 错误 ({elapsed:.2f}秒): {type(e).__name__}")
        print(f"   {str(e)[:100]}")
        return False, elapsed

def test_direct_vs_proxy(url):
    """对比直接访问和通过代理访问的速度"""
    print(f"\n{'='*70}")
    print(f"对比测试: {url}")
    print(f"{'='*70}")
    
    # 直接访问
    print("\n直接访问（不通过代理）:")
    start = time.time()
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        direct_time = time.time() - start
        print(f"  时间: {direct_time:.2f}秒 | 状态码: {response.status_code}")
    except Exception as e:
        direct_time = -1
        print(f"  失败: {type(e).__name__}")
    
    time.sleep(1)
    
    # 通过代理访问
    print("\n通过SOCKS5代理访问:")
    start = time.time()
    try:
        response = requests.get(url, proxies=proxies, timeout=20, allow_redirects=True)
        proxy_time = time.time() - start
        print(f"  时间: {proxy_time:.2f}秒 | 状态码: {response.status_code}")
        
        if direct_time > 0 and proxy_time > 0:
            overhead = proxy_time - direct_time
            print(f"\n代理开销: {overhead:.2f}秒 ({overhead/proxy_time*100:.1f}%)")
            
    except Exception as e:
        print(f"  失败: {type(e).__name__}")

def main():
    print("="*70)
    print("代理响应时间分析工具")
    print("="*70)
    
    # 测试所有URL
    results = []
    for url in test_urls:
        success, elapsed = test_with_proxy(url)
        results.append({'url': url, 'success': success, 'time': elapsed})
        time.sleep(2)
    
    # 总结
    print(f"\n\n{'='*70}")
    print("响应时间总结")
    print(f"{'='*70}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        print(f"\n成功的请求 ({len(successful)}个):")
        print(f"平均响应时间: {avg_time:.2f}秒")
        
        for r in sorted(successful, key=lambda x: x['time'], reverse=True):
            print(f"  {r['time']:6.2f}s - {r['url']}")
    
    if failed:
        print(f"\n失败的请求 ({len(failed)}个):")
        for r in failed:
            print(f"  ✗ {r['url']}")
    
    # 对比测试（选择一个URL）
    if len(successful) > 0:
        print(f"\n\n{'='*70}")
        print("直接访问 vs 代理访问 对比测试")
        test_direct_vs_proxy('http://httpbin.org/get')

if __name__ == '__main__':
    main()

