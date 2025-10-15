#!/usr/bin/env python3
"""
测试流量日志时区
"""
import requests
import socks
import socket
import time

def test_proxy_traffic():
    """通过代理发送一些测试请求"""
    print("开始测试代理流量...")
    
    # 配置SOCKS5代理
    proxy_host = "127.0.0.1"
    proxy_port = 1082  # 修改为正确的端口
    username = "admin"
    password = "admin"
    
    # 设置SOCKS5代理
    socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port, username=username, password=password)
    socket.socket = socks.socksocket
    
    # 发送多个HTTP请求
    test_urls = [
        "http://www.baidu.com",
        "http://www.google.com",
        "http://www.example.com",
    ]
    
    for i, url in enumerate(test_urls, 1):
        try:
            print(f"[{i}/{len(test_urls)}] 请求: {url}")
            response = requests.get(url, timeout=10)
            print(f"  ✓ 状态码: {response.status_code}, 大小: {len(response.content)} bytes")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ✗ 失败: {e}")
    
    print(f"\n测试完成！已发送 {len(test_urls)} 个请求")

if __name__ == "__main__":
    test_proxy_traffic()

