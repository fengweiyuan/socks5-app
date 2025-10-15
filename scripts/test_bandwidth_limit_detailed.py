#!/usr/bin/env python3
"""
带宽限制详细测试脚本
测试用户 fwy1988 的 50B/s 带宽限制是否生效
使用更长的超时时间和更详细的测量
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
TEST_PASSWORD = '%VirWorkSocks!'  # 超级密码

# MySQL配置
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db'
}

# 测试目标
TEST_TARGET_HOST = 'httpbin.org'
TEST_TARGET_PORT = 80

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
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}[INFO]{Colors.END} {text}")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {text}")

def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.END} {text}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}[ERROR]{Colors.END} {text}")

def check_user_bandwidth_limit():
    """检查用户的带宽限制设置"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询用户信息
        cursor.execute("SELECT * FROM users WHERE username = %s", (TEST_USERNAME,))
        user = cursor.fetchone()
        
        if not user:
            return None, None
        
        # 查询带宽限制表
        cursor.execute("SELECT * FROM bandwidth_limits WHERE user_id = %s", (user['id'],))
        limit_record = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if limit_record and limit_record['enabled']:
            return user['id'], limit_record['limit']
        elif user['bandwidth_limit'] > 0:
            return user['id'], user['bandwidth_limit']
        
        return user['id'], None
        
    except Exception as e:
        print_error(f"数据库查询失败: {e}")
        return None, None

def socks5_connect(username, password, target_host, target_port):
    """通过SOCKS5代理建立连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(60)  # 延长超时时间到60秒
        
        sock.connect((SOCKS5_HOST, SOCKS5_PORT))
        
        # 认证方法协商
        auth_methods = struct.pack('BBB', 0x05, 0x01, 0x02)
        sock.sendall(auth_methods)
        
        response = sock.recv(2)
        if len(response) != 2 or struct.unpack('BB', response)[1] != 0x02:
            raise Exception("认证方法协商失败")
        
        # 发送用户名密码
        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')
        auth_request = struct.pack('B', 0x01)
        auth_request += struct.pack('B', len(username_bytes)) + username_bytes
        auth_request += struct.pack('B', len(password_bytes)) + password_bytes
        sock.sendall(auth_request)
        
        auth_response = sock.recv(2)
        if len(auth_response) != 2 or struct.unpack('BB', auth_response)[1] != 0x00:
            raise Exception("认证失败")
        
        # 发送连接请求
        connect_request = struct.pack('BBBB', 0x05, 0x01, 0x00, 0x03)
        connect_request += struct.pack('B', len(target_host)) + target_host.encode('utf-8')
        connect_request += struct.pack('!H', target_port)
        sock.sendall(connect_request)
        
        response = sock.recv(4)
        if len(response) != 4 or struct.unpack('BBBB', response)[1] != 0x00:
            raise Exception("连接请求失败")
        
        # 读取剩余响应
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

def test_bandwidth_multiple_requests(user_id, expected_limit):
    """测试多次请求的带宽限制"""
    print_header("带宽限制详细测试")
    
    test_results = []
    
    # 测试5次小请求
    print_info("执行 5 次小数据传输测试（每次约 500 字节）\n")
    
    for i in range(5):
        print(f"{Colors.CYAN}测试 #{i+1}{Colors.END}")
        
        sock = socks5_connect(TEST_USERNAME, TEST_PASSWORD, TEST_TARGET_HOST, TEST_TARGET_PORT)
        if not sock:
            print_error(f"测试 #{i+1} 连接失败")
            continue
        
        try:
            # 请求较小的数据
            http_request = (
                f"GET /bytes/500 HTTP/1.1\r\n"
                f"Host: {TEST_TARGET_HOST}\r\n"
                f"Connection: close\r\n"
                f"User-Agent: BandwidthTest/1.0\r\n"
                f"\r\n"
            )
            
            sock.sendall(http_request.encode('utf-8'))
            
            total_bytes = 0
            start_time = time.time()
            
            while True:
                try:
                    sock.settimeout(20)  # 20秒超时
                    data = sock.recv(512)  # 使用较小的缓冲区
                    if not data:
                        break
                    total_bytes += len(data)
                except socket.timeout:
                    break
            
            end_time = time.time()
            elapsed = end_time - start_time
            speed = total_bytes / elapsed if elapsed > 0 else 0
            
            test_results.append({
                'test_num': i + 1,
                'bytes': total_bytes,
                'time': elapsed,
                'speed': speed
            })
            
            # 判断速度是否在限制范围内
            if expected_limit:
                within_limit = speed <= expected_limit * 1.3  # 允许30%误差
                color = Colors.GREEN if within_limit else Colors.RED
            else:
                color = Colors.YELLOW
            
            print(f"  接收字节: {total_bytes:>6} | 耗时: {elapsed:>6.2f}s | 速度: {color}{speed:>6.2f} B/s{Colors.END} | 限制: {expected_limit} B/s")
            
        finally:
            sock.close()
        
        # 等待1秒再进行下一次测试
        if i < 4:
            time.sleep(1)
    
    # 统计结果
    print_header("测试结果统计")
    
    if len(test_results) == 0:
        print_error("所有测试都失败了")
        return False
    
    total_bytes = sum(r['bytes'] for r in test_results)
    total_time = sum(r['time'] for r in test_results)
    avg_speed = sum(r['speed'] for r in test_results) / len(test_results)
    max_speed = max(r['speed'] for r in test_results)
    min_speed = min(r['speed'] for r in test_results)
    
    print_info(f"成功测试次数: {len(test_results)}/5")
    print_info(f"总传输字节: {total_bytes} bytes")
    print_info(f"总传输时间: {total_time:.2f} 秒")
    print_info(f"平均速度: {avg_speed:.2f} B/s")
    print_info(f"最大速度: {max_speed:.2f} B/s")
    print_info(f"最小速度: {min_speed:.2f} B/s")
    
    if expected_limit:
        print_info(f"\n预期限速: {expected_limit} B/s")
        
        # 评估限速效果
        tolerance = 0.3  # 30% 容差
        upper_bound = expected_limit * (1 + tolerance)
        
        if avg_speed <= upper_bound:
            print_success(f"\n✓ 限速功能正常工作！")
            print_success(f"  平均速度 {avg_speed:.2f} B/s 在限制范围内")
            print_success(f"  速度控制率: {(avg_speed / expected_limit * 100):.1f}%")
            return True
        else:
            print_error(f"\n✗ 限速可能未生效")
            print_error(f"  平均速度 {avg_speed:.2f} B/s 超过限制上限 {upper_bound:.2f} B/s")
            return False
    
    return True

def main():
    """主函数"""
    print_header("SOCKS5 带宽限制详细测试工具")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"测试用户: {TEST_USERNAME}")
    print_info(f"代理地址: {SOCKS5_HOST}:{SOCKS5_PORT}")
    
    # 检查数据库中的带宽限制
    user_id, expected_limit = check_user_bandwidth_limit()
    
    if user_id is None:
        print_error(f"\n无法找到用户 {TEST_USERNAME}")
        return 1
    
    if expected_limit is None:
        print_warning(f"\n用户 {TEST_USERNAME} 未设置带宽限制")
        return 1
    
    print_success(f"\n用户ID: {user_id}, 带宽限制: {expected_limit} B/s")
    
    # 执行测试
    success = test_bandwidth_multiple_requests(user_id, expected_limit)
    
    return 0 if success else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

