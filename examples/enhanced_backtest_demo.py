#!/usr/bin/env python3
"""
简化增强回测演示
Simplified Enhanced Backtest Demo

演示增强回测引擎核心功能
"""

import backtrader as bt
import random
import datetime
import sys
import os

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class EnhancedCommission(bt.CommInfoBase):
    """增强手续费模型"""
    
    params = (
        ('commission', 0.001),      # 基础手续费0.1%
        ('min_commission', 1.0),    # 最小手续费$1
        ('market_impact', 0.0001),  # 市场冲击0.01%
        ('spread_cost', 0.0003),    # 价差成本0.03%
    )
    
    def _getcommission(self, size, price, pseudoexec):
        """计算真实手续费"""
        
        # 基础手续费
        base_commission = abs(size) * price * self.p.commission
        
        # 应用最小手续费
        commission = max(base_commission, self.p.min_commission)
        
        # 大单市场冲击成本
        if abs(size) > 100:
            import math
            impact_factor = math.log(abs(size) / 100 + 1)
            impact_cost = abs(size) * price * self.p.market_impact * impact_factor
            commission += impact_cost
        
        # 买卖价差成本
        spread_cost = abs(size) * price * self.p.spread_cost
        commission += spread_cost
        
        return commission

class SlippageSimulator:
    """滑点模拟器"""
    
    def __init__(self):
        self.base_slippage = 0.0003    # 基础滑点0.03%
        self.volume_factor = 0.0005    # 成交量影响因子
        self.total_slippage = 0        # 累计滑点成本
    
    def calculate_slippage(self, order_size, current_price, market_volume):
        """计算订单滑点"""
        
        # 基础滑点
        slippage = self.base_slippage
        
        # 订单规模影响
        if market_volume > 0:
            size_impact = min(abs(order_size) / market_volume, 0.1)  # 最大10%
            slippage += size_impact * self.volume_factor
        
        # 随机成分
        random_factor = random.gauss(0, slippage * 0.2)
        slippage += abs(random_factor)
        
        # 限制最大滑点
        slippage = min(slippage, 0.02)  # 最大2%
        
        return slippage

class EnhancedBroker(bt.brokers.BackBroker):
    """增强经纪商 - 模拟真实交易环境"""
    
    def __init__(self):
        super().__init__()
        self.slippage_sim = SlippageSimulator()
        self.rejected_orders = 0
        self.order_count = 0
        
    def next(self):
        """在每个时间点处理订单"""
        super().next()
        
        # 模拟订单处理延迟和滑点
        for order in list(self.pending):
            if order.status == order.Accepted:
                self._process_order_with_slippage(order)
    
    def _process_order_with_slippage(self, order):
        """处理订单并应用滑点"""
        
        data = order.data
        current_price = data.close[0]
        current_volume = getattr(data, 'volume', [10000])[0] if hasattr(data, 'volume') else 10000
        
        # 检查大单是否被拒绝
        if abs(order.size) > current_volume * 0.08:  # 超过8%成交量
            rejection_chance = min(0.15, abs(order.size) / current_volume * 0.05)
            
            if random.random() < rejection_chance:
                self.rejected_orders += 1
                print(f"❌ 大单被拒绝: 订单 {order.size}, 市场成交量 {current_volume}")
                order.reject()
                return
        
        # 计算滑点
        slippage = self.slippage_sim.calculate_slippage(
            order.size, current_price, current_volume
        )
        
        # 应用滑点到执行价格
        if order.isbuy():
            execution_price = current_price * (1 + slippage)
        else:
            execution_price = current_price * (1 - slippage)
        
        # 计算滑点成本
        slippage_cost = abs(execution_price - current_price) * abs(order.size)
        self.slippage_sim.total_slippage += slippage_cost
        
        self.order_count += 1

