#!/usr/bin/env python3
"""
多时间框架Backtrader策略 - 简化版
Multi-Timeframe Backtrader Strategy - Simplified

集成多时间框架分析的专业交易策略，使用内置数据生成
"""

import backtrader as bt
import datetime
import random
import math
from enum import Enum

class TimeFrameStrength(Enum):
    """时间框架信号强度"""
    VERY_STRONG = 4
    STRONG = 3
    MODERATE = 2
    WEAK = 1
    NEUTRAL = 0

class MultiTimeFrameIndicator(bt.Indicator):
    """多时间框架指标"""
    
    lines = ('mtf_signal', 'trend_consistency', 'momentum_strength', 'overall_confidence')
    
    params = (
        ('fast_period', 10),
        ('slow_period', 20),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_stddev', 2.0),
    )
    
    def __init__(self):
        # 基础技术指标
        self.sma_fast = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.ema_12 = bt.indicators.EMA(self.data.close, period=12)
        self.ema_26 = bt.indicators.EMA(self.data.close, period=26)
        self.macd = self.ema_12 - self.ema_26
        
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        self.bbands = bt.indicators.BollingerBands(period=self.p.bb_period, devfactor=self.p.bb_stddev)
        self.atr = bt.indicators.ATR(period=14)
        
        # 成交量指标
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=10)
    
    def next(self):
        """计算多时间框架信号"""
        
        # 1. 趋势信号分析
        trend_score = 0
        
        # 移动平均线趋势
        if self.sma_fast[0] > self.sma_slow[0]:
            trend_score += 1
        if self.data.close[0] > self.sma_slow[0]:
            trend_score += 1
        
        # MACD趋势确认
        if self.macd[0] > 0:
            trend_score += 1
        
        # 价格动量
        if len(self) >= 5 and self.data.close[0] > self.data.close[-5]:
            trend_score += 1
        
        self.lines.trend_consistency[0] = trend_score
        
        # 2. 动量强度分析
        momentum_score = 0
        
        # RSI动量
        if 30 < self.rsi[0] < 70:
            momentum_score += 2  # 健康区间
        elif self.rsi[0] < 30:
            momentum_score += 3  # 超卖反弹机会
        elif self.rsi[0] > 70:
            momentum_score += 1  # 超买谨慎
        
        # 价格位置相对布林带
        bb_range = self.bbands.top[0] - self.bbands.bot[0]
        if bb_range > 0:
            bb_position = (self.data.close[0] - self.bbands.bot[0]) / bb_range
            
            if bb_position < 0.2:
                momentum_score += 2  # 接近下轨，反弹机会
            elif bb_position > 0.8:
                momentum_score -= 1  # 接近上轨，回调风险
            else:
                momentum_score += 1  # 中性区域
        
        # 成交量确认
        if len(self.volume_sma) > 0 and self.data.volume[0] > self.volume_sma[0] * 1.2:
            momentum_score += 1  # 放量确认
        
        self.lines.momentum_strength[0] = max(0, momentum_score)
        
        # 3. 综合多时间框架信号
        # 模拟不同时间框架权重
        short_term_weight = 1    # 短期(1H)权重
        medium_term_weight = 2   # 中期(4H)权重  
        long_term_weight = 3     # 长期(1D)权重
        
        # 长期趋势权重更高
        weighted_trend = (trend_score * long_term_weight) / 4
        weighted_momentum = (momentum_score * medium_term_weight) / 5
        
        # 综合信号强度 (0-10分)
        mtf_signal = min(10, max(0, (weighted_trend + weighted_momentum) * 2))
        self.lines.mtf_signal[0] = mtf_signal
        
        # 4. 整体置信度
        confidence = 0
        
        # 趋势一致性贡献
        if trend_score >= 3:
            confidence += 3
        elif trend_score >= 2:
            confidence += 2
        else:
            confidence += 1
        
        # 动量强度贡献
        momentum_score_val = self.lines.momentum_strength[0]
        if momentum_score_val >= 4:
            confidence += 3
        elif momentum_score_val >= 2:
            confidence += 2
        else:
            confidence += 1
            
        # 波动率调整
        if len(self.atr) > 0 and self.data.close[0] > 0:
            atr_pct = (self.atr[0] / self.data.close[0]) * 100
            if atr_pct < 2:  # 低波动率，信号更可靠
                confidence += 1
            elif atr_pct > 5:  # 高波动率，降低置信度
                confidence -= 1
        
        self.lines.overall_confidence[0] = max(1, min(7, confidence))

