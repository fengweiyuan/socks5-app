#!/usr/bin/env python3
"""
测试 API 端点是否正常工作
"""

import requests
import json
import sys

def test_api_endpoints():
    """测试 API 端点"""
    print("🔍 测试 API 端点...")
    
    endpoints = [
        ("/api/v1/traffic/limits", "GET", "获取带宽限制列表"),
        ("/api/v1/traffic/limit", "POST", "设置带宽限制"),
        ("/api/v1/traffic", "GET", "获取流量统计"),
        ("/api/v1/traffic/realtime", "GET", "获取实时流量数据"),
        ("/api/v1/users", "GET", "获取用户列表"),
        ("/api/v1/system/status", "GET", "获取系统状态"),
    ]
    
    results = []
    
    for endpoint, method, description in endpoints:
        try:
            url = f"http://localhost:8012{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=5)
            
            if response.status_code == 401:
                status = "✅ 需要认证（正常）"
                results.append(True)
            elif response.status_code == 200:
                status = "✅ 正常访问"
                results.append(True)
            elif response.status_code == 404:
                status = "❌ 端点不存在"
                results.append(False)
            else:
                status = f"⚠️  状态码: {response.status_code}"
                results.append(False)
            
            print(f"{description:20} {status}")
            
        except Exception as e:
            print(f"{description:20} ❌ 请求失败: {e}")
            results.append(False)
    
    return results

def test_web_interface():
    """测试 Web 界面"""
    print("\n🌐 测试 Web 界面...")
    
    try:
        response = requests.get("http://localhost:8012/", timeout=5)
        if response.status_code == 200 and "SOCKS5代理管理" in response.text:
            print("✅ Web 界面主页正常")
            return True
        else:
            print(f"❌ Web 界面主页异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web 界面测试失败: {e}")
        return False

def test_traffic_control_page():
    """测试流量控制页面"""
    print("\n📊 测试流量控制页面...")
    
    try:
        response = requests.get("http://localhost:8012/traffic-control", timeout=5)
        if response.status_code == 200:
            print("✅ 流量控制页面路由正常")
            return True
        else:
            print(f"❌ 流量控制页面路由异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 流量控制页面测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 API 端点和 Web 界面")
    print("=" * 60)
    
    # 测试 API 端点
    api_results = test_api_endpoints()
    
    # 测试 Web 界面
    web_result = test_web_interface()
    
    # 测试流量控制页面
    page_result = test_traffic_control_page()
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    api_passed = sum(api_results)
    api_total = len(api_results)
    
    print(f"API 端点测试: {api_passed}/{api_total} 通过")
    print(f"Web 界面测试: {'✅ 通过' if web_result else '❌ 失败'}")
    print(f"流量控制页面: {'✅ 通过' if page_result else '❌ 失败'}")
    
    total_passed = api_passed + (1 if web_result else 0) + (1 if page_result else 0)
    total_tests = api_total + 2
    
    print("=" * 60)
    print(f"总计: {total_passed}/{total_tests} 项测试通过")
    
    if total_passed == total_tests:
        print("🎉 所有测试通过！流量控制功能已成功集成到 Web 界面。")
        print("\n💡 使用说明:")
        print("1. 访问 http://localhost:8012 进入管理界面")
        print("2. 点击左侧菜单 '流量控制' 进入流量控制页面")
        print("3. 可以设置、查看、编辑和删除用户带宽限制")
        print("4. 实时监控流量统计和用户状态")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关服务。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
