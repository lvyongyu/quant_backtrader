"""
优化的布林带+MACD策略测试
调整条件使其更容易触发信号
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import backtrader as bt
import yfinance as yf


class OptimizedBollingerBandsMACDStrategy(bt.Strategy):
    """优化的布林带+MACD策略"""
    
    params = (
        ('bb_period', 20),
        ('bb_devfactor', 2),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
    )
    
    def __init__(self):
        # Bollinger Bands
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor
        )
        
        # MACD
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        
        # RSI for additional confirmation
        self.rsi = bt.indicators.RSI(self.data.close, period=14)
        
        self.order = None
        self.dataclose = self.data.close
        self.signal_count = 0
        
    def next(self):
        current_date = self.data.datetime.date(0)
        current_price = self.dataclose[0]
        
        # Check for pending order
        if self.order:
            return
            
        # Not in position
        if not self.position:
            # 买入条件：价格接近布林带下轨 + MACD看涨 + RSI超卖
            bb_lower_threshold = self.bb.lines.bot[0] * 1.02  # 允许2%的误差
            price_near_lower = current_price <= bb_lower_threshold
            macd_bullish = self.macd.lines.macd[0] > self.macd.lines.signal[0]
            rsi_oversold = self.rsi[0] < 40
            
            if price_near_lower and (macd_bullish or rsi_oversold):
                self.signal_count += 1
                self.order = self.buy()
                print(f"📈 买入信号 #{self.signal_count}: {current_date}")
                print(f"  价格: {current_price:.2f} (下轨: {self.bb.lines.bot[0]:.2f})")
                print(f"  MACD: {self.macd.lines.macd[0]:.4f} vs {self.macd.lines.signal[0]:.4f} {'✓' if macd_bullish else '✗'}")
                print(f"  RSI: {self.rsi[0]:.1f} {'✓' if rsi_oversold else '✗'}")
        
        else:
            # 卖出条件：价格接近布林带上轨 + MACD看跌 或 RSI超买
            bb_upper_threshold = self.bb.lines.top[0] * 0.98  # 允许2%的误差
            price_near_upper = current_price >= bb_upper_threshold
            macd_bearish = self.macd.lines.macd[0] < self.macd.lines.signal[0]
            rsi_overbought = self.rsi[0] > 70
            
            if price_near_upper or macd_bearish or rsi_overbought:
                self.signal_count += 1
                self.order = self.sell()
                print(f"📉 卖出信号 #{self.signal_count}: {current_date}")
                print(f"  价格: {current_price:.2f} (上轨: {self.bb.lines.top[0]:.2f})")
                print(f"  MACD: {self.macd.lines.macd[0]:.4f} vs {self.macd.lines.signal[0]:.4f} {'✓' if macd_bearish else '✗'}")
                print(f"  RSI: {self.rsi[0]:.1f} {'✓' if rsi_overbought else '✗'}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'✅ 买入执行: 价格 {order.executed.price:.2f}')
            elif order.issell():
                print(f'✅ 卖出执行: 价格 {order.executed.price:.2f}, 盈亏: {(order.executed.price - self.buy_price):.2f}')
                
        self.order = None
    
    def notify_trade(self, trade):
        if trade.isclosed:
            print(f'📊 交易完成: 盈亏 ${trade.pnl:.2f}')
            if hasattr(self, 'buy_price'):
                delattr(self, 'buy_price')
        else:
            self.buy_price = trade.price


def test_optimized_strategy(symbol='TSLA'):  # 使用波动性更大的股票
    print(f"🚀 测试优化布林带+MACD策略: {symbol}")
    print("=" * 70)
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(OptimizedBollingerBandsMACDStrategy)
    
    # Get data from Yahoo Finance - 使用更长时间段
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"无法获取 {symbol} 的数据")
            return
        
        print(f"📊 获取到 {len(df)} 天的数据")
        print(f"数据范围: {df.index[0].date()} 到 {df.index[-1].date()}")
        print(f"价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
        volatility = df['Close'].pct_change().std() * 100
        print(f"价格波动率: {volatility:.2f}%")
        print("=" * 70)
        
        # Create Backtrader data feed
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data)
        
        # Set cash
        cerebro.broker.setcash(10000.0)
        
        # Set commission
        cerebro.broker.setcommission(commission=0.001)
        
        print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
        print()
        
        # Run backtest
        results = cerebro.run()
        strategy = results[0]
        
        final_value = cerebro.broker.getvalue()
        print()
        print("=" * 70)
        print(f'📈 最终资金: ${final_value:.2f}')
        print(f'📊 收益率: {(final_value - 10000) / 10000 * 100:.2f}%')
        print(f'🎯 总信号数: {strategy.signal_count}')
        
        # 计算基准收益率
        buy_hold_return = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100
        print(f'📈 买入持有收益率: {buy_hold_return:.2f}%')
        
        alpha = (final_value - 10000) / 10000 * 100 - buy_hold_return
        print(f'📊 超额收益率 (Alpha): {alpha:.2f}%')
        print("=" * 70)
        
        return {
            'final_value': final_value,
            'return': (final_value - 10000) / 10000 * 100,
            'signals': strategy.signal_count,
            'buy_hold': buy_hold_return,
            'alpha': alpha
        }
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # 测试多个高波动性股票
    symbols = ['TSLA', 'MSTR', 'NVDA', 'AMD']
    results = {}
    
    for symbol in symbols:
        print()
        result = test_optimized_strategy(symbol)
        if result:
            results[symbol] = result
        print()
    
    # 汇总结果
    if results:
        print("📊 策略表现汇总:")
        print("=" * 80)
        print(f"{'股票':<6} {'最终资金':<10} {'策略收益':<8} {'信号数':<6} {'买入持有':<8} {'Alpha':<8}")
        print("=" * 80)
        
        for symbol, data in results.items():
            print(f"{symbol:<6} ${data['final_value']:>8,.0f} {data['return']:>6.1f}% "
                  f"{data['signals']:>4d} {data['buy_hold']:>6.1f}% {data['alpha']:>6.1f}%")
        
        avg_return = sum(r['return'] for r in results.values()) / len(results)
        avg_alpha = sum(r['alpha'] for r in results.values()) / len(results)
        
        print("=" * 80)
        print(f"平均策略收益率: {avg_return:.1f}%")
        print(f"平均Alpha: {avg_alpha:.1f}%")
        print("=" * 80)