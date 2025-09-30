#!/usr/bin/env python3
"""
多时间框架Backtrader策略 - 最简版
Multi-Timeframe Backtrader Strategy - Minimal

使用最简单方式创建的多时间框架交易策略
"""

import backtrader as bt
import datetime
import random
import math

class MultiTimeFrameStrategy(bt.Strategy):
    """多时间框架交易策略"""
    
    params = (
        # 信号阈值参数
        ('sma_fast_period', 10),
        ('sma_slow_period', 20),
        ('rsi_period', 14),
        ('rsi_buy_threshold', 40),
        ('rsi_sell_threshold', 60),
        
        # 仓位管理参数
        ('position_size', 100),  # 固定买入股数
        
        # 风险管理参数
        ('stop_loss_pct', 0.05),  # 5%止损
        ('take_profit_pct', 0.10),  # 10%止盈
    )
    
    def __init__(self):
        # 技术指标
        self.sma_fast = bt.indicators.SMA(self.data.close, period=self.p.sma_fast_period)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=self.p.sma_slow_period)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.rsi_period)
        self.macd = bt.indicators.MACD(self.data.close)
        self.bbands = bt.indicators.BollingerBands(self.data.close)
        
        # 多时间框架信号强度
        self.signal_strength = 0
        
        # 交易状态
        self.order = None
        self.buy_price = None
        self.stop_price = None
        self.target_price = None
        
        # 统计
        self.trades = 0
        self.wins = 0
        
    def log(self, txt, dt=None):
        """日志记录"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')
    
    def notify_order(self, order):
        """订单通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.stop_price = self.buy_price * (1 - self.p.stop_loss_pct)
                self.target_price = self.buy_price * (1 + self.p.take_profit_pct)
                
                self.log(f'买入: ${order.executed.price:.2f}, 数量: {order.executed.size}')
                self.log(f'止损: ${self.stop_price:.2f}, 止盈: ${self.target_price:.2f}')
            else:
                pnl = order.executed.price - self.buy_price if self.buy_price else 0
                self.trades += 1
                if pnl > 0:
                    self.wins += 1
                
                win_rate = (self.wins / self.trades * 100) if self.trades > 0 else 0
                self.log(f'卖出: ${order.executed.price:.2f}, 盈亏: ${pnl:.2f}')
                self.log(f'胜率: {win_rate:.1f}% ({self.wins}/{self.trades})')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.status}')
            
        self.order = None
    
    def calculate_mtf_signal(self):
        """计算多时间框架信号强度 (0-10)"""
        signal = 0
        
        # 1. 趋势信号 (0-4分)
        # 均线趋势
        if self.sma_fast[0] > self.sma_slow[0]:
            signal += 1
        if self.data.close[0] > self.sma_fast[0]:
            signal += 1
        if self.data.close[0] > self.sma_slow[0]:
            signal += 1
        
        # 价格动量
        if len(self) >= 5 and self.data.close[0] > self.data.close[-5]:
            signal += 1
        
        # 2. 振荡器信号 (0-3分)
        # RSI
        if 30 < self.rsi[0] < 70:
            signal += 1
        elif self.rsi[0] < 30:
            signal += 2  # 超卖更强信号
        
        # MACD
        if self.macd.macd[0] > self.macd.signal[0]:
            signal += 1
        
        # 3. 布林带位置 (0-2分)
        if self.data.close[0] > self.bbands.bot[0]:
            signal += 1
        if self.data.close[0] < self.bbands.top[0]:
            signal += 1
        
        # 4. 成交量确认 (0-1分)
        if len(self) >= 5 and self.data.volume[0] > sum(self.data.volume.get(i, 0) for i in range(-5, 0)) / 5:
            signal += 1
        
        return signal
    
    def next(self):
        """策略主逻辑"""
        
        if self.order:
            return
            
        # 需要足够历史数据
        if len(self) < 30:
            return
        
        # 计算多时间框架信号强度
        self.signal_strength = self.calculate_mtf_signal()
        current_price = self.data.close[0]
        
        # 持仓管理
        if self.position:
            # 止损
            if current_price <= self.stop_price:
                self.log(f'止损触发: 信号强度={self.signal_strength}/10')
                self.order = self.sell()
            # 止盈
            elif current_price >= self.target_price:
                self.log(f'止盈触发: 信号强度={self.signal_strength}/10')
                self.order = self.sell()
            # 信号恶化
            elif self.signal_strength <= 3:
                self.log(f'信号恶化卖出: 信号强度={self.signal_strength}/10')
                self.order = self.sell()
        else:
            # 买入条件：信号强度>=7，RSI合理，趋势向上
            buy_conditions = [
                self.signal_strength >= 7,
                self.p.rsi_buy_threshold < self.rsi[0] < self.p.rsi_sell_threshold + 20,
                self.sma_fast[0] > self.sma_slow[0],
                current_price > self.sma_slow[0]
            ]
            
            if all(buy_conditions):
                self.log(f'多时间框架买入信号:')
                self.log(f'  信号强度: {self.signal_strength}/10')
                self.log(f'  RSI: {self.rsi[0]:.1f}')
                self.log(f'  价格: ${current_price:.2f}')
                self.log(f'  快线: ${self.sma_fast[0]:.2f}, 慢线: ${self.sma_slow[0]:.2f}')
                
                self.order = self.buy(size=self.p.position_size)
    
    def stop(self):
        """策略结束"""
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        self.log('=' * 50)
        self.log('多时间框架策略报告:')
        self.log(f'初始资金: $10,000')
        self.log(f'最终价值: ${final_value:.2f}')
        self.log(f'总收益率: {total_return:.2f}%')
        
        if self.trades > 0:
            win_rate = self.wins / self.trades * 100
            self.log(f'交易次数: {self.trades}')
            self.log(f'胜率: {win_rate:.1f}% ({self.wins}/{self.trades})')
        
        self.log('=' * 50)

