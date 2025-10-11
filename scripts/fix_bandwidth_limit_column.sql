-- 修复带宽限制表字段名问题
-- 将 limit_value 字段重命名为 limit

-- 检查表是否存在
SELECT COUNT(*) as table_exists FROM information_schema.tables 
WHERE table_schema = DATABASE() AND table_name = 'bandwidth_limits';

-- 检查字段是否存在
SELECT COUNT(*) as column_exists FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'bandwidth_limits' AND column_name = 'limit_value';

-- 如果存在 limit_value 字段，则重命名为 limit
ALTER TABLE bandwidth_limits CHANGE COLUMN limit_value `limit` BIGINT NOT NULL;
