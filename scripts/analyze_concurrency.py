#!/usr/bin/env python3
"""
分析不同并发级别的性能表现
"""
import time
import threading
import requests
import statistics

PROXY = 'socks5://fwy1014:fwy1014@127.0.0.1:1082'
URL = "http://127.0.0.1:8888/test"

def test_concurrency_level(concurrency, total_requests=1000):
    """测试特定并发级别"""
    results = []
    errors = 0
    
    def worker():
        nonlocal errors
        session = requests.Session()
        session.proxies = {'http': PROXY}
        
        for _ in range(total_requests // concurrency):
            try:
                start = time.time()
                r = session.get(URL, timeout=5)
                elapsed = time.time() - start
                if r.status_code == 200:
                    results.append(elapsed)
                else:
                    errors += 1
            except:
                errors += 1
    
    start_time = time.time()
    threads = []
    for _ in range(concurrency):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    
    if results:
        avg = statistics.mean(results) * 1000
        qps = len(results) / total_time
        return {
            'concurrency': concurrency,
            'total_time': total_time,
            'success': len(results),
            'errors': errors,
            'avg_ms': avg,
            'median_ms': statistics.median(results) * 1000,
            'p95_ms': sorted(results)[int(len(results)*0.95)] * 1000,
            'qps': qps
        }
    return None

def main():
    print("="*70)
    print("并发级别性能分析")
    print("="*70)
    
    concurrency_levels = [1, 2, 5, 10, 20, 30, 50, 100]
    results = []
    
    for level in concurrency_levels:
        print(f"\n测试并发={level}...")
        result = test_concurrency_level(level, 1000)
        if result:
            results.append(result)
            print(f"  成功: {result['success']}, 错误: {result['errors']}")
            print(f"  平均: {result['avg_ms']:.2f}ms, P95: {result['p95_ms']:.2f}ms")
            print(f"  QPS: {result['qps']:.2f}")
    
    # 打印表格
    print(f"\n{'='*70}")
    print("性能汇总表")
    print(f"{'='*70}")
    print(f"{'并发数':<8} {'成功':<8} {'失败':<8} {'平均ms':<12} {'P95ms':<12} {'QPS':<12}")
    print(f"{'-'*70}")
    
    for r in results:
        print(f"{r['concurrency']:<8} {r['success']:<8} {r['errors']:<8} "
              f"{r['avg_ms']:<12.2f} {r['p95_ms']:<12.2f} {r['qps']:<12.2f}")
    
    # 分析QPS趋势
    print(f"\n{'='*70}")
    print("QPS变化趋势:")
    print(f"{'='*70}")
    for i, r in enumerate(results):
        if i == 0:
            change = "基准"
        else:
            prev_qps = results[i-1]['qps']
            change_pct = (r['qps'] - prev_qps) / prev_qps * 100
            change = f"{change_pct:+.1f}%"
        print(f"并发 {r['concurrency']:>3}: QPS {r['qps']:>8.2f}  变化: {change}")

if __name__ == "__main__":
    main()

