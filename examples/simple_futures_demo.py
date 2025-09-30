#!/usr/bin/env python3
"""
简化的期货交易系统
Simplified Futures Trading System

解决数据源问题的简化版本
"""

import backtrader as bt
import datetime
import random
import pandas as pd
from typing import Dict, List

class SimpleFuturesData(bt.feeds.PandasData):
    """简化的期货数据源 - 使用Pandas"""
    
    params = (
        ('symbol', 'CL'),
        ('days', 60),
    )
    
    def __init__(self):
        # 生成期货价格数据
        self.df = self.generate_futures_data()
        
        # 使用父类初始化
        super(SimpleFuturesData, self).__init__(dataname=self.df)
        
        print(f"✅ {self.p.symbol} 期货数据初始化完成: {len(self.df)} 条记录")
    
    def generate_futures_data(self) -> pd.DataFrame:
        """生成期货数据DataFrame"""
        
        # 基础价格
        base_prices = {
            'CL': 75.0,    # 原油
            'GC': 2000.0,  # 黄金
            'ES': 4500.0,  # S&P 500
            'BTC': 45000.0, # 比特币期货
        }
        
        base_price = base_prices.get(self.p.symbol, 100.0)
        dates = []
        prices = []
        
        # 生成日期序列
        start_date = datetime.datetime.now() - datetime.timedelta(days=self.p.days)
        current_price = base_price
        
        for i in range(self.p.days):
            date = start_date + datetime.timedelta(days=i)
            
            # 跳过周末
            if date.weekday() >= 5:
                continue
            
            # 价格随机游走
            volatility = 0.025 if self.p.symbol in ['BTC'] else 0.015
            change = random.gauss(0, volatility)
            current_price *= (1 + change)
            current_price = max(10, current_price)
            
            # 生成OHLCV
            open_price = current_price * random.uniform(0.998, 1.002)
            high_price = current_price * random.uniform(1.005, 1.025)
            low_price = current_price * random.uniform(0.975, 0.995)
            close_price = current_price
            volume = random.randint(10000, 100000)
            
            dates.append(date)
            prices.append({
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        # 创建DataFrame
        df = pd.DataFrame(prices, index=pd.DatetimeIndex(dates))
        
        return df

class SimpleFuturesStrategy(bt.Strategy):
    """简化的期货策略"""
    
    params = (
        ('leverage', 5),          # 杠杆倍数
        ('position_size', 0.3),   # 仓位大小
        ('sma_period', 15),       # 均线周期
        ('stop_loss', 0.03),      # 止损3%
        ('take_profit', 0.06),    # 止盈6%
    )
    
    def __init__(self):
        # 技术指标
        self.sma = bt.indicators.SMA(period=self.p.sma_period)
        self.rsi = bt.indicators.RSI(period=14)
        
        # 交易状态
        self.order = None
        self.buy_price = None
        self.trades = 0
        self.wins = 0
        
        print(f"📊 期货策略初始化:")
        print(f"   杠杆: {self.p.leverage}x")
        print(f"   仓位: {self.p.position_size*100}%")
        print(f"   止损: {self.p.stop_loss*100}%")
        print(f"   止盈: {self.p.take_profit*100}%")
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'期货买入: ${order.executed.price:.2f}, 数量: {order.executed.size}')
                
                # 计算止损止盈价格
                stop_price = self.buy_price * (1 - self.p.stop_loss)
                target_price = self.buy_price * (1 + self.p.take_profit)
                self.log(f'止损: ${stop_price:.2f}, 止盈: ${target_price:.2f}')
                
            else:
                if self.buy_price:
                    pnl = (order.executed.price - self.buy_price) / self.buy_price * 100
                    leveraged_pnl = pnl * self.p.leverage
                    
                    self.trades += 1
                    if pnl > 0:
                        self.wins += 1
                    
                    self.log(f'期货卖出: ${order.executed.price:.2f}')
                    self.log(f'收益: {pnl:+.2f}% (杠杆: {leveraged_pnl:+.2f}%)')
                
        self.order = None
    
    def next(self):
        if len(self) < self.p.sma_period:
            return
        
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # 持仓管理
        if self.position:
            # 止损
            if current_price <= self.buy_price * (1 - self.p.stop_loss):
                self.log(f'触发止损')
                self.order = self.sell()
                return
            
            # 止盈
            if current_price >= self.buy_price * (1 + self.p.take_profit):
                self.log(f'触发止盈')
                self.order = self.sell()
                return
            
            # 技术止损
            if current_price < self.sma[0] * 0.985:
                self.log(f'跌破均线止损')
                self.order = self.sell()
                return
        
        else:
            # 开仓信号
            if (current_price > self.sma[0] and 
                self.rsi[0] > 40 and self.rsi[0] < 70):
                
                # 计算仓位
                cash = self.broker.get_cash()
                position_value = cash * self.p.position_size
                size = int(position_value / current_price)
                
                if size > 0:
                    self.order = self.buy(size=size)
                    self.log(f'期货开仓信号: RSI={self.rsi[0]:.1f}')
    
    def stop(self):
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        win_rate = (self.wins / self.trades * 100) if self.trades > 0 else 0
        
        print('\n' + '='*50)
        print('📊 期货策略结果:')
        print(f'💰 初始资金: $10,000')
        print(f'💰 最终价值: ${final_value:.2f}')
        print(f'📈 总收益率: {total_return:+.2f}%')
        print(f'🎯 总交易数: {self.trades}')
        if self.trades > 0:
            print(f'✅ 胜率: {win_rate:.1f}% ({self.wins}/{self.trades})')
        print('='*50)

def run_simple_futures_test(symbol='CL'):
    """运行简化期货测试"""
    
    print(f"\n🚀 {symbol} 期货策略测试")
    print("-" * 40)
    
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(SimpleFuturesStrategy)
    
    # 添加数据
    data = SimpleFuturesData(symbol=symbol, days=60)
    cerebro.adddata(data)
    
    # 设置资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.002)
    
    print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
    
    # 运行
    cerebro.run()
    
    print(f'💰 最终资金: ${cerebro.broker.getvalue():.2f}')
    
    return cerebro

def futures_market_overview():
    """期货市场概览"""
    
    print("🔮 期货市场特点")
    print("=" * 40)
    
    features = [
        "📈 杠杆交易 - 资金效率高",
        "🔄 双向交易 - 可做多做空", 
        "💰 保证金制 - 风险可控",
        "🌊 流动性好 - 成交活跃",
        "📊 价格发现 - 反映预期",
        "⚡ 杠杆放大 - 收益和风险"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print(f"\n🎯 主要期货品种:")
    contracts = {
        'CL': '原油期货 - 能源之王',
        'GC': '黄金期货 - 避险之选', 
        'ES': 'S&P500期货 - 股指期货',
        'BTC': '比特币期货 - 数字资产'
    }
    
    for symbol, desc in contracts.items():
        print(f"  {symbol}: {desc}")

if __name__ == '__main__':
    """运行期货交易演示"""
    
    print("🎯 简化期货交易系统")
    print("=" * 50)
    
    try:
        # 市场概览
        futures_market_overview()
        
        # 测试不同合约
        test_symbols = ['CL', 'GC', 'BTC']
        
        for symbol in test_symbols:
            try:
                cerebro = run_simple_futures_test(symbol)
                print(f"✅ {symbol} 测试完成")
            except Exception as e:
                print(f"❌ {symbol} 测试失败: {e}")
        
        print(f"\n" + "=" * 50)
        print("🎉 期货系统演示完成!")
        
        print(f"\n📚 系统功能:")
        print("  ✅ 期货数据生成")
        print("  ✅ 杠杆交易模拟")
        print("  ✅ 止损止盈管理")
        print("  ✅ 技术分析策略") 
        print("  ✅ 风险控制机制")
        
        print(f"\n⚠️ 期货风险:")
        print("  🔥 杠杆高风险")
        print("  💸 可能爆仓")
        print("  📉 波动剧烈")
        print("  ⏰ 时间敏感")
        print("  🎓 需要专业知识")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()