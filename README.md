# 🚀 AlphaPilot AI - 合约智能交易终端

币安U本位永续合约 | AI多空双向评分 | 低价币扫描 | 遗传/贝叶斯优化 | 自适应学习 | 自动止盈止损 | 回测导出

## 🚀 Railway 部署

### 一键部署
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

### 手动部署步骤

1. **Fork 此项目** 到你的 GitHub 账户

2. **连接 Railway**
   - 访问 [Railway.app](https://railway.app)
   - 登录并连接你的 GitHub 账户
   - 选择此项目进行部署

3. **配置环境**（可选）
   - Railway 会自动检测 `railway.json` 和 `requirements.txt`
   - 如需自定义配置，可在 Railway 控制台设置环境变量

4. **部署完成**
   - Railway 会自动构建和部署应用
   - 获得分配的域名即可访问

## 🔧 本地开发

#### 环境准备
```bash
# 克隆项目
git clone https://github.com/你的用户名/AlphaPilot-Lite-Pro.git
cd AlphaPilot-Lite-Pro

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 运行应用
```bash
# 使用启动脚本（推荐）
./start.sh

# 或直接运行
streamlit run app.py
```

#### 故障排除
如果遇到网络问题导致依赖安装失败：
1. 使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
2. 或运行简化版本：`python3 simple_app.py`

## 📋 Railway 部署说明

- **构建器**: NIXPACKS (自动检测)
- **运行命令**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
- **依赖**: 自动从 `requirements.txt` 安装
- **端口**: 自动使用 Railway 分配的 `$PORT`

### 常见问题

**Q: 部署失败？**
A: 检查 Railway 构建日志，确保所有依赖都能正确安装。

**Q: 应用无法访问？**
A: 确认 Railway 分配的域名正确，等待几分钟让应用完全启动。

**Q: 内存不足？**
A: Railway 免费计划有内存限制，考虑升级到付费计划。

## 功能特性

- 🤖 **AI自动交易**：基于实时信号自动开仓，支持多空双向
- 📊 **专业K线分析**：集成Plotly专业图表
- 🎯 **实时信号评分**：RSI+MACD+均线多因子评分
- 🧬 **深度优化引擎**：遗传算法+贝叶斯优化
- 📈 **模拟交易**：虚拟本金安全测试策略
- 📥 **回测导出**：CSV格式交易记录导出