class MultiTimeFrameStrategy(bt.Strategy):
    """多时间框架交易策略"""
    
    params = (
        # 信号阈值参数
        ('buy_signal_threshold', 6.5),    # 买入信号阈值 (0-10)
        ('sell_signal_threshold', 4),     # 卖出信号阈值 (0-10)
        ('min_confidence', 4),            # 最低置信度要求 (1-7)
        
        # 仓位管理参数
        ('position_size_pct', 0.2),       # 基础仓位比例
        ('max_position_size', 0.5),       # 最大仓位比例
        
        # 风险管理参数
        ('stop_loss_pct', 0.08),          # 止损比例
        ('take_profit_pct', 0.15),        # 止盈比例
        ('trailing_stop_pct', 0.05),      # 移动止损比例
        
        # 多时间框架参数
        ('trend_consistency_min', 2),     # 最小趋势一致性要求
        ('momentum_threshold', 2),        # 动量强度阈值
    )
    
    def __init__(self):
        # 多时间框架指标
        self.mtf_indicator = MultiTimeFrameIndicator()
        
        # 基础技术指标
        self.sma_20 = bt.indicators.SMA(period=20)
        self.sma_50 = bt.indicators.SMA(period=50)
        self.rsi = bt.indicators.RSI()
        self.atr = bt.indicators.ATR()
        self.bbands = bt.indicators.BollingerBands()
        
        # 交易状态变量
        self.order = None
        self.buy_price = None
        self.stop_price = None
        self.target_price = None
        
        # 性能统计
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0
        
        # 信号历史记录
        self.signal_history = []
        
    def log(self, txt, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                
                # 动态止损计算
                atr_stop = self.atr[0] * 2.5 if len(self.atr) > 0 else self.buy_price * 0.05
                pct_stop = self.buy_price * self.p.stop_loss_pct
                self.stop_price = self.buy_price - max(atr_stop, pct_stop)
                
                # 动态止盈计算
                signal_strength = self.mtf_indicator.mtf_signal[0]
                if signal_strength >= 8:
                    profit_multiplier = 2.0  # 强信号，更大止盈
                else:
                    profit_multiplier = 1.5
                
                self.target_price = self.buy_price * (1 + self.p.take_profit_pct * profit_multiplier)
                
                self.log(f'买入执行: ${order.executed.price:.2f}, 数量: {order.executed.size}')
                self.log(f'止损: ${self.stop_price:.2f}, 止盈: ${self.target_price:.2f}')
                
            else:  # 卖出
                pnl = order.executed.price - self.buy_price if self.buy_price else 0
                self.total_pnl += pnl
                self.trade_count += 1
                
                if pnl > 0:
                    self.win_count += 1
                    
                win_rate = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0
                
                self.log(f'卖出执行: ${order.executed.price:.2f}')
                self.log(f'盈亏: ${pnl:.2f}, 累计: ${self.total_pnl:.2f}')
                self.log(f'胜率: {win_rate:.1f}% ({self.win_count}/{self.trade_count})')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.status}')
            
        self.order = None
    
    def next(self):
        """策略主逻辑"""
        
        # 避免重复订单
        if self.order:
            return
        
        # 确保有足够的历史数据
        if len(self) < 50:
            return
        
        # 获取多时间框架信号
        mtf_signal = self.mtf_indicator.mtf_signal[0]
        trend_consistency = self.mtf_indicator.trend_consistency[0]
        momentum_strength = self.mtf_indicator.momentum_strength[0]
        confidence = self.mtf_indicator.overall_confidence[0]
        
        current_price = self.data.close[0]
        
        # 记录信号历史
        signal_data = {
            'date': self.data.datetime.date(0),
            'price': current_price,
            'mtf_signal': mtf_signal,
            'trend_consistency': trend_consistency,
            'momentum_strength': momentum_strength,
            'confidence': confidence
        }
        self.signal_history.append(signal_data)
        
        # 持仓管理
        if self.position:
            # 移动止损
            if self.buy_price and current_price > self.buy_price * 1.1:  # 盈利10%以上
                new_stop = current_price * (1 - self.p.trailing_stop_pct)
                self.stop_price = max(self.stop_price, new_stop)
            
            # 止损检查
            if current_price <= self.stop_price:
                self.log(f'触发止损: 信号={mtf_signal:.1f}, 置信度={confidence:.1f}')
                self.order = self.sell()
                return
            
            # 止盈检查
            if current_price >= self.target_price:
                self.log(f'触发止盈: 信号={mtf_signal:.1f}, 置信度={confidence:.1f}')
                self.order = self.sell()
                return
            
            # 信号恶化卖出
            if (mtf_signal <= self.p.sell_signal_threshold and 
                confidence >= self.p.min_confidence):
                self.log(f'信号恶化卖出: 信号={mtf_signal:.1f}, 趋势={trend_consistency}')
                self.order = self.sell()
                return
        
        else:
            # 买入条件检查
            if (mtf_signal >= self.p.buy_signal_threshold and 
                confidence >= self.p.min_confidence and
                trend_consistency >= self.p.trend_consistency_min and
                momentum_strength >= self.p.momentum_threshold):
                
                # 额外确认条件
                additional_checks = []
                
                if len(self.sma_20) > 0:
                    additional_checks.append(current_price > self.sma_20[0])  # 价格在20日均线上方
                
                if len(self.sma_20) > 0 and len(self.sma_50) > 0:
                    additional_checks.append(self.sma_20[0] > self.sma_50[0])  # 短期均线>长期均线
                
                if len(self.rsi) > 0:
                    additional_checks.append(30 < self.rsi[0] < 80)  # RSI在合理区间
                
                if len(self.bbands.bot) > 0:
                    additional_checks.append(current_price > self.bbands.bot[0])  # 价格在布林带下轨上方
                
                confirmed_signals = sum(additional_checks)
                
                if confirmed_signals >= 2:  # 至少2个额外确认
                    # 动态仓位计算
                    base_size_pct = self.p.position_size_pct
                    
                    # 根据信号强度调整仓位
                    if mtf_signal >= 9:
                        size_multiplier = 2.0
                    elif mtf_signal >= 8:
                        size_multiplier = 1.5
                    else:
                        size_multiplier = 1.0
                    
                    # 根据置信度调整
                    if confidence >= 6:
                        confidence_multiplier = 1.2
                    else:
                        confidence_multiplier = 1.0
                    
                    final_size_pct = min(self.p.max_position_size, 
                                       base_size_pct * size_multiplier * confidence_multiplier)
                    
                    # 计算购买数量
                    available_cash = self.broker.get_cash()
                    target_value = available_cash * final_size_pct
                    size = int(target_value / current_price)
                    
                    if size > 0:
                        self.log(f'多时间框架买入信号触发:')
                        self.log(f'  信号强度: {mtf_signal:.1f}/10')
                        self.log(f'  趋势一致性: {trend_consistency}/4')
                        self.log(f'  动量强度: {momentum_strength}')
                        self.log(f'  置信度: {confidence}/7')
                        self.log(f'  确认条件: {confirmed_signals}/{len(additional_checks)}')
                        self.log(f'  仓位比例: {final_size_pct:.1%}')
                        
                        self.order = self.buy(size=size)
    
    def stop(self):
        """策略结束统计"""
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        self.log('=' * 60)
        self.log('多时间框架策略统计报告:')
        self.log(f'初始资金: $10,000.00')
        self.log(f'最终价值: ${final_value:.2f}')
        self.log(f'总收益率: {total_return:.2f}%')
        self.log(f'总交易数: {self.trade_count}')
        
        if self.trade_count > 0:
            win_rate = self.win_count / self.trade_count * 100
            avg_pnl = self.total_pnl / self.trade_count
            self.log(f'胜率: {win_rate:.1f}% ({self.win_count}/{self.trade_count})')
            self.log(f'平均每笔: ${avg_pnl:.2f}')
            
            # 信号质量分析
            if len(self.signal_history) > 0:
                recent_signals = self.signal_history[-50:]
                avg_signal = sum(s['mtf_signal'] for s in recent_signals) / len(recent_signals)
                avg_confidence = sum(s['confidence'] for s in recent_signals) / len(recent_signals)
                self.log(f'平均信号强度: {avg_signal:.1f}/10')
                self.log(f'平均置信度: {avg_confidence:.1f}/7')
        
        self.log('=' * 60)

