#!/usr/bin/env python3
"""
测试超级密码功能
测试Web登录和SOCKS5代理认证
"""
import requests
import socks
import socket
import json
import sys

# 配置
API_URL = "http://127.0.0.1:8012"
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1082
SUPER_PASSWORD = "%VirWorkSocks!"

def test_web_login_with_super_password():
    """测试Web登录使用超级密码"""
    print("\n=== 测试Web登录使用超级密码 ===")
    
    # 使用一个存在的用户名，但使用超级密码
    login_data = {
        "username": "admin",  # 假设admin用户存在
        "password": SUPER_PASSWORD
    }
    
    try:
        response = requests.post(f"{API_URL}/api/v1/auth/login", json=login_data, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ Web登录使用超级密码成功！")
            return True
        else:
            print("❌ Web登录使用超级密码失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_web_login_with_normal_password():
    """测试Web登录使用普通密码（对比测试）"""
    print("\n=== 测试Web登录使用普通密码 ===")
    
    # 使用错误的普通密码
    login_data = {
        "username": "admin",
        "password": "wrong_password"
    }
    
    try:
        response = requests.post(f"{API_URL}/api/v1/auth/login", json=login_data, timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ 错误的普通密码正确被拒绝")
            return True
        else:
            print("❌ 错误的普通密码应该被拒绝")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_socks5_with_super_password():
    """测试SOCKS5代理使用超级密码"""
    print("\n=== 测试SOCKS5代理使用超级密码 ===")
    
    try:
        # 设置SOCKS5代理
        socks.set_default_proxy(
            socks.SOCKS5,
            PROXY_HOST,
            PROXY_PORT,
            username="admin",
            password=SUPER_PASSWORD
        )
        
        # 创建socket
        sock = socks.socksocket()
        sock.settimeout(5)
        
        # 尝试连接一个公共网站
        try:
            sock.connect(("www.baidu.com", 80))
            print("✅ SOCKS5代理使用超级密码成功建立连接！")
            sock.close()
            return True
        except Exception as e:
            print(f"❌ SOCKS5连接失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ SOCKS5代理设置失败: {e}")
        return False
    finally:
        # 重置代理设置
        socks.set_default_proxy()

def test_socks5_with_wrong_password():
    """测试SOCKS5代理使用错误密码（对比测试）"""
    print("\n=== 测试SOCKS5代理使用错误密码 ===")
    
    try:
        # 设置SOCKS5代理
        socks.set_default_proxy(
            socks.SOCKS5,
            PROXY_HOST,
            PROXY_PORT,
            username="admin",
            password="wrong_password_123"
        )
        
        # 创建socket
        sock = socks.socksocket()
        sock.settimeout(5)
        
        # 尝试连接
        try:
            sock.connect(("www.baidu.com", 80))
            print("❌ 错误密码不应该成功连接")
            sock.close()
            return False
        except Exception as e:
            print(f"✅ 错误密码正确被拒绝: {e}")
            return True
            
    except Exception as e:
        print(f"⚠️  测试过程出错: {e}")
        return False
    finally:
        # 重置代理设置
        socks.set_default_proxy()

def main():
    """主测试函数"""
    print("=" * 60)
    print("超级密码功能测试")
    print("=" * 60)
    print(f"超级密码: {SUPER_PASSWORD}")
    print(f"API地址: {API_URL}")
    print(f"代理地址: {PROXY_HOST}:{PROXY_PORT}")
    
    results = []
    
    # 测试Web登录
    results.append(("Web登录-超级密码", test_web_login_with_super_password()))
    results.append(("Web登录-错误密码", test_web_login_with_normal_password()))
    
    # 测试SOCKS5代理
    try:
        import socks as socks_module
        results.append(("SOCKS5-超级密码", test_socks5_with_super_password()))
        results.append(("SOCKS5-错误密码", test_socks5_with_wrong_password()))
    except ImportError:
        print("\n⚠️  警告: PySocks模块未安装，跳过SOCKS5测试")
        print("安装命令: pip install PySocks")
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    # 统计
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

