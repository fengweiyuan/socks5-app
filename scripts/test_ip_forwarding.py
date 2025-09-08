#!/usr/bin/env python3
"""
测试 SOCKS5 代理的 IP 透传功能
这个脚本会启动一个简单的 HTTP 服务器来接收代理请求，并检查是否收到了客户端 IP 信息
"""

import socket
import threading
import time
import sys
import socks
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

class IPForwardingTestHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器，用于检查是否收到客户端 IP 信息"""
    
    def do_GET(self):
        # 获取客户端 IP
        client_ip = self.client_address[0]
        
        # 检查请求头中是否有 IP 透传信息
        real_ip = self.headers.get('X-Real-IP', 'Not Found')
        forwarded_for = self.headers.get('X-Forwarded-For', 'Not Found')
        
        print(f"[测试服务器] 收到请求:")
        print(f"  客户端地址: {client_ip}")
        print(f"  X-Real-IP: {real_ip}")
        print(f"  X-Forwarded-For: {forwarded_for}")
        print(f"  请求路径: {self.path}")
        print(f"  所有请求头: {dict(self.headers)}")
        print("-" * 50)
        
        # 返回响应
        response_body = f"""
        <html>
        <body>
            <h1>IP 透传测试结果</h1>
            <p><strong>客户端地址:</strong> {client_ip}</p>
            <p><strong>X-Real-IP:</strong> {real_ip}</p>
            <p><strong>X-Forwarded-For:</strong> {forwarded_for}</p>
            <p><strong>请求时间:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-length', str(len(response_body.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(response_body.encode('utf-8'))

def start_test_server(port=8888):
    """启动测试 HTTP 服务器"""
    server = HTTPServer(('0.0.0.0', port), IPForwardingTestHandler)
    print(f"[测试服务器] 启动在端口 {port}")
    print(f"[测试服务器] 访问地址: http://localhost:{port}")
    print("=" * 50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[测试服务器] 正在关闭...")
        server.shutdown()

def test_socks5_proxy(proxy_host='127.0.0.1', proxy_port=1082, 
                     proxy_user=None, proxy_pass=None, target_url='http://127.0.0.1:8888'):
    """测试 SOCKS5 代理的 IP 透传功能"""
    
    print(f"[代理测试] 开始测试 SOCKS5 代理")
    print(f"  代理地址: {proxy_host}:{proxy_port}")
    print(f"  目标地址: {target_url}")
    print("=" * 50)
    
    try:
        # 设置 SOCKS5 代理
        socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port, 
                               username=proxy_user, password=proxy_pass)
        socket.socket = socks.socksocket
        
        # 发送请求
        response = requests.get(target_url, timeout=10)
        print(f"[代理测试] 请求成功，状态码: {response.status_code}")
        print(f"[代理测试] 响应内容预览: {response.text[:200]}...")
        
    except Exception as e:
        print(f"[代理测试] 请求失败: {e}")
    finally:
        # 恢复默认 socket
        socks.set_default_proxy()
        socket.socket = socket._socketobject

def main():
    print("SOCKS5 代理 IP 透传功能测试")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == 'server':
            # 启动测试服务器
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8888
            start_test_server(port)
            return
        elif sys.argv[1] == 'client':
            # 运行客户端测试
            proxy_host = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
            proxy_port = int(sys.argv[3]) if len(sys.argv) > 3 else 1082
            test_socks5_proxy(proxy_host, proxy_port)
            return
    
    # 默认：启动服务器
    print("用法:")
    print("  python3 test_ip_forwarding.py server [port]  # 启动测试服务器")
    print("  python3 test_ip_forwarding.py client [proxy_host] [proxy_port]  # 测试代理")
    print()
    print("启动测试服务器...")
    start_test_server()

if __name__ == '__main__':
    main()
