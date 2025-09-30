# 智能股票分析系统 v3.0

基于Python的专业股票分析系统，提供四维度智能分析和投资决策支持。

## 🎯 核心功能

### 🔍 1. 选股筛选
- **四维度分析**: 技术面(40%) + 基本面(25%) + 市场环境(20%) + 情绪资金面(15%)
- **多市场支持**: SP500、NASDAQ100、中概股
- **智能评分**: 100分制综合评分系统
- **自动保存**: TOP5股票自动加入自选股池

### 📋 2. 自选股池管理
- **CRUD操作**: 增删改查自选股票
- **批量分析**: 一键分析所有自选股
- **历史跟踪**: 股价变化和评分记录
- **JSON存储**: 持久化数据管理

### 📈 3. 单只股票分析
- **深度解析**: 全面的技术面和基本面分析
- **实时数据**: 最新价格和财务指标
- **投资建议**: 基于综合评分的买卖建议
- **风险评估**: 详细的风险提示和注意事项

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 统一入口使用

#### 🔍 选股筛选
```bash
# 筛选SP500前5只股票
python main.py screen sp500 5

# 筛选NASDAQ100前10只股票  
python main.py screen nasdaq100 10

# 筛选中概股前3只
python main.py screen chinese 3
```

#### 📋 自选股管理
```bash
# 查看自选股池
python main.py watchlist show

# 分析自选股池所有股票
python main.py watchlist analyze

# 添加股票到自选股池
python main.py watchlist add AAPL

# 从自选股池移除股票
python main.py watchlist remove AAPL

# 清空自选股池
python main.py watchlist clear
```

#### 📈 单只股票分析
```bash
# 分析苹果股票
python main.py analyze AAPL

# 分析特斯拉股票
python main.py analyze TSLA

# 分析HWM股票
python main.py analyze HWM
```

### 查看帮助
```bash
python main.py --help
python main.py
```

## 📊 分析结果示例

### 四维度综合评分
```
🏆 HWM 四维度综合得分: 72.30/100
📊 构成: 技术89.5(40%) + 基本面50.0(25%) + 市场75.0(20%) + 情绪60.0(15%)
📈 投资建议: 🟡 谨慎乐观 - 可适量配置
```

### 技术指标详情
```
🔧 技术分析 (权重40%):
   总分: 89.5/100
   趋势得分: 100.0/100  (价格突破所有均线)
   动量得分: 100.0/100  (MACD多头，RSI适中)
   波动得分: 50.0/100   (波动率偏高)
   成交量得分: 80.0/100 (成交活跃)
```

### 投资建议
```
🎯 投资分析:
   🟢 技术面偏多 - 价格>20日均线，MACD多头
   ⚠️  估值偏高 - P/E 60+，注意回调风险
   📈 行业地位 - 航空材料龙头，技术护城河深厚
```

## 🛠️ 系统架构

```
backtrader_trading/
├── main.py                 # 统一入口脚本
├── examples/
│   └── stock_screener.py   # 选股筛选器
├── watchlist_tool.py       # 自选股管理工具
├── analyze_hwm_only.py     # 单股分析模板
├── src/
│   └── analyzers/          # 分析器模块
│       ├── fundamental_analyzer.py      # 基本面分析
│       ├── market_environment.py       # 市场环境分析
│       └── sentiment_fund_analyzer.py  # 情绪资金面分析
└── data/
    └── watchlist.json      # 自选股数据存储
```

## 🎯 分析维度详解

### 🔧 技术分析 (40% 权重)
- **趋势分析**: 多周期均线系统
- **动量指标**: RSI、MACD、KDJ
- **成交量**: 量价配合分析
- **形态识别**: 支撑阻力位判断

### 📊 基本面分析 (25% 权重)
- **估值指标**: P/E、P/B、PEG
- **财务健康**: ROE、ROA、负债率
- **盈利能力**: 毛利率、净利率
- **成长性**: 营收增长、利润增长

### 🌍 市场环境分析 (20% 权重)
- **Beta匹配**: 根据市场环境匹配股票风险
- **宏观环境**: VIX恐慌指数、市场情绪
- **行业轮动**: 板块强弱和资金流向

### 🎭 情绪资金面分析 (15% 权重)
- **资金流向**: MFI资金流量指标
- **买卖强度**: 主动买卖盘分析
- **相对表现**: 个股vs大盘表现对比

## 📈 使用场景

### 1. 日常选股
```bash
# 每日筛选优质股票
python main.py screen sp500 10
```

### 2. 投资组合管理
```bash
# 管理个人股票池
python main.py watchlist analyze
python main.py watchlist add NVDA
```

### 3. 深度研究
```bash
# 详细分析目标股票
python main.py analyze AAPL
```

## ⚡ 性能特点

- **高效筛选**: 500只股票15-20分钟完成
- **智能限流**: API调用自动重试和限频
- **成功率高**: 95%+ 分析成功率
- **内存优化**: 支持大规模股票分析

## 🎨 自定义配置

### 修改评分权重
编辑 `src/analyzers/` 中的分析器文件，调整各维度权重

### 添加新股票池
在 `stock_screener.py` 中添加新的股票列表

### 自定义技术指标
扩展技术分析函数，添加新的指标计算

## 🚨 免责声明

本系统仅供学习和研究使用，不构成投资建议。股市有风险，投资需谨慎。使用本系统进行投资决策的风险由用户自行承担。

## 📞 技术支持

如有问题请查看代码注释或在GitHub创建Issue。

---

**🎯 祝您投资顺利！ 📈**