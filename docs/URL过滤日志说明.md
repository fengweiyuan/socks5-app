# URL过滤日志说明

## 功能概述

当URL过滤规则阻止用户访问某个地址时，系统会记录详细的日志信息，包括：
- 用户信息（用户名、用户ID）
- 被阻止的目标地址
- 匹配的过滤规则信息（规则ID、Pattern、描述）

## 日志格式

### 主要日志
当URL被过滤阻止时，会输出以下格式的日志：

```
URL过滤: 阻止访问 | 用户: <用户名> (ID:<用户ID>) | 目标地址: <目标域名或IP> | 匹配规则: [ID:<规则ID>] Pattern:'<匹配模式>' | 描述: <规则描述>
```

### 日志示例

**示例1: 阻止访问百度**
```
URL过滤: 阻止访问 | 用户: testuser (ID:4) | 目标地址: baidu.com | 匹配规则: [ID:5] Pattern:'baidu.com' | 描述: 测试日志输出 - 阻止百度
```

**示例2: 阻止访问社交媒体**
```
URL过滤: 阻止访问 | 用户: john (ID:12) | 目标地址: facebook.com | 匹配规则: [ID:3] Pattern:'facebook.com' | 描述: 阻止访问社交媒体网站
```

**示例3: 阻止访问色情网站**
```
URL过滤: 阻止访问 | 用户: employee001 (ID:25) | 目标地址: pornhub.com | 匹配规则: [ID:8] Pattern:'pornhub.com' | 描述: 禁止访问不良网站
```

### 附加日志
在主要日志之后，还会有一条错误日志：
```
处理请求失败: URL被过滤: <目标地址>
```

## 日志级别

- **主要日志**: `WARN` 级别（黄色警告）
- **附加日志**: `ERROR` 级别（红色错误）

这样设计的原因：
- `WARN` 级别表示这是一个预期的阻止行为，不是系统错误
- 使用 `WARN` 可以方便地过滤和统计被阻止的访问
- `ERROR` 级别的附加日志用于记录请求失败的上下文

## 日志位置

日志文件位置: `logs/proxy.log`

## 查看日志的方法

### 1. 实时查看所有日志
```bash
tail -f logs/proxy.log
```

### 2. 只查看URL过滤相关日志
```bash
tail -f logs/proxy.log | grep "URL过滤"
```

### 3. 查看最近100条URL过滤日志
```bash
grep "URL过滤" logs/proxy.log | tail -100
```

### 4. 统计被阻止的访问次数
```bash
grep "URL过滤: 阻止访问" logs/proxy.log | wc -l
```

### 5. 查看特定用户被阻止的访问
```bash
grep "URL过滤: 阻止访问 | 用户: testuser" logs/proxy.log
```

### 6. 查看特定规则阻止的访问
```bash
grep "匹配规则: \[ID:5\]" logs/proxy.log
```

### 7. 按目标地址统计被阻止次数
```bash
grep "URL过滤: 阻止访问" logs/proxy.log | grep -oP "目标地址: \K[^ |]+" | sort | uniq -c | sort -rn
```

## 日志分析示例

### 场景1: 审计用户访问
管理员可以通过日志查看哪些用户尝试访问被阻止的网站：

```bash
grep "URL过滤: 阻止访问" logs/proxy.log | grep -oP "用户: \K[^ ]+" | sort | uniq -c | sort -rn
```

输出示例：
```
     15 testuser
      8 john
      3 employee001
```

### 场景2: 识别最常被访问的被阻止网站
了解哪些被阻止的网站访问频率最高：

```bash
grep "URL过滤: 阻止访问" logs/proxy.log | grep -oP "目标地址: \K[^ |]+" | sort | uniq -c | sort -rn | head -10
```

输出示例：
```
     25 baidu.com
     12 facebook.com
      8 twitter.com
      5 pornhub.com
```

### 场景3: 检查特定规则的效果
查看某条规则阻止了多少次访问：

```bash
grep "匹配规则: \[ID:5\]" logs/proxy.log
```

### 场景4: 按时间段分析
查看今天的URL过滤日志：

