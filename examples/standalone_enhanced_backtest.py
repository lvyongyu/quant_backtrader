#!/usr/bin/env python3
"""
独立增强回测引擎演示
Standalone Enhanced Backtesting Engine Demo

完全独立的增强回测系统，包含真实交易成本模拟
"""

import backtrader as bt
import numpy as np
import random
import datetime
import pandas as pd
from typing import Dict, List, Optional

class SimpleDataFeed(bt.feeds.PandasData):
    """简单数据源"""
    
    def __init__(self, symbol='AAPL', days=252):
        # 生成模拟数据
        df = self.generate_sample_data(symbol, days)
        super().__init__(dataname=df)
        print(f"✅ 生成 {symbol} 数据: {len(df)} 条记录")
    
    def generate_sample_data(self, symbol, days):
        """生成样本数据"""
        dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
        
        # 模拟价格走势
        base_price = 150.0
        prices = []
        current_price = base_price
        
        for i in range(days):
            # 随机游走
            change = random.gauss(0.001, 0.02)  # 均值0.1%，标准差2%
            current_price *= (1 + change)
            current_price = max(10, current_price)
            
            # 生成OHLCV
            open_price = current_price * random.uniform(0.995, 1.005)
            high_price = current_price * random.uniform(1.005, 1.025)
            low_price = current_price * random.uniform(0.975, 0.995)
            close_price = current_price
            volume = random.randint(50000, 200000)
            
            prices.append({
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        df = pd.DataFrame(prices, index=dates)
        return df

class RealisticCommission(bt.CommInfoBase):
    """真实手续费模型"""
    
    params = (
        ('commission', 0.001),      # 基础手续费率0.1%
        ('min_commission', 1.0),    # 最小手续费$1
        ('market_impact', 0.0002),  # 市场冲击成本
        ('spread_cost', 0.0005),    # 买卖价差成本
    )
    
    def _getcommission(self, size, price, pseudoexec):
        """计算真实手续费"""
        
        # 基础手续费
        base_commission = abs(size) * price * self.p.commission
        
        # 最小手续费
        commission = max(base_commission, self.p.min_commission)
        
        # 市场冲击成本 - 大单会有额外成本
        if abs(size) > 100:
            impact_factor = np.log(abs(size) / 100 + 1)
            impact_cost = abs(size) * price * self.p.market_impact * impact_factor
            commission += impact_cost
        
        # 买卖价差成本
        spread_cost = abs(size) * price * self.p.spread_cost
        commission += spread_cost
        
        return commission

class SlippageModel:
    """滑点模型"""
    
    def __init__(self):
        self.base_slippage = 0.0005     # 基础滑点0.05%
        self.volume_impact = 0.001      # 成交量影响
        self.volatility_factor = 0.5    # 波动率影响因子
    
    def calculate_slippage(self, size, price, volume, volatility=0.02):
        """计算滑点"""
        
        # 基础滑点
        slippage = self.base_slippage
        
        # 成交量影响
        if volume > 0:
            volume_ratio = abs(size) / volume
            volume_slippage = min(volume_ratio * self.volume_impact, 0.01)  # 最大1%
            slippage += volume_slippage
        
        # 波动率影响
        volatility_slippage = volatility * self.volatility_factor
        slippage += volatility_slippage
        
        # 随机因素
        random_component = random.gauss(0, slippage * 0.3)
        slippage += abs(random_component)
        
        return min(slippage, 0.05)  # 滑点不超过5%

class EnhancedBroker(bt.brokers.BackBroker):
    """增强型经纪商"""
    
    def __init__(self):
        super().__init__()
        self.slippage_model = SlippageModel()
        self.rejected_orders = 0
        self.total_slippage_cost = 0
        self.order_stats = []
    
    def submit(self, order, check=True):
        """提交订单时检查流动性"""
        
        # 获取当前数据
        data = order.data
        current_volume = data.volume[0] if len(data.volume) > 0 else 10000
        
        # 检查大单是否会被拒绝
        if abs(order.size) > current_volume * 0.05:  # 订单超过5%成交量
            rejection_prob = min(0.2, abs(order.size) / current_volume * 0.1)
            
            if random.random() < rejection_prob:
                self.rejected_orders += 1
                print(f"❌ 订单被拒绝: 规模过大 (订单:{order.size}, 市场成交量:{current_volume})")
                order.reject()
                return order
        
        return super().submit(order, check)
    
    def next(self):
        """在每个时间点应用滑点"""
        super().next()
        
        # 处理待执行订单的滑点
        for order in list(self.pending):
            if order.status == order.Accepted:
                self._apply_slippage(order)
    
    def _apply_slippage(self, order):
        """对订单应用滑点"""
        
        data = order.data
        current_price = data.close[0]
        current_volume = data.volume[0] if len(data.volume) > 0 else 10000
        
        # 计算近期波动率
        if len(data.close) >= 10:
            recent_prices = [data.close[-i] for i in range(10)]
            returns = np.diff(np.log(recent_prices))
            volatility = np.std(returns) * np.sqrt(252)
        else:
            volatility = 0.02
        
        # 计算滑点
        slippage = self.slippage_model.calculate_slippage(
            order.size, current_price, current_volume, volatility
        )
        
        # 应用滑点到订单价格
        if order.isbuy():
            slipped_price = current_price * (1 + slippage)
        else:
            slipped_price = current_price * (1 - slippage)
        
        # 计算滑点成本
        slippage_cost = abs(slipped_price - current_price) * abs(order.size)
        self.total_slippage_cost += slippage_cost
        
        # 记录统计
        self.order_stats.append({
            'size': order.size,
            'original_price': current_price,
            'slipped_price': slipped_price,
            'slippage_pct': slippage * 100,
            'slippage_cost': slippage_cost
        })
        
        # 如果是市价单，设置滑点价格
        if order.exectype == bt.Order.Market:
            order.price = slipped_price

class TradingCostAnalyzer(bt.Analyzer):
    """交易成本分析器"""
    
    def __init__(self):
        super().__init__()
        self.trades = []
        self.total_commission = 0
        
    def notify_trade(self, trade):
        """记录交易"""
        if trade.isclosed:
            self.trades.append({
                'date': self.data.datetime.date(0),
                'size': trade.size,
                'price': trade.price,
                'pnl_gross': trade.pnl,
                'pnl_net': trade.pnlcomm,
                'commission': trade.commission
            })
            self.total_commission += trade.commission
    
    def get_analysis(self):
        """获取分析结果"""
        if not self.trades:
            return {}
        
        total_pnl_gross = sum(t['pnl_gross'] for t in self.trades)
        total_pnl_net = sum(t['pnl_net'] for t in self.trades)
        
        return {
            'total_trades': len(self.trades),
            'total_commission': self.total_commission,
            'total_pnl_gross': total_pnl_gross,
            'total_pnl_net': total_pnl_net,
            'commission_impact': total_pnl_gross - total_pnl_net,
            'avg_commission': self.total_commission / len(self.trades),
            'commission_ratio': self.total_commission / abs(total_pnl_gross) if total_pnl_gross != 0 else 0
        }

class EnhancedStrategy(bt.Strategy):
    """增强策略示例"""
    
    params = (
        ('sma_period', 20),
        ('rsi_period', 14),
        ('position_size', 0.9),
        ('stop_loss', 0.03),
        ('take_profit', 0.06),
    )
    
    def __init__(self):
        # 技术指标
        self.sma = bt.indicators.SMA(period=self.p.sma_period)
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        self.atr = bt.indicators.ATR(period=14)
        
        # 交易状态
        self.order = None
        self.buy_price = None
        self.trades_count = 0
        
        print(f"📊 策略参数:")
        print(f"   SMA周期: {self.p.sma_period}")
        print(f"   RSI周期: {self.p.rsi_period}") 
        print(f"   仓位大小: {self.p.position_size*100}%")
        print(f"   止损: {self.p.stop_loss*100}%")
        print(f"   止盈: {self.p.take_profit*100}%")
    
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'买入执行: ${order.executed.price:.2f}, 数量: {order.executed.size}')
            else:
                if self.buy_price:
                    pnl = (order.executed.price - self.buy_price) / self.buy_price * 100
                    self.log(f'卖出执行: ${order.executed.price:.2f}, 盈亏: {pnl:+.2f}%')
                    self.trades_count += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.getstatusname()}')
        
        self.order = None
    
    def next(self):
        """策略逻辑"""
        # 等待足够数据
        if len(self) < max(self.p.sma_period, self.p.rsi_period):
            return
        
        if self.order:
            return
        
        current_price = self.data.close[0]
        current_volume = self.data.volume[0]
        
        # 持仓管理
        if self.position:
            # 动态止损止盈
            stop_price = self.buy_price * (1 - self.p.stop_loss)
            target_price = self.buy_price * (1 + self.p.take_profit)
            
            # 使用ATR调整止损
            atr_stop = self.buy_price - (self.atr[0] * 2)
            actual_stop = max(stop_price, atr_stop)
            
            if current_price <= actual_stop:
                self.log(f'触发止损: ${current_price:.2f} <= ${actual_stop:.2f}')
                self.order = self.sell()
            elif current_price >= target_price:
                self.log(f'触发止盈: ${current_price:.2f} >= ${target_price:.2f}')
                self.order = self.sell()
        else:
            # 开仓条件
            entry_signals = [
                current_price > self.sma[0],        # 价格在均线上方
                self.rsi[0] > 30 and self.rsi[0] < 70,  # RSI在合理范围
                current_volume > 50000,             # 成交量充足
            ]
            
            # 确认信号强度
            signal_strength = sum(entry_signals)
            
            if signal_strength >= 3:  # 所有条件满足
                # 计算仓位大小
                cash = self.broker.get_cash()
                position_value = cash * self.p.position_size
                size = int(position_value / current_price)
                
                # 检查流动性
                max_position = current_volume * 0.02  # 不超过成交量的2%
                size = min(size, int(max_position))
                
                if size > 0:
                    self.order = self.buy(size=size)
                    self.log(f'开仓信号: RSI={self.rsi[0]:.1f}, 信号强度={signal_strength}/3')
    
    def stop(self):
        """策略结束"""
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        print('\n' + '='*50)
        print('📊 策略执行结果:')
        print(f'💰 初始资金: $10,000')
        print(f'💰 最终价值: ${final_value:.2f}')
        print(f'📈 总收益率: {total_return:+.2f}%')
        print(f'🔄 总交易数: {self.trades_count}')
        
        # 显示经纪商统计
        if hasattr(self.broker, 'rejected_orders'):
            print(f'❌ 被拒订单: {self.broker.rejected_orders}')
        if hasattr(self.broker, 'total_slippage_cost'):
            print(f'💸 总滑点成本: ${self.broker.total_slippage_cost:.2f}')
        
        print('='*50)

