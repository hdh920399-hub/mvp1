#!/bin/bash
# AlphaPilot AI 启动脚本

echo "激活虚拟环境..."
source venv/bin/activate

echo "检查依赖..."
python -c "
import sys
missing = []
try:
    import streamlit
except ImportError:
    missing.append('streamlit')
try:
    import pandas
except ImportError:
    missing.append('pandas')
try:
    import numpy
except ImportError:
    missing.append('numpy')
try:
    import plotly
except ImportError:
    missing.append('plotly')
try:
    import requests
except ImportError:
    missing.append('requests')
try:
    import skopt
except ImportError:
    missing.append('scikit-optimize')

if missing:
    print(f'缺少依赖: {missing}')
    print('请运行: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('所有依赖已安装 ✓')
"

if [ $? -eq 0 ]; then
    echo "启动 AlphaPilot AI..."
    streamlit run app.py --server.port 8501 --server.address 0.0.0.0
else
    echo "依赖检查失败，请安装缺失的包"
fi