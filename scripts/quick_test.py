#!/usr/bin/env python3
"""快速测试"""
import time
import requests

PROXY = f'socks5://fwy1014:fwy1014@127.0.0.1:1082'
URL = "http://127.0.0.1:8888/test"

print("测试10个请求...")
session = requests.Session()
session.proxies = {'http': PROXY}

times = []
for i in range(10):
    start = time.time()
    r = session.get(URL, timeout=5)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"{i+1}: {elapsed*1000:.2f}ms - {len(r.content)} bytes")

import statistics
print(f"\n平均: {statistics.mean(times)*1000:.2f}ms")
print(f"中位数: {statistics.median(times)*1000:.2f}ms")

