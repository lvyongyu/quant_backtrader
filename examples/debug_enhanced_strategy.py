"""
调试增强布林带策略 - 查看为什么没有交易信号
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import backtrader as bt
import yfinance as yf


class DebugEnhancedBollingerStrategy(bt.Strategy):
    """调试版增强布林带策略"""
    
    params = (
        ('bb_period', 20),
        ('bb_devfactor', 2),
    )
    
    def __init__(self):
        # Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor
        )
        
        # MACD with histogram
        self.macd = bt.indicators.MACDHisto(
            self.data.close,
            period_me1=12,
            period_me2=26,
            period_signal=9
        )
        
        self.order = None
        self.signal_checks = 0
        
    def next(self):
        if self.order:
            return
        
        current_date = self.data.datetime.date(0)
        current_price = self.data.close[0]
        
        # 每10天检查一次条件
        if len(self) % 10 == 0:
            self.signal_checks += 1
            
            bb_lower = self.bollinger.lines.bot[0]
            bb_upper = self.bollinger.lines.top[0]
            bb_middle = self.bollinger.lines.mid[0]
            
            macd_line = self.macd.macd[0]
            macd_signal = self.macd.signal[0]
            macd_histogram = self.macd.histo[0]
            
            print(f"\n检查 #{self.signal_checks} - {current_date}")
            print(f"价格: {current_price:.2f}")
            print(f"布林带: 下={bb_lower:.2f}, 中={bb_middle:.2f}, 上={bb_upper:.2f}")
            print(f"MACD: 主线={macd_line:.4f}, 信号={macd_signal:.4f}, 直方图={macd_histogram:.4f}")
            
            # 检查买入条件
            if not self.position:
                bb_buy_signal = current_price <= bb_lower
                print(f"布林带买入信号: {bb_buy_signal} (价格{current_price:.2f} <= 下轨{bb_lower:.2f})")
                
                if bb_buy_signal:
                    # MACD确认条件
                    macd_bullish = macd_line > macd_signal
                    macd_momentum = (macd_histogram > 0 or 
                                   (len(self) > 1 and macd_histogram > self.macd.histo[-1]))
                    macd_rising = len(self) > 1 and macd_line > self.macd.macd[-1]
                    
                    print(f"  MACD看涨: {macd_bullish}")
                    print(f"  MACD动量: {macd_momentum}")
                    print(f"  MACD上升: {macd_rising}")
                    
                    macd_confirmations = sum([macd_bullish, macd_momentum, macd_rising])
                    print(f"  MACD确认数: {macd_confirmations}/3 (需要≥2)")
                    
                    if macd_confirmations >= 2:
                        print("  🎯 买入信号确认！")
                        self.order = self.buy()
            else:
                bb_sell_signal = current_price >= bb_upper
                print(f"布林带卖出信号: {bb_sell_signal} (价格{current_price:.2f} >= 上轨{bb_upper:.2f})")
                
                if bb_sell_signal:
                    # MACD确认条件
                    macd_bearish = macd_line < macd_signal
                    macd_momentum = (macd_histogram < 0 or 
                                   (len(self) > 1 and macd_histogram < self.macd.histo[-1]))
                    macd_falling = len(self) > 1 and macd_line < self.macd.macd[-1]
                    
                    print(f"  MACD看跌: {macd_bearish}")
                    print(f"  MACD动量: {macd_momentum}")
                    print(f"  MACD下降: {macd_falling}")
                    
                    macd_confirmations = sum([macd_bearish, macd_momentum, macd_falling])
                    print(f"  MACD确认数: {macd_confirmations}/3 (需要≥2)")
                    
                    if macd_confirmations >= 2:
                        print("  🎯 卖出信号确认！")
                        self.order = self.sell()
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f'✅ 买入执行: {order.executed.price:.2f}')
            elif order.issell():
                print(f'✅ 卖出执行: {order.executed.price:.2f}')
        self.order = None


def debug_enhanced_strategy(symbol='AAPL', days=90):
    """调试增强策略"""
    print(f"🔍 调试增强布林带策略: {symbol}")
    print("=" * 60)
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(DebugEnhancedBollingerStrategy)
    
    # 获取数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"无法获取 {symbol} 的数据")
            return
        
        print(f"📊 数据: {len(df)} 天 ({df.index[0].date()} 到 {df.index[-1].date()})")
        print(f"📈 价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
        
        # Create Backtrader data feed
        data = bt.feeds.PandasData(dataname=df)
        cerebro.adddata(data)
        cerebro.broker.setcash(10000.0)
        cerebro.broker.setcommission(commission=0.001)
        
        print(f"💰 初始资金: ${cerebro.broker.getvalue():.2f}")
        
        # Run strategy
        results = cerebro.run()
        strategy = results[0]
        
        final_value = cerebro.broker.getvalue()
        print(f"\n📈 最终资金: ${final_value:.2f}")
        print(f"📊 收益率: {(final_value - 10000) / 10000 * 100:.2f}%")
        print(f"🔍 总检查次数: {strategy.signal_checks}")
        
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    debug_enhanced_strategy('AAPL', 90)