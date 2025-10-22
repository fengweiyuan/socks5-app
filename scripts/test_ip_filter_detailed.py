#!/usr/bin/env python3
"""
IP黑白名单功能详细测试脚本
测试日期：2025-10-22
"""

import requests
import socks
import socket
import time
import json
from datetime import datetime

# 配置
API_BASE = "http://localhost:8012/api/v1"
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
USERNAME = "admin"
PASSWORD = "%VirWorkSocks!"

class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_header(text):
    print(f"\n{'='*60}")
    print(f"{text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.NC}")

def print_info(text):
    print(f"{Colors.BLUE}{text}{Colors.NC}")

def print_warning(text):
    print(f"{Colors.YELLOW}{text}{Colors.NC}")

class IPFilterTester:
    def __init__(self):
        self.token = None
        self.test_results = []
        
    def login(self):
        """登录获取token"""
        print_info("步骤 1: 登录获取Token")
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={"username": USERNAME, "password": PASSWORD}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                print_success(f"登录成功，Token: {self.token[:20]}...")
                return True
            else:
                print_error(f"登录失败: {response.text}")
                return False
        except Exception as e:
            print_error(f"登录异常: {str(e)}")
            return False
    
    def get_headers(self):
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def clear_all_rules(self):
        """清空所有黑白名单规则"""
        print_info("\n步骤 2: 清空所有规则")
        
        # 清空黑名单
        try:
            response = requests.get(f"{API_BASE}/ip-blacklist", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                blacklist = data.get("blacklist", [])
                for item in blacklist:
                    requests.delete(
                        f"{API_BASE}/ip-blacklist/{item['id']}",
                        headers=self.get_headers()
                    )
                    print(f"  删除黑名单规则 ID: {item['id']} - {item['cidr']}")
        except Exception as e:
            print_error(f"清空黑名单失败: {str(e)}")
        
        # 清空白名单
        try:
            response = requests.get(f"{API_BASE}/ip-whitelist", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                whitelist = data.get("whitelist", [])
                for item in whitelist:
                    requests.delete(
                        f"{API_BASE}/ip-whitelist/{item['id']}",
                        headers=self.get_headers()
                    )
                    print(f"  删除白名单规则 ID: {item['id']} - {item['ip']}")
        except Exception as e:
            print_error(f"清空白名单失败: {str(e)}")
        
        print_success("规则清空完成")
        print_warning("等待5秒让缓存刷新...")
        time.sleep(5)
    
    def add_blacklist(self, cidr, description):
        """添加黑名单规则"""
        try:
            response = requests.post(
                f"{API_BASE}/ip-blacklist",
                headers=self.get_headers(),
                json={
                    "cidr": cidr,
                    "description": description,
                    "enabled": True
                }
            )
            if response.status_code == 201:
                print_success(f"添加黑名单规则: {cidr}")
                return True
            else:
                print_error(f"添加黑名单失败: {response.text}")
                return False
        except Exception as e:
            print_error(f"添加黑名单异常: {str(e)}")
            return False
    
    def add_whitelist(self, ip, description):
        """添加白名单规则"""
        try:
            response = requests.post(
                f"{API_BASE}/ip-whitelist",
                headers=self.get_headers(),
                json={
                    "ip": ip,
                    "description": description,
                    "enabled": True
                }
            )
            if response.status_code == 201:
                print_success(f"添加白名单规则: {ip}")
                return True
            else:
                print_error(f"添加白名单失败: {response.text}")
                return False
        except Exception as e:
            print_error(f"添加白名单异常: {str(e)}")
            return False
    
    def test_socks5_connection(self, target_host, target_port=80):
        """测试SOCKS5代理连接"""
        try:
            # 创建socket并配置为SOCKS5代理
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, username=USERNAME, password=PASSWORD)
            s.settimeout(5)
            
            # 尝试连接
            s.connect((target_host, target_port))
            s.close()
            return True, "连接成功"
        except socks.ProxyConnectionError as e:
            return False, f"代理连接错误: {str(e)}"
        except socks.GeneralProxyError as e:
            return False, f"代理错误: {str(e)}"
        except Exception as e:
            return False, f"连接错误: {str(e)}"
    
    def get_current_rules(self):
        """获取当前规则"""
        print_info("\n当前规则:")
        
        try:
            # 黑名单
            response = requests.get(f"{API_BASE}/ip-blacklist", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                blacklist = data.get("blacklist", [])
                print(f"  黑名单({len(blacklist)}条):")
                for item in blacklist:
                    enabled = "启用" if item.get("enabled") else "禁用"
                    print(f"    [{enabled}] {item.get('cidr')} - {item.get('description')}")
            
            # 白名单
            response = requests.get(f"{API_BASE}/ip-whitelist", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                whitelist = data.get("whitelist", [])
                print(f"  白名单({len(whitelist)}条):")
                for item in whitelist:
                    enabled = "启用" if item.get("enabled") else "禁用"
                    print(f"    [{enabled}] {item.get('ip')} - {item.get('description')}")
        except Exception as e:
            print_error(f"获取规则失败: {str(e)}")
    
    def record_result(self, scenario, test_name, expected, actual):
        """记录测试结果"""
        passed = (expected == actual)
        self.test_results.append({
            "scenario": scenario,
            "test_name": test_name,
            "expected": expected,
            "actual": actual,
            "passed": passed
        })
        
        if passed:
            print_success(f"{test_name}: 符合预期")
        else:
            print_error(f"{test_name}: 不符合预期（期望:{expected}, 实际:{actual}）")
    
    def run_all_tests(self):
        """运行所有测试"""
        
        # 场景1: 无黑白名单
        print_header("场景 1: 无黑白名单（默认全部通过）")
        self.clear_all_rules()
        
        success, msg = self.test_socks5_connection("8.8.8.8", 53)
        self.record_result("场景1", "访问8.8.8.8:53", True, success)
        print(f"  结果: {msg}")
        
        # 场景2: 只有黑名单
        print_header("场景 2: 只有黑名单")
        self.add_blacklist("8.8.8.0/24", "测试-屏蔽Google DNS段")
        time.sleep(5)
        
        success, msg = self.test_socks5_connection("8.8.8.8", 53)
        self.record_result("场景2", "访问黑名单内IP 8.8.8.8", False, success)
        print(f"  结果: {msg}")
        
        success, msg = self.test_socks5_connection("1.1.1.1", 53)
        self.record_result("场景2", "访问非黑名单IP 1.1.1.1", True, success)
        print(f"  结果: {msg}")
        
        # 场景3: 黑名单+白名单赦免
        print_header("场景 3: 黑名单 + 白名单赦免")
        self.add_whitelist("8.8.8.8", "测试-赦免8.8.8.8")
        time.sleep(5)
        
        self.get_current_rules()
        
        success, msg = self.test_socks5_connection("8.8.8.8", 53)
        self.record_result("场景3", "访问被赦免的IP 8.8.8.8", True, success)
        print(f"  结果: {msg}")
        
        success, msg = self.test_socks5_connection("8.8.4.4", 53)
        self.record_result("场景3", "访问同网段未赦免IP 8.8.4.4", False, success)
        print(f"  结果: {msg}")
        
        # 场景4: 单个IP黑名单
        print_header("场景 4: 单个IP黑名单")
        self.clear_all_rules()
        self.add_blacklist("1.1.1.1", "测试-屏蔽单个IP")
        time.sleep(5)
        
        success, msg = self.test_socks5_connection("1.1.1.1", 53)
        self.record_result("场景4", "访问黑名单单个IP 1.1.1.1", False, success)
        print(f"  结果: {msg}")
        
        success, msg = self.test_socks5_connection("1.0.0.1", 53)
        self.record_result("场景4", "访问非黑名单IP 1.0.0.1", True, success)
        print(f"  结果: {msg}")
        
        # 场景5: 只有白名单（不应限制）
        print_header("场景 5: 只有白名单（白名单不应限制访问）")
        self.clear_all_rules()
        self.add_whitelist("8.8.8.8", "测试-仅白名单")
        time.sleep(5)
        
        success, msg = self.test_socks5_connection("8.8.8.8", 53)
        self.record_result("场景5", "访问白名单内IP 8.8.8.8", True, success)
        print(f"  结果: {msg}")
        
        success, msg = self.test_socks5_connection("1.1.1.1", 53)
        self.record_result("场景5", "访问白名单外IP 1.1.1.1", True, success)
        print(f"  结果: {msg} （白名单不应限制）")
        
        # 场景6: 使用0.0.0.0/0实现传统白名单模式
        print_header("场景 6: 使用0.0.0.0/0实现传统白名单模式")
        self.clear_all_rules()
        self.add_blacklist("0.0.0.0/0", "测试-屏蔽所有IP")
        self.add_whitelist("8.8.8.8", "测试-只允许8.8.8.8")
        time.sleep(5)
        
        self.get_current_rules()
        
        success, msg = self.test_socks5_connection("8.8.8.8", 53)
        self.record_result("场景6", "访问白名单内IP 8.8.8.8", True, success)
        print(f"  结果: {msg}")
        
        success, msg = self.test_socks5_connection("1.1.1.1", 53)
        self.record_result("场景6", "访问白名单外IP 1.1.1.1", False, success)
        print(f"  结果: {msg}")
        
    def print_summary(self):
        """打印测试总结"""
        print_header("测试总结")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {passed/total*100:.1f}%\n")
        
        if failed > 0:
            print("失败的测试:")
            for r in self.test_results:
                if not r["passed"]:
                    print(f"  {r['scenario']} - {r['test_name']}")
                    print(f"    期望: {r['expected']}, 实际: {r['actual']}")
        
        # 保存测试报告
        report_file = f"test_ip_filter_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_date": datetime.now().isoformat(),
                "total": total,
                "passed": passed,
                "failed": failed,
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细测试报告已保存到: {report_file}")

def main():
    print_header("IP黑白名单功能详细测试")
    
    # 检查依赖
    try:
        import socks
    except ImportError:
        print_error("缺少PySocks库，请安装: pip3 install PySocks")
        return
    
    tester = IPFilterTester()
    
    # 登录
    if not tester.login():
        print_error("登录失败，测试终止")
        return
    
    # 运行测试
    try:
        tester.run_all_tests()
    except Exception as e:
        print_error(f"测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 打印总结
    tester.print_summary()
    
    # 清理
    print_info("\n清理测试环境...")
    tester.clear_all_rules()
    print_success("测试完成!")

if __name__ == "__main__":
    main()