def generate_realistic_stock_data(symbol='STOCK', days=252, initial_price=100.0):
    """生成逼真的股票数据"""
    
    dates = []
    data_points = []
    
    current_price = initial_price
    trend = 0.0  # 趋势方向
    volatility = 0.02  # 基础波动率
    
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    for i in range(days):
        # 跳过周末
        current_date = start_date + datetime.timedelta(days=i)
        if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            continue
            
        dates.append(current_date)
        
        # 趋势变化
        if random.random() < 0.05:  # 5%概率改变趋势
            trend = random.gauss(0, 0.001)
        
        # 基础价格变动
        daily_return = trend + random.gauss(0, volatility)
        
        # 添加一些市场特征
        # 周一效应
        if current_date.weekday() == 0:
            daily_return *= 0.8
        
        # 月末效应
        if current_date.day >= 28:
            daily_return *= 1.1
        
        # 计算OHLCV
        open_price = current_price * (1 + random.gauss(0, 0.005))
        
        # 当日高低点
        high_volatility = abs(daily_return) * 2 + random.uniform(0.005, 0.02)
        low_volatility = abs(daily_return) * 2 + random.uniform(0.005, 0.02)
        
        high_price = max(open_price, current_price) * (1 + high_volatility)
        low_price = min(open_price, current_price) * (1 - low_volatility)
        
        # 收盘价
        close_price = current_price * (1 + daily_return)
        close_price = max(low_price, min(high_price, close_price))
        
        # 成交量 (基于波动率)
        base_volume = 1000000
        volume_multiplier = 1 + abs(daily_return) * 10  # 波动越大成交量越大
        volume = int(base_volume * volume_multiplier * random.uniform(0.5, 2.0))
        
        data_points.append({
            'datetime': current_date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
        
        current_price = close_price
    
    return data_points

def run_multi_timeframe_backtest(symbol='AAPL', days=252):
    """运行多时间框架策略回测"""
    
    cerebro = bt.Cerebro()
    
    # 添加多时间框架策略
    cerebro.addstrategy(
        MultiTimeFrameStrategy,
        buy_signal_threshold=6.5,
        sell_signal_threshold=4,
        min_confidence=4,
        position_size_pct=0.25,
        stop_loss_pct=0.08,
        take_profit_pct=0.15
    )
    
    # 生成模拟数据
    print(f"📊 生成 {symbol} 模拟数据 ({days} 天)")
    stock_data = generate_realistic_stock_data(symbol, days, random.uniform(80, 200))
    
    # 创建数据源
    class CustomData(bt.feeds.PandasData):
        lines = ('datetime', 'open', 'high', 'low', 'close', 'volume')
        
        def __init__(self):
            # 转换为pandas DataFrame
            try:
                import pandas as pd
                df = pd.DataFrame(stock_data)
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
                super().__init__(dataname=df)
            except ImportError:
                # 如果没有pandas，使用基础数据源
                super().__init__()
                self._data = stock_data
                self._idx = 0
                
        def _load(self):
            if hasattr(self, '_data'):
                if self._idx >= len(self._data):
                    return False
                
                point = self._data[self._idx]
                self.lines.datetime[0] = bt.date2num(point['datetime'])
                self.lines.open[0] = point['open']
                self.lines.high[0] = point['high'] 
                self.lines.low[0] = point['low']
                self.lines.close[0] = point['close']
                self.lines.volume[0] = point['volume']
                
                self._idx += 1
                return True
            return super()._load()
    
    # 使用简单的数据添加方法
    try:
        cerebro.adddata(CustomData())
    except:
        # 最后的备选方案 - 使用最基础的数据
        print("使用基础模拟数据")
        for i, point in enumerate(stock_data[:min(100, len(stock_data))]):
            if i == 0:
                # 只添加第一个数据点作为示例
                data = bt.feeds.GenericCSVData(
                    dataname=None,
                    name=symbol,
                    datetime=0,
                    open=1, high=2, low=3, close=4, volume=5,
                    dtformat='%Y-%m-%d',
                    fromdate=datetime.datetime.now() - datetime.timedelta(days=100),
                    todate=datetime.datetime.now()
                )
                cerebro.adddata(data)
                break
    
    # 设置初始资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%手续费
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    print(f'🚀 多时间框架策略回测 - {symbol}')
    print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
    
    # 运行策略
    results = cerebro.run()
    
    # 分析结果
    if results:
        strat = results[0]
        
        # 获取分析器结果
        try:
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.trades.get_analysis()
            
            print(f'\n📊 详细分析报告:')
            sharpe_ratio = sharpe.get('sharperatio', 0)
            if sharpe_ratio and not math.isnan(sharpe_ratio):
                print(f'夏普比率: {sharpe_ratio:.2f}')
            else:
                print('夏普比率: N/A')
                
            max_dd = drawdown.get('max', {}).get('drawdown', 0)
            print(f'最大回撤: {max_dd:.2f}%')
            
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            print(f'总交易数: {total_trades}')
            
            if total_trades > 0:
                win_rate = (won_trades / total_trades) * 100
                print(f'胜率: {win_rate:.1f}%')
                
        except Exception as e:
            print(f'分析器结果获取部分失败: {e}')
    
    print(f'💰 最终资金: ${cerebro.broker.getvalue():.2f}')
    
    return cerebro

if __name__ == '__main__':
    """运行多时间框架策略测试"""
    
    import sys
    
    # 测试股票列表
    test_symbols = ['AAPL', 'MSTR', 'TSLA', 'NVDA'] if len(sys.argv) <= 1 else [sys.argv[1].upper()]
    
    for symbol in test_symbols:
        print(f"\n{'='*80}")
        print(f"🔍 多时间框架策略回测 - {symbol}")
        print(f"{'='*80}")
        
        try:
            cerebro = run_multi_timeframe_backtest(symbol, days=180)
            print(f"✅ {symbol} 多时间框架策略回测完成")
        except Exception as e:
            print(f"❌ {symbol} 回测失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 多时间框架策略测试完成！")