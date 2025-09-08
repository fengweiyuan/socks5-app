#!/bin/bash

# SOCKS5代理服务器统一启停脚本
# 支持端口指定，如果不指定则使用配置文件中的默认端口

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_SERVER_PORT="8012"
DEFAULT_PROXY_PORT="1082"
DEFAULT_SERVER_HOST="0.0.0.0"
DEFAULT_PROXY_HOST="0.0.0.0"

# 显示帮助信息
show_help() {
    echo -e "${BLUE}SOCKS5代理服务器管理脚本${NC}"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  start    启动服务"
    echo "  stop     停止服务"
    echo "  restart  重启服务"
    echo "  status   查看服务状态"
    echo "  help     显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  -s, --server-port PORT    指定API服务器端口 (默认: $DEFAULT_SERVER_PORT)"
    echo "  -p, --proxy-port PORT     指定代理服务器端口 (默认: $DEFAULT_PROXY_PORT)"
    echo "  -h, --help                显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start                           # 使用默认端口启动"
    echo "  $0 start -s 8013 -p 1083          # 指定端口启动"
    echo "  $0 stop                            # 停止服务"
    echo "  $0 status                          # 查看服务状态"
    echo ""
}

# 解析命令行参数
parse_args() {
    SERVER_PORT="$DEFAULT_SERVER_PORT"
    PROXY_PORT="$DEFAULT_PROXY_PORT"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--server-port)
                SERVER_PORT="$2"
                shift 2
                ;;
            -p|--proxy-port)
                PROXY_PORT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            start|stop|restart|status)
                COMMAND="$1"
                shift
                ;;
            *)
                echo -e "${RED}错误: 未知参数 $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    if [[ -z "$COMMAND" ]]; then
        echo -e "${RED}错误: 请指定命令${NC}"
        show_help
        exit 1
    fi
}

# 设置工作目录
setup_environment() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR/.."
    
    # 创建必要的目录
    mkdir -p logs
    mkdir -p data
    
    # 检查配置文件
    if [ ! -f "configs/config.yaml" ]; then
        echo -e "${RED}错误: 配置文件不存在: configs/config.yaml${NC}"
        exit 1
    fi
    
    # 检查可执行文件
    if [ ! -f "bin/server" ]; then
        echo -e "${RED}错误: API服务器可执行文件不存在，请先运行构建脚本${NC}"
        exit 1
    fi
    
    if [ ! -f "bin/proxy" ]; then
        echo -e "${RED}错误: 代理服务器可执行文件不存在，请先运行构建脚本${NC}"
        exit 1
    fi
}

