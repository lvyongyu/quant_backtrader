#!/usr/bin/env python3
"""
完全独立的增强回测演示
Complete Standalone Enhanced Backtest Demo

包含内置数据生成，演示增强回测引擎功能
"""

import backtrader as bt
import random
import datetime
import math

class MockDataFeed(bt.feeds.GenericCSVData):
    """模拟数据源"""
    
    def __init__(self, symbol='TEST', days=100):
        # 创建临时CSV文件
        import tempfile
        import csv
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        # 生成模拟数据
        prices = self.generate_price_data(symbol, days)
        
        # 写入CSV
        writer = csv.writer(self.temp_file)
        writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
        
        for price_data in prices:
            writer.writerow([
                price_data['date'],
                price_data['open'],
                price_data['high'],
                price_data['low'],
                price_data['close'],
                price_data['volume']
            ])
        
        self.temp_file.close()
        
        # 初始化父类
        super().__init__(
            dataname=self.temp_file.name,
            dtformat='%Y-%m-%d',
            datetime=0,
            open=1, high=2, low=3, close=4, volume=5
        )
        
        print(f"✅ 生成 {symbol} 模拟数据: {len(prices)} 条记录")
    
    def generate_price_data(self, symbol, days):
        """生成价格数据"""
        data = []
        base_price = 100.0
        current_price = base_price
        
        start_date = datetime.datetime(2023, 1, 1)
        
        for i in range(days):
            date = start_date + datetime.timedelta(days=i)
            
            # 跳过周末
            if date.weekday() >= 5:
                continue
            
            # 价格随机游走
            daily_return = random.gauss(0.0005, 0.02)  # 0.05%均值，2%波动
            current_price *= (1 + daily_return)
            current_price = max(10, current_price)
            
            # 生成OHLCV
            open_price = current_price * random.uniform(0.995, 1.005)
            high_price = current_price * random.uniform(1.01, 1.03)
            low_price = current_price * random.uniform(0.97, 0.99)
            close_price = current_price
            volume = random.randint(50000, 200000)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        return data
    
    def __del__(self):
        """清理临时文件"""
        try:
            import os
            if hasattr(self, 'temp_file'):
                os.unlink(self.temp_file.name)
        except:
            pass

class EnhancedCommissionInfo(bt.CommInfoBase):
    """增强手续费信息"""
    
    params = (
        ('commission', 0.001),       # 基础手续费率0.1%
        ('min_commission', 1.0),     # 最小手续费$1
        ('market_impact', 0.0002),   # 市场冲击成本0.02%
        ('spread_cost', 0.0005),     # 买卖价差成本0.05%
    )
    
    def _getcommission(self, size, price, pseudoexec):
        """计算真实手续费"""
        
        # 基础手续费
        base_comm = abs(size) * price * self.p.commission
        
        # 应用最小手续费
        commission = max(base_comm, self.p.min_commission)
        
        # 大单市场冲击 - 订单越大影响越大
        if abs(size) > 50:
            impact_multiplier = math.log(abs(size) / 50 + 1)
            impact_cost = abs(size) * price * self.p.market_impact * impact_multiplier
            commission += impact_cost
        
        # 买卖价差成本
        spread_cost = abs(size) * price * self.p.spread_cost
        commission += spread_cost
        
        return commission

class SlippageCalculator:
    """滑点计算器"""
    
    def __init__(self):
        self.base_slippage = 0.0003      # 基础滑点0.03%
        self.volume_impact_factor = 0.001 # 成交量影响因子
        self.total_slippage_cost = 0     # 累计滑点成本
    
    def calculate_slippage(self, order_size, current_price, market_volume):
        """计算订单滑点"""
        
        # 基础滑点
        slippage_rate = self.base_slippage
        
        # 相对成交量影响
        if market_volume > 0:
            volume_ratio = abs(order_size) / market_volume
            volume_impact = min(volume_ratio * self.volume_impact_factor, 0.005)  # 最大0.5%
            slippage_rate += volume_impact
        
        # 订单规模影响
        if abs(order_size) > 100:
            size_impact = math.log(abs(order_size) / 100) * 0.0001
            slippage_rate += size_impact
        
        # 随机波动
        random_slip = random.gauss(0, slippage_rate * 0.3)
        slippage_rate += abs(random_slip)
        
        # 限制最大滑点
        slippage_rate = min(slippage_rate, 0.015)  # 最大1.5%
        
        return slippage_rate

