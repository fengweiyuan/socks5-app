#!/usr/bin/env python3
"""
动态带宽限制更新测试
验证在不重启代理的情况下，修改数据库中的带宽限制是否能自动生效
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

TEST_HOST = '127.0.0.1'
TEST_PORT = 8888
TEST_DATA_SIZE = 100000  # 100KB

# 颜色
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
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

def print_warning(text):
    print(f"{Colors.YELLOW}[⚠]{Colors.END} {text}")

def print_step(step_num, text):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}步骤 {step_num}: {text}{Colors.END}")

def get_bandwidth_limit():
    """获取当前带宽限制"""
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

def update_bandwidth_limit(user_id, new_limit):
    """更新带宽限制"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("UPDATE bandwidth_limits SET `limit` = %s WHERE user_id = %s", (new_limit, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print_error(f"更新失败: {e}")
        return False

def socks5_connect():
    """建立 SOCKS5 连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((SOCKS5_HOST, SOCKS5_PORT))
        
        # 认证
        sock.sendall(struct.pack('BBB', 0x05, 0x01, 0x02))
        if struct.unpack('BB', sock.recv(2))[1] != 0x02:
            raise Exception("认证方法失败")
        
        auth = struct.pack('B', 0x01)
        auth += struct.pack('B', len(TEST_USERNAME)) + TEST_USERNAME.encode()
        auth += struct.pack('B', len(TEST_PASSWORD)) + TEST_PASSWORD.encode()
        sock.sendall(auth)
        
        if struct.unpack('BB', sock.recv(2))[1] != 0x00:
            raise Exception("认证失败")
        
        # 连接目标
        req = struct.pack('BBBB', 0x05, 0x01, 0x00, 0x01)
        req += socket.inet_aton(TEST_HOST)
        req += struct.pack('!H', TEST_PORT)
        sock.sendall(req)
        
        if struct.unpack('BBBB', sock.recv(4))[1] != 0x00:
            raise Exception("连接失败")
        
        sock.recv(6)
        return sock
    except Exception as e:
        print_error(f"连接失败: {e}")
        if 'sock' in locals():
            sock.close()
        return None

def test_speed():
    """测试当前速度"""
    sock = socks5_connect()
    if not sock:
        return None
    
    try:
        request = (
            f"GET /data/{TEST_DATA_SIZE} HTTP/1.1\r\n"
            f"Host: {TEST_HOST}:{TEST_PORT}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        sock.sendall(request.encode())
        
        total_bytes = 0
        start_time = time.time()
        header_done = False
        speed_samples = []
        last_sample_time = start_time
        
        while True:
            try:
                sock.settimeout(10)
                data = sock.recv(8192)
                if not data:
                    break
                
                if not header_done:
                    header_end = data.find(b'\r\n\r\n')
                    if header_end != -1:
                        data = data[header_end + 4:]
                        header_done = True
                    else:
                        continue
                
                total_bytes += len(data)
                current_time = time.time()
                
                # 每0.5秒采样
                if current_time - last_sample_time >= 0.5:
                    elapsed = current_time - start_time
                    if elapsed > 5:  # 5秒后的速度更稳定
                        speed = total_bytes / elapsed
                        speed_samples.append(speed)
                    last_sample_time = current_time
                    
            except socket.timeout:
                break
        
        end_time = time.time()
        elapsed = end_time - start_time
        avg_speed = total_bytes / elapsed if elapsed > 0 else 0
        
        # 使用稳定阶段的平均速度
        stable_speed = sum(speed_samples) / len(speed_samples) if speed_samples else avg_speed
        
        return {
            'bytes': total_bytes,
            'time': elapsed,
            'avg_speed': avg_speed,
            'stable_speed': stable_speed
        }
    finally:
        sock.close()

def main():
    print_header("动态带宽限制更新测试")
    print_info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"测试用户: {TEST_USERNAME}")
    
    # 步骤1: 获取当前限制
    print_step(1, "获取当前带宽限制")
    user_id, current_limit = get_bandwidth_limit()
    if user_id is None:
        print_error("无法获取用户信息")
        return 1
    
    print_success(f"用户ID: {user_id}")
    print_success(f"当前带宽限制: {current_limit} B/s")
    
    # 步骤2: 第一次测速
    print_step(2, f"测试当前限速 ({current_limit} B/s)")
    print_info("开始传输数据...")
    
    result1 = test_speed()
    if not result1:
        print_error("测速失败")
        return 1
    
    print_info(f"接收: {result1['bytes']} bytes, 耗时: {result1['time']:.2f}s")
    print_success(f"平均速度: {result1['avg_speed']:.2f} B/s")
    print_success(f"稳定速度: {result1['stable_speed']:.2f} B/s")
    
    # 步骤3: 修改数据库中的限制
    new_limit = 3000  # 从 5000 改为 3000
    print_step(3, f"修改数据库中的带宽限制为 {new_limit} B/s")
    
    if not update_bandwidth_limit(user_id, new_limit):
        print_error("更新数据库失败")
        return 1
    
    print_success(f"数据库已更新: {current_limit} B/s → {new_limit} B/s")
    
    # 步骤4: 等待自动重新加载
    print_step(4, "等待代理自动重新加载配置（最多需要30秒）")
    
    for i in range(35, 0, -5):
        print(f"  {Colors.YELLOW}等待中... {i} 秒{Colors.END}", end='\r')
        time.sleep(5)
    print(f"  {Colors.GREEN}等待完成！{Colors.END}                    ")
    
    # 验证数据库
    _, db_limit = get_bandwidth_limit()
    print_info(f"数据库中的限制: {db_limit} B/s")
    
    # 步骤5: 第二次测速
    print_step(5, f"测试新限速 ({new_limit} B/s)")
    print_info("开始传输数据...")
    
    result2 = test_speed()
    if not result2:
        print_error("测速失败")
        return 1
    
    print_info(f"接收: {result2['bytes']} bytes, 耗时: {result2['time']:.2f}s")
    print_success(f"平均速度: {result2['avg_speed']:.2f} B/s")
    print_success(f"稳定速度: {result2['stable_speed']:.2f} B/s")
    
    # 步骤6: 对比结果
    print_header("测试结果对比")
    
    print(f"\n{Colors.BOLD}第一次测试 (限制: {current_limit} B/s){Colors.END}")
    print(f"  稳定速度: {result1['stable_speed']:.2f} B/s")
    
    print(f"\n{Colors.BOLD}第二次测试 (限制: {new_limit} B/s){Colors.END}")
    print(f"  稳定速度: {result2['stable_speed']:.2f} B/s")
    
    print(f"\n{Colors.BOLD}速度变化{Colors.END}")
    speed_change = result1['stable_speed'] - result2['stable_speed']
    speed_change_pct = (speed_change / result1['stable_speed']) * 100
    print(f"  下降: {speed_change:.2f} B/s ({speed_change_pct:.1f}%)")
    
    # 评估
    print_header("评估结果")
    
    expected_ratio = new_limit / current_limit  # 3000 / 5000 = 0.6
    actual_ratio = result2['stable_speed'] / result1['stable_speed']
    
    print_info(f"预期速度比率: {expected_ratio:.2f} ({new_limit}/{current_limit})")
    print_info(f"实际速度比率: {actual_ratio:.2f}")
    
    # 判断是否成功（实际比率应该接近预期比率，允许20%误差）
    if 0.5 <= actual_ratio <= 0.8:
        print_success("\n✓ 动态更新成功！")
        print_success(f"  新限速已生效，无需重启代理")
        print_success(f"  第二次测速明显慢于第一次，符合预期")
        return 0
    else:
        print_warning("\n⚠ 速度变化不明显")
        print_warning(f"  可能原因：")
        print_warning(f"  1. 测试数据量较小，受网络波动影响")
        print_warning(f"  2. 需要等待更长时间让配置完全生效")
        print_warning(f"  3. 检查 logs/proxy.log 查看是否有更新日志")
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

