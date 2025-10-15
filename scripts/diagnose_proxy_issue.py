#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断SOCKS5代理问题
"""

import requests
import time
import socks
import socket
from datetime import datetime

# SOCKS5代理配置
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1082
PROXY_USER = 'admin'
PROXY_PASS = '%VirWorkSocks!'

# 测试用例
test_cases = [
    {'url': 'http://www.baidu.com', 'description': '百度(HTTP)'},
    {'url': 'https://www.baidu.com', 'description': '百度(HTTPS)'},
    {'url': 'http://www.taobao.com', 'description': '淘宝(HTTP)'},
    {'url': 'https://www.taobao.com', 'description': '淘宝(HTTPS)'},
    {'url': 'http://www.sina.com.cn', 'description': '新浪(HTTP)'},
    {'url': 'https://www.sina.com.cn', 'description': '新浪(HTTPS)'},
    {'url': 'http://httpbin.org/get', 'description': 'HTTPBin(HTTP)'},
    {'url': 'https://httpbin.org/get', 'description': 'HTTPBin(HTTPS)'},
    {'url': 'http://example.com', 'description': 'Example(HTTP)'},
    {'url': 'https://example.com', 'description': 'Example(HTTPS)'},
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

def test_with_proxy(url, description, timeout=10):
    """通过代理测试"""
    print(f"\n{'='*70}")
    print(f"测试: {description}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    start_time = time.time()
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed = time.time() - start_time
        
        print(f"✓ 成功")
        print(f"  状态码: {response.status_code}")
        print(f"  响应时间: {elapsed:.2f}秒")
        print(f"  最终URL: {response.url}")
        print(f"  内容长度: {len(response.content)} 字节")
        if response.history:
            print(f"  重定向历史: {len(response.history)}次")
            for i, hist in enumerate(response.history):
                print(f"    {i+1}. {hist.status_code} -> {hist.headers.get('Location', 'N/A')}")
        return True
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"✗ 超时 (耗时: {elapsed:.2f}秒)")
        return False
        
    except requests.exceptions.ProxyError as e:
        elapsed = time.time() - start_time
        print(f"✗ 代理错误 (耗时: {elapsed:.2f}秒)")
        print(f"  错误: {str(e)}")
        return False
        
    except requests.exceptions.SSLError as e:
        elapsed = time.time() - start_time
        print(f"✗ SSL错误 (耗时: {elapsed:.2f}秒)")
        print(f"  错误: {str(e)}")
        return False
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"✗ 其他错误 (耗时: {elapsed:.2f}秒)")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误: {str(e)}")
        return False

def test_dns_resolution():
    """测试DNS解析"""
    print(f"\n{'='*70}")
    print("测试DNS解析速度")
    print(f"{'='*70}")
    
    domains = ['www.baidu.com', 'www.taobao.com', 'www.sina.com.cn', 'httpbin.org']
    
    for domain in domains:
        try:
            start = time.time()
            ip = socket.gethostbyname(domain)
            elapsed = time.time() - start
            print(f"  {domain}: {ip} ({elapsed*1000:.1f}ms)")
        except Exception as e:
            print(f"  {domain}: 解析失败 - {e}")

def main():
    print("="*70)
    print("SOCKS5代理问题诊断工具")
    print("="*70)
    
    # 先测试DNS解析
    test_dns_resolution()
    
    print(f"\n配置SOCKS5代理: {PROXY_HOST}:{PROXY_PORT}")
    setup_socks5_proxy()
    
    results = []
    for test_case in test_cases:
        result = test_with_proxy(test_case['url'], test_case['description'])
        results.append({
            'description': test_case['description'],
            'url': test_case['url'],
            'success': result
        })
        time.sleep(2)  # 每次测试间隔2秒
    
    # 总结
    print(f"\n{'='*70}")
    print("测试总结")
    print(f"{'='*70}")
    
    http_results = [r for r in results if 'HTTP)' in r['description']]
    https_results = [r for r in results if 'HTTPS)' in r['description']]
    
    http_success = sum(1 for r in http_results if r['success'])
    https_success = sum(1 for r in https_results if r['success'])
    
    print(f"\nHTTP测试: {http_success}/{len(http_results)} 成功")
    for r in http_results:
        status = '✓' if r['success'] else '✗'
        print(f"  {status} {r['description']}")
    
    print(f"\nHTTPS测试: {https_success}/{len(https_results)} 成功")
    for r in https_results:
        status = '✓' if r['success'] else '✗'
        print(f"  {status} {r['description']}")
    
    print(f"\n总体成功率: {sum(1 for r in results if r['success'])}/{len(results)}")
    
    print("\n可能的问题：")
    if http_success < len(http_results):
        print("- HTTP请求失败较多，可能是URL过滤或目标网站重定向问题")
    if https_success < len(https_results):
        print("- HTTPS请求失败较多，可能是SSL处理或CONNECT方法问题")
    if http_success == 0 and https_success == 0:
        print("- 所有请求都失败，可能是代理服务器连接问题或认证问题")

if __name__ == '__main__':
    main()

