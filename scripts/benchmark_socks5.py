#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKS5 代理压力测试脚本
用于测试代理服务器在高并发情况下的性能表现

功能：
- 支持自定义并发数
- 测试每个连接的流量吞吐量
- 测试每个连接的延迟
- 生成详细的性能报告
- 支持实时监控和图表生成
"""

import socket
import struct
import time
import threading
import statistics
import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from collections import defaultdict
import json

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SOCKS5Benchmark:
    """SOCKS5 代理压测工具"""
    
    def __init__(self, 
                 proxy_host='127.0.0.1', 
                 proxy_port=1082,
                 target_host='8.8.8.8',
                 target_port=80,
                 concurrent=100,
                 duration=30,
                 username=None,
                 password=None,
                 timeout=10,
                 packet_size=1024):
        """
        初始化压测工具
        
        Args:
            proxy_host: 代理服务器地址
            proxy_port: 代理服务器端口
            target_host: 目标服务器地址
            target_port: 目标服务器端口
            concurrent: 并发连接数
            duration: 测试持续时间(秒)
            username: SOCKS5 用户名
            password: SOCKS5 密码
            timeout: 连接超时时间
            packet_size: 每次发送的数据包大小(字节)
        """
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.target_host = target_host
        self.target_port = target_port
        self.concurrent = concurrent
        self.duration = duration
        self.username = username
        self.password = password
        self.timeout = timeout
        self.packet_size = packet_size
        
        # 统计数据
        self.lock = threading.Lock()
        self.results = []
        self.error_count = 0
        self.success_count = 0
        self.connection_times = []
        self.latencies = []
        self.throughputs = []
        self.errors = defaultdict(int)
        
        # 控制标志
        self.stop_flag = threading.Event()
        self.start_time = None
        self.end_time = None
    
    def connect_socks5(self, sock):
        """
        建立 SOCKS5 连接
        
        Returns:
            tuple: (成功标志, 错误信息)
        """
        try:
            # 连接到代理服务器
            connect_start = time.time()
            sock.connect((self.proxy_host, self.proxy_port))
            connect_time = time.time() - connect_start
            
            # SOCKS5 握手 - 选择认证方法
            if self.username and self.password:
                # 支持用户名密码认证
                sock.send(b'\x05\x02\x00\x02')  # 支持无认证和用户名密码认证
            else:
                # 只支持无认证
                sock.send(b'\x05\x01\x00')
            
            # 接收服务器选择的认证方法
            response = sock.recv(2)
            if len(response) < 2:
                return False, "握手响应不完整", connect_time
            
            version, method = struct.unpack('!BB', response)
            if version != 5:
                return False, f"不支持的SOCKS版本: {version}", connect_time
            
            if method == 0xFF:
                return False, "服务器拒绝所有认证方法", connect_time
            
            # 如果需要用户名密码认证
            if method == 2:
                if not self.username or not self.password:
                    return False, "服务器要求认证但未提供凭据", connect_time
                
                # 发送认证信息
                auth_data = struct.pack('!B', 1)  # 认证协议版本
                auth_data += struct.pack('!B', len(self.username))
                auth_data += self.username.encode()
                auth_data += struct.pack('!B', len(self.password))
                auth_data += self.password.encode()
                
                sock.send(auth_data)
                
                # 接收认证结果
                auth_response = sock.recv(2)
                if len(auth_response) < 2:
                    return False, "认证响应不完整", connect_time
                
                auth_version, auth_status = struct.unpack('!BB', auth_response)
                if auth_status != 0:
                    return False, f"认证失败: {auth_status}", connect_time
            
            # 发送连接请求
            request = b'\x05\x01\x00\x01'  # VER, CMD(CONNECT), RSV, ATYP(IPv4)
            
            # 添加目标地址
            ip_parts = [int(x) for x in self.target_host.split('.')]
            request += struct.pack('!BBBB', *ip_parts)
            request += struct.pack('!H', self.target_port)
            
            sock.send(request)
            
            # 接收连接响应
            response = sock.recv(10)
            if len(response) < 10:
                return False, "连接响应不完整", connect_time
            
            version, reply, rsv, atyp = struct.unpack('!BBBB', response[:4])
            
            if version != 5:
                return False, f"响应版本错误: {version}", connect_time
            
            if reply != 0:
                error_codes = {
                    1: "一般性失败",
                    2: "规则集不允许",
                    3: "网络不可达",
                    4: "主机不可达",
                    5: "连接被拒绝",
                    6: "TTL过期",
                    7: "不支持的命令",
                    8: "不支持的地址类型"
                }
                error_msg = error_codes.get(reply, f"未知错误: {reply}")
                return False, f"连接失败: {error_msg}", connect_time
            
            return True, None, connect_time
            
        except socket.timeout:
            return False, "连接超时", 0
        except Exception as e:
            return False, str(e), 0
    
    def worker(self, worker_id):
        """
        工作线程 - 执行压测任务
        
        Args:
            worker_id: 工作线程ID
        """
        result = {
            'worker_id': worker_id,
            'success': False,
            'connect_time': 0,
            'total_bytes_sent': 0,
            'total_bytes_recv': 0,
            'latencies': [],
            'error': None,
            'duration': 0
        }
        
        sock = None
        try:
            # 创建socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # 建立SOCKS5连接
            success, error, connect_time = self.connect_socks5(sock)
            result['connect_time'] = connect_time
            
            with self.lock:
                self.connection_times.append(connect_time)
            
            if not success:
                result['error'] = error
                with self.lock:
                    self.error_count += 1
                    self.errors[error] += 1
                return result
            
            # 开始传输数据测试
            test_data = b'X' * self.packet_size
            worker_start_time = time.time()
            
            while not self.stop_flag.is_set():
                elapsed = time.time() - worker_start_time
                if elapsed >= self.duration:
                    break
                
                try:
                    # 发送数据并测量延迟
                    send_start = time.time()
                    sent = sock.send(test_data)
                    send_time = time.time() - send_start
                    
                    result['total_bytes_sent'] += sent
                    result['latencies'].append(send_time * 1000)  # 转换为毫秒
                    
                    # 尝试接收数据（如果有）
                    sock.setblocking(False)
                    try:
                        recv_data = sock.recv(4096)
                        result['total_bytes_recv'] += len(recv_data)
                    except:
                        pass
                    sock.setblocking(True)
                    
                    # 短暂休息，避免过载
                    time.sleep(0.001)
                    
                except socket.timeout:
                    break
                except Exception as e:
                    result['error'] = str(e)
                    break
            
            result['duration'] = time.time() - worker_start_time
            result['success'] = True
            
            with self.lock:
                self.success_count += 1
                if result['latencies']:
                    self.latencies.extend(result['latencies'])
                
                if result['duration'] > 0:
                    throughput = result['total_bytes_sent'] / result['duration']
                    self.throughputs.append(throughput)
            
        except Exception as e:
            result['error'] = f"意外错误: {str(e)}"
            with self.lock:
                self.error_count += 1
                self.errors[result['error']] += 1
        
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
        
        return result
    
    def monitor_progress(self):
        """监控进度的后台线程"""
        print(f"\n{Colors.OKCYAN}⏱️  开始压测，持续时间: {self.duration} 秒{Colors.ENDC}\n")
        
        last_update = time.time()
        while not self.stop_flag.is_set():
            time.sleep(1)
            
            if time.time() - last_update >= 5:  # 每5秒更新一次
                elapsed = time.time() - self.start_time
                remaining = max(0, self.duration - elapsed)
                
                with self.lock:
                    current_success = self.success_count
                    current_error = self.error_count
                    total = current_success + current_error
                
                progress = min(100, (elapsed / self.duration) * 100)
                print(f"{Colors.OKBLUE}📊 进度: {progress:.1f}% | "
                      f"成功: {current_success} | "
                      f"失败: {current_error} | "
                      f"剩余: {remaining:.0f}秒{Colors.ENDC}")
                
                last_update = time.time()
    
    def run(self):
        """运行压测"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
        print(f"🚀 SOCKS5 代理压力测试")
        print(f"{'='*80}{Colors.ENDC}\n")
        
        print(f"{Colors.OKBLUE}测试配置:{Colors.ENDC}")
        print(f"  代理服务器: {self.proxy_host}:{self.proxy_port}")
        print(f"  目标服务器: {self.target_host}:{self.target_port}")
        print(f"  并发连接数: {self.concurrent}")
        print(f"  测试持续时间: {self.duration} 秒")
        print(f"  数据包大小: {self.packet_size} 字节")
        print(f"  认证模式: {'用户名密码' if self.username else '无认证'}")
        print(f"  连接超时: {self.timeout} 秒")
        
        # 开始测试
        self.start_time = time.time()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
        monitor_thread.start()
        
        # 使用线程池执行压测
        with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            futures = []
            
            # 提交所有工作线程
            for i in range(self.concurrent):
                future = executor.submit(self.worker, i)
                futures.append(future)
            
            # 等待所有线程完成或超时
            try:
                for future in as_completed(futures, timeout=self.duration + 10):
                    try:
                        result = future.result()
                        self.results.append(result)
                    except Exception as e:
                        print(f"{Colors.FAIL}❌ 线程执行失败: {e}{Colors.ENDC}")
            
            except KeyboardInterrupt:
                print(f"\n{Colors.WARNING}⏹️  用户中断测试{Colors.ENDC}")
                self.stop_flag.set()
            
            finally:
                self.stop_flag.set()
        
        self.end_time = time.time()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print(f"\n\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
        print(f"📊 测试报告")
        print(f"{'='*80}{Colors.ENDC}\n")
        
        total_time = self.end_time - self.start_time
        total_connections = self.success_count + self.error_count
        
        # 基本统计
        print(f"{Colors.OKGREEN}{Colors.BOLD}▶ 基本统计{Colors.ENDC}")
        print(f"  测试时长: {total_time:.2f} 秒")
        print(f"  总连接数: {total_connections}")
        print(f"  成功连接: {self.success_count} ({self.success_count/total_connections*100:.1f}%)")
        print(f"  失败连接: {self.error_count} ({self.error_count/total_connections*100:.1f}%)")
        
        # 连接性能
        if self.connection_times:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}▶ 连接性能{Colors.ENDC}")
            print(f"  平均连接时间: {statistics.mean(self.connection_times)*1000:.2f} ms")
            print(f"  最小连接时间: {min(self.connection_times)*1000:.2f} ms")
            print(f"  最大连接时间: {max(self.connection_times)*1000:.2f} ms")
            if len(self.connection_times) > 1:
                print(f"  连接时间标准差: {statistics.stdev(self.connection_times)*1000:.2f} ms")
        
        # 延迟统计
        if self.latencies:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}▶ 延迟统计{Colors.ENDC}")
            print(f"  平均延迟: {statistics.mean(self.latencies):.2f} ms")
            print(f"  最小延迟: {min(self.latencies):.2f} ms")
            print(f"  最大延迟: {max(self.latencies):.2f} ms")
            print(f"  中位数延迟: {statistics.median(self.latencies):.2f} ms")
            
            if len(self.latencies) > 1:
                print(f"  延迟标准差: {statistics.stdev(self.latencies):.2f} ms")
            
            # 百分位数
            sorted_latencies = sorted(self.latencies)
            p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            
            print(f"  P50 延迟: {p50:.2f} ms")
            print(f"  P95 延迟: {p95:.2f} ms")
            print(f"  P99 延迟: {p99:.2f} ms")
        
        # 吞吐量统计
        if self.throughputs:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}▶ 吞吐量统计{Colors.ENDC}")
            avg_throughput = statistics.mean(self.throughputs)
            total_throughput = sum(self.throughputs)
            
            print(f"  每连接平均吞吐量: {self.format_bytes(avg_throughput)}/s")
            print(f"  每连接最小吞吐量: {self.format_bytes(min(self.throughputs))}/s")
            print(f"  每连接最大吞吐量: {self.format_bytes(max(self.throughputs))}/s")
            print(f"  总吞吐量: {self.format_bytes(total_throughput)}/s")
        
        # 流量统计
        total_sent = sum(r['total_bytes_sent'] for r in self.results)
        total_recv = sum(r['total_bytes_recv'] for r in self.results)
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}▶ 流量统计{Colors.ENDC}")
        print(f"  总发送流量: {self.format_bytes(total_sent)}")
        print(f"  总接收流量: {self.format_bytes(total_recv)}")
        print(f"  总流量: {self.format_bytes(total_sent + total_recv)}")
        
        if total_time > 0:
            print(f"  平均发送速率: {self.format_bytes(total_sent/total_time)}/s")
            print(f"  平均接收速率: {self.format_bytes(total_recv/total_time)}/s")
        
        # 错误统计
        if self.errors:
            print(f"\n{Colors.FAIL}{Colors.BOLD}▶ 错误统计{Colors.ENDC}")
            for error, count in sorted(self.errors.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error}: {count} 次")
        
        # 性能评分
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}▶ 性能评分{Colors.ENDC}")
        
        score = 0
        max_score = 100
        
        # 成功率评分 (30分)
        if total_connections > 0:
            success_rate = self.success_count / total_connections
            score += success_rate * 30
            print(f"  成功率得分: {success_rate * 30:.1f}/30")
        
        # 延迟评分 (35分)
        if self.latencies:
            avg_latency = statistics.mean(self.latencies)
            # 延迟越低越好，假设10ms是完美延迟
            latency_score = max(0, 35 * (1 - min(avg_latency / 100, 1)))
            score += latency_score
            print(f"  延迟得分: {latency_score:.1f}/35")
        
        # 吞吐量评分 (35分)
        if self.throughputs:
            avg_throughput = statistics.mean(self.throughputs)
            # 假设10MB/s是完美吞吐量
            throughput_score = max(0, 35 * min(avg_throughput / (10 * 1024 * 1024), 1))
            score += throughput_score
            print(f"  吞吐量得分: {throughput_score:.1f}/35")
        
        print(f"\n  {Colors.BOLD}总分: {score:.1f}/{max_score}{Colors.ENDC}")
        
        # 评级
        if score >= 90:
            grade = "A+ (优秀)"
            color = Colors.OKGREEN
        elif score >= 80:
            grade = "A (良好)"
            color = Colors.OKGREEN
        elif score >= 70:
            grade = "B (中等)"
            color = Colors.OKBLUE
        elif score >= 60:
            grade = "C (一般)"
            color = Colors.WARNING
        else:
            grade = "D (较差)"
            color = Colors.FAIL
        
        print(f"  {color}{Colors.BOLD}评级: {grade}{Colors.ENDC}")
        
        # 保存详细报告
        self.save_report()
    
    def format_bytes(self, bytes_value):
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def save_report(self):
        """保存详细报告到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"benchmark_report_{timestamp}.json"
        
        report = {
            'test_config': {
                'proxy_host': self.proxy_host,
                'proxy_port': self.proxy_port,
                'target_host': self.target_host,
                'target_port': self.target_port,
                'concurrent': self.concurrent,
                'duration': self.duration,
                'packet_size': self.packet_size,
                'timeout': self.timeout
            },
            'summary': {
                'total_time': self.end_time - self.start_time,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'total_sent': sum(r['total_bytes_sent'] for r in self.results),
                'total_recv': sum(r['total_bytes_recv'] for r in self.results)
            },
            'connection_times': {
                'mean': statistics.mean(self.connection_times) if self.connection_times else 0,
                'min': min(self.connection_times) if self.connection_times else 0,
                'max': max(self.connection_times) if self.connection_times else 0,
                'stdev': statistics.stdev(self.connection_times) if len(self.connection_times) > 1 else 0
            },
            'latencies': {
                'mean': statistics.mean(self.latencies) if self.latencies else 0,
                'min': min(self.latencies) if self.latencies else 0,
                'max': max(self.latencies) if self.latencies else 0,
                'median': statistics.median(self.latencies) if self.latencies else 0,
                'stdev': statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0
            },
            'throughputs': {
                'mean': statistics.mean(self.throughputs) if self.throughputs else 0,
                'min': min(self.throughputs) if self.throughputs else 0,
                'max': max(self.throughputs) if self.throughputs else 0,
                'total': sum(self.throughputs) if self.throughputs else 0
            },
            'errors': dict(self.errors)
        }
        
        # 保存JSON报告
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n{Colors.OKGREEN}✅ JSON 报告已保存到: {json_filename}{Colors.ENDC}")
        except Exception as e:
            print(f"\n{Colors.WARNING}⚠️  保存 JSON 报告失败: {e}{Colors.ENDC}")
        
        # 保存Markdown报告
        self.save_markdown_report(report)
    
    def save_markdown_report(self, report):
        """生成并保存 Markdown 格式的测试报告"""
        md_filename = "yace.md"
        
        try:
            total_time = report['summary']['total_time']
            total_connections = report['summary']['success_count'] + report['summary']['error_count']
            success_rate = (report['summary']['success_count'] / total_connections * 100) if total_connections > 0 else 0
            
            total_sent = report['summary']['total_sent']
            total_recv = report['summary']['total_recv']
            
            # 计算评分
            score = 0
            if total_connections > 0:
                score += (report['summary']['success_count'] / total_connections) * 30
            
            if self.latencies:
                avg_latency = statistics.mean(self.latencies)
                latency_score = max(0, 35 * (1 - min(avg_latency / 100, 1)))
                score += latency_score
            
            if self.throughputs:
                avg_throughput = statistics.mean(self.throughputs)
                throughput_score = max(0, 35 * min(avg_throughput / (10 * 1024 * 1024), 1))
                score += throughput_score
            
            # 评级
            if score >= 90:
                grade = "A+ (优秀)"
            elif score >= 80:
                grade = "A (良好)"
            elif score >= 70:
                grade = "B (中等)"
            elif score >= 60:
                grade = "C (一般)"
            else:
                grade = "D (较差)"
            
            # 生成Markdown内容
            md_content = f"""# SOCKS5 代理压力测试报告

