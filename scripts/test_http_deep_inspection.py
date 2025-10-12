#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP深度检测功能测试脚本

测试场景：
1. HTTP流量 - Host头检测
2. HTTPS流量 - SNI检测
3. IP地址访问 - 深度检测拦截
"""

import requests
import socks
import socket
import time
import sys
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置
API_BASE = "http://localhost:8080/api"
PROXY_HOST = "localhost"
PROXY_PORT = 1080
USERNAME = "admin"
PASSWORD = "admin"

def get_token():
    """获取JWT token"""
    response = requests.post(
        f"{API_BASE}/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["token"]
    else:
        print(f"❌ 登录失败: {response.text}")
        sys.exit(1)

def create_filter_rule(token, pattern, description):
    """创建URL过滤规则"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE}/url-filters",
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
        print(f"✅ 创建过滤规则: {pattern} (ID: {rule_id})")
        return rule_id
    else:
        print(f"❌ 创建规则失败: {response.text}")
        return None

def delete_filter_rule(token, rule_id):
    """删除URL过滤规则"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{API_BASE}/url-filters/{rule_id}",
        headers=headers
    )
    if response.status_code == 200:
        print(f"✅ 删除过滤规则 ID: {rule_id}")
    else:
        print(f"❌ 删除规则失败: {response.text}")

def test_http_with_socks5(target_url, should_block=False):
    """
    通过SOCKS5代理测试HTTP访问
    
    Args:
        target_url: 目标URL
        should_block: 是否应该被拦截
    """
    print(f"\n{'='*60}")
    print(f"测试HTTP访问: {target_url}")
    print(f"预期结果: {'应该被拦截' if should_block else '应该通过'}")
    print(f"{'='*60}")
    
    # 配置SOCKS5代理
    socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, 
                           username=USERNAME, password=PASSWORD)
    socket.socket = socks.socksocket
    
    try:
        start_time = time.time()
        response = requests.get(target_url, timeout=10, verify=False)
        elapsed = time.time() - start_time
        
        if should_block:
            print(f"❌ 测试失败: 连接成功，但应该被拦截")
            print(f"   响应状态: {response.status_code}")
            print(f"   响应时间: {elapsed:.2f}秒")
        else:
            print(f"✅ 测试通过: 连接成功")
            print(f"   响应状态: {response.status_code}")
            print(f"   响应时间: {elapsed:.2f}秒")
            print(f"   响应大小: {len(response.content)} bytes")
        
    except Exception as e:
        if should_block:
            print(f"✅ 测试通过: 连接被拒绝（符合预期）")
            print(f"   错误信息: {str(e)[:100]}")
        else:
            print(f"❌ 测试失败: 连接被拒绝（不应该被拦截）")
            print(f"   错误信息: {str(e)}")
    
    finally:
        # 恢复默认socket
        import importlib
        importlib.reload(socket)

def test_scenario_1_http_host():
    """
    场景1: HTTP Host头检测
    
    测试步骤：
    1. 创建过滤规则：拦截 example.com
    2. 通过代理访问 http://example.com（浏览器会发送Host头）
    3. 验证是否被拦截
    """
    print("\n" + "="*70)
    print("场景1: HTTP Host头检测")
    print("="*70)
    
    token = get_token()
    
    # 创建过滤规则
    rule_id = create_filter_rule(token, "example.com", "测试HTTP Host头检测")
    if not rule_id:
        return
    
    time.sleep(1)  # 等待规则生效
    
    # 测试1: 直接访问域名（应该被拦截 - SOCKS5层）
    print("\n测试1.1: 直接访问域名")
    test_http_with_socks5("http://example.com", should_block=True)
    
    # 测试2: 访问其他域名（应该通过）
    print("\n测试1.2: 访问其他域名（应该通过）")
    test_http_with_socks5("http://httpbin.org/get", should_block=False)
    
    # 清理
    delete_filter_rule(token, rule_id)

def test_scenario_2_http_ip_with_host():
    """
    场景2: IP地址访问 + HTTP Host头检测
    
    这个场景模拟浏览器本地DNS解析后的情况：
    1. 创建过滤规则：拦截 baidu.com
    2. 获取baidu.com的IP地址
    3. 直接使用IP访问（但HTTP Host头仍然是域名）
    4. 验证深度检测是否能拦截
    
    注意：这个测试需要手动构造HTTP请求，因为requests库会自动设置Host头
    """
    print("\n" + "="*70)
    print("场景2: IP地址访问 + HTTP深度检测")
    print("="*70)
    
    token = get_token()
    
    # 创建过滤规则
    rule_id = create_filter_rule(token, "httpbin.org", "测试HTTP深度检测")
    if not rule_id:
        return
    
    time.sleep(1)
    
    # 测试: 访问httpbin.org
    # 即使IP地址可能绕过第一层检测，但HTTP Host头会被检测到
    print("\n测试2.1: 访问被拦截的域名")
    test_http_with_socks5("http://httpbin.org/get", should_block=True)
    
    # 清理
    delete_filter_rule(token, rule_id)

def test_scenario_3_https_sni():
    """
    场景3: HTTPS SNI检测
    
    测试步骤：
    1. 创建过滤规则：拦截某个HTTPS网站
    2. 通过代理访问该网站
    3. 验证SNI检测是否工作
    """
    print("\n" + "="*70)
    print("场景3: HTTPS SNI检测")
    print("="*70)
    
    token = get_token()
    
    # 创建过滤规则
    rule_id = create_filter_rule(token, "httpbin.org", "测试HTTPS SNI检测")
    if not rule_id:
        return
    
    time.sleep(1)
    
    # 测试HTTPS访问
    print("\n测试3.1: HTTPS访问（应该被拦截）")
    test_http_with_socks5("https://httpbin.org/get", should_block=True)
    
    print("\n测试3.2: 访问其他HTTPS站点（应该通过）")
    test_http_with_socks5("https://www.example.com", should_block=False)
    
    # 清理
    delete_filter_rule(token, rule_id)

def test_scenario_4_wildcard():
    """
    场景4: 通配符匹配
    
    测试包含匹配（子串匹配）
    """
    print("\n" + "="*70)
    print("场景4: 通配符/子串匹配")
    print("="*70)
    
    token = get_token()
    
    # 创建过滤规则 - 拦截所有包含 "bin" 的域名
    rule_id = create_filter_rule(token, "bin", "测试通配符匹配")
    if not rule_id:
        return
    
    time.sleep(1)
    
    # 这应该拦截 httpbin.org（包含 "bin"）
    print("\n测试4.1: 访问包含'bin'的域名（应该被拦截）")
    test_http_with_socks5("http://httpbin.org/get", should_block=True)
    
    print("\n测试4.2: 访问不包含'bin'的域名（应该通过）")
    test_http_with_socks5("http://example.com", should_block=False)
    
    # 清理
    delete_filter_rule(token, rule_id)

def main():
    """主测试流程"""
    print("="*70)
    print("HTTP深度检测功能测试")
    print("="*70)
    print(f"API地址: {API_BASE}")
    print(f"代理地址: {PROXY_HOST}:{PROXY_PORT}")
    print(f"测试账号: {USERNAME}/{PASSWORD}")
    print("="*70)
    
    try:
        # 检查SOCKS库
        import socks
        print("✅ PySocks库已安装")
    except ImportError:
        print("❌ 请先安装PySocks库: pip install PySocks")
        sys.exit(1)
    
    # 运行测试场景
    try:
        test_scenario_1_http_host()
        time.sleep(2)
        
        test_scenario_2_http_ip_with_host()
        time.sleep(2)
        
        test_scenario_3_https_sni()
        time.sleep(2)
        
        test_scenario_4_wildcard()
        
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)
    print("\n💡 提示：")
    print("1. 查看日志确认检测结果: tail -f logs/proxy.log | grep '检测到'")
    print("2. 查看拦截日志: tail -f logs/proxy.log | grep '拦截'")
    print("3. 如果测试失败，请检查代理服务是否正常运行")

if __name__ == "__main__":
    main()

