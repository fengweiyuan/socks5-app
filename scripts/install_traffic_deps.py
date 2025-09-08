#!/usr/bin/env python3
"""
安装流量测试脚本所需的依赖包
"""

import subprocess
import sys

def install_package(package):
    """安装 Python 包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ 成功安装: {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ 安装失败: {package}")
        return False

def main():
    print("📦 安装流量测试脚本依赖包...")
    
    required_packages = [
        "requests",
        "PySocks",
    ]
    
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 安装结果: {success_count}/{len(required_packages)} 个包安装成功")
    
    if success_count == len(required_packages):
        print("🎉 所有依赖包安装完成！")
        print("\n使用方法:")
        print("1. 简单测试: python3 scripts/simple_traffic_test.py")
        print("2. 完整功能: python3 scripts/traffic_generator.py --help")
    else:
        print("⚠️  部分依赖包安装失败，请手动安装:")
        for package in required_packages:
            print(f"   pip install {package}")

if __name__ == '__main__':
    main()
