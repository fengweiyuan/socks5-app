#!/usr/bin/env python3
"""
详细的时序分析
分解每个阶段的时间消耗
"""
import time
import socket
import socks

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
PROXY_USER = "fwy1014"
PROXY_PASS = "fwy1014"

def test_socks5_detailed():
    """详细测试SOCKS5各个阶段"""
    print("详细时序分析:")
    print("="*60)
    
    for i in range(5):
        print(f"\n第 {i+1} 次测试:")
        
        t0 = time.time()
        
        # 1. 创建socket
        s = socks.socksocket()
        t1 = time.time()
        print(f"  1. 创建socket: {(t1-t0)*1000:.2f}ms")
        
        # 2. 设置代理
        s.set_proxy(socks.SOCKS5, PROXY_HOST, PROXY_PORT, True, PROXY_USER, PROXY_PASS)
        t2 = time.time()
        print(f"  2. 设置代理: {(t2-t1)*1000:.2f}ms")
        
        # 3. 连接到目标
        s.connect(("127.0.0.1", 8888))
        t3 = time.time()
        print(f"  3. 建立连接(含认证): {(t3-t2)*1000:.2f}ms")
        
        # 4. 发送HTTP请求
        http_request = b"GET /test HTTP/1.1\r\nHost: 127.0.0.1:8888\r\nConnection: close\r\n\r\n"
        s.send(http_request)
        t4 = time.time()
        print(f"  4. 发送请求: {(t4-t3)*1000:.2f}ms")
        
        # 5. 接收响应
        response = b""
        s.settimeout(1)
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass
        t5 = time.time()
        print(f"  5. 接收响应: {(t5-t4)*1000:.2f}ms ({len(response)} bytes)")
        
        s.close()
        t6 = time.time()
        print(f"  6. 关闭连接: {(t6-t5)*1000:.2f}ms")
        
        total = t6 - t0
        print(f"  总计: {total*1000:.2f}ms")

if __name__ == "__main__":
    test_socks5_detailed()

