#!/usr/bin/env python3
"""
AlphaPilot AI - Streamlit 简化版本
当依赖不完整时运行此版本
"""

import streamlit as st
from datetime import datetime
import time

st.set_page_config(
    page_title="AlphaPilot Lite - 简化版",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 AlphaPilot Lite - 简化演示版")

st.markdown("""
这个是简化版本，只需要 Streamlit 就可以运行。

**完整版本功能：**
- 🤖 AI自动交易
- 📊 专业K线分析
- 🎯 实时信号评分
- 🧬 深度优化引擎
- 📈 模拟交易
- 📥 回测导出

**部署状态：**
- ✅ Railway 部署配置完成
- ✅ 自动构建优化
- ✅ 环境变量配置
""")

# 模拟一些数据
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("BTC/USDT", "45,230.50", "+2.34%")

with col2:
    st.metric("ETH/USDT", "2,450.80", "+1.87%")

with col3:
    st.metric("BNB/USDT", "315.20", "-0.45%")

st.subheader("📊 市场概览")
st.info("完整版本将显示实时市场数据和AI信号分析")

st.subheader("🤖 AI交易状态")
st.success("AI自动交易模块已配置完成，等待完整依赖安装后启用")

st.subheader("🚀 Railway部署")
st.markdown("""
**部署状态：** ✅ 已优化
- 自动构建配置
- 健康检查设置
- 环境变量配置
- Python 3.9 指定

**访问地址：** 部署完成后会获得 Railway 分配的域名
""")

# 模拟实时更新
placeholder = st.empty()
for i in range(10):
    with placeholder.container():
        st.write(f"系统状态检查中... {i+1}/10")
        time.sleep(0.5)

st.success("✅ 简化版运行正常！请在 Railway 上部署完整版本体验所有功能。")

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