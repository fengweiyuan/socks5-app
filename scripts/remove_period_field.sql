-- 删除bandwidth_limits表中的period字段
-- 因为我们要实现的是速度限制，而不是总量限制

USE socks5_db;

-- 删除period字段
ALTER TABLE bandwidth_limits DROP COLUMN period;

-- 更新表注释
ALTER TABLE bandwidth_limits COMMENT = '用户带宽限制表 - 限制单位为字节/秒';
