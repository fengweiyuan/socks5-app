-- 插入示例流量数据
-- 使用数据库
USE socks5_db;

-- 插入示例流量日志数据
INSERT INTO traffic_logs (user_id, client_ip, target_ip, target_port, bytes_sent, bytes_recv, protocol, timestamp) VALUES
(1, '192.168.1.100', '8.8.8.8', 80, 1024, 2048, 'tcp', NOW() - INTERVAL 1 HOUR),
(1, '192.168.1.100', '1.1.1.1', 443, 512, 1024, 'tcp', NOW() - INTERVAL 30 MINUTE),
(1, '192.168.1.100', '208.67.222.222', 53, 256, 512, 'udp', NOW() - INTERVAL 15 MINUTE),
(1, '192.168.1.100', '8.8.4.4', 53, 128, 256, 'udp', NOW() - INTERVAL 10 MINUTE),
(1, '192.168.1.100', '142.250.185.78', 443, 2048, 4096, 'tcp', NOW() - INTERVAL 5 MINUTE);

-- 插入示例代理会话数据
INSERT INTO proxy_sessions (user_id, client_ip, start_time, bytes_sent, bytes_recv, status) VALUES
(1, '192.168.1.100', NOW() - INTERVAL 2 HOUR, 4096, 8192, 'active'),
(1, '192.168.1.101', NOW() - INTERVAL 1 HOUR, 2048, 4096, 'active');

-- 更新用户表，确保有用户数据
UPDATE users SET bandwidth_limit = 1048576 WHERE username = 'admin';

-- 显示插入的数据
SELECT '流量日志数据:' as info;
SELECT * FROM traffic_logs ORDER BY timestamp DESC LIMIT 5;

SELECT '代理会话数据:' as info;
SELECT * FROM proxy_sessions WHERE status = 'active';

SELECT '流量统计:' as info;
SELECT 
    SUM(bytes_sent) as total_bytes_sent,
    SUM(bytes_recv) as total_bytes_recv,
    COUNT(*) as total_logs
FROM traffic_logs;