# 启动服务
start_services() {
    echo -e "${GREEN}启动SOCKS5代理服务器...${NC}"
    echo -e "${BLUE}API服务器端口: $SERVER_PORT${NC}"
    echo -e "${BLUE}代理服务器端口: $PROXY_PORT${NC}"
    
    # 检查端口是否被占用
    if lsof -Pi :$SERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}警告: 端口 $SERVER_PORT 已被占用${NC}"
    fi
    
    if lsof -Pi :$PROXY_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}警告: 端口 $PROXY_PORT 已被占用${NC}"
    fi
    
    # 启动API服务器
    echo -e "${BLUE}启动API服务器 (端口: $SERVER_PORT)...${NC}"
    SERVER_CMD="./bin/server -port $SERVER_PORT -host $DEFAULT_SERVER_HOST"
    nohup $SERVER_CMD > logs/server.log 2>&1 &
    SERVER_PID=$!
    echo -e "${GREEN}API服务器已启动，PID: $SERVER_PID${NC}"
    
    # 等待API服务器启动
    sleep 2
    
    # 启动SOCKS5代理服务器
    echo -e "${BLUE}启动SOCKS5代理服务器 (端口: $PROXY_PORT)...${NC}"
    PROXY_CMD="./bin/proxy -port $PROXY_PORT -host $DEFAULT_PROXY_HOST"
    nohup $PROXY_CMD > logs/proxy.log 2>&1 &
    PROXY_PID=$!
    echo -e "${GREEN}代理服务器已启动，PID: $PROXY_PID${NC}"
    
    # 保存PID文件
    echo $SERVER_PID > logs/server.pid
    echo $PROXY_PID > logs/proxy.pid
    
    echo ""
    echo -e "${GREEN}所有服务已启动！${NC}"
    echo -e "${BLUE}API服务器PID: $SERVER_PID (端口: $SERVER_PORT)${NC}"
    echo -e "${BLUE}代理服务器PID: $PROXY_PID (端口: $PROXY_PORT)${NC}"
    echo -e "${BLUE}日志文件位于: logs/${NC}"
    echo -e "${BLUE}访问管理界面: http://localhost:$SERVER_PORT${NC}"
    echo -e "${BLUE}代理服务地址: localhost:$PROXY_PORT${NC}"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}停止SOCKS5代理服务器...${NC}"
    
    # 停止API服务器
    if [ -f "logs/server.pid" ]; then
        SERVER_PID=$(cat logs/server.pid)
        if kill -0 $SERVER_PID 2>/dev/null; then
            echo -e "${BLUE}停止API服务器 (PID: $SERVER_PID)...${NC}"
            kill $SERVER_PID
            rm -f logs/server.pid
            echo -e "${GREEN}API服务器已停止${NC}"
        else
            echo -e "${YELLOW}API服务器进程不存在${NC}"
            rm -f logs/server.pid
        fi
    else
        echo -e "${YELLOW}API服务器PID文件不存在${NC}"
    fi
    
    # 停止代理服务器
    if [ -f "logs/proxy.pid" ]; then
        PROXY_PID=$(cat logs/proxy.pid)
        if kill -0 $PROXY_PID 2>/dev/null; then
            echo -e "${BLUE}停止代理服务器 (PID: $PROXY_PID)...${NC}"
            kill $PROXY_PID
            rm -f logs/proxy.pid
            echo -e "${GREEN}代理服务器已停止${NC}"
        else
            echo -e "${YELLOW}代理服务器进程不存在${NC}"
            rm -f logs/proxy.pid
        fi
    else
        echo -e "${YELLOW}代理服务器PID文件不存在${NC}"
    fi
    
    echo -e "${GREEN}所有服务已停止${NC}"
}

# 查看服务状态
show_status() {
    echo -e "${BLUE}SOCKS5代理服务器状态${NC}"
    echo ""
    
    # 检查API服务器
    if [ -f "logs/server.pid" ]; then
        SERVER_PID=$(cat logs/server.pid)
        if kill -0 $SERVER_PID 2>/dev/null; then
            echo -e "${GREEN}✓ API服务器运行中 (PID: $SERVER_PID)${NC}"
            # 获取端口信息
            SERVER_PORT=$(lsof -p $SERVER_PID -i -P -n | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
            if [ ! -z "$SERVER_PORT" ]; then
                echo -e "${BLUE}  监听端口: $SERVER_PORT${NC}"
            fi
        else
            echo -e "${RED}✗ API服务器未运行${NC}"
            rm -f logs/server.pid
        fi
    else
        echo -e "${RED}✗ API服务器未运行${NC}"
    fi
    
    # 检查代理服务器
    if [ -f "logs/proxy.pid" ]; then
        PROXY_PID=$(cat logs/proxy.pid)
        if kill -0 $PROXY_PID 2>/dev/null; then
            echo -e "${GREEN}✓ 代理服务器运行中 (PID: $PROXY_PID)${NC}"
            # 获取端口信息
            PROXY_PORT=$(lsof -p $PROXY_PID -i -P -n | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
            if [ ! -z "$PROXY_PORT" ]; then
                echo -e "${BLUE}  监听端口: $PROXY_PORT${NC}"
            fi
        else
            echo -e "${RED}✗ 代理服务器未运行${NC}"
            rm -f logs/proxy.pid
        fi
    else
        echo -e "${RED}✗ 代理服务器未运行${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}端口占用情况:${NC}"
    lsof -i :8012-1099 -sTCP:LISTEN 2>/dev/null | grep LISTEN || echo "  无相关端口占用"
}

# 主函数
main() {
    parse_args "$@"
    setup_environment
    
    case $COMMAND in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 2
            start_services
            ;;
        status)
            show_status
            ;;
        *)
            echo -e "${RED}错误: 未知命令 $COMMAND${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
