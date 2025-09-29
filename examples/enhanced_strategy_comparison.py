"""
增强布林带策略示例 - 使用真实的策略类进行测试
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import backtrader as bt
import yfinance as yf
from src.strategies.bollinger_bands import BollingerBandsStrategy


# 简单版布林带策略（仅用于对比）
class SimpleBollingerBandsStrategy(bt.Strategy):
    """简单的布林带策略，不使用MACD确认"""
    
    params = (
        ('bb_period', 20),
        ('bb_devfactor', 2),
    )
    
    def __init__(self):
        self.bollinger = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor
        )
        self.order = None
        
    def next(self):
        if self.order:
            return
            
        if not self.position:
            if self.data.close[0] <= self.bollinger.lines.bot[0]:
                self.order = self.buy()
        else:
            if self.data.close[0] >= self.bollinger.lines.top[0]:
                self.order = self.sell()
    
    def notify_order(self, order):
        self.order = None


def compare_strategies(symbol='AAPL', days=180):
    """
    比较增强布林带策略和简单布林带策略的表现
    """
    print(f"📊 策略对比测试: {symbol}")
    print("=" * 80)
    
    # 获取数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"无法获取 {symbol} 的数据")
            return
        
        print(f"📈 测试数据: {len(df)} 天 ({df.index[0].date()} 到 {df.index[-1].date()})")
        print(f"💰 价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
        volatility = df['Close'].pct_change().std() * 100
        print(f"📊 波动率: {volatility:.2f}%")
        print()
        
        # 测试增强版策略
        print("🔬 测试增强版布林带策略 (含MACD确认)")
        print("-" * 50)
        
        cerebro1 = bt.Cerebro()
        cerebro1.addstrategy(BollingerBandsStrategy, debug=False)
        
        data1 = bt.feeds.PandasData(dataname=df.copy())
        cerebro1.adddata(data1)
        cerebro1.broker.setcash(10000.0)
        cerebro1.broker.setcommission(commission=0.001)
        
        # 添加分析器
        cerebro1.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro1.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro1.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        results1 = cerebro1.run()
        strategy1 = results1[0]
        final1 = cerebro1.broker.getvalue()
        return1 = (final1 - 10000) / 10000 * 100
        
        # 获取交易分析
        trades1 = strategy1.analyzers.trades.get_analysis()
        total_trades1 = trades1.get('total', {}).get('total', 0)
        won_trades1 = trades1.get('won', {}).get('total', 0)
        win_rate1 = (won_trades1 / total_trades1 * 100) if total_trades1 > 0 else 0
        
        sharpe1 = strategy1.analyzers.sharpe.get_analysis().get('sharperatio', 'N/A')
        drawdown1 = strategy1.analyzers.drawdown.get_analysis()
        max_dd1 = drawdown1.get('max', {}).get('drawdown', 0)
        
        print(f"💰 最终资金: ${final1:,.2f}")
        print(f"📈 收益率: {return1:.2f}%")
        print(f"🎯 交易次数: {total_trades1}")
        print(f"✅ 胜率: {win_rate1:.1f}%")
        print(f"📊 夏普比率: {sharpe1}")
        print(f"📉 最大回撤: {max_dd1:.2f}%")
        print()
        
        # 测试简单版策略
        print("🔬 测试简单版布林带策略 (无MACD确认)")
        print("-" * 50)
        
        cerebro2 = bt.Cerebro()
        cerebro2.addstrategy(SimpleBollingerBandsStrategy)
        
        data2 = bt.feeds.PandasData(dataname=df.copy())
        cerebro2.adddata(data2)
        cerebro2.broker.setcash(10000.0)
        cerebro2.broker.setcommission(commission=0.001)
        
        # 添加分析器
        cerebro2.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro2.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro2.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        results2 = cerebro2.run()
        strategy2 = results2[0]
        final2 = cerebro2.broker.getvalue()
        return2 = (final2 - 10000) / 10000 * 100
        
        # 获取交易分析
        trades2 = strategy2.analyzers.trades.get_analysis()
        total_trades2 = trades2.get('total', {}).get('total', 0)
        won_trades2 = trades2.get('won', {}).get('total', 0)
        win_rate2 = (won_trades2 / total_trades2 * 100) if total_trades2 > 0 else 0
        
        sharpe2 = strategy2.analyzers.sharpe.get_analysis().get('sharperatio', 'N/A')
        drawdown2 = strategy2.analyzers.drawdown.get_analysis()
        max_dd2 = drawdown2.get('max', {}).get('drawdown', 0)
        
        print(f"💰 最终资金: ${final2:,.2f}")
        print(f"📈 收益率: {return2:.2f}%")
        print(f"🎯 交易次数: {total_trades2}")
        print(f"✅ 胜率: {win_rate2:.1f}%")
        print(f"📊 夏普比率: {sharpe2}")
        print(f"📉 最大回撤: {max_dd2:.2f}%")
        print()
        
        # 买入持有基准
        buy_hold = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100
        
        # 对比结果
        print("📊 策略对比结果")
        print("=" * 80)
        print(f"{'指标':<15} {'增强版':<12} {'简单版':<12} {'买入持有':<12} {'增强版优势'}")
        print("-" * 80)
        print(f"{'收益率':<15} {return1:>10.2f}% {return2:>10.2f}% {buy_hold:>10.2f}% {return1-return2:>+8.2f}%")
        print(f"{'交易次数':<15} {total_trades1:>10d} {total_trades2:>10d} {'1':>10s} {total_trades1-total_trades2:>+8d}")
        print(f"{'胜率':<15} {win_rate1:>10.1f}% {win_rate2:>10.1f}% {'-':>10s} {win_rate1-win_rate2:>+8.1f}%")
        print(f"{'最大回撤':<15} {max_dd1:>10.2f}% {max_dd2:>10.2f}% {'-':>10s} {max_dd1-max_dd2:>+8.2f}%")
        print("-" * 80)
        
        # 结论
        print("\n💡 策略分析:")
        if return1 > return2:
            print("✅ 增强版策略收益更高，MACD确认有效提升了盈利能力")
        elif return1 < return2:
            print("⚠️  简单版策略收益更高，但增强版可能风险更低")
        else:
            print("➡️  两种策略收益相当")
            
        if total_trades1 < total_trades2:
            print("✅ 增强版策略交易更少，MACD确认有效减少了假信号")
        
        if win_rate1 > win_rate2:
            print("✅ 增强版策略胜率更高，信号质量得到提升")
        
        print("=" * 80)
        
        return {
            'enhanced': {'return': return1, 'trades': total_trades1, 'win_rate': win_rate1},
            'simple': {'return': return2, 'trades': total_trades2, 'win_rate': win_rate2},
            'buy_hold': buy_hold
        }
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # 测试多个股票
    test_symbols = ['AAPL', 'TSLA', 'NVDA', 'MSTR']
    
    print("🚀 布林带策略增强效果验证")
    print("🎯 对比原版 vs MACD增强版")
    print("=" * 100)
    
    all_results = {}
    
    for symbol in test_symbols:
        print()
        result = compare_strategies(symbol, days=120)
        if result:
            all_results[symbol] = result
        print()
    
    # 总体汇总
    if all_results:
        print("\n📊 全部测试汇总:")
        print("=" * 100)
        print(f"{'股票':<6} {'增强版收益':<10} {'简单版收益':<10} {'买入持有':<10} {'增强版交易':<8} {'简单版交易'}")
        print("-" * 100)
        
        enhanced_wins = 0
        total_tests = len(all_results)
        
        for symbol, data in all_results.items():
            enhanced = data['enhanced']
            simple = data['simple']
            buy_hold = data['buy_hold']
            
            if enhanced['return'] > simple['return']:
                enhanced_wins += 1
                winner = "✅"
            else:
                winner = "❌"
            
            print(f"{symbol:<6} {enhanced['return']:>8.2f}% {simple['return']:>8.2f}% {buy_hold:>8.2f}% "
                  f"{enhanced['trades']:>6d} {simple['trades']:>6d} {winner}")
        
        print("-" * 100)
        print(f"增强版获胜率: {enhanced_wins}/{total_tests} = {enhanced_wins/total_tests*100:.1f}%")
        print("=" * 100)