-- 数据库性能监控脚本
-- 用于监控查询性能、索引使用情况和系统状态
-- 建议定期执行，监控数据库健康状况

USE socks5_db;

-- ============================================================================
-- 1. 慢查询分析
-- ============================================================================

-- 检查慢查询日志是否开启
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
SHOW VARIABLES LIKE 'slow_query_log_file';

-- 显示当前慢查询统计（如果开启了慢查询日志）
-- SELECT 
--     start_time,
--     user_host,
--     query_time,
--     lock_time,
--     rows_sent,
--     rows_examined,
--     sql_text
-- FROM mysql.slow_log 
-- WHERE start_time >= DATE_SUB(NOW(), INTERVAL 1 DAY)
-- ORDER BY query_time DESC
-- LIMIT 10;

-- ============================================================================
-- 2. 索引使用情况分析
-- ============================================================================

-- 显示所有表的索引信息
SELECT 
    t.TABLE_NAME,
    t.TABLE_ROWS,
    s.INDEX_NAME,
    s.COLUMN_NAME,
    s.SEQ_IN_INDEX,
    s.CARDINALITY,
    s.NULLABLE,
    s.INDEX_TYPE
FROM information_schema.TABLES t
JOIN information_schema.STATISTICS s ON t.TABLE_SCHEMA = s.TABLE_SCHEMA AND t.TABLE_NAME = s.TABLE_NAME
WHERE t.TABLE_SCHEMA = 'socks5_db'
ORDER BY t.TABLE_NAME, s.INDEX_NAME, s.SEQ_IN_INDEX;

-- 显示未使用的索引（需要结合慢查询日志分析）
-- 这里提供一个索引使用统计的框架
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    '需要分析实际使用情况' as usage_status
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'socks5_db'
GROUP BY TABLE_NAME, INDEX_NAME
ORDER BY TABLE_NAME, INDEX_NAME;

-- ============================================================================
-- 3. 表大小和行数统计
-- ============================================================================

-- 显示所有表的大小统计
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    ROUND(DATA_LENGTH/1024/1024, 2) as data_size_mb,
    ROUND(INDEX_LENGTH/1024/1024, 2) as index_size_mb,
    ROUND((DATA_LENGTH + INDEX_LENGTH)/1024/1024, 2) as total_size_mb,
    ROUND(INDEX_LENGTH/NULLIF(DATA_LENGTH, 0) * 100, 2) as index_ratio_percent
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'socks5_db'
ORDER BY TABLE_ROWS DESC;

-- 显示大表的详细信息
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    ROUND(DATA_LENGTH/1024/1024, 2) as data_size_mb,
    ROUND(INDEX_LENGTH/1024/1024, 2) as index_size_mb
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'socks5_db' 
  AND TABLE_ROWS > 10000
ORDER BY TABLE_ROWS DESC;

-- ============================================================================
-- 4. 查询性能测试
-- ============================================================================

-- 测试1：用户流量统计查询性能
SET profiling = 1;

-- 执行查询
SELECT 
    user_id,
    DATE(timestamp) as date,
    SUM(bytes_sent) as total_sent,
    SUM(bytes_recv) as total_recv
FROM traffic_logs 
WHERE user_id = 1 
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- 显示查询性能分析
SHOW PROFILES;
SHOW PROFILE FOR QUERY 1;

-- 测试2：时间范围查询性能
SELECT 
    user_id,
    COUNT(*) as request_count
FROM traffic_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY user_id
ORDER BY request_count DESC;

-- 显示查询性能分析
SHOW PROFILES;
SHOW PROFILE FOR QUERY 2;

-- 关闭性能分析
SET profiling = 0;

-- ============================================================================
-- 5. 连接和进程状态
-- ============================================================================

-- 显示当前连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';
SHOW STATUS LIKE 'Connections';

-- 显示当前进程列表
SHOW PROCESSLIST;

-- 显示连接相关配置
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE 'wait_timeout';
SHOW VARIABLES LIKE 'interactive_timeout';

-- ============================================================================
-- 6. 缓存和缓冲池状态
-- ============================================================================

-- 显示查询缓存状态（MySQL 5.7及以下版本）
-- SHOW STATUS LIKE 'Qcache%';

-- 显示InnoDB缓冲池状态
SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests';
SHOW STATUS LIKE 'Innodb_buffer_pool_reads';
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_total';
SHOW STATUS LIKE 'Innodb_buffer_pool_pages_free';

-- 计算缓冲池命中率
SELECT 
    ROUND(
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') /
        NULLIF((SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') + 
                (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'), 0) * 100, 2
    ) as buffer_pool_hit_rate;

-- ============================================================================
-- 7. 锁和等待状态
-- ============================================================================

-- 显示当前锁等待情况
SELECT 
    r.trx_id waiting_trx_id,
    r.trx_mysql_thread_id waiting_thread,
    r.trx_query waiting_query,
    b.trx_id blocking_trx_id,
    b.trx_mysql_thread_id blocking_thread,
    b.trx_query blocking_query
FROM information_schema.innodb_lock_waits w
INNER JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
INNER JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;

-- 显示表锁状态
SHOW STATUS LIKE 'Table_locks_waited';
SHOW STATUS LIKE 'Table_locks_immediate';

-- ============================================================================
-- 8. 系统资源使用情况
-- ============================================================================

-- 显示系统变量配置
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';
SHOW VARIABLES LIKE 'innodb_log_file_size';
SHOW VARIABLES LIKE 'innodb_flush_log_at_trx_commit';
SHOW VARIABLES LIKE 'sync_binlog';

-- 显示InnoDB状态摘要
SHOW ENGINE INNODB STATUS\G

-- ============================================================================
-- 9. 性能优化建议
-- ============================================================================

-- 基于当前状态生成优化建议
SELECT 
    '性能监控完成！' as status,
    '请根据上述指标分析数据库性能状况。' as message;

-- 建议1：索引优化
-- - 检查是否有未使用的索引
-- - 确保复合索引的顺序正确
-- - 考虑添加缺失的索引

-- 建议2：查询优化
-- - 分析慢查询日志
-- - 优化SELECT语句
-- - 避免SELECT *
-- - 使用LIMIT限制结果集

-- 建议3：配置优化
-- - 调整innodb_buffer_pool_size
-- - 优化innodb_log_file_size
-- - 调整max_connections

-- 建议4：维护优化
-- - 定期执行ANALYZE TABLE
-- - 定期执行OPTIMIZE TABLE
-- - 定期清理历史数据

-- 建议5：监控告警
-- - 设置连接数告警
-- - 设置慢查询告警
-- - 设置磁盘空间告警

-- ============================================================================
-- 10. 自动化监控脚本示例
-- ============================================================================

-- 创建性能监控视图
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    '连接数' as metric,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected') as current_value,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_variables WHERE VARIABLE_NAME = 'max_connections') as max_value
UNION ALL
SELECT 
    '缓冲池命中率' as metric,
    ROUND(
        (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') /
        NULLIF((SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') + 
                (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'), 0) * 100, 2
    ) as current_value,
    95 as max_value
UNION ALL
SELECT 
    '表锁等待' as metric,
    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Table_locks_waited') as current_value,
    0 as max_value;

-- 显示性能摘要
SELECT * FROM performance_summary;

-- 显示监控完成信息
SELECT '数据库性能监控完成！请根据上述指标分析系统健康状况。' as message;
