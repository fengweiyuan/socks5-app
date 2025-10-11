# URL过滤日志功能说明

## 更新时间
2025年10月11日

## 功能概述

为URL过滤功能添加了详细的日志记录，当用户访问被阻止时，系统会记录完整的上下文信息，便于管理员审计和故障排查。

---

## ✨ 新增功能

### 1. 详细的阻止日志

当URL过滤规则阻止用户访问时，会记录以下信息：

| 字段 | 说明 | 示例 |
|------|------|------|
| 用户名 | 尝试访问的用户 | testuser |
| 用户ID | 用户的数据库ID | 4 |
| 目标地址 | 被阻止的目标域名/IP | baidu.com |
| 规则ID | 匹配的过滤规则ID | 5 |
| Pattern | 规则的匹配模式 | baidu.com |
| 规则描述 | 规则的说明信息 | 阻止访问百度 |

### 2. 日志格式

```
URL过滤: 阻止访问 | 用户: <用户名> (ID:<用户ID>) | 目标地址: <域名> | 匹配规则: [ID:<规则ID>] Pattern:'<匹配模式>' | 描述: <规则描述>
```

### 3. 实际日志示例

```
URL过滤: 阻止访问 | 用户: testuser (ID:4) | 目标地址: baidu.com | 匹配规则: [ID:5] Pattern:'baidu.com' | 描述: 测试日志输出 - 阻止百度
URL过滤: 阻止访问 | 用户: testuser (ID:4) | 目标地址: facebook.com | 匹配规则: [ID:6] Pattern:'facebook.com' | 描述: 阻止访问社交媒体网站
URL过滤: 阻止访问 | 用户: testuser (ID:4) | 目标地址: twitter.com | 匹配规则: [ID:7] Pattern:'twitter.com' | 描述: 阻止访问Twitter
URL过滤: 阻止访问 | 用户: testuser (ID:4) | 目标地址: pornhub.com | 匹配规则: [ID:8] Pattern:'pornhub.com' | 描述: 禁止访问不良网站
```

---

## 🔧 代码修改

### 修改的文件
`internal/proxy/socks5.go`

### 修改内容

#### 1. checkURLFilter 函数（431-463行）

**修改前:**
```go
for _, filter := range filters {
    if strings.Contains(targetAddr, filter.Pattern) {
        if filter.Type == "block" {
            return false  // 直接返回，无日志
        }
    }
}
```

**修改后:**
```go
for _, filter := range filters {
    if strings.Contains(targetAddr, filter.Pattern) {
        if filter.Type == "block" {
            // 记录详细的阻止日志
            logger.Log.Warnf(
                "URL过滤: 阻止访问 | 用户: %s (ID:%d) | 目标地址: %s | 匹配规则: [ID:%d] Pattern:'%s' | 描述: %s",
                user.Username,
                user.ID,
                targetAddr,
                filter.ID,
                filter.Pattern,
                filter.Description,
            )
            return false
        }
    }
}
```

#### 2. handleRequest 函数（296-300行）

**修改前:**
```go
if !s.checkURLFilter(client.user, targetAddr) {
    s.sendReply(client.conn, FAILED, targetAddr, int(port))
    return errors.New("URL被过滤")
}
```

**修改后:**
```go
if !s.checkURLFilter(client.user, targetAddr) {
    s.sendReply(client.conn, FAILED, targetAddr, int(port))
    return fmt.Errorf("URL被过滤: %s", targetAddr)
}
```

---

## 📊 使用场景

### 场景1: 审计用户行为
管理员可以查看哪些用户尝试访问被禁止的网站：

```bash
# 统计各用户被阻止的次数
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "用户: \K[^ ]+" | sort | uniq -c | sort -rn
```

**输出示例:**
```
     45 employee001    # 员工001尝试了45次
     23 testuser       # testuser尝试了23次
      8 john           # john尝试了8次
```

### 场景2: 识别热门被阻止网站
了解哪些网站被访问次数最多：

```bash
# 统计被阻止网站的访问次数
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "目标地址: \K[^ |]+" | sort | uniq -c | sort -rn
```

**输出示例:**
```
     78 facebook.com   # Facebook被尝试访问78次
     45 baidu.com      # 百度被尝试访问45次
     23 twitter.com    # Twitter被尝试访问23次
```

### 场景3: 评估规则效果
查看每条规则阻止了多少次访问：

```bash
# 统计各规则的命中次数
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "匹配规则: \[ID:\K[0-9]+" | sort | uniq -c | sort -rn
```

**输出示例:**
```
    150 5    # 规则5命中150次
     78 6    # 规则6命中78次
     45 7    # 规则7命中45次
```

### 场景4: 实时监控
实时查看被阻止的访问：

```bash
# 实时显示URL过滤日志
tail -f logs/proxy.log | grep --line-buffered "URL过滤"
```

---

## 🧪 测试工具

### 1. 功能测试脚本
```bash
python3 scripts/test_url_filter_logs.py
```

**功能:**
- 创建测试过滤规则
- 尝试访问被阻止的网站
- 验证日志是否正确输出
- 检查日志内容完整性