## 📋 测试概览

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**测试结果**: {'✅ 通过' if success_rate >= 95 else '⚠️ 需要优化' if success_rate >= 80 else '❌ 失败'}

**性能评分**: {score:.1f}/100 - {grade}

---

## ⚙️ 测试配置

| 配置项 | 值 |
|--------|-----|
| 代理服务器 | `{report['test_config']['proxy_host']}:{report['test_config']['proxy_port']}` |
| 目标服务器 | `{report['test_config']['target_host']}:{report['test_config']['target_port']}` |
| 并发连接数 | **{report['test_config']['concurrent']}** |
| 测试持续时间 | {report['test_config']['duration']} 秒 |
| 数据包大小 | {report['test_config']['packet_size']} 字节 |
| 连接超时 | {report['test_config']['timeout']} 秒 |
| 认证模式 | {'用户名密码认证' if self.username else '无认证'} |

---

## 📊 测试结果

### 基本统计

| 指标 | 数值 |
|------|------|
| 实际测试时长 | {total_time:.2f} 秒 |
| 总连接数 | {total_connections} |
| 成功连接 | {report['summary']['success_count']} ({success_rate:.1f}%) |
| 失败连接 | {report['summary']['error_count']} ({(report['summary']['error_count']/total_connections*100) if total_connections > 0 else 0:.1f}%) |

