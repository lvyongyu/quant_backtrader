# 📈 量化交易系统 - 快速开始指南

让量化交易变得像使用计算器一样简单！🎯

## 🚀 5分钟快速开始

### 1. 基本使用（Python）

```python
# 导入简化接口
from core.quick_trade import *

# 📊 获取数据
data = get_stock_data('AAPL', '2023-01-01', '2023-12-31')
print(f"获取了{len(data)}天的AAPL数据")

# 🔧 创建策略
strategy = create_simple_strategy('RSI', {'period': 14, 'oversold': 30})

# 📈 运行回测（一行代码！）
result = backtest('RSI', 'AAPL')
print(result.summary())

# 💰 启动模拟交易
trader = start_trading('RSI', 'AAPL')
print(get_trading_status(trader))
```

### 2. 命令行使用

```bash
# 获取股票数据
python core/simple_cli.py data AAPL

# 快速分析
python core/simple_cli.py analyze AAPL

# 运行回测
python core/simple_cli.py backtest run RSI AAPL

# 启动模拟交易
python core/simple_cli.py trade start RSI AAPL

# 查看系统状态
python core/simple_cli.py system status
```

## 🎯 核心功能

### 📊 数据获取
```python
# 获取股票数据
data = get_stock_data('AAPL')                    # 默认1年数据
data = get_stock_data('AAPL', '2023-01-01')     # 指定开始日期
data = get_stock_data('AAPL', '2023-01-01', '2023-12-31')  # 指定范围

# 获取实时价格
price = get_price('AAPL')
print(f"AAPL当前价格：${price:.2f}")

# 获取股票信息
info = get_info('AAPL')
print(f"公司名称：{info.get('name', 'N/A')}")
```

### 🔧 策略创建
```python
# 可用策略
strategies = list_strategies()
print("可用策略：", strategies)  # ['MA_Cross', 'RSI', 'MACD', 'BollingerBands']

# 创建策略
ma_strategy = create_simple_strategy('MA_Cross', {'fast': 5, 'slow': 20})
rsi_strategy = create_simple_strategy('RSI', {'period': 14})
macd_strategy = create_simple_strategy('MACD')
bb_strategy = create_simple_strategy('BollingerBands', {'window': 20})

# 测试策略信号
signal = test_strategy('RSI', 'AAPL')
print(f"信号：{signal.signal.value}，置信度：{signal.confidence:.2f}")
```

### 📈 回测分析
```python
# 一行代码完成回测
result = backtest('RSI', 'AAPL')
print(result.summary())

# 自定义参数
result = backtest(
    strategy_name='MA_Cross',
    symbol='AAPL', 
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_capital=50000,
    strategy_params={'fast': 10, 'slow': 30}
)

# 比较多个策略
results = compare_strategies(['MA_Cross', 'RSI', 'MACD'], 'AAPL')
for name, result in results.items():
    print(f"{name}: {result.total_return_percent:.2f}%")

# 保存回测结果
save_path = save_backtest(result)
```

### 💰 模拟交易
```python
# 启动单股票交易
trader = start_trading('RSI', 'AAPL')

# 启动多股票交易
trader = start_trading('MA_Cross', ['AAPL', 'MSFT', 'GOOGL'], 100000)

# 查看交易状态
status = get_trading_status(trader)
print(status)

# 停止交易并保存结果
save_path = stop_trading(trader, save_results=True)
```

## 🛠️ 策略参数配置

### 移动平均交叉 (MA_Cross)
```python
strategy = create_simple_strategy('MA_Cross', {
    'fast': 5,    # 快线周期
    'slow': 20    # 慢线周期
})
```

### RSI策略
```python
strategy = create_simple_strategy('RSI', {
    'period': 14,        # RSI周期
    'oversold': 30,      # 超卖阈值
    'overbought': 70     # 超买阈值
})
```

### MACD策略
```python
strategy = create_simple_strategy('MACD', {
    'fast': 12,           # 快线周期
    'slow': 26,           # 慢线周期
    'signal_period': 9    # 信号线周期
})
```

### 布林带策略
```python
strategy = create_simple_strategy('BollingerBands', {
    'window': 20,     # 移动平均窗口
    'std_dev': 2      # 标准差倍数
})
```

## 📋 完整示例

### 示例1：快速回测
```python
from core.quick_trade import *

# 回测Apple股票使用RSI策略
result = backtest('RSI', 'AAPL', '2023-01-01', '2023-12-31')
print("📊 回测结果：")
print(result.summary())
print(f"💰 总收益：{result.total_return_percent:.2f}%")
print(f"📊 胜率：{result.win_rate:.1f}%")
print(f"📉 最大回撤：{result.max_drawdown:.2f}%")
```

### 示例2：策略比较
```python
from core.quick_trade import *

# 比较不同策略在AAPL上的表现
strategies = ['MA_Cross', 'RSI', 'MACD', 'BollingerBands']
results = compare_strategies(strategies, 'AAPL', '2023-01-01', '2023-12-31')

print("📊 策略比较结果：")
print("-" * 50)
for name, result in results.items():
    print(f"{name:15} | 收益: {result.total_return_percent:6.2f}% | "
          f"胜率: {result.win_rate:5.1f}% | 夏普: {result.sharpe_ratio:5.2f}")
```

