#!/bin/bash

# SOCKS5代理服务器停止脚本

set -e

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "停止SOCKS5代理服务器..."

# 停止API服务器
if [ -f "logs/server.pid" ]; then
    SERVER_PID=$(cat logs/server.pid)
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "停止API服务器 (PID: $SERVER_PID)..."
        kill $SERVER_PID
        sleep 2
        if kill -0 $SERVER_PID 2>/dev/null; then
            echo "强制停止API服务器..."
            kill -9 $SERVER_PID
        fi
        rm -f logs/server.pid
        echo "API服务器已停止"
    else
        echo "API服务器未运行"
        rm -f logs/server.pid
    fi
else
    echo "API服务器PID文件不存在"
fi

# 停止SOCKS5代理服务器
if [ -f "logs/proxy.pid" ]; then
    PROXY_PID=$(cat logs/proxy.pid)
    if kill -0 $PROXY_PID 2>/dev/null; then
        echo "停止SOCKS5代理服务器 (PID: $PROXY_PID)..."
        kill $PROXY_PID
        sleep 2
        if kill -0 $PROXY_PID 2>/dev/null; then
            echo "强制停止SOCKS5代理服务器..."
            kill -9 $PROXY_PID
        fi
        rm -f logs/proxy.pid
        echo "SOCKS5代理服务器已停止"
    else
        echo "SOCKS5代理服务器未运行"
        rm -f logs/proxy.pid
    fi
else
    echo "SOCKS5代理服务器PID文件不存在"
fi

echo "所有服务已停止！"
