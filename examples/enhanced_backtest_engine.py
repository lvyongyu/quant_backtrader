#!/usr/bin/env python3
"""
增强型回测引擎
Enhanced Backtesting Engine

实现更真实的交易成本模拟，包括滑点、手续费、市场冲击等
"""

import backtrader as bt
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class RealisticCommission(bt.CommInfoBase):
    """真实手续费模型"""
    
    params = (
        ('commission', 0.001),     # 基础手续费率
        ('min_commission', 1.0),   # 最小手续费
        ('market_impact', 0.0001), # 市场冲击成本
        ('spread_cost', 0.0005),   # 买卖价差成本
    )
    
    def _getcommission(self, size, price, pseudoexec):
        """计算真实手续费"""
        
        # 基础手续费
        base_commission = abs(size) * price * self.p.commission
        
        # 最小手续费
        commission = max(base_commission, self.p.min_commission)
        
        # 市场冲击成本 (大单会有额外成本)
        if abs(size) > 100:
            impact_cost = abs(size) * price * self.p.market_impact * np.log(abs(size) / 100)
            commission += impact_cost
        
        # 买卖价差成本
        spread_cost = abs(size) * price * self.p.spread_cost
        commission += spread_cost
        
        return commission

class SlippageModel:
    """滑点模型"""
    
    def __init__(self, base_slippage=0.0005, volume_impact=0.001):
        self.base_slippage = base_slippage  # 基础滑点
        self.volume_impact = volume_impact  # 成交量影响
    
    def calculate_slippage(self, size: int, price: float, volume: float, volatility: float = 0.02) -> float:
        """计算滑点"""
        
        # 基础滑点
        slippage = self.base_slippage
        
        # 成交量影响 (订单量相对于市场成交量)
        if volume > 0:
            volume_ratio = abs(size) / volume
            volume_slippage = volume_ratio * self.volume_impact
            slippage += volume_slippage
        
        # 波动率影响
        volatility_slippage = volatility * 0.5
        slippage += volatility_slippage
        
        # 随机成分
        random_slippage = random.gauss(0, slippage * 0.3)
        slippage += abs(random_slippage)
        
        return slippage

class EnhancedBroker(bt.brokers.BackBroker):
    """增强型经纪商"""
    
    def __init__(self):
        super().__init__()
        self.slippage_model = SlippageModel()
        self.rejected_orders = 0
        self.total_slippage = 0
        
    def buy(self, owner, data, size, price=None, plimit=None, exectype=None, valid=None, tradeid=0, oco=None, trailamount=None, trailpercent=None, parent=None, transmit=True, **kwargs):
        """模拟买入订单"""
        
        # 检查流动性
        current_volume = data.volume[0] if len(data.volume) > 0 else 1000
        
        # 大单可能被拒绝
        if size > current_volume * 0.1:  # 订单超过市场成交量10%
            rejection_prob = min(0.3, (size / current_volume) * 0.5)
            if random.random() < rejection_prob:
                self.rejected_orders += 1
                print(f"❌ 大单被拒绝: 订单量 {size} 超过市场容量")
                return None
        
        return super().buy(owner, data, size, price, plimit, exectype, valid, tradeid, oco, trailamount, trailpercent, parent, transmit, **kwargs)
    
    def _execute(self, order, ago=0):
        """执行订单时应用滑点"""
        
        # 获取当前数据
        data = order.data
        current_price = data.close[0]
        current_volume = data.volume[0] if len(data.volume) > 0 else 1000
        
        # 计算波动率
        if len(data.close) >= 20:
            returns = np.diff(np.log(data.close.get(ago=-19, size=20)))
            volatility = np.std(returns) * np.sqrt(252)
        else:
            volatility = 0.02
        
        # 计算滑点
        slippage = self.slippage_model.calculate_slippage(
            order.size, current_price, current_volume, volatility
        )
        
        # 应用滑点
        if order.isbuy():
            slipped_price = current_price * (1 + slippage)
        else:
            slipped_price = current_price * (1 - slippage)
        
        # 记录滑点
        self.total_slippage += abs(slipped_price - current_price) * abs(order.size)
        
        # 更新订单价格
        order.executed.price = slipped_price
        order.executed.value = abs(order.size) * slipped_price
        
        return super()._execute(order, ago)

