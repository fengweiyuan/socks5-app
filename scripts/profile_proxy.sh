#!/bin/bash
# 在负载下分析代理性能

echo "启动性能分析..."
echo "1. 启动后台负载生成器..."

# 后台运行负载
python3 scripts/compare_proxy_performance.py > /dev/null 2>&1 &
LOAD_PID=$!

sleep 5

echo "2. 采集30秒CPU profile..."
curl -s "http://localhost:6060/debug/pprof/profile?seconds=30" > /tmp/proxy_cpu.prof

echo "3. 停止负载..."
kill $LOAD_PID 2>/dev/null

echo "4. 分析profile..."
go tool pprof -text -flat /tmp/proxy_cpu.prof | head -n 30

echo ""
echo "详细分析可运行："
echo "go tool pprof -http=:8080 /tmp/proxy_cpu.prof"

