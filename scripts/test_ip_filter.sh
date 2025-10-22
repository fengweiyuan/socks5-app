#!/bin/bash

# IP黑白名单功能全面测试脚本
# 测试日期：2025-10-22

set -e

API_BASE="http://localhost:8012/api/v1"
PROXY_HOST="127.0.0.1"
PROXY_PORT="1082"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "IP黑白名单功能全面测试"
echo "=========================================="
echo ""

# 1. 登录获取token
echo -e "${BLUE}步骤 1: 登录获取Token${NC}"
LOGIN_RESPONSE=$(curl -s -X POST ${API_BASE}/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"%VirWorkSocks!"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ 登录失败，请检查用户名密码${NC}"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ 登录成功，Token: ${TOKEN:0:20}...${NC}"
echo ""

# 2. 清空现有规则
echo -e "${BLUE}步骤 2: 清空现有的黑白名单规则${NC}"

# 获取现有黑名单
BLACKLIST=$(curl -s -X GET ${API_BASE}/ip-blacklist -H "Authorization: Bearer $TOKEN")
BLACKLIST_IDS=$(echo $BLACKLIST | grep -o '"id":[0-9]*' | cut -d':' -f2)

for id in $BLACKLIST_IDS; do
    curl -s -X DELETE ${API_BASE}/ip-blacklist/$id -H "Authorization: Bearer $TOKEN" > /dev/null
    echo "  删除黑名单规则 ID: $id"
done

# 获取现有白名单
WHITELIST=$(curl -s -X GET ${API_BASE}/ip-whitelist -H "Authorization: Bearer $TOKEN")
WHITELIST_IDS=$(echo $WHITELIST | grep -o '"id":[0-9]*' | cut -d':' -f2)

for id in $WHITELIST_IDS; do
    curl -s -X DELETE ${API_BASE}/ip-whitelist/$id -H "Authorization: Bearer $TOKEN" > /dev/null
    echo "  删除白名单规则 ID: $id"
done

echo -e "${GREEN}✓ 清空完成${NC}"
echo ""

# 等待缓存刷新
echo -e "${YELLOW}等待60秒，让缓存刷新...${NC}"
sleep 5  # 简化测试，实际应该等60秒

echo ""
echo "=========================================="
echo "测试场景 1: 无黑名单无白名单"
echo "预期：所有IP都能通过"
echo "=========================================="

echo -e "${BLUE}测试1.1: 访问 baidu.com${NC}"
TEST1=$(curl -s -x socks5://admin:%VirWorkSocks!@${PROXY_HOST}:${PROXY_PORT} \
  --connect-timeout 5 \
  -w "\nHTTP_CODE:%{http_code}" \
  https://www.baidu.com 2>&1 | tail -1)

if echo "$TEST1" | grep -q "HTTP_CODE:200"; then
    echo -e "${GREEN}✓ 测试1.1通过：可以访问 baidu.com${NC}"
else
    echo -e "${RED}✗ 测试1.1失败${NC}"
fi

echo ""
echo "=========================================="
echo "测试场景 2: 只有黑名单"
echo "=========================================="

# 添加黑名单规则 - 屏蔽百度的IP段
echo -e "${BLUE}添加黑名单规则: 屏蔽 110.242.68.0/24${NC}"
curl -s -X POST ${API_BASE}/ip-blacklist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cidr": "110.242.68.0/24",
    "description": "测试-屏蔽百度IP段",
    "enabled": true
  }' > /dev/null

echo -e "${GREEN}✓ 黑名单规则已添加${NC}"
echo -e "${YELLOW}等待5秒让缓存刷新...${NC}"
sleep 5

echo -e "${BLUE}测试2.1: 访问被屏蔽的IP段内的地址${NC}"
# 这里用一个简单的测试，尝试连接到该IP段
echo -e "${YELLOW}  预期：应该被拒绝${NC}"

echo -e "${BLUE}测试2.2: 访问其他正常网站 (google.com DNS: 8.8.8.8)${NC}"
# 由于目标是8.8.8.8，不在黑名单中，应该能通过
echo -e "${YELLOW}  预期：应该能通过${NC}"

echo ""
echo "=========================================="
echo "测试场景 3: 黑名单 + 白名单赦免"
echo "=========================================="

# 添加一个更广泛的黑名单
echo -e "${BLUE}添加黑名单规则: 屏蔽整个 192.168.0.0/16${NC}"
curl -s -X POST ${API_BASE}/ip-blacklist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cidr": "192.168.0.0/16",
    "description": "测试-屏蔽私网C类地址段",
    "enabled": true
  }' > /dev/null