class MarketRegimeAnalyzer(bt.Analyzer):
    """市场环境分析器"""
    
    def __init__(self):
        super().__init__()
        self.regimes = []
        self.current_regime = "normal"
        
    def next(self):
        # 计算市场波动率
        if len(self.data.close) >= 20:
            returns = np.diff(np.log(self.data.close.get(size=20)))
            volatility = np.std(returns) * np.sqrt(252)
            
            # 分类市场环境
            if volatility > 0.25:
                regime = "high_volatility"
            elif volatility < 0.15:
                regime = "low_volatility"
            else:
                regime = "normal"
            
            self.regimes.append({
                'date': self.data.datetime.date(0),
                'regime': regime,
                'volatility': volatility
            })
            
            self.current_regime = regime
    
    def get_analysis(self):
        return {
            'regimes': self.regimes,
            'regime_distribution': self._get_regime_stats()
        }
    
    def _get_regime_stats(self):
        """统计市场环境分布"""
        if not self.regimes:
            return {}
        
        regime_counts = {}
        for r in self.regimes:
            regime = r['regime']
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        total = len(self.regimes)
        return {k: v/total for k, v in regime_counts.items()}

class TransactionCostAnalyzer(bt.Analyzer):
    """交易成本分析器"""
    
    def __init__(self):
        super().__init__()
        self.trades = []
        self.total_commission = 0
        self.total_slippage = 0
        
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                'date': self.data.datetime.date(0),
                'pnl': trade.pnl,
                'pnlcomm': trade.pnlcomm,
                'commission': trade.commission,
                'size': trade.size,
                'price': trade.price
            })
            
            self.total_commission += trade.commission
    
    def get_analysis(self):
        if not self.trades:
            return {}
        
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_pnl_comm = sum(t['pnlcomm'] for t in self.trades)
        total_commission = sum(t['commission'] for t in self.trades)
        
        return {
            'total_trades': len(self.trades),
            'total_pnl_gross': total_pnl,
            'total_pnl_net': total_pnl_comm,
            'total_commission': total_commission,
            'commission_impact': (total_pnl - total_pnl_comm) / total_pnl if total_pnl != 0 else 0,
            'avg_commission_per_trade': total_commission / len(self.trades),
            'commission_as_pct_of_pnl': total_commission / abs(total_pnl) if total_pnl != 0 else 0
        }

class EnhancedStrategy(bt.Strategy):
    """增强回测策略示例"""
    
    params = (
        ('sma_period', 20),
        ('rsi_period', 14),
        ('position_size', 0.95),
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
        
        # 市场环境跟踪
        self.regime_analyzer = MarketRegimeAnalyzer()
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.buy_price = order.executed.price
                slippage_cost = abs(order.executed.price - self.data.close[0])
                self.log(f'买入: ${order.executed.price:.2f}, 滑点成本: ${slippage_cost:.4f}')
            else:
                if self.buy_price:
                    pnl = (order.executed.price - self.buy_price) / self.buy_price * 100
                    slippage_cost = abs(order.executed.price - self.data.close[0])
                    self.log(f'卖出: ${order.executed.price:.2f}, 收益: {pnl:.2f}%, 滑点: ${slippage_cost:.4f}')
                    self.trades_count += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.getstatusname()}')
        
        self.order = None
    
    def next(self):
        if len(self) < max(self.p.sma_period, self.p.rsi_period):
            return
        
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # 获取当前市场环境
        self.regime_analyzer.next()
        current_regime = getattr(self.regime_analyzer, 'current_regime', 'normal')
        
        # 位置管理
        if self.position:
            # 根据市场环境调整止损
            if current_regime == "high_volatility":
                stop_multiplier = 1.5  # 高波动时放宽止损
            else:
                stop_multiplier = 1.0
            
            stop_price = self.buy_price * (1 - self.p.stop_loss * stop_multiplier)
            target_price = self.buy_price * (1 + self.p.take_profit)
            
            if current_price <= stop_price:
                self.log(f'止损 (环境: {current_regime})')
                self.order = self.sell()
            elif current_price >= target_price:
                self.log(f'止盈')
                self.order = self.sell()
        else:
            # 开仓条件 - 根据市场环境调整
            basic_conditions = [
                current_price > self.sma[0],
                30 < self.rsi[0] < 70,
            ]
            
            # 高波动环境下更谨慎
            if current_regime == "high_volatility":
                volatility_conditions = [
                    self.rsi[0] < 60,  # 更严格的RSI条件
                    current_price > self.sma[0] * 1.02,  # 价格明显突破均线
                ]
                entry_conditions = basic_conditions + volatility_conditions
                required_conditions = len(entry_conditions)
            else:
                entry_conditions = basic_conditions
                required_conditions = len(basic_conditions)
            
            if sum(entry_conditions) >= required_conditions:
                # 计算仓位大小
                cash = self.broker.get_cash()
                value = self.broker.getvalue()
                
                # 根据市场环境调整仓位
                if current_regime == "high_volatility":
                    position_mult = 0.7  # 高波动时减少仓位
                elif current_regime == "low_volatility":
                    position_mult = 1.0  # 低波动时正常仓位
                else:
                    position_mult = 0.85  # 正常环境
                
                position_value = value * self.p.position_size * position_mult
                size = int(position_value / current_price)
                
                if size > 0:
                    self.order = self.buy(size=size)
                    self.log(f'开仓 (环境: {current_regime}, 仓位调整: {position_mult:.1f})')
    
    def stop(self):
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        print('\n' + '='*60)
        print('📊 增强回测结果:')
        print(f'💰 初始资金: $10,000')
        print(f'💰 最终价值: ${final_value:.2f}')
        print(f'📈 总收益率: {total_return:+.2f}%')
        print(f'🔄 交易次数: {self.trades_count}')
        
        # 显示经纪商统计
        if hasattr(self.broker, 'rejected_orders'):
            print(f'❌ 被拒订单: {self.broker.rejected_orders}')
        if hasattr(self.broker, 'total_slippage'):
            print(f'💸 总滑点成本: ${self.broker.total_slippage:.2f}')
        
        print('='*60)

