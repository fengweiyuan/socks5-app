# 数据库优化脚本部署指南

## 📋 概述

本指南详细说明了如何部署和使用SOCKS5代理服务器项目的数据库优化脚本，确保项目上线时获得最佳性能。

## 🚀 快速开始

### 1. 项目初始化（首次部署）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd socks5-app

# 2. 初始化数据库（包含优化索引）
mysql -u root -p < scripts/init.sql

# 3. 验证索引创建
mysql -u socks5_user -p socks5_db -e "SHOW INDEX FROM traffic_logs;"
```

### 2. 验证索引效果

```bash
# 执行索引性能测试
mysql -u socks5_user -p socks5_db < scripts/test_index_performance.sql
```

## 📁 脚本文件说明

### 核心脚本

| 脚本文件 | 用途 | 执行频率 | 说明 |
|---------|------|----------|------|
| `init.sql` | 数据库初始化 | 一次性 | 包含优化后的索引设计 |
| `test_index_performance.sql` | 性能测试 | 部署后验证 | 验证索引效果 |
| `cleanup_old_data.sql` | 数据清理 | 每周 | 清理历史数据 |
| `monitor_performance.sql` | 性能监控 | 每天 | 监控数据库健康状态 |
| `maintenance_automation.sh` | 自动化维护 | 定时任务 | 综合维护脚本 |

### 辅助文档

| 文档文件 | 内容 | 用途 |
|---------|------|------|
| `README.md` | 脚本使用说明 | 日常维护参考 |
| `INDEX_OPTIMIZATION.md` | 索引设计详解 | 技术细节了解 |
| `DEPLOYMENT_GUIDE.md` | 部署指南 | 部署和配置 |

## 🔧 部署步骤详解

### 步骤1：环境准备

```bash
# 1. 确保MySQL已安装并运行
sudo systemctl status mysql

# 2. 创建数据库用户（如果不存在）
mysql -u root -p -e "
CREATE USER IF NOT EXISTS 'socks5_user'@'localhost' IDENTIFIED BY 'socks5_password';
GRANT ALL PRIVILEGES ON socks5_db.* TO 'socks5_user'@'localhost';
FLUSH PRIVILEGES;
"

# 3. 检查MySQL版本（建议8.0+）
mysql --version
```

### 步骤2：数据库初始化

```bash
# 1. 创建数据库和表结构（包含优化索引）
mysql -u root -p < scripts/init.sql

# 2. 验证数据库创建
mysql -u socks5_user -p -e "USE socks5_db; SHOW TABLES;"

# 3. 验证索引创建
mysql -u socks5_user -p socks5_db -e "
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'socks5_db' 
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
"
```

### 步骤3：性能验证

```bash
# 1. 执行性能测试
mysql -u socks5_user -p socks5_db < scripts/test_index_performance.sql

# 2. 检查测试结果
# 重点关注EXPLAIN输出中的索引使用情况
# 应该看到"Using index"或"Using index condition"
```

### 步骤4：配置自动化维护

```bash
# 1. 配置数据库连接信息
vim scripts/maintenance_automation.sh

# 修改以下配置变量：
# DB_NAME="socks5_db"
# DB_USER="socks5_user"
# DB_PASS="socks5_password"
# DB_HOST="127.0.0.1"
# DB_PORT="3306"

# 2. 添加定时任务
crontab -e

# 添加以下定时任务：
# 每周日凌晨2点执行数据清理
0 2 * * 0 /path/to/socks5-app/scripts/maintenance_automation.sh cleanup

# 每天凌晨3点执行性能监控
0 3 * * * /path/to/socks5-app/scripts/maintenance_automation.sh monitor

# 每月1日凌晨4点执行表分析
0 4 1 * * /path/to/socks5-app/scripts/maintenance_automation.sh analyze

# 每周日凌晨1点执行数据库备份
0 1 * * 0 /path/to/socks5-app/scripts/maintenance_automation.sh backup
```

## 📊 索引优化效果验证

### 验证方法1：EXPLAIN分析

```sql
-- 测试用户流量统计查询
EXPLAIN SELECT 
    user_id,
    DATE(timestamp) as date,
    SUM(bytes_sent) as total_sent,
    SUM(bytes_recv) as total_recv
FROM traffic_logs 
WHERE user_id = 1 
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- 期望结果：应该使用 idx_user_timestamp 索引
-- 不应该看到 "Using filesort" 或 "Using temporary"
```

### 验证方法2：性能对比测试

```bash
# 1. 测试有索引的查询
time mysql -u socks5_user -p socks5_db -e "
SELECT COUNT(*) FROM traffic_logs 
WHERE user_id = 1 AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY);
"

# 2. 测试无索引的查询（强制不使用索引）
time mysql -u socks5_user -p socks5_db -e "
SELECT COUNT(*) FROM traffic_logs IGNORE INDEX (idx_user_timestamp)
WHERE user_id = 1 AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY);
"

