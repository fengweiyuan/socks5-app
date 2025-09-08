#!/usr/bin/env python3
"""
持续流量生成脚本 - 专门用于测试流量统计功能
"""

import socket
import socks
import requests
import time
import random
from datetime import datetime

def generate_continuous_traffic(username='testuser', password='testpass', duration=300):
    """持续生成流量"""
    print(f"🚀 开始持续流量生成")
    print(f"用户: {username}")
    print(f"持续时间: {duration} 秒")
    print("按 Ctrl+C 停止")
    print("-" * 50)
    
    # 设置带认证的代理
    socks.set_default_proxy(socks.SOCKS5, 'localhost', 1082, username=username, password=password)
    socket.socket = socks.socksocket
    
    # 测试网站列表
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
                print(f"📡 [{request_count + 1:3d}] {url}")
                
                response = requests.get(url, timeout=15)
                request_count += 1
                
                if response.status_code == 200:
                    success_count += 1
                    total_bytes += len(response.content)
                    print(f"    ✅ 成功: {len(response.content):,} 字节")
                else:
                    print(f"    ⚠️  状态码: {response.status_code}")
                
                # 随机间隔 1-3 秒
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                request_count += 1
                print(f"    ❌ 失败: {str(e)}")
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
    
    print(f"\n🌐 请在 Web 管理界面查看流量统计:")
    print(f"   http://localhost:8012")
    print(f"   登录后进入「流量管理」页面")

def main():
    print("🚀 SOCKS5 代理持续流量生成器")
    print("=" * 50)
    
    # 获取参数
    username = input("用户名 (默认: testuser): ").strip() or "testuser"
    password = input("密码 (默认: testpass): ").strip() or "testpass"
    
    try:
        duration = int(input("持续时间(秒，默认300): ") or "300")
    except ValueError:
        print("❌ 无效的输入，使用默认值 300 秒")
        duration = 300
    
    print(f"\n开始生成流量...")
    time.sleep(2)
    
    # 开始生成流量
    generate_continuous_traffic(username, password, duration)

if __name__ == '__main__':
    main()
