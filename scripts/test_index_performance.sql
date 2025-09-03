-- 索引性能测试脚本
-- 用于验证优化后的索引效果和查询性能
-- 建议在测试环境执行，避免影响生产数据

USE socks5_db;

-- ============================================================================
-- 1. 准备测试数据
-- ============================================================================

-- 清空现有测试数据（谨慎操作）
-- DELETE FROM traffic_logs;
-- DELETE FROM access_logs;
-- DELETE FROM proxy_sessions;
-- DELETE FROM proxy_heartbeats;

-- 插入测试数据（如果表为空）
-- 注意：这里只插入少量测试数据，实际项目中会有大量真实数据

-- 插入测试流量日志数据
INSERT IGNORE INTO traffic_logs (user_id, client_ip, target_ip, target_port, bytes_sent, bytes_recv, protocol, timestamp) VALUES
(1, '192.168.1.100', '8.8.8.8', 80, 1024, 2048, 'tcp', NOW() - INTERVAL 1 HOUR),
(1, '192.168.1.100', '1.1.1.1', 443, 512, 1024, 'tcp', NOW() - INTERVAL 30 MINUTE),
(1, '192.168.1.100', '208.67.222.222', 53, 256, 512, 'udp', NOW() - INTERVAL 15 MINUTE),
(1, '192.168.1.100', '8.8.4.4', 53, 128, 256, 'udp', NOW() - INTERVAL 10 MINUTE),
(1, '192.168.1.100', '142.250.185.78', 443, 2048, 4096, 'tcp', NOW() - INTERVAL 5 MINUTE),
(2, '192.168.1.101', '8.8.8.8', 80, 2048, 4096, 'tcp', NOW() - INTERVAL 2 HOUR),
(2, '192.168.1.101', '1.1.1.1', 443, 1024, 2048, 'tcp', NOW() - INTERVAL 1 HOUR),
(2, '192.168.1.101', '208.67.222.222', 53, 512, 1024, 'udp', NOW() - INTERVAL 30 MINUTE);

-- 插入测试访问日志数据
INSERT IGNORE INTO access_logs (user_id, client_ip, target_url, method, status, timestamp) VALUES
(1, '192.168.1.100', 'https://www.google.com', 'GET', '200', NOW() - INTERVAL 1 HOUR),
(1, '192.168.1.100', 'https://www.facebook.com', 'POST', '403', NOW() - INTERVAL 30 MINUTE),
(1, '192.168.1.100', 'https://www.github.com', 'GET', '200', NOW() - INTERVAL 15 MINUTE),
(2, '192.168.1.101', 'https://www.stackoverflow.com', 'GET', '200', NOW() - INTERVAL 2 HOUR),
(2, '192.168.1.101', 'https://www.reddit.com', 'GET', '200', NOW() - INTERVAL 1 HOUR);

-- 插入测试代理会话数据
INSERT IGNORE INTO proxy_sessions (user_id, client_ip, start_time, bytes_sent, bytes_recv, status) VALUES
(1, '192.168.1.100', NOW() - INTERVAL 2 HOUR, 4096, 8192, 'active'),
(1, '192.168.1.100', NOW() - INTERVAL 1 DAY, 2048, 4096, 'closed'),
(2, '192.168.1.101', NOW() - INTERVAL 1 HOUR, 2048, 4096, 'active'),
(2, '192.168.1.101', NOW() - INTERVAL 2 DAY, 1024, 2048, 'disconnected');

-- 插入测试代理心跳数据
INSERT IGNORE INTO proxy_heartbeats (proxy_id, proxy_host, proxy_port, status, active_conns, total_conns, last_heartbeat) VALUES
('test-proxy-1', '0.0.0.0', '1082', 'online', 5, 100, NOW() - INTERVAL 5 SECOND),
('test-proxy-2', '0.0.0.0', '1083', 'online', 3, 50, NOW() - INTERVAL 10 SECOND),
('test-proxy-3', '0.0.0.0', '1084', 'offline', 0, 25, NOW() - INTERVAL 1 MINUTE);

