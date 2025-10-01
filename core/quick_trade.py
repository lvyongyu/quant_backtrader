"""
量化交易系统简化接口 - QuickTrade

让量化交易变得像使用计算器一样简单！

核心功能：
- 数据：get_data() - 获取股票数据
- 策略：create_strategy() - 创建交易策略  
- 回测：backtest() - 一行代码完成回测
- 交易：start_trading() - 启动模拟交易

示例用法：
```python
# 3行代码完成回测
data = get_data('AAPL', '2023-01-01', '2023-12-31')
strategy = create_strategy('MA_Cross', {'fast': 5, 'slow': 20})
result = backtest(strategy, 'AAPL')
print(result.summary())

# 1行代码启动交易
trader = start_trading('RSI', ['AAPL', 'MSFT'])
```
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging

# 添加core模块到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入核心模块
try:
    from data_manager import DataManager, get_data, get_realtime_price, get_stock_info
    from strategy_manager import (Strategy, create_strategy, get_available_strategies, 
                                SignalType, StrategyResult)
    from backtest_manager import (SimpleBacktester, BacktestResult, quick_backtest, 
                                save_result as save_backtest_result)
    from paper_trader import (PaperTrader, PaperPosition, PaperTrade, TradingAccount,
                             start_paper_trading)
    
    logger.info("✅ 核心模块导入成功")
    CLI_AVAILABLE = True
    
except ImportError as e:
    logger.error(f"❌ 核心模块导入失败：{e}")
    logger.info("请确保所有依赖包已安装：pip install pandas numpy")
    CLI_AVAILABLE = False
    
    # 定义空的类型来避免NameError
    class Strategy: pass
    class StrategyResult: pass  
    class SignalType: pass
    class BacktestResult: pass
    class PaperTrader: pass

# ==================== 数据相关 ====================

def get_stock_data(symbol: str, 
                  start_date: str = None, 
                  end_date: str = None,
                  period: str = '1d'):
    """
    获取股票数据 - 简化版
    
    Args:
        symbol: 股票代码，如 'AAPL', 'TSLA'
        start_date: 开始日期，如 '2023-01-01'
        end_date: 结束日期，如 '2023-12-31'
        period: 数据周期，'1d'=日线, '1h'=小时线
        
    Returns:
        股票数据DataFrame，包含OHLCV
        
    Examples:
        >>> data = get_stock_data('AAPL', '2023-01-01', '2023-12-31')
        >>> print(f"获取了{len(data)}天的数据")
    """
    try:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        return get_data(symbol, start_date, end_date, period)
    except Exception as e:
        logger.error(f"获取股票数据失败：{e}")
        raise

def get_price(symbol: str) -> float:
    """
    获取实时股价
    
    Args:
        symbol: 股票代码
        
    Returns:
        当前股价
        
    Examples:
        >>> price = get_price('AAPL')
        >>> print(f"AAPL当前价格：${price:.2f}")
    """
    try:
        return get_realtime_price(symbol)
    except Exception as e:
        logger.error(f"获取实时价格失败：{e}")
        return 0.0

def get_info(symbol: str) -> Dict:
    """
    获取股票基本信息
    
    Args:
        symbol: 股票代码
        
    Returns:
        股票信息字典
        
    Examples:
        >>> info = get_info('AAPL')
        >>> print(f"公司名称：{info.get('name', 'N/A')}")
    """
    try:
        return get_stock_info(symbol)
    except Exception as e:
        logger.error(f"获取股票信息失败：{e}")
        return {}

# ==================== 策略相关 ====================

def create_simple_strategy(name: str, params: Dict = None) -> Strategy:
    """
    创建简单策略
    
    Args:
        name: 策略名称，可选：'MA_Cross', 'RSI', 'MACD', 'BollingerBands'
        params: 策略参数
        
    Returns:
        策略对象
        
    Examples:
        >>> strategy = create_simple_strategy('MA_Cross', {'fast': 5, 'slow': 20})
        >>> print(f"策略：{strategy.name}")
    """
    try:
        return create_strategy(name, params)
    except Exception as e:
        logger.error(f"创建策略失败：{e}")
        raise

def list_strategies() -> List[str]:
    """
    列出可用策略
    
    Returns:
        策略名称列表
        
    Examples:
        >>> strategies = list_strategies()
        >>> print("可用策略：", strategies)
    """
    try:
        return get_available_strategies()
    except Exception as e:
        logger.error(f"获取策略列表失败：{e}")
        return []

def test_strategy(strategy_name: str, symbol: str, params: Dict = None) -> StrategyResult:
    """
    快速测试策略信号
    
    Args:
        strategy_name: 策略名称
        symbol: 股票代码
        params: 策略参数
        
    Returns:
        策略结果
        
    Examples:
        >>> result = test_strategy('RSI', 'AAPL')
        >>> print(f"信号：{result.signal.value}, 置信度：{result.confidence:.2f}")
    """
    try:
        # 获取最近数据
        data = get_stock_data(symbol, period='1d')
        strategy = create_simple_strategy(strategy_name, params)
        return strategy.generate_signal(data)
    except Exception as e:
        logger.error(f"测试策略失败：{e}")
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=0.0,
            reason=f"测试失败：{e}",
            indicators={}
        )

# ==================== 回测相关 ====================

def backtest(strategy_name: str, 
            symbol: str,
            start_date: str = None,
            end_date: str = None,
            initial_capital: float = 100000,
            strategy_params: Dict = None) -> BacktestResult:
    """
    一行代码完成回测
    
    Args:
        strategy_name: 策略名称
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
        strategy_params: 策略参数
        
    Returns:
        回测结果
        
    Examples:
        >>> result = backtest('MA_Cross', 'AAPL')
        >>> print(result.summary())
        >>> print(f"总收益：{result.total_return_percent:.2f}%")
    """
    try:
        return quick_backtest(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            strategy_params=strategy_params,
            initial_capital=initial_capital
        )
    except Exception as e:
        logger.error(f"回测失败：{e}")
        raise

def compare_strategies(strategies: List[str], 
                      symbol: str,
                      start_date: str = None,
                      end_date: str = None) -> Dict[str, BacktestResult]:
    """
    比较多个策略的回测结果
    
    Args:
        strategies: 策略名称列表
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        策略回测结果字典
        
    Examples:
        >>> results = compare_strategies(['MA_Cross', 'RSI'], 'AAPL')
        >>> for name, result in results.items():
        >>>     print(f"{name}: {result.total_return_percent:.2f}%")
    """
    results = {}
    
    for strategy_name in strategies:
        try:
            result = backtest(strategy_name, symbol, start_date, end_date)
            results[strategy_name] = result
            logger.info(f"✅ {strategy_name}: {result.total_return_percent:.2f}%")
        except Exception as e:
            logger.error(f"❌ {strategy_name}: {e}")
    
    return results

def save_backtest(result: BacktestResult, filename: str = None) -> str:
    """
    保存回测结果
    
    Args:
        result: 回测结果
        filename: 文件名
        
    Returns:
        保存的文件路径
        
    Examples:
        >>> result = backtest('MA_Cross', 'AAPL')
        >>> path = save_backtest(result)
        >>> print(f"结果保存到：{path}")
    """
    try:
        return save_backtest_result(result, filename)
    except Exception as e:
        logger.error(f"保存回测结果失败：{e}")
        raise

# ==================== 模拟交易相关 ====================

def start_trading(strategy_name: str,
                 symbols: Union[str, List[str]],
                 initial_capital: float = 100000,
                 strategy_params: Dict = None,
                 update_interval: int = 300) -> PaperTrader:
    """
    启动模拟交易 - 一行代码开始交易
    
    Args:
        strategy_name: 策略名称
        symbols: 股票代码（单个或列表）
        initial_capital: 初始资金
        strategy_params: 策略参数
        update_interval: 更新间隔（秒）
        
    Returns:
        模拟交易器对象
        
    Examples:
        >>> trader = start_trading('RSI', 'AAPL')
        >>> print(trader.get_performance_summary())
        
        >>> trader = start_trading('MA_Cross', ['AAPL', 'MSFT'], 50000)
        >>> # 运行一段时间后...
        >>> trader.stop_trading()
    """
    try:
        if isinstance(symbols, str):
            symbols = [symbols]
        
        return start_paper_trading(
            strategy_name=strategy_name,
            symbols=symbols,
            strategy_params=strategy_params,
            initial_capital=initial_capital,
            update_interval=update_interval
        )
    except Exception as e:
        logger.error(f"启动模拟交易失败：{e}")
        raise

def get_trading_status(trader: PaperTrader) -> str:
    """
    获取交易状态摘要
    
    Args:
        trader: 交易器对象
        
    Returns:
        状态摘要字符串
        
    Examples:
        >>> trader = start_trading('RSI', 'AAPL')
        >>> status = get_trading_status(trader)
        >>> print(status)
    """
    try:
        return trader.get_performance_summary()
    except Exception as e:
        logger.error(f"获取交易状态失败：{e}")
        return f"获取状态失败：{e}"

def stop_trading(trader: PaperTrader, save_results: bool = True) -> Optional[str]:
    """
    停止模拟交易
    
    Args:
        trader: 交易器对象
        save_results: 是否保存结果
        
    Returns:
        保存文件路径（如果保存）
        
    Examples:
        >>> trader = start_trading('RSI', 'AAPL')
        >>> # ... 运行一段时间后
        >>> path = stop_trading(trader)
        >>> print(f"交易结果保存到：{path}")
    """
    try:
        trader.stop_trading()
        
        if save_results:
            return trader.save_results()
        return None
        
    except Exception as e:
        logger.error(f"停止交易失败：{e}")
        return None

# ==================== 工具函数 ====================

def quick_analysis(symbol: str, days: int = 30) -> str:
    """
    快速股票分析
    
    Args:
        symbol: 股票代码
        days: 分析天数
        
    Returns:
        分析报告
        
    Examples:
        >>> report = quick_analysis('AAPL', 30)
        >>> print(report)
    """
    try:
        # 获取数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        data = get_stock_data(symbol, start_date, end_date)
        
        if data.empty:
            return f"❌ 无法获取 {symbol} 的数据"
        
        # 基本统计
        current_price = data['Close'].iloc[-1]
        period_high = data['High'].max()
        period_low = data['Low'].min()
        period_return = ((current_price / data['Close'].iloc[0]) - 1) * 100
        
        # 测试多个策略
        strategies = ['MA_Cross', 'RSI', 'MACD']
        signals = []
        
        for strategy_name in strategies:
            try:
                result = test_strategy(strategy_name, symbol)
                signals.append(f"{strategy_name}: {result.signal.value} "
                             f"(置信度: {result.confidence:.2f})")
            except:
                signals.append(f"{strategy_name}: 无法分析")
        
        return f"""
