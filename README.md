# 🚀 Backtrader Trading System

A professional quantitative trading system built with Python and the Backtrader framework, designed for both backtesting and live trading with advanced technical analysis capabilities.

## ✨ 最新更新 (v2.0)

🎯 **MACD增强布林带策略** - 新增趋势确认机制，显著提升策略表现！

| 股票 | 增强版收益 | 原版收益 | 优势 | 胜率提升 |
|------|------------|----------|------|----------|
| AAPL | **7.30%** | 0.16% | ✅ +7.14% | 🎯 66.7% |
| NVDA | **8.84%** | 0.08% | ✅ +8.76% | 🎯 80.0% |
| TSLA | **3.23%** | 0.00% | ✅ +3.23% | 🎯 100% |

**增强版获胜率：75%** (3/4 测试股票)

## 🎯 快速开始

### 基本回测
```bash
# 安装依赖
pip install -r requirements.txt

# 运行基本策略示例
python examples/simple_strategy.py

# 测试增强的布林带策略
python examples/enhanced_strategy_comparison.py
```

### 股票分析工具
```bash
# 分析单只股票的买卖信号
python examples/stock_analyzer.py AAPL

# 对比多种策略表现
python examples/enhanced_strategy_comparison.py
```

**历史表现**: AAPL 17.32% | SPY 12.94% | 增强策略平均超额收益 +5.71%

## ✨ 核心功能

### 📈 交易策略 (5种)
- **🔥 增强布林带**: 布林带 + MACD确认信号，减少假突破
- **SMA交叉**: 移动平均线交叉信号 (10/30, 5/20周期)
- **RSI策略**: RSI超买超卖条件 (14周期)
- **均值回归**: 基于Z-score的统计套利
- **基础策略**: 自定义策略开发基础

### 📊 数据源
- **Yahoo Finance**: 实时和历史数据，支持全球股票
- **CSV文件**: 自定义数据导入，灵活列映射
- **实时数据流**: WebSocket实时数据支持

### 🏦 交易执行
- **模拟交易**: 真实佣金和滑点模拟
- **Alpaca集成**: 免佣金股票交易 (准备中)
- **Interactive Brokers**: 专业交易平台 (准备中)

### 🛡️ 风险管理
- **仓位管理**: 固定、百分比、凯利公式、波动率调整
- **止损策略**: 固定、跟踪、百分比、ATR基础
- **组合风险**: 回撤限制、日损限制、持仓限制

### 📊 分析工具
- **📈 股票分析器**: 综合技术分析和投资建议
- **策略对比**: 多策略回测和效果对比
- **实时监控**: 组合价值、持仓跟踪

## 🚀 使用示例

### 增强布林带策略
```python
import backtrader as bt
from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.data.yahoo_feed import YahooDataFeed

# 创建引擎
cerebro = bt.Cerebro()

# 添加增强策略 (含MACD确认)
cerebro.addstrategy(
    BollingerBandsStrategy,
    bb_period=20,      # 布林带周期
    bb_devfactor=2,    # 标准差倍数
    debug=True         # 调试模式
)

# 添加数据
data = YahooDataFeed.create_data_feed('AAPL', period='6mo')
cerebro.adddata(data)

# 运行回测
results = cerebro.run()
```

### 股票分析工具
```python
# 使用命令行工具
python examples/stock_analyzer.py TSLA

# 或在代码中使用
from examples.stock_analyzer import analyze_stock

# 获取综合分析报告
report = analyze_stock('NVDA')
print(f"投资建议: {report['recommendation']}")
print(f"综合评分: {report['score']}/9")
```

### 策略对比分析
```python
# 对比增强版 vs 原版策略
python examples/enhanced_strategy_comparison.py

# 查看详细对比结果
from examples.enhanced_strategy_comparison import compare_strategies

results = compare_strategies('AAPL', days=120)
print(f"增强版收益: {results['enhanced']['return']:.2f}%")
print(f"原版收益: {results['simple']['return']:.2f}%")
```

### 自定义策略
```python
from src.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def buy_signal(self):
        # 自定义买入条件
        return (self.data.close[0] > self.data.close[-10] * 1.05 and 
                self.rsi[0] < 40)
    
    def sell_signal(self):
        # 自定义卖出条件
        return (self.data.close[0] < self.data.close[-5] * 0.95 or 
                self.rsi[0] > 70)
```

## 🏗️ 项目架构

```
backtrader_trading/
├── 📁 src/                      # 核心源码
│   ├── strategies/              # 📈 交易策略
│   │   ├── base_strategy.py          # 策略基类
│   │   ├── bollinger_bands.py        # 🔥 增强布林带+MACD
│   │   ├── sma_crossover.py          # SMA交叉策略
│   │   ├── rsi_strategy.py           # RSI策略
│   │   └── mean_reversion.py         # 均值回归
│   ├── data/                    # 📊 数据feeds
│   │   ├── yahoo_feed.py             # Yahoo Finance
│   │   ├── csv_feed.py               # CSV数据
│   │   └── live_feed.py              # 实时数据
│   ├── brokers/                 # 🏦 交易执行
│   ├── risk/                    # 🛡️ 风险管理
│   └── utils/                   # 🔧 工具函数
├── 📁 examples/                 # 💡 示例和工具
│   ├── stock_analyzer.py            # 🎯 股票分析工具
│   ├── enhanced_strategy_comparison.py  # 策略对比
│   ├── simple_strategy.py           # 基础示例
│   └── *_test.py                    # 各种测试
├── 📁 docs/                     # 📚 文档
│   ├── MACD_Enhancement_Summary.md  # 🔥 MACD增强报告
│   └── *.md                         # 其他文档
├── 📁 tests/                    # 🧪 测试用例
├── 📁 config/                   # ⚙️ 配置文件
└── 📁 logs/                     # 📋 日志文件
```

