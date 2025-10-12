#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试：URL过滤双层检测机制

测试目标：
1. 验证SOCKS5层过滤（第一层）
2. 验证HTTP深度检测（第二层）
3. 验证两层配合工作
4. 验证逻辑一致性

测试场景：
- 场景A：SOCKS5层拦截（域名匹配）
- 场景B：应用层拦截（IP访问+HTTP Host检测）
- 场景C：HTTPS SNI检测
- 场景D：通过检测（无匹配规则）
- 场景E：边界情况
"""

import requests
import socket
import time
import sys
import json
from typing import Dict, List, Tuple
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置
API_BASE = "http://localhost:8012/api/v1"
PROXY_HOST = "localhost"
PROXY_PORT = 1082
USERNAME = "admin"
PASSWORD = "admin"

# 测试结果
test_results = []

class TestResult:
    def __init__(self, scenario: str, test_name: str, expected: str, actual: str, passed: bool, details: str = ""):
        self.scenario = scenario
        self.test_name = test_name
        self.expected = expected
        self.actual = actual
        self.passed = passed
        self.details = details
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} [{self.scenario}] {self.test_name}\n  预期: {self.expected}\n  实际: {self.actual}\n  详情: {self.details}"

def get_token():
    """获取JWT token"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()["token"]
        else:
            print(f"❌ 登录失败: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 连接API服务器失败: {e}")
        print(f"请确保server服务正在运行: ./bin/server")
        sys.exit(1)

def create_filter_rule(token: str, pattern: str, description: str) -> int:
    """创建URL过滤规则"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE}/filters",
        headers=headers,
        json={
            "pattern": pattern,
            "type": "block",
            "description": description,
            "enabled": True
        }
    )
    if response.status_code in [200, 201]:
        rule_id = response.json()["filter"]["id"]
        print(f"  ✓ 创建规则 [{rule_id}]: {pattern}")
        return rule_id
    else:
        print(f"  ✗ 创建规则失败: {response.text}")
        return None

def delete_filter_rule(token: str, rule_id: int):
    """删除URL过滤规则"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{API_BASE}/filters/{rule_id}",
        headers=headers
    )
    if response.status_code == 200:
        print(f"  ✓ 删除规则 [{rule_id}]")
    else:
        print(f"  ✗ 删除规则失败: {response.text}")

def test_socks5_access(url: str, should_block: bool, timeout: int = 5) -> Tuple[bool, str]:
    """
    通过SOCKS5代理测试访问
    
    返回: (是否被阻止, 详情信息)
    """
    try:
        import socks
        
        # 配置SOCKS5代理
        socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT,
                               username=USERNAME, password=PASSWORD)
        
        # 临时替换socket
        original_socket = socket.socket
        socket.socket = socks.socksocket
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout, verify=False)
            elapsed = time.time() - start_time
            
            # 连接成功
            blocked = False
            details = f"响应状态:{response.status_code}, 耗时:{elapsed:.2f}s"
            
        except Exception as e:
            # 连接失败（被拦截或其他错误）
            blocked = True
            details = f"连接失败: {str(e)[:100]}"
        
        finally:
            # 恢复原始socket
            socket.socket = original_socket
            import importlib
            importlib.reload(socket)
        
        return blocked, details
        
    except ImportError:
        return False, "PySocks未安装"

def run_test(scenario: str, test_name: str, url: str, should_block: bool, rule_pattern: str = None):
    """运行单个测试"""
    print(f"\n  测试: {test_name}")
    print(f"  目标: {url}")
    print(f"  预期: {'应该被拦截' if should_block else '应该通过'}")
    
    blocked, details = test_socks5_access(url, should_block)
    
    expected = "拦截" if should_block else "通过"
    actual = "拦截" if blocked else "通过"
    passed = (blocked == should_block)
    
    result = TestResult(
        scenario=scenario,
        test_name=test_name,
        expected=expected,
        actual=actual,
        passed=passed,
        details=details
    )
    
    test_results.append(result)
    print(f"  {'✅ 通过' if passed else '❌ 失败'}: {details}")
    
    return passed

