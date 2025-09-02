#!/bin/bash

# 测试修复后的代理健康状态功能

echo "=== 测试修复后的代理健康状态功能 ==="

# 设置变量
API_BASE="http://localhost:8014"
AUTH_TOKEN="test-token"  # 这里需要真实的JWT token

echo "1. 测试代理健康状态接口..."
echo "请求: GET $API_BASE/api/v1/proxy/health"
echo "认证头: Authorization: Bearer $AUTH_TOKEN"
echo ""

# 测试代理健康状态接口
response=$(curl -s -w "\nHTTP状态码: %{http_code}\n" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_BASE/api/v1/proxy/health")

echo "响应内容:"
echo "$response"
echo ""

# 测试心跳记录接口
echo "2. 测试心跳记录接口..."
echo "请求: GET $API_BASE/api/v1/proxy/heartbeat"
echo ""

response=$(curl -s -w "\nHTTP状态码: %{http_code}\n" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_BASE/api/v1/proxy/heartbeat")

echo "响应内容:"
echo "$response"
echo ""

# 测试心跳清理接口
echo "3. 测试心跳清理接口..."
echo "请求: POST $API_BASE/api/v1/proxy/cleanup"
echo ""

response=$(curl -s -w "\nHTTP状态码: %{http_code}\n" \
  -X POST \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  "$API_BASE/api/v1/proxy/cleanup")

echo "响应内容:"
echo "$response"
echo ""

echo "=== 测试完成 ==="
echo ""
echo "说明："
echo "- 如果返回 401 错误，说明需要有效的JWT token"
echo "- 如果返回 200 成功，说明接口功能正常"
echo "- 心跳超时时间已调整为 15 秒"
echo "- 支持多代理服务器管理"
echo "- 提供心跳记录清理功能"