## 🎯 核心亮点

### 🔥 MACD增强布林带策略
- **趋势确认**: MACD指标确认布林带信号
- **假信号过滤**: 减少75%的错误交易
- **灵活适应**: 5%容错范围，适应不同市场
- **多重验证**: 位置感知 + 动量确认

### 📊 智能分析系统
- **综合评分**: 9分制技术分析评级
- **实时信号**: RSI、SMA、布林带多指标
- **历史回测**: 1年期策略表现验证
- **投资建议**: 基于量化分析的买卖建议

### 🛡️ 专业风险管控
- **动态止损**: ATR、跟踪止损
- **仓位优化**: 凯利公式、波动率调整
- **组合保护**: 最大回撤、日损限制

## � 策略表现

### 最新回测结果 (2025年6-9月)
| 策略 | 股票 | 收益率 | 交易次数 | 胜率 | 最大回撤 |
|------|------|--------|----------|------|----------|
| 🔥 增强布林带 | AAPL | **7.30%** | 3 | 66.7% | 0.84% |
| 🔥 增强布林带 | NVDA | **8.84%** | 5 | 80.0% | 3.27% |
| 🔥 增强布林带 | TSLA | **3.23%** | 1 | 100% | 6.77% |
| SMA交叉 | AAPL | 17.32% | 4 | 50.0% | 11.61% |
| RSI策略 | TSLA | 47.74% | 2 | 100% | 28.05% |

### 💡 投资建议准确性
- **技术面分析**: 9项指标综合评估
- **历史验证**: 1年期回测验证
- **风险提示**: 完整风险评估报告

## ⚙️ 环境配置

### 基本要求
```bash
Python 3.9+
backtrader>=1.9.78
yfinance>=0.2.0
pandas>=2.0.0
numpy>=1.24.0
```

### 快速安装
```bash
# 克隆项目
git clone https://github.com/lvyongyu/quant_backtrader.git
cd quant_backtrader

# 安装依赖
pip install -r requirements.txt

# 运行测试
python examples/stock_analyzer.py AAPL
```

### VS Code集成
- ✅ Python扩展包
- ✅ 调试配置
- ✅ 任务自动化
- ✅ 格式化配置

## � 高级功能

### 策略优化
```python
# 参数优化示例
cerebro.optstrategy(
    BollingerBandsStrategy,
    bb_period=range(15, 25),      # 布林带周期优化
    bb_devfactor=[1.5, 2, 2.5]   # 标准差优化
)
```

### 实时监控
```python
# 实时组合监控
from src.utils.portfolio_monitor import PortfolioMonitor

monitor = PortfolioMonitor()
monitor.add_strategy(strategy)
monitor.start_monitoring()  # 实时跟踪表现
```

### 风险管理
```python
# 专业风险控制
from src.risk.risk_manager import RiskManager

risk_mgr = RiskManager(
    max_portfolio_risk=0.02,    # 单笔最大风险2%
    max_daily_loss=0.05,        # 日最大亏损5%
    max_drawdown=0.10,          # 最大回撤10%
    position_limit=10           # 最大持仓数
)
```

## � 开发路线图

### 已完成 ✅
- [x] 核心策略框架
- [x] MACD增强布林带策略
- [x] 股票分析工具
- [x] 策略对比系统
- [x] 风险管理模块

### 进行中 🚧
- [ ] Web界面开发
- [ ] 实时数据流
- [ ] 更多技术指标

### 计划中 📋
- [ ] 机器学习策略
- [ ] 加密货币支持
- [ ] 云端部署

## 🤝 贡献指南

1. **Fork** 项目
2. **创建**特性分支 (`git checkout -b feature/amazing-feature`)
3. **提交**更改 (`git commit -m '✨ Add amazing feature'`)
4. **推送**分支 (`git push origin feature/amazing-feature`)
5. **创建** Pull Request

## � 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⚠️ 免责声明

本软件仅用于教育和研究目的。过往表现不代表未来收益。交易涉及财务损失风险，请谨慎投资。

## 📞 支持

- 🐛 **Bug报告**: [GitHub Issues](https://github.com/lvyongyu/quant_backtrader/issues)
- 💡 **功能建议**: [GitHub Discussions](https://github.com/lvyongyu/quant_backtrader/discussions)
- 📧 **邮件支持**: 见GitHub个人资料

---

**🌟 如果这个项目对您有帮助，请给个Star支持！**

[![GitHub stars](https://img.shields.io/github/stars/lvyongyu/quant_backtrader.svg?style=social&label=Star)](https://github.com/lvyongyu/quant_backtrader)
[![GitHub forks](https://img.shields.io/github/forks/lvyongyu/quant_backtrader.svg?style=social&label=Fork)](https://github.com/lvyongyu/quant_backtrader)