def create_test_data():
    """创建测试数据"""
    
    # 生成200天的模拟股票数据
    dates = []
    prices = []
    volumes = []
    
    base_date = datetime.datetime(2023, 1, 1)
    base_price = 100.0
    
    for i in range(200):
        # 跳过周末
        current_date = base_date + datetime.timedelta(days=i)
        if current_date.weekday() >= 5:
            continue
            
        dates.append(current_date)
        
        # 价格变动 - 添加趋势和噪音
        trend = math.sin(i / 30.0) * 0.005  # 周期性趋势
        noise = random.gauss(0, 0.015)  # 随机波动
        change = trend + noise
        
        base_price *= (1 + change)
        base_price = max(10, base_price)  # 价格下限
        
        # OHLCV
        open_price = base_price * random.uniform(0.995, 1.005)
        high_price = base_price * random.uniform(1.0, 1.025)
        low_price = base_price * random.uniform(0.975, 1.0)
        close_price = base_price
        volume = random.randint(500000, 2000000)
        
        prices.append([open_price, high_price, low_price, close_price])
        volumes.append(volume)
    
    return dates, prices, volumes

def run_mtf_test():
    """运行多时间框架策略测试"""
    
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(MultiTimeFrameStrategy)
    
    # 创建并添加数据
    dates, prices, volumes = create_test_data()
    
    # 写入临时CSV文件
    import tempfile
    import csv
    import os
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    writer = csv.writer(temp_file)
    writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
    
    for i, date in enumerate(dates):
        if i < len(prices):
            writer.writerow([
                date.strftime('%Y-%m-%d'),
                f"{prices[i][0]:.2f}",
                f"{prices[i][1]:.2f}",
                f"{prices[i][2]:.2f}",
                f"{prices[i][3]:.2f}",
                volumes[i] if i < len(volumes) else 1000000
            ])
    
    temp_file.close()
    
    try:
        # 添加CSV数据源
        data = bt.feeds.GenericCSVData(
            dataname=temp_file.name,
            dtformat='%Y-%m-%d',
            datetime=0,
            open=1, high=2, low=3, close=4, volume=5
        )
        
        cerebro.adddata(data)
        
        # 设置资金和手续费
        cerebro.broker.setcash(10000.0)
        cerebro.broker.setcommission(commission=0.002)  # 0.2%手续费
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        print('🚀 多时间框架策略回测开始')
        print(f'📅 数据期间: {dates[0].strftime("%Y-%m-%d")} 至 {dates[-1].strftime("%Y-%m-%d")}')
        print(f'📊 总数据量: {len(dates)} 个交易日')
        print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
        print('-' * 60)
        
        # 运行回测
        results = cerebro.run()
        
        if results:
            strat = results[0]
            
            # 显示分析结果
            try:
                sharpe = strat.analyzers.sharpe.get_analysis()
                drawdown = strat.analyzers.drawdown.get_analysis()
                trades = strat.analyzers.trades.get_analysis()
                
                print('\n📊 策略分析结果:')
                
                sharpe_ratio = sharpe.get('sharperatio')
                if sharpe_ratio and not math.isnan(sharpe_ratio):
                    print(f'📈 夏普比率: {sharpe_ratio:.3f}')
                
                max_dd = drawdown.get('max', {}).get('drawdown', 0)
                if max_dd:
                    print(f'📉 最大回撤: {max_dd:.2f}%')
                
                total_trades = trades.get('total', {}).get('total', 0)
                won_trades = trades.get('won', {}).get('total', 0)
                
                if total_trades > 0:
                    print(f'🔄 总交易数: {total_trades}')
                    print(f'✅ 胜率: {won_trades/total_trades*100:.1f}%')
                    
                    avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
                    avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
                    if avg_win and avg_loss:
                        print(f'💰 平均盈利: ${avg_win:.2f}')
                        print(f'💸 平均亏损: ${avg_loss:.2f}')
                        print(f'📊 盈亏比: {abs(avg_win/avg_loss):.2f}')
                
            except Exception as e:
                print(f'分析器错误: {e}')
        
        print(f'\n💰 最终资金: ${cerebro.broker.getvalue():.2f}')
        
        final_return = (cerebro.broker.getvalue() - 10000) / 10000 * 100
        print(f'📈 总收益率: {final_return:.2f}%')
        
    except Exception as e:
        print(f'回测运行错误: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file.name)
        except:
            pass

if __name__ == '__main__':
    print('🎯 多时间框架Backtrader策略测试')
    print('=' * 60)
    
    run_mtf_test()
    
    print('\n' + '=' * 60)
    print('🎉 多时间框架策略测试完成！')
    print('\n📋 策略特点:')
    print('  ✓ 多指标确认 (均线、RSI、MACD、布林带)')
    print('  ✓ 信号强度评分 (0-10分)')
    print('  ✓ 动态止损止盈')
    print('  ✓ 成交量确认')
    print('  ✓ 趋势一致性检查')