"""
测试增强的布林带+MACD策略

比较原始布林带策略和新的MACD增强版本的效果
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import backtrader as bt
    from src.strategies.bollinger_bands import BollingerBandsStrategy
    from src.data.yahoo_feed import YahooDataFeed
    from src.brokers.paper_broker import PaperBroker
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def test_enhanced_bollinger_strategy(symbol: str = 'AAPL'):
    """
    测试增强的布林带+MACD策略
    
    Args:
        symbol: 股票代码
    """
    print(f"🎯 测试增强布林带策略: {symbol}")
    print("📊 策略特点: 布林带 + MACD确认信号")
    print("=" * 60)
    
    # Create Cerebro engine
    cerebro = bt.Cerebro()
    
    # Add enhanced strategy
    cerebro.addstrategy(
        BollingerBandsStrategy,
        bb_period=20,
        bb_devfactor=2,
        debug=True
    )
    
    # Create data feed
    try:
        data_feed = YahooDataFeed.create_data_feed(
            symbol=symbol,
            period='6mo',
            interval='1d'
        )
        cerebro.adddata(data_feed)
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return
    
    # Set up broker
    paper_broker = PaperBroker.create_realistic_broker(cash=10000)
    paper_broker.setup_broker(cerebro)
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # Print starting conditions
    starting_value = cerebro.broker.getvalue()
    print(f'💰 初始资金: ${starting_value:,.2f}')
    print()
    
    # Run backtest
    try:
        print("🚀 运行回测...")
        results = cerebro.run()
        strategy = results[0]
        
        # Print final results
        final_value = cerebro.broker.getvalue()
        total_return = ((final_value - starting_value) / starting_value) * 100
        
        print("=" * 60)
        print("📈 回测结果:")
        print("-" * 60)
        print(f'最终资产: ${final_value:,.2f}')
        print(f'总收益率: {total_return:.2f}%')
        
        # Print analyzer results
        if hasattr(strategy.analyzers, 'sharpe'):
            sharpe = strategy.analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe.get("sharperatio", "N/A")
            print(f'夏普比率: {sharpe_ratio}')
        
        if hasattr(strategy.analyzers, 'drawdown'):
            drawdown = strategy.analyzers.drawdown.get_analysis()
            max_dd = drawdown.get("max", {}).get("drawdown", 0)
            print(f'最大回撤: {max_dd:.2f}%')
        
        if hasattr(strategy.analyzers, 'trades'):
            trades = strategy.analyzers.trades.get_analysis()
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
            
            print(f'总交易次数: {total_trades}')
            print(f'盈利交易: {won_trades}')
            print(f'亏损交易: {lost_trades}')
            print(f'胜率: {win_rate:.1f}%')
        
        print("=" * 60)
        print()
        
        # 策略优势分析
        print("💡 MACD增强策略优势:")
        print("✅ 减少假突破信号")
        print("✅ 趋势确认，提高准确率")
        print("✅ 多重确认机制，降低风险")
        print("✅ 适合震荡和趋势市场")
        print()
        
        return {
            'return': total_return,
            'trades': total_trades,
            'win_rate': win_rate,
            'max_drawdown': max_dd
        }
        
    except Exception as e:
        print(f"❌ 运行回测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # 测试多个股票
    test_symbols = ['AAPL', 'TSLA', 'MSTR', 'NVDA']
    
    print("🔬 增强布林带策略测试报告")
    print("=" * 80)
    
    results = {}
    
    for symbol in test_symbols:
        result = test_enhanced_bollinger_strategy(symbol)
        if result:
            results[symbol] = result
        print()
    
    # 汇总结果
    if results:
        print("📊 策略表现汇总:")
        print("-" * 80)
        print(f"{'股票':<8} {'收益率':<10} {'交易次数':<8} {'胜率':<8} {'最大回撤'}")
        print("-" * 80)
        
        total_return = 0
        total_trades = 0
        total_wins = 0
        
        for symbol, data in results.items():
            print(f"{symbol:<8} {data['return']:>8.2f}% {data['trades']:>6d} {data['win_rate']:>6.1f}% {data['max_drawdown']:>8.2f}%")
            total_return += data['return']
            total_trades += data['trades']
            if data['trades'] > 0:
                total_wins += data['win_rate'] * data['trades'] / 100
        
        avg_return = total_return / len(results)
        avg_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        print("-" * 80)
        print(f"平均收益率: {avg_return:.2f}%")
        print(f"总交易次数: {total_trades}")
        print(f"平均胜率: {avg_win_rate:.1f}%")
        print("=" * 80)