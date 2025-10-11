#!/bin/bash

# 应用数据库修复脚本
# 修复带宽限制表字段名问题

echo "开始修复数据库表结构..."

# 检查MySQL连接
mysql -h 127.0.0.1 -u socks5_user -psocks5_password socks5_db -e "SELECT 1;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 无法连接到数据库，请检查数据库配置"
    exit 1
fi

echo "✅ 数据库连接正常"

# 执行字段重命名
echo "正在修复带宽限制表字段名..."
mysql -h 127.0.0.1 -u socks5_user -psocks5_password socks5_db -e "
-- 检查字段是否存在
SELECT COUNT(*) as column_exists FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'bandwidth_limits' AND column_name = 'limit_value';

-- 如果存在 limit_value 字段，则重命名为 limit
ALTER TABLE bandwidth_limits CHANGE COLUMN limit_value \`limit\` BIGINT NOT NULL;
"

if [ $? -eq 0 ]; then
    echo "✅ 数据库表结构修复成功"
else
    echo "⚠️  字段可能已经重命名或不存在，继续执行..."
fi

# 验证修复结果
echo "验证修复结果..."
mysql -h 127.0.0.1 -u socks5_user -psocks5_password socks5_db -e "
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM information_schema.columns 
WHERE table_schema = DATABASE() AND table_name = 'bandwidth_limits' 
AND column_name IN ('limit', 'limit_value');
"

echo "数据库修复完成！"
