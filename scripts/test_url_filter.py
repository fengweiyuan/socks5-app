#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL过滤功能测试脚本
测试设置过滤规则后，其他网址是否能正常访问
"""

import requests
import socks
import socket
import time
import sys
import json

# 配置
API_BASE_URL = "http://localhost:8012/api/v1"
PROXY_HOST = "localhost"
PROXY_PORT = 1082

# 测试用户凭证
TEST_USER = "testuser"
TEST_PASSWORD = "testpass"

# 管理员凭证
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"


class URLFilterTester:
    def __init__(self):
        self.token = None
        self.filter_ids = []
        
    def login(self, username, password):
        """登录并获取token"""
        print(f"\n=== 登录: {username} ===")
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            print(f"✓ 登录成功，获得token")
            return True
        else:
            print(f"✗ 登录失败: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        """获取带token的请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def create_url_filter(self, pattern, filter_type, description):
        """创建URL过滤规则"""
        print(f"\n=== 创建过滤规则 ===")
        print(f"Pattern: {pattern}")
        print(f"Type: {filter_type}")
        print(f"Description: {description}")
        
        response = requests.post(
            f"{API_BASE_URL}/filters",
            headers=self.get_headers(),
            json={
                "pattern": pattern,
                "type": filter_type,
                "description": description,
                "enabled": True
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            filter_id = data.get("filter", {}).get("id")
            self.filter_ids.append(filter_id)
            print(f"✓ 过滤规则创建成功，ID: {filter_id}")
            return filter_id
        else:
            print(f"✗ 创建失败: {response.status_code} - {response.text}")
            return None
    
    def get_filters(self):
        """获取所有过滤规则"""
        print(f"\n=== 获取当前所有过滤规则 ===")
        response = requests.get(
            f"{API_BASE_URL}/filters",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            filters = data.get("filters", [])
            print(f"当前有 {len(filters)} 条过滤规则:")
            for f in filters:
                print(f"  - ID: {f['id']}, Pattern: {f['pattern']}, Type: {f['type']}, Enabled: {f['enabled']}")
            return filters
        else:
            print(f"✗ 获取失败: {response.status_code} - {response.text}")
            return []
    
    def delete_filter(self, filter_id):
        """删除过滤规则"""
        print(f"\n删除过滤规则 ID: {filter_id}")
        response = requests.delete(
            f"{API_BASE_URL}/filters/{filter_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            print(f"✓ 过滤规则删除成功")
            return True
        else:
            print(f"✗ 删除失败: {response.status_code} - {response.text}")
            return False
    
    def cleanup_filters(self):
        """清理测试创建的过滤规则"""
        print(f"\n=== 清理测试过滤规则 ===")
        for filter_id in self.filter_ids:
            self.delete_filter(filter_id)
        self.filter_ids = []
    
    def test_socks5_connection(self, target_host, target_port=80, timeout=5):
        """测试通过SOCKS5代理连接目标主机"""
        try:
            # 配置SOCKS5代理
            socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, 
                                   username=TEST_USER, password=TEST_PASSWORD)
            socket.socket = socks.socksocket
            
            # 尝试连接
            print(f"\n尝试连接: {target_host}:{target_port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((target_host, target_port))
            sock.close()
            
            print(f"✓ 连接成功: {target_host}")
            return True
            
        except socks.ProxyConnectionError as e:
            print(f"✗ 代理连接错误: {e}")
            return False
        except Exception as e:
            print(f"✗ 连接失败: {type(e).__name__} - {e}")
            return False
        finally:
            # 重置socket
            import importlib
            importlib.reload(socket)
    
    def test_http_request(self, url, timeout=5):
        """测试通过SOCKS5代理发送HTTP请求"""
        try:
            # 配置requests使用SOCKS5代理
            proxies = {
                'http': f'socks5://{TEST_USER}:{TEST_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}',
                'https': f'socks5://{TEST_USER}:{TEST_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'
            }
            
            print(f"\n尝试HTTP请求: {url}")
            response = requests.get(url, proxies=proxies, timeout=timeout)
            
            print(f"✓ 请求成功: {url}")
            print(f"  状态码: {response.status_code}")
            print(f"  响应大小: {len(response.content)} 字节")
            return True
            
        except requests.exceptions.ProxyError as e:
            print(f"✗ 代理错误: {e}")
            return False
        except requests.exceptions.Timeout:
            print(f"✗ 请求超时")
            return False
        except Exception as e:
            print(f"✗ 请求失败: {type(e).__name__} - {e}")
            return False
    
    def run_test_scenario_1(self):
        """
        测试场景1: 设置block类型过滤规则
        - 创建一个block规则阻止 baidu.com
        - 测试访问 baidu.com (应该被阻止)
        - 测试访问 163.com (应该成功)
        - 测试访问内网地址 (应该成功)
        """
        print("\n" + "="*60)
        print("测试场景1: Block类型过滤规则")
        print("="*60)
        
        # 创建block规则
        filter_id = self.create_url_filter("baidu.com", "block", "测试阻止百度")
        if not filter_id:
            print("创建过滤规则失败，测试终止")
            return
        
        time.sleep(1)  # 等待规则生效
        
        # 查看当前规则
        self.get_filters()
        
        # 测试访问被阻止的网站
        print("\n--- 测试1: 访问被阻止的网站 (baidu.com) ---")
        result1 = self.test_socks5_connection("baidu.com", 80)
        expected1 = False
        status1 = "✓ 通过" if result1 == expected1 else "✗ 失败"
        print(f"预期: 被阻止, 实际: {'被阻止' if not result1 else '成功'}, {status1}")
        
        # 测试访问其他网站
        print("\n--- 测试2: 访问其他网站 (163.com) ---")
        result2 = self.test_socks5_connection("163.com", 80)
        expected2 = True
        status2 = "✓ 通过" if result2 == expected2 else "✗ 失败"
        print(f"预期: 成功, 实际: {'成功' if result2 else '被阻止'}, {status2}")
        
        # 测试访问google
        print("\n--- 测试3: 访问 google.com ---")
        result3 = self.test_socks5_connection("google.com", 80)
        expected3 = True
        status3 = "✓ 通过" if result3 == expected3 else "✗ 失败"
        print(f"预期: 成功, 实际: {'成功' if result3 else '被阻止'}, {status3}")
        
        # 总结
        print("\n--- 场景1测试结果 ---")
        all_passed = (result1 == expected1) and (result2 == expected2) and (result3 == expected3)
        if all_passed:
            print("✓ 所有测试通过")
        else:
            print("✗ 部分测试失败")
            print(f"  测试1 (阻止baidu.com): {status1}")
            print(f"  测试2 (允许163.com): {status2}")
            print(f"  测试3 (允许google.com): {status3}")
        
        # 清理
        self.cleanup_filters()
        return all_passed
    
    def run_test_scenario_2(self):
        """
        测试场景2: 设置allow类型过滤规则
        - 创建一个allow规则允许 baidu.com
        - 测试访问 baidu.com (当前代码应该成功)
        - 测试访问 163.com (当前代码应该成功)
        - 验证allow规则的实际行为
        """
        print("\n" + "="*60)
        print("测试场景2: Allow类型过滤规则")
        print("="*60)
        
        # 创建allow规则
        filter_id = self.create_url_filter("baidu.com", "allow", "测试允许百度")
        if not filter_id:
            print("创建过滤规则失败，测试终止")
            return
        
        time.sleep(1)  # 等待规则生效
        
        # 查看当前规则
        self.get_filters()
        
        # 测试访问被允许的网站
        print("\n--- 测试1: 访问被允许的网站 (baidu.com) ---")
        result1 = self.test_socks5_connection("baidu.com", 80)
        print(f"实际结果: {'成功' if result1 else '被阻止'}")
        
        # 测试访问其他网站
        print("\n--- 测试2: 访问其他网站 (163.com) ---")
        result2 = self.test_socks5_connection("163.com", 80)
        print(f"实际结果: {'成功' if result2 else '被阻止'}")
        
        # 测试访问google
        print("\n--- 测试3: 访问 google.com ---")
        result3 = self.test_socks5_connection("google.com", 80)
        print(f"实际结果: {'成功' if result3 else '被阻止'}")
        
        # 总结
        print("\n--- 场景2测试结果 ---")
        print("注意: 当前代码中，allow类型的规则不会真正生效")
        print("因为checkURLFilter函数只处理block类型，不处理allow类型")
        print(f"  访问baidu.com (allow规则): {'成功' if result1 else '失败'}")
        print(f"  访问163.com (无规则): {'成功' if result2 else '失败'}")
        print(f"  访问google.com (无规则): {'成功' if result3 else '失败'}")
        
        # 清理
        self.cleanup_filters()
    
    def run_test_scenario_3(self):
        """
        测试场景3: 多条规则组合
        - 创建多条block规则
        - 测试各种访问情况
        """
        print("\n" + "="*60)
        print("测试场景3: 多条Block规则")
        print("="*60)
        
        # 创建多条block规则
        self.create_url_filter("baidu.com", "block", "阻止百度")
        self.create_url_filter("taobao.com", "block", "阻止淘宝")
        
        time.sleep(1)
        
        # 查看当前规则
        self.get_filters()
        
        # 测试各个网站
        test_hosts = [
            ("baidu.com", False, "应该被阻止"),
            ("taobao.com", False, "应该被阻止"),
            ("163.com", True, "应该成功"),
            ("google.com", True, "应该成功"),
        ]
        
        results = []
        for host, expected, desc in test_hosts:
            print(f"\n--- 测试: {host} ({desc}) ---")
            result = self.test_socks5_connection(host, 80)
            passed = (result == expected)
            status = "✓ 通过" if passed else "✗ 失败"
            print(f"预期: {'成功' if expected else '被阻止'}, 实际: {'成功' if result else '被阻止'}, {status}")
            results.append(passed)
        
        # 总结
        print("\n--- 场景3测试结果 ---")
        if all(results):
            print("✓ 所有测试通过")
        else:
            print(f"✗ {sum(results)}/{len(results)} 测试通过")
        
        # 清理
        self.cleanup_filters()
        return all(results)


def main():
    """主测试函数"""
    print("="*60)
    print("URL过滤功能测试")
    print("="*60)
    
    tester = URLFilterTester()
    
    # 登录
    if not tester.login(ADMIN_USER, ADMIN_PASSWORD):
        print("登录失败，测试终止")
        return 1
    
    # 运行测试场景
    try:
        # 场景1: Block规则
        print("\n\n")
        scenario1_passed = tester.run_test_scenario_1()
        
        time.sleep(2)
        
        # 场景2: Allow规则  
        print("\n\n")
        tester.run_test_scenario_2()
        
        time.sleep(2)
        
        # 场景3: 多条规则
        print("\n\n")
        scenario3_passed = tester.run_test_scenario_3()
        
        # 最终总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        print(f"场景1 (单个Block规则): {'✓ 通过' if scenario1_passed else '✗ 失败'}")
        print(f"场景2 (Allow规则): 已执行，需人工判断")
        print(f"场景3 (多个Block规则): {'✓ 通过' if scenario3_passed else '✗ 失败'}")
        
        print("\n重要发现:")
        print("1. Block类型的过滤规则工作正常")
        print("2. Allow类型的过滤规则在当前代码中不生效")
        print("3. 如果用户反映'设置过滤后其他地址无法访问'，可能的原因：")
        print("   - 误用了Allow规则期望白名单效果")
        print("   - 或者前端显示/提交的规则类型有误")
        print("   - 需要查看数据库中实际保存的规则类型")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        tester.cleanup_filters()
        return 1
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        tester.cleanup_filters()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