### 连接性能

| 指标 | 数值 |
|------|------|
| 平均连接时间 | {report['connection_times']['mean']*1000:.2f} ms |
| 最小连接时间 | {report['connection_times']['min']*1000:.2f} ms |
| 最大连接时间 | {report['connection_times']['max']*1000:.2f} ms |
| 连接时间标准差 | {report['connection_times']['stdev']*1000:.2f} ms |

### 延迟统计

| 指标 | 数值 |
|------|------|
| 平均延迟 | **{report['latencies']['mean']:.2f} ms** |
| 最小延迟 | {report['latencies']['min']:.2f} ms |
| 最大延迟 | {report['latencies']['max']:.2f} ms |
| 中位数延迟 | {report['latencies']['median']:.2f} ms |
| 延迟标准差 | {report['latencies']['stdev']:.2f} ms |
"""

            # 添加延迟百分位数
            if self.latencies:
                sorted_latencies = sorted(self.latencies)
                p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
                p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
                p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
                
                md_content += f"""
#### 延迟百分位数

| 百分位 | 延迟 |
|--------|------|
| P50 (中位数) | {p50:.2f} ms |
| P95 | {p95:.2f} ms |
| P99 | {p99:.2f} ms |
"""

            # 添加吞吐量统计
            md_content += f"""
