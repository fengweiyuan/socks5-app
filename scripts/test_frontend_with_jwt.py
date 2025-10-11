#!/usr/bin/env python3
"""
创建过期JWT token并测试前端重定向功能
"""

import requests
import time
import jwt

# 配置
API_BASE = "http://localhost:8012/api/v1"
JWT_SECRET = "your-secret-key-change-this-in-production"

def create_expired_token():
    """创建一个过期的JWT token"""
    # 创建一个过期的payload
    payload = {
        'user_id': 4,
        'username': 'testuser',
        'role': 'user',
        'exp': int(time.time()) - 3600,  # 1小时前过期
        'iat': int(time.time()) - 7200,  # 2小时前签发
        'nbf': int(time.time()) - 7200   # 2小时前生效
    }
    
    # 生成过期token
    expired_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return expired_token

def test_api_with_token(token, description):
    """使用指定token测试API"""
    print(f"\n{description}")
    print("-" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试用户列表API
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 401:
            print("✅ 正确返回401错误")
            return True
        else:
            print("❌ 应该返回401错误但没有返回")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    print("=" * 60)
    print("测试过期JWT token的API响应")
    print("=" * 60)
    
    # 1. 先登录获取有效token
    print("\n1. 登录获取有效token...")
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            valid_token = data.get('token')
            print(f"✅ 登录成功，获取到有效token")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return
    
    # 2. 测试有效token
    test_api_with_token(valid_token, "2. 使用有效token测试API")
    
    # 3. 创建过期token
    print("\n3. 创建过期token...")
    expired_token = create_expired_token()
    print(f"✅ 创建了过期token: {expired_token[:50]}...")
    
    # 4. 测试过期token
    is_401 = test_api_with_token(expired_token, "4. 使用过期token测试API")
    
    # 5. 生成测试用的HTML文件
    print("\n5. 生成测试HTML文件...")
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JWT Token 测试</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background-color: #d4edda; }}
        .error {{ background-color: #f8d7da; }}
        button {{ background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 5px; }}
        button:hover {{ background-color: #0056b3; }}
        #result {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; min-height: 100px; }}
    </style>
</head>
<body>
    <h1>JWT Token 测试页面</h1>
    
    <div class="section">
        <h3>测试说明</h3>
        <p>这个页面使用真实的过期JWT token来测试401重定向功能。</p>
        <p>过期token: <code>{expired_token[:50]}...</code></p>
    </div>
    
    <div class="section">
        <button onclick="testExpiredToken()">测试过期Token (应该返回401)</button>
        <button onclick="testInvalidToken()">测试无效Token (应该返回401)</button>
        <button onclick="clearResult()">清空结果</button>
    </div>
    
    <div class="section">
        <h3>测试结果</h3>
        <div id="result"></div>
    </div>

    <script>
        const API_BASE = 'http://localhost:8012/api/v1';
        
        function log(message, type = 'info') {{
            const result = document.getElementById('result');
            const timestamp = new Date().toLocaleTimeString();
            const color = type === 'error' ? 'red' : type === 'success' ? 'green' : 'black';
            result.innerHTML += `<div style="color: ${{color}}">[${{timestamp}}] ${{message}}</div>`;
        }}
        
        function clearResult() {{
            document.getElementById('result').innerHTML = '';
        }}
        
        async function testExpiredToken() {{
            log('使用过期token测试API...', 'info');
            
            const expiredToken = '{expired_token}';
            
            try {{
                const response = await fetch('${{API_BASE}}/users', {{
                    headers: {{
                        'Authorization': `Bearer ${{expiredToken}}`
                    }}
                }});
                
                log(`状态码: ${{response.status}}`, 'info');
                
                if (response.status === 401) {{
                    log('✅ 正确返回401错误（会话过期）', 'success');
                    log('模拟重定向到登录页面...', 'error');
                    
                    // 清除token
                    localStorage.removeItem('token');
                    
                    // 模拟重定向
                    setTimeout(() => {{
                        alert('会话已过期！即将跳转到登录页面');
                        log('跳转到登录页面', 'error');
                    }}, 1000);
                }} else {{
                    const data = await response.json();
                    log(`❌ 意外成功: ${{JSON.stringify(data)}}`, 'error');
                }}
            }} catch (error) {{
                log(`❌ 请求失败: ${{error.message}}`, 'error');
            }}
        }}
        
        async function testInvalidToken() {{
            log('使用无效token测试API...', 'info');
            
            const invalidToken = 'invalid_token_123';
            
            try {{
                const response = await fetch('${{API_BASE}}/users', {{
                    headers: {{
                        'Authorization': `Bearer ${{invalidToken}}`
                    }}
                }});
                
                log(`状态码: ${{response.status}}`, 'info');
                
                if (response.status === 401) {{
                    log('✅ 正确返回401错误（无效token）', 'success');
                    log('模拟重定向到登录页面...', 'error');
                    
                    // 清除token
                    localStorage.removeItem('token');
                    
                    // 模拟重定向
                    setTimeout(() => {{
                        alert('认证失败！即将跳转到登录页面');
                        log('跳转到登录页面', 'error');
                    }}, 1000);
                }} else {{
                    const data = await response.json();
                    log(`❌ 意外成功: ${{JSON.stringify(data)}}`, 'error');
                }}
            }} catch (error) {{
                log(`❌ 请求失败: ${{error.message}}`, 'error');
            }}
        }}
    </script>
</body>
</html>
"""
    
    with open('/Users/fwy/code/pub/socks5-app/scripts/jwt_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ 生成了测试HTML文件: jwt_test.html")
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"- 后端API正确处理401错误: {'✅' if is_401 else '❌'}")
    print("- 前端重定向机制: 需要手动测试HTML页面")
    print("- 建议: 在浏览器中打开 jwt_test.html 进行前端测试")
    print("=" * 60)

if __name__ == "__main__":
    main()