def run_enhanced_backtest_demo():
    """运行增强回测演示"""
    
    print("🚀 增强回测引擎演示")
    print("="*40)
    
    cerebro = bt.Cerebro()
    
    # 使用增强型经纪商
    cerebro.broker = EnhancedBroker()
    
    # 设置真实手续费
    commission_info = RealisticCommission()
    cerebro.broker.addcommissioninfo(commission_info)
    
    # 添加策略
    cerebro.addstrategy(EnhancedStrategy)
    
    # 添加数据
    data = SimpleDataFeed(symbol='AAPL', days=120)
    cerebro.adddata(data)
    
    # 添加分析器
    cerebro.addanalyzer(TradingCostAnalyzer, _name='costs')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    # 设置初始资金
    cerebro.broker.setcash(10000.0)
    
    print(f"💰 初始资金: ${cerebro.broker.getvalue():.2f}")
    print("-" * 40)
    
    # 运行回测
    results = cerebro.run()
    
    if results:
        strat = results[0]
        
        # 交易成本分析
        try:
            cost_analysis = strat.analyzers.costs.get_analysis()
            
            if cost_analysis:
                print(f"\n💸 交易成本分析:")
                print(f"   总交易数: {cost_analysis.get('total_trades', 0)}")
                print(f"   总手续费: ${cost_analysis.get('total_commission', 0):.2f}")
                print(f"   平均手续费: ${cost_analysis.get('avg_commission', 0):.2f}")
                
                commission_impact = cost_analysis.get('commission_impact', 0)
                print(f"   手续费影响: ${commission_impact:.2f}")
                
                ratio = cost_analysis.get('commission_ratio', 0)
                print(f"   手续费占比: {ratio*100:.2f}%")
        except Exception as e:
            print(f"❌ 成本分析失败: {e}")
        
        # 交易分析
        try:
            trade_analysis = strat.analyzers.trades.get_analysis()
            
            total = trade_analysis.get('total', {}).get('total', 0)
            won = trade_analysis.get('won', {}).get('total', 0)
            
            if total > 0:
                print(f"\n📈 交易统计:")
                print(f"   胜率: {won/total*100:.1f}% ({won}/{total})")
                
                avg_win = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0)
                avg_loss = trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0)
                
                if avg_win and avg_loss:
                    print(f"   平均盈利: ${avg_win:.2f}")
                    print(f"   平均亏损: ${avg_loss:.2f}")
                    print(f"   盈亏比: {abs(avg_win/avg_loss):.2f}")
        except Exception as e:
            print(f"❌ 交易分析失败: {e}")
        
        # 风险分析
        try:
            sharpe_analysis = strat.analyzers.sharpe.get_analysis()
            drawdown_analysis = strat.analyzers.drawdown.get_analysis()
            
            sharpe_ratio = sharpe_analysis.get('sharperatio')
            if sharpe_ratio and not np.isnan(sharpe_ratio):
                print(f"\n⚡ 风险指标:")
                print(f"   夏普比率: {sharpe_ratio:.3f}")
            
            max_dd = drawdown_analysis.get('max', {}).get('drawdown', 0)
            if max_dd:
                print(f"   最大回撤: {max_dd:.2f}%")
        except Exception as e:
            print(f"❌ 风险分析失败: {e}")
    
    print(f"\n💰 最终资金: ${cerebro.broker.getvalue():.2f}")
    
    return cerebro

