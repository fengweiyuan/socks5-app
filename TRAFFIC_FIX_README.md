# 仪表盘流量显示问题修复说明

## 问题描述
仪表盘的「总流量」、「发送流量」、「接收流量」显示为 `NaN undefined`

## 问题原因
1. **后端数据库查询返回 NULL 值**：当没有流量数据时，`SUM()` 函数返回 `NULL`
2. **前端数据处理不当**：没有正确处理 `null`、`undefined` 或无效数值
3. **缺少错误处理**：数据库查询失败时没有提供合理的默认值

## 修复方案

### 1. 后端修复 (internal/api/traffic.go)

#### 使用 COALESCE 函数处理 NULL 值
```sql
SELECT COALESCE(SUM(bytes_sent), 0) as total_sent, COALESCE(SUM(bytes_recv), 0) as total_recv
```

#### 改进错误处理
- 使用事务确保数据一致性
- 为每个查询添加错误处理
- 查询失败时返回默认值而不是崩溃

#### 处理指针类型
```go
var result struct {
    TotalSent *int64 `json:"total_sent"`
    TotalRecv *int64 `json:"total_recv"`
}
```

### 2. 前端修复 (web/src/views/Dashboard.vue)

#### 改进 formatBytes 函数
```javascript
const formatBytes = (bytes) => {
  // 处理无效值
  if (bytes === null || bytes === undefined || isNaN(bytes) || bytes < 0) {
    return '0 B'
  }
  
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
```

#### 改进数据获取逻辑
```javascript
// 确保数据存在且为有效值
if (statsRes && statsRes.stats) {
  stats.value = {
    totalBytesSent: statsRes.stats.total_bytes_sent || 0,
    totalBytesRecv: statsRes.stats.total_bytes_recv || 0,
    activeConnections: statsRes.stats.active_connections || 0,
    totalUsers: statsRes.stats.total_users || 0,
    onlineUsers: statsRes.stats.online_users || 0
  }
}
```

#### 添加错误处理和默认值
```javascript
} catch (error) {
  console.error('获取仪表盘数据失败:', error)
  // 设置默认值避免显示 NaN
  stats.value = {
    totalBytesSent: 0,
    totalBytesRecv: 0,
    activeConnections: 0,
    totalUsers: 0,
    onlineUsers: 0
  }
  onlineUsers.value = []
}
```

### 3. 测试数据 (scripts/insert_sample_traffic.sql)

创建了示例流量数据脚本，包含：
- 示例流量日志数据
- 示例代理会话数据
- 流量统计查询示例

## 使用方法

### 1. 重启后端服务
```bash
cd /path/to/socks5-app
make restart-server
```

### 2. 插入测试数据（可选）
```bash
mysql -u username -p socks5_db < scripts/insert_sample_traffic.sql
```

### 3. 刷新前端页面
重新加载仪表盘页面，流量数据应该正常显示

## 验证修复

1. **检查后端日志**：确认没有数据库查询错误
2. **检查前端控制台**：确认没有 JavaScript 错误
3. **验证数据显示**：流量数据应该显示为 "0 B" 或实际的字节数
4. **测试边界情况**：即使没有数据也应该显示 "0 B" 而不是 NaN

## 预防措施

1. **数据验证**：前后端都要验证数据的有效性
2. **错误处理**：为所有可能的错误情况提供合理的默认值
3. **日志记录**：记录错误信息便于调试
4. **单元测试**：为关键函数添加测试用例
