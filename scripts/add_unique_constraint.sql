-- 为bandwidth_limits表的user_id字段添加唯一约束索引
-- 确保一个用户只能有一条带宽限制记录

USE socks5_db;

-- 首先检查是否已存在唯一约束
SELECT 
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS 
WHERE TABLE_SCHEMA = 'socks5_db' 
    AND TABLE_NAME = 'bandwidth_limits' 
    AND CONSTRAINT_TYPE = 'UNIQUE';

-- 添加唯一约束索引
ALTER TABLE bandwidth_limits 
ADD CONSTRAINT uk_bandwidth_limits_user_id UNIQUE (user_id);

-- 验证约束是否添加成功
SHOW INDEX FROM bandwidth_limits WHERE Key_name = 'uk_bandwidth_limits_user_id';