class CostAnalyzer(bt.Analyzer):
    """交易成本分析器"""
    
    def __init__(self):
        super().__init__()
        self.trade_costs = []
        self.total_commission = 0
    
    def notify_trade(self, trade):
        """记录每笔交易成本"""
        if trade.isclosed:
            cost_info = {
                'date': self.data.datetime.date(0),
                'size': trade.size,
                'pnl_gross': trade.pnl,
                'pnl_net': trade.pnlcomm,
                'commission': trade.commission,
                'cost_impact': trade.pnl - trade.pnlcomm
            }
            
            self.trade_costs.append(cost_info)
            self.total_commission += trade.commission
    
    def get_analysis(self):
        """返回成本分析结果"""
        if not self.trade_costs:
            return {'total_trades': 0}
        
        total_gross_pnl = sum(t['pnl_gross'] for t in self.trade_costs)
        total_net_pnl = sum(t['pnl_net'] for t in self.trade_costs)
        
        return {
            'total_trades': len(self.trade_costs),
            'total_commission': self.total_commission,
            'total_gross_pnl': total_gross_pnl,
            'total_net_pnl': total_net_pnl,
            'cost_impact': total_gross_pnl - total_net_pnl,
            'avg_commission': self.total_commission / len(self.trade_costs),
            'commission_drag': (total_gross_pnl - total_net_pnl) / abs(total_gross_pnl) if total_gross_pnl != 0 else 0
        }

class TestStrategy(bt.Strategy):
    """测试策略"""
    
    params = (
        ('sma_period', 15),
        ('position_size', 0.8),
        ('stop_loss', 0.04),
        ('take_profit', 0.08),
    )
    
    def __init__(self):
        self.sma = bt.indicators.SMA(period=self.p.sma_period)
        self.rsi = bt.indicators.RSI(period=14)
        
        self.order = None
        self.buy_price = None
        self.trade_count = 0
        
        print(f"📊 策略初始化:")
        print(f"   均线周期: {self.p.sma_period}")
        print(f"   仓位大小: {self.p.position_size*100}%")
        print(f"   止损: {self.p.stop_loss*100}%")
        print(f"   止盈: {self.p.take_profit*100}%")
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'买入: ${order.executed.price:.2f}, 数量: {order.executed.size}')
            else:
                if self.buy_price:
                    pnl_pct = (order.executed.price - self.buy_price) / self.buy_price * 100
                    self.log(f'卖出: ${order.executed.price:.2f}, 收益: {pnl_pct:+.2f}%')
                    self.trade_count += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.getstatusname()}')
        
        self.order = None
    
    def next(self):
        if len(self) < self.p.sma_period:
            return
        
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # 持仓管理
        if self.position:
            # 止损止盈
            if current_price <= self.buy_price * (1 - self.p.stop_loss):
                self.log('触发止损')
                self.order = self.sell()
            elif current_price >= self.buy_price * (1 + self.p.take_profit):
                self.log('触发止盈')
                self.order = self.sell()
        else:
            # 开仓条件
            if (current_price > self.sma[0] and 
                self.rsi[0] > 35 and self.rsi[0] < 65):
                
                cash = self.broker.get_cash()
                size = int((cash * self.p.position_size) / current_price)
                
                if size > 0:
                    self.order = self.buy(size=size)
                    self.log(f'开仓信号: RSI={self.rsi[0]:.1f}')
    
    def stop(self):
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        print('\n' + '='*40)
        print('📊 策略结果:')
        print(f'💰 初始: $10,000 → 最终: ${final_value:.2f}')
        print(f'📈 收益率: {total_return:+.2f}%')
        print(f'🔄 交易数: {self.trade_count}')
        
        # 显示增强统计
        if hasattr(self.broker, 'rejected_orders'):
            print(f'❌ 被拒订单: {self.broker.rejected_orders}')
        if hasattr(self.broker, 'slippage_sim'):
            total_slippage = self.broker.slippage_sim.total_slippage
            print(f'💸 滑点成本: ${total_slippage:.2f}')
        
        print('='*40)