def compare_backtest_engines():
    """对比基础和增强回测引擎"""
    
    print("\n🔍 回测引擎对比")
    print("="*40)
    
    results = {}
    
    # 测试配置
    configs = [
        ("基础回测", False),
        ("增强回测", True)
    ]
    
    for name, use_enhanced in configs:
        print(f"\n🧪 {name}")
        
        cerebro = bt.Cerebro()
        
        if use_enhanced:
            # 增强型配置
            cerebro.broker = EnhancedBroker()
            commission_info = RealisticCommission()
            cerebro.broker.addcommissioninfo(commission_info)
        else:
            # 基础配置
            cerebro.broker.setcommission(commission=0.001)
        
        # 添加相同策略和数据
        cerebro.addstrategy(EnhancedStrategy)
        data = SimpleDataFeed(symbol='TEST', days=80)
        cerebro.adddata(data)
        cerebro.broker.setcash(10000.0)
        
        # 运行
        start_value = cerebro.broker.getvalue()
        cerebro.run()
        end_value = cerebro.broker.getvalue()
        
        return_pct = (end_value - start_value) / start_value * 100
        
        results[name] = {
            'start': start_value,
            'end': end_value,
            'return': return_pct
        }
        
        print(f"   收益率: {return_pct:+.2f}%")
    
    # 显示对比结果
    if len(results) == 2:
        basic_return = results["基础回测"]["return"]
        enhanced_return = results["增强回测"]["return"]
        difference = basic_return - enhanced_return
        
        print(f"\n📊 对比结果:")
        print(f"   基础回测收益: {basic_return:+.2f}%")
        print(f"   增强回测收益: {enhanced_return:+.2f}%")
        print(f"   真实成本影响: {difference:+.2f}%")
        
        if difference > 0:
            print(f"   💡 真实交易成本使收益降低 {difference:.2f}%")