```bash
grep "$(date +%Y-%m-%d)" logs/proxy.log | grep "URL过滤"
```

## 与数据库的关联

日志中的规则ID可以在数据库中查询到详细信息：

```sql
-- 查看规则详情
SELECT * FROM url_filters WHERE id = 5;

-- 查看所有启用的规则
SELECT id, pattern, type, description, enabled 
FROM url_filters 
WHERE enabled = 1 
ORDER BY id;
```

## 日志轮转建议

为避免日志文件过大，建议配置日志轮转：

```bash
# 使用logrotate
cat > /etc/logrotate.d/socks5-proxy << EOF
/Users/fwy/code/pub/socks5-app/logs/proxy.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 fwy fwy
    postrotate
        kill -USR1 \$(cat /Users/fwy/code/pub/socks5-app/logs/proxy.pid)
    endscript
}
EOF
```

## 监控告警建议

### 1. 异常访问告警
如果某个用户短时间内被阻止多次，可能需要调查：

```bash
# 统计最近1小时内每个用户被阻止的次数
tail -10000 logs/proxy.log | grep "URL过滤: 阻止访问" | \
  grep "$(date +%Y-%m-%d\ %H)" | \
  grep -oP "用户: \K[^ ]+" | sort | uniq -c | sort -rn
```

### 2. 规则效果监控
定期检查哪些规则实际在起作用：

```bash
# 统计各规则阻止的访问次数
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "匹配规则: \[ID:\K[0-9]+" | sort | uniq -c | sort -rn
```

输出示例：
```
    150 5    # 规则5阻止了150次访问
     45 3    # 规则3阻止了45次访问
     12 8    # 规则8阻止了12次访问
      2 15   # 规则15阻止了2次访问
```

## 故障排查

### 问题1: 看不到URL过滤日志
**可能原因:**
1. 日志级别设置过高，过滤了WARN级别
2. 代理服务没有重启，使用的是旧版本代码
3. 过滤规则没有生效

**解决方法:**
```bash
# 检查日志级别配置
grep "level:" configs/config.yaml

# 检查代理服务是否运行新版本
ps aux | grep proxy

# 重启代理服务
./scripts/service.sh restart proxy
```

### 问题2: 日志信息不完整
**可能原因:**
1. 数据库中的规则缺少描述字段

**解决方法:**
```sql
-- 检查规则信息
SELECT id, pattern, description FROM url_filters WHERE id = 5;

-- 更新规则描述
UPDATE url_filters SET description = '描述信息' WHERE id = 5;
```

## 性能影响

添加详细日志对性能的影响：
- **磁盘I/O**: 每次阻止访问会写入约150-200字节的日志
- **CPU**: 字符串格式化的开销极小（< 1ms）
- **总体影响**: 可以忽略不计

## 隐私保护建议

日志中包含敏感信息（用户名、访问目标），建议：

1. **限制日志文件访问权限**
   ```bash
   chmod 600 logs/proxy.log
   chown proxy:proxy logs/proxy.log
   ```

2. **定期清理旧日志**
   ```bash
   find logs/ -name "proxy.log.*" -mtime +90 -delete
   ```

3. **避免在公共环境查看日志**
   不要在屏幕共享或演示时展示包含真实用户信息的日志

## 测试工具

我们提供了测试脚本来验证日志功能：

```bash
# 测试URL过滤日志
python3 scripts/test_url_filter_logs.py

# 测试URL过滤功能（包括日志）
python3 scripts/test_url_filter_simple.py
```

## 后续改进建议

1. **结构化日志**: 考虑使用JSON格式的日志，便于机器解析
2. **日志聚合**: 集成ELK（Elasticsearch + Logstash + Kibana）进行日志分析
3. **实时告警**: 使用日志监控工具（如Grafana Loki）实现实时告警
4. **统计报表**: 定期生成URL过滤统计报表

## 相关文档

- [URL过滤测试报告.md](./URL过滤测试报告.md) - URL过滤功能测试文档
- [SOCKS5限流机制文档.md](./SOCKS5限流机制文档.md) - 流量控制相关文档

