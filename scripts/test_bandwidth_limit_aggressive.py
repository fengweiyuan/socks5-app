#!/usr/bin/env python3
"""
激进的带宽限制测试脚本
使用更大的数据量和更快的目标服务器
"""

import socket
import struct
import time
import sys
import pymysql
from datetime import datetime

# 配置信息
SOCKS5_HOST = '127.0.0.1'
SOCKS5_PORT = 1082
TEST_USERNAME = 'fwy1988'
TEST_PASSWORD = '%VirWorkSocks!'

# MySQL配置
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

# 测试目标 - 使用更快的服务器
TEST_TARGETS = [
    ('httpbin.org', 80, '/bytes/10000'),  # 10KB 数据
    ('www.baidu.com', 80, '/'),  # 百度首页
]

# 颜色输出
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
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}[ERROR]{Colors.END} {text}")

def check_bandwidth_limit():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (TEST_USERNAME,))
        user = cursor.fetchone()
        if not user:
            return None, None
        cursor.execute("SELECT * FROM bandwidth_limits WHERE user_id = %s", (user['id'],))
        limit_record = cursor.fetchone()
        cursor.close()
        conn.close()
        if limit_record and limit_record['enabled']:
            return user['id'], limit_record['limit']
        return user['id'], user.get('bandwidth_limit', 0)
    except Exception as e:
        print_error(f"数据库错误: {e}")
        return None, None

def socks5_connect(username, password, target_host, target_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((SOCKS5_HOST, SOCKS5_PORT))
        
        # 认证方法协商
        auth_methods = struct.pack('BBB', 0x05, 0x01, 0x02)
        sock.sendall(auth_methods)
        response = sock.recv(2)
        if len(response) != 2 or struct.unpack('BB', response)[1] != 0x02:
            raise Exception("认证方法协商失败")
        
        # 用户名密码认证
        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')
        auth_request = struct.pack('B', 0x01)
        auth_request += struct.pack('B', len(username_bytes)) + username_bytes
        auth_request += struct.pack('B', len(password_bytes)) + password_bytes
        sock.sendall(auth_request)
        
        auth_response = sock.recv(2)
        if len(auth_response) != 2 or struct.unpack('BB', auth_response)[1] != 0x00:
            raise Exception("认证失败")
        
        # 连接目标
        connect_request = struct.pack('BBBB', 0x05, 0x01, 0x00, 0x03)
        connect_request += struct.pack('B', len(target_host)) + target_host.encode('utf-8')
        connect_request += struct.pack('!H', target_port)
        sock.sendall(connect_request)
        
        response = sock.recv(4)
        if len(response) != 4 or struct.unpack('BBBB', response)[1] != 0x00:
            raise Exception("连接失败")
        
        atyp = struct.unpack('B', response[3:4])[0]
        if atyp == 0x01:
            sock.recv(6)
        elif atyp == 0x03:
            addr_len = struct.unpack('B', sock.recv(1))[0]
            sock.recv(addr_len + 2)
        elif atyp == 0x04:
            sock.recv(18)
        
        return sock
    except Exception as e:
        print_error(f"连接失败: {e}")
        if sock:
            sock.close()
        return None

def test_transfer(host, port, path, expected_limit):
    """测试单次传输"""
    sock = socks5_connect(TEST_USERNAME, TEST_PASSWORD, host, port)
    if not sock:
        return None
    
    try:
        # 发送 HTTP 请求
        http_request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Connection: close\r\n"
            f"User-Agent: BandwidthTest/2.0\r\n"
            f"\r\n"
        )
        
        sock.sendall(http_request.encode('utf-8'))
        
        total_bytes = 0
        start_time = time.time()
        chunk_count = 0
        speed_samples = []
        last_report = start_time
        
        print(f"  {Colors.CYAN}{'时间(s)':<10} {'接收字节':<12} {'瞬时速度(B/s)':<18} {'限制(B/s)':<15}{Colors.END}")
        print(f"  {Colors.CYAN}{'-'*60}{Colors.END}")
        
        while True:
            try:
                sock.settimeout(10)
                data = sock.recv(4096)  # 使用更大的缓冲区
                if not data:
                    break
                
                chunk_count += 1
                total_bytes += len(data)
                current_time = time.time()
                
                # 每0.5秒报告一次
                if current_time - last_report >= 0.5:
                    elapsed = current_time - start_time
                    current_speed = total_bytes / elapsed if elapsed > 0 else 0
                    speed_samples.append(current_speed)
                    
                    # 判断是否在限制范围内
                    if expected_limit and expected_limit > 0:
                        within_limit = current_speed <= expected_limit * 1.3
                        color = Colors.GREEN if within_limit else Colors.RED
                    else:
                        color = Colors.YELLOW
                    
                    print(f"  {elapsed:<10.1f} {total_bytes:<12} {color}{current_speed:<18.2f}{Colors.END} {expected_limit if expected_limit else 'N/A':<15}")
                    last_report = current_time
                    
            except socket.timeout:
                break
        
        end_time = time.time()
        elapsed = end_time - start_time
        avg_speed = total_bytes / elapsed if elapsed > 0 else 0
        
        return {
            'host': host,
            'path': path,
            'bytes': total_bytes,
            'time': elapsed,
            'speed': avg_speed,
            'chunks': chunk_count,
            'samples': speed_samples
        }
        
    finally:
        sock.close()

