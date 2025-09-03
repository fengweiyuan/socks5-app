# 数据库优化脚本说明

本目录包含了针对SOCKS5代理服务器项目的数据库优化脚本，主要用于提升流水表的查询性能和维护数据库健康状态。

## 📁 脚本文件说明

### 1. `optimize_indexes.sql` - 索引优化脚本
**用途**: 为流水表创建合适的复合索引，提升查询性能  
**适用场景**: 数据库初始化后、表结构变更后、性能优化时  
**执行频率**: 一次性执行，或表结构变更后执行  

**主要优化内容**:
- 流量日志表 (`traffic_logs`) 的复合索引
- 访问日志表 (`access_logs`) 的复合索引  
- 代理会话表 (`proxy_sessions`) 的复合索引
- 代理心跳表 (`proxy_heartbeats`) 的复合索引

**索引设计原则**:
- 优先考虑查询频率最高的字段组合
- 时间字段通常放在索引的后面（用于范围查询）
- 避免创建过多索引（影响写入性能）

### 2. `cleanup_old_data.sql` - 数据清理脚本
**用途**: 定期清理历史数据，维护数据库性能  
**适用场景**: 定期维护、磁盘空间不足、性能下降时  
**执行频率**: 建议每周执行一次  

**清理策略**:
- 流量日志: 保留3-6个月数据
- 访问日志: 保留3-6个月数据
- 代理会话: 保留1-3个月数据
- 代理心跳: 保留1个月数据

**注意事项**:
- 清理前建议先备份数据库
- 选择业务低峰期执行
- 根据实际业务需求调整保留时间

### 3. `monitor_performance.sql` - 性能监控脚本
**用途**: 监控数据库性能指标，分析系统健康状况  
**适用场景**: 定期监控、性能问题排查、容量规划时  
**执行频率**: 建议每天执行一次  

**监控指标**:
- 慢查询分析
- 索引使用情况
- 表大小和行数统计
- 连接和进程状态
- 缓存和缓冲池状态
- 锁和等待状态

## 🚀 使用方法

### 方法1: 命令行执行
```bash
# 索引优化
mysql -u username -ppassword socks5_db < optimize_indexes.sql

# 数据清理
mysql -u username -ppassword socks5_db < cleanup_old_data.sql

# 性能监控
mysql -u username -ppassword socks5_db < monitor_performance.sql
```

### 方法2: MySQL客户端执行
```sql
-- 在MySQL客户端中执行
source /path/to/optimize_indexes.sql;
source /path/to/cleanup_old_data.sql;
source /path/to/monitor_performance.sql;
```

### 方法3: 定时任务执行
```bash
# 编辑crontab
crontab -e

# 添加定时任务
# 每周日凌晨2点执行数据清理
0 2 * * 0 /usr/bin/mysql -u username -ppassword socks5_db < /path/to/cleanup_old_data.sql

# 每天凌晨3点执行性能监控
0 3 * * * /usr/bin/mysql -u username -ppassword socks5_db < /path/to/monitor_performance.sql

# 每月1日凌晨4点执行表优化
0 4 1 * * /usr/bin/mysql -u username -ppassword socks5_db -e "OPTIMIZE TABLE traffic_logs, access_logs, proxy_sessions;"
```

## 📊 流水表索引设计详解

### 流量日志表 (`traffic_logs`)
**数据特点**: 高频写入、大量数据、时间序列  
**主要查询模式**:
1. 按用户查询特定时间段流量
2. 按时间范围查询所有用户流量
3. 按目标地址分析访问情况
4. 按客户端IP分析行为模式

**索引设计**:
```sql
-- 用户ID + 时间戳（最常用查询）
CREATE INDEX idx_user_timestamp ON traffic_logs (user_id, timestamp DESC);

-- 时间戳 + 用户ID（时间范围查询）
CREATE INDEX idx_timestamp_user ON traffic_logs (timestamp DESC, user_id);

-- 目标分析（IP + 端口 + 协议）
CREATE INDEX idx_target_analysis ON traffic_logs (target_ip, target_port, protocol);

-- 客户端行为分析
CREATE INDEX idx_client_timestamp ON traffic_logs (client_ip, timestamp DESC);
```

