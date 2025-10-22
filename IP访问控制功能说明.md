# IP访问控制功能说明

## 功能概述

SOCKS5 代理现在支持基于 IP 地址和 CIDR 网段的访问控制，可以灵活地管理哪些 IP 可以通过代理访问。

## 功能特性

### 1. IP黑名单
- ✅ 支持单个 IP 地址（如：`192.168.1.1`）
- ✅ 支持 CIDR 网段格式（如：`192.168.10.0/24`）
- ✅ 匹配到黑名单的 IP 将被阻止访问
- ✅ 支持启用/禁用状态
- ✅ 支持添加描述信息

### 2. IP白名单
- ✅ 支持单个 IP 地址
- ✅ 如果白名单不为空，只允许白名单中的 IP 通过
- ✅ 支持启用/禁用状态
- ✅ 支持添加描述信息

### 3. 过滤逻辑
执行顺序：
1. **白名单检查**：如果配置了白名单规则，且目标 IP 不在白名单中，则拒绝
2. **黑名单检查**：检查目标 IP 是否匹配黑名单规则（支持 CIDR 匹配）
3. **通过**：如果没有匹配到任何限制规则，则允许通过

## 数据库表结构

### IP黑名单表 (ip_blacklists)
```sql
CREATE TABLE ip_blacklists (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cidr VARCHAR(50) NOT NULL,           -- IP或CIDR，如：192.168.10.0/24
  description TEXT,                     -- 描述信息
  enabled TINYINT(1) DEFAULT 1,         -- 是否启用
  created_at DATETIME,
  updated_at DATETIME,
  INDEX idx_enabled (enabled)
);
```

### IP白名单表 (ip_whitelists)
```sql
CREATE TABLE ip_whitelists (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  ip VARCHAR(50) NOT NULL,              -- IP地址
  description TEXT,                     -- 描述信息
  enabled TINYINT(1) DEFAULT 1,         -- 是否启用
  created_at DATETIME,
  updated_at DATETIME,
  INDEX idx_enabled (enabled)
);
```

## API 接口

### IP黑名单 API

#### 获取黑名单列表
```bash
GET /api/v1/ip-blacklist
Authorization: Bearer <token>
```

#### 添加黑名单规则
```bash
POST /api/v1/ip-blacklist
Authorization: Bearer <token>
Content-Type: application/json

{
  "cidr": "192.168.10.0/24",
  "description": "测试网段",
  "enabled": true
}
```

#### 更新黑名单规则
```bash
PUT /api/v1/ip-blacklist/:id
Authorization: Bearer <token>
Content-Type: application/json

{
  "cidr": "192.168.10.0/24",
  "description": "更新后的描述",
  "enabled": true
}
```

#### 删除黑名单规则
```bash
DELETE /api/v1/ip-blacklist/:id
Authorization: Bearer <token>
```

### IP白名单 API

接口格式与黑名单类似，路径为 `/api/v1/ip-whitelist`

## Web 管理界面

访问路径：`/ip-control`

### 功能说明

1. **黑名单标签页**
   - 显示所有黑名单规则
   - 支持添加单个 IP 或 CIDR 网段
   - 支持启用/禁用规则
   - 显示创建时间

2. **白名单标签页**
   - 显示所有白名单规则
   - 支持添加单个 IP 地址
   - 支持启用/禁用规则
   - 显示创建时间

## 使用示例

### 示例1：屏蔽某个网段
添加黑名单规则：
- CIDR: `192.168.10.0/24`
- 描述: 屏蔽内网测试网段
- 状态: 启用

效果：所有 `192.168.10.1` - `192.168.10.254` 的 IP 将无法通过代理访问

### 示例2：只允许特定IP访问
添加白名单规则：
- IP: `192.168.1.100`
- 描述: 管理员办公IP
- 状态: 启用

效果：只有 `192.168.1.100` 可以通过代理访问

### 示例3：屏蔽单个IP
添加黑名单规则：
- CIDR: `10.0.0.50`
- 描述: 屏蔽异常IP
- 状态: 启用

效果：`10.0.0.50` 将无法通过代理访问

## 性能优化

- ✅ 使用缓存机制，每60秒自动刷新一次规则
- ✅ 避免频繁查询数据库
- ✅ 使用读写锁保证并发安全
- ✅ 规则修改后60秒内自动生效，无需重启服务

## 日志记录

被过滤的访问会记录在日志中：
```
IP被过滤 - 用户: testuser, 目标: 192.168.10.100, 原因: 匹配IP黑名单规则: 192.168.10.0/24 (测试网段)
```

## 注意事项

1. **白名单优先**：如果配置了白名单，只有白名单中的 IP 才能通过
2. **CIDR 格式**：黑名单支持 CIDR 格式，白名单只支持单个 IP
3. **立即生效**：规则修改后，最多 60 秒后生效（缓存刷新周期）
4. **谨慎使用白名单**：配置白名单后，所有不在白名单中的 IP 都会被拒绝

## 测试验证

1. 在管理界面添加黑名单规则：`192.168.10.0/24`
2. 使用该网段的 IP 尝试通过代理访问
3. 查看日志文件 `logs/proxy.log`，确认拦截信息
4. 在管理界面禁用该规则，验证可以正常访问

## 服务状态

- ✅ Server 服务：运行中（端口 8012）
- ✅ Proxy 服务：运行中（端口 1082）
- ✅ IP黑名单表：已创建
- ✅ IP白名单表：已创建
- ✅ API 接口：已注册
- ✅ Web 界面：已部署

访问管理界面：http://localhost:8012

