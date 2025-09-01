#!/bin/bash

# 数据库连接测试脚本

set -e

echo "测试数据库连接..."

# 检查配置文件
if [ ! -f "configs/config.yaml" ]; then
    echo "错误: 配置文件不存在 configs/config.yaml"
    exit 1
fi

# 读取数据库配置
DB_HOST=$(grep -A 5 "database:" configs/config.yaml | grep "host:" | awk '{print $2}' | tr -d '"')
DB_PORT=$(grep -A 5 "database:" configs/config.yaml | grep "port:" | awk '{print $2}' | tr -d '"')
DB_USER=$(grep -A 5 "database:" configs/config.yaml | grep "username:" | awk '{print $2}' | tr -d '"')
DB_PASS=$(grep -A 5 "database:" configs/config.yaml | grep "password:" | awk '{print $2}' | tr -d '"')
DB_NAME=$(grep -A 5 "database:" configs/config.yaml | grep "database:" | awk '{print $2}' | tr -d '"')

echo "数据库配置:"
echo "  主机: $DB_HOST"
echo "  端口: $DB_PORT"
echo "  用户: $DB_USER"
echo "  数据库: $DB_NAME"

# 测试MySQL连接
echo ""
echo "测试MySQL连接..."

if command -v mysql &> /dev/null; then
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "USE $DB_NAME; SHOW TABLES;" 2>/dev/null; then
        echo "✅ MySQL连接成功"
        
        # 检查表是否存在
        echo ""
        echo "检查数据库表..."
        TABLES=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "USE $DB_NAME; SHOW TABLES;" 2>/dev/null | tail -n +2)
        
        if [ -n "$TABLES" ]; then
            echo "✅ 数据库表已存在:"
            echo "$TABLES"
        else
            echo "⚠️  数据库表不存在，需要运行初始化脚本"
            echo "请运行: mysql -u $DB_USER -p$DB_PASS $DB_NAME < scripts/init.sql"
        fi
    else
        echo "❌ MySQL连接失败"
        echo "请检查:"
        echo "  1. MySQL服务是否启动"
        echo "  2. 数据库配置是否正确"
        echo "  3. 用户权限是否足够"
        exit 1
    fi
else
    echo "❌ MySQL客户端未安装"
    echo "请安装MySQL客户端:"
    echo "  Ubuntu/Debian: sudo apt-get install mysql-client"
    echo "  CentOS/RHEL: sudo yum install mysql"
    echo "  macOS: brew install mysql-client"
    exit 1
fi

echo ""
echo "数据库连接测试完成！"
