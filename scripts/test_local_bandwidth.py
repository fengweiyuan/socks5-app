#!/usr/bin/env python3
"""
本地带宽限制测试
使用本地HTTP服务器进行更准确的测试
"""

import socket
import struct
import time
import sys
import pymysql
from datetime import datetime

# 配置
SOCKS5_HOST = '127.0.0.1'
SOCKS5_PORT = 1082
TEST_USERNAME = 'fwy1988'
TEST_PASSWORD = '%VirWorkSocks!'

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

# 本地测试服务器
TEST_HOST = '127.0.0.1'
TEST_PORT = 8888

# 颜色
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_info(text):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {text}")

def print_success(text):
    print(f"{Colors.GREEN}[✓]{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}[✗]{Colors.END} {text}")

def get_bandwidth_limit():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id FROM users WHERE username = %s", (TEST_USERNAME,))
        user = cursor.fetchone()
        if not user:
            return None, None
        cursor.execute("SELECT `limit` FROM bandwidth_limits WHERE user_id = %s AND enabled = 1", (user['id'],))
        limit = cursor.fetchone()
        cursor.close()
        conn.close()
        return user['id'], limit['limit'] if limit else 0
    except Exception as e:
        print_error(f"数据库错误: {e}")
        return None, None

def socks5_connect(target_host, target_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((SOCKS5_HOST, SOCKS5_PORT))
        
        # 认证
        sock.sendall(struct.pack('BBB', 0x05, 0x01, 0x02))
        if struct.unpack('BB', sock.recv(2))[1] != 0x02:
            raise Exception("认证方法失败")
        
        # 用户名密码
        auth = struct.pack('B', 0x01)
        auth += struct.pack('B', len(TEST_USERNAME)) + TEST_USERNAME.encode()
        auth += struct.pack('B', len(TEST_PASSWORD)) + TEST_PASSWORD.encode()
        sock.sendall(auth)
        
        if struct.unpack('BB', sock.recv(2))[1] != 0x00:
            raise Exception("认证失败")
        
        # 连接
        req = struct.pack('BBBB', 0x05, 0x01, 0x00, 0x01)
        req += socket.inet_aton(target_host)
        req += struct.pack('!H', target_port)
        sock.sendall(req)
        
        resp = sock.recv(4)
        if struct.unpack('BBBB', resp)[1] != 0x00:
            raise Exception("连接失败")
        
        # 读取剩余响应
        sock.recv(6)  # IPv4: 4字节IP + 2字节端口
        
        return sock
    except Exception as e:
        print_error(f"SOCKS5连接失败: {e}")
        if 'sock' in locals():
            sock.close()
        return None

def test_bandwidth(data_size, expected_limit):
    """测试指定数据量的带宽"""
    print_header(f"测试传输 {data_size} 字节数据")
    
    sock = socks5_connect(TEST_HOST, TEST_PORT)
    if not sock:
        return None
    
    try:
        # HTTP 请求
        request = (
            f"GET /data/{data_size} HTTP/1.1\r\n"
            f"Host: {TEST_HOST}:{TEST_PORT}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        sock.sendall(request.encode())
        
        # 接收数据
        total_bytes = 0
        start_time = time.time()
        header_done = False
        
        print(f"{Colors.CYAN}时间(s)  接收(B)   速度(B/s)  限制(B/s){Colors.END}")
        print(f"{Colors.CYAN}{'-'*45}{Colors.END}")
        
        last_report = start_time
        
        while True:
            try:
                sock.settimeout(10)
                data = sock.recv(8192)
                if not data:
                    break
                
                # 跳过 HTTP 头
                if not header_done:
                    header_end = data.find(b'\r\n\r\n')
                    if header_end != -1:
                        data = data[header_end + 4:]
                        header_done = True
                    else:
                        continue
                
                total_bytes += len(data)
                current_time = time.time()
                
                # 每0.2秒报告
                if current_time - last_report >= 0.2:
                    elapsed = current_time - start_time
                    speed = total_bytes / elapsed if elapsed > 0 else 0
                    
                    # 检查是否超速
                    if expected_limit > 0:
                        if speed > expected_limit * 1.2:
                            color = Colors.RED
                        else:
                            color = Colors.GREEN
                    else:
                        color = Colors.YELLOW
                    
                    print(f"{elapsed:>6.1f}  {total_bytes:>8}  {color}{speed:>9.1f}{Colors.END}  {expected_limit:>10}")
                    last_report = current_time
                    
            except socket.timeout:
                break
        
        end_time = time.time()
        elapsed = end_time - start_time
        avg_speed = total_bytes / elapsed if elapsed > 0 else 0
        
        print(f"{Colors.CYAN}{'-'*45}{Colors.END}")
        print_info(f"总接收: {total_bytes} bytes")
        print_info(f"耗时: {elapsed:.2f} 秒")
        print_info(f"平均速度: {avg_speed:.2f} B/s")
        
        return {
            'size': data_size,
            'received': total_bytes,
            'time': elapsed,
            'speed': avg_speed
        }
        
    finally:
        sock.close()

def main():
    print_header("本地带宽限制测试")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"测试用户: {TEST_USERNAME}")
    print_info(f"本地服务器: {TEST_HOST}:{TEST_PORT}")
    
    # 获取带宽限制
    user_id, limit = get_bandwidth_limit()
    if user_id is None:
        print_error("无法获取用户信息")
        return 1
    
    print_success(f"用户ID: {user_id}")
    print_success(f"带宽限制: {limit} B/s")
    
    # 测试不同大小的数据
    test_sizes = [50000, 100000, 200000]  # 50KB, 100KB, 200KB
    results = []
    
    for size in test_sizes:
        result = test_bandwidth(size, limit)
        if result:
            results.append(result)
        time.sleep(1)
    
    # 总结
    if results:
        print_header("测试总结")
        
        for i, r in enumerate(results, 1):
            print_info(f"测试 #{i}: {r['size']} 字节 -> 平均速度 {r['speed']:.2f} B/s")
        
        avg_speed = sum(r['speed'] for r in results) / len(results)
        print(f"\n{Colors.BOLD}总体平均速度: {avg_speed:.2f} B/s{Colors.END}")
        print(f"{Colors.BOLD}配置的限制: {limit} B/s{Colors.END}")
        
        if limit > 0:
            ratio = (avg_speed / limit) * 100
            print(f"{Colors.BOLD}速度比率: {ratio:.1f}%{Colors.END}")
            
            if avg_speed <= limit * 1.3:
                print_success(f"\n✓ 限速功能正常！平均速度 {avg_speed:.2f} B/s ≤ 限制 {limit} B/s")
            else:
                print_error(f"\n✗ 可能未正确限速！平均速度 {avg_speed:.2f} B/s > 限制 {limit} B/s")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