### 吞吐量统计

| 指标 | 数值 |
|------|------|
| 每连接平均吞吐量 | **{self.format_bytes(report['throughputs']['mean'])}/s** |
| 每连接最小吞吐量 | {self.format_bytes(report['throughputs']['min'])}/s |
| 每连接最大吞吐量 | {self.format_bytes(report['throughputs']['max'])}/s |
| 总吞吐量 | **{self.format_bytes(report['throughputs']['total'])}/s** |

### 流量统计

| 指标 | 数值 |
|------|------|
| 总发送流量 | {self.format_bytes(total_sent)} |
| 总接收流量 | {self.format_bytes(total_recv)} |
| 总流量 | {self.format_bytes(total_sent + total_recv)} |
| 平均发送速率 | {self.format_bytes(total_sent/total_time) if total_time > 0 else '0 B'}/s |
| 平均接收速率 | {self.format_bytes(total_recv/total_time) if total_time > 0 else '0 B'}/s |

---

## 🎯 性能指标总结

### 单个并发连接性能

基于 **{self.concurrent}** 个并发连接的测试结果：

- **平均延迟**: {report['latencies']['mean']:.2f} ms
- **每连接吞吐量**: {self.format_bytes(report['throughputs']['mean'])}/s
- **每连接流量**: {self.format_bytes(total_sent/self.concurrent if self.concurrent > 0 else 0)}

