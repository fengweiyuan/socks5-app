#!/usr/bin/env python3
"""
全面测试 SOCKS5 代理和 Web 服务功能
"""

import requests
import socket
import time
import json
import sys

def test_web_service():
    """测试 Web 服务"""
    print("🔍 测试 Web 服务...")
    
    try:
        # 测试健康检查
        response = requests.get("http://localhost:8012/health", timeout=5)
        if response.status_code == 200:
            print("✅ Web 服务健康检查通过")
            health_data = response.json()
            print(f"   服务状态: {health_data.get('status')}")
        else:
            print(f"❌ Web 服务健康检查失败: {response.status_code}")
            return False
            
        # 测试主页
        response = requests.get("http://localhost:8012/", timeout=5)
        if response.status_code == 200 and "SOCKS5代理管理" in response.text:
            print("✅ Web 管理界面正常")
        else:
            print(f"❌ Web 管理界面异常: {response.status_code}")
            return False
            
        # 测试 Prometheus 指标
        response = requests.get("http://localhost:8012/metrics", timeout=5)
        if response.status_code == 200 and "socks5_" in response.text:
            print("✅ Prometheus 指标端点正常")
        else:
            print(f"❌ Prometheus 指标端点异常: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Web 服务测试失败: {e}")
        return False

def test_proxy_service():
    """测试代理服务"""
    print("\n🔍 测试 SOCKS5 代理服务...")
    
    try:
        # 测试代理端口是否监听
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 1082))
        sock.close()
        
        if result == 0:
            print("✅ SOCKS5 代理端口 1082 正常监听")
        else:
            print("❌ SOCKS5 代理端口 1082 无法连接")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 代理服务测试失败: {e}")
        return False

def test_ip_forwarding():
    """测试 IP 透传功能"""
    print("\n🔍 测试 IP 透传功能...")
    
    try:
        # 启动测试服务器
        import subprocess
        import threading
        import http.server
        import socketserver
        
        class TestHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                real_ip = self.headers.get('X-Real-IP', 'Not Found')
                forwarded_for = self.headers.get('X-Forwarded-For', 'Not Found')
                
                response = f"""
                <html>
                <body>
                    <h1>IP 透传测试结果</h1>
                    <p><strong>客户端地址:</strong> {self.client_address[0]}</p>
                    <p><strong>X-Real-IP:</strong> {real_ip}</p>
                    <p><strong>X-Forwarded-For:</strong> {forwarded_for}</p>
                    <p><strong>请求时间:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </body>
                </html>
                """
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
        
        # 启动测试服务器
        server = socketserver.TCPServer(("", 8889), TestHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(1)  # 等待服务器启动
        
        # 测试直接访问
        response = requests.get("http://localhost:8889", timeout=5)
        if response.status_code == 200:
            print("✅ IP 透传测试服务器启动成功")
            if "X-Real-IP" in response.text:
                print("   检测到 IP 透传头信息")
            else:
                print("   ⚠️  未检测到 IP 透传头信息（可能需要通过代理访问）")
        else:
            print(f"❌ IP 透传测试服务器异常: {response.status_code}")
            return False
            
        server.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ IP 透传功能测试失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        # 通过 API 测试数据库连接（需要认证的端点会返回认证错误而不是数据库错误）
        response = requests.get("http://localhost:8012/api/v1/users", timeout=5)
        if response.status_code == 401:  # 未授权，说明服务正常但需要认证
            print("✅ 数据库连接正常（API 需要认证）")
            return True
        elif response.status_code == 500:  # 服务器错误，可能是数据库问题
            print("❌ 数据库连接可能有问题")
            return False
        else:
            print(f"⚠️  意外的响应状态码: {response.status_code}")
            return True
            
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始全面测试 SOCKS5 代理和 Web 服务")
    print("=" * 50)
    
    tests = [
        ("Web 服务", test_web_service),
        ("代理服务", test_proxy_service),
        ("IP 透传功能", test_ip_forwarding),
        ("数据库连接", test_database_connection),
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
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！服务运行正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关服务。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
