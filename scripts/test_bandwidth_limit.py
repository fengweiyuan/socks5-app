#!/usr/bin/env python3
"""
带宽限制测试脚本
测试用户 fwy1988 的 50B/s 带宽限制是否生效
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
TEST_PASSWORD = 'password'  # 需要从数据库获取实际密码

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
    print_header("检查数据库中的带宽限制设置")
    
    try:
        # 连接数据库
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 查询用户信息
        cursor.execute("SELECT * FROM users WHERE username = %s", (TEST_USERNAME,))
        user = cursor.fetchone()
        
        if not user:
            print_error(f"用户 {TEST_USERNAME} 不存在")
            return None
        
        print_info(f"用户ID: {user['id']}")
        print_info(f"用户名: {user['username']}")
        print_info(f"状态: {user['status']}")
        print_info(f"用户表中的带宽限制: {user['bandwidth_limit']} B/s")
        
        # 查询带宽限制表
        cursor.execute("SELECT * FROM bandwidth_limits WHERE user_id = %s", (user['id'],))
        limit_record = cursor.fetchone()
        
        if limit_record:
            print_info(f"\n带宽限制表记录:")
            print_info(f"  限制ID: {limit_record['id']}")
            print_info(f"  用户ID: {limit_record['user_id']}")
            print_info(f"  限制值: {limit_record['limit']} B/s")
            print_info(f"  是否启用: {limit_record['enabled']}")
            print_info(f"  更新时间: {limit_record['updated_at']}")
            
            if limit_record['enabled']:
                print_success(f"✓ 带宽限制已启用: {limit_record['limit']} B/s")
                cursor.close()
                conn.close()
                return limit_record['limit']
            else:
                print_warning("⚠ 带宽限制已设置但未启用")
        else:
            print_warning(f"⚠ 未找到用户的带宽限制记录")
            if user['bandwidth_limit'] > 0:
                print_info(f"将使用用户表中的带宽限制: {user['bandwidth_limit']} B/s")
                cursor.close()
                conn.close()
                return user['bandwidth_limit']
        
        cursor.close()
        conn.close()
        return None
        
    except Exception as e:
        print_error(f"数据库查询失败: {e}")
        return None

def socks5_connect(username, password, target_host, target_port):
    """通过SOCKS5代理建立连接"""
    print_header("建立SOCKS5代理连接")
    
    try:
        # 创建socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        
        print_info(f"连接到SOCKS5代理 {SOCKS5_HOST}:{SOCKS5_PORT}")
        sock.connect((SOCKS5_HOST, SOCKS5_PORT))
        
        # 1. 发送认证方法协商
        # VER(1) + NMETHODS(1) + METHODS(1-255)
        auth_methods = struct.pack('BBB', 0x05, 0x01, 0x02)  # SOCKS5, 1个方法, 用户名密码认证
        sock.sendall(auth_methods)
        
        # 接收服务器选择的认证方法
        response = sock.recv(2)
        if len(response) != 2:
            raise Exception("认证方法协商失败")
        
        version, method = struct.unpack('BB', response)
        if method != 0x02:
            raise Exception(f"服务器不支持用户名密码认证，返回方法: {method}")
        
        print_info("认证方法协商成功，使用用户名密码认证")
        
        # 2. 发送用户名密码
        # VER(1) + ULEN(1) + UNAME + PLEN(1) + PASSWD
        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')
        auth_request = struct.pack('B', 0x01)  # 认证协议版本
        auth_request += struct.pack('B', len(username_bytes)) + username_bytes
        auth_request += struct.pack('B', len(password_bytes)) + password_bytes
        sock.sendall(auth_request)
        
        # 接收认证结果
        auth_response = sock.recv(2)
        if len(auth_response) != 2:
            raise Exception("认证失败")
        
        auth_version, auth_status = struct.unpack('BB', auth_response)
        if auth_status != 0x00:
            raise Exception(f"认证失败，状态码: {auth_status}")
        
        print_success(f"✓ 用户 {username} 认证成功")
        
        # 3. 发送连接请求
        # VER(1) + CMD(1) + RSV(1) + ATYP(1) + DST.ADDR + DST.PORT
        connect_request = struct.pack('BBBB', 0x05, 0x01, 0x00, 0x03)  # SOCKS5, CONNECT, RSV, DOMAINNAME
        connect_request += struct.pack('B', len(target_host)) + target_host.encode('utf-8')
        connect_request += struct.pack('!H', target_port)
        sock.sendall(connect_request)
        
        # 接收连接响应
        response = sock.recv(4)
        if len(response) != 4:
            raise Exception("连接请求失败")
        
        version, reply, rsv, atyp = struct.unpack('BBBB', response)
        
        if reply != 0x00:
            raise Exception(f"连接被拒绝，状态码: {reply}")
        
        # 根据地址类型读取剩余数据
        if atyp == 0x01:  # IPv4
            sock.recv(6)  # 4字节IP + 2字节端口
        elif atyp == 0x03:  # 域名
            addr_len = struct.unpack('B', sock.recv(1))[0]
            sock.recv(addr_len + 2)  # 域名 + 2字节端口
        elif atyp == 0x04:  # IPv6
            sock.recv(18)  # 16字节IP + 2字节端口
        
        print_success(f"✓ 成功连接到目标 {target_host}:{target_port}")
        return sock
        
    except Exception as e:
        print_error(f"SOCKS5连接失败: {e}")
        if sock:
            sock.close()
        return None

def test_bandwidth_speed(sock, expected_limit):
    """测试实际传输速度"""
    print_header("测试实际传输速度")
    
    try:
        # 发送HTTP请求，获取较大的响应
        http_request = (
            f"GET /bytes/5000 HTTP/1.1\r\n"  # 请求5000字节数据
            f"Host: {TEST_TARGET_HOST}\r\n"
            f"Connection: close\r\n"
            f"User-Agent: BandwidthTest/1.0\r\n"
            f"\r\n"
        )
        
        print_info(f"发送HTTP请求获取 5000 字节数据")
        sock.sendall(http_request.encode('utf-8'))
        
        # 开始接收数据并计算速度
        total_bytes = 0
        start_time = time.time()
        last_report_time = start_time
        
        # 用于存储每秒的速度
        speed_samples = []
        
        print_info("\n开始接收数据...")
        print(f"{Colors.CYAN}{'时间(s)':<10} {'接收字节':<12} {'当前速度(B/s)':<18} {'限制(B/s)':<15}{Colors.END}")
        print(f"{Colors.CYAN}{'-'*60}{Colors.END}")
        
        while True:
            # 设置较小的接收缓冲区以便更精确测量
            try:
                sock.settimeout(5)
                data = sock.recv(1024)
                if not data:
                    break
                
                total_bytes += len(data)
                current_time = time.time()
                
                # 每0.5秒报告一次
                if current_time - last_report_time >= 0.5:
                    elapsed = current_time - start_time
                    current_speed = total_bytes / elapsed if elapsed > 0 else 0
                    speed_samples.append(current_speed)
                    
                    # 判断速度是否在限制范围内
                    if expected_limit:
                        # 允许10%的误差
                        is_limited = current_speed <= expected_limit * 1.2
                        speed_color = Colors.GREEN if is_limited else Colors.RED
                    else:
                        speed_color = Colors.YELLOW
                    
                    print(f"{elapsed:<10.1f} {total_bytes:<12} {speed_color}{current_speed:<18.2f}{Colors.END} {expected_limit if expected_limit else 'N/A':<15}")
                    last_report_time = current_time
                    
            except socket.timeout:
                print_warning("接收数据超时")
                break
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        average_speed = total_bytes / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\n{Colors.CYAN}{'-'*60}{Colors.END}")
        print_info(f"\n传输统计:")
        print_info(f"  总接收字节: {total_bytes} bytes")
        print_info(f"  传输时间: {elapsed_time:.2f} 秒")
        print_info(f"  平均速度: {average_speed:.2f} B/s")
        
        if len(speed_samples) > 0:
            max_speed = max(speed_samples)
            min_speed = min(speed_samples)
            print_info(f"  最大速度: {max_speed:.2f} B/s")
            print_info(f"  最小速度: {min_speed:.2f} B/s")
        
        # 评估限速效果
        if expected_limit:
            print_header("限速效果评估")
            
            # 允许20%的误差范围（因为网络延迟、测量误差等）
            tolerance = 0.2
            upper_bound = expected_limit * (1 + tolerance)
            lower_bound = expected_limit * (1 - tolerance)
            
            print_info(f"预期限速: {expected_limit} B/s")
            print_info(f"实际平均速度: {average_speed:.2f} B/s")
            print_info(f"速度比率: {(average_speed / expected_limit * 100):.1f}%")
            
            if average_speed <= upper_bound:
                if average_speed >= lower_bound:
                    print_success(f"\n✓ 限速效果良好！实际速度在预期范围内")
                    print_success(f"  预期: {expected_limit} B/s ± {tolerance*100}%")
                    print_success(f"  实际: {average_speed:.2f} B/s")
                    return True
                else:
                    print_warning(f"\n⚠ 限速过于严格！实际速度低于预期下限")
                    print_warning(f"  预期下限: {lower_bound:.2f} B/s")
                    print_warning(f"  实际速度: {average_speed:.2f} B/s")
                    return True  # 虽然过于严格，但限速确实生效了
            else:
                print_error(f"\n✗ 限速未生效！实际速度超过预期上限")
                print_error(f"  预期上限: {upper_bound:.2f} B/s")
                print_error(f"  实际速度: {average_speed:.2f} B/s")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"速度测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print_header(f"SOCKS5 带宽限制测试工具")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"测试用户: {TEST_USERNAME}")
    print_info(f"代理地址: {SOCKS5_HOST}:{SOCKS5_PORT}")
    
    # 1. 检查数据库中的带宽限制
    expected_limit = check_user_bandwidth_limit()
    
    if expected_limit is None:
        print_warning("\n未找到有效的带宽限制设置，将继续测试但无法评估限速效果")
    
    # 获取用户密码
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT password FROM users WHERE username = %s", (TEST_USERNAME,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            print_error(f"无法获取用户 {TEST_USERNAME} 的密码")
            return 1
        
        # 注意：密码在数据库中可能是加密的，这里假设是明文或使用超级密码
        # 如果数据库中是加密密码，应该使用超级密码 "%VirWorkSocks!"
        TEST_PASSWORD = "%VirWorkSocks!"  # 使用超级密码
        
    except Exception as e:
        print_error(f"获取用户密码失败: {e}")
        return 1
    
    # 2. 建立SOCKS5连接
    sock = socks5_connect(TEST_USERNAME, TEST_PASSWORD, TEST_TARGET_HOST, TEST_TARGET_PORT)
    
    if not sock:
        print_error("\n测试失败：无法建立SOCKS5连接")
        return 1
    
    # 3. 测试传输速度
    try:
        success = test_bandwidth_speed(sock, expected_limit)
        
        if success:
            print_header("测试结论")
            if expected_limit:
                print_success(f"✓ 带宽限制测试完成，限速功能工作正常")
            else:
                print_success(f"✓ 数据传输测试完成")
            return 0
        else:
            print_header("测试结论")
            print_error(f"✗ 带宽限制未生效，请检查配置")
            return 1
            
    finally:
        if sock:
            sock.close()
            print_info("\n连接已关闭")

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
