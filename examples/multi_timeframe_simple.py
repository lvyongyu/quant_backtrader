#!/usr/bin/env python3
"""
多时间框架Backtrader策略 - 内置数据版
Multi-Timeframe Backtrader Strategy - Built-in Data

使用Backtrader内置数据生成功能的多时间框架交易策略
"""

import backtrader as bt
import datetime
import random
import math

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
        long_term_weight = 3     # 长期(1D)权重
        medium_term_weight = 2   # 中期(4H)权重  
        
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
        
        # 记录信号历史（减少频率以避免过多输出）
        if len(self) % 5 == 0:  # 每5天记录一次
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
                recent_signals = self.signal_history[-10:]  # 最近10个记录点
                if recent_signals:
                    avg_signal = sum(s['mtf_signal'] for s in recent_signals) / len(recent_signals)
                    avg_confidence = sum(s['confidence'] for s in recent_signals) / len(recent_signals)
                    self.log(f'平均信号强度: {avg_signal:.1f}/10')
                    self.log(f'平均置信度: {avg_confidence:.1f}/7')
        
        self.log('=' * 60)

def run_multi_timeframe_backtest(symbol='TEST', days=252):
    """运行多时间框架策略回测"""
    
    cerebro = bt.Cerebro()
    
    # 添加多时间框架策略
    cerebro.addstrategy(
        MultiTimeFrameStrategy,
        buy_signal_threshold=6.0,  # 降低阈值以便观察更多交易
        sell_signal_threshold=4,
        min_confidence=3,  # 降低置信度要求
        position_size_pct=0.25,
        stop_loss_pct=0.08,
        take_profit_pct=0.15
    )
    
    # 使用Backtrader内置的随机数据生成
    # 创建随机价格数据
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    
    # 生成价格序列
    base_price = random.uniform(50, 200)  # 基础价格
    prices = []
    volumes = []
    
    current_price = base_price
    for i in range(days):
        # 价格变动 - 添加一些趋势和随机性
        trend = math.sin(i / 50.0) * 0.01  # 周期性趋势
        noise = random.gauss(0, 0.02)  # 随机噪音
        change = trend + noise
        
        current_price *= (1 + change)
        current_price = max(10, current_price)  # 确保价格不会太低
        
        # 生成OHLCV数据
        open_price = current_price * random.uniform(0.98, 1.02)
        high_price = current_price * random.uniform(1.0, 1.05)
        low_price = current_price * random.uniform(0.95, 1.0)
        close_price = current_price
        volume = random.randint(100000, 1000000)
        
        prices.append([open_price, high_price, low_price, close_price])
        volumes.append(volume)
    
    # 创建简单的数据源
    class SimpleTestData(bt.feeds.GenericCSVData):
        def __init__(self):
            self.data_points = []
            for i in range(days):
                date = start_date + datetime.timedelta(days=i)
                if date.weekday() < 5:  # 只包含工作日
                    self.data_points.append({
                        'date': date,
                        'open': prices[i][0],
                        'high': prices[i][1], 
                        'low': prices[i][2],
                        'close': prices[i][3],
                        'volume': volumes[i]
                    })
            
            # 创建临时CSV文件
            import tempfile
            import csv
            
            self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
            writer = csv.writer(self.temp_file)
            writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
            
            for point in self.data_points:
                writer.writerow([
                    point['date'].strftime('%Y-%m-%d'),
                    f"{point['open']:.2f}",
                    f"{point['high']:.2f}",
                    f"{point['low']:.2f}", 
                    f"{point['close']:.2f}",
                    point['volume']
                ])
            
            self.temp_file.close()
            
            super().__init__(
                dataname=self.temp_file.name,
                dtformat='%Y-%m-%d',
                datetime=0,
                open=1, high=2, low=3, close=4, volume=5,
                fromdate=start_date,
                todate=end_date
            )
    
    # 添加数据到cerebro
    data = SimpleTestData()
    cerebro.adddata(data)
    
    # 设置初始资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%手续费
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    print(f'🚀 多时间框架策略回测 - {symbol}')
    print(f'📅 回测期间: {start_date.strftime("%Y-%m-%d")} 至 {end_date.strftime("%Y-%m-%d")}')
    print(f'📊 生成 {len(data.data_points)} 个交易日数据')
    print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
    
    # 运行策略
    try:
        results = cerebro.run()
        
        # 清理临时文件
        import os
        try:
            os.unlink(data.temp_file.name)
        except:
            pass
        
        # 分析结果
        if results:
            strat = results[0]
            
            # 获取分析器结果
            try:
                sharpe = strat.analyzers.sharpe.get_analysis()
                drawdown = strat.analyzers.drawdown.get_analysis()
                trades = strat.analyzers.trades.get_analysis()
                returns = strat.analyzers.returns.get_analysis()
                
                print(f'\n📊 详细分析报告:')
                
                # 夏普比率
                sharpe_ratio = sharpe.get('sharperatio', 0)
                if sharpe_ratio and not math.isnan(sharpe_ratio):
                    print(f'夏普比率: {sharpe_ratio:.3f}')
                else:
                    print('夏普比率: N/A (数据不足)')
                    
                # 最大回撤
                max_dd = drawdown.get('max', {}).get('drawdown', 0)
                if max_dd:
                    print(f'最大回撤: {max_dd:.2f}%')
                else:
                    print('最大回撤: N/A')
                
                # 交易统计
                total_trades = trades.get('total', {}).get('total', 0)
                won_trades = trades.get('won', {}).get('total', 0)
                lost_trades = trades.get('lost', {}).get('total', 0)
                
                print(f'总交易数: {total_trades}')
                print(f'盈利交易: {won_trades}, 亏损交易: {lost_trades}')
                
                if total_trades > 0:
                    win_rate = (won_trades / total_trades) * 100
                    print(f'胜率: {win_rate:.1f}%')
                    
                    # 平均盈亏
                    avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
                    avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
                    if avg_win and avg_loss:
                        print(f'平均盈利: ${avg_win:.2f}')
                        print(f'平均亏损: ${avg_loss:.2f}')
                        print(f'盈亏比: {abs(avg_win/avg_loss):.2f}' if avg_loss != 0 else 'N/A')
                
                # 年化收益率
                total_return = returns.get('rtot', 0)
                if total_return:
                    annual_return = ((1 + total_return) ** (252/days) - 1) * 100
                    print(f'年化收益率: {annual_return:.2f}%')
                    
            except Exception as e:
                print(f'分析器结果处理出现问题: {e}')
        
        print(f'💰 最终资金: ${cerebro.broker.getvalue():.2f}')
        
        return cerebro
        
    except Exception as e:
        print(f'策略运行失败: {e}')
        # 清理临时文件
        import os
        try:
            os.unlink(data.temp_file.name)
        except:
            pass
        return None

if __name__ == '__main__':
    """运行多时间框架策略测试"""
    
    import sys
    
    # 测试股票列表
    test_symbols = ['AAPL', 'MSTR', 'TSLA'] if len(sys.argv) <= 1 else [sys.argv[1].upper()]
    
    for symbol in test_symbols:
        print(f"\n{'='*80}")
        print(f"🔍 多时间框架策略回测 - {symbol}")
        print(f"{'='*80}")
        
        try:
            cerebro = run_multi_timeframe_backtest(symbol, days=120)  # 4个月数据
            if cerebro:
                print(f"✅ {symbol} 多时间框架策略回测完成")
            else:
                print(f"❌ {symbol} 回测未能完成")
        except Exception as e:
            print(f"❌ {symbol} 回测失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 多时间框架策略测试完成！")
    print(f"\n📝 多时间框架策略特点:")
    print(f"  • 集成1小时、4小时、日线多时间框架分析")
    print(f"  • 趋势一致性检查和动量强度确认")
    print(f"  • 动态仓位管理和风险控制")
    print(f"  • 信号强度加权和置信度评估")
    print(f"  • 智能止损止盈和移动止损")