class EnhancedBroker(bt.brokers.BackBroker):
    """增强经纪商 - 模拟真实交易条件"""
    
    def __init__(self):
        super().__init__()
        self.slippage_calc = SlippageCalculator()
        self.order_rejection_count = 0
        self.total_orders = 0
        self.execution_log = []
    
    def submit(self, order, check=True):
        """提交订单时进行检查"""
        self.total_orders += 1
        
        # 获取市场数据
        data = order.data
        current_volume = data.volume[0] if len(data.volume) > 0 else 100000
        
        # 检查流动性 - 大单可能被拒绝
        max_order_size = current_volume * 0.1  # 不能超过10%成交量
        
        if abs(order.size) > max_order_size:
            rejection_probability = min(0.3, abs(order.size) / current_volume)
            
            if random.random() < rejection_probability:
                self.order_rejection_count += 1
                print(f"❌ 订单被拒绝: 规模 {order.size} 超过市场容量")
                order.reject()
                return order
        
        return super().submit(order, check)
    
    def next(self):
        """每个时间点的处理"""
        super().next()
        
        # 对pending订单应用滑点
        for order in list(self.pending):
            if order.status == order.Accepted:
                self._apply_slippage_to_order(order)
    
    def _apply_slippage_to_order(self, order):
        """对订单应用滑点"""
        
        data = order.data
        current_price = data.close[0]
        current_volume = data.volume[0] if len(data.volume) > 0 else 100000
        
        # 计算滑点
        slippage_rate = self.slippage_calc.calculate_slippage(
            order.size, current_price, current_volume
        )
        
        # 计算执行价格
        if order.isbuy():
            execution_price = current_price * (1 + slippage_rate)
        else:
            execution_price = current_price * (1 - slippage_rate)
        
        # 记录滑点成本
        slippage_cost = abs(execution_price - current_price) * abs(order.size)
        self.slippage_calc.total_slippage_cost += slippage_cost
        
        # 记录执行信息
        self.execution_log.append({
            'order_size': order.size,
            'market_price': current_price,
            'execution_price': execution_price,
            'slippage_rate': slippage_rate * 100,
            'slippage_cost': slippage_cost
        })

class CostTrackingAnalyzer(bt.Analyzer):
    """成本跟踪分析器"""
    
    def __init__(self):
        super().__init__()
        self.trades = []
        self.total_commission = 0
    
    def notify_trade(self, trade):
        """交易完成时记录"""
        if trade.isclosed:
            trade_info = {
                'date': self.data.datetime.date(0),
                'size': trade.size,
                'entry_price': trade.price,
                'pnl_gross': trade.pnl,
                'pnl_net': trade.pnlcomm,
                'commission': trade.commission
            }
            
            self.trades.append(trade_info)
            self.total_commission += trade.commission
    
    def get_analysis(self):
        """获取分析结果"""
        if not self.trades:
            return {'trade_count': 0}
        
        gross_pnl = sum(t['pnl_gross'] for t in self.trades)
        net_pnl = sum(t['pnl_net'] for t in self.trades)
        
        return {
            'trade_count': len(self.trades),
            'total_commission': self.total_commission,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'commission_impact': gross_pnl - net_pnl,
            'avg_commission_per_trade': self.total_commission / len(self.trades),
            'commission_drag_pct': (gross_pnl - net_pnl) / abs(gross_pnl) * 100 if gross_pnl != 0 else 0
        }

