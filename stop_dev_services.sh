#!/bin/bash

# 停止开发环境服务

echo "=== 停止开发环境服务 ==="

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查PID文件
if [ ! -f "logs/server_dev.pid" ] || [ ! -f "logs/proxy_dev.pid" ] || [ ! -f "logs/frontend_dev.pid" ]; then
    echo "PID文件不存在，尝试查找进程..."
    
    # 查找并停止服务进程
    echo "查找API服务器进程..."
    SERVER_PIDS=$(ps aux | grep "./bin/server" | grep -v grep | awk '{print $2}')
    if [ ! -z "$SERVER_PIDS" ]; then
        echo "找到API服务器进程: $SERVER_PIDS"
        echo "$SERVER_PIDS" | xargs kill -9
        echo "API服务器已停止"
    else
        echo "未找到API服务器进程"
    fi
    
    echo "查找代理服务器进程..."
    PROXY_PIDS=$(ps aux | grep "./bin/proxy" | grep -v grep | awk '{print $2}')
    if [ ! -z "$PROXY_PIDS" ]; then
        echo "找到代理服务器进程: $PROXY_PIDS"
        echo "$PROXY_PIDS" | xargs kill -9
        echo "代理服务器已停止"
    else
        echo "未找到代理服务器进程"
    fi
    
    echo "查找前端开发服务器进程..."
    FRONTEND_PIDS=$(ps aux | grep "npm run dev\|vite" | grep -v grep | awk '{print $2}')
    if [ ! -z "$FRONTEND_PIDS" ]; then
        echo "找到前端开发服务器进程: $FRONTEND_PIDS"
        echo "$FRONTEND_PIDS" | xargs kill -9
        echo "前端开发服务器已停止"
    else
        echo "未找到前端开发服务器进程"
    fi
else
    # 使用PID文件停止服务
    echo "使用PID文件停止服务..."
    
    if [ -f "logs/server_dev.pid" ]; then
        SERVER_PID=$(cat logs/server_dev.pid)
        if kill -0 $SERVER_PID 2>/dev/null; then
            echo "停止API服务器 (PID: $SERVER_PID)..."
            kill $SERVER_PID
            echo "API服务器已停止"
        else
            echo "API服务器进程不存在"
        fi
        rm -f logs/server_dev.pid
    fi
    
    if [ -f "logs/proxy_dev.pid" ]; then
        PROXY_PID=$(cat logs/proxy_dev.pid)
        if kill -0 $PROXY_PID 2>/dev/null; then
            echo "停止代理服务器 (PID: $PROXY_PID)..."
            kill $PROXY_PID
            echo "代理服务器已停止"
        else
            echo "代理服务器进程不存在"
        fi
        rm -f logs/proxy_dev.pid
    fi
    
    if [ -f "logs/frontend_dev.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend_dev.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "停止前端开发服务器 (PID: $FRONTEND_PID)..."
            kill $FRONTEND_PID
            echo "前端开发服务器已停止"
        else
            echo "前端开发服务器进程不存在"
        fi
        rm -f logs/frontend_dev.pid
    fi
fi

echo ""
echo "=== 检查端口状态 ==="
echo "检查端口 8014 (API服务器)..."
if netstat -an | grep ":8014" | grep LISTEN > /dev/null; then
    echo "端口 8014 仍被占用"
else
    echo "端口 8014 已释放"
fi

echo "检查端口 1082 (代理服务器)..."
if netstat -an | grep ":1082" | grep LISTEN > /dev/null; then
    echo "端口 1082 仍被占用"
else
    echo "端口 1082 已释放"
fi

echo "检查端口 3000 (前端开发服务器)..."
if netstat -an | grep ":3000" | grep LISTEN > /dev/null; then
    echo "端口 3000 仍被占用"
else
    echo "端口 3000 已释放"
fi

echo ""
echo "=== 开发环境服务已停止 ==="
