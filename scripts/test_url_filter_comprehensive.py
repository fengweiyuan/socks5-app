#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL过滤功能综合测试
测试各种场景和边界情况
"""

import pymysql
import socks
import socket
import time
import subprocess
import sys
from datetime import datetime

# 配置
PROXY_HOST = "localhost"
PROXY_PORT = 1082
TEST_USER = "testuser"
TEST_PASSWORD = "testpass"

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db',
    'charset': 'utf8mb4'
}


class URLFilterTester:
    def __init__(self):
        self.test_results = []
        self.filter_ids = []
        
    def print_section(self, title, level=1):
        """打印分隔标题"""
        if level == 1:
            print("\n" + "="*80)
            print(f"  {title}")
            print("="*80)
        else:
            print(f"\n{title}")
            print("-"*80)
    
    def create_filter(self, pattern, description):
        """创建过滤规则"""
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        sql = """
            INSERT INTO url_filters (pattern, type, description, enabled, created_at, updated_at)
            VALUES (%s, 'block', %s, 1, NOW(), NOW())
        """
        cursor.execute(sql, (pattern, description))
        conn.commit()
        filter_id = cursor.lastrowid
        cursor.close()
        conn.close()
        self.filter_ids.append(filter_id)
        return filter_id
    
    def clear_filters(self):
        """清空所有过滤规则"""
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM url_filters")
        conn.commit()
        cursor.close()
        conn.close()
        self.filter_ids = []
    
    def test_access(self, target, port=80, timeout=5):
        """测试访问"""
        try:
            socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, 
                                   username=TEST_USER, password=TEST_PASSWORD)
            socket.socket = socks.socksocket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((target, port))
            sock.close()
            return True, None
        except Exception as e:
            return False, str(type(e).__name__)
        finally:
            import importlib
            importlib.reload(socket)
    
    def get_filter_logs(self, lines=100):
        """获取URL过滤日志"""
        try:
            result = subprocess.run(
                ['tail', '-n', str(lines), 'logs/proxy.log'],
                capture_output=True,
                text=True,
                cwd='/Users/fwy/code/pub/socks5-app'
            )
            logs = [line for line in result.stdout.split('\n') if 'URL过滤: 阻止访问' in line]
            return logs
        except:
            return []
    
    def record_result(self, scenario, test_name, expected, actual, passed):
        """记录测试结果"""
        self.test_results.append({
            'scenario': scenario,
            'test': test_name,
            'expected': expected,
            'actual': actual,
            'passed': passed
        })
    
    def test_scenario_1(self):
        """场景1: 单个规则精确匹配"""
        self.print_section("场景1: 单个规则精确匹配")
        
        print("\n目的: 验证单个精确的域名过滤规则")
        
        # 清空并创建规则
        self.clear_filters()
        filter_id = self.create_filter("baidu.com", "场景1: 阻止百度")
        print(f"✓ 创建规则: Pattern='baidu.com'")
        time.sleep(1)
        
        # 测试
        tests = [
            ("baidu.com", False, "应该被阻止"),
            ("www.baidu.com", False, "子域名应该被阻止"),
            ("google.com", True, "其他域名应该通过"),
            ("163.com", True, "其他域名应该通过"),
        ]
        
        for target, expected, desc in tests:
            actual, error = self.test_access(target)
            passed = (actual == expected)
            status = "✓" if passed else "✗"
            print(f"{status} {target:20s} → {'通过' if actual else '阻止':8s} ({desc})")
            self.record_result("场景1", target, expected, actual, passed)
        
        # 检查日志
        time.sleep(0.5)
        logs = self.get_filter_logs()
        baidu_logs = [log for log in logs if 'baidu.com' in log]
        print(f"\n日志: 找到 {len(baidu_logs)} 条baidu.com相关日志")
        
        self.clear_filters()
    
    def test_scenario_2(self):
        """场景2: 多个规则同时生效"""
        self.print_section("场景2: 多个规则同时生效")
        
        print("\n目的: 验证多条规则可以同时工作")
        
        # 创建多个规则
        self.clear_filters()
        rules = [
            ("facebook.com", "阻止Facebook"),
            ("twitter.com", "阻止Twitter"),
            ("youtube.com", "阻止YouTube"),
        ]
        
        for pattern, desc in rules:
            self.create_filter(pattern, desc)
            print(f"✓ 创建规则: Pattern='{pattern}'")
        
        time.sleep(1)
        
        # 测试
        tests = [
            ("facebook.com", False, "应该被阻止"),
            ("twitter.com", False, "应该被阻止"),
            ("youtube.com", False, "应该被阻止"),
            ("google.com", True, "应该通过"),
            ("163.com", True, "应该通过"),
        ]
        
        for target, expected, desc in tests:
            actual, error = self.test_access(target)
            passed = (actual == expected)
            status = "✓" if passed else "✗"
            print(f"{status} {target:20s} → {'通过' if actual else '阻止':8s} ({desc})")
            self.record_result("场景2", target, expected, actual, passed)
        
        self.clear_filters()
    
    def test_scenario_3(self):
        """场景3: 危险的宽泛Pattern"""
        self.print_section("场景3: 危险的宽泛Pattern (警告测试)")
        
        print("\n⚠️  警告: 这个场景测试过于宽泛的pattern，可能会阻止大量网站")
        print("目的: 演示不当配置的影响")
        
        # 测试宽泛的pattern
        dangerous_patterns = [
            ("com", "太宽泛，会阻止所有.com域名"),
            (".", "极度危险，会阻止所有域名"),
        ]
        
        for pattern, warning in dangerous_patterns:
            print(f"\n--- 测试Pattern: '{pattern}' ---")
            print(f"⚠️  {warning}")
            
            self.clear_filters()
            self.create_filter(pattern, f"危险测试: {pattern}")
            time.sleep(1)
            
            # 测试多个网站
            test_sites = ["google.com", "baidu.com", "163.com"]
            blocked_count = 0
            
            for site in test_sites:
                actual, _ = self.test_access(site, timeout=3)
                if not actual:
                    blocked_count += 1
                print(f"  {site}: {'通过' if actual else '被阻止'}")
            
            print(f"结果: {blocked_count}/{len(test_sites)} 个网站被阻止")
            
            if blocked_count == len(test_sites):
                print("⚠️  警告: 此Pattern阻止了所有测试网站！")
        
        self.clear_filters()
    
    def test_scenario_4(self):
        """场景4: 内网地址测试"""
        self.print_section("场景4: 内网地址不受影响")
        
        print("\n目的: 验证过滤规则不会影响内网访问")
        
        # 创建规则阻止baidu.com
        self.clear_filters()
        self.create_filter("baidu.com", "阻止百度")
        print("✓ 创建规则: Pattern='baidu.com'")
        time.sleep(1)
        
        # 测试内网地址
        # 注意: 这些地址可能无法实际连接，但应该不会被过滤规则阻止
        internal_addresses = [
            "192.168.1.1",
            "10.0.0.1", 
            "172.16.0.1",
            "127.0.0.1",
            "localhost",
        ]
        
        print("\n内网地址测试（即使连接失败，也不应该是被过滤阻止）:")
        for addr in internal_addresses:
            actual, error = self.test_access(addr, timeout=2)
            # 内网地址可能连接失败，但不应该是因为过滤规则
            status = "✓" if error != "GeneralProxyError" else "✗"
            print(f"{status} {addr:20s} → 错误类型: {error if error else 'None'}")
        
        # 验证baidu.com仍然被阻止
        print("\n验证过滤规则仍然生效:")
        actual, error = self.test_access("baidu.com")
        print(f"{'✓' if not actual else '✗'} baidu.com → {'被阻止' if not actual else '未被阻止'}")
        
        self.clear_filters()
    
    def test_scenario_5(self):
        """场景5: 部分匹配测试"""
        self.print_section("场景5: 部分字符串匹配")
        
        print("\n目的: 验证Pattern的匹配行为（使用strings.Contains）")
        
        # 创建规则
        self.clear_filters()
        self.create_filter("book", "阻止包含book的域名")
        print("✓ 创建规则: Pattern='book'")
        time.sleep(1)
        
        # 测试
        tests = [
            ("facebook.com", False, "包含'book'，应该被阻止"),
            ("booking.com", False, "包含'book'，应该被阻止"),
            ("google.com", True, "不包含'book'，应该通过"),
            ("baidu.com", True, "不包含'book'，应该通过"),
        ]
        
        for target, expected, desc in tests:
            actual, error = self.test_access(target)
            passed = (actual == expected)
            status = "✓" if passed else "✗"
            print(f"{status} {target:20s} → {'通过' if actual else '阻止':8s} ({desc})")
            self.record_result("场景5", target, expected, actual, passed)
        
        self.clear_filters()
    
    def test_scenario_6(self):
        """场景6: 日志完整性验证"""
        self.print_section("场景6: 日志完整性验证")
        
        print("\n目的: 验证日志包含所有必要信息")
        
        # 创建规则
        self.clear_filters()
        filter_id = self.create_filter("test-unique-domain.com", "专门用于日志测试")
        print(f"✓ 创建规则: ID={filter_id}, Pattern='test-unique-domain.com'")
        time.sleep(1)
        
        # 尝试访问
        print("\n尝试访问被阻止的域名...")
        self.test_access("test-unique-domain.com")
        time.sleep(1)
        
        # 检查日志
        logs = self.get_filter_logs(50)
        target_logs = [log for log in logs if 'test-unique-domain.com' in log]
        
        if target_logs:
            print(f"\n✓ 找到 {len(target_logs)} 条相关日志")
            log = target_logs[-1]  # 最新的一条
            
            print("\n日志内容:")
            print(f"  {log}")
            
            print("\n日志完整性检查:")
            checks = [
                ("用户:", "包含用户信息"),
                ("ID:", "包含用户ID"),
                ("目标地址:", "包含目标地址"),
                ("匹配规则:", "包含规则信息"),
                ("Pattern:", "包含匹配模式"),
                ("描述:", "包含规则描述"),
                ("test-unique-domain.com", "包含正确的域名"),
                (str(filter_id), "包含正确的规则ID"),
                ("专门用于日志测试", "包含完整描述"),
            ]
            
            all_passed = True
            for keyword, desc in checks:
                found = keyword in log
                status = "✓" if found else "✗"
                print(f"  {status} {desc}")
                if not found:
                    all_passed = False
            
            if all_passed:
                print("\n✅ 日志完整性检查通过")
            else:
                print("\n⚠️  日志信息不完整")
        else:
            print("\n✗ 未找到相关日志")
        
        self.clear_filters()
    
    def test_scenario_7(self):
        """场景7: 边界情况测试"""
        self.print_section("场景7: 边界情况测试")
        
        print("\n目的: 测试各种边界情况")
        
        # 测试1: 空Pattern（如果数据库允许）
        print("\n--- 测试1: 特殊字符Pattern ---")
        self.clear_filters()
        special_patterns = [
            (".", "单个点"),
            ("-", "单个横杠"),
            ("_", "单个下划线"),
        ]
        
        for pattern, desc in special_patterns:
            try:
                self.create_filter(pattern, f"边界测试: {desc}")
                print(f"✓ 创建Pattern='{pattern}' ({desc})")
            except Exception as e:
                print(f"✗ 创建Pattern='{pattern}'失败: {e}")
        
        time.sleep(1)
        
        # 测试访问
        test_sites = ["google.com", "baidu.com"]
        print("\n测试访问:")
        for site in test_sites:
            actual, _ = self.test_access(site, timeout=3)
            print(f"  {site}: {'通过' if actual else '被阻止'}")
        
        self.clear_filters()
    
    def test_scenario_8(self):
        """场景8: 性能测试（多规则）"""
        self.print_section("场景8: 性能测试")
        
        print("\n目的: 测试大量规则时的性能")
        
        # 创建多个规则
        self.clear_filters()
        num_rules = 50
        print(f"\n创建 {num_rules} 条过滤规则...")
        
        start_time = time.time()
        for i in range(num_rules):
            self.create_filter(f"blocked-domain-{i}.com", f"性能测试规则 {i}")
        create_time = time.time() - start_time
        print(f"✓ 创建完成，耗时: {create_time:.2f}秒")
        
        time.sleep(1)
        
        # 测试访问性能
        print("\n测试访问性能:")
        
        # 测试1: 访问被阻止的域名
        start_time = time.time()
        self.test_access("blocked-domain-25.com", timeout=3)
        blocked_time = time.time() - start_time
        print(f"  访问被阻止的域名: {blocked_time:.3f}秒")
        
        # 测试2: 访问允许的域名
        start_time = time.time()
        self.test_access("allowed-domain.com", timeout=3)
        allowed_time = time.time() - start_time
        print(f"  访问允许的域名: {allowed_time:.3f}秒")
        
        # 性能评估
        print(f"\n性能分析:")
        print(f"  规则数量: {num_rules}")
        print(f"  被阻止请求耗时: {blocked_time:.3f}秒")
        print(f"  允许请求耗时: {allowed_time:.3f}秒")
        
        if blocked_time < 1.0 and allowed_time < 1.0:
            print(f"  ✓ 性能良好")
        else:
            print(f"  ⚠️  性能需要优化")
        
        self.clear_filters()
    
    def test_scenario_9(self):
        """场景9: 真实世界常见网站"""
        self.print_section("场景9: 真实世界常见网站过滤")
        
        print("\n目的: 测试常见的网站过滤场景")
        
        # 创建真实的过滤规则
        self.clear_filters()
        real_world_rules = [
            ("facebook.com", "公司政策: 禁止访问社交媒体"),
            ("twitter.com", "公司政策: 禁止访问社交媒体"),
            ("youtube.com", "带宽管理: 限制视频网站"),
            ("netflix.com", "带宽管理: 限制视频网站"),
            ("pornhub.com", "内容过滤: 禁止成人内容"),
        ]
        
        print("\n创建真实场景的过滤规则:")
        for pattern, desc in real_world_rules:
            self.create_filter(pattern, desc)
            print(f"  ✓ {pattern:20s} - {desc}")
        
        time.sleep(1)
        
        # 测试访问
        print("\n测试访问:")
        test_cases = [
            # 应该被阻止的
            ("facebook.com", False, "社交媒体"),
            ("twitter.com", False, "社交媒体"),
            ("youtube.com", False, "视频网站"),
            # 应该允许的
            ("google.com", True, "搜索引擎"),
            ("github.com", True, "开发工具"),
            ("stackoverflow.com", True, "技术网站"),
        ]
        
        passed_count = 0
        for target, expected, category in test_cases:
            actual, _ = self.test_access(target)
            passed = (actual == expected)
            if passed:
                passed_count += 1
            status = "✓" if passed else "✗"
            result = "通过" if actual else "阻止"
            print(f"{status} {target:25s} → {result:8s} ({category})")
        
        print(f"\n通过率: {passed_count}/{len(test_cases)}")
        
        # 检查日志
        time.sleep(0.5)
        logs = self.get_filter_logs(100)
        blocked_sites = {}
        for log in logs:
            for pattern, desc in real_world_rules:
                if pattern in log:
                    blocked_sites[pattern] = blocked_sites.get(pattern, 0) + 1
        
        if blocked_sites:
            print("\n各规则阻止次数:")
            for site, count in blocked_sites.items():
                print(f"  {site:20s}: {count} 次")
        
        self.clear_filters()
    
    def print_summary(self):
        """打印测试总结"""
        self.print_section("测试总结")
        
        if not self.test_results:
            print("\n没有详细的测试结果记录")
            return
        
        # 按场景分组统计
        scenarios = {}
        for result in self.test_results:
            scenario = result['scenario']
            if scenario not in scenarios:
                scenarios[scenario] = {'total': 0, 'passed': 0}
            scenarios[scenario]['total'] += 1
            if result['passed']:
                scenarios[scenario]['passed'] += 1
        
        print("\n各场景通过率:")
        for scenario, stats in scenarios.items():
            rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = "✓" if rate == 100 else "⚠️"
            print(f"  {status} {scenario}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # 总体统计
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n总体结果:")
        print(f"  总测试数: {total}")
        print(f"  通过数: {passed}")
        print(f"  失败数: {total - passed}")
        print(f"  通过率: {rate:.1f}%")
        
        if rate == 100:
            print("\n🎉 所有测试通过！")
        elif rate >= 80:
            print("\n✓ 大部分测试通过")
        else:
            print("\n⚠️  存在较多失败的测试")


def main():
    """主函数"""
    print("="*80)
    print("  URL过滤功能综合测试")
    print("="*80)
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = URLFilterTester()
    
    try:
        # 运行所有测试场景
        tester.test_scenario_1()   # 单个规则
        tester.test_scenario_2()   # 多个规则
        tester.test_scenario_3()   # 危险的宽泛Pattern
        tester.test_scenario_4()   # 内网地址
        tester.test_scenario_5()   # 部分匹配
        tester.test_scenario_6()   # 日志完整性
        tester.test_scenario_7()   # 边界情况
        tester.test_scenario_8()   # 性能测试
        tester.test_scenario_9()   # 真实场景
        
        # 打印总结
        tester.print_summary()
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 确保清理
        tester.clear_filters()
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*80)
    print("  测试完成")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

