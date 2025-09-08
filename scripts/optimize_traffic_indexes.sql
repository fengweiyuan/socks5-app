-- 优化流量查询相关的索引
-- 为历史流量查询功能添加必要的索引

-- 1. 为 traffic_logs 表添加复合索引，优化按用户和时间范围查询
CREATE INDEX idx_traffic_user_timestamp 
ON traffic_logs (user_id, timestamp DESC);

-- 2. 为 traffic_logs 表添加复合索引，优化按时间范围查询
CREATE INDEX idx_traffic_timestamp_desc 
ON traffic_logs (timestamp DESC);

-- 3. 为 traffic_logs 表添加复合索引，优化按目标IP和时间查询
CREATE INDEX idx_traffic_target_timestamp 
ON traffic_logs (target_ip, timestamp DESC);

-- 4. 为 traffic_logs 表添加复合索引，优化按用户、目标IP和时间查询
CREATE INDEX idx_traffic_user_target_timestamp 
ON traffic_logs (user_id, target_ip, timestamp DESC);

-- 5. 为 traffic_logs 表添加复合索引，优化按用户和字节数查询
CREATE INDEX idx_traffic_user_bytes 
ON traffic_logs (user_id, bytes_sent DESC, bytes_recv DESC);

-- 6. 为 users 表添加复合索引，优化按状态和用户名查询
CREATE INDEX idx_users_status_username 
ON users (status, username);

-- 7. 为 users 表添加复合索引，优化按角色和状态查询
CREATE INDEX idx_users_role_status 
ON users (role, status);

-- 显示优化后的索引信息
SHOW INDEX FROM traffic_logs;
SHOW INDEX FROM users;
