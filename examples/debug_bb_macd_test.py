"""
调试版布林带+MACD策略测试
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import backtrader as bt
import yfinance as yf


class DebugBollingerBandsMACDStrategy(bt.Strategy):
    """调试版布林带+MACD策略"""
    
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
        
        self.order = None
        self.dataclose = self.data.close
        self.signal_count = 0
        
    def next(self):
        current_date = self.data.datetime.date(0)
        current_price = self.dataclose[0]
        
        # 每10天输出一次调试信息
        if len(self) % 10 == 0:
            bb_lower = self.bb.lines.bot[0]
            bb_upper = self.bb.lines.top[0]
            bb_middle = self.bb.lines.mid[0]
            macd_main = self.macd.lines.macd[0]
            macd_signal = self.macd.lines.signal[0]
            
            print(f"日期: {current_date} 价格: {current_price:.2f}")
            print(f"  布林带: 下轨={bb_lower:.2f}, 中轨={bb_middle:.2f}, 上轨={bb_upper:.2f}")
            print(f"  MACD: 主线={macd_main:.4f}, 信号线={macd_signal:.4f}")
            print(f"  持仓: {self.position.size}")
            print("-" * 40)
        
        # Check for pending order
        if self.order:
            return
            
        # Not in position
        if not self.position:
            # Buy signal: Price touches lower band + MACD bullish
            buy_condition1 = current_price <= self.bb.lines.bot[0]
            buy_condition2 = self.macd.lines.macd[0] > self.macd.lines.signal[0]
            
            if buy_condition1 and buy_condition2:
                self.signal_count += 1
                self.order = self.buy()
                print(f"📈 买入信号 #{self.signal_count}: {current_date} 价格: {current_price:.2f}")
                print(f"  条件1 (价格<=下轨): {buy_condition1} ({current_price:.2f} <= {self.bb.lines.bot[0]:.2f})")
                print(f"  条件2 (MACD>信号): {buy_condition2} ({self.macd.lines.macd[0]:.4f} > {self.macd.lines.signal[0]:.4f})")
        
        else:
            # Sell signal: Price touches upper band or MACD bearish
            sell_condition1 = current_price >= self.bb.lines.top[0]
            sell_condition2 = self.macd.lines.macd[0] < self.macd.lines.signal[0]
            
            if sell_condition1 or sell_condition2:
                self.signal_count += 1
                self.order = self.sell()
                print(f"📉 卖出信号 #{self.signal_count}: {current_date} 价格: {current_price:.2f}")
                print(f"  条件1 (价格>=上轨): {sell_condition1} ({current_price:.2f} >= {self.bb.lines.top[0]:.2f})")
                print(f"  条件2 (MACD<信号): {sell_condition2} ({self.macd.lines.macd[0]:.4f} < {self.macd.lines.signal[0]:.4f})")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'✅ 买入执行: 价格 {order.executed.price:.2f}, 手数 {order.executed.size}')
            elif order.issell():
                print(f'✅ 卖出执行: 价格 {order.executed.price:.2f}, 手数 {order.executed.size}')
        
        self.order = None


def debug_strategy(symbol='AAPL'):
    print(f"🔍 调试增强布林带策略: {symbol}")
    print("=" * 60)
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(DebugBollingerBandsMACDStrategy)
    
    # Get data from Yahoo Finance
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 缩短到90天
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"无法获取 {symbol} 的数据")
            return
        
        print(f"📊 获取到 {len(df)} 天的数据")
        print(f"数据范围: {df.index[0].date()} 到 {df.index[-1].date()}")
        print(f"价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
        print("=" * 60)
        
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
        print("=" * 60)
        print(f'📈 最终资金: ${final_value:.2f}')
        print(f'📊 收益率: {(final_value - 10000) / 10000 * 100:.2f}%')
        print(f'🎯 总信号数: {strategy.signal_count}')
        print("=" * 60)
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_strategy('AAPL')