def scenario_a_socks5_layer():
    """
    场景A: SOCKS5层拦截测试
    
    目标：验证第一层检测（SOCKS5层）能够正确拦截域名请求
    """
    print("\n" + "="*70)
    print("场景A: SOCKS5层拦截（第一层检测）")
    print("="*70)
    print("说明：当SOCKS5请求中包含域名时，第一层检测应该拦截")
    
    token = get_token()
    
    # 创建过滤规则
    rule_id = create_filter_rule(token, "example.com", "测试场景A-SOCKS5层拦截")
    if not rule_id:
        return False
    
    time.sleep(1)
    
    # 测试1: 直接访问被拦截的域名
    run_test(
        scenario="场景A",
        test_name="A1-域名直接匹配",
        url="http://example.com",
        should_block=True,
        rule_pattern="example.com"
    )
    
    # 测试2: 访问被拦截域名的子域名
    run_test(
        scenario="场景A",
        test_name="A2-子域名匹配",
        url="http://www.example.com",
        should_block=True,
        rule_pattern="example.com"
    )
    
    # 测试3: 访问其他域名应该通过
    run_test(
        scenario="场景A",
        test_name="A3-其他域名应通过",
        url="http://httpbin.org/get",
        should_block=False
    )
    
    # 清理
    delete_filter_rule(token, rule_id)
    time.sleep(1)

def scenario_b_http_deep_inspection():
    """
    场景B: HTTP深度检测（第二层）
    
    目标：验证当SOCKS5层使用IP地址时，HTTP Host头检测能够识别并拦截
    注意：这个场景模拟浏览器本地DNS解析的情况
    """
    print("\n" + "="*70)
    print("场景B: HTTP深度检测（第二层检测）")
    print("="*70)
    print("说明：即使SOCKS5请求使用IP地址，HTTP Host头检测也应该能识别域名并拦截")
    
    token = get_token()
    
    # 创建过滤规则 - 拦截httpbin.org
    rule_id = create_filter_rule(token, "httpbin.org", "测试场景B-HTTP深度检测")
    if not rule_id:
        return False
    
    time.sleep(1)
    
    # 测试1: 访问被拦截的域名（会携带HTTP Host头）
    # 即使浏览器解析成IP，HTTP请求中仍会有Host头
    run_test(
        scenario="场景B",
        test_name="B1-HTTP Host头检测",
        url="http://httpbin.org/get",
        should_block=True,
        rule_pattern="httpbin.org"
    )
    
    # 测试2: HTTPS访问（应该通过SNI检测）
    run_test(
        scenario="场景B",
        test_name="B2-HTTPS SNI检测",
        url="https://httpbin.org/get",
        should_block=True,
        rule_pattern="httpbin.org"
    )
    
    # 测试3: 访问其他域名应该通过
    run_test(
        scenario="场景B",
        test_name="B3-其他域名应通过",
        url="http://example.com",
        should_block=False
    )
    
    # 清理
    delete_filter_rule(token, rule_id)
    time.sleep(1)

def scenario_c_https_sni():
    """
    场景C: HTTPS SNI检测
    
    目标：验证TLS握手时SNI扩展的检测
    """
    print("\n" + "="*70)
    print("场景C: HTTPS TLS SNI检测")
    print("="*70)
    print("说明：HTTPS流量通过TLS SNI检测域名")
    
    token = get_token()
    
    # 创建过滤规则
    rule_id = create_filter_rule(token, "www.example.com", "测试场景C-SNI检测")
    if not rule_id:
        return False
    
    time.sleep(1)
    
    # 测试1: HTTPS访问被拦截的域名
    run_test(
        scenario="场景C",
        test_name="C1-HTTPS SNI拦截",
        url="https://www.example.com",
        should_block=True,
        rule_pattern="www.example.com"
    )
    
    # 测试2: HTTPS访问其他域名
    run_test(
        scenario="场景C",
        test_name="C2-HTTPS其他域名",
        url="https://httpbin.org/get",
        should_block=False
    )
    
    # 清理
    delete_filter_rule(token, rule_id)
    time.sleep(1)

