#!/usr/bin/env python3
"""
SOCKS5代理性能综合测试脚本
测试多个方面：连接稳定性、并发性能、数据库负载、流量控制影响
"""

import time
import socket
import socks
import threading
import requests
import statistics
import sys
from collections import defaultdict

# 配置
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
PROXY_USER = "admin"
PROXY_PASS = "%VirWorkSocks!"  # 使用超级密码
TEST_URL = "http://httpbin.org/get"
TEST_DOWNLOAD_URL = "http://httpbin.org/bytes/1048576"  # 1MB数据

class PerformanceMetrics:
    """性能指标收集器"""
    def __init__(self):
        self.connection_times = []
        self.request_times = []
        self.errors = defaultdict(int)
        self.success_count = 0
        self.total_bytes = 0
        self.lock = threading.Lock()
        
    def add_connection_time(self, t):
        with self.lock:
            self.connection_times.append(t)
    
    def add_request_time(self, t):
        with self.lock:
            self.request_times.append(t)
    
    def add_error(self, error_type):
        with self.lock:
            self.errors[error_type] += 1
    
    def add_success(self, bytes_received=0):
        with self.lock:
            self.success_count += 1
            self.total_bytes += bytes_received
    
    def get_stats(self):
        with self.lock:
            return {
                'connection_times': self.connection_times.copy(),
                'request_times': self.request_times.copy(),
                'errors': dict(self.errors),
                'success_count': self.success_count,
                'total_bytes': self.total_bytes
            }

def test_basic_connection():
    """测试1：基础连接测试"""
    print("\n=== 测试1：基础连接测试 ===")
    try:
        start = time.time()
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, PROXY_USER, PROXY_PASS)
        s.connect(("httpbin.org", 80))
        conn_time = time.time() - start
        
        s.send(b"GET /get HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n")
        response = s.recv(4096)
        s.close()
        
        total_time = time.time() - start
        print(f"✓ 连接成功")
        print(f"  - 连接时间: {conn_time*1000:.2f}ms")
        print(f"  - 总时间: {total_time*1000:.2f}ms")
        print(f"  - 响应大小: {len(response)} bytes")
        return True
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

def test_concurrent_connections(num_threads=10, requests_per_thread=10):
    """测试2：并发连接测试"""
    print(f"\n=== 测试2：并发连接测试 ({num_threads}线程 x {requests_per_thread}请求) ===")
    
    metrics = PerformanceMetrics()
    
    def worker():
        session = requests.Session()
        session.proxies = {
            'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
            'https': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
        }
        
        for _ in range(requests_per_thread):
            try:
                start = time.time()
                response = session.get(TEST_URL, timeout=30)
                request_time = time.time() - start
                
                if response.status_code == 200:
                    metrics.add_success(len(response.content))
                    metrics.add_request_time(request_time)
                else:
                    metrics.add_error(f"HTTP_{response.status_code}")
            except requests.exceptions.Timeout:
                metrics.add_error("timeout")
            except requests.exceptions.ProxyError as e:
                metrics.add_error("proxy_error")
            except Exception as e:
                metrics.add_error(f"other: {type(e).__name__}")
    
    start_time = time.time()
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    stats = metrics.get_stats()
    
    print(f"✓ 测试完成")
    print(f"  - 总耗时: {total_time:.2f}s")
    print(f"  - 成功请求: {stats['success_count']}/{num_threads * requests_per_thread}")
    print(f"  - 失败统计: {stats['errors']}")
    
    if stats['request_times']:
        print(f"  - 平均响应时间: {statistics.mean(stats['request_times'])*1000:.2f}ms")
        print(f"  - 中位数响应时间: {statistics.median(stats['request_times'])*1000:.2f}ms")
        print(f"  - 最小响应时间: {min(stats['request_times'])*1000:.2f}ms")
        print(f"  - 最大响应时间: {max(stats['request_times'])*1000:.2f}ms")
        print(f"  - 标准差: {statistics.stdev(stats['request_times'])*1000:.2f}ms")
    
    if total_time > 0:
        qps = stats['success_count'] / total_time
        print(f"  - QPS: {qps:.2f}")
        print(f"  - 吞吐量: {stats['total_bytes']/1024/1024/total_time:.2f} MB/s")
    
    return stats

def test_sustained_load(duration=60, concurrent=5):
    """测试3：持续负载测试"""
    print(f"\n=== 测试3：持续负载测试 ({duration}秒, {concurrent}并发) ===")
    
    metrics = PerformanceMetrics()
    stop_flag = threading.Event()
    
    def worker():
        session = requests.Session()
        session.proxies = {
            'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
            'https': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
        }
        
        while not stop_flag.is_set():
            try:
                start = time.time()
                response = session.get(TEST_URL, timeout=10)
                request_time = time.time() - start
                
                if response.status_code == 200:
                    metrics.add_success(len(response.content))
                    metrics.add_request_time(request_time)
                else:
                    metrics.add_error(f"HTTP_{response.status_code}")
            except Exception as e:
                metrics.add_error(type(e).__name__)
            
            time.sleep(0.1)  # 稍微延迟避免过载
    
    start_time = time.time()
    threads = []
    for _ in range(concurrent):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    # 定期报告
    report_interval = 10
    last_report = time.time()
    last_count = 0
    
    try:
        while time.time() - start_time < duration:
            time.sleep(1)
            current_time = time.time()
            if current_time - last_report >= report_interval:
                stats = metrics.get_stats()
                current_count = stats['success_count']
                interval_qps = (current_count - last_count) / report_interval
                print(f"  [{int(current_time - start_time)}s] 成功: {current_count}, 错误: {sum(stats['errors'].values())}, QPS: {interval_qps:.2f}")
                last_report = current_time
                last_count = current_count
    except KeyboardInterrupt:
        print("\n  用户中断测试")
    
    stop_flag.set()
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    stats = metrics.get_stats()
    
    print(f"\n✓ 持续测试完成")
    print(f"  - 实际运行时间: {total_time:.2f}s")
    print(f"  - 总成功请求: {stats['success_count']}")
    print(f"  - 总失败请求: {sum(stats['errors'].values())}")
    print(f"  - 平均QPS: {stats['success_count']/total_time:.2f}")
    
    if stats['errors']:
        print(f"  - 错误分布: {stats['errors']}")
    
    if stats['request_times']:
        print(f"  - 平均响应时间: {statistics.mean(stats['request_times'])*1000:.2f}ms")
        print(f"  - P95响应时间: {sorted(stats['request_times'])[int(len(stats['request_times'])*0.95)]*1000:.2f}ms")
        print(f"  - P99响应时间: {sorted(stats['request_times'])[int(len(stats['request_times'])*0.99)]*1000:.2f}ms")
    
    return stats

