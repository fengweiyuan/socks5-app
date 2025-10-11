-- MySQL数据库初始化脚本
-- 创建数据库和用户

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS socks5_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE socks5_db;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role ENUM('admin', 'user') DEFAULT 'user',
    status ENUM('active', 'inactive') DEFAULT 'active',
    bandwidth_limit BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_status (status),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建代理会话表
CREATE TABLE IF NOT EXISTS proxy_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    client_ip VARCHAR(45) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    bytes_sent BIGINT DEFAULT 0,
    bytes_recv BIGINT DEFAULT 0,
    status ENUM('active', 'closed', 'disconnected') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    -- 优化后的复合索引，提升查询性能
    INDEX idx_user_status_time (user_id, status, start_time DESC),
    INDEX idx_status_start_time (status, start_time DESC),
    INDEX idx_client_start_time (client_ip, start_time DESC),
    INDEX idx_time_range (start_time, end_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建流量日志表
CREATE TABLE IF NOT EXISTS traffic_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    client_ip VARCHAR(45) NOT NULL,
    target_ip VARCHAR(45) NOT NULL,
    target_port INT NOT NULL,
    bytes_sent BIGINT DEFAULT 0,
    bytes_recv BIGINT DEFAULT 0,
    protocol VARCHAR(10) DEFAULT 'tcp',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    -- 优化后的复合索引，提升查询性能
    INDEX idx_user_timestamp (user_id, timestamp DESC),
    INDEX idx_timestamp_user (timestamp DESC, user_id),
    INDEX idx_target_analysis (target_ip, target_port, protocol),
    INDEX idx_client_timestamp (client_ip, timestamp DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建访问日志表
CREATE TABLE IF NOT EXISTS access_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    client_ip VARCHAR(45) NOT NULL,
    target_url TEXT NOT NULL,
    method VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    -- 优化后的复合索引，提升查询性能
    INDEX idx_user_timestamp (user_id, timestamp DESC),
    INDEX idx_timestamp_status (timestamp DESC, status),
    INDEX idx_client_timestamp (client_ip, timestamp DESC),
    INDEX idx_status_timestamp (status, timestamp DESC),
    INDEX idx_target_url_prefix (target_url(100), timestamp DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建URL过滤规则表
CREATE TABLE IF NOT EXISTS url_filters (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pattern VARCHAR(255) NOT NULL,
    type ENUM('block', 'allow') DEFAULT 'block',
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_pattern (pattern),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建IP白名单表
CREATE TABLE IF NOT EXISTS ip_whitelists (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(45) NOT NULL UNIQUE,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ip (ip),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建带宽限制表
CREATE TABLE IF NOT EXISTS bandwidth_limits (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    `limit` BIGINT NOT NULL,
    period ENUM('daily', 'monthly') DEFAULT 'daily',
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建代理服务器心跳表
CREATE TABLE IF NOT EXISTS proxy_heartbeats (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    proxy_id VARCHAR(100) NOT NULL,
    proxy_host VARCHAR(50) NOT NULL,
    proxy_port VARCHAR(10) NOT NULL,
    status ENUM('online', 'offline') DEFAULT 'online',
    active_conns INT DEFAULT 0,
    total_conns BIGINT DEFAULT 0,
    last_heartbeat TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_proxy_id (proxy_id),
    -- 优化后的复合索引，提升查询性能
    INDEX idx_proxy_heartbeat (proxy_id, last_heartbeat DESC),
    INDEX idx_status_heartbeat (status, last_heartbeat DESC),
    INDEX idx_heartbeat_status (last_heartbeat DESC, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户（密码为 'password' 的bcrypt哈希）
INSERT IGNORE INTO users (username, password, email, role, status) VALUES 
('admin', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin@example.com', 'admin', 'active');

-- 插入一些示例URL过滤规则
INSERT IGNORE INTO url_filters (pattern, type, description) VALUES 
('*.google.com', 'block', '阻止访问Google'),
('*.facebook.com', 'block', '阻止访问Facebook'),
('*.twitter.com', 'block', '阻止访问Twitter');

-- 插入一些示例IP白名单
INSERT IGNORE INTO ip_whitelists (ip, description) VALUES 
('192.168.1.0/24', '内网IP段'),
('10.0.0.0/8', '私有网络IP段');

-- ============================================================================
-- 创建性能优化视图，提升复杂查询性能
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

-- 创建系统性能监控视图
CREATE OR REPLACE VIEW system_performance_summary AS
SELECT 
    'traffic_logs' as table_name,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_record,
    MAX(timestamp) as latest_record
FROM traffic_logs
UNION ALL
SELECT 
    'access_logs' as table_name,
    COUNT(*) as total_records,
    MIN(timestamp) as earliest_record,
    MAX(timestamp) as latest_record
FROM access_logs
UNION ALL
SELECT 
    'proxy_sessions' as table_name,
    COUNT(*) as total_records,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record
FROM proxy_sessions;

-- ============================================================================
-- 索引优化说明
-- ============================================================================
-- 
-- 本脚本已包含针对流水表的优化索引设计：
-- 
-- 1. traffic_logs表：
--    - idx_user_timestamp: 用户ID + 时间戳（最常用查询）
--    - idx_timestamp_user: 时间戳 + 用户ID（时间范围查询）
--    - idx_target_analysis: 目标IP + 端口 + 协议（目标分析）
--    - idx_client_timestamp: 客户端IP + 时间戳（客户端行为分析）
-- 
-- 2. access_logs表：
--    - idx_user_timestamp: 用户ID + 时间戳（用户访问记录）
--    - idx_timestamp_status: 时间戳 + 状态（时间范围状态查询）
--    - idx_client_timestamp: 客户端IP + 时间戳（客户端行为分析）
--    - idx_status_timestamp: 状态 + 时间戳（状态统计查询）
--    - idx_target_url_prefix: URL前缀 + 时间戳（URL模式查询）
-- 
-- 3. proxy_sessions表：
--    - idx_user_status_time: 用户ID + 状态 + 开始时间（用户活跃会话）
--    - idx_status_start_time: 状态 + 开始时间（状态统计查询）
--    - idx_client_start_time: 客户端IP + 开始时间（客户端会话查询）
--    - idx_time_range: 开始时间 + 结束时间（时间范围查询）
-- 
-- 4. proxy_heartbeats表：
--    - idx_proxy_heartbeat: 代理ID + 最后心跳时间（健康状态查询）
--    - idx_status_heartbeat: 状态 + 最后心跳时间（状态监控查询）
--    - idx_heartbeat_status: 最后心跳时间 + 状态（时间范围状态查询）
-- 
-- 这些索引设计基于以下查询模式优化：
-- - 按用户查询特定时间段的数据
-- - 按时间范围查询统计数据
-- - 按客户端IP分析行为模式
-- - 按状态和时间进行统计查询
-- - 支持高效的范围查询和排序操作
