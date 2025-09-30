#!/usr/bin/env python3
"""
Enhanced Backtrader Strategy with Multi-Dimensional Signal Analysis
集成多维度信号分析的增强型Backtrader策略
"""

import backtrader as bt
import requests
import datetime
import math


class MultiDimensionalIndicator(bt.Indicator):
    """多维度技术指标"""
    
    lines = ('signal_score', 'trend_signal', 'momentum_signal', 'volume_signal', 'volatility_signal')
    params = (
        ('period_short', 5),
        ('period_medium', 14), 
        ('period_long', 20),
        ('volume_threshold', 1.5),
    )
    
    def __init__(self):
        # 基础技术指标
        self.sma_short = bt.indicators.SMA(self.data.close, period=self.p.period_short)
        self.sma_medium = bt.indicators.SMA(self.data.close, period=self.p.period_medium)
        self.sma_long = bt.indicators.SMA(self.data.close, period=self.p.period_long)
        
        self.rsi = bt.indicators.RSI(period=self.p.period_medium)
        self.stochastic = bt.indicators.Stochastic()
        self.atr = bt.indicators.ATR(period=self.p.period_medium)
        self.bbands = bt.indicators.BollingerBands(period=self.p.period_long)
        
        # MACD指标
        self.macd = bt.indicators.MACD()
        
        # 成交量指标
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=10)
        
    def next(self):
        """计算多维度信号"""
        
        # 1. 趋势信号 (0-4分)
        trend_score = 0
        if self.sma_short[0] > self.sma_medium[0]:
            trend_score += 1
        if self.sma_medium[0] > self.sma_long[0]:
            trend_score += 1
        if self.macd.macd[0] > self.macd.signal[0]:
            trend_score += 1
        if self.macd.histo[0] > 0:
            trend_score += 1
            
        self.lines.trend_signal[0] = trend_score
        
        # 2. 动量信号 (0-3分)
        momentum_score = 0
        if self.rsi[0] < 30:
            momentum_score += 1
        elif self.rsi[0] > 70:
            momentum_score -= 1
            
        if self.stochastic.percK[0] < 20:
            momentum_score += 1
        elif self.stochastic.percK[0] > 80:
            momentum_score -= 1
            
        # 将动量信号标准化到0-3
        self.lines.momentum_signal[0] = max(0, min(3, momentum_score + 1.5))
        
        # 3. 成交量信号 (0-2分)
        volume_score = 0
        if self.data.volume[0] > self.volume_sma[0] * self.p.volume_threshold:
            volume_score += 1
        # 价格与成交量确认
        if self.data.close[0] > self.data.close[-1] and self.data.volume[0] > self.volume_sma[0]:
            volume_score += 1
            
        self.lines.volume_signal[0] = volume_score
        
        # 4. 波动率信号 (0-2分)
        volatility_score = 0
        bb_position = (self.data.close[0] - self.bbands.bot[0]) / (self.bbands.top[0] - self.bbands.bot[0])
        
        if bb_position < 0.2:  # 接近下轨，超卖
            volatility_score += 2
        elif bb_position > 0.8:  # 接近上轨，超买
            volatility_score = 0
        else:
            volatility_score += 1
            
        self.lines.volatility_signal[0] = volatility_score
        
        # 综合信号评分 (0-11分，转换为0-10分)
        total_score = (self.lines.trend_signal[0] + 
                      self.lines.momentum_signal[0] + 
                      self.lines.volume_signal[0] + 
                      self.lines.volatility_signal[0])
        
        # 标准化到1-10分
        normalized_score = min(10, max(1, round((total_score / 11) * 9 + 1)))
        self.lines.signal_score[0] = normalized_score


