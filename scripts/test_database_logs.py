#!/usr/bin/env python3
"""
检查数据库中的日志审计数据
"""

import pymysql
import json
from datetime import datetime

def connect_database():
    """连接数据库"""
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='socks5_user',
            password='socks5_password',
            database='socks5_db',
            charset='utf8mb4'
        )
        return connection
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def check_access_logs(connection):
    """检查访问日志"""
    print("\n" + "="*60)
    print("📋 访问日志 (AccessLog)")
    print("="*60)
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM access_logs")
        total = cursor.fetchone()['total']
        print(f"总记录数: {total}")
        
        if total > 0:
            # 获取最近的10条记录
            cursor.execute("""
                SELECT al.*, u.username 
                FROM access_logs al 
                LEFT JOIN users u ON al.user_id = u.id 
                ORDER BY al.timestamp DESC 
                LIMIT 10
            """)
            
            logs = cursor.fetchall()
            
            print(f"\n最近的 {len(logs)} 条记录:")
            for i, log in enumerate(logs, 1):
                print(f"\n{i}. 记录ID: {log['id']}")
                print(f"   用户: {log['username']} (ID: {log['user_id']})")
                print(f"   客户端IP: {log['client_ip']}")
                print(f"   目标URL: {log['target_url']}")
                print(f"   方法: {log['method']}")
                print(f"   状态: {log['status']}")
                print(f"   用户代理: {log['user_agent'][:50]}..." if len(log['user_agent']) > 50 else f"   用户代理: {log['user_agent']}")
                print(f"   时间: {log['timestamp']}")
                
        cursor.close()
        
    except Exception as e:
        print(f"❌ 查询访问日志失败: {e}")

def check_traffic_logs(connection):
    """检查流量日志"""
    print("\n" + "="*60)
    print("🌐 流量日志 (TrafficLog)")
    print("="*60)
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM traffic_logs")
        total = cursor.fetchone()['total']
        print(f"总记录数: {total}")
        
        if total > 0:
            # 获取最近的10条记录
            cursor.execute("""
                SELECT tl.*, u.username 
                FROM traffic_logs tl 
                LEFT JOIN users u ON tl.user_id = u.id 
                ORDER BY tl.timestamp DESC 
                LIMIT 10
            """)
            
            logs = cursor.fetchall()
            
            print(f"\n最近的 {len(logs)} 条记录:")
            for i, log in enumerate(logs, 1):
                print(f"\n{i}. 记录ID: {log['id']}")
                print(f"   用户: {log['username']} (ID: {log['user_id']})")
                print(f"   客户端IP: {log['client_ip']}")
                print(f"   目标IP: {log['target_ip']}")
                print(f"   目标端口: {log['target_port']}")
                print(f"   协议: {log['protocol']}")
                print(f"   发送字节: {log['bytes_sent']}")
                print(f"   接收字节: {log['bytes_recv']}")
                print(f"   时间: {log['timestamp']}")
                
        cursor.close()
        
    except Exception as e:
        print(f"❌ 查询流量日志失败: {e}")

def check_proxy_sessions(connection):
    """检查代理会话"""
    print("\n" + "="*60)
    print("🔗 代理会话 (ProxySession)")
    print("="*60)
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM proxy_sessions")
        total = cursor.fetchone()['total']
        print(f"总记录数: {total}")
        
        if total > 0:
            # 获取最近的10条记录
            cursor.execute("""
                SELECT ps.*, u.username 
                FROM proxy_sessions ps 
                LEFT JOIN users u ON ps.user_id = u.id 
                ORDER BY ps.start_time DESC 
                LIMIT 10
            """)
            
            sessions = cursor.fetchall()
            
            print(f"\n最近的 {len(sessions)} 条记录:")
            for i, session in enumerate(sessions, 1):
                print(f"\n{i}. 会话ID: {session['id']}")
                print(f"   用户: {session['username']} (ID: {session['user_id']})")
                print(f"   客户端IP: {session['client_ip']}")
                print(f"   开始时间: {session['start_time']}")
                print(f"   结束时间: {session['end_time']}")
                print(f"   状态: {session['status']}")
                print(f"   发送字节: {session['bytes_sent']}")
                print(f"   接收字节: {session['bytes_recv']}")
                
        cursor.close()
        
    except Exception as e:
        print(f"❌ 查询代理会话失败: {e}")

def check_users(connection):
    """检查用户表"""
    print("\n" + "="*60)
    print("👥 用户信息")
    print("="*60)
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("SELECT id, username, email, role, status, bandwidth_limit, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        print(f"用户总数: {len(users)}")
        for user in users:
            print(f"- {user['username']} (ID: {user['id']}, 角色: {user['role']}, 状态: {user['status']}, 带宽限制: {user['bandwidth_limit']})")
            
        cursor.close()
        
    except Exception as e:
        print(f"❌ 查询用户失败: {e}")

def analyze_log_types(connection):
    """分析日志类型和真实性"""
    print("\n" + "="*60)
    print("📊 日志类型和真实性分析")
    print("="*60)
    
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 分析访问日志的类型
        print("\n🔍 访问日志类型分析:")
        cursor.execute("""
            SELECT 
                target_url,
                method,
                status,
                COUNT(*) as count
            FROM access_logs 
            GROUP BY target_url, method, status
            ORDER BY count DESC
            LIMIT 10
        """)
        
        access_stats = cursor.fetchall()
        for stat in access_stats:
            print(f"  {stat['method']} {stat['target_url']} - {stat['status']}: {stat['count']}次")
        
        # 分析流量日志的目标IP
        print("\n🌐 流量日志目标分析:")
        cursor.execute("""
            SELECT 
                target_ip,
                target_port,
                COUNT(*) as count,
                SUM(bytes_sent) as total_sent,
                SUM(bytes_recv) as total_recv
            FROM traffic_logs 
            GROUP BY target_ip, target_port
            ORDER BY count DESC
            LIMIT 10
        """)
        
        traffic_stats = cursor.fetchall()
        for stat in traffic_stats:
            print(f"  {stat['target_ip']}:{stat['target_port']} - {stat['count']}次连接, 发送:{stat['total_sent']}字节, 接收:{stat['total_recv']}字节")
        
        # 检查数据的时间分布
        print("\n⏰ 时间分布分析:")
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as count
            FROM access_logs 
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 7
        """)
        
        time_stats = cursor.fetchall()
        for stat in time_stats:
            print(f"  {stat['date']}: {stat['count']}条访问日志")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ 分析日志失败: {e}")

def main():
    print("=" * 80)
    print("🔍 SOCKS5应用日志审计分析")
    print("=" * 80)
    
    # 连接数据库
    connection = connect_database()
    if not connection:
        return
    
    try:
        # 检查各种日志类型
        check_users(connection)
        check_access_logs(connection)
        check_traffic_logs(connection)
        check_proxy_sessions(connection)
        analyze_log_types(connection)
        
        print("\n" + "="*80)
        print("✅ 日志审计分析完成")
        print("="*80)
        
    finally:
        connection.close()

if __name__ == "__main__":
    main()
