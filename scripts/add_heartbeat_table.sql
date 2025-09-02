-- 添加代理服务器心跳表的迁移脚本
-- 使用数据库
USE socks5_db;

-- 创建代理服务器心跳表
CREATE TABLE IF NOT EXISTS proxy_heartbeats (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    proxy_id VARCHAR(100) NOT NULL COMMENT '代理服务器唯一标识',
    proxy_host VARCHAR(50) NOT NULL COMMENT '代理服务器主机地址',
    proxy_port VARCHAR(10) NOT NULL COMMENT '代理服务器端口',
    status ENUM('online', 'offline') DEFAULT 'online' COMMENT '服务器状态',
    active_conns INT DEFAULT 0 COMMENT '当前活跃连接数',
    total_conns BIGINT DEFAULT 0 COMMENT '累计总连接数',
    last_heartbeat TIMESTAMP NOT NULL COMMENT '最后心跳时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY unique_proxy_id (proxy_id),
    INDEX idx_proxy_id (proxy_id),
    INDEX idx_status (status),
    INDEX idx_last_heartbeat (last_heartbeat)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理服务器心跳表';

-- 查看表是否创建成功
SHOW CREATE TABLE proxy_heartbeats;

-- 显示表结构
DESCRIBE proxy_heartbeats;
