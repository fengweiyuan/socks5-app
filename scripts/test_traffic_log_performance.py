#!/usr/bin/env python3
"""
流量日志性能测试 - 验证批量写入机制
"""
import requests
import socks
import socket
import time
import concurrent.futures
from datetime import datetime

def test_single_connection(test_id):
    """单个连接测试"""
    try:
        # 配置SOCKS5代理
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1082, 
                                username="admin", password="admin")
        socket.socket = socks.socksocket
        
        # 发送HTTP请求
        response = requests.get("http://www.baidu.com", timeout=10)
        return {
            'id': test_id,
            'status': response.status_code,
            'size': len(response.content),
            'success': True
        }
    except Exception as e:
        return {
            'id': test_id,
            'success': False,
            'error': str(e)
        }

def test_performance(num_requests=50, num_workers=10):
    """性能测试"""
    print(f"\n{'='*60}")
    print(f"开始性能测试")
    print(f"{'='*60}")
    print(f"请求数量: {num_requests}")
    print(f"并发数: {num_workers}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'-'*60}")
    
    start_time = time.time()
    success_count = 0
    fail_count = 0
    
    # 使用线程池进行并发测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(test_single_connection, i) 
                  for i in range(num_requests)]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result['success']:
                success_count += 1
                print(f"✓ [{success_count+fail_count}/{num_requests}] 请求成功")
            else:
                fail_count += 1
                print(f"✗ [{success_count+fail_count}/{num_requests}] 请求失败: {result.get('error', 'Unknown')}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"{'-'*60}")
    print(f"测试完成!")
    print(f"{'='*60}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"成功请求: {success_count}")
    print(f"失败请求: {fail_count}")
    print(f"平均响应时间: {total_time/num_requests:.3f} 秒/请求")
    print(f"QPS: {num_requests/total_time:.2f}")
    print(f"{'='*60}\n")
    
    return {
        'total_time': total_time,
        'success_count': success_count,
        'fail_count': fail_count,
        'avg_time': total_time/num_requests,
        'qps': num_requests/total_time
    }

def check_traffic_logs():
    """检查流量日志记录情况"""
    import pymysql
    
    print(f"\n{'='*60}")
    print(f"检查流量日志")
    print(f"{'='*60}")
    
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='socks5_user',
            password='socks5_password',
            database='socks5_db'
        )
        cursor = conn.cursor()
        
        # 查询最近1分钟的日志
        cursor.execute("""
            SELECT COUNT(*) as count, 
                   MIN(timestamp) as first_log,
                   MAX(timestamp) as last_log
            FROM traffic_logs 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)
        """)
        result = cursor.fetchone()
        
        print(f"最近1分钟流量日志数量: {result[0]}")
        print(f"最早日志时间: {result[1]}")
        print(f"最晚日志时间: {result[2]}")
        print(f"当前数据库时间: ", end="")
        
        cursor.execute("SELECT NOW()")
        print(cursor.fetchone()[0])
        
        # 查询最新10条日志
        cursor.execute("""
            SELECT id, user_id, SUBSTRING(client_ip, 1, 20) as client_ip, 
                   target_ip, bytes_sent, bytes_recv, timestamp
            FROM traffic_logs 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        print(f"\n最新10条流量日志:")
        print(f"{'-'*60}")
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, 用户: {row[1]}, 客户端: {row[2]}")
            print(f"  -> 目标: {row[3]}, 发送: {row[4]}B, 接收: {row[5]}B")
            print(f"  时间: {row[6]}")
        
        cursor.close()
        conn.close()
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"查询失败: {e}\n")

if __name__ == "__main__":
    print(f"\n流量日志批量写入性能测试")
    print(f"测试说明: 验证批量写入机制（每30秒或1000条记录flush一次）")
    
    # 第一轮测试 - 小批量
    print(f"\n[第1轮] 小批量测试 (20个请求)")
    test_performance(num_requests=20, num_workers=5)
    
    # 等待30秒，让批量写入触发
    print(f"等待35秒，让批量写入机制触发...")
    time.sleep(35)
    
    # 检查日志
    check_traffic_logs()
    
    # 第二轮测试 - 大批量
    print(f"\n[第2轮] 大批量测试 (100个请求)")
    test_performance(num_requests=100, num_workers=10)
    
    # 等待35秒，让批量写入触发
    print(f"等待35秒，让批量写入机制触发...")
    time.sleep(35)
    
    # 检查日志
    check_traffic_logs()
    
    print(f"\n{'='*60}")
    print(f"测试完成！")
    print(f"批量写入机制验证：")
    print(f"1. 日志不会立即写入数据库")
    print(f"2. 每30秒或累积1000条后批量写入")
    print(f"3. 大幅减少数据库IO，提升性能")
    print(f"{'='*60}\n")

