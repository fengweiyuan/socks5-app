#!/usr/bin/env python3
"""
简单的 IP 透传测试脚本
"""

import socket
import socks
import requests
import time

def test_ip_forwarding():
    """测试 IP 透传功能"""
    print("开始测试 SOCKS5 代理 IP 透传功能...")
    
    # 设置 SOCKS5 代理
    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1082)
    socket.socket = socks.socksocket
    
    try:
        # 发送 HTTP 请求
        response = requests.get("http://httpbin.org/ip", timeout=10)
        print(f"请求成功，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        # 检查是否返回了真实IP
        if "origin" in response.json():
            origin_ip = response.json()["origin"]
            print(f"检测到的IP地址: {origin_ip}")
            
            # 如果返回的是代理服务器IP而不是真实客户端IP，说明透传可能有问题
            if origin_ip == "127.0.0.1" or origin_ip.startswith("192.168."):
                print("⚠️  警告: 可能返回的是代理服务器IP，而不是真实客户端IP")
            else:
                print("✅ IP透传功能可能正常工作")
        
    except Exception as e:
        print(f"请求失败: {e}")
    finally:
        # 恢复默认 socket
        socks.set_default_proxy()
        socket.socket = socket._socketobject

if __name__ == "__main__":
    test_ip_forwarding()
