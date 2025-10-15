#!/usr/bin/env python3
"""
高并发压力测试 - 用于pprof分析
"""
import time
import threading
import requests

PROXY = 'socks5://fwy1014:fwy1014@127.0.0.1:1082'
URL = "http://127.0.0.1:8888/test"

def worker(duration):
    """持续发送请求"""
    session = requests.Session()
    session.proxies = {'http': PROXY}
    
    end_time = time.time() + duration
    count = 0
    
    while time.time() < end_time:
        try:
            session.get(URL, timeout=5)
            count += 1
        except:
            pass
    
    return count

def main():
    concurrency = 50  # 50并发
    duration = 60     # 持续60秒
    
    print(f"启动{concurrency}并发压力测试，持续{duration}秒...")
    print("用于pprof分析，请在另一个终端运行:")
    print("curl -s 'http://localhost:6060/debug/pprof/profile?seconds=30' > /tmp/proxy_profile.prof")
    print()
    
    start = time.time()
    threads = []
    
    for i in range(concurrency):
        t = threading.Thread(target=worker, args=(duration,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    print(f"\n测试完成，实际耗时: {elapsed:.1f}秒")

if __name__ == "__main__":
    main()