### 整体性能表现

- **总吞吐量**: {self.format_bytes(report['throughputs']['total'])}/s
- **成功率**: {success_rate:.1f}%
- **平均响应时间**: {report['latencies']['mean']:.2f} ms

---
"""

            # 添加错误统计（如果有）
            if report['errors']:
                md_content += f"""## ⚠️ 错误统计

| 错误类型 | 出现次数 |
|----------|----------|
"""
                for error, count in sorted(report['errors'].items(), key=lambda x: x[1], reverse=True):
                    md_content += f"| {error} | {count} |\n"
                
                md_content += "\n---\n\n"

            # 添加性能分析和建议
            md_content += f"""## 💡 性能分析与建议

### 性能评估

"""
            
            if success_rate >= 95:
                md_content += "✅ **连接成功率优秀** - 代理服务器稳定性良好\n\n"
            elif success_rate >= 80:
                md_content += "⚠️ **连接成功率一般** - 建议检查网络配置和资源限制\n\n"
            else:
                md_content += "❌ **连接成功率较低** - 需要立即检查代理服务器状态\n\n"
            
            if self.latencies:
                avg_latency = statistics.mean(self.latencies)
                if avg_latency < 10:
                    md_content += "✅ **延迟表现优秀** - 响应速度非常快\n\n"
                elif avg_latency < 50:
                    md_content += "✅ **延迟表现良好** - 响应速度可接受\n\n"
                elif avg_latency < 100:
                    md_content += "⚠️ **延迟表现一般** - 建议优化网络路径或增加服务器资源\n\n"
                else:
                    md_content += "❌ **延迟过高** - 需要立即优化网络配置或升级硬件\n\n"
            
            if self.throughputs:
                avg_throughput = statistics.mean(self.throughputs)
                if avg_throughput > 5 * 1024 * 1024:  # 5MB/s
                    md_content += "✅ **吞吐量优秀** - 数据传输速度很快\n\n"
                elif avg_throughput > 1 * 1024 * 1024:  # 1MB/s
                    md_content += "✅ **吞吐量良好** - 数据传输速度可接受\n\n"
                elif avg_throughput > 100 * 1024:  # 100KB/s
                    md_content += "⚠️ **吞吐量一般** - 建议检查网络带宽限制\n\n"
                else:
                    md_content += "❌ **吞吐量较低** - 需要检查网络配置或增加带宽\n\n"

            md_content += f"""### 优化建议