-- ============================================================================
-- 2. 索引使用情况验证
-- ============================================================================

-- 显示所有表的索引信息
SELECT 
    '索引信息概览' as info,
    '' as detail;

SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX,
    CARDINALITY
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'socks5_db' 
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- ============================================================================
-- 3. 查询性能测试
-- ============================================================================

-- 启用查询性能分析
SET profiling = 1;

-- 测试1：用户流量统计查询（应该使用 idx_user_timestamp）
SELECT '测试1：用户流量统计查询' as test_name;
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

-- 执行查询并记录性能
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

-- 测试2：时间范围查询（应该使用 idx_timestamp_user）
SELECT '测试2：时间范围查询' as test_name;
EXPLAIN SELECT 
    user_id,
    COUNT(*) as request_count
FROM traffic_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY user_id
ORDER BY request_count DESC;

-- 执行查询并记录性能
SELECT 
    user_id,
    COUNT(*) as request_count
FROM traffic_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
GROUP BY user_id
ORDER BY request_count DESC;

-- 测试3：目标分析查询（应该使用 idx_target_analysis）
SELECT '测试3：目标分析查询' as test_name;
EXPLAIN SELECT 
    target_ip,
    target_port,
    protocol,
    COUNT(*) as access_count
FROM traffic_logs 
WHERE target_ip = '8.8.8.8'
GROUP BY target_ip, target_port, protocol;

-- 执行查询并记录性能
SELECT 
    target_ip,
    target_port,
    protocol,
    COUNT(*) as access_count
FROM traffic_logs 
WHERE target_ip = '8.8.8.8'
GROUP BY target_ip, target_port, protocol;

-- 测试4：客户端行为分析（应该使用 idx_client_timestamp）
SELECT '测试4：客户端行为分析' as test_name;
EXPLAIN SELECT 
    client_ip,
    COUNT(*) as access_count,
    MAX(timestamp) as last_access
FROM traffic_logs 
WHERE client_ip = '192.168.1.100'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY client_ip;

-- 执行查询并记录性能
SELECT 
    client_ip,
    COUNT(*) as access_count,
    MAX(timestamp) as last_access
FROM traffic_logs 
WHERE client_ip = '192.168.1.100'
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY client_ip;

-- 测试5：访问日志状态查询（应该使用 idx_timestamp_status）
SELECT '测试5：访问日志状态查询' as test_name;
EXPLAIN SELECT 
    status,
    COUNT(*) as count
FROM access_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
GROUP BY status;

-- 执行查询并记录性能
SELECT 
    status,
    COUNT(*) as count
FROM access_logs 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
GROUP BY status;

-- 测试6：代理健康状态查询（应该使用 idx_proxy_heartbeat）
SELECT '测试6：代理健康状态查询' as test_name;
EXPLAIN SELECT 
    proxy_id,
    status,
    last_heartbeat
FROM proxy_heartbeats 
WHERE proxy_id = 'test-proxy-1'
ORDER BY last_heartbeat DESC
LIMIT 1;

-- 执行查询并记录性能
SELECT 
    proxy_id,
    status,
    last_heartbeat
FROM proxy_heartbeats 
WHERE proxy_id = 'test-proxy-1'
ORDER BY last_heartbeat DESC
LIMIT 1;

-- 测试7：代理会话状态查询（应该使用 idx_user_status_time）
SELECT '测试7：代理会话状态查询' as test_name;
EXPLAIN SELECT 
    user_id,
    status,
    COUNT(*) as session_count
FROM proxy_sessions 
WHERE user_id = 1 AND status = 'active'
GROUP BY user_id, status;

-- 执行查询并记录性能
SELECT 
    user_id,
    status,
    COUNT(*) as session_count
FROM proxy_sessions 
WHERE user_id = 1 AND status = 'active'
GROUP BY user_id, status;