if __name__ == '__main__':
    """运行演示"""
    
    print("🎯 增强型回测引擎演示")
    print("="*50)
    
    try:
        # 1. 运行增强回测
        run_enhanced_backtest_demo()
        
        # 2. 对比不同引擎
        compare_backtest_engines()
        
        print(f"\n" + "="*50)
        print("🎉 增强回测演示完成!")
        
        print(f"\n📚 增强功能:")
        print("  ✅ 动态滑点模拟")
        print("  ✅ 真实手续费计算")
        print("  ✅ 市场冲击成本")
        print("  ✅ 流动性限制检查")
        print("  ✅ 大单拒绝机制")
        print("  ✅ 交易成本分析")
        
        print(f"\n💡 改进要点:")
        print("  🔸 滑点随订单大小和波动率变化")
        print("  🔸 手续费包含最小费用和冲击成本")
        print("  🔸 大单会面临流动性约束")
        print("  🔸 买卖价差成本真实模拟")
        print("  🔸 详细的成本分析报告")
        
        print(f"\n⚠️ 注意:")
        print("  • 真实交易成本会显著影响策略收益")
        print("  • 高频策略对交易成本更敏感")
        print("  • 大资金策略需考虑市场冲击")
        print("  • 不同市场和经纪商成本结构不同")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()