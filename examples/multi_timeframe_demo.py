#!/usr/bin/env python3
"""
多时间框架Backtrader策略 - 演示版
Multi-Timeframe Backtrader Strategy Demo

使用Backtrader内置数据演示多时间框架策略
"""

import backtrader as bt
import datetime

class MultiTimeFrameStrategy(bt.Strategy):
    """多时间框架交易策略"""
    
    params = (
        ('sma_fast', 10),
        ('sma_slow', 20), 
        ('rsi_period', 14),
        ('signal_threshold', 6),
        ('printlog', True),
    )
    
    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}: {txt}')
    
    def __init__(self):
        # 保存数据引用
        self.dataclose = self.datas[0].close
        
        # 跟踪待处理订单
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # 添加技术指标
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_fast)
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_slow)
        
        self.rsi = bt.indicators.RelativeStrengthIndex(
            period=self.params.rsi_period)
        
        self.macd = bt.indicators.MACD(self.datas[0])
        self.bbands = bt.indicators.BollingerBands(self.datas[0])
        
        # 统计变量
        self.trade_count = 0
        self.win_count = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单提交/接受 - 无需处理
            return

        # 检查订单是否完成
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'买入执行, 价格: {order.executed.price:.2f}, '
                    f'费用: {order.executed.comm:.2f}, '
                    f'数量: {order.executed.size}')

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # 卖出
                self.trade_count += 1
                pnl = order.executed.price - self.buyprice - self.buycomm
                if pnl > 0:
                    self.win_count += 1
                
                win_rate = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0
                
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}, '
                        f'费用: {order.executed.comm:.2f}, '
                        f'盈亏: {pnl:.2f}')
                self.log(f'胜率: {win_rate:.1f}% ({self.win_count}/{self.trade_count})')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')

        # 订单完成，置空
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'操作利润, 毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}')

    def get_signal_strength(self):
        """计算多时间框架信号强度 (0-10分)"""
        signal = 0
        
        # 1. 趋势信号 (最多4分)
        if self.sma_fast[0] > self.sma_slow[0]:
            signal += 2  # 快线在慢线上方
        if self.dataclose[0] > self.sma_fast[0]:
            signal += 1  # 价格在快线上方
        if self.dataclose[0] > self.sma_slow[0]:
            signal += 1  # 价格在慢线上方
        
        # 2. RSI信号 (最多3分)
        if 30 < self.rsi[0] < 70:
            signal += 1  # RSI在健康区间
        elif self.rsi[0] < 30:
            signal += 3  # 超卖，强烈买入信号
        elif self.rsi[0] < 40:
            signal += 2  # 接近超卖
        
        # 3. MACD信号 (最多2分)
        if self.macd.macd[0] > self.macd.signal[0]:
            signal += 2  # MACD线在信号线上方
        elif self.macd.macd[0] > 0:
            signal += 1  # MACD为正
        
        # 4. 布林带位置 (最多1分)
        bb_position = (self.dataclose[0] - self.bbands.bot[0]) / (self.bbands.top[0] - self.bbands.bot[0]) if self.bbands.top[0] != self.bbands.bot[0] else 0.5
        if 0.2 < bb_position < 0.8:
            signal += 1  # 在布林带中部，相对安全
        
        return min(10, signal)

    def next(self):
        # 简单记录收盘价
        # self.log(f'收盘价, {self.dataclose[0]:.2f}')

        # 检查是否有待处理订单
        if self.order:
            return

        # 计算多时间框架信号强度
        signal_strength = self.get_signal_strength()

        # 如果没有持仓
        if not self.position:
            # 买入条件：信号强度足够高
            if signal_strength >= self.params.signal_threshold:
                self.log(f'多时间框架买入信号触发!')
                self.log(f'信号强度: {signal_strength}/10')
                self.log(f'RSI: {self.rsi[0]:.2f}')
                self.log(f'快线: {self.sma_fast[0]:.2f}, 慢线: {self.sma_slow[0]:.2f}')
                self.log(f'MACD: {self.macd.macd[0]:.4f}, 信号: {self.macd.signal[0]:.4f}')

                # 买入
                self.order = self.buy()

        else:
            # 已经持仓，检查卖出条件
            
            # 卖出条件1：信号强度显著下降
            if signal_strength <= 3:
                self.log(f'信号恶化，卖出! 信号强度: {signal_strength}/10')
                self.order = self.sell()
            
            # 卖出条件2：价格跌破慢线
            elif self.dataclose[0] < self.sma_slow[0]:
                self.log(f'跌破慢线，止损卖出!')
                self.order = self.sell()
            
            # 卖出条件3：RSI过高
            elif self.rsi[0] > 75:
                self.log(f'RSI过高，获利了结! RSI: {self.rsi[0]:.2f}')
                self.order = self.sell()

    def stop(self):
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        self.log('=' * 60, doprint=True)
        self.log('多时间框架策略结果报告:', doprint=True)
        self.log(f'初始资金: $10,000.00', doprint=True)
        self.log(f'最终价值: ${final_value:.2f}', doprint=True)
        self.log(f'总收益率: {total_return:.2f}%', doprint=True)
        
        if self.trade_count > 0:
            win_rate = self.win_count / self.trade_count * 100
            self.log(f'总交易次数: {self.trade_count}', doprint=True)
            self.log(f'胜率: {win_rate:.1f}% ({self.win_count}/{self.trade_count})', doprint=True)
        else:
            self.log('没有完成任何交易', doprint=True)
        
        self.log('=' * 60, doprint=True)

