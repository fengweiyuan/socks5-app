#!/usr/bin/env python3
"""
SOCKS5代理真实性能测试
使用本地HTTP服务器，排除网络延迟影响
"""

import time
import threading
import requests
import statistics
from collections import defaultdict

# 配置
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
PROXY_USER = "admin"
PROXY_PASS = "%VirWorkSocks!"
LOCAL_SERVER = "http://127.0.0.1:8888/test"

class PerformanceMetrics:
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
        self.errors = defaultdict(int)
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None
    
    def add_success(self, response_time):
        with self.lock:
            self.success_count += 1
            self.response_times.append(response_time)
    
    def add_error(self, error_type):
        with self.lock:
            self.error_count += 1
            self.errors[error_type] += 1
    
    def get_stats(self):
        with self.lock:
            return {
                'success': self.success_count,
                'errors': self.error_count,
                'error_types': dict(self.errors),
                'response_times': self.response_times.copy()
            }

def test_without_proxy(num_requests=1000):
    """测试不使用代理的性能（基准）"""
    print("\n" + "="*60)
    print(f"基准测试：不使用代理 ({num_requests}个请求)")
    print("="*60)
    
    metrics = PerformanceMetrics()
    
    def worker():
        session = requests.Session()
        for _ in range(num_requests // 10):  # 10个线程，每个处理1/10
            try:
                start = time.time()
                response = session.get(LOCAL_SERVER, timeout=5)
                elapsed = time.time() - start
                if response.status_code == 200:
                    metrics.add_success(elapsed)
                else:
                    metrics.add_error(f"HTTP_{response.status_code}")
            except Exception as e:
                metrics.add_error(type(e).__name__)
    
    start_time = time.time()
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    stats = metrics.get_stats()
    
    print(f"\n✓ 测试完成")
    print(f"  - 总耗时: {total_time:.2f}s")
    print(f"  - 成功请求: {stats['success']}")
    print(f"  - 失败请求: {stats['errors']}")
    if stats['response_times']:
        print(f"  - 平均响应: {statistics.mean(stats['response_times'])*1000:.2f}ms")
        print(f"  - 中位数: {statistics.median(stats['response_times'])*1000:.2f}ms")
        print(f"  - 最小: {min(stats['response_times'])*1000:.2f}ms")
        print(f"  - 最大: {max(stats['response_times'])*1000:.2f}ms")
        print(f"  - P95: {sorted(stats['response_times'])[int(len(stats['response_times'])*0.95)]*1000:.2f}ms")
        print(f"  - P99: {sorted(stats['response_times'])[int(len(stats['response_times'])*0.99)]*1000:.2f}ms")
    
    qps = stats['success'] / total_time
    print(f"  - QPS: {qps:.2f}")
    
    return qps

def test_with_proxy(num_requests=1000, num_threads=10):
    """测试使用代理的性能"""
    print("\n" + "="*60)
    print(f"代理测试：通过SOCKS5代理 ({num_requests}个请求, {num_threads}线程)")
    print("="*60)
    
    metrics = PerformanceMetrics()
    
    def worker():
        session = requests.Session()
        session.proxies = {
            'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
        }
        
        for _ in range(num_requests // num_threads):
            try:
                start = time.time()
                response = session.get(LOCAL_SERVER, timeout=5)
                elapsed = time.time() - start
                if response.status_code == 200:
                    metrics.add_success(elapsed)
                else:
                    metrics.add_error(f"HTTP_{response.status_code}")
            except Exception as e:
                metrics.add_error(type(e).__name__)
    
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
    
    print(f"\n✓ 测试完成")
    print(f"  - 总耗时: {total_time:.2f}s")
    print(f"  - 成功请求: {stats['success']}/{num_requests}")
    print(f"  - 失败请求: {stats['errors']}")
    if stats['errors'] > 0:
        print(f"  - 错误类型: {stats['error_types']}")
    
    if stats['response_times']:
        print(f"  - 平均响应: {statistics.mean(stats['response_times'])*1000:.2f}ms")
        print(f"  - 中位数: {statistics.median(stats['response_times'])*1000:.2f}ms")
        print(f"  - 最小: {min(stats['response_times'])*1000:.2f}ms")
        print(f"  - 最大: {max(stats['response_times'])*1000:.2f}ms")
        print(f"  - P95: {sorted(stats['response_times'])[int(len(stats['response_times'])*0.95)]*1000:.2f}ms")
        print(f"  - P99: {sorted(stats['response_times'])[int(len(stats['response_times'])*0.99)]*1000:.2f}ms")
        print(f"  - 标准差: {statistics.stdev(stats['response_times'])*1000:.2f}ms")
    
    qps = stats['success'] / total_time
    print(f"  - QPS: {qps:.2f}")
    
    return qps

def test_sustained_load(duration=30, num_threads=20):
    """持续负载测试"""
    print("\n" + "="*60)
    print(f"持续负载测试：{duration}秒 ({num_threads}并发)")
    print("="*60)
    
    metrics = PerformanceMetrics()
    stop_flag = threading.Event()
    
    def worker():
        session = requests.Session()
        session.proxies = {
            'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
        }
        
        while not stop_flag.is_set():
            try:
                start = time.time()
                response = session.get(LOCAL_SERVER, timeout=5)
                elapsed = time.time() - start
                if response.status_code == 200:
                    metrics.add_success(elapsed)
                else:
                    metrics.add_error(f"HTTP_{response.status_code}")
            except Exception as e:
                metrics.add_error(type(e).__name__)
    
    # 启动线程
    start_time = time.time()
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    # 定期报告
    last_report = start_time
    last_count = 0
    
    try:
        while time.time() - start_time < duration:
            time.sleep(5)
            current_time = time.time()
            stats = metrics.get_stats()
            current_count = stats['success']
            interval_qps = (current_count - last_count) / (current_time - last_report)
            print(f"  [{int(current_time - start_time)}s] 成功: {current_count}, 错误: {stats['errors']}, 当前QPS: {interval_qps:.2f}")
            last_report = current_time
            last_count = current_count
    except KeyboardInterrupt:
        print("\n  测试被中断")
    
    stop_flag.set()
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    stats = metrics.get_stats()
    
    print(f"\n✓ 持续测试完成")
    print(f"  - 实际运行: {total_time:.2f}s")
    print(f"  - 总成功: {stats['success']}")
    print(f"  - 总失败: {stats['errors']}")
    print(f"  - 平均QPS: {stats['success']/total_time:.2f}")
    
    if stats['response_times']:
        print(f"  - 平均响应: {statistics.mean(stats['response_times'])*1000:.2f}ms")
        print(f"  - P95响应: {sorted(stats['response_times'])[int(len(stats['response_times'])*0.95)]*1000:.2f}ms")
        print(f"  - P99响应: {sorted(stats['response_times'])[int(len(stats['response_times'])*0.99)]*1000:.2f}ms")

def check_local_server():
    """检查本地服务器是否运行"""
    try:
        response = requests.get(LOCAL_SERVER, timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print("="*60)
    print("SOCKS5代理真实性能测试")
    print("="*60)
    print(f"\n代理配置: {PROXY_HOST}:{PROXY_PORT}")
    print(f"测试服务器: {LOCAL_SERVER}")
    
    # 检查本地HTTP服务器
    if not check_local_server():
        print("\n⚠️  错误: 本地HTTP服务器未运行！")
        print("请先运行: python3 scripts/simple_http_test_server.py")
        return
    
    print("✓ 本地HTTP服务器运行正常\n")
    
    try:
        # 测试1：基准测试（不使用代理）
        baseline_qps = test_without_proxy(num_requests=1000)
        
        # 测试2：使用代理（少量请求）
        print("\n" + "-"*60)
        proxy_qps_small = test_with_proxy(num_requests=1000, num_threads=10)
        
        # 测试3：使用代理（大量请求）
        print("\n" + "-"*60)
        proxy_qps_large = test_with_proxy(num_requests=5000, num_threads=20)
        
        # 测试4：持续负载
        print("\n" + "-"*60)
        user_input = input("\n是否运行30秒持续负载测试? (y/N): ")
        if user_input.lower() == 'y':
            test_sustained_load(duration=30, num_threads=20)
        
        # 总结
        print("\n" + "="*60)
        print("性能测试总结")
        print("="*60)
        print(f"\n基准QPS（无代理）: {baseline_qps:.2f}")
        print(f"代理QPS（1000请求）: {proxy_qps_small:.2f}")
        print(f"代理QPS（5000请求）: {proxy_qps_large:.2f}")
        
        if baseline_qps > 0:
            overhead = (1 - proxy_qps_large / baseline_qps) * 100
            print(f"\n代理开销: {overhead:.1f}%")
            print(f"代理效率: {(proxy_qps_large / baseline_qps * 100):.1f}%")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()

