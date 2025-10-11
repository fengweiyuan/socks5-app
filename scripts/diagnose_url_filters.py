#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL过滤规则诊断脚本
检查数据库中的过滤规则，找出可能导致内网地址无法访问的问题
"""

import pymysql
import sys

# MySQL配置
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'socks5_user',
    'password': 'socks5_password',
    'database': 'socks5_db',
    'charset': 'utf8mb4'
}


def print_section(title):
    """打印分隔标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def diagnose_filters():
    """诊断过滤规则"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        print_section("当前数据库中的所有URL过滤规则")
        
        # 查询所有规则
        cursor.execute("SELECT * FROM url_filters ORDER BY id")
        all_filters = cursor.fetchall()
        
        if not all_filters:
            print("\n✓ 数据库中没有任何过滤规则")
            return
        
        print(f"\n共有 {len(all_filters)} 条过滤规则：\n")
        
        # 分类规则
        enabled_filters = []
        disabled_filters = []
        problematic_filters = []
        
        for f in all_filters:
            status = "启用" if f['enabled'] else "禁用"
            print(f"ID: {f['id']}")
            print(f"  Pattern:     {f['pattern']}")
            print(f"  Type:        {f['type']}")
            print(f"  Enabled:     {f['enabled']} ({status})")
            print(f"  Description: {f['description']}")
            print(f"  Created:     {f['created_at']}")
            print()
            
            if f['enabled']:
                enabled_filters.append(f)
                
                # 检查可能有问题的规则
                pattern = f['pattern']
                filter_type = f['type']
                
                # 问题1: pattern过于宽泛
                if len(pattern) <= 3:
                    problematic_filters.append({
                        'id': f['id'],
                        'issue': f"Pattern '{pattern}' 过于宽泛，会匹配很多域名",
                        'severity': '高'
                    })
                
                # 问题2: 包含通配符
                if '*' in pattern or '?' in pattern:
                    problematic_filters.append({
                        'id': f['id'],
                        'issue': f"Pattern '{pattern}' 包含通配符，可能影响范围过大",
                        'severity': '高'
                    })
                
                # 问题3: 只是一个数字或很短的字符串
                if pattern.isdigit():
                    problematic_filters.append({
                        'id': f['id'],
                        'issue': f"Pattern '{pattern}' 是纯数字，会匹配包含该数字的所有域名和IP",
                        'severity': '高'
                    })
                
                # 问题4: 包含常见的IP段或端口号
                if pattern in ['192', '168', '10', '172', '127']:
                    problematic_filters.append({
                        'id': f['id'],
                        'issue': f"Pattern '{pattern}' 是常见内网IP段，会阻止内网访问",
                        'severity': '严重'
                    })
                
                # 问题5: 空pattern或只有空格
                if not pattern or pattern.strip() == '':
                    problematic_filters.append({
                        'id': f['id'],
                        'issue': "Pattern 为空，会匹配所有域名",
                        'severity': '严重'
                    })
                
                # 问题6: type是allow（代码中不支持）
                if filter_type == 'allow':
                    problematic_filters.append({
                        'id': f['id'],
                        'issue': "Type 是 'allow'，但当前代码不支持 allow 类型（只处理 block）",
                        'severity': '中'
                    })
            else:
                disabled_filters.append(f)
        
        # 显示诊断结果
        print_section("诊断结果")
        
        print(f"\n启用的规则: {len(enabled_filters)} 条")
        print(f"禁用的规则: {len(disabled_filters)} 条")
        
        if problematic_filters:
            print(f"\n⚠️  发现 {len(problematic_filters)} 个潜在问题：\n")
            
            for i, problem in enumerate(problematic_filters, 1):
                severity_icon = {
                    '严重': '🔴',
                    '高': '🟠',
                    '中': '🟡'
                }.get(problem['severity'], '⚪')
                
                print(f"{severity_icon} 问题 {i} (严重程度: {problem['severity']})")
                print(f"   规则ID: {problem['id']}")
                print(f"   问题: {problem['issue']}")
                print()
            
            print_section("建议")
            print("\n针对发现的问题，建议：")
            print("\n1. 检查 pattern 是否设置正确")
            print("   - Pattern 应该是完整的域名，如 'baidu.com' 而不是 'com'")
            print("   - 避免使用过短或过于通用的字符串")
            print("   - 内网IP过滤要谨慎，避免阻止所有内网访问")
            print("\n2. 如果要实现白名单功能（只允许特定域名）")
            print("   - 当前代码不支持 allow 类型")
            print("   - 需要修改 checkURLFilter 函数来实现白名单逻辑")
            print("\n3. 测试规则")
            print("   - 创建规则后，用测试脚本验证是否符合预期")
            print("   - 使用 test_url_filter_simple.py 测试")
            
        else:
            print("\n✓ 未发现明显问题")
            print("\n启用的规则看起来都是合理的。")
            print("如果仍然遇到访问问题，请检查：")
            print("  1. 网络连接是否正常")
            print("  2. 代理服务是否正常运行")
            print("  3. 客户端配置是否正确")
        
        # 显示当前生效的阻止规则
        if enabled_filters:
            print_section("当前生效的阻止规则")
            print("\n以下域名会被阻止访问：\n")
            for f in enabled_filters:
                if f['type'] == 'block':
                    print(f"  ✗ 包含 '{f['pattern']}' 的域名")
            print("\n其他所有域名都可以正常访问")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ 诊断失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("="*70)
    print("  URL过滤规则诊断工具")
    print("="*70)
    print("\n本工具将检查数据库中的URL过滤规则，")
    print("帮助您找出可能导致内网地址无法访问的问题。")
    
    diagnose_filters()
    
    print("\n" + "="*70)
    print("诊断完成")
    print("="*70 + "\n")


if __name__ == "__main__":
    sys.exit(main())

