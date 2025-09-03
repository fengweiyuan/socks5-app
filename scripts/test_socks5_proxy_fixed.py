#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKS5代理功能测试脚本 (修复版)
测试代理服务器是否能正常处理SOCKS5协议请求和转发流量
支持用户名密码认证
"""

import socket
import struct
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

class Socks5Tester:
    def __init__(self, proxy_host='127.0.0.1', proxy_port=1082, timeout=10, username='testuser', password='testpass'):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.timeout = timeout
        self.username = username
        self.password = password
        self.test_results = []
        
    def test_connection(self):
        """测试基本连接"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.proxy_host, self.proxy_port))
            sock.close()
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {e}"
    
    def authenticate_socks5(self, sock):
        """SOCKS5认证流程"""
        try:
            # 发送支持的认证方法
            sock.send(b'\x05\x02\x00\x02')  # SOCKS5, 2个方法: 无认证 + 用户名密码认证
            
            # 接收服务器响应
            response = sock.recv(2)
            if len(response) < 2:
                return False, "握手响应不完整"
            
            version, method = struct.unpack('!BB', response)
            if version != 5:
                return False, f"不支持的SOCKS版本: {version}"
            
            if method == 0xFF:  # NO_ACCEPTABLE
                return False, "服务器不接受任何认证方法"
            
            # 如果服务器选择用户名密码认证
            if method == 2:  # USER_PASS_AUTH
                # 发送用户名密码
                auth_data = struct.pack('!B', 1)  # 版本1
                auth_data += struct.pack('!B', len(self.username))
                auth_data += self.username.encode()
                auth_data += struct.pack('!B', len(self.password))
                auth_data += self.password.encode()
                
                sock.send(auth_data)
                
                # 接收认证响应
                auth_response = sock.recv(2)
                if len(auth_response) < 2:
                    return False, "认证响应不完整"
                
                auth_version, auth_status = struct.unpack('!BB', auth_response)
                if auth_version != 1:
                    return False, f"认证版本错误: {auth_version}"
                
                if auth_status != 0:
                    return False, f"认证失败: {auth_status}"
                
                return True, "用户名密码认证成功"
            
            return True, "无认证模式"
            
        except Exception as e:
            return False, f"认证失败: {e}"
    
    def test_socks5_handshake(self):
        """测试SOCKS5握手协议"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.proxy_host, self.proxy_port))
            
            # 进行认证
            success, message = self.authenticate_socks5(sock)
            if not success:
                sock.close()
                return False, message
            
            sock.close()
            return True, f"SOCKS5握手成功 ({message})"
            
        except Exception as e:
            return False, f"SOCKS5握手失败: {e}"
    
    def test_socks5_connect(self, target_host='8.8.8.8', target_port=80):
        """测试SOCKS5连接请求"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.proxy_host, self.proxy_port))
            
            # 进行认证
            success, message = self.authenticate_socks5(sock)
            if not success:
                sock.close()
                return False, message
            
            # 发送连接请求
            # 构建请求包: VER(1) + CMD(1) + RSV(1) + ATYP(1) + DST.ADDR + DST.PORT(2)
            request = b'\x05\x01\x00\x01'  # SOCKS5, CONNECT, RSV, IPv4
            
            # 添加目标IP地址
            ip_parts = [int(x) for x in target_host.split('.')]
            request += struct.pack('!BBBB', *ip_parts)
            
            # 添加目标端口
            request += struct.pack('!H', target_port)
            
            sock.send(request)
            
            # 接收响应
            response = sock.recv(10)
            if len(response) < 10:
                sock.close()
                return False, "连接响应不完整"
            
            # 解析响应: VER(1) + REP(1) + RSV(1) + ATYP(1) + BND.ADDR(4) + BND.PORT(2)
            version, reply, rsv, atyp = struct.unpack('!BBBB', response[:4])
            
            if version != 5:
                sock.close()
                return False, f"响应版本错误: {version}"
            
            if reply != 0:
                error_codes = {
                    1: "一般性失败",
                    2: "规则集不允许",
                    3: "网络不可达",
                    4: "主机不可达",
                    5: "连接被拒绝",
                    6: "TTL过期",
                    7: "不支持的命令",
                    8: "不支持的地址类型"
                }
                error_msg = error_codes.get(reply, f"未知错误: {reply}")
                sock.close()
                return False, f"连接失败: {error_msg}"
            
            sock.close()
            return True, f"成功连接到 {target_host}:{target_port}"
            
        except Exception as e:
            return False, f"SOCKS5连接测试失败: {e}"
    
    def test_http_through_proxy(self, target_host='httpbin.org', target_port=80):
        """通过代理测试HTTP请求"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.proxy_host, self.proxy_port))
            
            # 进行认证
            success, message = self.authenticate_socks5(sock)
            if not success:
                sock.close()
                return False, message
            
            # 发送连接请求到目标HTTP服务器
            request = b'\x05\x01\x00\x01'
            
            # 解析域名
            try:
                target_ip = socket.gethostbyname(target_host)
            except:
                target_ip = '8.8.8.8'  # 备用IP
            
            ip_parts = [int(x) for x in target_ip.split('.')]
            request += struct.pack('!BBBB', *ip_parts)
            request += struct.pack('!H', target_port)
            
            sock.send(request)
            
            # 接收响应
            response = sock.recv(10)
            if len(response) < 10:
                sock.close()
                return False, "连接响应不完整"
            
            version, reply, rsv, atyp = struct.unpack('!BBBB', response[:4])
            if version != 5 or reply != 0:
                sock.close()
                return False, "SOCKS5连接失败"
            
            # 发送HTTP GET请求
            http_request = f"GET / HTTP/1.1\r\nHost: {target_host}\r\nConnection: close\r\n\r\n".encode()
            sock.send(http_request)
            
            # 接收HTTP响应
            response_data = b''
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
                    data = sock.recv(1024)
                    if not data:
                        break
                    response_data += data
                    if b'\r\n\r\n' in response_data:  # HTTP头部结束
                        break
                except socket.timeout:
                    break
            
            sock.close()
            
            if response_data:
                # 检查是否包含HTTP响应头
                if b'HTTP/' in response_data[:20]:
                    return True, f"HTTP请求成功，响应长度: {len(response_data)} 字节"
                else:
                    return False, "HTTP响应格式不正确"
            else:
                return False, "未收到HTTP响应"
                
        except Exception as e:
            return False, f"HTTP代理测试失败: {e}"
    
    def test_bandwidth(self, duration=5):
        """测试代理带宽性能"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.proxy_host, self.proxy_port))
            
            # 进行认证
            success, message = self.authenticate_socks5(sock)
            if not success:
                sock.close()
                return False, message
            
            # 连接到测试服务器
            request = b'\x05\x01\x00\x01'
            ip_parts = [8, 8, 8, 8]  # 8.8.8.8
            request += struct.pack('!BBBB', *ip_parts)
            request += struct.pack('!H', 80)
            
            sock.send(request)
            response = sock.recv(10)
            if len(response) < 10:
                sock.close()
                return False, "连接响应不完整"
            
            version, reply, rsv, atyp = struct.unpack('!BBBB', response[:4])
            if version != 5 or reply != 0:
                sock.close()
                return False, "SOCKS5连接失败"
            
            # 发送大量数据测试带宽
            test_data = b'X' * 1024  # 1KB数据
            total_sent = 0
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    sent = sock.send(test_data)
                    total_sent += sent
                    time.sleep(0.01)  # 小延迟避免阻塞
                except:
                    break
            
            sock.close()
            
            elapsed_time = time.time() - start_time
            bandwidth = (total_sent / 1024) / elapsed_time  # KB/s
            
            return True, f"带宽测试完成: {bandwidth:.2f} KB/s ({total_sent} 字节, {elapsed_time:.2f}秒)"
            
        except Exception as e:
            return False, f"带宽测试失败: {e}"
    
    def run_all_tests(self):
        """运行所有测试"""
        print(f"🔍 开始测试SOCKS5代理: {self.proxy_host}:{self.proxy_port}")
        print(f"🔑 认证信息: 用户名={self.username}, 密码={self.password}")
        print("=" * 60)
        
        tests = [
            ("基本连接测试", self.test_connection),
            ("SOCKS5握手测试", self.test_socks5_handshake),
            ("SOCKS5连接测试", self.test_socks5_connect),
            ("HTTP代理测试", self.test_http_through_proxy),
            ("带宽性能测试", self.test_bandwidth)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}...")
            try:
                success, message = test_func()
                status = "✅ 通过" if success else "❌ 失败"
                print(f"   状态: {status}")
                print(f"   结果: {message}")
                self.test_results.append((test_name, success, message))
            except Exception as e:
                print(f"   状态: ❌ 异常")
                print(f"   错误: {e}")
                self.test_results.append((test_name, False, f"异常: {e}"))
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"总测试数: {total}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {total - passed}")
        print(f"成功率: {(passed/total)*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, success, message in self.test_results:
            status = "✅" if success else "❌"
            print(f"  {status} {test_name}: {message}")
        
        if passed == total:
            print(f"\n🎉 所有测试通过！SOCKS5代理工作正常。")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败，请检查代理配置。")

def main():
    parser = argparse.ArgumentParser(description='SOCKS5代理功能测试工具 (修复版)')
    parser.add_argument('--host', default='127.0.0.1', help='代理服务器地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=1082, help='代理服务器端口 (默认: 1082)')
    parser.add_argument('--timeout', type=int, default=10, help='连接超时时间 (默认: 10秒)')
    parser.add_argument('--username', default='testuser', help='认证用户名 (默认: testuser)')
    parser.add_argument('--password', default='testpass', help='认证密码 (默认: testpass)')
    
    args = parser.parse_args()
    
    tester = Socks5Tester(args.host, args.port, args.timeout, args.username, args.password)
    tester.run_all_tests()

if __name__ == '__main__':
    main()
