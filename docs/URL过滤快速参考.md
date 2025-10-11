# URL过滤功能快速参考

## 🚀 快速开始

### 查看实时日志
```bash
tail -f logs/proxy.log | grep "URL过滤"
```

### 运行测试
```bash
# 综合测试（推荐）
python3 scripts/test_url_filter_comprehensive.py

# 快速测试
python3 scripts/test_url_filter_simple.py
```

---

## 📋 常用命令

### 日志查询

```bash
# 查看最近50条过滤日志
grep "URL过滤: 阻止访问" logs/proxy.log | tail -50

# 统计总阻止次数
grep "URL过滤: 阻止访问" logs/proxy.log | wc -l

# 按用户统计
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "用户: \K[^ ]+" | sort | uniq -c | sort -rn

# 按域名统计
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "目标地址: \K[^ |]+" | sort | uniq -c | sort -rn

# 按规则统计
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep -oP "匹配规则: \[ID:\K[0-9]+" | sort | uniq -c | sort -rn
```

### 数据库操作

```bash
# 连接数据库
mysql -h 127.0.0.1 -u socks5_user -p socks5_db

# 或者使用Python脚本
python3 scripts/diagnose_url_filters.py
```

```sql
-- 查看所有规则
SELECT id, pattern, type, description, enabled FROM url_filters;

-- 创建规则
INSERT INTO url_filters (pattern, type, description, enabled, created_at, updated_at)
VALUES ('baidu.com', 'block', '阻止百度', 1, NOW(), NOW());

-- 禁用规则
UPDATE url_filters SET enabled = 0 WHERE id = 1;

-- 删除规则
DELETE FROM url_filters WHERE id = 1;

-- 清空所有规则
DELETE FROM url_filters;
```

---

## 🧪 测试工具

| 脚本 | 用途 | 命令 |
|------|------|------|
| 综合测试 | 9个场景全面测试 | `python3 scripts/test_url_filter_comprehensive.py` |
| 简单测试 | 快速验证基本功能 | `python3 scripts/test_url_filter_simple.py` |
| 日志测试 | 验证日志完整性 | `python3 scripts/test_url_filter_logs.py` |
| 演示脚本 | 展示日志效果 | `python3 scripts/demo_url_filter_logs.py` |
| 诊断工具 | 检查规则配置 | `python3 scripts/diagnose_url_filters.py` |

---

## 📊 日志格式

```
URL过滤: 阻止访问 | 用户: testuser (ID:4) | 目标地址: baidu.com | 匹配规则: [ID:5] Pattern:'baidu.com' | 描述: 阻止百度
```

**包含信息:**
- 用户名和ID
- 目标域名/IP
- 匹配的规则ID和Pattern
- 规则描述

---

## ✅ 推荐做法

### 创建规则
```sql
-- ✅ 使用完整域名
INSERT INTO url_filters (pattern, type, description, enabled)
VALUES ('facebook.com', 'block', '公司政策: 禁止访问社交媒体', 1);

-- ✅ 添加清晰的描述
INSERT INTO url_filters (pattern, type, description, enabled)
VALUES ('pornhub.com', 'block', '内容过滤: 禁止成人内容', 1);

-- ✅ 使用部分匹配阻止一类网站
INSERT INTO url_filters (pattern, type, description, enabled)
VALUES ('porn', 'block', '内容过滤: 阻止所有色情网站', 1);
```

### 日常维护
```bash
# 每周审查日志
grep "URL过滤: 阻止访问" logs/proxy.log | \
  grep "$(date -v-7d +%Y-%m-%d)" | wc -l

# 检查规则效果
python3 scripts/diagnose_url_filters.py

# 定期清理无效规则
mysql -h 127.0.0.1 -u socks5_user -p -e \
  "SELECT * FROM socks5_db.url_filters WHERE enabled = 1;"
```

---

## ❌ 避免的做法

### 危险的Pattern

```sql
-- ❌ 不要使用过短的pattern
INSERT INTO url_filters (pattern, type, description, enabled)
VALUES ('com', 'block', '...', 1);  -- 会阻止所有.com域名

-- ❌ 不要使用单字符
INSERT INTO url_filters (pattern, type, description, enabled)
VALUES ('.', 'block', '...', 1);  -- 会阻止所有域名

-- ❌ 不要使用内网IP段
INSERT INTO url_filters (pattern, type, description, enabled)
VALUES ('192', 'block', '...', 1);  -- 会阻止192.168.x.x
```

