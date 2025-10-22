#!/bin/bash

echo "=========================================="
echo "SOCKS5 认证问题诊断工具"
echo "=========================================="
echo ""

# 读取配置文件
CONFIG_FILE="configs/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 从配置文件解析数据库连接信息
DB_HOST=$(grep -A 10 "^database:" "$CONFIG_FILE" | grep "host:" | awk '{print $2}' | tr -d '"')
DB_PORT=$(grep -A 10 "^database:" "$CONFIG_FILE" | grep "port:" | awk '{print $2}' | tr -d '"')
DB_USER=$(grep -A 10 "^database:" "$CONFIG_FILE" | grep "username:" | awk '{print $2}' | tr -d '"')
DB_PASS=$(grep -A 10 "^database:" "$CONFIG_FILE" | grep "password:" | awk '{print $2}' | tr -d '"')
DB_NAME=$(grep -A 10 "^database:" "$CONFIG_FILE" | grep "database:" | awk '{print $2}' | tr -d '"')

PROXY_PORT=$(grep -A 5 "^proxy:" "$CONFIG_FILE" | grep "port:" | awk '{print $2}' | tr -d '"')

echo "📋 配置信息："
echo "   数据库: ${DB_HOST}:${DB_PORT}"
echo "   数据库名: ${DB_NAME}"
echo "   代理端口: ${PROXY_PORT}"
echo ""

# 1. 检查代理服务是否运行
echo "1️⃣  检查代理服务状态..."
if lsof -i :${PROXY_PORT} > /dev/null 2>&1; then
    echo "   ✅ 代理服务正在运行 (端口 ${PROXY_PORT})"
    lsof -i :${PROXY_PORT} | grep LISTEN
else
    echo "   ❌ 代理服务未运行 (端口 ${PROXY_PORT} 未监听)"
    echo "   请先启动代理服务: ./bin/proxy 或 make run-proxy"
    exit 1
fi
echo ""

# 2. 检查 MySQL 连接
echo "2️⃣  检查 MySQL 数据库连接..."
if command -v mysql > /dev/null 2>&1; then
    if mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" -e "SELECT 1" > /dev/null 2>&1; then
        echo "   ✅ MySQL 连接成功"
    else
        echo "   ❌ MySQL 连接失败！"
        echo "   请检查："
        echo "      - MySQL 服务是否启动"
        echo "      - 配置文件中的数据库连接信息是否正确"
        echo "      - 防火墙是否允许连接"
        exit 1
    fi
else
    echo "   ⚠️  未安装 mysql 客户端，跳过数据库连接测试"
fi
echo ""

# 3. 检查数据库和表
echo "3️⃣  检查数据库和表..."
if command -v mysql > /dev/null 2>&1; then
    DB_EXISTS=$(mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" -e "SHOW DATABASES LIKE '${DB_NAME}'" 2>/dev/null | grep -c "${DB_NAME}")
    if [ "$DB_EXISTS" -eq 1 ]; then
        echo "   ✅ 数据库 ${DB_NAME} 存在"
        
        # 检查 users 表
        TABLE_EXISTS=$(mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" -e "SHOW TABLES LIKE 'users'" 2>/dev/null | grep -c "users")
        if [ "$TABLE_EXISTS" -eq 1 ]; then
            echo "   ✅ users 表存在"
        else
            echo "   ❌ users 表不存在！"
            exit 1
        fi
    else
        echo "   ❌ 数据库 ${DB_NAME} 不存在！"
        exit 1
    fi
fi
echo ""

# 4. 检查活跃用户
echo "4️⃣  检查活跃用户列表..."
if command -v mysql > /dev/null 2>&1; then
    echo "   活跃用户 (status='active')："
    mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" -e "
        SELECT id, username, status, created_at 
        FROM users 
        WHERE status='active' 
        ORDER BY id 
        LIMIT 10
    " 2>/dev/null | tail -n +2
    
    ACTIVE_COUNT=$(mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" -e "
        SELECT COUNT(*) FROM users WHERE status='active'
    " 2>/dev/null | tail -n 1)
    
    echo ""
    echo "   共有 ${ACTIVE_COUNT} 个活跃用户"
    
    if [ "$ACTIVE_COUNT" -eq 0 ]; then
        echo "   ⚠️  警告：没有活跃用户！所有认证都会失败"
    fi
fi
echo ""

# 5. 测试认证
echo "5️⃣  测试 SOCKS5 认证..."
echo "   请手动测试（将下面的命令中的用户名和密码替换为实际值）："
echo ""
echo "   # 使用超级密码测试（任意用户名 + 超级密码）："
echo "   curl --socks5 admin:%VirWorkSocks!@127.0.0.1:${PROXY_PORT} http://www.baidu.com -v"
echo ""
echo "   # 使用普通用户密码测试："
echo "   curl --socks5 your_username:your_password@127.0.0.1:${PROXY_PORT} http://www.baidu.com -v"
echo ""

# 6. 查看代理日志
echo "6️⃣  最近的代理日志（如果有认证失败信息会在这里）："
if [ -f "logs/proxy.log" ]; then
    echo "   --- logs/proxy.log (最后 20 行) ---"
    tail -20 logs/proxy.log | grep -E "(认证|auth|密码|password|用户|user)" || echo "   (无相关日志)"
elif [ -f "logs/app.log" ]; then
    echo "   --- logs/app.log (最后 20 行) ---"
    tail -20 logs/app.log | grep -E "(认证|auth|密码|password|用户|user)" || echo "   (无相关日志)"
else
    echo "   ⚠️  未找到日志文件"
fi
echo ""

echo "=========================================="
echo "诊断完成！"
echo ""
echo "💡 常见问题解决方案："
echo ""
echo "1. 如果显示 '用户不存在或已被禁用'："
echo "   - 检查用户名是否正确"
echo "   - 检查用户的 status 字段是否为 'active'"
echo "   - 在数据库中创建或启用用户"
echo ""
echo "2. 如果显示 '密码错误'："
echo "   - 检查密码是否正确"
echo "   - 或使用超级密码: %VirWorkSocks!"
echo ""
echo "3. 如果显示 '数据库连接不可用'："
echo "   - 检查 MySQL 服务是否运行"
echo "   - 检查配置文件中的数据库连接信息"
echo "   - 检查防火墙设置"
echo ""
echo "4. 查看详细错误日志："
echo "   tail -f logs/proxy.log"
echo "   或"
echo "   tail -f logs/app.log"
echo "=========================================="

