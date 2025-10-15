#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速诊断SOCKS5代理问题
"""

import requests
import time
import socks
import socket
import concurrent.futures

# SOCKS5代理配置
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1082
PROXY_USER = 'admin'
PROXY_PASS = '%VirWorkSocks!'

# 减少超时时间加快测试
TIMEOUT = 5

test_cases = [
    {'url': 'http://www.sina.com.cn', 'description': '新浪(HTTP)'},
    {'url': 'https://www.sina.com.cn', 'description': '新浪(HTTPS)'},
    {'url': 'http://www.baidu.com', 'description': '百度(HTTP)'},
    {'url': 'http://httpbin.org/get', 'description': 'HTTPBin(HTTP)'},
    {'url': 'https://httpbin.org/get', 'description': 'HTTPBin(HTTPS)'},
]

def setup_socks5_proxy():
    """配置SOCKS5代理"""
    socks.set_default_proxy(
        socks.SOCKS5,
        PROXY_HOST,
        PROXY_PORT,
        username=PROXY_USER,
        password=PROXY_PASS
    )
    socket.socket = socks.socksocket

def test_single(url, description):
    """测试单个URL"""
    print(f"\n测试: {description} - {url}")
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        elapsed = time.time() - start_time
        
        print(f"  ✓ 成功 | 状态码:{response.status_code} | 时间:{elapsed:.2f}s | 长度:{len(response.content)}字节")
        if response.history:
            print(f"  重定向: {' -> '.join([str(h.status_code) for h in response.history])} -> {response.status_code}")
        return True, elapsed, None
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"  ✗ 超时 ({elapsed:.2f}s)")
        return False, elapsed, 'timeout'
        
    except requests.exceptions.ProxyError as e:
        elapsed = time.time() - start_time
        print(f"  ✗ 代理错误 ({elapsed:.2f}s): {str(e)[:50]}")
        return False, elapsed, 'proxy_error'
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ✗ {type(e).__name__} ({elapsed:.2f}s): {str(e)[:50]}")
        return False, elapsed, type(e).__name__

def main():
    print("="*70)
    print("快速诊断SOCKS5代理")
    print("="*70)
    
    setup_socks5_proxy()
    print(f"代理: {PROXY_HOST}:{PROXY_PORT} | 超时: {TIMEOUT}秒\n")
    
    results = []
    for test in test_cases:
        success, elapsed, error = test_single(test['url'], test['description'])
        results.append({
            'desc': test['description'],
            'url': test['url'],
            'success': success,
            'elapsed': elapsed,
            'error': error
        })
        time.sleep(1)
    
    # 总结
    print(f"\n{'='*70}")
    print("测试总结")
    print(f"{'='*70}")
    success_count = sum(1 for r in results if r['success'])
    print(f"成功: {success_count}/{len(results)}")
    
    if success_count < len(results):
        print("\n失败的请求:")
        for r in results:
            if not r['success']:
                print(f"  ✗ {r['desc']}: {r['error']} ({r['elapsed']:.1f}s)")
    
    # 分析
    timeout_count = sum(1 for r in results if r['error'] == 'timeout')
    if timeout_count > 0:
        print(f"\n⚠️ 发现{timeout_count}个超时，可能原因:")
        print("  1. 代理服务器处理慢")
        print("  2. 目标网站响应慢")
        print("  3. 网络连接问题")
        print("  4. 代理配置的超时时间太短")

if __name__ == '__main__':
    main()