---

## 🔍 故障排查

### 问题1: 规则不生效
```bash
# 检查规则是否启用
mysql -h 127.0.0.1 -u socks5_user -p -e \
  "SELECT * FROM socks5_db.url_filters WHERE enabled = 1;"

# 检查代理服务是否运行
ps aux | grep proxy

# 重启代理服务
kill $(cat logs/proxy.pid)
nohup ./bin/proxy -port 1082 -host 0.0.0.0 > logs/proxy.log 2>&1 &
echo $! > logs/proxy.pid
```

### 问题2: 看不到日志
```bash
# 检查日志文件
tail -20 logs/proxy.log

# 手动触发一次阻止
python3 scripts/test_url_filter_logs.py

# 检查日志级别
grep "level:" configs/config.yaml
```

### 问题3: 误阻止内网地址
```bash
# 检查是否有过于宽泛的规则
python3 scripts/diagnose_url_filters.py

# 查看具体哪条规则导致
grep "URL过滤: 阻止访问" logs/proxy.log | grep "192.168"
```

---

## 📈 性能优化

### 规则数量建议
- **< 100条**: 无需优化，性能良好
- **100-500条**: 考虑添加索引
- **> 500条**: 建议使用规则缓存

### 添加索引
```sql
-- 为常用查询添加索引
CREATE INDEX idx_enabled_pattern ON url_filters(enabled, pattern);
```

### 规则缓存（代码层面）
```go
// 缓存规则，减少数据库查询
var filterCache []database.URLFilter
var cacheTime time.Time
var cacheDuration = 5 * time.Minute

// 在checkURLFilter中使用缓存
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [URL过滤测试报告.md](./URL过滤测试报告.md) | 基础功能测试 |
| [URL过滤综合测试报告.md](./URL过滤综合测试报告.md) | 9个场景全面测试 |
| [URL过滤日志功能说明.md](./URL过滤日志功能说明.md) | 日志功能详细说明 |
| [URL过滤日志说明.md](./URL过滤日志说明.md) | 日志分析方法 |

---

## 💡 小技巧

### 1. 实时监控被阻止的访问
```bash
watch -n 5 'grep "URL过滤: 阻止访问" logs/proxy.log | tail -10'
```

### 2. 生成每日报告
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
echo "URL过滤日报 - $DATE"
echo "总阻止次数:"
grep "URL过滤: 阻止访问" logs/proxy.log | grep "$DATE" | wc -l
echo ""
echo "Top 10 被阻止的网站:"
grep "URL过滤: 阻止访问" logs/proxy.log | grep "$DATE" | \
  grep -oP "目标地址: \K[^ |]+" | sort | uniq -c | sort -rn | head -10
```

### 3. 导出规则到Excel
```bash
# 导出为CSV
mysql -h 127.0.0.1 -u socks5_user -p -e \
  "SELECT id, pattern, type, description, enabled FROM socks5_db.url_filters;" \
  | sed 's/\t/,/g' > url_filters_export.csv
```

### 4. 批量导入规则
```python
import pymysql

rules = [
    ("facebook.com", "block", "社交媒体"),
    ("twitter.com", "block", "社交媒体"),
    ("youtube.com", "block", "视频网站"),
]

conn = pymysql.connect(host='127.0.0.1', user='socks5_user', 
                       password='socks5_password', database='socks5_db')
cursor = conn.cursor()

for pattern, type, desc in rules:
    cursor.execute(
        "INSERT INTO url_filters (pattern, type, description, enabled, created_at, updated_at) "
        "VALUES (%s, %s, %s, 1, NOW(), NOW())",
        (pattern, type, desc)
    )

conn.commit()
cursor.close()
conn.close()
```

---

## 🎯 最佳实践总结

1. ✅ **使用完整域名** - 避免误伤
2. ✅ **添加清晰描述** - 便于管理
3. ✅ **定期审查日志** - 了解使用情况
4. ✅ **测试后再部署** - 避免业务影响
5. ✅ **保持规则简洁** - 删除无效规则
6. ✅ **备份规则配置** - 防止误删除
7. ✅ **监控性能指标** - 及时发现问题

---

**更新时间**: 2025-10-11  
**版本**: 1.0

