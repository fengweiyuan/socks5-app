-- 数据库索引优化脚本
-- 针对会产生大量数据的流水表进行索引优化
-- 使用数据库
USE socks5_db;

-- ============================================================================
-- 1. 流量日志表 (traffic_logs) - 高频写入，大量数据
-- ============================================================================

-- 删除现有索引（如果存在）
DROP INDEX IF EXISTS idx_user_id ON traffic_logs;
DROP INDEX IF EXISTS idx_timestamp ON traffic_logs;
DROP INDEX IF EXISTS idx_target_ip ON traffic_logs;

-- 创建复合索引：用户ID + 时间戳（最常用的查询组合）
-- 支持按用户查询特定时间段的流量
CREATE INDEX idx_user_timestamp ON traffic_logs (user_id, timestamp DESC);

-- 创建复合索引：时间戳 + 用户ID（支持时间范围查询）
-- 支持按时间查询所有用户的流量统计
CREATE INDEX idx_timestamp_user ON traffic_logs (timestamp DESC, user_id);

-- 创建复合索引：目标IP + 端口 + 协议（支持目标分析）
-- 支持分析特定目标的访问情况
CREATE INDEX idx_target_analysis ON traffic_logs (target_ip, target_port, protocol);

-- 创建复合索引：客户端IP + 时间戳（支持客户端行为分析）
-- 支持分析特定客户端的访问模式
CREATE INDEX idx_client_timestamp ON traffic_logs (client_ip, timestamp DESC);

-- 创建时间分区索引（按月分区，提升时间范围查询性能）
-- 注意：MySQL 8.0+ 支持自动分区
-- ALTER TABLE traffic_logs PARTITION BY RANGE (YEAR(timestamp) * 100 + MONTH(timestamp)) (
--     PARTITION p202401 VALUES LESS THAN (202402),
--     PARTITION p202402 VALUES LESS THAN (202403),
--     PARTITION p202403 VALUES LESS THAN (202404),
--     PARTITION p202404 VALUES LESS THAN (202405),
--     PARTITION p202405 VALUES LESS THAN (202406),
--     PARTITION p202406 VALUES LESS THAN (202407),
--     PARTITION p202407 VALUES LESS THAN (202408),
--     PARTITION p202408 VALUES LESS THAN (202409),
--     PARTITION p202409 VALUES LESS THAN (202410),
--     PARTITION p202410 VALUES LESS THAN (202411),
--     PARTITION p202411 VALUES LESS THAN (202412),
--     PARTITION p202412 VALUES LESS THAN (202501),
--     PARTITION p_future VALUES LESS THAN MAXVALUE
-- );

-- ============================================================================
-- 2. 访问日志表 (access_logs) - 高频写入，大量数据
-- ============================================================================

-- 删除现有索引（如果存在）
DROP INDEX IF EXISTS idx_user_id ON access_logs;
DROP INDEX IF EXISTS idx_timestamp ON access_logs;
DROP INDEX IF EXISTS idx_status ON access_logs;

-- 创建复合索引：用户ID + 时间戳（最常用的查询组合）
-- 支持按用户查询特定时间段的访问记录
CREATE INDEX idx_user_timestamp ON access_logs (user_id, timestamp DESC);

-- 创建复合索引：时间戳 + 状态（支持时间范围状态查询）
-- 支持按时间查询特定状态的访问记录
CREATE INDEX idx_timestamp_status ON access_logs (timestamp DESC, status);

-- 创建复合索引：客户端IP + 时间戳（支持客户端行为分析）
-- 支持分析特定客户端的访问模式
CREATE INDEX idx_client_timestamp ON access_logs (client_ip, timestamp DESC);

-- 创建复合索引：状态 + 时间戳（支持状态统计查询）
-- 支持按状态统计不同时间段的访问情况
CREATE INDEX idx_status_timestamp ON access_logs (status, timestamp DESC);

-- 创建URL前缀索引（支持URL模式查询，限制长度避免索引过大）
-- 支持按URL模式进行模糊查询
CREATE INDEX idx_target_url_prefix ON access_logs (target_url(100), timestamp DESC);

-- ============================================================================
-- 3. 代理会话表 (proxy_sessions) - 中等频率写入，中等数据量
-- ============================================================================

-- 删除现有索引（如果存在）
DROP INDEX IF EXISTS idx_user_id ON proxy_sessions;
DROP INDEX IF EXISTS idx_status ON proxy_sessions;
DROP INDEX IF EXISTS idx_start_time ON proxy_sessions;

-- 创建复合索引：用户ID + 状态 + 开始时间
-- 支持查询用户的活跃会话
CREATE INDEX idx_user_status_time ON proxy_sessions (user_id, status, start_time DESC);

-- 创建复合索引：状态 + 开始时间（支持状态统计查询）
-- 支持查询不同状态的会话统计
CREATE INDEX idx_status_start_time ON proxy_sessions (status, start_time DESC);

-- 创建复合索引：客户端IP + 开始时间（支持客户端会话查询）
-- 支持查询特定客户端的会话历史
CREATE INDEX idx_client_start_time ON proxy_sessions (client_ip, start_time DESC);

-- 创建复合索引：开始时间 + 结束时间（支持时间范围查询）
-- 支持查询特定时间段的会话
CREATE INDEX idx_time_range ON proxy_sessions (start_time, end_time);