def run_demo():
    """运行演示"""
    
    cerebro = bt.Cerebro()
    
    # 添加多时间框架策略
    cerebro.addstrategy(MultiTimeFrameStrategy)
    
    # 创建数据源 - 使用Backtrader自带的测试数据生成器
    modpath = bt.__file__.replace('__init__.py', '')
    datapath = modpath + 'datas/orcl-1995-2014.txt'
    
    try:
        # 尝试使用示例数据
        data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(2000, 1, 1),
            todate=datetime.datetime(2000, 12, 31),
            reverse=False)
        
        cerebro.adddata(data)
        print("✅ 使用Oracle示例数据 (2000年)")
        
    except:
        # 如果示例数据不存在，创建简单的模拟数据
        print("📊 示例数据不可用，生成模拟数据")
        
        # 生成模拟数据
        import tempfile
        import csv
        import random
        import os
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(temp_file)
        
        # CSV头
        writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'])
        
        # 生成200天的数据
        base_date = datetime.date(2023, 1, 1)
        price = 100.0
        
        for i in range(200):
            date = base_date + datetime.timedelta(days=i)
            
            # 跳过周末
            if date.weekday() >= 5:
                continue
            
            # 价格变动
            change = random.gauss(0, 0.02)
            price = max(10, price * (1 + change))
            
            # OHLCV数据
            open_p = price * random.uniform(0.99, 1.01)
            high_p = price * random.uniform(1.00, 1.04)
            low_p = price * random.uniform(0.96, 1.00)
            close_p = price
            volume = random.randint(100000, 1000000)
            
            writer.writerow([
                date.strftime('%Y-%m-%d'),
                f"{open_p:.2f}",
                f"{high_p:.2f}",
                f"{low_p:.2f}",
                f"{close_p:.2f}",
                volume,
                f"{close_p:.2f}"
            ])
        
        temp_file.close()
        
        # 加载模拟数据
        data = bt.feeds.YahooFinanceCSVData(
            dataname=temp_file.name,
            fromdate=datetime.datetime(2023, 1, 1),
            todate=datetime.datetime(2023, 7, 31)
        )
        
        cerebro.adddata(data)
        
        # 清理临时文件的函数
        def cleanup():
            try:
                os.unlink(temp_file.name)
            except:
                pass
    
    # 设置初始资金
    cerebro.broker.setcash(10000.0)
    
    # 设置手续费 - 0.1%
    cerebro.broker.setcommission(commission=0.001)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    print('🚀 多时间框架策略回测开始')
    print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
    print('-' * 60)
    
    # 运行策略
    results = cerebro.run()
    
    # 获取策略实例
    strat = results[0]
    
    # 清理临时文件
    if 'cleanup' in locals():
        cleanup()
    
    # 尝试获取分析器结果
    try:
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()
        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        
        print('\n📊 额外分析结果:')
        
        sharpe_ratio = sharpe_analysis.get('sharperatio', None)
        if sharpe_ratio:
            print(f'📈 夏普比率: {sharpe_ratio:.3f}')
        
        max_drawdown = drawdown_analysis.get('max', {}).get('drawdown', None)
        if max_drawdown:
            print(f'📉 最大回撤: {max_drawdown:.2f}%')
    except Exception as e:
        print(f'分析器结果获取失败: {e}')
    
    print(f'\n💰 最终资金: ${cerebro.broker.getvalue():.2f}')

if __name__ == '__main__':
    print('🎯 多时间框架Backtrader策略演示')
    print('=' * 60)
    print('📋 策略特点:')
    print('  ✓ 多指标综合评分 (SMA, RSI, MACD, 布林带)')
    print('  ✓ 信号强度量化 (0-10分制)')
    print('  ✓ 多条件买入确认')
    print('  ✓ 多重卖出保护 (信号恶化、止损、获利了结)')
    print('=' * 60)
    
    try:
        run_demo()
        print('\n✅ 多时间框架策略演示完成!')
    except Exception as e:
        print(f'\n❌ 演示失败: {e}')
        import traceback
        traceback.print_exc()