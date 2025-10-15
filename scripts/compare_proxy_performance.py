#!/usr/bin/env python3
"""
对比使用和不使用SOCKS5代理的性能差异
使用本地HTTP服务器消除网络延迟影响
"""

import time
import threading
import requests
import statistics
import sys

# 配置
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
PROXY_USER = "fwy1014"
PROXY_PASS = "fwy1014"
LOCAL_SERVER = "http://127.0.0.1:8888/test"

class TestMetrics:
    def __init__(self, name):
        self.name = name
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
        self.lock = threading.Lock()
    
    def add_success(self, response_time):
        with self.lock:
            self.success_count += 1
            self.response_times.append(response_time)
    
    def add_error(self):
        with self.lock:
            self.error_count += 1
    
    def print_report(self, total_time):
        print(f"\n{'='*60}")
        print(f"测试结果: {self.name}")
        print(f"{'='*60}")
        print(f"总耗时: {total_time:.2f}s")
        print(f"成功请求: {self.success_count}")
        print(f"失败请求: {self.error_count}")
        print(f"成功率: {self.success_count/(self.success_count+self.error_count)*100:.1f}%")
        
        if self.response_times:
            sorted_times = sorted(self.response_times)
            print(f"\n响应时间统计:")
            print(f"  平均值: {statistics.mean(self.response_times)*1000:.2f}ms")
            print(f"  中位数: {statistics.median(self.response_times)*1000:.2f}ms")
            print(f"  最小值: {min(self.response_times)*1000:.2f}ms")
            print(f"  最大值: {max(self.response_times)*1000:.2f}ms")
            print(f"  P90: {sorted_times[int(len(sorted_times)*0.9)]*1000:.2f}ms")
            print(f"  P95: {sorted_times[int(len(sorted_times)*0.95)]*1000:.2f}ms")
            print(f"  P99: {sorted_times[int(len(sorted_times)*0.99)]*1000:.2f}ms")
            print(f"  标准差: {statistics.stdev(self.response_times)*1000:.2f}ms")
        
        if total_time > 0:
            qps = self.success_count / total_time
            print(f"\nQPS: {qps:.2f}")
            print(f"平均TPS: {self.success_count/total_time:.2f}")

def test_without_proxy(num_requests, num_threads):
    """测试不使用代理"""
    print(f"\n{'='*60}")
    print(f"测试1: 不使用代理 ({num_requests}请求, {num_threads}线程)")
    print(f"{'='*60}")
    
    metrics = TestMetrics("不使用代理")
    
    def worker():
        session = requests.Session()
        requests_per_thread = num_requests // num_threads
        
        for _ in range(requests_per_thread):
            try:
                start = time.time()
                response = session.get(LOCAL_SERVER, timeout=5)
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    metrics.add_success(elapsed)
                else:
                    metrics.add_error()
            except:
                metrics.add_error()
    
    start_time = time.time()
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    metrics.print_report(total_time)
    
    return metrics

def test_with_proxy(num_requests, num_threads):
    """测试使用SOCKS5代理"""
    print(f"\n{'='*60}")
    print(f"测试2: 使用SOCKS5代理 ({num_requests}请求, {num_threads}线程)")
    print(f"{'='*60}")
    print(f"代理用户: {PROXY_USER}")
    
    metrics = TestMetrics("使用SOCKS5代理")
    
    def worker():
        session = requests.Session()
        session.proxies = {
            'http': f'socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
        }
        requests_per_thread = num_requests // num_threads
        
        for _ in range(requests_per_thread):
            try:
                start = time.time()
                response = session.get(LOCAL_SERVER, timeout=5)
                elapsed = time.time() - start
                
                if response.status_code == 200:
                    metrics.add_success(elapsed)
                else:
                    metrics.add_error()
            except:
                metrics.add_error()
    
    start_time = time.time()
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    metrics.print_report(total_time)
    
    return metrics

