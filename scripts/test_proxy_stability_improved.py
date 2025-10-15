#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的SOCKS5代理稳定性测试
10分钟持续测试，使用优化的配置
"""

import requests
import time
from datetime import datetime
import json

# SOCKS5代理配置
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 1082
PROXY_USER = 'admin'
PROXY_PASS = '%VirWorkSocks!'

# 构建代理字符串
proxies = {
    'http': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    'https': f'socks5h://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
}

# 测试配置
TEST_DURATION = 600  # 10分钟
REQUEST_INTERVAL = 5  # 请求间隔
REQUEST_TIMEOUT = 20  # 增加超时时间到20秒

# 使用稳定可靠的测试网站
TEST_WEBSITES = [
    {'url': 'http://httpbin.org/get', 'name': 'HTTPBin(HTTP)', 'timeout': 15},
    {'url': 'https://httpbin.org/get', 'name': 'HTTPBin(HTTPS)', 'timeout': 15},
    {'url': 'http://example.com', 'name': 'Example(HTTP)', 'timeout': 10},
    {'url': 'https://example.com', 'name': 'Example(HTTPS)', 'timeout': 15},
    {'url': 'http://www.baidu.com', 'name': '百度(HTTP)', 'timeout': 15},
    {'url': 'https://www.baidu.com', 'name': '百度(HTTPS)', 'timeout': 20},
    {'url': 'https://www.github.com', 'name': 'GitHub', 'timeout': 20},
]

# 统计数据
stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'timeouts': 0,
    'connection_errors': 0,
    'proxy_errors': 0,
    'ssl_errors': 0,
    'other_errors': 0,
    'response_times': [],
    'errors_detail': [],
    'website_stats': {},  # 每个网站的统计
}

def init_website_stats():
    """初始化网站统计"""
    for site in TEST_WEBSITES:
        stats['website_stats'][site['name']] = {
            'total': 0,
            'success': 0,
            'fail': 0,
            'avg_time': 0,
            'times': []
        }

def test_single_request(site, request_num):
    """测试单次请求"""
    url = site['url']
    name = site['name']
    timeout = site['timeout']
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_time = time.time()
    
    try:
        print(f"\n[请求 #{request_num}] {timestamp}")
        print(f"  目标: {name} ({url})")
        
        response = requests.get(
            url, 
            proxies=proxies, 
            timeout=timeout,
            allow_redirects=True
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            stats['successful_requests'] += 1
            stats['response_times'].append(elapsed)
            stats['website_stats'][name]['success'] += 1
            stats['website_stats'][name]['times'].append(elapsed)
            
            print(f"  ✓ 成功 | 状态码: {response.status_code} | "
                  f"响应时间: {elapsed:.2f}秒 | "
                  f"内容长度: {len(response.content)} 字节")
            
            if response.history:
                print(f"  有 {len(response.history)} 次重定向")
            
            return True
        else:
            stats['failed_requests'] += 1
            stats['website_stats'][name]['fail'] += 1
            error_msg = f"HTTP状态码错误: {response.status_code}"
            stats['errors_detail'].append({
                'timestamp': timestamp,
                'site': name,
                'url': url,
                'error': error_msg,
                'type': 'http_error',
                'elapsed': elapsed
            })
            print(f"  ✗ 失败 | {error_msg}")
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['timeouts'] += 1
        stats['website_stats'][name]['fail'] += 1
        error_msg = f"请求超时 (>{timeout}秒)"
        stats['errors_detail'].append({
            'timestamp': timestamp,
            'site': name,
            'url': url,
            'error': error_msg,
            'type': 'timeout',
            'elapsed': elapsed
        })
        print(f"  ✗ 超时 ({elapsed:.2f}秒)")
        return False
        
    except requests.exceptions.ProxyError as e:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['proxy_errors'] += 1
        stats['website_stats'][name]['fail'] += 1
        error_msg = str(e)[:100]
        stats['errors_detail'].append({
            'timestamp': timestamp,
            'site': name,
            'url': url,
            'error': error_msg,
            'type': 'proxy_error',
            'elapsed': elapsed
        })
        print(f"  ✗ 代理错误 ({elapsed:.2f}秒)")
        return False
        
    except requests.exceptions.SSLError as e:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['ssl_errors'] += 1
        stats['website_stats'][name]['fail'] += 1
        error_msg = str(e)[:100]
        stats['errors_detail'].append({
            'timestamp': timestamp,
            'site': name,
            'url': url,
            'error': error_msg,
            'type': 'ssl_error',
            'elapsed': elapsed
        })
        print(f"  ✗ SSL错误 ({elapsed:.2f}秒)")
        return False
        
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['connection_errors'] += 1
        stats['website_stats'][name]['fail'] += 1
        error_msg = str(e)[:100]
        stats['errors_detail'].append({
            'timestamp': timestamp,
            'site': name,
            'url': url,
            'error': error_msg,
            'type': 'connection_error',
            'elapsed': elapsed
        })
        print(f"  ✗ 连接错误 ({elapsed:.2f}秒)")
        return False
        
    except Exception as e:
        elapsed = time.time() - start_time
        stats['failed_requests'] += 1
        stats['other_errors'] += 1
        stats['website_stats'][name]['fail'] += 1
        error_msg = f"{type(e).__name__}: {str(e)[:80]}"
        stats['errors_detail'].append({
            'timestamp': timestamp,
            'site': name,
            'url': url,
            'error': error_msg,
            'type': 'other_error',
            'elapsed': elapsed
        })
        print(f"  ✗ 其他错误 ({elapsed:.2f}秒): {error_msg}")
        return False
    finally:
        stats['website_stats'][name]['total'] += 1

def print_progress_stats():
    """打印进度统计"""
    success_rate = (stats['successful_requests'] / stats['total_requests'] * 100) \
                   if stats['total_requests'] > 0 else 0
    
    avg_response_time = sum(stats['response_times']) / len(stats['response_times']) \
                       if stats['response_times'] else 0
    
    print(f"\n{'='*70}")
    print(f"当前统计 ({stats['total_requests']}次请求):")
    print(f"  成功: {stats['successful_requests']} | 失败: {stats['failed_requests']} | "
          f"成功率: {success_rate:.1f}%")
    
    if stats['response_times']:
        min_time = min(stats['response_times'])
        max_time = max(stats['response_times'])
        print(f"  响应时间: 平均{avg_response_time:.2f}s | 最快{min_time:.2f}s | 最慢{max_time:.2f}s")
    
    if stats['failed_requests'] > 0:
        print(f"  失败原因: 超时{stats['timeouts']} | 连接{stats['connection_errors']} | "
              f"代理{stats['proxy_errors']} | SSL{stats['ssl_errors']} | 其他{stats['other_errors']}")
    
    print(f"{'='*70}")

def generate_report():
    """生成详细测试报告"""
    report_filename = f"proxy_stability_report_{int(time.time())}.md"
    
    success_rate = (stats['successful_requests'] / stats['total_requests'] * 100) \
                   if stats['total_requests'] > 0 else 0
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("# SOCKS5代理稳定性测试报告\n\n")
        f.write(f"**测试时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 优化项\n\n")
        f.write("本次测试前已应用以下优化：\n\n")
        f.write("1. ✅ 增大缓冲区大小：从 4KB 提升到 32KB\n")
        f.write("2. ✅ 添加读写超时：每次操作最多60秒\n")
        f.write("3. ✅ 启用TCP Keep-Alive：每30秒探测连接状态\n")
        f.write("4. ✅ 禁用Nagle算法：减少延迟\n")
        f.write("5. ✅ 禁用baidu.com的URL过滤规则\n\n")
        
        f.write("## 测试配置\n\n")
        f.write(f"- **代理服务器:** {PROXY_HOST}:{PROXY_PORT}\n")
        f.write(f"- **测试时长:** {TEST_DURATION}秒 ({TEST_DURATION//60}分钟)\n")
        f.write(f"- **请求间隔:** {REQUEST_INTERVAL}秒\n")
        f.write(f"- **测试网站数量:** {len(TEST_WEBSITES)}\n\n")
        
        f.write("## 测试结果\n\n")
        f.write(f"- **总请求数:** {stats['total_requests']}\n")
        f.write(f"- **成功:** {stats['successful_requests']}\n")
        f.write(f"- **失败:** {stats['failed_requests']}\n")
        f.write(f"- **成功率:** {success_rate:.2f}%\n\n")
        
        if stats['response_times']:
            avg_time = sum(stats['response_times']) / len(stats['response_times'])
            min_time = min(stats['response_times'])
            max_time = max(stats['response_times'])
            f.write("### 响应时间统计\n\n")
            f.write(f"- **平均响应时间:** {avg_time:.2f}秒\n")
            f.write(f"- **最快响应:** {min_time:.2f}秒\n")
            f.write(f"- **最慢响应:** {max_time:.2f}秒\n\n")
        
        # 各网站统计
        f.write("### 各网站统计\n\n")
        f.write("| 网站 | 请求数 | 成功 | 失败 | 成功率 | 平均响应 |\n")
        f.write("|------|--------|------|------|--------|----------|\n")
        
        for site in TEST_WEBSITES:
            name = site['name']
            ws = stats['website_stats'][name]
            if ws['total'] > 0:
                ws_rate = ws['success'] / ws['total'] * 100
                ws_avg = sum(ws['times']) / len(ws['times']) if ws['times'] else 0
                f.write(f"| {name} | {ws['total']} | {ws['success']} | {ws['fail']} | "
                       f"{ws_rate:.1f}% | {ws_avg:.2f}s |\n")
        
        f.write("\n")
        
        if stats['failed_requests'] > 0:
            f.write("### 失败原因分布\n\n")
            f.write(f"- 超时: {stats['timeouts']}\n")
            f.write(f"- 连接错误: {stats['connection_errors']}\n")
            f.write(f"- 代理错误: {stats['proxy_errors']}\n")
            f.write(f"- SSL错误: {stats['ssl_errors']}\n")
            f.write(f"- 其他错误: {stats['other_errors']}\n\n")
            
            if len(stats['errors_detail']) > 0 and len(stats['errors_detail']) <= 20:
                f.write("### 错误详情\n\n")
                for i, err in enumerate(stats['errors_detail'], 1):
                    f.write(f"**错误 #{i}** ({err['timestamp']})\n")
                    f.write(f"- 网站: {err['site']}\n")
                    f.write(f"- 类型: {err['type']}\n")
                    f.write(f"- 耗时: {err['elapsed']:.2f}秒\n")
                    f.write(f"- 错误: {err['error']}\n\n")
        
        f.write("## 结论\n\n")
        
        if success_rate >= 95:
            f.write(f"✅ **代理非常稳定** (成功率 {success_rate:.1f}%)\n\n")
            f.write("代理服务器运行良好，适合生产环境使用。\n")
        elif success_rate >= 85:
            f.write(f"✅ **代理基本稳定** (成功率 {success_rate:.1f}%)\n\n")
            f.write("代理服务器运行正常，偶有失败但在可接受范围内。\n")
        elif success_rate >= 70:
            f.write(f"⚠️  **代理不够稳定** (成功率 {success_rate:.1f}%)\n\n")
            f.write("建议检查：\n")
            f.write("1. 网络连接质量\n")
            f.write("2. 服务器资源使用情况\n")
            f.write("3. 目标网站的可访问性\n")
        else:
            f.write(f"❌ **代理不稳定** (成功率 {success_rate:.1f}%)\n\n")
            f.write("需要立即处理，建议：\n")
            f.write("1. 检查代理服务器日志\n")
            f.write("2. 重启代理服务\n")
            f.write("3. 检查防火墙和网络配置\n")
    
    return report_filename

def main():
    """主测试流程"""
    print("="*70)
    print("SOCKS5代理稳定性测试 - 改进版")
    print("="*70)
    print(f"测试时长: {TEST_DURATION}秒 ({TEST_DURATION//60}分钟)")
    print(f"请求间隔: {REQUEST_INTERVAL}秒")
    print(f"测试网站: {len(TEST_WEBSITES)}个")
    print("="*70)
    
    init_website_stats()
    
    print(f"\n开始测试... (按Ctrl+C可提前结束)")
    start_time = time.time()
    request_num = 0
    site_index = 0
    
    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= TEST_DURATION:
                print(f"\n已达到测试时长 ({TEST_DURATION}秒)，结束测试。")
                break
            
            # 轮询访问不同网站
            site = TEST_WEBSITES[site_index % len(TEST_WEBSITES)]
            site_index += 1
            
            request_num += 1
            stats['total_requests'] += 1
            
            test_single_request(site, request_num)
            
            # 每10次请求打印一次统计
            if request_num % 10 == 0:
                print_progress_stats()
                remaining = TEST_DURATION - elapsed
                print(f"剩余时间: {remaining:.0f}秒 ({remaining/60:.1f}分钟)\n")
            
            # 等待下一次请求
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
    print(f"\n✅ 详细测试报告已生成: {report_file}")
    
    # 给出建议
    success_rate = (stats['successful_requests'] / stats['total_requests'] * 100) \
                   if stats['total_requests'] > 0 else 0
    
    print("\n建议:")
    if success_rate >= 95:
        print("  ✅ 代理非常稳定，无需额外操作")
    elif success_rate >= 85:
        print("  ✅ 代理基本稳定，可以继续使用")
        if stats['timeouts'] > 0:
            print("  💡 少量超时可能是目标网站响应慢，可以适当增加超时时间")
    else:
        print("  ⚠️  代理稳定性需要改进")
        print("  1. 查看详细报告了解失败原因")
        print("  2. 检查代理服务器日志: logs/proxy.log")
        print("  3. 检查系统资源使用情况")

if __name__ == '__main__':
    main()

