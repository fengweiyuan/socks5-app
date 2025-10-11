#!/usr/bin/env python3
"""
综合测试所有操作的日志审计功能
"""

import requests
import json
import time
from datetime import datetime

# 配置
API_BASE = "http://localhost:8012/api/v1"

def login_and_get_token():
    """登录并获取token"""
    print("🔐 登录获取token...")
    login_data = {
        "username": "testuser2",  # 使用管理员用户
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ 登录成功")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

def test_all_operations(token):
    """测试所有操作"""
    print("\n" + "=" * 80)
    print("🧪 执行各种操作测试")
    print("=" * 80)
    
    operations_results = {}
    
    # 1. 创建用户
    print("\n1️⃣ 创建用户操作...")
    user_data = {
        "username": f"test_user_{int(time.time())}",
        "email": "test@example.com",
        "password": "testpass123",
        "role": "user",
        "bandwidth_limit": 1024
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{API_BASE}/users", json=user_data, headers=headers)
        if response.status_code == 201:
            print("✅ 用户创建成功")
            operations_results['create_user'] = True
            test_user_id = response.json().get('user', {}).get('id')
        else:
            print(f"❌ 用户创建失败: {response.status_code}")
            operations_results['create_user'] = False
            test_user_id = None
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        operations_results['create_user'] = False
        test_user_id = None
    
    time.sleep(1)
    
    # 2. 更新用户
    if test_user_id:
        print("\n2️⃣ 更新用户操作...")
        update_data = {
            "email": "updated@example.com",
            "role": "user",
            "status": "active",
            "bandwidth_limit": 2048
        }
        
        try:
            response = requests.put(f"{API_BASE}/users/{test_user_id}", json=update_data, headers=headers)
            if response.status_code == 200:
                print("✅ 用户更新成功")
                operations_results['update_user'] = True
            else:
                print(f"❌ 用户更新失败: {response.status_code}")
                operations_results['update_user'] = False
        except Exception as e:
            print(f"❌ 更新用户失败: {e}")
            operations_results['update_user'] = False
        
        time.sleep(1)
        
        # 3. 删除用户
        print("\n3️⃣ 删除用户操作...")
        try:
            response = requests.delete(f"{API_BASE}/users/{test_user_id}", headers=headers)
            if response.status_code == 200:
                print("✅ 用户删除成功")
                operations_results['delete_user'] = True
            else:
                print(f"❌ 用户删除失败: {response.status_code}")
                operations_results['delete_user'] = False
        except Exception as e:
            print(f"❌ 删除用户失败: {e}")
            operations_results['delete_user'] = False
    else:
        operations_results['update_user'] = False
        operations_results['delete_user'] = False
    
    time.sleep(1)
    
    # 4. 导出日志
    print("\n4️⃣ 导出日志操作...")
    try:
        response = requests.get(f"{API_BASE}/logs/export", headers=headers)
        if response.status_code == 200:
            print("✅ 日志导出成功")
            operations_results['export_logs'] = True
        else:
            print(f"❌ 日志导出失败: {response.status_code}")
            operations_results['export_logs'] = False
    except Exception as e:
        print(f"❌ 导出日志失败: {e}")
        operations_results['export_logs'] = False
    
    time.sleep(1)
    
    # 5. 清理日志
    print("\n5️⃣ 清理日志操作...")
    try:
        response = requests.delete(f"{API_BASE}/logs", headers=headers)
        if response.status_code == 200:
            print("✅ 日志清理成功")
            operations_results['clear_logs'] = True
        else:
            print(f"❌ 日志清理失败: {response.status_code}")
            operations_results['clear_logs'] = False
    except Exception as e:
        print(f"❌ 清理日志失败: {e}")
        operations_results['clear_logs'] = False
    
    time.sleep(1)
    
    # 6. 退出登录
    print("\n6️⃣ 退出登录操作...")
    try:
        response = requests.post(f"{API_BASE}/auth/logout", headers=headers)
        if response.status_code == 200:
            print("✅ 退出登录成功")
            operations_results['logout'] = True
        else:
            print(f"❌ 退出登录失败: {response.status_code}")
            operations_results['logout'] = False
    except Exception as e:
        print(f"❌ 退出登录失败: {e}")
        operations_results['logout'] = False
    
    return operations_results

def analyze_logs(token):
    """分析所有操作日志"""
    print("\n" + "=" * 80)
    print("📊 日志审计分析")
    print("=" * 80)
    
    # 重新登录以查看日志
    login_data = {"username": "testuser2", "password": "testpass"}
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get('token')
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = requests.get(f"{API_BASE}/logs?pageSize=50", headers=headers)
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                
                print(f"✅ 获取到 {len(logs)} 条日志记录")
                
                # 分析不同类型的操作
                operation_counts = {
                    'login': 0,
                    'logout': 0,
                    'create_user': 0,
                    'update_user': 0,
                    'delete_user': 0,
                    'export_logs': 0,
                    'clear_logs': 0,
                    'other': 0
                }
                
                for log in logs:
                    user_agent = log.get('user_agent', '')
                    url = log.get('target_url', '')
                    method = log.get('method', '')
                    
                    if 'CREATE_USER' in user_agent:
                        operation_counts['create_user'] += 1
                    elif 'UPDATE_USER' in user_agent:
                        operation_counts['update_user'] += 1
                    elif 'DELETE_USER' in user_agent:
                        operation_counts['delete_user'] += 1
                    elif 'EXPORT_LOGS' in user_agent or url.endswith('/logs/export'):
                        operation_counts['export_logs'] += 1
                    elif 'CLEAR_LOGS' in user_agent or (url.endswith('/logs') and method == 'DELETE'):
                        operation_counts['clear_logs'] += 1
                    elif '/auth/login' in url:
                        operation_counts['login'] += 1
                    elif '/auth/logout' in url:
                        operation_counts['logout'] += 1
                    else:
                        operation_counts['other'] += 1
                
                print(f"\n📈 操作统计:")
                print(f"  🔐 登录操作: {operation_counts['login']} 次")
                print(f"  🚪 退出操作: {operation_counts['logout']} 次")
                print(f"  👤 创建用户: {operation_counts['create_user']} 次")
                print(f"  ✏️ 更新用户: {operation_counts['update_user']} 次")
                print(f"  🗑️ 删除用户: {operation_counts['delete_user']} 次")
                print(f"  📥 导出日志: {operation_counts['export_logs']} 次")
                print(f"  🧹 清理日志: {operation_counts['clear_logs']} 次")
                print(f"  🔧 其他操作: {operation_counts['other']} 次")
                
                # 显示最近的操作日志
                print(f"\n🕒 最近的操作日志:")
                recent_logs = logs[:10]  # 最近10条
                for i, log in enumerate(recent_logs, 1):
                    user_agent = log.get('user_agent', '')
                    url = log.get('target_url', '')
                    
                    operation = "其他操作"
                    if 'CREATE_USER' in user_agent:
                        operation = "创建用户"
                    elif 'UPDATE_USER' in user_agent:
                        operation = "更新用户"
                    elif 'DELETE_USER' in user_agent:
                        operation = "删除用户"
                    elif 'EXPORT_LOGS' in user_agent:
                        operation = "导出日志"
                    elif 'CLEAR_LOGS' in user_agent:
                        operation = "清理日志"
                    elif '/auth/login' in url:
                        operation = "登录"
                    elif '/auth/logout' in url:
                        operation = "退出"
                    
                    username = log.get('user', {}).get('username', 'N/A')
                    timestamp = log.get('timestamp', 'N/A')
                    
                    print(f"  {i:2d}. {operation} - {username} - {timestamp}")
                
        except Exception as e:
            print(f"❌ 分析日志失败: {e}")
    else:
        print("❌ 重新登录失败")

def main():
    print("=" * 80)
    print("🧪 综合日志审计功能测试")
    print("=" * 80)
    
    # 登录获取token
    token = login_and_get_token()
    if not token:
        return
    
    # 执行所有操作
    operations_results = test_all_operations(token)
    
    # 分析日志
    analyze_logs(token)
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 测试总结:")
    total_operations = len(operations_results)
    successful_operations = sum(operations_results.values())
    
    for operation, success in operations_results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {operation}: {status}")
    
    print(f"\n总体成功率: {successful_operations}/{total_operations} ({successful_operations/total_operations*100:.1f}%)")
    
    if successful_operations == total_operations:
        print("🎉 所有操作的日志审计功能测试通过！")
        print("💡 请登录Web界面查看日志审计页面确认所有操作都已记录")
    else:
        print("⚠️ 部分操作失败，请检查相关功能")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