def compare_results(no_proxy_metrics, with_proxy_metrics):
    """对比结果"""
    print(f"\n{'='*60}")
    print(f"性能对比总结")
    print(f"{'='*60}")
    
    no_proxy_times = no_proxy_metrics.response_times
    with_proxy_times = with_proxy_metrics.response_times
    
    if no_proxy_times and with_proxy_times:
        no_proxy_avg = statistics.mean(no_proxy_times) * 1000
        with_proxy_avg = statistics.mean(with_proxy_times) * 1000
        
        overhead = with_proxy_avg - no_proxy_avg
        overhead_pct = (overhead / no_proxy_avg) * 100
        
        print(f"\n平均响应时间:")
        print(f"  不使用代理: {no_proxy_avg:.2f}ms")
        print(f"  使用代理: {with_proxy_avg:.2f}ms")
        print(f"  代理开销: {overhead:.2f}ms ({overhead_pct:.1f}%)")
        
        no_proxy_p95 = sorted(no_proxy_times)[int(len(no_proxy_times)*0.95)] * 1000
        with_proxy_p95 = sorted(with_proxy_times)[int(len(with_proxy_times)*0.95)] * 1000
        
        print(f"\nP95响应时间:")
        print(f"  不使用代理: {no_proxy_p95:.2f}ms")
        print(f"  使用代理: {with_proxy_p95:.2f}ms")
        print(f"  代理开销: {with_proxy_p95 - no_proxy_p95:.2f}ms")
        
        # QPS对比
        # 使用实际的成功请求数和总时间计算
        print(f"\n吞吐量对比:")
        print(f"  不使用代理: {no_proxy_metrics.success_count} 请求")
        print(f"  使用代理: {with_proxy_metrics.success_count} 请求")
        
        if no_proxy_avg > 0:
            slowdown = with_proxy_avg / no_proxy_avg
            print(f"\n性能比率:")
            print(f"  代理相对性能: {(1/slowdown)*100:.1f}%")
            print(f"  性能降低: {(slowdown-1)*100:.1f}%")

def check_local_server():
    """检查本地服务器是否运行"""
    try:
        response = requests.get(LOCAL_SERVER, timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print("="*60)
    print("SOCKS5代理性能对比测试")
    print("="*60)
    print(f"\n配置:")
    print(f"  代理地址: {PROXY_HOST}:{PROXY_PORT}")
    print(f"  测试用户: {PROXY_USER}")
    print(f"  测试服务器: {LOCAL_SERVER}")
    
    # 检查本地HTTP服务器
    if not check_local_server():
        print(f"\n✗ 错误: 本地HTTP服务器未运行！")
        print(f"请先运行: python3 scripts/simple_http_test_server.py")
        sys.exit(1)
    
    print(f"✓ 本地HTTP服务器运行正常")
    
    # 运行测试
    print(f"\n开始测试...")
    
    # 测试1: 少量请求
    print(f"\n{'#'*60}")
    print(f"# 测试场景1: 1000请求, 10并发")
    print(f"{'#'*60}")
    no_proxy_1 = test_without_proxy(1000, 10)
    with_proxy_1 = test_with_proxy(1000, 10)
    compare_results(no_proxy_1, with_proxy_1)
    
    # 测试2: 大量请求
    print(f"\n{'#'*60}")
    print(f"# 测试场景2: 5000请求, 20并发")
    print(f"{'#'*60}")
    no_proxy_2 = test_without_proxy(5000, 20)
    with_proxy_2 = test_with_proxy(5000, 20)
    compare_results(no_proxy_2, with_proxy_2)
    
    # 测试3: 高并发
    print(f"\n{'#'*60}")
    print(f"# 测试场景3: 10000请求, 50并发")
    print(f"{'#'*60}")
    no_proxy_3 = test_without_proxy(10000, 50)
    with_proxy_3 = test_with_proxy(10000, 50)
    compare_results(no_proxy_3, with_proxy_3)
    
    print(f"\n{'='*60}")
    print("所有测试完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(0)