# 对比两个查询的执行时间
```

### 验证方法3：索引使用统计

```sql
-- 查看索引使用情况
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    CARDINALITY,
    SUB_PART,
    PACKED,
    NULLABLE,
    INDEX_TYPE
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'socks5_db'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
```

## 🔍 性能监控和告警

### 关键性能指标

| 指标 | 正常值 | 告警阈值 | 监控频率 |
|------|--------|----------|----------|
| 连接数 | < 80% | > 80% | 实时 |
| 缓冲池命中率 | > 95% | < 95% | 每小时 |
| 慢查询数量 | < 10/小时 | > 10/小时 | 每小时 |
| 表锁等待时间 | < 1秒 | > 1秒 | 实时 |
| 磁盘空间使用率 | < 80% | > 80% | 每天 |

### 监控脚本使用

```bash
# 1. 手动执行性能监控
./scripts/maintenance_automation.sh monitor

# 2. 查看监控日志
tail -f /var/log/mysql/maintenance/maintenance_*.log

# 3. 设置告警（示例）
# 在监控脚本中添加告警逻辑
if [ "$connection_ratio" -gt 80 ]; then
    echo "警告: 数据库连接数过高: $connection_ratio%" | mail -s "数据库告警" admin@example.com
fi
```

## 🛠️ 维护和故障排除

### 常见问题解决

#### 问题1：索引未生效

**症状**: EXPLAIN显示未使用索引  
**解决方案**:
```sql
-- 1. 更新表统计信息
ANALYZE TABLE traffic_logs;
ANALYZE TABLE access_logs;

-- 2. 检查索引是否存在
SHOW INDEX FROM traffic_logs;

-- 3. 强制使用索引
SELECT * FROM traffic_logs FORCE INDEX (idx_user_timestamp) WHERE user_id = 1;
```

#### 问题2：查询性能下降

**症状**: 查询响应时间变长  
**解决方案**:
```sql
-- 1. 检查慢查询日志
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 2. 分析慢查询
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- 3. 优化查询语句
-- 使用EXPLAIN分析执行计划
-- 检查WHERE条件是否匹配索引
```

#### 问题3：磁盘空间不足

**症状**: 数据库写入失败，磁盘空间不足  
**解决方案**:
```bash
# 1. 执行数据清理
./scripts/maintenance_automation.sh cleanup

# 2. 手动清理大表
mysql -u socks5_user -p socks5_db -e "
DELETE FROM traffic_logs WHERE timestamp < DATE_SUB(NOW(), INTERVAL 6 MONTH);
DELETE FROM access_logs WHERE timestamp < DATE_SUB(NOW(), INTERVAL 6 MONTH);
"

# 3. 优化表结构
mysql -u socks5_user -p socks5_db -e "
OPTIMIZE TABLE traffic_logs;
OPTIMIZE TABLE access_logs;
"
```

### 定期维护任务

```bash
# 1. 每周维护
./scripts/maintenance_automation.sh cleanup    # 数据清理
./scripts/maintenance_automation.sh backup     # 数据备份

# 2. 每月维护
./scripts/maintenance_automation.sh optimize   # 表优化
./scripts/maintenance_automation.sh analyze    # 表分析

# 3. 每季度维护
# 检查索引使用效率
# 分析慢查询日志
# 评估是否需要调整索引策略
```

## 📈 性能优化建议

### 应用层优化

1. **查询优化**:
   - 避免使用 `SELECT *`
   - 合理使用 `LIMIT`
   - 避免在 `WHERE` 子句中使用函数

2. **连接池配置**:
   - 设置合适的连接池大小
   - 配置连接超时时间
   - 监控连接池状态

3. **缓存策略**:
   - 使用Redis缓存热点数据
   - 实现查询结果缓存
   - 配置适当的缓存过期时间

### 数据库层优化

1. **配置优化**:
   ```ini
   # my.cnf 配置建议
   [mysqld]
   innodb_buffer_pool_size = 70% of RAM
   innodb_log_file_size = 256M
   innodb_log_files_in_group = 2
   max_connections = 1000
   slow_query_log = 1
   long_query_time = 2
   ```

2. **分区策略**:
   ```sql
   -- 对于大表，考虑按月分区
   ALTER TABLE traffic_logs PARTITION BY RANGE (YEAR(timestamp) * 100 + MONTH(timestamp)) (
       PARTITION p202401 VALUES LESS THAN (202402),
       PARTITION p202402 VALUES LESS THAN (202403),
       -- ... 更多分区
   );
   ```

## 🔐 安全注意事项

### 数据库安全

1. **用户权限管理**:
   - 使用最小权限原则
   - 定期审查用户权限
   - 避免使用root用户

2. **连接安全**:
   - 限制数据库访问IP
   - 使用SSL连接
   - 定期更换密码

3. **数据备份**:
   - 定期备份数据库
   - 测试备份恢复流程
   - 异地备份重要数据

### 脚本安全

1. **文件权限**:
   ```bash
   chmod 600 scripts/maintenance_automation.sh
   chown mysql:mysql scripts/maintenance_automation.sh
   ```

2. **密码安全**:
   - 不要在脚本中硬编码密码
   - 使用环境变量或配置文件
   - 定期更换数据库密码

## 📞 技术支持

### 获取帮助

1. **文档资源**:
   - MySQL官方文档
   - 项目README文档
   - 索引优化说明文档

2. **问题排查**:
   - 检查MySQL错误日志
   - 使用EXPLAIN分析查询
   - 监控慢查询日志

3. **联系支持**:
   - 项目维护团队
   - 数据库管理员
   - 技术社区

---

*本部署指南提供了完整的数据库优化部署流程，请根据实际环境和需求调整相关配置。如有疑问，请参考相关文档或联系技术支持团队。*