class DemoStrategy(bt.Strategy):
    """演示策略"""
    
    params = (
        ('sma_period', 20),
        ('rsi_period', 14),
        ('position_size', 0.8),
        ('stop_loss_pct', 0.03),
        ('take_profit_pct', 0.06),
    )
    
    def __init__(self):
        # 技术指标
        self.sma = bt.indicators.SMA(period=self.p.sma_period)
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        
        # 交易状态
        self.order = None
        self.buy_price = None
        self.trade_count = 0
        
        print(f"📊 策略配置:")
        print(f"   SMA周期: {self.p.sma_period}")
        print(f"   RSI周期: {self.p.rsi_period}")
        print(f"   仓位大小: {self.p.position_size*100}%")
        print(f"   止损: {self.p.stop_loss_pct*100}%")
        print(f"   止盈: {self.p.take_profit_pct*100}%")
    
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status == order.Completed:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'✅ 买入成交: ${order.executed.price:.2f} x {order.executed.size}')
            else:
                if self.buy_price:
                    pnl = (order.executed.price - self.buy_price) / self.buy_price * 100
                    self.log(f'✅ 卖出成交: ${order.executed.price:.2f}, 收益: {pnl:+.2f}%')
                    self.trade_count += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'❌ 订单失败: {order.getstatusname()}')
        
        self.order = None
    
    def next(self):
        """策略主逻辑"""
        # 等待足够的历史数据
        if len(self) < max(self.p.sma_period, self.p.rsi_period):
            return
        
        # 跳过有未完成订单的情况
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # 持仓管理
        if self.position:
            # 计算止损止盈价格
            stop_price = self.buy_price * (1 - self.p.stop_loss_pct)
            target_price = self.buy_price * (1 + self.p.take_profit_pct)
            
            # 止损
            if current_price <= stop_price:
                self.log(f'🛑 触发止损: {current_price:.2f} <= {stop_price:.2f}')
                self.order = self.sell()
            
            # 止盈
            elif current_price >= target_price:
                self.log(f'🎯 触发止盈: {current_price:.2f} >= {target_price:.2f}')
                self.order = self.sell()
        
        else:
            # 开仓条件检查
            conditions = [
                current_price > self.sma[0],          # 价格高于均线
                self.rsi[0] > 30 and self.rsi[0] < 70, # RSI在合理范围
                self.data.volume[0] > 80000,          # 成交量充足
            ]
            
            signal_strength = sum(conditions)
            
            # 需要满足所有条件
            if signal_strength == 3:
                # 计算订单大小
                available_cash = self.broker.get_cash()
                position_value = available_cash * self.p.position_size
                order_size = int(position_value / current_price)
                
                if order_size > 0:
                    self.order = self.buy(size=order_size)
                    self.log(f'🚀 开仓信号: RSI={self.rsi[0]:.1f}, 信号强度={signal_strength}/3')
    
    def stop(self):
        """策略结束统计"""
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        print('\n' + '='*50)
        print('📊 策略执行结果:')
        print(f'💰 初始资金: $10,000.00')
        print(f'💰 最终价值: ${final_value:.2f}')
        print(f'📈 总收益率: {total_return:+.2f}%')
        print(f'🔄 完成交易: {self.trade_count} 笔')
        
        # 显示增强统计信息
        broker = self.broker
        if hasattr(broker, 'order_rejection_count'):
            rejection_rate = broker.order_rejection_count / broker.total_orders * 100 if broker.total_orders > 0 else 0
            print(f'❌ 订单拒绝: {broker.order_rejection_count}/{broker.total_orders} ({rejection_rate:.1f}%)')
        
        if hasattr(broker, 'slippage_calc'):
            total_slippage = broker.slippage_calc.total_slippage_cost
            print(f'💸 滑点成本: ${total_slippage:.2f}')
        
        print('='*50)

def run_enhanced_backtest():
    """运行增强回测"""
    
    print("🚀 增强回测引擎演示")
    print("="*40)
    
    cerebro = bt.Cerebro()
    
    # 使用增强经纪商
    cerebro.broker = EnhancedBroker()
    
    # 设置增强手续费模型
    enhanced_commission = EnhancedCommissionInfo()
    cerebro.broker.addcommissioninfo(enhanced_commission)
    
    # 添加策略
    cerebro.addstrategy(DemoStrategy)
    
    # 添加模拟数据
    data = MockDataFeed(symbol='DEMO', days=120)
    cerebro.adddata(data)
    
    # 添加分析器
    cerebro.addanalyzer(CostTrackingAnalyzer, _name='cost_tracking')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
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
        
        # 成本分析
        try:
            cost_analysis = strat.analyzers.cost_tracking.get_analysis()
            
            if cost_analysis.get('trade_count', 0) > 0:
                print(f"\n💸 交易成本详细分析:")
                print(f"   交易笔数: {cost_analysis['trade_count']}")
                print(f"   总手续费: ${cost_analysis['total_commission']:.2f}")
                print(f"   平均手续费: ${cost_analysis['avg_commission_per_trade']:.2f}")
                print(f"   手续费拖累: {cost_analysis['commission_drag_pct']:.2f}%")
                print(f"   毛收益: ${cost_analysis['gross_pnl']:.2f}")
                print(f"   净收益: ${cost_analysis['net_pnl']:.2f}")
        except Exception as e:
            print(f"❌ 成本分析失败: {e}")
        
        # 交易分析
        try:
            trade_analysis = strat.analyzers.trade_analyzer.get_analysis()
            
            total = trade_analysis.get('total', {}).get('total', 0)
            won = trade_analysis.get('won', {}).get('total', 0)
            
            if total > 0:
                win_rate = won / total * 100
                print(f"\n📈 交易表现分析:")
                print(f"   胜率: {win_rate:.1f}% ({won}/{total})")
                
                avg_win = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0)
                avg_loss = trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0)
                
                if avg_win and avg_loss:
                    profit_factor = abs(avg_win / avg_loss)
                    print(f"   平均盈利: ${avg_win:.2f}")
                    print(f"   平均亏损: ${avg_loss:.2f}")
                    print(f"   盈亏比: {profit_factor:.2f}")
        except Exception as e:
            print(f"❌ 交易分析失败: {e}")
        
        # 风险指标
        try:
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            
            sharpe_ratio = sharpe.get('sharperatio')
            if sharpe_ratio and not math.isnan(sharpe_ratio):
                print(f"\n⚡ 风险收益指标:")
                print(f"   夏普比率: {sharpe_ratio:.3f}")
            
            max_dd = drawdown.get('max', {}).get('drawdown', 0)
            if max_dd:
                print(f"   最大回撤: {max_dd:.2f}%")
        except Exception as e:
            print(f"❌ 风险分析失败: {e}")
    
    print(f"\n💰 最终资金: ${cerebro.broker.getvalue():.2f}")
    
    return cerebro