1. **并发优化**
   - 当前测试并发数: {self.concurrent}
   - 建议根据服务器配置调整 `max_connections` 参数
   - 监控系统资源使用情况（CPU、内存、网络）

2. **性能调优**
   - 检查系统文件描述符限制 (`ulimit -n`)
   - 优化 TCP/IP 内核参数
   - 考虑启用连接池和连接复用

3. **监控建议**
   - 持续监控延迟和吞吐量指标
   - 设置告警阈值，及时发现性能问题
   - 定期进行压力测试，了解服务器承载能力

---

## 📈 测试结论

基于本次压力测试结果：

- 代理服务器在 **{self.concurrent} 个并发连接** 下运行 **{total_time:.0f} 秒**
- 总共处理了 **{total_connections} 个连接请求**
- 平均每个连接的延迟为 **{report['latencies']['mean']:.2f} ms**
- 平均每个连接的吞吐量为 **{self.format_bytes(report['throughputs']['mean'])}/s**
- 总体性能评分: **{score:.1f}/100** ({grade})

"""

            if score >= 80:
                md_content += "✅ **总体评价**: 代理服务器性能表现良好，可以满足生产环境需求。\n"
            elif score >= 60:
                md_content += "⚠️ **总体评价**: 代理服务器性能一般，建议进行优化后再投入生产环境。\n"
            else:
                md_content += "❌ **总体评价**: 代理服务器性能不足，需要进行重大优化或升级硬件。\n"

            md_content += f"""
