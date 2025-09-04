.PHONY: build clean start stop dev test help db-test db-init build-linux dist-linux

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
BINARY_DIR=bin
DIST_DIR=dist
DIST_LINUX_DIR=dist_linux
CONFIG_DIR=configs
WEB_DIR=web

# 构建目标
build: ## 构建整个项目
	@echo "开始构建SOCKS5代理服务器..."
	@mkdir -p $(BINARY_DIR)
	@mkdir -p logs
	@echo "构建后端服务..."
	@go build -ldflags="-s -w" -o $(BINARY_DIR)/server cmd/server/main.go
	@go build -ldflags="-s -w" -o $(BINARY_DIR)/proxy cmd/proxy/main.go
	@echo "构建前端应用..."
	@cd $(WEB_DIR) && npm install && npm run build
	@echo "构建完成！"

# 构建Linux版本（CentOS兼容）
build-linux: ## 构建Linux版本（CentOS兼容）
	@echo "开始构建Linux版本的SOCKS5代理服务器..."
	@mkdir -p $(BINARY_DIR)
	@mkdir -p logs
	@echo "构建后端服务（Linux版本）..."
	@GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o $(BINARY_DIR)/server cmd/server/main.go
	@GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o $(BINARY_DIR)/proxy cmd/proxy/main.go
	@echo "构建前端应用..."
	@cd $(WEB_DIR) && npm install && npm run build
	@echo "Linux版本构建完成！"

# 开发模式
dev: ## 启动开发模式
	@echo "启动开发模式..."
	@echo "请分别运行以下命令："
	@echo "1. 后端API服务: go run cmd/server/main.go"
	@echo "2. 代理服务: go run cmd/proxy/main.go"
	@echo "3. 前端开发: cd web && npm run dev"

# 启动服务
start: ## 启动所有服务
	@echo "启动SOCKS5代理服务器..."
	@chmod +x scripts/service.sh
	@./scripts/service.sh start

# 停止服务
stop: ## 停止所有服务
	@echo "停止SOCKS5代理服务器..."
	@chmod +x scripts/service.sh
	@./scripts/service.sh stop

# 重启服务
restart: ## 重启所有服务
	@echo "重启SOCKS5代理服务器..."
	@chmod +x scripts/service.sh
	@./scripts/service.sh restart

# 查看服务状态
status: ## 查看服务状态
	@echo "查看SOCKS5代理服务器状态..."
	@chmod +x scripts/service.sh
	@./scripts/service.sh status

# 清理构建文件
clean: ## 清理构建文件
	@echo "清理构建文件..."
	@rm -rf $(BINARY_DIR)
	@rm -rf $(DIST_DIR)
	@rm -rf $(DIST_LINUX_DIR)
	@rm -rf $(WEB_DIR)/build
	@rm -rf $(WEB_DIR)/node_modules
	@echo "清理完成！"

# 测试
test: ## 运行测试
	@echo "运行测试..."
	@go test ./...

# 安装依赖
deps: ## 安装Go依赖
	@echo "安装Go依赖..."
	@go mod tidy
	@go mod download

# 前端依赖
web-deps: ## 安装前端依赖
	@echo "安装前端依赖..."
	@cd $(WEB_DIR) && npm install

# 数据库测试
db-test: ## 测试数据库连接
	@echo "测试数据库连接..."
	@chmod +x scripts/test-db.sh
	@./scripts/test-db.sh

# 数据库初始化
db-init: ## 初始化数据库
	@echo "初始化数据库..."
	@echo "请确保MySQL服务已启动，然后运行："
	@echo "mysql -u socks5_user -p socks5_db < scripts/init.sql"

# 创建发布包
dist: build ## 创建发布包
	@echo "创建发布包..."
	@mkdir -p $(DIST_DIR)
	@cp -r $(BINARY_DIR) $(DIST_DIR)/
	@cp -r $(CONFIG_DIR) $(DIST_DIR)/
	@cp -r $(WEB_DIR)/build $(DIST_DIR)/web/
	@cp -r scripts $(DIST_DIR)/
	@cp README.md $(DIST_DIR)/
	@echo "发布包创建完成！位于: $(DIST_DIR)/"

# 创建Linux发布包
dist-linux: build-linux ## 创建Linux发布包
	@echo "创建Linux发布包..."
	@mkdir -p $(DIST_LINUX_DIR)
	@cp -r $(BINARY_DIR) $(DIST_LINUX_DIR)/
	@cp -r $(CONFIG_DIR) $(DIST_LINUX_DIR)/
	@cp -r $(WEB_DIR)/build $(DIST_LINUX_DIR)/web/
	@cp -r scripts $(DIST_LINUX_DIR)/
	@cp README.md $(DIST_LINUX_DIR)/
	@echo "Linux发布包创建完成！位于: $(DIST_LINUX_DIR)/"

# 帮助信息
help: ## 显示帮助信息
	@echo "SOCKS5代理服务器管理命令："
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "使用示例："
	@echo "  make build    # 构建项目"
	@echo "  make start    # 启动服务"
	@echo "  make stop     # 停止服务"
	@echo "  make dev      # 开发模式"
	@echo "  make clean    # 清理文件"
	@echo "  make db-test  # 测试数据库连接"
	@echo "  make db-init  # 初始化数据库"
