#!/usr/bin/env python3
"""
测试testuser用户的1B/s带宽限制
"""

import socket
import time
import threading
import requests
import json
from datetime import datetime

class BandwidthTest:
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 1082
        self.api_host = "127.0.0.1"
        self.api_port = 8012
        self.testuser_username = "testuser2"
        self.testuser_password = "testpass"
        self.auth_token = None
        
    def login(self):
        """登录获取认证token"""
        try:
            url = f"http://{self.api_host}:{self.api_port}/api/v1/auth/login"
            data = {
                "username": self.testuser_username,
                "password": self.testuser_password
            }
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.auth_token = result.get("token")
                print(f"✅ 登录成功，获取到token: {self.auth_token[:20]}...")
                return True
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def get_traffic_stats(self):
        """获取流量统计"""
        try:
            url = f"http://{self.api_host}:{self.api_port}/api/v1/traffic/realtime"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取流量统计失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 获取流量统计异常: {e}")
            return None
    
    def get_user_limits(self):
        """获取用户带宽限制"""
        try:
            url = f"http://{self.api_host}:{self.api_port}/api/v1/traffic/limits"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取用户限制失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 获取用户限制异常: {e}")
            return None
    
    def test_socks5_connection(self, duration=30):
        """测试SOCKS5连接和流量传输"""
        print(f"\n🚀 开始测试SOCKS5连接，持续{duration}秒...")
        
        # 记录开始时间
        start_time = time.time()
        bytes_sent = 0
        bytes_received = 0
        
        try:
            # 创建SOCKS5连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.proxy_host, self.proxy_port))
            
            print("✅ SOCKS5连接建立成功")
            
            # SOCKS5握手 - 支持用户名密码认证
            # 发送认证方法选择 (SOCKS5, 1个方法, 用户名密码认证)
            sock.send(b'\x05\x01\x02')  # SOCKS5, 1个方法, 用户名密码认证
            response = sock.recv(2)
            if response[0] != 0x05 or response[1] != 0x02:
                print(f"❌ SOCKS5握手失败: {response.hex()}")
                return False
            
            # 发送用户名密码认证
            username = self.testuser_username.encode('utf-8')
            password = self.testuser_password.encode('utf-8')
            
            # 构建认证数据: 版本(1) + 用户名长度 + 用户名 + 密码长度 + 密码
            auth_data = b'\x01' + bytes([len(username)]) + username + bytes([len(password)]) + password
            sock.send(auth_data)
            
            # 接收认证响应
            auth_response = sock.recv(2)
            if auth_response[0] != 0x01 or auth_response[1] != 0x00:
                print(f"❌ SOCKS5认证失败: {auth_response.hex()}")
                return False
            
            print("✅ SOCKS5认证成功")
            
            # 发送连接请求 (连接到www.baidu.com:80)
            target_host = b'www.baidu.com'
            target_port = 80
            request = b'\x05\x01\x00\x03' + bytes([len(target_host)]) + target_host + target_port.to_bytes(2, 'big')
            sock.send(request)
            response = sock.recv(10)
            
            if response[0] != 0x05 or response[1] != 0x00:
                print("❌ SOCKS5连接请求失败")
                return False
            
            print("✅ SOCKS5连接建立成功，开始传输数据...")
            
            # 发送HTTP请求
            http_request = b"GET / HTTP/1.1\r\nHost: www.baidu.com\r\nConnection: close\r\n\r\n"
            sock.send(http_request)
            bytes_sent += len(http_request)
            
            # 接收数据并统计
            while time.time() - start_time < duration:
                try:
                    data = sock.recv(1024)
                    if not data:
                        break
                    bytes_received += len(data)
                    
                    # 每5秒输出一次统计
                    elapsed = time.time() - start_time
                    if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                        speed = bytes_received / elapsed
                        print(f"⏱️  {elapsed:.1f}s - 接收: {bytes_received} bytes, 速度: {speed:.2f} B/s")
                    
                    time.sleep(0.1)  # 短暂延迟
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"❌ 接收数据异常: {e}")
                    break
            
            sock.close()
            
            # 最终统计
            total_time = time.time() - start_time
            avg_speed = bytes_received / total_time if total_time > 0 else 0
            
            print(f"\n📊 测试完成:")
            print(f"   总时间: {total_time:.2f}秒")
            print(f"   发送字节: {bytes_sent}")
            print(f"   接收字节: {bytes_received}")
            print(f"   平均速度: {avg_speed:.2f} B/s")
            
            return True
            
        except Exception as e:
            print(f"❌ SOCKS5连接测试异常: {e}")
            return False
    
    def monitor_traffic_during_test(self, duration=30):
        """在测试期间监控流量统计"""
        print(f"\n📈 开始监控流量统计，持续{duration}秒...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                stats = self.get_traffic_stats()
                if stats:
                    print(f"📊 实时统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
                
                limits = self.get_user_limits()
                if limits:
                    print(f"🔒 用户限制: {json.dumps(limits, indent=2, ensure_ascii=False)}")
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                time.sleep(5)
    
    def run_test(self):
        """运行完整的带宽限制测试"""
        print("=" * 60)
        print("🧪 SOCKS5代理带宽限制测试")
        print("=" * 60)
        
        # 1. 登录
        if not self.login():
            return False
        
        # 2. 获取初始状态
        print("\n📋 获取初始状态...")
        initial_stats = self.get_traffic_stats()
        if initial_stats:
            print(f"初始流量统计: {json.dumps(initial_stats, indent=2, ensure_ascii=False)}")
        
        initial_limits = self.get_user_limits()
        if initial_limits:
            print(f"用户带宽限制: {json.dumps(initial_limits, indent=2, ensure_ascii=False)}")
        
        # 3. 启动监控线程
        monitor_thread = threading.Thread(target=self.monitor_traffic_during_test, args=(35,))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 4. 执行流量测试
        test_success = self.test_socks5_connection(30)
        
        # 5. 等待监控线程结束
        monitor_thread.join(timeout=5)
        
        # 6. 获取最终状态
        print("\n📋 获取最终状态...")
        final_stats = self.get_traffic_stats()
        if final_stats:
            print(f"最终流量统计: {json.dumps(final_stats, indent=2, ensure_ascii=False)}")
        
        final_limits = self.get_user_limits()
        if final_limits:
            print(f"最终用户限制: {json.dumps(final_limits, indent=2, ensure_ascii=False)}")
        
        # 7. 分析结果
        print("\n" + "=" * 60)
        print("📊 测试结果分析")
        print("=" * 60)
        
        if test_success:
            print("✅ SOCKS5连接测试成功")
        else:
            print("❌ SOCKS5连接测试失败")
        
        print("\n💡 说明:")
        print("- 如果1B/s限制生效，您应该看到传输速度被严格限制在1字节/秒左右")
        print("- 如果速度远超过1B/s，说明限制可能没有生效")
        print("- 监控数据会显示实时的流量统计和用户限制信息")
        
        return test_success

if __name__ == "__main__":
    test = BandwidthTest()
    test.run_test()