-- ============================================================================
-- 4. 代理心跳表 (proxy_heartbeats) - 高频写入，中等数据量
-- ============================================================================

-- 删除现有索引（如果存在）
DROP INDEX IF EXISTS idx_proxy_id ON proxy_heartbeats;
DROP INDEX IF EXISTS idx_status ON proxy_heartbeats;
DROP INDEX IF EXISTS idx_last_heartbeat ON proxy_heartbeats;

-- 创建复合索引：代理ID + 最后心跳时间（支持健康状态查询）
-- 支持查询特定代理的最新心跳状态
CREATE INDEX idx_proxy_heartbeat ON proxy_heartbeats (proxy_id, last_heartbeat DESC);

-- 创建复合索引：状态 + 最后心跳时间（支持状态监控查询）
-- 支持查询不同状态的代理服务器
CREATE INDEX idx_status_heartbeat ON proxy_heartbeats (status, last_heartbeat DESC);

-- 创建复合索引：最后心跳时间 + 状态（支持时间范围状态查询）
-- 支持查询特定时间范围内的心跳状态
CREATE INDEX idx_heartbeat_status ON proxy_heartbeats (last_heartbeat DESC, status);

-- ============================================================================
-- 5. 用户表 (users) - 低频写入，少量数据
-- ============================================================================

-- 用户表已有合适的索引，无需额外优化

-- ============================================================================
-- 6. 其他配置表 - 低频写入，少量数据
-- ============================================================================

-- URL过滤、IP白名单、带宽限制等表数据量较小，现有索引足够

-- ============================================================================
-- 7. 创建统计视图（可选，提升复杂查询性能）
-- ============================================================================

-- 创建用户流量统计视图
CREATE OR REPLACE VIEW user_traffic_summary AS
SELECT 
    u.id,
    u.username,
    u.role,
    COUNT(DISTINCT tl.id) as total_requests,
    SUM(tl.bytes_sent) as total_bytes_sent,
    SUM(tl.bytes_recv) as total_bytes_recv,
    COUNT(DISTINCT DATE(tl.timestamp)) as active_days,
    MAX(tl.timestamp) as last_activity
FROM users u
LEFT JOIN traffic_logs tl ON u.id = tl.user_id
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.username, u.role;

-- 创建代理健康状态视图
CREATE OR REPLACE VIEW proxy_health_summary AS
SELECT 
    proxy_id,
    proxy_host,
    proxy_port,
    status,
    active_conns,
    total_conns,
    last_heartbeat,
    CASE 
        WHEN TIMESTAMPDIFF(SECOND, last_heartbeat, NOW()) <= 15 THEN 'healthy'
        WHEN TIMESTAMPDIFF(SECOND, last_heartbeat, NOW()) <= 30 THEN 'warning'
        ELSE 'offline'
    END as health_status
FROM proxy_heartbeats
ORDER BY last_heartbeat DESC;

-- ============================================================================
-- 8. 索引使用情况分析
-- ============================================================================

-- 显示表的索引信息
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX,
    CARDINALITY
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'socks5_db' 
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- 显示表的行数统计
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'socks5_db'
ORDER BY TABLE_ROWS DESC;

-- ============================================================================
-- 9. 性能优化建议
-- ============================================================================

-- 建议1：定期清理历史数据
-- 对于流量日志和访问日志，建议保留3-6个月的数据
-- 可以通过定时任务删除过期数据

-- 建议2：分区表策略
-- 对于traffic_logs和access_logs表，建议按月分区
-- 提升时间范围查询性能，便于数据维护

-- 建议3：读写分离
-- 考虑将历史数据查询分离到只读副本
-- 减轻主库查询压力

-- 建议4：缓存策略
-- 对于频繁查询的统计数据，使用Redis缓存
-- 减少数据库查询压力

-- 建议5：定期分析表
-- 定期执行ANALYZE TABLE更新统计信息
-- 帮助优化器选择最佳执行计划

-- 建议6：监控慢查询
-- 开启慢查询日志，定期分析慢查询
-- 持续优化索引和查询语句

-- ============================================================================
-- 10. 示例查询性能测试
-- ============================================================================

-- 测试1：用户流量统计查询（应该使用idx_user_timestamp）
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

-- 测试2：时间范围查询（应该使用idx_timestamp_user）
EXPLAIN SELECT 
    user_id,
    COUNT(*) as request_count
FROM traffic_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY user_id
ORDER BY request_count DESC;

-- 测试3：代理健康状态查询（应该使用idx_proxy_heartbeat）
EXPLAIN SELECT 
    proxy_id,
    status,
    last_heartbeat
FROM proxy_heartbeats 
WHERE proxy_id = 'test-proxy'
ORDER BY last_heartbeat DESC
LIMIT 1;

-- 测试4：客户端行为分析（应该使用idx_client_timestamp）
EXPLAIN SELECT 
    client_ip,
    COUNT(*) as access_count,
    MAX(timestamp) as last_access
FROM access_logs 
WHERE client_ip = '192.168.1.100'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY client_ip;

-- 显示执行计划结果
SELECT '索引优化完成！请查看上述执行计划，确保使用了正确的索引。' as message;
