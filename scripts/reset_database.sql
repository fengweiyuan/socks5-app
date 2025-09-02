-- 重置数据库脚本
-- 删除现有数据库并重新创建

-- 删除数据库（如果存在）
DROP DATABASE IF EXISTS socks5_db;

-- 重新创建数据库
CREATE DATABASE socks5_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 删除用户（如果存在）
DROP USER IF EXISTS 'socks5_user'@'%';
DROP USER IF EXISTS 'socks5_user'@'localhost';
DROP USER IF EXISTS 'socks5_user'@'127.0.0.1';

-- 创建用户
CREATE USER 'socks5_user'@'%' IDENTIFIED BY 'socks5_password';
CREATE USER 'socks5_user'@'localhost' IDENTIFIED BY 'socks5_password';
CREATE USER 'socks5_user'@'127.0.0.1' IDENTIFIED BY 'socks5_password';

-- 授权
GRANT ALL PRIVILEGES ON socks5_db.* TO 'socks5_user'@'%';
GRANT ALL PRIVILEGES ON socks5_db.* TO 'socks5_user'@'localhost';
GRANT ALL PRIVILEGES ON socks5_db.* TO 'socks5_user'@'127.0.0.1';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示创建结果
SHOW DATABASES LIKE 'socks5_db';
SELECT User, Host FROM mysql.user WHERE User = 'socks5_user';