---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

*测试工具: SOCKS5 Benchmark v1.0*
"""

            # 写入文件
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"{Colors.OKGREEN}✅ Markdown 报告已保存到: {md_filename}{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  保存 Markdown 报告失败: {e}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(
        description='SOCKS5 代理压力测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本测试 (100个并发，持续30秒)
  python benchmark_socks5.py
  
  # 500个并发测试，持续60秒
  python benchmark_socks5.py --concurrent 500 --duration 60
  
  # 使用认证的测试
  python benchmark_socks5.py --concurrent 500 --username testuser --password testpass
  
  # 自定义数据包大小 (10KB)
  python benchmark_socks5.py --concurrent 500 --packet-size 10240
  
  # 测试特定目标服务器
  python benchmark_socks5.py --target-host 1.1.1.1 --target-port 53
        """
    )
    
    parser.add_argument('--proxy-host', default='127.0.0.1',
                        help='代理服务器地址 (默认: 127.0.0.1)')
    parser.add_argument('--proxy-port', type=int, default=1082,
                        help='代理服务器端口 (默认: 1082)')
    parser.add_argument('--target-host', default='8.8.8.8',
                        help='目标服务器地址 (默认: 8.8.8.8)')
    parser.add_argument('--target-port', type=int, default=80,
                        help='目标服务器端口 (默认: 80)')
    parser.add_argument('-c', '--concurrent', type=int, default=100,
                        help='并发连接数 (默认: 100)')
    parser.add_argument('-d', '--duration', type=int, default=30,
                        help='测试持续时间(秒) (默认: 30)')
    parser.add_argument('-u', '--username', default=None,
                        help='SOCKS5 用户名')
    parser.add_argument('-p', '--password', default=None,
                        help='SOCKS5 密码')
    parser.add_argument('--timeout', type=int, default=10,
                        help='连接超时时间(秒) (默认: 10)')
    parser.add_argument('--packet-size', type=int, default=1024,
                        help='数据包大小(字节) (默认: 1024)')
    
    args = parser.parse_args()
    
    # 创建并运行压测
    benchmark = SOCKS5Benchmark(
        proxy_host=args.proxy_host,
        proxy_port=args.proxy_port,
        target_host=args.target_host,
        target_port=args.target_port,
        concurrent=args.concurrent,
        duration=args.duration,
        username=args.username,
        password=args.password,
        timeout=args.timeout,
        packet_size=args.packet_size
    )
    
    try:
        benchmark.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⏹️  测试被中断{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ 测试失败: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == '__main__':
    main()

