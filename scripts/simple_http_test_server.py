#!/usr/bin/env python3
"""
简单的HTTP测试服务器
用于测试SOCKS5代理的真实性能
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        # 检查是否是/bytes/N的请求
        if self.path.startswith('/bytes/'):
            try:
                # 提取字节数
                size = int(self.path.split('/')[-1])
                # 生成指定大小的数据
                data = b'0' * size
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', len(data))
                self.end_headers()
                self.wfile.write(data)
                return
            except:
                pass
        
        # 返回简单的JSON响应
        response = {
            "status": "ok",
            "timestamp": time.time(),
            "path": self.path
        }
        
        response_json = json.dumps(response)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response_json))
        self.end_headers()
        self.wfile.write(response_json.encode())
    
    def log_message(self, format, *args):
        """禁用日志输出以提高性能"""
        pass

def main():
    port = 8888
    server = HTTPServer(('127.0.0.1', port), SimpleHandler)
    print(f"简单HTTP测试服务器启动在 http://127.0.0.1:{port}")
    print("按 Ctrl+C 停止服务器")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == '__main__':
    main()