def run_enhanced_backtest():
    """运行增强回测"""
    
    print("🚀 增强型回测引擎演示")
    print("="*50)
    
    cerebro = bt.Cerebro()
    
    # 使用增强型经纪商
    cerebro.broker = EnhancedBroker()
    
    # 设置真实的手续费模型
    commission_info = RealisticCommission()
    cerebro.broker.addcommissioninfo(commission_info)
    
    # 添加策略
    cerebro.addstrategy(EnhancedStrategy)
    
    # 添加数据
    from src.data.yahoo_feed import YahooDataFeed
    data = YahooDataFeed(symbol='AAPL', period='1y')
    cerebro.adddata(data)
    
    # 添加分析器
    cerebro.addanalyzer(MarketRegimeAnalyzer, _name='regime')
    cerebro.addanalyzer(TransactionCostAnalyzer, _name='txn_cost')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    
    # 设置初始资金
    cerebro.broker.setcash(10000.0)
    
    print(f"💰 初始资金: ${cerebro.broker.getvalue():.2f}")
    print("🔄 运行增强回测...")
    
    # 运行回测
    results = cerebro.run()
    
    if results:
        strat = results[0]
        
        # 分析结果
        print(f"\n📊 详细分析报告:")
        
        # 交易成本分析
        try:
            txn_analysis = strat.analyzers.txn_cost.get_analysis()
            
            if txn_analysis:
                print(f"\n💸 交易成本分析:")
                print(f"   总交易数: {txn_analysis.get('total_trades', 0)}")
                print(f"   总手续费: ${txn_analysis.get('total_commission', 0):.2f}")
                print(f"   平均每笔手续费: ${txn_analysis.get('avg_commission_per_trade', 0):.2f}")
                
                commission_impact = txn_analysis.get('commission_impact', 0)
                print(f"   手续费对收益影响: {commission_impact*100:.2f}%")
        except:
            print("❌ 交易成本分析失败")
        
        # 市场环境分析
        try:
            regime_analysis = strat.analyzers.regime.get_analysis()
            regime_dist = regime_analysis.get('regime_distribution', {})
            
            if regime_dist:
                print(f"\n🌊 市场环境分析:")
                for regime, pct in regime_dist.items():
                    print(f"   {regime}: {pct*100:.1f}%")
        except:
            print("❌ 市场环境分析失败")
        
        # 标准分析
        try:
            trades = strat.analyzers.trades.get_analysis()
            
            total = trades.get('total', {}).get('total', 0)
            won = trades.get('won', {}).get('total', 0)
            
            if total > 0:
                print(f"\n📈 交易分析:")
                print(f"   胜率: {won/total*100:.1f}% ({won}/{total})")
                
                avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
                avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
                
                if avg_win and avg_loss:
                    print(f"   平均盈利: ${avg_win:.2f}")
                    print(f"   平均亏损: ${avg_loss:.2f}")
                    print(f"   盈亏比: {abs(avg_win/avg_loss):.2f}")
        except:
            print("❌ 交易分析失败")
        
        # 风险指标
        try:
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            
            sharpe_ratio = sharpe.get('sharperatio')
            if sharpe_ratio and not (sharpe_ratio != sharpe_ratio):
                print(f"\n⚡ 风险指标:")
                print(f"   夏普比率: {sharpe_ratio:.3f}")
            
            max_dd = drawdown.get('max', {}).get('drawdown', 0)
            if max_dd:
                print(f"   最大回撤: {max_dd:.2f}%")
        except:
            print("❌ 风险指标分析失败")
    
    final_value = cerebro.broker.getvalue()
    print(f"\n💰 最终资金: ${final_value:.2f}")
    
    return cerebro