### 访问日志表 (`access_logs`)
**数据特点**: 高频写入、大量数据、URL模式查询  
**主要查询模式**:
1. 按用户查询访问记录
2. 按时间范围查询状态统计
3. 按客户端IP分析行为
4. 按URL模式进行过滤

**索引设计**:
```sql
-- 用户ID + 时间戳
CREATE INDEX idx_user_timestamp ON access_logs (user_id, timestamp DESC);

-- 时间戳 + 状态
CREATE INDEX idx_timestamp_status ON access_logs (timestamp DESC, status);

-- 客户端IP + 时间戳
CREATE INDEX idx_client_timestamp ON access_logs (client_ip, timestamp DESC);

-- URL前缀 + 时间戳（限制长度避免索引过大）
CREATE INDEX idx_target_url_prefix ON access_logs (target_url(100), timestamp DESC);
```

## 🔧 性能优化最佳实践

### 1. 索引优化原则
- **选择性**: 选择区分度高的字段作为索引前缀
- **顺序性**: 复合索引中，等值查询字段放在前面，范围查询字段放在后面
- **覆盖性**: 尽量让索引覆盖查询需求，避免回表查询
- **维护性**: 避免创建过多索引，影响写入性能

### 2. 查询优化建议
- 使用 `EXPLAIN` 分析查询执行计划
- 避免使用 `SELECT *`，只查询需要的字段
- 合理使用 `LIMIT` 限制结果集大小
- 避免在 `WHERE` 子句中使用函数
- 使用 `INNER JOIN` 替代 `WHERE` 子查询

### 3. 数据维护策略
- 定期执行 `ANALYZE TABLE` 更新统计信息
- 定期执行 `OPTIMIZE TABLE` 回收空间
- 设置合理的数据保留期限
- 考虑数据归档策略
- 监控表大小增长趋势

### 4. 系统配置优化
- 调整 `innodb_buffer_pool_size` 为物理内存的70-80%
- 优化 `innodb_log_file_size` 和 `innodb_log_files_in_group`
- 设置合适的 `max_connections` 值
- 配置慢查询日志和监控告警

## 📈 性能监控指标

### 关键性能指标
1. **查询响应时间**: 平均查询时间、慢查询数量
2. **索引效率**: 索引命中率、索引使用情况
3. **连接状态**: 当前连接数、最大连接数、连接等待时间
4. **缓冲池性能**: 缓冲池命中率、读写比例
5. **锁等待**: 表锁等待、行锁等待情况

### 监控告警阈值
- 连接数 > 80% 最大连接数
- 缓冲池命中率 < 95%
- 慢查询数量 > 10个/小时
- 表锁等待时间 > 1秒
- 磁盘空间使用率 > 80%

## 🚨 注意事项

### 安全注意事项
1. 执行脚本前务必备份数据库
2. 使用专用数据库用户，避免使用root用户
3. 限制数据库用户权限，只授予必要权限
4. 定期检查数据库访问日志

### 性能注意事项
1. 避免在业务高峰期执行大量数据操作
2. 监控索引创建和删除对系统性能的影响
3. 注意数据清理操作的事务大小
4. 定期检查索引的维护成本

### 业务注意事项
1. 根据业务需求调整数据保留期限
2. 考虑法律法规要求的数据保留要求
3. 平衡存储成本和查询性能需求
4. 与业务团队协调数据清理策略

## 📞 技术支持

如果在使用过程中遇到问题，请：
1. 检查MySQL错误日志
2. 使用 `EXPLAIN` 分析查询执行计划
3. 参考MySQL官方文档
4. 联系数据库管理员或开发团队

---

*本文档提供了数据库优化的完整指南，请根据实际环境和需求调整相关参数和策略。*