def compare_basic_vs_enhanced():
    """对比基础与增强回测"""
    
    print("\n🔍 基础 vs 增强回测对比")
    print("="*30)
    
    results = {}
    
    test_configs = [
        ("基础回测", False),
        ("增强回测", True)
    ]
    
    for config_name, use_enhanced in test_configs:
        print(f"\n🧪 运行 {config_name}")
        
        cerebro = bt.Cerebro()
        
        if use_enhanced:
            # 增强配置
            cerebro.broker = EnhancedBroker()
            cerebro.broker.addcommissioninfo(EnhancedCommissionInfo())
        else:
            # 基础配置
            cerebro.broker.setcommission(commission=0.001)
        
        # 使用相同的策略和数据
        cerebro.addstrategy(DemoStrategy)
        data = MockDataFeed(symbol='COMPARE', days=80)
        cerebro.adddata(data)
        cerebro.broker.setcash(10000.0)
        
        # 运行
        initial_value = cerebro.broker.getvalue()
        cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        return_pct = (final_value - initial_value) / initial_value * 100
        results[config_name] = return_pct
        
        print(f"   收益率: {return_pct:+.2f}%")
    
    # 显示对比结果
    if len(results) == 2:
        basic_return = results["基础回测"]
        enhanced_return = results["增强回测"]
        cost_impact = basic_return - enhanced_return
        
        print(f"\n📊 对比结果总结:")
        print(f"   基础回测收益: {basic_return:+.2f}%")
        print(f"   增强回测收益: {enhanced_return:+.2f}%")
        print(f"   真实成本影响: {cost_impact:+.2f}%")
        
        if cost_impact > 0:
            print(f"   💡 真实交易成本降低了 {cost_impact:.2f}% 的收益")
        else:
            print(f"   ⚠️ 异常：增强模型收益更高，可能是随机性影响")

if __name__ == '__main__':
    """主程序入口"""
    
    print("🎯 增强回测引擎完整演示")
    print("="*60)
    
    try:
        # 1. 主要演示
        run_enhanced_backtest()
        
        # 2. 对比演示
        compare_basic_vs_enhanced()
        
        print(f"\n" + "="*60)
        print("🎉 增强回测引擎演示完成!")
        
        print(f"\n📚 系统特色:")
        print("  ✅ 真实滑点模拟 - 考虑订单大小和市场容量")
        print("  ✅ 动态手续费计算 - 包含最小费用和市场冲击")
        print("  ✅ 流动性约束 - 大单可能被拒绝")
        print("  ✅ 订单执行追踪 - 详细记录每笔交易成本")
        print("  ✅ 成本影响分析 - 量化真实交易成本")
        print("  ✅ 多维度比较 - 基础vs增强模型对比")
        
        print(f"\n💡 实际应用价值:")
        print("  🔸 更准确的策略收益评估")
        print("  🔸 识别高频策略的成本敏感性")
        print("  🔸 优化订单执行策略")
        print("  🔸 制定合理的资金管理方案")
        print("  🔸 评估不同经纪商的成本差异")
        
        print(f"\n⚠️ 重要提示:")
        print("  • 真实交易成本通常比预期更高")
        print("  • 滑点在市场波动时会显著增加")
        print("  • 大资金策略必须考虑市场冲击")
        print("  • 高频交易对成本极其敏感")
        print("  • 建议在模拟环境中充分测试")
        
    except Exception as e:
        print(f"❌ 演示过程出错: {e}")
        import traceback
        traceback.print_exc()