#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的响应速度
"""

import requests
import time

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1082
PROXY_USER = 'admin'
PROXY_PASS = '%VirWorkSocks!'

proxies = {
    'http': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    'https': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
}

test_cases = [
    {'url': 'http://www.sina.com.cn', 'name': '新浪(HTTP)'},
    {'url': 'https://www.sina.com.cn', 'name': '新浪(HTTPS)'},
    {'url': 'http://www.baidu.com', 'name': '百度(HTTP)'},
    {'url': 'https://www.baidu.com', 'name': '百度(HTTPS)'},
    {'url': 'http://httpbin.org/get', 'name': 'HTTPBin(HTTP)'},
    {'url': 'https://httpbin.org/get', 'name': 'HTTPBin(HTTPS)'},
]

def test_url(url, name):
    """测试URL并返回结果"""
    start = time.time()
    try:
        response = requests.get(url, proxies=proxies, timeout=15, allow_redirects=True)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"✓ {name:20s} | {elapsed:5.2f}s | {len(response.content):7d} bytes")
            return True, elapsed
        else:
            print(f"✗ {name:20s} | {elapsed:5.2f}s | 状态码: {response.status_code}")
            return False, elapsed
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"✗ {name:20s} | {elapsed:5.2f}s | 超时")
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ {name:20s} | {elapsed:5.2f}s | {type(e).__name__}")
        return False, elapsed

def main():
    print("="*70)
    print("测试修复后的响应速度（已禁用admin的带宽限制）")
    print("="*70)
    print()
    
    results = []
    for test in test_cases:
        success, elapsed = test_url(test['url'], test['name'])
        results.append({'name': test['name'], 'success': success, 'time': elapsed})
        time.sleep(1)
    
    print()
    print("="*70)
    print("总结")
    print("="*70)
    
    successful = [r for r in results if r['success']]
    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        max_time = max(r['time'] for r in successful)
        min_time = min(r['time'] for r in successful)
        
        print(f"成功: {len(successful)}/{len(results)}")
        print(f"平均响应时间: {avg_time:.2f}秒 (之前: 23.82秒)")
        print(f"最快: {min_time:.2f}秒")
        print(f"最慢: {max_time:.2f}秒")
        
        if avg_time < 3:
            print("\n✅ 响应速度非常快！带宽限制已解除。")
        elif avg_time < 10:
            print("\n✅ 响应速度明显改善！")
        else:
            print("\n⚠️  响应速度仍较慢，可能还有其他瓶颈。")

if __name__ == '__main__':
    main()

