#!/bin/bash

# 启动开发环境的SOCKS5代理服务器

echo "=== 启动开发环境服务 ==="

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

# 检查前端依赖
if [ ! -d "web/node_modules" ]; then
    echo "前端依赖未安装，正在安装..."
    cd web && npm install && cd ..
fi

echo "启动开发环境服务..."

# 启动API服务器
echo "启动API服务器 (端口 8014)..."
nohup ./bin/server > logs/server_dev.log 2>&1 &
SERVER_PID=$!
echo "API服务器已启动，PID: $SERVER_PID"

# 等待API服务器启动
sleep 2

# 启动SOCKS5代理服务器
echo "启动SOCKS5代理服务器 (端口 1082)..."
nohup ./bin/proxy > logs/proxy_dev.log 2>&1 &
PROXY_PID=$!
echo "SOCKS5代理服务器已启动，PID: $PROXY_PID"

# 等待代理服务器启动
sleep 2

# 启动前端开发服务器
echo "启动前端开发服务器 (端口 3000)..."
cd web
nohup npm run dev > ../logs/frontend_dev.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "前端开发服务器已启动，PID: $FRONTEND_PID"

# 保存PID文件
echo $SERVER_PID > logs/server_dev.pid
echo $PROXY_PID > logs/proxy_dev.pid
echo $FRONTEND_PID > logs/frontend_dev.pid

echo ""
echo "=== 所有开发服务已启动！ ==="
echo "API服务器PID: $SERVER_PID (端口 8014)"
echo "代理服务器PID: $PROXY_PID (端口 1082)"
echo "前端开发服务器PID: $FRONTEND_PID (端口 3000)"
echo ""
echo "访问地址："
echo "- 前端开发界面: http://localhost:3000"
echo "- API接口: http://localhost:8014/api/v1/"
echo "- 代理服务: localhost:1082"
echo ""
echo "日志文件位于: logs/"
echo "- API服务器: logs/server_dev.log"
echo "- 代理服务器: logs/proxy_dev.log"
echo "- 前端开发: logs/frontend_dev.log"
echo ""
echo "注意：旧服务仍在端口 8012 和 1080 上运行"
echo "如需停止旧服务，请使用 root 权限运行: sudo pkill -f './bin/server' && sudo pkill -f './bin/proxy'"
echo ""
echo "停止开发服务命令："
echo "kill \$(cat logs/server_dev.pid)"
echo "kill \$(cat logs/proxy_dev.pid)"
echo "kill \$(cat logs/frontend_dev.pid)"