def test_large_file_transfer():
    """测试4：大文件传输测试"""
    print(f"\n=== 测试4：大文件传输测试 ===")
    
    session = requests.Session()
    session.proxies = {
        'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    }
    
    sizes = [1024*1024, 5*1024*1024, 10*1024*1024]  # 1MB, 5MB, 10MB
    
    for size in sizes:
        try:
            print(f"\n  测试下载 {size/1024/1024:.0f}MB 文件...")
            start = time.time()
            response = session.get(f"http://httpbin.org/bytes/{size}", timeout=60)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                actual_size = len(response.content)
                speed = actual_size / elapsed / 1024 / 1024
                print(f"  ✓ 下载成功")
                print(f"    - 实际大小: {actual_size/1024/1024:.2f}MB")
                print(f"    - 耗时: {elapsed:.2f}s")
                print(f"    - 速度: {speed:.2f} MB/s")
            else:
                print(f"  ✗ 下载失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ 下载失败: {e}")

def test_connection_reuse():
    """测试5：连接复用测试"""
    print(f"\n=== 测试5：连接复用测试 ===")
    
    # 测试有连接复用
    session = requests.Session()
    session.proxies = {
        'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    }
    
    print("\n  使用Session（连接复用）：")
    times = []
    for i in range(10):
        start = time.time()
        response = session.get(TEST_URL, timeout=10)
        elapsed = time.time() - start
        times.append(elapsed)
    
    print(f"  - 平均时间: {statistics.mean(times)*1000:.2f}ms")
    print(f"  - 最小时间: {min(times)*1000:.2f}ms")
    print(f"  - 最大时间: {max(times)*1000:.2f}ms")
    
    # 测试无连接复用
    print("\n  不使用Session（每次新连接）：")
    times = []
    for i in range(10):
        start = time.time()
        response = requests.get(TEST_URL, 
            proxies={'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'},
            timeout=10)
        elapsed = time.time() - start
        times.append(elapsed)
    
    print(f"  - 平均时间: {statistics.mean(times)*1000:.2f}ms")
    print(f"  - 最小时间: {min(times)*1000:.2f}ms")
    print(f"  - 最大时间: {max(times)*1000:.2f}ms")

def analyze_bottlenecks():
    """分析性能瓶颈"""
    print("\n" + "="*60)
    print("性能瓶颈分析")
    print("="*60)
    
    print("\n基于代码分析的潜在问题：")
    print("\n1. 数据库写入频繁")
    print("   - logTraffic()在每次数据包转发时都记录日志")
    print("   - 建议：批量写入或异步写入")
    
    print("\n2. 锁竞争问题")
    print("   - 流量控制器的令牌桶算法每次都加锁")
    print("   - 多个goroutine并发时锁竞争严重")
    print("   - 建议：使用原子操作或减少锁粒度")
    
    print("\n3. 流量统计更新频繁")
    print("   - 每5秒更新一次用户统计")
    print("   - 每30秒重新加载带宽限制")
    print("   - 建议：根据实际需求调整更新频率")
    
    print("\n4. HTTP深度检测开销")
    print("   - 当启用时，每个连接的第一个数据包都需要检测")
    print("   - 建议：仅在必要时启用")
    
    print("\n5. URL过滤器查询")
    print("   - 每个连接都查询数据库获取过滤规则")
    print("   - 建议：缓存过滤规则")
    
    print("\n6. 连接超时设置")
    print("   - 读写超时都是60秒")
    print("   - 可能导致大量半开连接")
    print("   - 建议：根据场景调整超时时间")

def main():
    print("="*60)
    print("SOCKS5代理性能综合测试")
    print("="*60)
    print(f"\n代理配置: {PROXY_HOST}:{PROXY_PORT}")
    print(f"用户: {PROXY_USER}")
    print(f"测试URL: {TEST_URL}")
    
    # 检查依赖
    try:
        import socks
        import requests
    except ImportError as e:
        print(f"\n错误: 缺少必要的Python包")
        print(f"请运行: pip3 install requests PySocks")
        sys.exit(1)
    
    # 运行测试
    try:
        # 1. 基础连接测试
        if not test_basic_connection():
            print("\n⚠️  基础连接测试失败，请检查代理服务器是否运行")
            return
        
        # 2. 并发连接测试
        test_concurrent_connections(num_threads=10, requests_per_thread=5)
        
        # 3. 连接复用测试
        test_connection_reuse()
        
        # 4. 大文件传输测试
        test_large_file_transfer()
        
        # 5. 持续负载测试（可选，时间较长）
        user_input = input("\n是否运行60秒持续负载测试? (y/N): ")
        if user_input.lower() == 'y':
            test_sustained_load(duration=60, concurrent=5)
        
        # 6. 分析瓶颈
        analyze_bottlenecks()
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()