-- ============================================================================
-- 4. 性能分析结果
-- ============================================================================

-- 显示所有查询的性能分析
SELECT '查询性能分析结果' as info;
SHOW PROFILES;

-- 显示第一个查询的详细性能分析
SELECT '第一个查询的详细性能分析' as info;
SHOW PROFILE FOR QUERY 1;

-- 显示第二个查询的详细性能分析
SELECT '第二个查询的详细性能分析' as info;
SHOW PROFILE FOR QUERY 2;

-- 关闭性能分析
SET profiling = 0;

-- ============================================================================
-- 5. 索引使用效率分析
-- ============================================================================

-- 分析表以更新统计信息
ANALYZE TABLE traffic_logs;
ANALYZE TABLE access_logs;
ANALYZE TABLE proxy_sessions;
ANALYZE TABLE proxy_heartbeats;

-- 显示表的统计信息
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    ROUND(DATA_LENGTH/1024/1024, 2) as data_size_mb,
    ROUND(INDEX_LENGTH/1024/1024, 2) as index_size_mb,
    ROUND(INDEX_LENGTH/NULLIF(DATA_LENGTH, 0) * 100, 2) as index_ratio_percent
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'socks5_db'
ORDER BY TABLE_NAME;

-- ============================================================================
-- 6. 复合索引效果验证
-- ============================================================================

-- 验证复合索引的前缀特性
SELECT '验证复合索引前缀特性' as info;

-- 测试：只使用复合索引的第一个字段
EXPLAIN SELECT * FROM traffic_logs WHERE user_id = 1 LIMIT 5;

-- 测试：使用复合索引的两个字段
EXPLAIN SELECT * FROM traffic_logs WHERE user_id = 1 AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY) LIMIT 5;

-- 测试：使用复合索引的所有字段
EXPLAIN SELECT * FROM traffic_logs WHERE user_id = 1 AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY) ORDER BY timestamp DESC LIMIT 5;

-- ============================================================================
-- 7. 性能对比测试
-- ============================================================================

-- 测试无索引查询的性能（通过强制不使用索引）
SELECT '无索引查询性能测试' as info;

-- 强制不使用索引查询
EXPLAIN SELECT 
    user_id,
    COUNT(*) as request_count
FROM traffic_logs IGNORE INDEX (idx_user_timestamp)
WHERE user_id = 1 
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
GROUP BY user_id;

-- 使用索引查询（对比）
EXPLAIN SELECT 
    user_id,
    COUNT(*) as request_count
FROM traffic_logs 
WHERE user_id = 1 
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
GROUP BY user_id;

-- ============================================================================
-- 8. 测试结果总结
-- ============================================================================

SELECT '索引性能测试完成！' as status;

-- 显示测试结果摘要
SELECT 
    '测试结果摘要' as summary,
    '请检查上述EXPLAIN结果，确保查询使用了正确的索引。' as note,
    '如果看到"Using index"或"Using index condition"，说明索引使用良好。' as tip,
    '如果看到"Using where"且扫描行数很多，可能需要进一步优化。' as warning;

-- 显示索引使用建议
SELECT 
    '索引使用建议' as advice,
    '1. 确保WHERE条件与索引字段匹配' as tip1,
    '2. 利用复合索引的前缀特性' as tip2,
    '3. 注意索引字段的顺序和方向' as tip3,
    '4. 定期使用EXPLAIN分析查询性能' as tip4,
    '5. 监控慢查询日志，持续优化' as tip5;

-- 清理测试数据（可选）
-- 注意：在生产环境中不要执行此操作
-- DELETE FROM traffic_logs WHERE user_id IN (1, 2);
-- DELETE FROM access_logs WHERE user_id IN (1, 2);
-- DELETE FROM proxy_sessions WHERE user_id IN (1, 2);
-- DELETE FROM proxy_heartbeats WHERE proxy_id LIKE 'test-proxy-%';
