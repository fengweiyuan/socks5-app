#!/usr/bin/env python3
"""
简单的 SOCKS5 代理流量测试脚本
用于快速测试代理连接和流量统计
"""

import socket
import socks
import requests
import time
import random
from datetime import datetime

def test_socks5_proxy():
    """测试 SOCKS5 代理连接"""
    print("🔍 测试 SOCKS5 代理连接...")
    
    # 设置代理
    socks.set_default_proxy(socks.SOCKS5, 'localhost', 1082)
    socket.socket = socks.socksocket
    
    # 测试连接
    test_urls = [
        'http://httpbin.org/ip',
        'http://httpbin.org/get',
        'https://httpbin.org/ip',
        'https://httpbin.org/get',
    ]
    
    success_count = 0
    total_bytes = 0
    
    for i, url in enumerate(test_urls, 1):
        try:
            print(f"📡 测试 {i}/{len(test_urls)}: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                success_count += 1
                total_bytes += len(response.content)
                print(f"✅ 成功: {response.status_code} - {len(response.content)} 字节")
            else:
                print(f"⚠️  状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 失败: {str(e)}")
        
        time.sleep(1)
    
    print(f"\n📊 测试结果:")
    print(f"成功请求: {success_count}/{len(test_urls)}")
    print(f"总接收字节: {total_bytes:,}")
    
    return success_count > 0

def generate_continuous_traffic(duration=300):
    """持续生成流量"""
    print(f"🚀 开始持续生成流量 (持续 {duration} 秒)")
    print("按 Ctrl+C 停止")
    
    # 设置代理
    socks.set_default_proxy(socks.SOCKS5, 'localhost', 1082)
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
        'https://httpbin.org/get',
        'https://httpbin.org/json',
        'https://httpbin.org/ip',
        'https://httpbin.org/bytes/1024',
        'https://httpbin.org/bytes/2048',
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
                
                response = requests.get(url, timeout=10)
                request_count += 1
                
                if response.status_code == 200:
                    success_count += 1
                    total_bytes += len(response.content)
                    print(f"✅ 成功: {response.status_code} - {len(response.content)} 字节")
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

def main():
    print("🚀 SOCKS5 代理流量测试工具")
    print("=" * 50)
    
    # 首先测试连接
    if not test_socks5_proxy():
        print("❌ 代理连接测试失败，请检查代理服务是否正常运行")
        return
    
    print("\n" + "=" * 50)
    
    # 询问是否继续生成流量
    try:
        duration = int(input("请输入流量生成持续时间(秒，默认300): ") or "300")
        generate_continuous_traffic(duration)
    except ValueError:
        print("❌ 无效的输入，使用默认值 300 秒")
        generate_continuous_traffic(300)
    except KeyboardInterrupt:
        print("\n👋 再见!")

if __name__ == '__main__':
    main()
