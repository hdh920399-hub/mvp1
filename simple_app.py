#!/usr/bin/env python3
"""
AlphaPilot AI - 简化版本
当依赖不完整时运行此版本
"""

import sys
import os

# 检查依赖
def check_dependencies():
    missing = []
    try:
        import streamlit as st
    except ImportError:
        missing.append("streamlit")
    try:
        import pandas as pd
    except ImportError:
        missing.append("pandas")
    try:
        import numpy as np
    except ImportError:
        missing.append("numpy")
    try:
        import requests
    except ImportError:
        missing.append("requests")

    if missing:
        print(f"缺少依赖包: {', '.join(missing)}")
        print("正在运行简化版本...")

        # 运行简化版本
        run_simplified_version()
        return False
    return True

def run_simplified_version():
    print("🚀 AlphaPilot AI - 简化版本")
    print("=" * 50)
    print("此版本提供基本功能，不需要完整依赖")
    print()
    print("可用功能:")
    print("1. 查看项目结构")
    print("2. 检查依赖状态")
    print("3. 运行基本测试")
    print("4. 查看帮助文档")
    print()

    while True:
        choice = input("请选择功能 (1-4，q退出): ").strip()
        if choice == '1':
            show_project_structure()
        elif choice == '2':
            check_dependency_status()
        elif choice == '3':
            run_basic_tests()
        elif choice == '4':
            show_help()
        elif choice.lower() == 'q':
            break
        else:
            print("无效选择，请重新输入")

def show_project_structure():
    print("\n📁 项目结构:")
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if not file.startswith('.') and file.endswith(('.py', '.md', '.txt', '.sh')):
                print(f"{subindent}{file}")
    print()

def check_dependency_status():
    print("\n📦 依赖状态检查:")
    deps = ['streamlit', 'pandas', 'numpy', 'plotly', 'requests', 'scikit-optimize']
    for dep in deps:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
    print()

def run_basic_tests():
    print("\n🧪 基本测试:")
    try:
        import requests
        print("✅ HTTP请求测试...")
        # 测试币安API连接
        response = requests.get("https://api.binance.com/api/v3/ping", timeout=5)
        if response.status_code == 200:
            print("✅ 币安API连接正常")
        else:
            print("❌ 币安API连接失败")
    except ImportError:
        print("❌ 无法测试网络连接（缺少requests）")
    except Exception as e:
        print(f"❌ 网络测试失败: {e}")

    print("✅ Python版本:", sys.version)
    print()

def show_help():
    print("\n📖 帮助文档:")
    print("此项目是基于Streamlit的AI交易终端")
    print("主要功能包括:")
    print("- AI信号分析")
    print("- 自动交易")
    print("- 回测分析")
    print("- 策略优化")
    print()
    print("要运行完整版本，请安装所有依赖:")
    print("pip install -r requirements.txt")
    print()

if __name__ == "__main__":
    if check_dependencies():
        # 如果依赖完整，运行完整版本
        print("依赖完整，启动完整版本...")
        os.system("streamlit run app.py")
    else:
        # 依赖不完整，运行简化版本
        run_simplified_version()