def compare_backtest_models():
    """对比不同回测模型"""
    
    print("\n🔍 回测模型对比")
    print("="*50)
    
    models = [
        ("基础模型", "无滑点，固定手续费"),
        ("增强模型", "动态滑点，真实手续费"),
    ]
    
    results = {}
    
    for model_name, description in models:
        print(f"\n🧪 测试 {model_name}: {description}")
        
        cerebro = bt.Cerebro()
        
        if model_name == "增强模型":
            # 使用增强型经纪商
            cerebro.broker = EnhancedBroker()
            commission_info = RealisticCommission()
            cerebro.broker.addcommissioninfo(commission_info)
        else:
            # 使用标准经纪商
            cerebro.broker.setcommission(commission=0.001)
        
        # 添加简单策略
        cerebro.addstrategy(EnhancedStrategy)
        
        # 添加数据
        from src.data.yahoo_feed import YahooDataFeed
        data = YahooDataFeed(symbol='AAPL', period='6mo')
        cerebro.adddata(data)
        
        cerebro.broker.setcash(10000.0)
        
        # 运行
        strat_results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        results[model_name] = {
            'final_value': final_value,
            'return': (final_value - 10000) / 10000 * 100
        }
        
        print(f"   最终价值: ${final_value:.2f}")
        print(f"   收益率: {results[model_name]['return']:+.2f}%")
    
    # 显示对比
    print(f"\n📊 模型对比结果:")
    basic_return = results.get("基础模型", {}).get('return', 0)
    enhanced_return = results.get("增强模型", {}).get('return', 0)
    
    difference = basic_return - enhanced_return
    print(f"   基础模型收益: {basic_return:+.2f}%")
    print(f"   增强模型收益: {enhanced_return:+.2f}%")
    print(f"   差异: {difference:+.2f}% (真实成本影响)")
    
    if difference > 0:
        print(f"   💡 真实交易成本降低收益 {difference:.2f}%")
    
    return results

if __name__ == '__main__':
    """运行增强回测演示"""
    
    print("🎯 增强型回测引擎")
    print("="*60)
    
    try:
        # 1. 运行增强回测
        cerebro = run_enhanced_backtest()
        
        # 2. 对比不同模型
        comparison_results = compare_backtest_models()
        
        print(f"\n" + "="*60)
        print("🎉 增强回测演示完成!")
        
        print(f"\n📚 系统特性:")
        print("  ✅ 真实滑点模拟")
        print("  ✅ 动态手续费计算")
        print("  ✅ 市场冲击成本")
        print("  ✅ 流动性限制")
        print("  ✅ 市场环境适应")
        print("  ✅ 交易成本分析")
        
        print(f"\n💡 模型改进:")
        print("  🔸 考虑订单规模影响")
        print("  🔸 波动率动态调整")
        print("  🔸 买卖价差成本")
        print("  🔸 大单拒绝模拟")
        print("  🔸 环境适应策略")
        
        print(f"\n⚠️ 注意事项:")
        print("  • 真实交易成本会显著影响收益")
        print("  • 滑点在高波动期间更明显")
        print("  • 大单交易需要考虑流动性")
        print("  • 手续费结构因经纪商而异")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()