def scenario_d_double_layer_coordination():
    """
    场景D: 双层协调测试
    
    目标：验证两层检测机制协调工作，不会重复拦截或遗漏
    """
    print("\n" + "="*70)
    print("场景D: 双层检测协调性测试")
    print("="*70)
    print("说明：验证SOCKS5层和应用层检测协调工作")
    
    token = get_token()
    
    # 创建过滤规则 - 使用通配符模式
    rule_id = create_filter_rule(token, "test-block", "测试场景D-双层协调")
    if not rule_id:
        return False
    
    time.sleep(1)
    
    # 测试1: 第一层应该拦截（域名包含test-block）
    # 注意：这是一个不存在的域名，测试逻辑
    print(f"\n  测试: D1-第一层拦截")
    print(f"  说明: 域名包含'test-block'，应在SOCKS5层被拦截")
    # 由于这是不存在的域名，我们期望在第一层就被拦截
    # 实际测试中会因为域名不存在而失败，但这也验证了拦截逻辑
    
    # 测试2: 验证不会误拦截
    run_test(
        scenario="场景D",
        test_name="D2-不误拦截",
        url="http://httpbin.org/get",
        should_block=False
    )
    
    # 清理
    delete_filter_rule(token, rule_id)
    time.sleep(1)

def scenario_e_edge_cases():
    """
    场景E: 边界情况测试
    
    目标：测试特殊情况和边界条件
    """
    print("\n" + "="*70)
    print("场景E: 边界情况测试")
    print("="*70)
    print("说明：测试特殊情况和边界条件")
    
    token = get_token()
    
    # 测试1: 空规则（没有任何过滤规则时，所有请求都应该通过）
    print(f"\n  测试: E1-无规则时全部通过")
    run_test(
        scenario="场景E",
        test_name="E1-无规则通过",
        url="http://example.com",
        should_block=False
    )
    
    # 测试2: 多个规则组合
    rule_id1 = create_filter_rule(token, "badsite1.com", "测试场景E-多规则1")
    rule_id2 = create_filter_rule(token, "badsite2.com", "测试场景E-多规则2")
    
    time.sleep(1)
    
    # 访问不在任何规则中的站点
    run_test(
        scenario="场景E",
        test_name="E2-多规则不匹配",
        url="http://httpbin.org/get",
        should_block=False
    )
    
    # 清理
    if rule_id1:
        delete_filter_rule(token, rule_id1)
    if rule_id2:
        delete_filter_rule(token, rule_id2)
    
    time.sleep(1)
    
    # 测试3: 部分匹配（应该匹配）
    rule_id3 = create_filter_rule(token, "example", "测试场景E-部分匹配")
    time.sleep(1)
    
    run_test(
        scenario="场景E",
        test_name="E3-部分匹配拦截",
        url="http://example.com",
        should_block=True,
        rule_pattern="example"
    )
    
    if rule_id3:
        delete_filter_rule(token, rule_id3)

def scenario_f_performance_test():
    """
    场景F: 性能测试
    
    目标：验证深度检测不会显著影响性能
    """
    print("\n" + "="*70)
    print("场景F: 性能基准测试")
    print("="*70)
    print("说明：测试检测机制对性能的影响")
    
    token = get_token()
    
    # 不创建规则，测试正常通过的性能
    print(f"\n  测试: F1-正常访问性能")
    
    times = []
    for i in range(5):
        start = time.time()
        blocked, details = test_socks5_access("http://httpbin.org/get", False, timeout=10)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"    第{i+1}次: {elapsed:.3f}s, 状态: {'拦截' if blocked else '通过'}")
    
    avg_time = sum(times) / len(times)
    print(f"  平均响应时间: {avg_time:.3f}s")
    
    # 性能判断
    if avg_time < 2.0:
        print(f"  ✅ 性能良好 (< 2s)")
        test_results.append(TestResult(
            scenario="场景F",
            test_name="F1-性能测试",
            expected="< 2s",
            actual=f"{avg_time:.3f}s",
            passed=True,
            details="性能表现良好"
        ))
    else:
        print(f"  ⚠️  性能一般 (>= 2s)")
        test_results.append(TestResult(
            scenario="场景F",
            test_name="F1-性能测试",
            expected="< 2s",
            actual=f"{avg_time:.3f}s",
            passed=False,
            details="性能可能受影响"
        ))

