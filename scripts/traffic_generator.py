#!/usr/bin/env python3
"""
SOCKS5 代理流量生成器
用于持续向代理发送流量，测试流量统计功能
"""

import socket
import socks
import requests
import time
import random
import threading
import argparse
import sys
from datetime import datetime
import json

class TrafficGenerator:
    def __init__(self, proxy_host='localhost', proxy_port=1082, username=None, password=None):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.username = username
        self.password = password
        self.running = False
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_bytes_sent': 0,
            'total_bytes_received': 0,
            'start_time': None
        }
        
    def setup_socks_proxy(self):
        """设置 SOCKS5 代理"""
        socks.set_default_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port, 
                               username=self.username, password=self.password)
        socket.socket = socks.socksocket
        
    def generate_http_traffic(self, duration=60, interval=1):
        """生成 HTTP 流量"""
        print(f"🚀 开始生成 HTTP 流量 (持续 {duration} 秒，间隔 {interval} 秒)")
        
        # 测试网站列表
        test_urls = [
            'http://httpbin.org/get',
            'http://httpbin.org/json',
            'http://httpbin.org/uuid',
            'http://httpbin.org/ip',
            'http://httpbin.org/user-agent',
            'http://httpbin.org/headers',
            'http://httpbin.org/bytes/1024',  # 1KB
            'http://httpbin.org/bytes/2048',  # 2KB
            'http://httpbin.org/bytes/4096',  # 4KB
            'http://httpbin.org/bytes/8192',  # 8KB
        ]
        
        start_time = time.time()
        self.stats['start_time'] = datetime.now()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                url = random.choice(test_urls)
                print(f"📡 请求: {url}")
                
                response = requests.get(url, timeout=10)
                
                self.stats['total_requests'] += 1
                self.stats['successful_requests'] += 1
                self.stats['total_bytes_sent'] += len(response.request.body or b'')
                self.stats['total_bytes_received'] += len(response.content)
                
                print(f"✅ 成功: {response.status_code} - 接收 {len(response.content)} 字节")
                
            except Exception as e:
                self.stats['total_requests'] += 1
                self.stats['failed_requests'] += 1
                print(f"❌ 失败: {str(e)}")
            
            time.sleep(interval)
    
    def generate_https_traffic(self, duration=60, interval=2):
        """生成 HTTPS 流量"""
        print(f"🔒 开始生成 HTTPS 流量 (持续 {duration} 秒，间隔 {interval} 秒)")
        
        # HTTPS 测试网站
        test_urls = [
            'https://httpbin.org/get',
            'https://httpbin.org/json',
            'https://httpbin.org/uuid',
            'https://httpbin.org/ip',
            'https://httpbin.org/user-agent',
            'https://httpbin.org/headers',
            'https://httpbin.org/bytes/1024',
            'https://httpbin.org/bytes/2048',
            'https://httpbin.org/bytes/4096',
            'https://httpbin.org/bytes/8192',
            'https://www.google.com',
            'https://www.github.com',
            'https://www.stackoverflow.com',
        ]
        
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                url = random.choice(test_urls)
                print(f"🔐 请求: {url}")
                
                response = requests.get(url, timeout=15)
                
                self.stats['total_requests'] += 1
                self.stats['successful_requests'] += 1
                self.stats['total_bytes_sent'] += len(response.request.body or b'')
                self.stats['total_bytes_received'] += len(response.content)
                
                print(f"✅ 成功: {response.status_code} - 接收 {len(response.content)} 字节")
                
            except Exception as e:
                self.stats['total_requests'] += 1
                self.stats['failed_requests'] += 1
                print(f"❌ 失败: {str(e)}")
            
            time.sleep(interval)
    
    def generate_large_file_traffic(self, duration=60, interval=5):
        """生成大文件下载流量"""
        print(f"📁 开始生成大文件流量 (持续 {duration} 秒，间隔 {interval} 秒)")
        
        # 大文件测试 URL
        large_file_urls = [
            'https://httpbin.org/bytes/1048576',   # 1MB
            'https://httpbin.org/bytes/2097152',   # 2MB
            'https://httpbin.org/bytes/5242880',   # 5MB
            'https://httpbin.org/bytes/10485760',  # 10MB
        ]
        
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                url = random.choice(large_file_urls)
                print(f"📦 下载大文件: {url}")
                
                response = requests.get(url, timeout=30, stream=True)
                
                self.stats['total_requests'] += 1
                self.stats['successful_requests'] += 1
                
                # 计算实际接收的字节数
                received_bytes = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        received_bytes += len(chunk)
                
                self.stats['total_bytes_received'] += received_bytes
                print(f"✅ 成功: 下载 {received_bytes} 字节")
                
            except Exception as e:
                self.stats['total_requests'] += 1
                self.stats['failed_requests'] += 1
                print(f"❌ 失败: {str(e)}")
            
            time.sleep(interval)
    
    def generate_continuous_traffic(self, interval=1):
        """持续生成流量"""
        print(f"🔄 开始持续生成流量 (间隔 {interval} 秒)")
        
        # 混合流量类型
        traffic_types = [
            ('http', self.generate_http_traffic),
            ('https', self.generate_https_traffic),
            ('large', self.generate_large_file_traffic)
        ]
        
        while self.running:
            try:
                traffic_type, generator_func = random.choice(traffic_types)
                duration = random.randint(10, 30)  # 随机持续时间
                
                print(f"🎯 生成 {traffic_type} 流量，持续 {duration} 秒")
                generator_func(duration, interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 流量生成错误: {str(e)}")
                time.sleep(5)
    
    def print_stats(self):
        """打印统计信息"""
        if self.stats['start_time']:
            elapsed = datetime.now() - self.stats['start_time']
            print(f"\n📊 流量统计 (运行时间: {elapsed})")
            print(f"总请求数: {self.stats['total_requests']}")
            print(f"成功请求: {self.stats['successful_requests']}")
            print(f"失败请求: {self.stats['failed_requests']}")
            print(f"总发送字节: {self.stats['total_bytes_sent']:,}")
            print(f"总接收字节: {self.stats['total_bytes_received']:,}")
            
            if self.stats['total_requests'] > 0:
                success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
                print(f"成功率: {success_rate:.1f}%")
            
            if elapsed.total_seconds() > 0:
                avg_speed = self.stats['total_bytes_received'] / elapsed.total_seconds()
                print(f"平均速度: {avg_speed:.2f} 字节/秒")
    
    def start(self, mode='continuous', duration=60, interval=1):
        """启动流量生成器"""
        print("🚀 SOCKS5 代理流量生成器启动")
        print(f"代理地址: {self.proxy_host}:{self.proxy_port}")
        if self.username:
            print(f"认证用户: {self.username}")
        print("-" * 50)
        
        try:
            self.setup_socks_proxy()
            self.running = True
            
            if mode == 'http':
                self.generate_http_traffic(duration, interval)
            elif mode == 'https':
                self.generate_https_traffic(duration, interval)
            elif mode == 'large':
                self.generate_large_file_traffic(duration, interval)
            elif mode == 'continuous':
                self.generate_continuous_traffic(interval)
            else:
                print(f"❌ 未知模式: {mode}")
                return
                
        except KeyboardInterrupt:
            print("\n⏹️  用户中断")
        except Exception as e:
            print(f"❌ 启动失败: {str(e)}")
        finally:
            self.running = False
            self.print_stats()
            print("🏁 流量生成器已停止")

def main():
    parser = argparse.ArgumentParser(description='SOCKS5 代理流量生成器')
    parser.add_argument('--proxy-host', default='localhost', help='代理服务器地址 (默认: localhost)')
    parser.add_argument('--proxy-port', type=int, default=1082, help='代理服务器端口 (默认: 1082)')
    parser.add_argument('--username', help='代理认证用户名')
    parser.add_argument('--password', help='代理认证密码')
    parser.add_argument('--mode', choices=['http', 'https', 'large', 'continuous'], 
                       default='continuous', help='流量生成模式 (默认: continuous)')
    parser.add_argument('--duration', type=int, default=60, help='持续时间(秒) (默认: 60)')
    parser.add_argument('--interval', type=float, default=1, help='请求间隔(秒) (默认: 1)')
    
    args = parser.parse_args()
    
    # 创建流量生成器
    generator = TrafficGenerator(
        proxy_host=args.proxy_host,
        proxy_port=args.proxy_port,
        username=args.username,
        password=args.password
    )
    
    # 启动流量生成
    generator.start(
        mode=args.mode,
        duration=args.duration,
        interval=args.interval
    )

if __name__ == '__main__':
    main()
