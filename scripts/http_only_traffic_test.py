#!/usr/bin/env python3
"""
仅 HTTP 流量的 SOCKS5 代理测试脚本
"""

import socket
import socks
import requests
import time
import random
from datetime import datetime

def test_http_traffic(username, password, duration=60):
    """测试 HTTP 流量"""
    print(f"🚀 开始 HTTP 流量测试 (用户: {username}, 持续 {duration} 秒)")
    print("按 Ctrl+C 停止")
    
    # 设置带认证的代理
    socks.set_default_proxy(socks.SOCKS5, 'localhost', 1082, username=username, password=password)
    socket.socket = socks.socksocket
    
    # HTTP 测试网站列表
    test_urls = [
        'http://httpbin.org/get',
        'http://httpbin.org/json',
        'http://httpbin.org/uuid',
        'http://httpbin.org/ip',
        'http://httpbin.org/user-agent',
        'http://httpbin.org/headers',
        'http://httpbin.org/bytes/1024',
        'http://httpbin.org/bytes/2048',
        'http://httpbin.org/bytes/4096',
        'http://httpbin.org/bytes/8192',
        'http://httpbin.org/delay/1',
        'http://httpbin.org/delay/2',
    ]
    
    start_time = time.time()
    request_count = 0
    success_count = 0
    total_bytes = 0
    
    try:
        while time.time() - start_time < duration:
            try:
                url = random.choice(test_urls)
                print(f"📡 [{request_count + 1}] 请求: {url}")
                
                response = requests.get(url, timeout=15)
                request_count += 1
                
                if response.status_code == 200:
                    success_count += 1
                    total_bytes += len(response.content)
                    print(f"✅ 成功: {response.status_code} - {len(response.content)} 字节")
                    
                    # 显示特殊信息
                    if 'ip' in url:
                        try:
                            data = response.json()
                            print(f"   代理IP: {data.get('origin', 'N/A')}")
                        except:
                            pass
                    elif 'user-agent' in url:
                        try:
                            data = response.json()
                            print(f"   User-Agent: {data.get('user-agent', 'N/A')}")
                        except:
                            pass
                else:
                    print(f"⚠️  状态码: {response.status_code}")
                
                # 随机间隔 1-3 秒
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                request_count += 1
                print(f"❌ 失败: {str(e)}")
                time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
    
    # 打印统计
    elapsed = time.time() - start_time
    print(f"\n📊 流量统计:")
    print(f"运行时间: {elapsed:.1f} 秒")
    print(f"总请求数: {request_count}")
    print(f"成功请求: {success_count}")
    print(f"成功率: {(success_count/request_count*100):.1f}%" if request_count > 0 else "0%")
    print(f"总接收字节: {total_bytes:,}")
    if elapsed > 0:
        print(f"平均速度: {total_bytes/elapsed:.2f} 字节/秒")
        print(f"平均请求频率: {request_count/elapsed:.2f} 请求/秒")

def main():
    print("🚀 SOCKS5 代理 HTTP 流量测试工具")
    print("=" * 50)
    
    # 获取用户名和密码
    username = input("请输入用户名 (默认: testuser): ").strip() or "testuser"
    password = input("请输入密码 (默认: testpass): ").strip() or "testpass"
    
    print(f"\n使用认证信息: {username} / {'*' * len(password)}")
    
    # 询问持续时间
    try:
        duration = int(input("请输入测试持续时间(秒，默认60): ") or "60")
    except ValueError:
        print("❌ 无效的输入，使用默认值 60 秒")
        duration = 60
    
    print(f"\n开始测试，持续 {duration} 秒...")
    time.sleep(2)
    
    # 开始测试
    test_http_traffic(username, password, duration)

if __name__ == '__main__':
    main()
