#!/usr/bin/env python3
"""
期货交易数据源
Futures Trading Data Feed

支持期货合约数据获取和交易
"""

import backtrader as bt
import requests
import datetime
import random
from typing import Dict, List

class FuturesAPI:
    """期货API模拟客户端"""
    
    def __init__(self):
        # 模拟的期货合约
        self.contracts = {
            'CL': {'name': '原油期货', 'tick_size': 0.01, 'contract_size': 1000},
            'GC': {'name': '黄金期货', 'tick_size': 0.1, 'contract_size': 100},
            'ES': {'name': 'E-mini S&P 500', 'tick_size': 0.25, 'contract_size': 50},
            'NQ': {'name': 'E-mini Nasdaq', 'tick_size': 0.25, 'contract_size': 20},
            'BTC': {'name': '比特币期货', 'tick_size': 5.0, 'contract_size': 5},
            'ETH': {'name': '以太坊期货', 'tick_size': 0.05, 'contract_size': 50}
        }
        
    def get_contract_info(self, symbol: str) -> Dict:
        """获取合约信息"""
        return self.contracts.get(symbol.upper(), {})
    
    def generate_futures_data(self, symbol: str, days: int = 60) -> List[Dict]:
        """生成期货数据"""
        data = []
        
        # 基础价格设置
        base_prices = {
            'CL': 75.0,    # 原油
            'GC': 2000.0,  # 黄金
            'ES': 4500.0,  # S&P 500
            'NQ': 15000.0, # Nasdaq
            'BTC': 45000.0, # 比特币期货
            'ETH': 3000.0   # 以太坊期货
        }
        
        base_price = base_prices.get(symbol.upper(), 100.0)
        current_price = base_price
        
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        for i in range(days):
            date = start_date + datetime.timedelta(days=i)
            
            # 跳过周末
            if date.weekday() >= 5:
                continue
            
            # 价格波动
            # 期货价格波动更大
            volatility = 0.03 if symbol.upper() in ['BTC', 'ETH'] else 0.02
            change = random.gauss(0, volatility)
            current_price *= (1 + change)
            current_price = max(10, current_price)
            
            # 生成OHLCV
            open_price = current_price * random.uniform(0.995, 1.005)
            high_price = current_price * random.uniform(1.0, 1.025)
            low_price = current_price * random.uniform(0.975, 1.0)
            close_price = current_price
            
            # 期货成交量通常较小
            volume = random.randint(5000, 50000)
            
            # 计算持仓量 (Open Interest)
            open_interest = random.randint(10000, 100000)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'open_interest': open_interest
            })
        
        return data

class FuturesDataFeed(bt.feeds.GenericCSVData):
    """期货数据源"""
    
    params = (
        ('symbol', 'CL'),       # 期货合约代码
        ('days', 60),           # 数据天数
        ('margin_req', 0.1),    # 保证金要求 (10%)
        ('tick_size', 0.01),    # 最小变动价位
    )
    
    def __init__(self):
        self.api = FuturesAPI()
        
        # 获取合约信息
        self.contract_info = self.api.get_contract_info(self.p.symbol)
        
        # 创建临时CSV文件
        import tempfile
        import csv
        import os
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        try:
            print(f"📊 生成 {self.p.symbol} 期货数据...")
            
            # 生成期货数据
            futures_data = self.api.generate_futures_data(self.p.symbol, self.p.days)
            
            if not futures_data:
                raise ValueError("No futures data generated")
            
            # 写入CSV
            writer = csv.writer(self.temp_file)
            writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
            
            for data_point in futures_data:
                writer.writerow([
                    data_point['date'],
                    data_point['open'],
                    data_point['high'],
                    data_point['low'],
                    data_point['close'],
                    data_point['volume']
                ])
            
            self.temp_file.close()
            
            print(f"✅ 生成 {len(futures_data)} 条 {self.p.symbol} 期货数据")
            
            if self.contract_info:
                print(f"   合约名称: {self.contract_info['name']}")
                print(f"   最小变动: {self.contract_info['tick_size']}")
                print(f"   合约规模: {self.contract_info['contract_size']}")
            
            # 初始化父类
            super(FuturesDataFeed, self).__init__(
                dataname=self.temp_file.name,
                dtformat='%Y-%m-%d',
                datetime=0,
                open=1, high=2, low=3, close=4, volume=5
            )
            
        except Exception as e:
            print(f"❌ {self.p.symbol} 期货数据生成失败: {e}")
            self.temp_file.close()
            
            # 创建空文件
            with open(self.temp_file.name, 'w') as f:
                f.write('date,open,high,low,close,volume\n')
            
            super(FuturesDataFeed, self).__init__(
                dataname=self.temp_file.name,
                dtformat='%Y-%m-%d',
                datetime=0,
                open=1, high=2, low=3, close=4, volume=5
            )
    
    def __del__(self):
        """清理临时文件"""
        try:
            import os
            if hasattr(self, 'temp_file') and self.temp_file:
                os.unlink(self.temp_file.name)
        except:
            pass