class MultiDimensionalStrategy(bt.Strategy):
    """多维度信号交易策略"""
    
    params = (
        ('buy_threshold', 7),      # 买入信号阈值
        ('sell_threshold', 4),     # 卖出信号阈值  
        ('position_size', 0.3),    # 仓位大小
        ('stop_loss_pct', 0.05),   # 止损比例
        ('take_profit_pct', 0.10), # 止盈比例
        ('atr_multiplier', 2.0),   # ATR止损倍数
    )
    
    def __init__(self):
        # 多维度指标
        self.md_indicator = MultiDimensionalIndicator()
        
        # 基础指标
        self.rsi = bt.indicators.RSI()
        self.atr = bt.indicators.ATR()
        self.sma_20 = bt.indicators.SMA(period=20)
        
        # 记录变量
        self.order = None
        self.buy_price = None
        self.stop_price = None
        self.target_price = None
        
        # 性能统计
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0
        
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                # 设置动态止损价格
                atr_stop = self.atr[0] * self.p.atr_multiplier
                stop_loss = self.buy_price * self.p.stop_loss_pct
                self.stop_price = self.buy_price - max(atr_stop, stop_loss)
                self.target_price = self.buy_price * (1 + self.p.take_profit_pct)
                
                self.log(f'BUY 执行, 价格: {order.executed.price:.2f}, '
                        f'数量: {order.executed.size}, '
                        f'止损: {self.stop_price:.2f}, '
                        f'目标: {self.target_price:.2f}')
            else:
                pnl = order.executed.price - self.buy_price if self.buy_price else 0
                self.total_pnl += pnl
                self.trade_count += 1
                if pnl > 0:
                    self.win_count += 1
                    
                self.log(f'SELL 执行, 价格: {order.executed.price:.2f}, '
                        f'PnL: {pnl:.2f}, '
                        f'胜率: {self.win_count/self.trade_count*100:.1f}%')
                        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.status}')
            
        self.order = None
    
    def next(self):
        """策略逻辑"""
        
        if self.order:
            return
            
        current_price = self.data.close[0]
        signal_score = self.md_indicator.signal_score[0]
        
        # 如果持有仓位
        if self.position:
            # 止损检查
            if current_price <= self.stop_price:
                self.log(f'触发止损, 信号: {signal_score:.0f}/10, RSI: {self.rsi[0]:.1f}')
                self.order = self.sell()
                return
                
            # 止盈检查
            if current_price >= self.target_price:
                self.log(f'触发止盈, 信号: {signal_score:.0f}/10, RSI: {self.rsi[0]:.1f}')
                self.order = self.sell()
                return
                
            # 信号恶化卖出
            if signal_score <= self.p.sell_threshold:
                self.log(f'信号恶化卖出, 信号: {signal_score:.0f}/10, RSI: {self.rsi[0]:.1f}')
                self.order = self.sell()
                return
                
            # 动态止损调整
            if current_price > self.buy_price * 1.05:  # 盈利5%以上
                new_stop = max(self.stop_price, current_price * 0.98)  # 移动止损到2%
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
                    
        else:
            # 买入信号检查
            if signal_score >= self.p.buy_threshold:
                # 额外确认条件
                trend_signal = self.md_indicator.trend_signal[0]
                volume_signal = self.md_indicator.volume_signal[0]
                
                # 多重确认
                if (trend_signal >= 2 and                           # 趋势向上
                    volume_signal >= 1 and                         # 成交量确认
                    current_price > self.sma_20[0] and             # 价格在均线上方
                    self.rsi[0] > 30 and self.rsi[0] < 70):       # RSI合理区间
                    
                    # 计算仓位大小
                    size = int(self.broker.get_cash() * self.p.position_size / current_price)
                    
                    if size > 0:
                        self.log(f'BUY 信号触发, 信号: {signal_score:.0f}/10, '
                               f'趋势: {trend_signal:.0f}, 成交量: {volume_signal:.0f}, '
                               f'RSI: {self.rsi[0]:.1f}')
                        self.order = self.buy(size=size)
    
    def stop(self):
        """策略结束时的统计"""
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        win_rate = self.win_count / max(1, self.trade_count) * 100
        
        self.log('=' * 50)
        self.log(f'多维度策略统计:')
        self.log(f'总收益率: {total_return:.2f}%')
        self.log(f'最终价值: ${final_value:.2f}')
        self.log(f'交易次数: {self.trade_count}')
        self.log(f'胜率: {win_rate:.1f}%')
        self.log(f'平均盈亏: ${self.total_pnl/max(1, self.trade_count):.2f}')


def run_multi_dimensional_backtest(symbol='AAPL', days=252):
    """运行多维度策略回测"""
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MultiDimensionalStrategy)
    
    # 获取数据
    from src.data.yahoo_feed import YahooFinanceData
    
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    
    try:
        data_feed = YahooFinanceData(
            dataname=symbol,
            fromdate=start_date,
            todate=end_date,
            timeframe=bt.TimeFrame.Days
        )
        
        cerebro.adddata(data_feed)
        
    except Exception as e:
        print(f"数据获取失败: {e}")
        return None
    
    # 设置初始资金
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%手续费
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    print(f'🚀 多维度策略回测开始 - {symbol}')
    print(f'初始资金: ${cerebro.broker.getvalue():.2f}')
    
    # 运行回测
    results = cerebro.run()
    
    print(f'最终资金: ${cerebro.broker.getvalue():.2f}')
    
    # 分析结果
    strat = results[0]
    
    # 获取分析器结果
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    returns = strat.analyzers.returns.get_analysis()
    
    print(f'\n📊 详细统计:')
    print(f'夏普比率: {sharpe.get("sharperatio", 0):.3f}')
    print(f'最大回撤: {drawdown.get("max", {}).get("drawdown", 0):.2f}%')
    print(f'总交易: {trades.get("total", {}).get("total", 0)}')
    print(f'胜率: {trades.get("won", {}).get("total", 0) / max(1, trades.get("total", {}).get("total", 1)) * 100:.1f}%')
    
    return cerebro


if __name__ == '__main__':
    """运行多维度策略测试"""
    
    symbols = ['AAPL', 'MSTR', 'TSLA', 'NVDA']
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"测试股票: {symbol}")
        print(f"{'='*60}")
        
        cerebro = run_multi_dimensional_backtest(symbol, days=180)
        
        if cerebro:
            print(f"✅ {symbol} 多维度策略回测完成\n")
        else:
            print(f"❌ {symbol} 回测失败\n")