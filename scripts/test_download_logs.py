#!/usr/bin/env python3
"""
测试文件下载和清理操作的日志审计功能
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

def test_export_logs(token):
    """测试导出日志"""
    print("\n📥 测试导出日志...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/logs/export", headers=headers)
        print(f"导出状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查响应头
            content_type = response.headers.get('Content-Type', '')
            content_disposition = response.headers.get('Content-Disposition', '')
            
            print(f"✅ 日志导出成功")
            print(f"内容类型: {content_type}")
            print(f"文件信息: {content_disposition}")
            print(f"文件大小: {len(response.content)} 字节")
            
            # 保存文件用于验证
            filename = f"test_export_logs_{int(time.time())}.csv"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"文件已保存为: {filename}")
            
            return True
        else:
            print(f"❌ 日志导出失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 导出日志请求失败: {e}")
        return False

def test_clear_logs(token):
    """测试清理日志"""
    print("\n🗑️ 测试清理日志...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(f"{API_BASE}/logs", headers=headers)
        print(f"清理状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 日志清理成功")
            return True
        else:
            print(f"❌ 日志清理失败")
            return False
    except Exception as e:
        print(f"❌ 清理日志请求失败: {e}")
        return False

def check_download_logs(token):
    """检查下载和清理操作日志"""
    print("\n📋 检查下载和清理操作日志...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/logs?pageSize=20", headers=headers)
        print(f"日志查询状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            
            print(f"✅ 获取到 {len(logs)} 条日志记录")
            
            # 查找下载和清理相关的日志
            download_logs = []
            for log in logs:
                user_agent = log.get('user_agent', '')
                url = log.get('target_url', '')
                
                # 检查是否是导出或清理操作
                if ('EXPORT_LOGS' in user_agent or 
                    'CLEAR_LOGS' in user_agent or
                    url.endswith('/logs/export') or
                    (url.endswith('/logs') and log.get('method') == 'DELETE')):
                    download_logs.append(log)
            
            if download_logs:
                print(f"\n🔍 找到 {len(download_logs)} 条下载/清理操作日志:")
                for i, log in enumerate(download_logs, 1):
                    user_agent = log.get('user_agent', '')
                    url = log.get('target_url', '')
                    
                    operation = ""
                    if 'EXPORT_LOGS' in user_agent or url.endswith('/logs/export'):
                        operation = "导出日志"
                    elif 'CLEAR_LOGS' in user_agent or (url.endswith('/logs') and log.get('method') == 'DELETE'):
                        operation = "清理日志"
                    else:
                        operation = "日志操作"
                    
                    print(f"\n{i}. {operation}")
                    print(f"   操作用户: {log.get('user', {}).get('username', 'N/A')}")
                    print(f"   目标URL: {log.get('target_url', 'N/A')}")
                    print(f"   方法: {log.get('method', 'N/A')}")
                    print(f"   状态: {log.get('status', 'N/A')}")
                    print(f"   客户端IP: {log.get('client_ip', 'N/A')}")
                    print(f"   时间: {log.get('timestamp', 'N/A')}")
                    print(f"   详情: {user_agent}")
            else:
                print("❌ 没有找到下载/清理操作日志")
        else:
            print(f"❌ 获取日志失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 检查日志请求失败: {e}")

def main():
    print("=" * 80)
    print("📥 文件下载和清理操作日志审计测试")
    print("=" * 80)
    
    # 登录获取token
    token = login_and_get_token()
    if not token:
        return
    
    # 执行操作
    operations_success = []
    
    # 1. 导出日志
    operations_success.append(test_export_logs(token))
    time.sleep(1)  # 等待日志记录
    
    # 2. 清理日志
    operations_success.append(test_clear_logs(token))
    time.sleep(1)  # 等待日志记录
    
    # 检查日志
    check_download_logs(token)
    
    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结:")
    print(f"- 导出日志: {'✅ 成功' if operations_success[0] else '❌ 失败'}")
    print(f"- 清理日志: {'✅ 成功' if operations_success[1] else '❌ 失败'}")
    
    success_count = sum(operations_success)
    print(f"\n总操作成功: {success_count}/2")
    
    if success_count == 2:
        print("🎉 所有下载和清理操作测试通过！")
        print("💡 请登录Web界面查看日志审计页面确认日志记录")
    else:
        print("⚠️ 部分操作失败，请检查日志")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
