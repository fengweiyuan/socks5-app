-- 数据清理脚本
-- 用于定期清理历史数据，维护数据库性能
-- 建议通过定时任务执行，如crontab

USE socks5_db;

-- ============================================================================
-- 1. 流量日志表清理 (traffic_logs)
-- ============================================================================

-- 删除3个月前的流量日志数据
-- 注意：根据实际业务需求调整保留时间
DELETE FROM traffic_logs 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- 删除6个月前的流量日志数据（更激进的清理策略）
-- DELETE FROM traffic_logs 
-- WHERE timestamp < DATE_SUB(NOW(), INTERVAL 6 MONTH);

-- 显示清理后的数据统计
SELECT 
    'traffic_logs' as table_name,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_record,
    MAX(timestamp) as latest_record
FROM traffic_logs;

-- ============================================================================
-- 2. 访问日志表清理 (access_logs)
-- ============================================================================

-- 删除3个月前的访问日志数据
DELETE FROM access_logs 
WHERE timestamp < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- 删除6个月前的访问日志数据（更激进的清理策略）
-- DELETE FROM access_logs 
-- WHERE timestamp < DATE_SUB(NOW(), INTERVAL 6 MONTH);

-- 显示清理后的数据统计
SELECT 
    'access_logs' as table_name,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_record,
    MAX(timestamp) as latest_record
FROM access_logs;

-- ============================================================================
-- 3. 代理会话表清理 (proxy_sessions)
-- ============================================================================

-- 删除已关闭且超过1个月的会话记录
DELETE FROM proxy_sessions 
WHERE status IN ('closed', 'disconnected') 
  AND updated_at < DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- 删除超过3个月的会话记录（无论状态）
-- DELETE FROM proxy_sessions 
-- WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- 显示清理后的数据统计
SELECT 
    'proxy_sessions' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
    COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_sessions,
    COUNT(CASE WHEN status = 'disconnected' THEN 1 END) as disconnected_sessions
FROM proxy_sessions;

-- ============================================================================
-- 4. 代理心跳表清理 (proxy_heartbeats)
-- ============================================================================

-- 删除超过1个月的心跳记录（保留最近的心跳状态）
-- 注意：这个表通常不需要大量清理，因为心跳记录相对较少
-- 但可以删除过期的历史记录

-- 保留每个代理的最新心跳记录，删除其他历史记录
DELETE ph1 FROM proxy_heartbeats ph1
INNER JOIN proxy_heartbeats ph2 
WHERE ph1.proxy_id = ph2.proxy_id 
  AND ph1.id < ph2.id 
  AND ph1.last_heartbeat < DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- 显示清理后的数据统计
SELECT 
    'proxy_heartbeats' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT proxy_id) as unique_proxies
FROM proxy_heartbeats;

-- ============================================================================
-- 5. 数据归档策略（可选）
-- ============================================================================

-- 在删除数据之前，可以考虑将数据归档到历史表
-- 创建归档表（如果不存在）
CREATE TABLE IF NOT EXISTS traffic_logs_archive LIKE traffic_logs;
CREATE TABLE IF NOT EXISTS access_logs_archive LIKE access_logs;
CREATE TABLE IF NOT EXISTS proxy_sessions_archive LIKE proxy_sessions;

-- 归档3个月前的数据（在删除之前执行）
-- INSERT INTO traffic_logs_archive 
-- SELECT * FROM traffic_logs 
-- WHERE timestamp < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- INSERT INTO access_logs_archive 
-- SELECT * FROM access_logs 
-- WHERE timestamp < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- INSERT INTO proxy_sessions_archive 
-- SELECT * FROM proxy_sessions 
-- WHERE created_at < DATE_SUB(NOW(), INTERVAL 3 MONTH);

-- ============================================================================
-- 6. 表优化和维护
-- ============================================================================

-- 分析表以更新统计信息
ANALYZE TABLE traffic_logs;
ANALYZE TABLE access_logs;
ANALYZE TABLE proxy_sessions;
ANALYZE TABLE proxy_heartbeats;

-- 优化表以回收空间（可选，在低峰期执行）
-- OPTIMIZE TABLE traffic_logs;
-- OPTIMIZE TABLE access_logs;
-- OPTIMIZE TABLE proxy_sessions;

-- ============================================================================
-- 7. 清理后的整体统计
-- ============================================================================

-- 显示所有表的数据统计
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    ROUND(DATA_LENGTH/1024/1024, 2) as data_size_mb,
    ROUND(INDEX_LENGTH/1024/1024, 2) as index_size_mb,
    ROUND((DATA_LENGTH + INDEX_LENGTH)/1024/1024, 2) as total_size_mb
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'socks5_db'
ORDER BY TABLE_ROWS DESC;

-- ============================================================================
-- 8. 清理建议和注意事项
-- ============================================================================

-- 建议1：清理频率
-- - 流量日志和访问日志：建议每周清理一次
-- - 代理会话：建议每月清理一次
-- - 代理心跳：建议每季度清理一次

-- 建议2：清理时间
-- - 选择业务低峰期执行清理
-- - 避免在高峰期进行大量数据删除操作

-- 建议3：备份策略
-- - 清理前建议先备份数据库
-- - 考虑数据归档而不是直接删除

-- 建议4：监控清理效果
-- - 记录清理前后的数据量变化
-- - 监控清理操作的执行时间
-- - 观察清理后的查询性能改善

-- 建议5：自动化脚本
-- - 将清理脚本添加到crontab定时任务
-- - 设置清理日志记录
-- - 配置清理失败告警

-- 建议6：业务规则调整
-- - 根据实际业务需求调整数据保留时间
-- - 考虑法律法规要求的数据保留期限
-- - 平衡存储成本和查询性能需求

-- ============================================================================
-- 9. 示例crontab配置
-- ============================================================================

-- 每周日凌晨2点执行数据清理
-- 0 2 * * 0 /usr/bin/mysql -u username -ppassword socks5_db < /path/to/cleanup_old_data.sql

-- 每月1日凌晨3点执行表优化
-- 0 3 1 * * /usr/bin/mysql -u username -ppassword socks5_db -e "OPTIMIZE TABLE traffic_logs, access_logs, proxy_sessions;"

-- 显示清理完成信息
SELECT '数据清理完成！请检查上述统计信息，确认清理效果。' as message;