class FuturesStrategy(bt.Strategy):
    """期货交易策略"""
    
    params = (
        ('leverage', 10),           # 杠杆倍数
        ('margin_requirement', 0.1), # 保证金要求
        ('position_size_pct', 0.2),  # 仓位大小百分比
        ('stop_loss_pct', 0.03),     # 止损百分比
        ('take_profit_pct', 0.06),   # 止盈百分比
        ('sma_period', 20),          # 均线周期
        ('rsi_period', 14),          # RSI周期
    )
    
    def __init__(self):
        # 技术指标
        self.sma = bt.indicators.SMA(period=self.p.sma_period)
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        self.macd = bt.indicators.MACD()
        self.atr = bt.indicators.ATR(period=14)
        
        # 交易状态
        self.order = None
        self.buy_price = None
        self.stop_price = None
        self.target_price = None
        
        # 统计
        self.trades = 0
        self.wins = 0
        self.total_pnl = 0
        
        # 风险控制
        self.max_position_value = 0
        self.margin_used = 0
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def calculate_position_size(self):
        """计算期货仓位大小"""
        available_cash = self.broker.get_cash()
        current_price = self.data.close[0]
        
        # 基于保证金计算最大可开仓位
        margin_per_contract = current_price * self.p.margin_requirement
        max_contracts = available_cash / margin_per_contract
        
        # 使用风险控制，只用部分资金
        target_contracts = max_contracts * self.p.position_size_pct
        
        return int(target_contracts)
    
    def calculate_stop_loss(self, entry_price, is_long=True):
        """计算止损价格"""
        atr_stop = self.atr[0] * 2  # 使用ATR的2倍作为止损
        pct_stop = entry_price * self.p.stop_loss_pct
        
        stop_distance = max(atr_stop, pct_stop)
        
        if is_long:
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.stop_price = self.calculate_stop_loss(self.buy_price, True)
                self.target_price = self.buy_price * (1 + self.p.take_profit_pct)
                
                # 计算保证金使用
                position_value = order.executed.size * order.executed.price
                self.margin_used = position_value * self.p.margin_requirement
                
                self.log(f'期货买入: ${order.executed.price:.2f}, 数量: {order.executed.size}')
                self.log(f'止损: ${self.stop_price:.2f}, 止盈: ${self.target_price:.2f}')
                self.log(f'保证金使用: ${self.margin_used:.2f}')
                
            else:
                if self.buy_price:
                    pnl = (order.executed.price - self.buy_price) * order.executed.size
                    self.total_pnl += pnl
                    self.trades += 1
                    
                    if pnl > 0:
                        self.wins += 1
                    
                    pnl_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    leveraged_return = pnl_pct * self.p.leverage
                    
                    self.log(f'期货卖出: ${order.executed.price:.2f}')
                    self.log(f'盈亏: ${pnl:.2f} ({leveraged_return:+.2f}%杠杆收益)')
                
                self.margin_used = 0
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.getstatusname()}')
        
        self.order = None
    
    def next(self):
        # 等待足够的历史数据
        if len(self) < self.p.sma_period:
            return
        
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # 持仓管理
        if self.position:
            # 止损
            if current_price <= self.stop_price:
                self.log(f'触发止损: ${current_price:.2f} <= ${self.stop_price:.2f}')
                self.order = self.sell()
                return
            
            # 止盈
            if current_price >= self.target_price:
                self.log(f'触发止盈: ${current_price:.2f} >= ${self.target_price:.2f}')
                self.order = self.sell()
                return
            
            # 技术止损：跌破均线
            if current_price < self.sma[0] * 0.98:
                self.log(f'跌破均线止损: RSI={self.rsi[0]:.1f}')
                self.order = self.sell()
                return
        
        else:
            # 开仓条件
            entry_conditions = [
                current_price > self.sma[0],  # 价格在均线上方
                self.rsi[0] < 70,  # RSI不超买
                self.rsi[0] > 30,  # RSI不超卖
                self.macd.macd[0] > self.macd.signal[0],  # MACD金叉
            ]
            
            if sum(entry_conditions) >= 3:  # 至少满足3个条件
                size = self.calculate_position_size()
                
                if size > 0:
                    # 检查保证金充足
                    required_margin = size * current_price * self.p.margin_requirement
                    available_cash = self.broker.get_cash()
                    
                    if required_margin <= available_cash:
                        self.order = self.buy(size=size)
                        self.log(f'期货开多仓信号:')
                        self.log(f'  价格: ${current_price:.2f}')
                        self.log(f'  RSI: {self.rsi[0]:.1f}')
                        self.log(f'  条件满足: {sum(entry_conditions)}/4')
                        self.log(f'  杠杆: {self.p.leverage}x')
                    else:
                        self.log(f'保证金不足: 需要${required_margin:.2f}, 可用${available_cash:.2f}')
    
    def stop(self):
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        win_rate = (self.wins / self.trades * 100) if self.trades > 0 else 0
        
        self.log('=' * 60)
        self.log('期货交易策略结果:')
        self.log(f'初始资金: $10,000.00')
        self.log(f'最终价值: ${final_value:.2f}')
        self.log(f'总收益率: {total_return:+.2f}%')
        self.log(f'总交易数: {self.trades}')
        
        if self.trades > 0:
            self.log(f'胜率: {win_rate:.1f}% ({self.wins}/{self.trades})')
            avg_pnl = self.total_pnl / self.trades
            self.log(f'平均每笔: ${avg_pnl:.2f}')
            
            # 计算杠杆效应
            unleveraged_return = total_return / self.p.leverage
            self.log(f'杠杆收益: {total_return:.2f}% (无杠杆: {unleveraged_return:.2f}%)')
        
        self.log('=' * 60)

