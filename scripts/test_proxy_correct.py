#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确的SOCKS5代理测试方式
使用requests的proxies参数而不是全局socket替换
"""

import requests
import time
from datetime import datetime

# SOCKS5代理配置
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1082
PROXY_USER = 'admin'
PROXY_PASS = '%VirWorkSocks!'

# 构建代理字符串
proxies = {
    'http': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    'https': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
}

test_urls = [
    'http://httpbin.org/get',
    'https://httpbin.org/get',
    'http://www.baidu.com',
    'https://www.baidu.com',
    'http://www.sina.com.cn',
    'https://www.sina.com.cn',
    'http://example.com',
]

def test_url(url, timeout=15):
    """测试单个URL"""
    print(f"\n测试: {url}")
    start_time = time.time()
    
    try:
        response = requests.get(
            url, 
            proxies=proxies, 
            timeout=timeout,
            allow_redirects=True
        )
        elapsed = time.time() - start_time
        
        print(f"  ✓ 成功 | 状态码:{response.status_code} | "
              f"时间:{elapsed:.2f}s | 大小:{len(response.content)}字节")
        
        if response.history:
            redirects = ' -> '.join([f"{h.status_code}" for h in response.history])
            print(f"  重定向: {redirects} -> {response.status_code}")
            print(f"  最终URL: {response.url}")
        
        return True, elapsed
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"  ✗ 超时 ({elapsed:.2f}s)")
        return False, elapsed
        
    except requests.exceptions.ProxyError as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + '...'
        print(f"  ✗ 代理错误 ({elapsed:.2f}s)")
        print(f"     {error_msg}")
        return False, elapsed
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + '...'
        print(f"  ✗ {type(e).__name__} ({elapsed:.2f}s)")
        print(f"     {error_msg}")
        return False, elapsed

def main():
    print("="*70)
    print("SOCKS5代理测试（正确方法）")
    print("="*70)
    print(f"代理: {PROXY_HOST}:{PROXY_PORT}")
    print(f"超时: 15秒")
    
    results = []
    for url in test_urls:
        success, elapsed = test_url(url)
        results.append({
            'url': url,
            'success': success,
            'elapsed': elapsed
        })
        time.sleep(2)
    
    # 统计
    print(f"\n{'='*70}")
    print("测试结果")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n总体: {success_count}/{len(results)} 成功")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        avg_time = sum(r['elapsed'] for r in successful) / len(successful)
        print(f"\n成功请求平均时间: {avg_time:.2f}秒")
        print("成功的URL:")
        for r in successful:
            print(f"  ✓ {r['url']} ({r['elapsed']:.2f}s)")
    
    if failed:
        print(f"\n失败的URL:")
        for r in failed:
            print(f"  ✗ {r['url']} ({r['elapsed']:.2f}s)")
    
    # 结论
    print(f"\n{'='*70}")
    if success_count == len(results):
        print("✅ 代理完全正常！")
    elif success_count >= len(results) * 0.8:
        print("⚠️  代理基本正常，但有少量失败")
    elif success_count > 0:
        print("⚠️  代理不稳定，成功率较低")
    else:
        print("❌ 代理无法正常工作")

if __name__ == '__main__':
    main()