### 2. 演示脚本
```bash
python3 scripts/demo_url_filter_logs.py
```

**功能:**
- 创建多条过滤规则
- 测试访问多个被阻止的网站
- 展示实际的日志输出效果

---

## 📈 日志分析命令

### 基础查询

```bash
# 查看所有URL过滤日志
grep "URL过滤" logs/proxy.log

# 查看最近100条
grep "URL过滤" logs/proxy.log | tail -100

# 实时查看
tail -f logs/proxy.log | grep "URL过滤"
```

### 统计分析

```bash
# 统计总的阻止次数
grep "URL过滤: 阻止访问" logs/proxy.log | wc -l

# 按用户统计
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "用户: \K[^ ]+" | sort | uniq -c | sort -rn

# 按目标地址统计
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "目标地址: \K[^ |]+" | sort | uniq -c | sort -rn

# 按规则统计
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "匹配规则: \[ID:\K[0-9]+" | sort | uniq -c | sort -rn
```

### 高级查询

```bash
# 查看特定用户的阻止记录
grep "URL过滤: 阻止访问 | 用户: testuser" logs/proxy.log

# 查看特定规则的阻止记录
grep "匹配规则: \[ID:5\]" logs/proxy.log

# 查看特定时间段的记录（今天）
grep "$(date +%Y-%m-%d)" logs/proxy.log | grep "URL过滤"

# 查看最近1小时的记录
grep "$(date +%Y-%m-%d\ %H)" logs/proxy.log | grep "URL过滤"
```

---

## 🔍 故障排查

### 问题: 看不到URL过滤日志

**可能原因:**
1. 代理服务没有重启，仍在使用旧版本
2. 日志级别设置过高
3. 过滤规则没有生效

**解决方法:**

```bash
# 1. 重新编译
cd /Users/fwy/code/pub/socks5-app
go build -o bin/proxy cmd/proxy/main.go

# 2. 重启代理服务
kill $(cat logs/proxy.pid)
nohup ./bin/proxy -port 1082 -host 0.0.0.0 > logs/proxy.log 2>&1 &
echo $! > logs/proxy.pid

# 3. 测试
python3 scripts/test_url_filter_logs.py
```

---

## 📝 日志管理建议

### 1. 日志轮转
避免日志文件过大：

```bash
# 每天轮转，保留30天
logs/proxy.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### 2. 定期清理
```bash
# 删除30天前的日志
find logs/ -name "proxy.log.*" -mtime +30 -delete
```

### 3. 权限控制
日志包含敏感信息，需要限制访问：

```bash
chmod 600 logs/proxy.log
chown proxy:proxy logs/proxy.log
```

---

## 💡 最佳实践

### 1. 规则描述要清晰
创建规则时，写清楚描述信息：

```sql
INSERT INTO url_filters (pattern, type, description, enabled) VALUES
('facebook.com', 'block', '公司政策：工作时间禁止访问社交媒体', 1),
('gambling.com', 'block', '安全策略：禁止访问赌博网站', 1),
('malware.com', 'block', '安全防护：已知恶意网站', 1);
```

### 2. 定期审查日志
建议每周审查一次URL过滤日志：
- 识别频繁被阻止的网站
- 发现异常访问行为
- 评估规则的有效性

### 3. 结合监控告警
对异常情况设置告警：
- 单个用户短时间内被阻止多次
- 新的恶意域名被访问
- 规则命中率异常

---

## 🚀 后续改进方向

### 1. 结构化日志
将日志格式改为JSON，便于机器解析：

```json
{
  "timestamp": "2025-10-11T15:30:45Z",
  "level": "WARN",
  "event": "url_filter_blocked",
  "user": {
    "id": 4,
    "username": "testuser"
  },
  "target": "baidu.com",
  "filter": {
    "id": 5,
    "pattern": "baidu.com",
    "description": "阻止访问百度"
  }
}
```

### 2. 数据库记录
除了日志文件，还可以在数据库中记录：

```sql
CREATE TABLE url_filter_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    target_address VARCHAR(255) NOT NULL,
    filter_id INT NOT NULL,
    timestamp DATETIME NOT NULL,
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_filter_timestamp (filter_id, timestamp)
);
```

### 3. 可视化仪表板
使用Grafana或类似工具展示：
- 阻止访问趋势图
- 用户行为热力图
- 规则效果统计

---

## 📚 相关文档

- [URL过滤测试报告.md](./URL过滤测试报告.md) - 过滤功能测试
- [URL过滤日志说明.md](./URL过滤日志说明.md) - 日志使用详细说明
- [架构说明.md](./架构说明.md) - 系统架构文档

---

## ✅ 总结

通过添加详细的URL过滤日志，管理员现在可以：

1. **审计用户行为** - 知道谁在访问什么
2. **评估规则效果** - 了解规则的实际作用
3. **发现异常访问** - 及时发现安全威胁
4. **优化过滤策略** - 基于数据调整规则

日志信息完整且易读，便于管理和分析。

