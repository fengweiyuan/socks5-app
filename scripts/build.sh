#!/bin/bash

# SOCKS5代理服务器构建脚本

set -e

echo "开始构建SOCKS5代理服务器..."

# 创建必要的目录
mkdir -p bin
mkdir -p logs

# 设置Go环境变量
export CGO_ENABLED=1
export GOOS=linux
export GOARCH=amd64

# 构建后端服务
echo "构建API服务器..."
go build -ldflags="-s -w" -o bin/server cmd/server/main.go

echo "构建SOCKS5代理服务器..."
go build -ldflags="-s -w" -o bin/proxy cmd/proxy/main.go

# 构建前端
echo "构建前端应用..."
cd web
npm install
npm run build
cd ..

# 创建发布包
echo "创建发布包..."
mkdir -p dist
cp -r bin dist/
cp -r configs dist/
cp -r web/build dist/web/
cp -r scripts dist/
cp README.md dist/

echo "构建完成！"
echo "可执行文件位于: dist/bin/"
echo "配置文件位于: dist/configs/"
echo "前端文件位于: dist/web/"