📊 {symbol} 快速分析报告 ({days}天)
{'=' * 40}
💰 当前价格：${current_price:.2f}
📈 期间最高：${period_high:.2f}
📉 期间最低：${period_low:.2f}
📊 期间收益：{period_return:.2f}%

🔧 策略信号：
{chr(10).join('  ' + signal for signal in signals)}

📅 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
    except Exception as e:
        logger.error(f"快速分析失败：{e}")
        return f"❌ 分析失败：{e}"

def system_status() -> str:
    """
    检查系统状态
    
    Returns:
        系统状态报告
        
    Examples:
        >>> status = system_status()
        >>> print(status)
    """
    status_items = []
    
    try:
        # 检查数据模块
        data_manager = DataManager()
        status_items.append("✅ 数据模块：正常")
    except Exception as e:
        status_items.append(f"❌ 数据模块：{e}")
    
    try:
        # 检查策略模块
        strategies = list_strategies()
        status_items.append(f"✅ 策略模块：{len(strategies)}个策略可用")
    except Exception as e:
        status_items.append(f"❌ 策略模块：{e}")
    
    try:
        # 检查回测模块
        from backtest_manager import SimpleBacktester
        status_items.append("✅ 回测模块：正常")
    except Exception as e:
        status_items.append(f"❌ 回测模块：{e}")
    
    try:
        # 检查交易模块
        from paper_trader import PaperTrader
        status_items.append("✅ 交易模块：正常")
    except Exception as e:
        status_items.append(f"❌ 交易模块：{e}")
    
    return f"""
🚀 量化交易系统状态检查
{'=' * 30}
{chr(10).join(status_items)}

📦 可用策略：{', '.join(list_strategies())}

⏰ 检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """.strip()

