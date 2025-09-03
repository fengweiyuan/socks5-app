#!/bin/bash

# 测试代理健康状态接口的脚本

echo "=== 测试代理健康状态接口 ==="

# 1. 测试未认证的请求
echo "1. 测试未认证的请求:"
curl -s -w "HTTP状态码: %{http_code}\n" http://localhost:8012/api/v1/proxy/health
echo ""

# 2. 测试无效token的请求
echo "2. 测试无效token的请求:"
curl -s -w "HTTP状态码: %{http_code}\n" -H "Authorization: Bearer invalid-token" http://localhost:8012/api/v1/proxy/health
echo ""

# 3. 测试系统状态接口（不需要认证）
echo "3. 测试系统状态接口（不需要认证）:"
curl -s -w "HTTP状态码: %{http_code}\n" http://localhost:8012/api/v1/system/status
echo ""

# 4. 检查数据库中的心跳记录
echo "4. 检查数据库中的心跳记录:"
mysql -u socks5_user -psocks5_password -h 127.0.0.1 -P 3306 socks5_db -e "SELECT proxy_id, status, last_heartbeat, active_conns FROM proxy_heartbeats ORDER BY last_heartbeat DESC;"
echo ""

# 5. 检查服务状态
echo "5. 检查服务状态:"
ps aux | grep -E "(server|proxy)" | grep -v grep | head -5
echo ""

# 6. 检查端口监听状态
echo "6. 检查端口监听状态:"
netstat -an | grep -E "(8012|1080)" | grep LISTEN
echo ""

echo "=== 测试完成 ==="
