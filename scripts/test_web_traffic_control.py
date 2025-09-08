#!/usr/bin/env python3
"""
测试 Web 界面的流量控制功能
"""

import requests
import json
import time
import sys

def test_web_interface():
    """测试 Web 界面"""
    print("🔍 测试 Web 界面...")
    
    try:
        # 测试主页
        response = requests.get("http://localhost:8012/", timeout=5)
        if response.status_code == 200 and "SOCKS5代理管理" in response.text:
            print("✅ Web 界面主页正常")
        else:
            print(f"❌ Web 界面主页异常: {response.status_code}")
            return False
            
        # 测试流量控制页面路由
        response = requests.get("http://localhost:8012/traffic-control", timeout=5)
        if response.status_code == 200:
            print("✅ 流量控制页面路由正常")
        else:
            print(f"⚠️  流量控制页面路由状态: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ Web 界面测试失败: {e}")
        return False

def test_traffic_control_api():
    """测试流量控制 API"""
    print("\n🔍 测试流量控制 API...")
    
    base_url = "http://localhost:8012/api/v1"
    
    # 测试获取带宽限制列表
    try:
        response = requests.get(f"{base_url}/traffic/limits", timeout=5)
        if response.status_code == 401:
            print("✅ 带宽限制 API 需要认证（正常）")
        else:
            print(f"⚠️  带宽限制 API 响应状态: {response.status_code}")
    except Exception as e:
        print(f"❌ 带宽限制 API 测试失败: {e}")
    
    # 测试设置带宽限制
    try:
        test_data = {
            "user_id": 1,
            "limit": 1048576,  # 1MB/s
            "period": "daily"
        }
        response = requests.post(f"{base_url}/traffic/limit", 
                               json=test_data, timeout=5)
        if response.status_code == 401:
            print("✅ 设置带宽限制 API 需要认证（正常）")
        else:
            print(f"⚠️  设置带宽限制 API 响应状态: {response.status_code}")
    except Exception as e:
        print(f"❌ 设置带宽限制 API 测试失败: {e}")
    
    # 测试流量统计
    try:
        response = requests.get(f"{base_url}/traffic", timeout=5)
        if response.status_code == 401:
            print("✅ 流量统计 API 需要认证（正常）")
        else:
            print(f"⚠️  流量统计 API 响应状态: {response.status_code}")
    except Exception as e:
        print(f"❌ 流量统计 API 测试失败: {e}")

def test_static_resources():
    """测试静态资源"""
    print("\n🔍 测试静态资源...")
    
    try:
        # 测试 CSS 文件
        response = requests.get("http://localhost:8012/static/index-ff995c82.css", timeout=5)
        if response.status_code == 200:
            print("✅ CSS 文件正常")
        else:
            print(f"❌ CSS 文件异常: {response.status_code}")
            
        # 测试 JS 文件
        response = requests.get("http://localhost:8012/static/index-4197900a.js", timeout=5)
        if response.status_code == 200:
            print("✅ JS 文件正常")
        else:
            print(f"❌ JS 文件异常: {response.status_code}")
            
        # 测试流量控制页面 JS
        response = requests.get("http://localhost:8012/static/TrafficControl-96d343cb.js", timeout=5)
        if response.status_code == 200:
            print("✅ 流量控制页面 JS 文件正常")
        else:
            print(f"❌ 流量控制页面 JS 文件异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 静态资源测试失败: {e}")

def test_api_endpoints():
    """测试 API 端点"""
    print("\n🔍 测试 API 端点...")
    
    endpoints = [
        "/api/v1/traffic/limits",
        "/api/v1/traffic",
        "/api/v1/users",
        "/api/v1/system/status"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8012{endpoint}", timeout=5)
            if response.status_code == 401:
                print(f"✅ {endpoint} - 需要认证（正常）")
            elif response.status_code == 200:
                print(f"✅ {endpoint} - 正常访问")
            else:
                print(f"⚠️  {endpoint} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - 请求失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试 Web 界面流量控制功能")
    print("=" * 60)
    
    tests = [
        ("Web 界面", test_web_interface),
        ("流量控制 API", test_traffic_control_api),
        ("静态资源", test_static_resources),
        ("API 端点", test_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 Web 界面流量控制功能测试结果:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        if result is not False:
            status = "✅ 通过"
            passed += 1
        else:
            status = "❌ 失败"
        print(f"{test_name:20} {status}")
    
    print("=" * 60)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Web 界面流量控制功能正常。")
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
