#!/usr/bin/env python3
"""
简单的HTTP测试服务器
用于带宽限制测试
"""

import http.server
import socketserver
import sys

PORT = 8888

class TestHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 生成指定大小的数据
        if self.path.startswith('/data/'):
            try:
                size = int(self.path.split('/')[2])
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(size))
                self.end_headers()
                
                # 发送数据（每次发送1KB）
                chunk_size = 1024
                remaining = size
                while remaining > 0:
                    to_send = min(chunk_size, remaining)
                    self.wfile.write(b'X' * to_send)
                    remaining -= to_send
                
                print(f"已发送 {size} 字节数据")
                
            except Exception as e:
                self.send_error(500, f"Error: {e}")
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Test Server Running</h1></body></html>')
    
    def log_message(self, format, *args):
        # 简化日志输出
        sys.stdout.write(f"{self.address_string()} - {format%args}\n")

def main():
    with socketserver.TCPServer(("", PORT), TestHTTPRequestHandler) as httpd:
        print(f"测试服务器运行在端口 {PORT}")
        print(f"访问 http://localhost:{PORT}/data/<size> 获取指定大小的数据")
        print(f"例如: http://localhost:{PORT}/data/10000 获取 10KB 数据")
        print("按 Ctrl+C 停止服务器")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == '__main__':
    main()