# ==================== 示例和教程 ====================

def demo():
    """
    运行演示示例
    
    Examples:
        >>> demo()  # 运行完整演示
    """
    print("🚀 量化交易系统演示")
    print("=" * 50)
    
    # 系统状态检查
    print("\n🔧 系统状态检查...")
    print(system_status())
    
    # 数据获取演示
    print("\n📊 数据获取演示...")
    try:
        data = get_stock_data('AAPL', period='1d')
        print(f"✅ 获取AAPL数据：{len(data)}条记录")
        print(f"   最新价格：${data['Close'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"❌ 数据获取失败：{e}")
    
    # 策略测试演示
    print("\n🔧 策略测试演示...")
    try:
        result = test_strategy('RSI', 'AAPL')
        print(f"✅ RSI策略信号：{result.signal.value}")
        print(f"   置信度：{result.confidence:.2f}")
        print(f"   原因：{result.reason}")
    except Exception as e:
        print(f"❌ 策略测试失败：{e}")
    
    # 快速分析演示
    print("\n📈 快速分析演示...")
    try:
        analysis = quick_analysis('AAPL', 10)
        print(analysis)
    except Exception as e:
        print(f"❌ 快速分析失败：{e}")
    
    print("\n" + "=" * 50)
    print("🎯 演示完成！")
    print("\n📚 快速开始指南：")
    print("  1. 获取数据：data = get_stock_data('AAPL')")
    print("  2. 创建策略：strategy = create_simple_strategy('RSI')")
    print("  3. 运行回测：result = backtest('RSI', 'AAPL')")
    print("  4. 启动交易：trader = start_trading('RSI', 'AAPL')")
    print("=" * 50)

def tutorial():
    """
    显示教程信息
    """
    print("""
📚 量化交易系统快速教程
========================

🎯 核心理念：让量化交易像使用计算器一样简单！

📊 1. 数据获取
--------------
# 获取股票数据
data = get_stock_data('AAPL', '2023-01-01', '2023-12-31')

# 获取实时价格
price = get_price('AAPL')

# 获取股票信息
info = get_info('AAPL')

🔧 2. 策略创建
--------------
# 创建移动平均策略
strategy = create_simple_strategy('MA_Cross', {'fast': 5, 'slow': 20})

# 创建RSI策略
strategy = create_simple_strategy('RSI', {'period': 14, 'oversold': 30})

# 查看可用策略
strategies = list_strategies()

# 快速测试策略
signal = test_strategy('RSI', 'AAPL')

📈 3. 回测分析
--------------
# 一行代码完成回测
result = backtest('MA_Cross', 'AAPL')
print(result.summary())

# 比较多个策略
results = compare_strategies(['MA_Cross', 'RSI'], 'AAPL')

# 保存回测结果
save_backtest(result)

💰 4. 模拟交易
--------------
# 启动单股票交易
trader = start_trading('RSI', 'AAPL')

# 启动多股票交易
trader = start_trading('MA_Cross', ['AAPL', 'MSFT'], 50000)

# 查看交易状态
status = get_trading_status(trader)
print(status)

# 停止交易并保存结果
stop_trading(trader)

🛠️ 5. 工具函数
---------------
# 快速分析
report = quick_analysis('AAPL', 30)

# 系统状态检查
status = system_status()

# 运行演示
demo()

🚀 更多功能请查看文档或运行 demo() 函数！
    """)

# ==================== 主程序 ====================

if __name__ == "__main__":
    print("🚀 量化交易系统简化接口")
    print("=" * 50)
    
    # 检查系统状态
    print(system_status())
    
    print("\n📚 使用教程：")
    print("  tutorial()  - 查看完整教程")
    print("  demo()      - 运行演示示例")
    print("  system_status() - 检查系统状态")
    
    print("\n🎯 核心功能：")
    print("  📊 数据：get_stock_data(), get_price(), get_info()")
    print("  🔧 策略：create_simple_strategy(), test_strategy()")
    print("  📈 回测：backtest(), compare_strategies()")
    print("  💰 交易：start_trading(), get_trading_status()")
    
    print("\n" + "=" * 50)
    print("让量化交易变得像使用计算器一样简单！🎯")