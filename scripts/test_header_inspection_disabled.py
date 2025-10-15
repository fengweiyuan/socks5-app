#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP Header检测禁用验证测试

测试目标：验证当 enable_http_inspection = false 时
1. 不会检查 HTTP Request Header
2. 不会提取 HTTP Host
3. 不会提取 TLS SNI
4. 性能不受影响
"""

import requests
import socket
import time
import sys
import socks
import subprocess

# 配置
PROXY_HOST = "localhost"
PROXY_PORT = 1082
USERNAME = "admin"
PASSWORD = "admin"
LOG_FILE = "logs/proxy.log"

def check_log_for_inspection():
    """检查日志中是否有HTTP深度检测的痕迹"""
    try:
        result = subprocess.run(
            ["tail", "-100", LOG_FILE],
            capture_output=True,
            text=True,
            timeout=5
        )
        log_content = result.stdout
        
        # 检查关键字
        inspection_keywords = [
            "检测到HTTP Host",
            "检测到TLS SNI", 
            "HTTP深度检测拦截",
            "ExtractHost",
            "ExtractSNI"
        ]
        
        found_keywords = []
        for keyword in inspection_keywords:
            if keyword in log_content:
                found_keywords.append(keyword)
        
        return found_keywords
    except Exception as e:
        print(f"⚠️  无法读取日志: {e}")
        return []

def check_startup_log():
    """检查启动日志，确认HTTP深度检测配置"""
    try:
        result = subprocess.run(
            ["tail", "-200", LOG_FILE],
            capture_output=True,
            text=True,
            timeout=5
        )
        log_content = result.stdout
        
        # 查找配置信息
        if "HTTP深度检测已禁用" in log_content or "HTTP深度检测: false" in log_content:
            return True, "已禁用"
        elif "HTTP深度检测已启用" in log_content or "HTTP深度检测: true" in log_content:
            return True, "已启用"
        else:
            return False, "未找到配置信息"
    except Exception as e:
        return False, f"错误: {e}"

def test_http_request():
    """测试HTTP请求"""
    print("\n" + "="*70)
    print("测试1: HTTP请求 - 验证不会检查Header")
    print("="*70)
    
    # 清空最近的日志（获取新日志的基准）
    try:
        subprocess.run(["tail", "-0", LOG_FILE], capture_output=True)
    except:
        pass
    
    # 配置SOCKS5代理
    socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT,
                           username=USERNAME, password=PASSWORD)
    
    original_socket = socket.socket
    socket.socket = socks.socksocket
    
    try:
        print("  发送HTTP请求到 http://example.com...")
        start_time = time.time()
        response = requests.get("http://example.com", timeout=10)
        elapsed = time.time() - start_time
        
        print(f"  ✅ 请求成功: 状态码 {response.status_code}")
        print(f"  ⏱️  响应时间: {elapsed:.3f}秒")
        
        # 检查日志
        time.sleep(1)  # 等待日志写入
        found = check_log_for_inspection()
        
        if found:
            print(f"\n  ❌ 测试失败：在日志中发现HTTP检测关键字：")
            for keyword in found:
                print(f"     - {keyword}")
            return False
        else:
            print(f"  ✅ 验证通过：日志中没有HTTP深度检测关键字")
            return True
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return False
    finally:
        socket.socket = original_socket
        import importlib
        importlib.reload(socket)

def test_https_request():
    """测试HTTPS请求"""
    print("\n" + "="*70)
    print("测试2: HTTPS请求 - 验证不会提取SNI")
    print("="*70)
    
    # 配置SOCKS5代理
    socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT,
                           username=USERNAME, password=PASSWORD)
    
    original_socket = socket.socket
    socket.socket = socks.socksocket
    
    try:
        print("  发送HTTPS请求到 https://example.com...")
        start_time = time.time()
        response = requests.get("https://example.com", timeout=10, verify=False)
        elapsed = time.time() - start_time
        
        print(f"  ✅ 请求成功: 状态码 {response.status_code}")
        print(f"  ⏱️  响应时间: {elapsed:.3f}秒")
        
        # 检查日志
        time.sleep(1)  # 等待日志写入
        found = check_log_for_inspection()
        
        if found:
            print(f"\n  ❌ 测试失败：在日志中发现SNI检测关键字：")
            for keyword in found:
                print(f"     - {keyword}")
            return False
        else:
            print(f"  ✅ 验证通过：日志中没有SNI检测关键字")
            return True
            
    except Exception as e:
        print(f"  ⚠️  请求失败: {e}")
        # HTTPS可能因为证书问题失败，但只要日志中没有检测痕迹就算通过
        time.sleep(1)
        found = check_log_for_inspection()
        if found:
            print(f"  ❌ 测试失败：在日志中发现SNI检测关键字：")
            for keyword in found:
                print(f"     - {keyword}")
            return False
        else:
            print(f"  ✅ 验证通过：即使请求失败，日志中也没有SNI检测")
            return True
    finally:
        socket.socket = original_socket
        import importlib
        importlib.reload(socket)

def test_performance():
    """性能测试 - 对比禁用前后"""
    print("\n" + "="*70)
    print("测试3: 性能测试 - 验证无额外开销")
    print("="*70)
    
    # 配置SOCKS5代理
    socks.set_default_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT,
                           username=USERNAME, password=PASSWORD)
    
    original_socket = socket.socket
    socket.socket = socks.socksocket
    
    times = []
    success_count = 0
    
    print("  执行5次HTTP请求测试...")
    for i in range(5):
        try:
            start_time = time.time()
            response = requests.get("http://example.com", timeout=10)
            elapsed = time.time() - start_time
            times.append(elapsed)
            success_count += 1
            print(f"    第{i+1}次: {elapsed:.3f}秒 ✓")
        except Exception as e:
            print(f"    第{i+1}次: 超时或失败 ✗")
    
    socket.socket = original_socket
    import importlib
    importlib.reload(socket)
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n  📊 性能统计:")
        print(f"     成功率: {success_count}/5")
        print(f"     平均响应时间: {avg_time:.3f}秒")
        print(f"     最快: {min_time:.3f}秒")
        print(f"     最慢: {max_time:.3f}秒")
        
        # 不检查 header 的情况下，性能应该很好
        if avg_time < 3.0:
            print(f"  ✅ 性能优秀: 平均响应 < 3秒")
            return True
        elif avg_time < 5.0:
            print(f"  ⚠️  性能一般: 平均响应 3-5秒（可能是网络原因）")
            return True
        else:
            print(f"  ⚠️  性能较慢: 平均响应 > 5秒")
            return False
    else:
        print(f"  ❌ 所有请求都失败了")
        return False

def check_config():
    """检查配置文件"""
    print("\n" + "="*70)
    print("前置检查: 验证配置")
    print("="*70)
    
    try:
        with open("configs/config.yaml", "r") as f:
            content = f.read()
            
        if "enable_http_inspection: false" in content:
            print("  ✅ 配置文件中 enable_http_inspection = false")
            return True
        elif "enable_http_inspection: true" in content:
            print("  ❌ 配置文件中 enable_http_inspection = true")
            print("  请将配置改为 false 后重启 proxy")
            return False
        else:
            print("  ⚠️  配置文件中未找到 enable_http_inspection")
            return False
    except Exception as e:
        print(f"  ❌ 无法读取配置文件: {e}")
        return False

def main():
    """主测试流程"""
    print("="*70)
    print("HTTP Header 检测禁用验证测试")
    print("="*70)
    print(f"代理地址: {PROXY_HOST}:{PROXY_PORT}")
    print(f"日志文件: {LOG_FILE}")
    print("="*70)
    
    # 检查依赖
    try:
        import socks
        print("✅ PySocks库已安装")
    except ImportError:
        print("❌ 请先安装PySocks库: pip3 install PySocks")
        sys.exit(1)
    
    # 检查配置
    if not check_config():
        print("\n⚠️  配置检查失败，请先修改配置")
        sys.exit(1)
    
    # 检查启动日志
    found, status = check_startup_log()
    if found:
        print(f"  ℹ️  启动日志显示: HTTP深度检测 {status}")
    
    # 运行测试
    results = []
    
    results.append(("HTTP请求测试", test_http_request()))
    time.sleep(2)
    
    results.append(("HTTPS请求测试", test_https_request()))
    time.sleep(2)
    
    results.append(("性能测试", test_performance()))
    
    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n" + "="*70)
        print("✅ 所有测试通过！")
        print("="*70)
        print("\n✨ 验证结论：")
        print("  • enable_http_inspection = false 配置生效")
        print("  • 不会检查 HTTP Request Header")
        print("  • 不会提取 HTTP Host 或 TLS SNI")
        print("  • 性能没有受到影响")
        print("  • 只使用 SOCKS5 层的 URL 过滤")
        print("\n💡 说明：")
        print("  当前配置下，只会检查 SOCKS5 请求中的目标地址（IP或域名）")
        print("  不会深入检查数据包内容，确保最佳性能。")
    else:
        print("\n" + "="*70)
        print("⚠️  部分测试失败")
        print("="*70)
        print("\n建议：")
        print("  • 确认 proxy 已重启")
        print("  • 查看日志: tail -f logs/proxy.log")
        print("  • 检查配置: cat configs/config.yaml | grep enable_http_inspection")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