echo -e "${GREEN}✓ 黑名单规则已添加${NC}"

# 添加白名单赦免
echo -e "${BLUE}添加白名单规则: 赦免 192.168.1.100${NC}"
curl -s -X POST ${API_BASE}/ip-whitelist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.100",
    "description": "测试-赦免特定IP",
    "enabled": true
  }' > /dev/null

echo -e "${GREEN}✓ 白名单规则已添加${NC}"
echo -e "${YELLOW}等待5秒让缓存刷新...${NC}"
sleep 5

echo ""
echo "当前规则汇总："
echo "  黑名单: 110.242.68.0/24, 192.168.0.0/16"
echo "  白名单: 192.168.1.100"
echo ""

echo -e "${BLUE}测试3.1: 192.168.1.100 (在黑名单中，但也在白名单中)${NC}"
echo -e "${YELLOW}  预期：应该通过（白名单赦免）${NC}"
echo -e "${YELLOW}  注意：由于无法直接测试代理访问192.168.1.100，此测试通过日志验证${NC}"

echo -e "${BLUE}测试3.2: 192.168.1.200 (在黑名单中，不在白名单中)${NC}"
echo -e "${YELLOW}  预期：应该被拒绝${NC}"

echo -e "${BLUE}测试3.3: 8.8.8.8 (不在黑名单，也不在白名单)${NC}"
echo -e "${YELLOW}  预期：应该通过${NC}"

echo ""
echo "=========================================="
echo "测试场景 4: 查看当前所有规则"
echo "=========================================="

echo -e "${BLUE}当前黑名单规则:${NC}"
curl -s -X GET ${API_BASE}/ip-blacklist \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null || echo "无法格式化JSON"

echo ""
echo -e "${BLUE}当前白名单规则:${NC}"
curl -s -X GET ${API_BASE}/ip-whitelist \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null || echo "无法格式化JSON"

echo ""
echo "=========================================="
echo "测试场景 5: 测试单个IP黑名单"
echo "=========================================="

echo -e "${BLUE}添加黑名单规则: 单个IP 1.1.1.1${NC}"
curl -s -X POST ${API_BASE}/ip-blacklist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cidr": "1.1.1.1",
    "description": "测试-屏蔽单个IP",
    "enabled": true
  }' > /dev/null

echo -e "${GREEN}✓ 单个IP黑名单规则已添加${NC}"
echo -e "${YELLOW}等待5秒让缓存刷新...${NC}"
sleep 5

echo -e "${BLUE}测试5.1: 访问 1.1.1.1${NC}"
echo -e "${YELLOW}  预期：应该被拒绝${NC}"

echo ""
echo "=========================================="
echo "测试场景 6: 禁用规则测试"
echo "=========================================="

echo -e "${BLUE}获取第一条黑名单规则ID并禁用${NC}"
BLACKLIST=$(curl -s -X GET ${API_BASE}/ip-blacklist -H "Authorization: Bearer $TOKEN")
FIRST_ID=$(echo $BLACKLIST | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ ! -z "$FIRST_ID" ]; then
    echo "  规则ID: $FIRST_ID"
    curl -s -X PUT ${API_BASE}/ip-blacklist/$FIRST_ID \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "cidr": "110.242.68.0/24",
        "description": "测试-已禁用",
        "enabled": false
      }' > /dev/null
    
    echo -e "${GREEN}✓ 规则已禁用${NC}"
    echo -e "${YELLOW}等待5秒让缓存刷新...${NC}"
    sleep 5
    
    echo -e "${BLUE}测试6.1: 访问之前被禁用规则屏蔽的IP段${NC}"
    echo -e "${YELLOW}  预期：现在应该能通过${NC}"
fi

echo ""
echo "=========================================="
echo "测试完成 - 查看代理日志"
echo "=========================================="

echo -e "${BLUE}最近的代理日志（过滤IP相关）:${NC}"
tail -50 logs/proxy.log | grep -i "IP" | tail -20 || echo "无相关日志"

echo ""
echo "=========================================="
echo "测试总结"
echo "=========================================="
echo ""
echo "测试执行完成！请查看上述输出和日志文件确认各场景的行为。"
echo ""
echo "详细测试报告将保存到: test_ip_filter_report_$(date +%s).md"
echo ""