def run_futures_backtest(symbol='CL'):
    """运行期货回测"""
    
    cerebro = bt.Cerebro()
    
    # 添加期货策略
    cerebro.addstrategy(FuturesStrategy)
    
    # 添加期货数据源
    data = FuturesDataFeed(symbol=symbol, days=80)
    cerebro.adddata(data)
    
    # 设置初始资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.002)  # 期货手续费较高
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    print(f'🚀 {symbol} 期货策略回测')
    print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
    print('-' * 50)
    
    # 运行回测
    results = cerebro.run()
    
    if results:
        strat = results[0]
        
        try:
            trades = strat.analyzers.trades.get_analysis()
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            
            print(f'\n📊 期货策略分析:')
            
            total = trades.get('total', {}).get('total', 0)
            won = trades.get('won', {}).get('total', 0)
            
            if total > 0:
                win_rate = (won / total) * 100
                print(f'总交易: {total}, 胜率: {win_rate:.1f}%')
                
                avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
                avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
                
                if avg_win and avg_loss:
                    print(f'平均盈利: ${avg_win:.2f}')
                    print(f'平均亏损: ${avg_loss:.2f}')
                    print(f'盈亏比: {abs(avg_win/avg_loss):.2f}')
            
            sharpe_ratio = sharpe.get('sharperatio')
            if sharpe_ratio and not (sharpe_ratio != sharpe_ratio):
                print(f'夏普比率: {sharpe_ratio:.3f}')
            
            max_drawdown = drawdown.get('max', {}).get('drawdown', 0)
            if max_drawdown:
                print(f'最大回撤: {max_drawdown:.2f}%')
                
        except Exception as e:
            print(f'分析器获取失败: {e}')
    
    print(f'💰 最终资金: ${cerebro.broker.getvalue():.2f}')
    
    return cerebro

def demonstrate_futures_markets():
    """演示期货市场"""
    
    print("🔮 期货市场概览")
    print("=" * 50)
    
    api = FuturesAPI()
    
    print(f"{'合约':<6} {'名称':<20} {'最小变动':<10} {'合约规模':<10}")
    print("-" * 50)
    
    for symbol, info in api.contracts.items():
        print(f"{symbol:<6} {info['name']:<20} {info['tick_size']:<10} {info['contract_size']:<10}")
    
    print(f"\n💡 期货交易特点:")
    print(f"  • 杠杆交易，资金利用率高")
    print(f"  • 双向交易，可做多做空")
    print(f"  • 保证金制度，风险可控")
    print(f"  • 流动性好，成交活跃")
    print(f"  • 价格发现功能")

if __name__ == '__main__':
    """运行期货交易演示"""
    
    print("🎯 期货交易系统演示")
    print("=" * 60)
    
    try:
        # 1. 期货市场概览
        demonstrate_futures_markets()
        
        # 2. 期货策略回测
        print(f"\n" + "=" * 60)
        
        # 测试不同期货合约
        test_contracts = ['CL', 'GC', 'BTC']
        
        for contract in test_contracts:
            print(f"\n🔍 测试 {contract} 期货:")
            try:
                cerebro = run_futures_backtest(contract)
                print(f"✅ {contract} 期货回测完成")
            except Exception as e:
                print(f"❌ {contract} 期货回测失败: {e}")
        
        print(f"\n" + "=" * 60)
        print("🎉 期货交易系统演示完成!")
        print("\n📚 系统功能:")
        print("  ✅ 多种期货合约支持")
        print("  ✅ 杠杆交易模拟")
        print("  ✅ 保证金管理")
        print("  ✅ 动态止损止盈")
        print("  ✅ 技术指标策略")
        print("  ✅ 风险控制机制")
        
        print(f"\n⚠️ 风险提示:")
        print(f"  • 期货交易风险极高")
        print(f"  • 杠杆放大收益和损失")
        print(f"  • 可能损失全部本金")
        print(f"  • 务必充分了解风险")
        print(f"  • 建议从模拟开始")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()