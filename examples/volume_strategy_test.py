#!/usr/bin/env python3
"""
量价确认布林带策略测试脚本
测试新的成交量确认机制是否能提升策略表现
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import backtrader as bt
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

# 导入策略
from src.strategies.volume_confirmed_bb import VolumeConfirmedBollingerStrategy
from src.strategies.bollinger_bands import EnhancedBollingerBandsStrategy  # 现有增强策略
from src.analyzers import trade_analyzer


def fetch_stock_data(symbol, period='1y'):
    """获取股票数据"""
    print(f"📈 获取 {symbol} 数据...")
    
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period)
    
    if data.empty:
        raise ValueError(f"无法获取 {symbol} 数据")
    
    print(f"✅ 获取 {len(data)} 天数据: {data.index[0].date()} 到 {data.index[-1].date()}")
    return data


def create_cerebro(strategy_class, data, initial_cash=100000):
    """创建backtrader环境"""
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class)
    
    # 添加数据
    bt_data = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(bt_data)
    
    # 设置经纪人
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% 手续费
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    
    return cerebro


def run_backtest(symbol, strategy_class, strategy_name):
    """运行回测"""
    print(f"\n{'='*60}")
    print(f"🧪 测试策略: {strategy_name}")
    print(f"📊 标的: {symbol}")
    print(f"{'='*60}")
    
    # 获取数据
    data = fetch_stock_data(symbol)
    
    # 创建backtrader环境
    cerebro = create_cerebro(strategy_class, data)
    
    # 记录初始资金
    start_value = cerebro.broker.getvalue()
    print(f"💰 初始资金: ${start_value:,.2f}")
    
    # 运行回测
    print("🔄 运行回测...")
    results = cerebro.run()
    
    # 获取结果
    end_value = cerebro.broker.getvalue()
    result = results[0]
    
    # 提取分析结果
    returns = result.analyzers.returns.get_analysis()
    drawdown = result.analyzers.drawdown.get_analysis()
    trades = result.analyzers.trades.get_analysis()
    sharpe = result.analyzers.sharpe.get_analysis()
    
    # 计算关键指标
    total_return = (end_value - start_value) / start_value * 100
    total_trades = trades.get('total', {}).get('total', 0)
    win_rate = 0
    if total_trades > 0:
        won_trades = trades.get('won', {}).get('total', 0)
        win_rate = won_trades / total_trades * 100
    
    # 打印结果
    print("\n📋 回测结果:")
    print(f"  💵 最终价值: ${end_value:,.2f}")
    print(f"  📈 总收益率: {total_return:+.2f}%")
    print(f"  🎯 胜率: {win_rate:.1f}%")
    print(f"  📊 总交易数: {total_trades}")
    print(f"  📉 最大回撤: {drawdown.get('max', {}).get('drawdown', 0):.2f}%")
    print(f"  📊 夏普比率: {sharpe.get('sharperatio', 0):.3f}")
    
    return {
        'symbol': symbol,
        'strategy': strategy_name,
        'total_return': total_return,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'max_drawdown': abs(drawdown.get('max', {}).get('drawdown', 0)),
        'sharpe_ratio': sharpe.get('sharperatio', 0),
        'final_value': end_value
    }


def compare_strategies():
    """对比测试两种策略"""
    print("🚀 量价确认策略 vs 增强布林带策略对比测试")
    print("="*80)
    
    # 测试股票列表
    symbols = ['AAPL', 'NVDA', 'TSLA', 'MSFT']
    
    # 策略配置
    strategies = [
        (EnhancedBollingerBandsStrategy, "增强布林带 (MACD)"),
        (VolumeConfirmedBollingerStrategy, "量价确认布林带 (新)")
    ]
    
    all_results = []
    
    # 对每个股票测试每种策略
    for symbol in symbols:
        print(f"\n🏷️  测试标的: {symbol}")
        print("-" * 50)
        
        symbol_results = []
        for strategy_class, strategy_name in strategies:
            try:
                result = run_backtest(symbol, strategy_class, strategy_name)
                symbol_results.append(result)
                all_results.append(result)
            except Exception as e:
                print(f"❌ {strategy_name} 测试失败: {e}")
                continue
        
        # 对比当前股票的策略表现
        if len(symbol_results) == 2:
            old_strategy, new_strategy = symbol_results
            improvement = new_strategy['total_return'] - old_strategy['total_return']
            win_rate_diff = new_strategy['win_rate'] - old_strategy['win_rate']
            
            print(f"\n🔍 {symbol} 策略对比:")
            print(f"  收益率提升: {improvement:+.2f}% "
                  f"({old_strategy['total_return']:.2f}% → {new_strategy['total_return']:.2f}%)")
            print(f"  胜率变化: {win_rate_diff:+.1f}% "
                  f"({old_strategy['win_rate']:.1f}% → {new_strategy['win_rate']:.1f}%)")
    
    # 综合分析
    print(f"\n{'='*80}")
    print("📊 综合策略表现分析")
    print(f"{'='*80}")
    
    # 按策略分组统计
    strategy_stats = {}
    for result in all_results:
        strategy_name = result['strategy']
        if strategy_name not in strategy_stats:
            strategy_stats[strategy_name] = []
        strategy_stats[strategy_name].append(result)
    
    for strategy_name, results in strategy_stats.items():
        avg_return = sum(r['total_return'] for r in results) / len(results)
        avg_win_rate = sum(r['win_rate'] for r in results) / len(results)
        win_count = sum(1 for r in results if r['total_return'] > 0)
        
        print(f"\n🎯 {strategy_name}:")
        print(f"  平均收益率: {avg_return:+.2f}%")
        print(f"  平均胜率: {avg_win_rate:.1f}%")
        print(f"  盈利股票: {win_count}/{len(results)} ({win_count/len(results)*100:.0f}%)")
    
    # 策略优势分析
    if len(strategy_stats) == 2:
        old_results = strategy_stats["增强布林带 (MACD)"]
        new_results = strategy_stats["量价确认布林带 (新)"]
        
        improvements = []
        for old, new in zip(old_results, new_results):
            if old['symbol'] == new['symbol']:
                improvements.append(new['total_return'] - old['total_return'])
        
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            better_count = sum(1 for imp in improvements if imp > 0)
            
            print(f"\n🏆 量价确认策略优势:")
            print(f"  平均收益提升: {avg_improvement:+.2f}%")
            print(f"  表现更好的股票: {better_count}/{len(improvements)} "
                  f"({better_count/len(improvements)*100:.0f}%)")
            
            if avg_improvement > 2:
                print("✅ 量价确认策略显著优于基础策略！")
            elif avg_improvement > 0:
                print("✅ 量价确认策略略优于基础策略")
            else:
                print("⚠️  量价确认策略需要进一步调优")


if __name__ == "__main__":
    try:
        compare_strategies()
        print(f"\n{'='*80}")
        print("🎉 测试完成！查看上方结果分析。")
        print("💡 提示: 如果量价确认策略表现更好，建议正式部署使用。")
        print("="*80)
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()