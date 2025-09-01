#!/bin/bash

# SOCKS5代理服务器启动脚本

set -e

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "请以root权限运行此脚本"
    exit 1
fi

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

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
echo "启动API服务器..."
nohup ./bin/server > logs/server.log 2>&1 &
SERVER_PID=$!
echo "API服务器已启动，PID: $SERVER_PID"

# 等待API服务器启动
sleep 2

# 启动SOCKS5代理服务器
echo "启动SOCKS5代理服务器..."
nohup ./bin/proxy > logs/proxy.log 2>&1 &
PROXY_PID=$!
echo "SOCKS5代理服务器已启动，PID: $PROXY_PID"

# 保存PID文件
echo $SERVER_PID > logs/server.pid
echo $PROXY_PID > logs/proxy.pid

echo "所有服务已启动！"
echo "API服务器PID: $SERVER_PID"
echo "代理服务器PID: $PROXY_PID"
echo "日志文件位于: logs/"
echo "访问管理界面: http://localhost:8012"
