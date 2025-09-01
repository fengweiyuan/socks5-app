# SOCKS5 代理服务器管理系统

一个功能完整的SOCKS5代理服务器，使用Go语言开发，提供Web管理界面和丰富的管理功能。

## 功能特性

- 🔐 **用户认证系统** - 支持用户名密码认证
- 📊 **流量控制** - 带宽限制和流量统计
- 🌐 **IP代理** - 非匿名代理，支持IP白名单
- 🚫 **URL过滤** - 网站访问控制和黑名单
- 👥 **用户在线监控** - 实时用户状态显示
- 📝 **日志审计** - 完整的操作和访问日志
- 🎨 **美观的Web界面** - 现代化的管理界面
- 🔧 **RESTful API** - 完整的后端管理接口

## 系统架构

```
socks5-app/
├── cmd/              # 主程序入口
│   ├── server/       # 主服务器
│   └── proxy/        # SOCKS5代理服务
├── internal/         # 内部包
│   ├── auth/         # 认证模块
│   ├── proxy/        # 代理核心
│   ├── api/          # API接口
│   ├── config/       # 配置管理
│   ├── database/     # 数据库操作
│   ├── logger/       # 日志系统
│   └── middleware/   # 中间件
├── web/              # Web前端界面
├── configs/          # 配置文件
├── scripts/          # 部署脚本
└── docs/             # 文档
```

## 技术栈

### 后端
- **语言**: Go 1.21+
- **Web框架**: Gin
- **数据库**: MySQL 8.0
- **认证**: JWT
- **日志**: Logrus
- **配置**: Viper

### 前端
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts

## 快速开始

### 环境要求
- Go 1.21+
- Node.js 18+ (前端开发)
- MySQL 8.0+

### 安装部署

1. **克隆项目**
```bash
git clone <repository-url>
cd socks5-app
```

2. **使用Docker Compose启动（推荐）**
```bash
docker-compose up -d
```

3. **访问管理界面**
```
http://localhost:8012
默认账户: admin / password
```

### 手动部署

1. **准备MySQL数据库**
```sql
-- 创建数据库
CREATE DATABASE socks5_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'socks5_user'@'%' IDENTIFIED BY 'socks5_password';
GRANT ALL PRIVILEGES ON socks5_db.* TO 'socks5_user'@'%';
FLUSH PRIVILEGES;
```

2. **安装依赖**
```bash
# Go依赖
go mod tidy

# 前端依赖
cd web && npm install
```

3. **配置数据库连接**
编辑 `configs/config.yaml` 文件：l
```yaml
database:
  driver: "mysql"
  host: "localhost"
  port: "3306"
  username: "socks5_user"
  password: "socks5_password"
  database: "socks5_db"
```

4. **构建并运行**
```bash
# 构建项目
make build

# 启动服务
make start
```

## 配置说明

### 代理服务器配置
- 默认端口: 1080
- 认证方式: 用户名密码
- 日志级别: INFO

### Web管理界面
- 端口: 8012
- 认证: JWT Token
- 数据库: MySQL

### 数据库配置
- **类型**: MySQL 8.0
- **字符集**: utf8mb4
- **排序规则**: utf8mb4_unicode_ci
- **连接池**: 支持连接池配置

## API文档

### 用户管理
- `GET /api/v1/users` - 获取用户列表
- `POST /api/v1/users` - 创建用户
- `PUT /api/v1/users/:id` - 更新用户
- `DELETE /api/v1/users/:id` - 删除用户

### 流量控制
- `GET /api/v1/traffic` - 获取流量统计
- `POST /api/v1/traffic/limit` - 设置带宽限制
- `GET /api/v1/traffic/realtime` - 实时流量监控

### 日志管理
- `GET /api/v1/logs` - 获取日志列表
- `GET /api/v1/logs/export` - 导出日志
- `DELETE /api/v1/logs` - 清理日志

## 数据库结构

### 主要表结构
- `users` - 用户表
- `proxy_sessions` - 代理会话表
- `traffic_logs` - 流量日志表
- `access_logs` - 访问日志表
- `url_filters` - URL过滤规则表
- `ip_whitelists` - IP白名单表
- `bandwidth_limits` - 带宽限制表

### 数据库初始化
项目包含完整的数据库初始化脚本 `scripts/init.sql`，会自动创建所有必要的表和索引。

## 许可证

MIT License
