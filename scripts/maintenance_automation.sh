#!/bin/bash

# 数据库维护自动化脚本
# 用于定期执行数据库维护任务，保持系统性能
# 建议添加到crontab定时任务中

# 配置变量
DB_NAME="socks5_db"
DB_USER="socks5_user"
DB_PASS="socks5_password"
DB_HOST="127.0.0.1"
DB_PORT="3306"

# 日志文件
LOG_DIR="/var/log/mysql/maintenance"
LOG_FILE="$LOG_DIR/maintenance_$(date +%Y%m%d_%H%M%S).log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 错误处理函数
error_exit() {
    log "错误: $1"
    exit 1
}

# 检查MySQL连接
check_mysql_connection() {
    log "检查MySQL连接..."
    if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" -e "SELECT 1;" >/dev/null 2>&1; then
        error_exit "无法连接到MySQL数据库"
    fi
    log "MySQL连接正常"
}

# 执行SQL文件
execute_sql_file() {
    local sql_file="$1"
    local description="$2"
    
    if [ ! -f "$sql_file" ]; then
        log "警告: SQL文件不存在: $sql_file"
        return 1
    fi
    
    log "执行: $description"
    if mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$sql_file" 2>&1 | tee -a "$LOG_FILE"; then
        log "成功: $description"
        return 0
    else
        log "失败: $description"
        return 1
    fi
}

# 数据清理任务
cleanup_old_data() {
    log "开始数据清理任务..."
    
    # 清理3个月前的流量日志
    log "清理3个月前的流量日志..."
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
        DELETE FROM traffic_logs 
        WHERE timestamp < DATE_SUB(NOW(), INTERVAL 3 MONTH);
        SELECT '流量日志清理完成，影响行数:' as message, ROW_COUNT() as affected_rows;
    " 2>&1 | tee -a "$LOG_FILE"
    
    # 清理3个月前的访问日志
    log "清理3个月前的访问日志..."
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
        DELETE FROM access_logs 
        WHERE timestamp < DATE_SUB(NOW(), INTERVAL 3 MONTH);
        SELECT '访问日志清理完成，影响行数:' as message, ROW_COUNT() as affected_rows;
    " 2>&1 | tee -a "$LOG_FILE"
    
    # 清理已关闭且超过1个月的代理会话
    log "清理已关闭的代理会话..."
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
        DELETE FROM proxy_sessions 
        WHERE status IN ('closed', 'disconnected') 
          AND updated_at < DATE_SUB(NOW(), INTERVAL 1 MONTH);
        SELECT '代理会话清理完成，影响行数:' as message, ROW_COUNT() as affected_rows;
    " 2>&1 | tee -a "$LOG_FILE"
    
    log "数据清理任务完成"
}

# 表优化任务
optimize_tables() {
    log "开始表优化任务..."
    
    # 获取需要优化的表列表
    local tables=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -N -e "
        SELECT TABLE_NAME 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = '$DB_NAME' 
          AND TABLE_ROWS > 1000
        ORDER BY TABLE_ROWS DESC;
    " 2>/dev/null)
    
    if [ -z "$tables" ]; then
        log "没有找到需要优化的表"
        return 0
    fi
    
    # 逐个优化表
    for table in $tables; do
        log "优化表: $table"
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
            OPTIMIZE TABLE $table;
        " 2>&1 | tee -a "$LOG_FILE"
    done
    
    log "表优化任务完成"
}

# 表分析任务
analyze_tables() {
    log "开始表分析任务..."
    
    # 分析所有表以更新统计信息
    local tables=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -N -e "
        SELECT TABLE_NAME 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = '$DB_NAME';
    " 2>/dev/null)
    
    for table in $tables; do
        log "分析表: $table"
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
            ANALYZE TABLE $table;
        " 2>&1 | tee -a "$LOG_FILE"
    done
    
    log "表分析任务完成"
}

# 性能监控任务
performance_monitoring() {
    log "开始性能监控任务..."
    
    # 检查连接数
    local connections=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -N -e "
        SHOW STATUS LIKE 'Threads_connected';
    " 2>/dev/null | awk '{print $2}')
    
    local max_connections=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -N -e "
        SHOW VARIABLES LIKE 'max_connections';
    " 2>/dev/null | awk '{print $2}')
    
    local connection_ratio=$((connections * 100 / max_connections))
    
    log "当前连接数: $connections / $max_connections ($connection_ratio%)"
    
    # 检查缓冲池命中率
    local buffer_pool_hit_rate=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -N -e "
        SELECT ROUND(
            (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') /
            NULLIF((SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') + 
                    (SELECT VARIABLE_VALUE FROM performance_schema.global_status WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'), 0) * 100, 2
        ) as buffer_pool_hit_rate;
    " 2>/dev/null)
    
    log "缓冲池命中率: ${buffer_pool_hit_rate}%"
    
    # 检查表大小
    log "表大小统计:"
    mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "
        SELECT 
            TABLE_NAME,
            TABLE_ROWS,
            ROUND(DATA_LENGTH/1024/1024, 2) as data_size_mb,
            ROUND(INDEX_LENGTH/1024/1024, 2) as index_size_mb,
            ROUND((DATA_LENGTH + INDEX_LENGTH)/1024/1024, 2) as total_size_mb
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = '$DB_NAME'
        ORDER BY TABLE_ROWS DESC;
    " 2>&1 | tee -a "$LOG_FILE"
    
    log "性能监控任务完成"
}

# 备份任务（可选）
backup_database() {
    local backup_dir="/var/backups/mysql"
    local backup_file="$backup_dir/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql"
    
    log "开始数据库备份..."
    
    # 创建备份目录
    mkdir -p "$backup_dir"
    
    # 执行备份
    if mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" \
        --single-transaction --routines --triggers "$DB_NAME" > "$backup_file" 2>&1 | tee -a "$LOG_FILE"; then
        log "数据库备份成功: $backup_file"
        
        # 压缩备份文件
        gzip "$backup_file"
        log "备份文件已压缩: ${backup_file}.gz"
        
        # 删除7天前的备份文件
        find "$backup_dir" -name "*.sql.gz" -mtime +7 -delete
        log "已清理7天前的备份文件"
    else
        log "数据库备份失败"
        return 1
    fi
}

# 主函数
main() {
    local task="$1"
    
    log "数据库维护脚本开始执行"
    log "任务类型: ${task:-全部}"
    
    # 检查MySQL连接
    check_mysql_connection
    
    case "$task" in
        "cleanup")
            cleanup_old_data
            ;;
        "optimize")
            optimize_tables
            ;;
        "analyze")
            analyze_tables
            ;;
        "monitor")
            performance_monitoring
            ;;
        "backup")
            backup_database
            ;;
        "all"|"")
            # 执行所有任务
            cleanup_old_data
            analyze_tables
            performance_monitoring
            # 注意：优化表操作比较耗时，建议在低峰期单独执行
            # optimize_tables
            ;;
        *)
            log "未知任务类型: $task"
            echo "用法: $0 [cleanup|optimize|analyze|monitor|backup|all]"
            exit 1
            ;;
    esac
    
    log "数据库维护脚本执行完成"
}

# 脚本入口
if [ "$#" -eq 0 ]; then
    main "all"
else
    main "$1"
fi