def main():
    print_header("SOCKS5 带宽限制激进测试")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"测试用户: {TEST_USERNAME}")
    
    # 检查带宽限制
    user_id, expected_limit = check_bandwidth_limit()
    if user_id is None:
        print_error("无法获取用户信息")
        return 1
    
    print_success(f"用户ID: {user_id}, 带宽限制: {expected_limit} B/s")
    
    # 执行测试
    results = []
    
    for host, port, path in TEST_TARGETS:
        print_header(f"测试目标: {host}{path}")
        result = test_transfer(host, port, path, expected_limit)
        
        if result:
            results.append(result)
            print(f"\n  {Colors.CYAN}{'-'*60}{Colors.END}")
            print_info(f"总接收: {result['bytes']} bytes")
            print_info(f"传输时间: {result['time']:.2f} 秒")
            print_info(f"平均速度: {result['speed']:.2f} B/s")
            print_info(f"数据块数: {result['chunks']}")
            
            if result['samples']:
                max_speed = max(result['samples'])
                min_speed = min(result['samples'])
                print_info(f"最大速度: {max_speed:.2f} B/s")
                print_info(f"最小速度: {min_speed:.2f} B/s")
        
        time.sleep(2)  # 每个测试之间等待2秒
    
    # 总结
    if results:
        print_header("测试总结")
        
        total_bytes = sum(r['bytes'] for r in results)
        total_time = sum(r['time'] for r in results)
        avg_speed = sum(r['speed'] for r in results) / len(results)
        
        print_info(f"测试次数: {len(results)}/{len(TEST_TARGETS)}")
        print_info(f"总传输量: {total_bytes} bytes ({total_bytes/1024:.2f} KB)")
        print_info(f"总时间: {total_time:.2f} 秒")
        print_info(f"平均速度: {avg_speed:.2f} B/s")
        
        if expected_limit and expected_limit > 0:
            print_info(f"\n配置的带宽限制: {expected_limit} B/s")
            
            # 评估
            if avg_speed <= expected_limit * 1.3:
                print_success(f"\n✓ 限速生效！平均速度 {avg_speed:.2f} B/s 在限制范围内")
                print_success(f"  速度占限制比例: {(avg_speed / expected_limit * 100):.1f}%")
            else:
                print_warning(f"\n⚠ 平均速度 {avg_speed:.2f} B/s 超过限制 {expected_limit} B/s")
                print_warning(f"  可能的原因：网络延迟、协议开销、或限速未完全生效")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\n\n测试中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