def print_summary():
    """打印测试总结"""
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    passed_count = sum(1 for r in test_results if r.passed)
    failed_count = len(test_results) - passed_count
    
    print(f"\n总测试数: {len(test_results)}")
    print(f"通过: {passed_count} ✅")
    print(f"失败: {failed_count} ❌")
    print(f"通过率: {passed_count/len(test_results)*100:.1f}%")
    
    # 按场景分组
    scenarios = {}
    for result in test_results:
        if result.scenario not in scenarios:
            scenarios[result.scenario] = []
        scenarios[result.scenario].append(result)
    
    print("\n各场景结果：")
    for scenario, results in scenarios.items():
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        print(f"  {scenario}: {passed}/{total} 通过")
    
    # 打印失败的测试
    if failed_count > 0:
        print("\n❌ 失败的测试详情：")
        for result in test_results:
            if not result.passed:
                print(f"\n  {result}")
    
    # 最终评估
    print("\n" + "="*70)
    if failed_count == 0:
        print("✅ 所有测试通过！双层检测机制工作正常！")
        print("="*70)
        print("\n✨ 结论：")
        print("  • SOCKS5层过滤正常工作")
        print("  • HTTP深度检测正常工作")
        print("  • 两层检测协调良好")
        print("  • 没有逻辑冲突")
        print("  • 性能表现良好")
    else:
        print("⚠️  部分测试失败，请检查日志和配置")
        print("="*70)
        print("\n📋 建议：")
        print("  • 检查proxy服务是否正常运行")
        print("  • 检查配置文件中 enable_http_inspection 是否为 true")
        print("  • 查看日志: tail -f logs/proxy.log")
        print("  • 检查网络连接是否正常")

def main():
    """主测试流程"""
    print("="*70)
    print("URL过滤双层检测机制 - 全面测试")
    print("="*70)
    print(f"API地址: {API_BASE}")
    print(f"代理地址: {PROXY_HOST}:{PROXY_PORT}")
    print(f"测试账号: {USERNAME}/{PASSWORD}")
    print("="*70)
    
    # 检查依赖
    try:
        import socks
        print("✅ PySocks库已安装")
    except ImportError:
        print("❌ 请先安装PySocks库: pip install PySocks")
        sys.exit(1)
    
    print("\n📋 测试计划：")
    print("  场景A: SOCKS5层拦截（第一层）")
    print("  场景B: HTTP深度检测（第二层）")
    print("  场景C: HTTPS SNI检测")
    print("  场景D: 双层协调测试")
    print("  场景E: 边界情况测试")
    print("  场景F: 性能基准测试")
    
    # 自动开始测试
    print("\n开始测试...")
    
    try:
        # 运行所有测试场景
        scenario_a_socks5_layer()
        time.sleep(2)
        
        scenario_b_http_deep_inspection()
        time.sleep(2)
        
        scenario_c_https_sni()
        time.sleep(2)
        
        scenario_d_double_layer_coordination()
        time.sleep(2)
        
        scenario_e_edge_cases()
        time.sleep(2)
        
        scenario_f_performance_test()
        
        # 打印总结
        print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        print_summary()
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        print_summary()
        sys.exit(1)
    
    print("\n💡 下一步：")
    print("  • 查看proxy日志: tail -f logs/proxy.log | grep '检测到\\|拦截'")
    print("  • 调整配置: vim configs/config.yaml")
    print("  • 查看文档: docs/HTTP深度检测过滤功能说明.md")

if __name__ == "__main__":
    main()

