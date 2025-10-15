#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy 性能压力测试

测试场景：
- 模拟 100 个并发用户
- 监控 CPU、内存使用情况
- 记录响应时间、成功率
- 统计性能指标
"""

import requests
import socket
import time
import sys
import socks
import psutil
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import statistics

# 配置
PROXY_HOST = "localhost"
PROXY_PORT = 1082
USERNAME = "admin"
PASSWORD = "admin"
CONCURRENT_USERS = 100  # 并发用户数
REQUESTS_PER_USER = 5   # 每个用户的请求数
TEST_URL = "http://example.com"  # 测试URL

# 性能统计
stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'response_times': [],
    'errors': defaultdict(int),
    'start_time': 0,
    'end_time': 0,
}

# CPU监控数据
cpu_stats = {
    'samples': [],
    'per_core_samples': [],
    'memory_samples': [],
}

# 锁
stats_lock = threading.Lock()
monitor_running = True

def get_proxy_pid():
    """获取proxy进程的PID"""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        for line in result.stdout.split('\n'):
            if 'bin/proxy' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) > 1:
                    return int(parts[1])
        
        return None
    except Exception as e:
        print(f"⚠️  无法获取proxy进程PID: {e}")
        return None

def monitor_proxy_resources(pid, interval=0.5):
    """监控proxy进程的资源使用"""
    global monitor_running, cpu_stats
    
    if pid is None:
        print("⚠️  未找到proxy进程，跳过资源监控")
        return
    
    try:
        process = psutil.Process(pid)
        print(f"✅ 开始监控 proxy 进程 (PID: {pid})")
        
        while monitor_running:
            try:
                # CPU使用率（总体）
                cpu_percent = process.cpu_percent(interval=interval)
                
                # 每个核心的CPU使用率
                cpu_times = process.cpu_times()
                
                # 内存使用
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # MB
                
                # 线程数
                num_threads = process.num_threads()
                
                with stats_lock:
                    cpu_stats['samples'].append({
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_mb,
                        'num_threads': num_threads,
                    })
                
                time.sleep(interval)
                
            except psutil.NoSuchProcess:
                print("⚠️  proxy进程已停止")
                break
            except Exception as e:
                print(f"⚠️  监控错误: {e}")
                time.sleep(interval)
                
    except psutil.NoSuchProcess:
        print(f"❌ 进程 {pid} 不存在")
    except Exception as e:
        print(f"❌ 监控启动失败: {e}")

def make_request(user_id, request_id):
    """单个请求"""
    # 配置SOCKS5代理
    socks.set_default_proxy(
        socks.SOCKS5, 
        PROXY_HOST, 
        PROXY_PORT,
        username=USERNAME, 
        password=PASSWORD
    )
    
    original_socket = socket.socket
    socket.socket = socks.socksocket
    
    start_time = time.time()
    error = None
    status_code = None
    
    try:
        response = requests.get(TEST_URL, timeout=30)
        status_code = response.status_code
        elapsed = time.time() - start_time
        
        with stats_lock:
            stats['successful_requests'] += 1
            stats['response_times'].append(elapsed)
        
        return {
            'user_id': user_id,
            'request_id': request_id,
            'success': True,
            'elapsed': elapsed,
            'status_code': status_code,
            'error': None
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        error = str(e)[:100]
        
        with stats_lock:
            stats['failed_requests'] += 1
            stats['errors'][type(e).__name__] += 1
        
        return {
            'user_id': user_id,
            'request_id': request_id,
            'success': False,
            'elapsed': elapsed,
            'status_code': None,
            'error': error
        }
        
    finally:
        socket.socket = original_socket
        import importlib
        importlib.reload(socket)

def user_simulation(user_id):
    """模拟单个用户的行为"""
    results = []
    
    for i in range(REQUESTS_PER_USER):
        with stats_lock:
            stats['total_requests'] += 1
        
        result = make_request(user_id, i)
        results.append(result)
        
        # 短暂休息，模拟真实用户行为
        time.sleep(0.1)
    
    return results

def print_progress(completed, total):
    """打印进度"""
    percent = (completed / total) * 100
    bar_length = 50
    filled = int(bar_length * completed / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\r  进度: [{bar}] {percent:.1f}% ({completed}/{total})", end='', flush=True)

def run_benchmark():
    """运行压力测试"""
    global monitor_running
    
    print("="*70)
    print("Proxy 性能压力测试")
    print("="*70)
    print(f"配置:")
    print(f"  代理地址: {PROXY_HOST}:{PROXY_PORT}")
    print(f"  并发用户: {CONCURRENT_USERS}")
    print(f"  每用户请求数: {REQUESTS_PER_USER}")
    print(f"  总请求数: {CONCURRENT_USERS * REQUESTS_PER_USER}")
    print(f"  测试URL: {TEST_URL}")
    print("="*70)
    
    # 获取proxy进程PID
    proxy_pid = get_proxy_pid()
    if proxy_pid:
        print(f"✅ 找到 proxy 进程 (PID: {proxy_pid})")
        
        # 获取系统CPU核心数
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        print(f"✅ 系统CPU: {cpu_count} 物理核心, {cpu_count_logical} 逻辑核心")
    else:
        print("⚠️  未找到 proxy 进程，将跳过资源监控")
    
    print("\n开始压力测试...")
    
    # 启动资源监控线程
    monitor_thread = None
    if proxy_pid:
        monitor_thread = threading.Thread(
            target=monitor_proxy_resources, 
            args=(proxy_pid, 0.5),
            daemon=True
        )
        monitor_thread.start()
    
    # 记录开始时间
    stats['start_time'] = time.time()
    
    # 使用线程池执行并发测试
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        # 提交所有用户任务
        futures = {
            executor.submit(user_simulation, user_id): user_id 
            for user_id in range(CONCURRENT_USERS)
        }
        
        # 等待完成并显示进度
        completed = 0
        print_progress(completed, CONCURRENT_USERS)
        
        for future in as_completed(futures):
            completed += 1
            print_progress(completed, CONCURRENT_USERS)
            
            try:
                result = future.result()
            except Exception as e:
                print(f"\n⚠️  用户 {futures[future]} 执行失败: {e}")
    
    print("\n")
    
    # 记录结束时间
    stats['end_time'] = time.time()
    
    # 停止监控
    monitor_running = False
    if monitor_thread:
        monitor_thread.join(timeout=2)
    
    print("✅ 压力测试完成！\n")

def analyze_results():
    """分析测试结果"""
    print("="*70)
    print("测试结果分析")
    print("="*70)
    
    total_time = stats['end_time'] - stats['start_time']
    total_requests = stats['total_requests']
    successful = stats['successful_requests']
    failed = stats['failed_requests']
    
    print(f"\n📊 基本统计:")
    print(f"  总耗时: {total_time:.2f}秒")
    print(f"  总请求数: {total_requests}")
    print(f"  成功: {successful} ({successful/total_requests*100:.1f}%)")
    print(f"  失败: {failed} ({failed/total_requests*100:.1f}%)")
    print(f"  吞吐量: {total_requests/total_time:.2f} 请求/秒")
    
    if stats['response_times']:
        response_times = stats['response_times']
        
        print(f"\n⏱️  响应时间统计:")
        print(f"  平均: {statistics.mean(response_times):.3f}秒")
        print(f"  中位数: {statistics.median(response_times):.3f}秒")
        print(f"  最快: {min(response_times):.3f}秒")
        print(f"  最慢: {max(response_times):.3f}秒")
        
        if len(response_times) > 1:
            print(f"  标准差: {statistics.stdev(response_times):.3f}秒")
        
        # 百分位数
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p90 = sorted_times[int(len(sorted_times) * 0.90)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print(f"\n  百分位数:")
        print(f"    P50: {p50:.3f}秒")
        print(f"    P90: {p90:.3f}秒")
        print(f"    P95: {p95:.3f}秒")
        print(f"    P99: {p99:.3f}秒")
    
    if stats['errors']:
        print(f"\n❌ 错误统计:")
        for error_type, count in stats['errors'].items():
            print(f"  {error_type}: {count}")
    
    # CPU和内存统计
    if cpu_stats['samples']:
        samples = cpu_stats['samples']
        
        cpu_percents = [s['cpu_percent'] for s in samples]
        memory_mbs = [s['memory_mb'] for s in samples]
        thread_counts = [s['num_threads'] for s in samples]
        
        print(f"\n💻 Proxy 进程资源使用:")
        print(f"  CPU 使用率:")
        print(f"    平均: {statistics.mean(cpu_percents):.1f}%")
        print(f"    峰值: {max(cpu_percents):.1f}%")
        print(f"    最低: {min(cpu_percents):.1f}%")
        
        # 估算使用的CPU核心数
        cpu_count = psutil.cpu_count()
        avg_cpu = statistics.mean(cpu_percents)
        cores_used = avg_cpu / 100  # 每100%代表1个核心
        
        print(f"\n  CPU 核心使用:")
        print(f"    系统总核心: {cpu_count} 个")
        print(f"    平均使用: {cores_used:.2f} 个核心")
        print(f"    峰值使用: {max(cpu_percents)/100:.2f} 个核心")
        
        print(f"\n  内存使用:")
        print(f"    平均: {statistics.mean(memory_mbs):.1f} MB")
        print(f"    峰值: {max(memory_mbs):.1f} MB")
        print(f"    最低: {min(memory_mbs):.1f} MB")
        
        print(f"\n  线程数:")
        print(f"    平均: {statistics.mean(thread_counts):.0f}")
        print(f"    峰值: {max(thread_counts)}")
    
    print("\n" + "="*70)

def generate_report():
    """生成测试报告"""
    report_file = "benchmark_report.txt"
    
    with open(report_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("Proxy 性能压力测试报告\n")
        f.write("="*70 + "\n")
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"并发用户: {CONCURRENT_USERS}\n")
        f.write(f"每用户请求数: {REQUESTS_PER_USER}\n")
        f.write(f"总请求数: {CONCURRENT_USERS * REQUESTS_PER_USER}\n")
        f.write("\n")
        
        total_time = stats['end_time'] - stats['start_time']
        total_requests = stats['total_requests']
        successful = stats['successful_requests']
        failed = stats['failed_requests']
        
        f.write("基本统计:\n")
        f.write(f"  总耗时: {total_time:.2f}秒\n")
        f.write(f"  成功: {successful} ({successful/total_requests*100:.1f}%)\n")
        f.write(f"  失败: {failed} ({failed/total_requests*100:.1f}%)\n")
        f.write(f"  吞吐量: {total_requests/total_time:.2f} 请求/秒\n")
        f.write("\n")
        
        if stats['response_times']:
            response_times = stats['response_times']
            f.write("响应时间:\n")
            f.write(f"  平均: {statistics.mean(response_times):.3f}秒\n")
            f.write(f"  中位数: {statistics.median(response_times):.3f}秒\n")
            f.write(f"  最快: {min(response_times):.3f}秒\n")
            f.write(f"  最慢: {max(response_times):.3f}秒\n")
            f.write("\n")
        
        if cpu_stats['samples']:
            samples = cpu_stats['samples']
            cpu_percents = [s['cpu_percent'] for s in samples]
            memory_mbs = [s['memory_mb'] for s in samples]
            
            f.write("资源使用:\n")
            f.write(f"  CPU平均: {statistics.mean(cpu_percents):.1f}%\n")
            f.write(f"  CPU峰值: {max(cpu_percents):.1f}%\n")
            f.write(f"  内存平均: {statistics.mean(memory_mbs):.1f} MB\n")
            f.write(f"  内存峰值: {max(memory_mbs):.1f} MB\n")
        
        f.write("="*70 + "\n")
    
    print(f"\n📄 测试报告已保存: {report_file}")

def main():
    """主函数"""
    # 检查依赖
    try:
        import socks
        print("✅ PySocks库已安装")
    except ImportError:
        print("❌ 请先安装PySocks库: pip3 install PySocks")
        sys.exit(1)
    
    try:
        import psutil
        print("✅ psutil库已安装")
    except ImportError:
        print("❌ 请先安装psutil库: pip3 install psutil")
        sys.exit(1)
    
    print()
    
    # 运行压测
    try:
        run_benchmark()
        analyze_results()
        generate_report()
        
        print("\n✨ 压力测试完成！")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        monitor_running = False
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        monitor_running = False
        sys.exit(1)

if __name__ == "__main__":
    main()

