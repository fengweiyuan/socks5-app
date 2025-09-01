# 多阶段构建
FROM node:18-alpine AS frontend-builder

# 设置工作目录
WORKDIR /app

# 复制前端文件
COPY web/package*.json ./
RUN npm ci --only=production

# 复制前端源码
COPY web/ ./
RUN npm run build

# Go构建阶段
FROM golang:1.21-alpine AS backend-builder

# 安装必要的包
RUN apk add --no-cache git ca-certificates tzdata

# 设置工作目录
WORKDIR /app

# 复制Go模块文件
COPY go.mod go.sum ./
RUN go mod download

# 复制源码
COPY . .

# 构建后端服务
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o server cmd/server/main.go
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o proxy cmd/proxy/main.go

# 最终运行阶段
FROM alpine:latest

# 安装必要的包
RUN apk --no-cache add ca-certificates tzdata mysql-client

# 创建非root用户
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# 设置工作目录
WORKDIR /app

# 从构建阶段复制文件
COPY --from=backend-builder /app/server .
COPY --from=backend-builder /app/proxy .
COPY --from=frontend-builder /app/build ./web/build
COPY configs/ ./configs/
COPY scripts/ ./scripts/

# 创建必要的目录
RUN mkdir -p logs data && \
    chown -R appuser:appgroup /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8080 1080

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/v1/system/status || exit 1

# 启动命令
CMD ["./server"]
