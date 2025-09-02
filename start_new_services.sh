#!/bin/bash

# 启动新端口的SOCKS5代理服务器

echo "=== 启动新端口的SOCKS5代理服务器 ==="

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 创建必要的目录
mkdir -p logs
mkdir -p data

# 检查配置文件
if [ ! -f "configs/config.yaml" ]; then
    echo "配置文件不存在: configs/config.yaml"
    exit 1
fi

# 检查可执行文件
if [ ! -f "bin/server" ]; then
    echo "API服务器可执行文件不存在，请先运行构建脚本"
    exit 1
fi

if [ ! -f "bin/proxy" ]; then
    echo "代理服务器可执行文件不存在，请先运行构建脚本"
    exit 1
fi

# 启动服务
echo "启动SOCKS5代理服务器..."

# 启动API服务器
echo "启动API服务器 (端口 8013)..."
nohup ./bin/server > logs/server_new.log 2>&1 &
SERVER_PID=$!
echo "API服务器已启动，PID: $SERVER_PID"

# 等待API服务器启动
sleep 2

# 启动SOCKS5代理服务器
echo "启动SOCKS5代理服务器 (端口 1081)..."
nohup ./bin/proxy > logs/proxy_new.log 2>&1 &
PROXY_PID=$!
echo "SOCKS5代理服务器已启动，PID: $PROXY_PID"

# 保存PID文件
echo $SERVER_PID > logs/server_new.pid
echo $PROXY_PID > logs/proxy_new.pid

echo "所有服务已启动！"
echo "API服务器PID: $SERVER_PID (端口 8013)"
echo "代理服务器PID: $PROXY_PID (端口 1081)"
echo "日志文件位于: logs/"
echo "访问管理界面: http://localhost:8013"
echo ""
echo "注意：旧服务仍在端口 8012 和 1080 上运行"
echo "如需停止旧服务，请使用 root 权限运行: sudo pkill -f './bin/server' && sudo pkill -f './bin/proxy'"