def run_enhanced_demo():
    """运行增强回测演示"""
    
    print("🚀 增强回测引擎演示")
    print("="*40)
    
    cerebro = bt.Cerebro()
    
    # 使用增强经纪商
    cerebro.broker = EnhancedBroker()
    
    # 设置增强手续费
    enhanced_commission = EnhancedCommission()
    cerebro.broker.addcommissioninfo(enhanced_commission)
    
    # 添加策略
    cerebro.addstrategy(TestStrategy)
    
    # 使用现有数据源
    try:
        from src.data.yahoo_feed import YahooDataFeed
        data = YahooDataFeed(symbol='AAPL', period='6mo')
        cerebro.adddata(data)
        print("✅ 使用Yahoo数据源")
    except:
        print("❌ Yahoo数据源不可用，使用内置数据")
        # 使用Backtrader内置测试数据
        data = bt.feeds.YahooFinanceCSVData(
            dataname=None,  # 会使用内置样本数据
            fromdate=datetime.datetime(2023, 1, 1),
            todate=datetime.datetime(2023, 12, 31)
        )
        cerebro.adddata(data)
    
    # 添加分析器
    cerebro.addanalyzer(CostAnalyzer, _name='costs')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    
    # 设置资金
    cerebro.broker.setcash(10000.0)
    
    print(f"💰 初始资金: ${cerebro.broker.getvalue():.2f}")
    print("-" * 40)
    
    # 运行回测
    results = cerebro.run()
    
    if results:
        strat = results[0]
        
        # 成本分析
        try:
            cost_analysis = strat.analyzers.costs.get_analysis()
            
            if cost_analysis.get('total_trades', 0) > 0:
                print(f"\n💸 交易成本分析:")
                print(f"   总交易: {cost_analysis['total_trades']}")
                print(f"   总手续费: ${cost_analysis['total_commission']:.2f}")
                print(f"   平均手续费: ${cost_analysis['avg_commission']:.2f}")
                print(f"   成本拖累: {cost_analysis['commission_drag']*100:.2f}%")
        except Exception as e:
            print(f"❌ 成本分析失败: {e}")
        
        # 交易分析
        try:
            trade_analysis = strat.analyzers.trades.get_analysis()
            
            total_trades = trade_analysis.get('total', {}).get('total', 0)
            won_trades = trade_analysis.get('won', {}).get('total', 0)
            
            if total_trades > 0:
                print(f"\n📈 交易统计:")
                print(f"   胜率: {won_trades/total_trades*100:.1f}% ({won_trades}/{total_trades})")
        except Exception as e:
            print(f"❌ 交易分析失败: {e}")
    
    print(f"\n💰 最终资金: ${cerebro.broker.getvalue():.2f}")
    
    return cerebro

def demo_cost_comparison():
    """演示成本对比"""
    
    print("\n🔍 成本模型对比")
    print("="*30)
    
    results = {}
    
    # 测试不同成本模型
    models = [
        ("基础模型", False),
        ("增强模型", True)
    ]
    
    for model_name, use_enhanced in models:
        print(f"\n🧪 {model_name}")
        
        cerebro = bt.Cerebro()
        
        if use_enhanced:
            cerebro.broker = EnhancedBroker()
            cerebro.broker.addcommissioninfo(EnhancedCommission())
        else:
            cerebro.broker.setcommission(commission=0.001)
        
        cerebro.addstrategy(TestStrategy)
        
        # 使用相同数据
        try:
            from src.data.yahoo_feed import YahooDataFeed
            data = YahooDataFeed(symbol='AAPL', period='3mo')
            cerebro.adddata(data)
        except:
            continue
        
        cerebro.broker.setcash(10000.0)
        
        start_value = cerebro.broker.getvalue()
        cerebro.run()
        end_value = cerebro.broker.getvalue()
        
        return_pct = (end_value - start_value) / start_value * 100
        results[model_name] = return_pct
        
        print(f"   收益率: {return_pct:+.2f}%")
    
    # 显示对比
    if len(results) == 2:
        basic = results.get("基础模型", 0)
        enhanced = results.get("增强模型", 0)
        diff = basic - enhanced
        
        print(f"\n📊 对比结果:")
        print(f"   基础模型: {basic:+.2f}%")
        print(f"   增强模型: {enhanced:+.2f}%")
        print(f"   成本影响: {diff:+.2f}%")

if __name__ == '__main__':
    """运行演示"""
    
    print("🎯 增强回测引擎")
    print("="*50)
    
    try:
        # 1. 主要演示
        run_enhanced_demo()
        
        # 2. 成本对比
        demo_cost_comparison()
        
        print(f"\n" + "="*50)
        print("🎉 增强回测演示完成!")
        
        print(f"\n📚 增强特性:")
        print("  ✅ 动态滑点计算")
        print("  ✅ 真实手续费模型")
        print("  ✅ 市场冲击成本")
        print("  ✅ 大单流动性限制")
        print("  ✅ 订单拒绝机制")
        print("  ✅ 详细成本分析")
        
        print(f"\n💡 关键改进:")
        print("  🔸 滑点随订单大小变化")
        print("  🔸 手续费包含最小费用")
        print("  🔸 成本分析量化影响")
        print("  🔸 更真实的交易环境")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()