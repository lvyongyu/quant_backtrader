"""
简化测试：验证增强布林带策略
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import backtrader as bt
import yfinance as yf


class BollingerBandsMACDStrategy(bt.Strategy):
    """简化的布林带+MACD策略测试"""
    
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
        
    def next(self):
        # Check for pending order
        if self.order:
            return
            
        # Not in position
        if not self.position:
            # Buy signal: Price touches lower band + MACD bullish
            if (self.dataclose[0] <= self.bb.lines.bot[0] and
                self.macd.lines.macd[0] > self.macd.lines.signal[0]):
                
                self.order = self.buy()
                print(f"买入信号: {self.data.datetime.date(0)} 价格: {self.dataclose[0]:.2f}")
        
        else:
            # Sell signal: Price touches upper band or MACD bearish
            if (self.dataclose[0] >= self.bb.lines.top[0] or
                self.macd.lines.macd[0] < self.macd.lines.signal[0]):
                
                self.order = self.sell()
                print(f"卖出信号: {self.data.datetime.date(0)} 价格: {self.dataclose[0]:.2f}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'买入执行: 价格 {order.executed.price:.2f}')
            elif order.issell():
                print(f'卖出执行: 价格 {order.executed.price:.2f}')
        
        self.order = None


def test_strategy(symbol='AAPL'):
    print(f"测试增强布林带策略: {symbol}")
    print("=" * 50)
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(BollingerBandsMACDStrategy)
    
    # Get data from Yahoo Finance
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"无法获取 {symbol} 的数据")
            return
        
        # Create Backtrader data feed
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data)
        
        # Set cash
        cerebro.broker.setcash(10000.0)
        
        # Set commission
        cerebro.broker.setcommission(commission=0.001)
        
        print(f'初始资金: ${cerebro.broker.getvalue():.2f}')
        
        # Run backtest
        cerebro.run()
        
        final_value = cerebro.broker.getvalue()
        print(f'最终资金: ${final_value:.2f}')
        print(f'收益率: {(final_value - 10000) / 10000 * 100:.2f}%')
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_strategy('AAPL')