### 示例3：实时分析
```python
from core.quick_trade import *

# 对多只股票进行快速分析
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

for symbol in symbols:
    print(f"\n{'='*20} {symbol} {'='*20}")
    
    # 快速分析
    analysis = quick_analysis(symbol, 30)
    print(analysis)
    
    # 获取多个策略信号
    for strategy_name in ['RSI', 'MA_Cross']:
        signal = test_strategy(strategy_name, symbol)
        print(f"🔧 {strategy_name}: {signal.signal.value} (置信度: {signal.confidence:.2f})")
```

### 示例4：自动交易系统
```python
from core.quick_trade import *
import time

# 创建自动交易系统
def auto_trading_system():
    # 股票池
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # 启动多个交易器
    traders = {}
    for symbol in symbols:
        trader = start_trading('RSI', symbol, initial_capital=50000)
        traders[symbol] = trader
        print(f"✅ {symbol} 交易已启动")
    
    # 监控交易状态
    try:
        while True:
            print("\n" + "="*50)
            print(f"📊 交易监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            for symbol, trader in traders.items():
                status = get_trading_status(trader)
                print(f"\n{symbol}:")
                print(status)
            
            time.sleep(300)  # 每5分钟检查一次
            
    except KeyboardInterrupt:
        print("\n🛑 停止所有交易...")
        for symbol, trader in traders.items():
            stop_trading(trader, save_results=True)
            print(f"✅ {symbol} 交易已停止")

# 运行自动交易系统
# auto_trading_system()
```

## 🔧 命令行工具

### 数据命令
```bash
# 获取股票数据
python core/simple_cli.py data AAPL
python core/simple_cli.py data AAPL --start 2023-01-01 --end 2023-12-31
python core/simple_cli.py data AAPL --save  # 保存到CSV

# 获取实时价格
python core/simple_cli.py data price AAPL

# 获取股票信息
python core/simple_cli.py data info AAPL
```

### 策略命令
```bash
# 列出可用策略
python core/simple_cli.py strategy list

# 测试策略信号
python core/simple_cli.py strategy test RSI AAPL
python core/simple_cli.py strategy test MA_Cross AAPL --params '{"fast":5,"slow":20}'
```

### 回测命令
```bash
# 运行回测
python core/simple_cli.py backtest run RSI AAPL
python core/simple_cli.py backtest run MA_Cross AAPL --start 2023-01-01 --capital 50000

# 比较策略
python core/simple_cli.py backtest compare "MA_Cross,RSI,MACD" AAPL

# 保存回测结果
python core/simple_cli.py backtest run RSI AAPL --save
```

### 交易命令
```bash
# 启动模拟交易
python core/simple_cli.py trade start RSI AAPL
python core/simple_cli.py trade start MA_Cross "AAPL,MSFT" --capital 100000

# 查看交易列表
python core/simple_cli.py trade list
```

### 分析命令
```bash
# 快速分析
python core/simple_cli.py analyze AAPL
python core/simple_cli.py analyze AAPL --days 60
```

### 系统命令
```bash
# 查看系统状态
python core/simple_cli.py system status

# 运行演示
python core/simple_cli.py system demo

# 查看教程
python core/simple_cli.py system tutorial
```

## 🎓 学习路径

### 新手（5分钟上手）
1. 运行演示：`python core/simple_cli.py system demo`
2. 获取数据：`python core/simple_cli.py data AAPL`
3. 快速分析：`python core/simple_cli.py analyze AAPL`
4. 运行回测：`python core/simple_cli.py backtest run RSI AAPL`

### 进阶（30分钟掌握）
1. 学习所有策略：比较不同策略的效果
2. 自定义参数：调整策略参数优化表现
3. 多股票分析：分析不同股票的特点
4. 模拟交易：启动实时模拟交易

### 高级（1小时精通）
1. 策略组合：使用多策略组合
2. 风险管理：设置止损止盈
3. 批量分析：分析股票池
4. 自动化系统：构建自动交易系统

## ❓ 常见问题

### Q: 如何安装依赖？
```bash
pip install pandas numpy yfinance matplotlib
```

### Q: 如何修改策略参数？
```python
# 使用字典传递参数
strategy = create_simple_strategy('RSI', {
    'period': 21,        # 修改RSI周期为21
    'oversold': 25,      # 调整超卖线
    'overbought': 75     # 调整超买线
})
```

### Q: 如何添加自定义策略？
```python
# 在strategy_manager.py中添加新的策略函数
def my_custom_strategy(data, param1=10, param2=0.5):
    # 实现您的策略逻辑
    return StrategyResult(...)

# 然后可以这样使用
strategy = Strategy('MyStrategy', my_custom_strategy, {'param1': 15})
```

### Q: 回测结果保存在哪里？
回测结果保存在 `data/backtest_results/` 目录下，格式为JSON文件。

### Q: 如何查看详细的交易记录？
```python
result = backtest('RSI', 'AAPL')
for trade in result.trades:
    print(f"{trade.date}: {trade.action} {trade.shares} @${trade.price:.2f}")
```

## 🚀 下一步

1. **查看完整文档**：`docs/USER_GUIDE_COMPLETE.md`
2. **学习高级功能**：`docs/HIGH_FREQUENCY_TRADING_GUIDE.md`
3. **API参考**：`docs/API_REFERENCE.md`
4. **示例代码**：`examples/` 目录

---

**让量化交易变得简单易用！** 🎯

如有问题，请查看 `python core/simple_cli.py system tutorial` 或运行 `python core/simple_cli.py system demo` 进行演示。