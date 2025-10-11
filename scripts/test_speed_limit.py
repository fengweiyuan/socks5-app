#!/usr/bin/env python3
"""
测试修改后的速度限制功能
"""

import socket
import time
import threading
import requests
import json
from datetime import datetime

class SpeedLimitTest:
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
    
    def set_bandwidth_limit(self, limit_bytes_per_second):
        """设置用户带宽限制"""
        try:
            url = f"http://{self.api_host}:{self.api_port}/api/v1/traffic/limit"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            data = {
                "user_id": 5,  # testuser2的ID
                "limit": limit_bytes_per_second
            }
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ 设置带宽限制成功: {limit_bytes_per_second} 字节/秒")
                return True
            else:
                print(f"❌ 设置带宽限制失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 设置带宽限制异常: {e}")
            return False
    
    def get_bandwidth_limits(self):
        """获取带宽限制信息"""
        try:
            url = f"http://{self.api_host}:{self.api_port}/api/v1/traffic/limits"
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取带宽限制失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 获取带宽限制异常: {e}")
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
            sock.send(b'\x05\x01\x02')  # SOCKS5, 1个方法, 用户名密码认证
            response = sock.recv(2)
            if response[0] != 0x05 or response[1] != 0x02:
                print(f"❌ SOCKS5握手失败: {response.hex()}")
                return False
            
            # 发送用户名密码认证
            username = self.testuser_username.encode('utf-8')
            password = self.testuser_password.encode('utf-8')
            
            auth_data = b'\x01' + bytes([len(username)]) + username + bytes([len(password)]) + password
            sock.send(auth_data)
            
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
                print(f"❌ SOCKS5连接请求失败: {response.hex()}")
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
                    
                    # 每2秒输出一次统计
                    elapsed = time.time() - start_time
                    if int(elapsed) % 2 == 0 and int(elapsed) > 0:
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
    
    def run_speed_test(self, limit_bytes_per_second, test_duration=30):
        """运行速度限制测试"""
        print("=" * 60)
        print(f"🧪 SOCKS5代理速度限制测试 - 限制: {limit_bytes_per_second} B/s")
        print("=" * 60)
        
        # 1. 登录
        if not self.login():
            return False
        
        # 2. 设置带宽限制
        print(f"\n🔧 设置带宽限制为 {limit_bytes_per_second} 字节/秒...")
        if not self.set_bandwidth_limit(limit_bytes_per_second):
            return False
        
        # 3. 获取当前限制信息
        print("\n📋 获取当前带宽限制...")
        limits = self.get_bandwidth_limits()
        if limits:
            print(f"当前带宽限制: {json.dumps(limits, indent=2, ensure_ascii=False)}")
        
        # 4. 等待一下让限制生效
        print("\n⏳ 等待限制生效...")
        time.sleep(2)
        
        # 5. 执行流量测试
        test_success = self.test_socks5_connection(test_duration)
        
        # 6. 分析结果
        print("\n" + "=" * 60)
        print("📊 测试结果分析")
        print("=" * 60)
        
        if test_success:
            print("✅ SOCKS5连接测试成功")
        else:
            print("❌ SOCKS5连接测试失败")
        
        print(f"\n💡 说明:")
        print(f"- 如果{limit_bytes_per_second}B/s限制生效，您应该看到传输速度被严格限制在{limit_bytes_per_second}字节/秒左右")
        print(f"- 如果速度远超过{limit_bytes_per_second}B/s，说明限制可能没有生效")
        print(f"- 这是速度限制，不是总量限制")
        
        return test_success

if __name__ == "__main__":
    test = SpeedLimitTest()
    
    # 测试不同的速度限制
    test_cases = [
        (10, 20),    # 10 B/s, 20秒
        (100, 15),   # 100 B/s, 15秒
        (1000, 10),  # 1000 B/s, 10秒
    ]
    
    for limit, duration in test_cases:
        print(f"\n{'='*80}")
        print(f"测试案例: {limit} B/s 限制，持续 {duration} 秒")
        print(f"{'='*80}")
        
        success = test.run_speed_test(limit, duration)
        
        if not success:
            print(f"❌ 测试案例失败: {limit} B/s")
            break
        
        print(f"✅ 测试案例完成: {limit} B/s")
        
        # 测试间隔
        if limit < 1000:  # 不是最后一个测试
            print("\n⏳ 等待5秒后进行下一个测试...")
            time.sleep(5)
    
    print(f"\n🎉 所有测试完成！")
