# SOCKS5 代理服务器快速开始指南

## 环境要求

- Go 1.21+
- Node.js 18+ (前端开发)
- MySQL 8.0+

## 快速部署

### 方法一：使用Docker Compose（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd socks5-app
```

2. **使用Docker Compose启动**
```bash
docker-compose up -d
```

3. **访问管理界面**
```
http://localhost:8012
```

### 方法二：手动部署

1. **准备MySQL数据库**
```sql
-- 创建数据库
CREATE DATABASE socks5_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'socks5_user'@'%' IDENTIFIED BY 'socks5_password';
GRANT ALL PRIVILEGES ON socks5_db.* TO 'socks5_user'@'%';
FLUSH PRIVILEGES;

-- 运行初始化脚本
mysql -u socks5_user -p socks5_db < scripts/init.sql
```

2. **安装依赖**
```bash
# Go依赖
go mod tidy

# 前端依赖
cd web && npm install && cd ..
```

3. **构建项目**
```bash
make build
```

4. **启动服务**
```bash
make start
```

## 默认配置

- **Web管理界面**: http://localhost:8012
- **SOCKS5代理端口**: 1080
- **MySQL端口**: 3306
- **默认管理员账户**: admin / password

## 功能特性

### 🔐 用户认证系统
- 用户名密码认证
- JWT令牌管理
- 角色权限控制

### 📊 流量控制
- 实时流量监控
- 带宽限制设置
- 流量统计图表

### 🌐 IP代理
- 非匿名SOCKS5代理
- IP白名单管理
- 客户端IP记录

### 🚫 URL过滤
- 网站访问控制
- 黑白名单管理
- 正则表达式匹配

### 👥 用户在线监控
- 实时用户状态
- 连接会话管理
- 强制断开连接

### 📝 日志审计
- 完整的操作日志
- 访问记录追踪
- 日志导出功能

## 配置说明

### 代理服务器配置
编辑 `configs/config.yaml` 文件：

```yaml
proxy:
  port: "1080"           # SOCKS5代理端口
  host: "0.0.0.0"        # 监听地址
  timeout: 30            # 连接超时时间
  max_connections: 1000  # 最大连接数
```

### Web管理界面配置
```yaml
server:
  port: "8012"           # Web服务端口
  host: "0.0.0.0"        # 监听地址
  mode: "debug"          # 运行模式
  jwt_key: "your-secret-key"  # JWT密钥
```

### 数据库配置
```yaml
database:
  driver: "mysql"        # 数据库驱动
  host: "localhost"      # 数据库主机
  port: "3306"          # 数据库端口
  username: "socks5_user"    # 数据库用户名
  password: "socks5_password" # 数据库密码
  database: "socks5_db"      # 数据库名称
```

## 使用示例

### 1. 创建用户
通过Web界面或API创建新用户：

```bash
curl -X POST http://localhost:8080/api/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com",
    "role": "user"
  }'
```

### 2. 设置带宽限制
```bash
curl -X POST http://localhost:8080/api/v1/traffic/limit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "limit": 1048576,
    "period": "daily"
  }'
```

### 3. 添加URL过滤规则
```bash
curl -X POST http://localhost:8080/api/v1/filters \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "*.google.com",
    "type": "block",
    "description": "阻止访问Google"
  }'
```

## 客户端配置

### 使用SOCKS5代理
配置客户端使用SOCKS5代理：

- **代理地址**: 127.0.0.1
- **代理端口**: 1080
- **认证方式**: 用户名密码
- **用户名**: 您在系统中创建的用户名
- **密码**: 对应的密码

### 支持的客户端
- Chrome/Edge (使用SwitchyOmega插件)
- Firefox (内置代理设置)
- curl (使用--socks5参数)
- wget (使用--proxy参数)

## 数据库管理

### 连接数据库
```bash
mysql -u socks5_user -p socks5_db
```

### 查看表结构
```sql
SHOW TABLES;
DESCRIBE users;
DESCRIBE proxy_sessions;
```

### 备份数据库
```bash
mysqldump -u socks5_user -p socks5_db > backup.sql
```

### 恢复数据库
```bash
mysql -u socks5_user -p socks5_db < backup.sql
```

## 故障排除

### 1. 服务启动失败
检查端口是否被占用：
```bash
netstat -tlnp | grep :8080
netstat -tlnp | grep :1080
netstat -tlnp | grep :3306
```

### 2. 数据库连接失败
检查MySQL服务状态：
```bash
systemctl status mysql
# 或
service mysql status
```

检查数据库连接：
```bash
mysql -u socks5_user -p -h localhost socks5_db
```

### 3. 前端无法访问
检查前端构建文件：
```bash
ls -la web/build/
```

### 4. Docker容器问题
查看容器日志：
```bash
docker-compose logs socks5-app
docker-compose logs mysql
```

重启服务：
```bash
docker-compose restart
```

## 安全建议

1. **修改默认密码**
   - 首次登录后立即修改默认管理员密码
   - 修改MySQL root密码

2. **配置防火墙**
   - 只开放必要的端口
   - 限制访问来源IP

3. **定期备份**
   - 备份数据库文件
   - 备份配置文件

4. **监控日志**
   - 定期检查访问日志
   - 监控异常连接

5. **数据库安全**
   - 使用强密码
   - 限制数据库访问IP
   - 定期更新MySQL版本

## 性能优化

### 数据库优化
```sql
-- 添加索引
CREATE INDEX idx_timestamp ON traffic_logs(timestamp);
CREATE INDEX idx_user_status ON users(username, status);

-- 优化查询
EXPLAIN SELECT * FROM traffic_logs WHERE timestamp > DATE_SUB(NOW(), INTERVAL 1 HOUR);
```

### 应用优化
- 调整连接池大小
- 启用数据库连接复用
- 配置适当的日志级别

## 技术支持

如遇到问题，请检查：
1. 日志文件 (`logs/` 目录)
2. 配置文件 (`configs/config.yaml`)
3. 数据库连接状态
4. 系统资源使用情况

更多信息请参考完整文档。
