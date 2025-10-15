#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKS5代理稳定性测试脚本
持续访问多个网站，检测代理连接的稳定性
"""

import requests
import time
import sys
from datetime import datetime
import socks
import socket
from urllib.parse import urlparse
import traceback

# SOCKS5代理配置
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1082
PROXY_USER = 'admin'     # 使用admin用户
PROXY_PASS = '%VirWorkSocks!'   # 使用超级密码

# 测试配置
TEST_DURATION = 600  # 测试时长（秒），10分钟
REQUEST_INTERVAL = 5  # 每次请求间隔（秒）
REQUEST_TIMEOUT = 10  # 单个请求超时时间（秒）

# 测试网站列表（多样化的网站）
TEST_WEBSITES = [
    'http://www.baidu.com',
    'http://www.qq.com',
    'http://www.sina.com.cn',
    'http://www.163.com',
    'http://www.taobao.com',
    'http://httpbin.org/get',
    'http://example.com',
    'http://www.github.com',
]

# 统计数据
stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'timeouts': 0,
    'connection_errors': 0,
    'proxy_errors': 0,
    'other_errors': 0,
    'errors': [],
    'response_times': [],
    'failed_websites': {}
}


def setup_socks5_proxy():
    """配置SOCKS5代理"""
    # 设置默认的socket使用SOCKS5代理
    socks.set_default_proxy(
        socks.SOCKS5,
        PROXY_HOST,
        PROXY_PORT,
        username=PROXY_USER,
        password=PROXY_PASS
    )
    socket.socket = socks.socksocket
    print(f"✓ 已配置SOCKS5代理: {PROXY_HOST}:{PROXY_PORT}")


def test_single_request(url, request_num):
    """测试单次请求"""
    start_time = time.time()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        print(f"\n[请求 #{request_num}] {timestamp}")
        print(f"  目标: {url}")
        
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            stats['successful_requests'] += 1
            stats['response_times'].append(elapsed)
            print(f"  ✓ 成功 | 状态码: {response.status_code} | "
                  f"响应时间: {elapsed:.2f}秒 | "
                  f"内容长度: {len(response.content)} 字节")
            return True
        else:
            stats['failed_requests'] += 1
            error_msg = f"HTTP状态码错误: {response.status_code}"
            stats['errors'].append({
                'timestamp': timestamp,
                'url': url,
                'error': error_msg,
                'type': 'http_error'
            })
            print(f"  ✗ 失败 | {error_msg}")
            track_failed_website(url)
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['timeouts'] += 1
        error_msg = f"请求超时 (>{REQUEST_TIMEOUT}秒)"
        stats['errors'].append({
            'timestamp': timestamp,
            'url': url,
            'error': error_msg,
            'type': 'timeout',
            'elapsed': elapsed
        })
        print(f"  ✗ 失败 | {error_msg}")
        track_failed_website(url)
        return False
        
    except requests.exceptions.ProxyError as e:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['proxy_errors'] += 1
        error_msg = f"代理错误: {str(e)}"
        stats['errors'].append({
            'timestamp': timestamp,
            'url': url,
            'error': error_msg,
            'type': 'proxy_error',
            'elapsed': elapsed,
            'traceback': traceback.format_exc()
        })
        print(f"  ✗ 失败 | {error_msg}")
        track_failed_website(url)
        return False
        
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['connection_errors'] += 1
        error_msg = f"连接错误: {str(e)}"
        stats['errors'].append({
            'timestamp': timestamp,
            'url': url,
            'error': error_msg,
            'type': 'connection_error',
            'elapsed': elapsed,
            'traceback': traceback.format_exc()
        })
        print(f"  ✗ 失败 | {error_msg}")
        track_failed_website(url)
        return False
        
    except Exception as e:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['other_errors'] += 1
        error_msg = f"其他错误: {type(e).__name__}: {str(e)}"
        stats['errors'].append({
            'timestamp': timestamp,
            'url': url,
            'error': error_msg,
            'type': 'other_error',
            'elapsed': elapsed,
            'traceback': traceback.format_exc()
        })
        print(f"  ✗ 失败 | {error_msg}")
        track_failed_website(url)
        return False


def track_failed_website(url):
    """记录失败的网站"""
    if url not in stats['failed_websites']:
        stats['failed_websites'][url] = 0
    stats['failed_websites'][url] += 1


def print_progress_stats():
    """打印进度统计"""
    success_rate = (stats['successful_requests'] / stats['total_requests'] * 100) \
                   if stats['total_requests'] > 0 else 0
    
    avg_response_time = sum(stats['response_times']) / len(stats['response_times']) \
                       if stats['response_times'] else 0
    
    print(f"\n{'='*70}")
    print(f"当前统计:")
    print(f"  总请求数: {stats['total_requests']}")
    print(f"  成功: {stats['successful_requests']} | 失败: {stats['failed_requests']}")
    print(f"  成功率: {success_rate:.1f}%")
    if stats['response_times']:
        print(f"  平均响应时间: {avg_response_time:.2f}秒")
    if stats['failed_requests'] > 0:
        print(f"  失败原因分布:")
        print(f"    - 超时: {stats['timeouts']}")
        print(f"    - 连接错误: {stats['connection_errors']}")
        print(f"    - 代理错误: {stats['proxy_errors']}")
        print(f"    - 其他错误: {stats['other_errors']}")
    print(f"{'='*70}")


def generate_report():
    """生成详细测试报告"""
    report_filename = f"proxy_stability_test_report_{int(time.time())}.md"
    
    success_rate = (stats['successful_requests'] / stats['total_requests'] * 100) \
                   if stats['total_requests'] > 0 else 0
    
    avg_response_time = sum(stats['response_times']) / len(stats['response_times']) \
                       if stats['response_times'] else 0
    
    min_response_time = min(stats['response_times']) if stats['response_times'] else 0
    max_response_time = max(stats['response_times']) if stats['response_times'] else 0
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("# SOCKS5代理稳定性测试报告\n\n")
        f.write(f"**测试时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 测试配置\n\n")
        f.write(f"- **代理服务器:** {PROXY_HOST}:{PROXY_PORT}\n")
        f.write(f"- **测试时长:** {TEST_DURATION}秒 ({TEST_DURATION//60}分钟)\n")
        f.write(f"- **请求间隔:** {REQUEST_INTERVAL}秒\n")
        f.write(f"- **请求超时:** {REQUEST_TIMEOUT}秒\n")
        f.write(f"- **测试网站数量:** {len(TEST_WEBSITES)}\n\n")
        
        f.write("### 测试网站列表\n\n")
        for i, url in enumerate(TEST_WEBSITES, 1):
            f.write(f"{i}. {url}\n")
        f.write("\n")
        
        f.write("## 测试结果统计\n\n")
        f.write(f"- **总请求数:** {stats['total_requests']}\n")
        f.write(f"- **成功请求:** {stats['successful_requests']}\n")
        f.write(f"- **失败请求:** {stats['failed_requests']}\n")
        f.write(f"- **成功率:** {success_rate:.2f}%\n\n")
        
        if stats['response_times']:
            f.write("### 响应时间统计\n\n")
            f.write(f"- **平均响应时间:** {avg_response_time:.2f}秒\n")
            f.write(f"- **最快响应时间:** {min_response_time:.2f}秒\n")
            f.write(f"- **最慢响应时间:** {max_response_time:.2f}秒\n\n")
        
        if stats['failed_requests'] > 0:
            f.write("### 失败原因分布\n\n")
            f.write(f"- **超时 (Timeout):** {stats['timeouts']} ({stats['timeouts']/stats['failed_requests']*100:.1f}%)\n")
            f.write(f"- **连接错误 (Connection Error):** {stats['connection_errors']} ({stats['connection_errors']/stats['failed_requests']*100:.1f}%)\n")
            f.write(f"- **代理错误 (Proxy Error):** {stats['proxy_errors']} ({stats['proxy_errors']/stats['failed_requests']*100:.1f}%)\n")
            f.write(f"- **其他错误:** {stats['other_errors']} ({stats['other_errors']/stats['failed_requests']*100:.1f}%)\n\n")
            
            if stats['failed_websites']:
                f.write("### 失败网站统计\n\n")
                sorted_failures = sorted(stats['failed_websites'].items(), 
                                       key=lambda x: x[1], reverse=True)
                for url, count in sorted_failures:
                    f.write(f"- {url}: {count}次失败\n")
                f.write("\n")
            
            f.write("## 详细错误日志\n\n")
            for i, error in enumerate(stats['errors'], 1):
                f.write(f"### 错误 #{i}\n\n")
                f.write(f"- **时间:** {error['timestamp']}\n")
                f.write(f"- **URL:** {error['url']}\n")
                f.write(f"- **错误类型:** {error['type']}\n")
                f.write(f"- **错误信息:** {error['error']}\n")
                if 'elapsed' in error:
                    f.write(f"- **耗时:** {error['elapsed']:.2f}秒\n")
                if 'traceback' in error:
                    f.write(f"\n**详细堆栈:**\n\n```\n{error['traceback']}\n```\n")
                f.write("\n")
        
        f.write("## 结论\n\n")
        if success_rate >= 99:
            f.write("✅ **代理连接非常稳定**，成功率达到99%以上。\n\n")
        elif success_rate >= 95:
            f.write("⚠️ **代理连接基本稳定**，但有少量失败情况，建议关注。\n\n")
        elif success_rate >= 80:
            f.write("⚠️ **代理连接不够稳定**，失败率较高，需要调查原因。\n\n")
        else:
            f.write("❌ **代理连接非常不稳定**，失败率过高，需要紧急处理。\n\n")
        
        if stats['proxy_errors'] > 0:
            f.write("**发现代理错误**，可能的原因：\n")
            f.write("1. 代理服务器不稳定或重启\n")
            f.write("2. 网络连接问题\n")
            f.write("3. 代理服务器资源不足\n")
            f.write("4. 防火墙或安全策略限制\n\n")
        
        if stats['timeouts'] > stats['failed_requests'] * 0.5 and stats['failed_requests'] > 0:
            f.write("**超时是主要问题**，建议：\n")
            f.write("1. 检查代理服务器性能\n")
            f.write("2. 检查网络延迟\n")
            f.write("3. 增加超时时间\n")
            f.write("4. 检查目标网站的可访问性\n\n")
        
        if stats['connection_errors'] > 0:
            f.write("**发现连接错误**，建议：\n")
            f.write("1. 检查代理服务器是否正常运行\n")
            f.write("2. 检查网络连接状态\n")
            f.write("3. 查看代理服务器日志\n")
            f.write("4. 检查是否有连接数限制\n\n")
    
    print(f"\n详细测试报告已生成: {report_filename}")
    return report_filename


def main():
    """主测试流程"""
    print("="*70)
    print("SOCKS5代理稳定性测试")
    print("="*70)
    print(f"测试时长: {TEST_DURATION}秒 ({TEST_DURATION//60}分钟)")
    print(f"请求间隔: {REQUEST_INTERVAL}秒")
    print(f"测试网站: {len(TEST_WEBSITES)}个")
    print("="*70)
    
    # 检查PySocks是否安装
    try:
        import socks
    except ImportError:
        print("错误: 需要安装PySocks库")
        print("请运行: pip install PySocks requests")
        sys.exit(1)
    
    # 配置代理
    try:
        setup_socks5_proxy()
    except Exception as e:
        print(f"配置代理失败: {e}")
        sys.exit(1)
    
    # 开始测试
    print(f"\n开始测试... (按Ctrl+C可提前结束)")
    start_time = time.time()
    request_num = 0
    website_index = 0
    
    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= TEST_DURATION:
                print(f"\n已达到测试时长 ({TEST_DURATION}秒)，结束测试。")
                break
            
            # 轮询访问不同网站
            url = TEST_WEBSITES[website_index % len(TEST_WEBSITES)]
            website_index += 1
            
            request_num += 1
            stats['total_requests'] += 1
            
            test_single_request(url, request_num)
            
            # 每10次请求打印一次统计
            if request_num % 10 == 0:
                print_progress_stats()
                remaining = TEST_DURATION - elapsed
                print(f"剩余时间: {remaining:.0f}秒 ({remaining/60:.1f}分钟)")
            
            # 等待下一次请求
            if elapsed < TEST_DURATION:
                time.sleep(REQUEST_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n用户中断测试。")
    
    # 最终统计
    print("\n" + "="*70)
    print("测试完成!")
    print("="*70)
    print_progress_stats()
    
    # 生成报告
    report_file = generate_report()
    
    print(f"\n测试报告已保存到: {report_file}")
    print("\n建议:")
    if stats['failed_requests'] > 0:
        print("1. 查看详细报告了解失败原因")
        print("2. 检查代理服务器日志: logs/proxy.log")
        print("3. 检查服务器状态和资源使用情况")
        if stats['proxy_errors'] > 0:
            print("4. 重点关注代理错误，可能需要重启代理服务")


if __name__ == '__main__':
    main()

