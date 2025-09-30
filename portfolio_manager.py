#!/usr/bin/env python3
"""
智能投资组合管理与自动交易系统
Intelligent Portfolio Management & Auto Trading System

基于自选股池和四维分析结果进行自动买卖交易，形成智能投资组合
"""

import os
import sys
import json
import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from examples.stock_screener import StockScreener, run_stock_screening


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    last_updated: str
    entry_date: str
    entry_score: float  # 买入时的四维分析得分


@dataclass
class Transaction:
    """交易记录"""
    timestamp: str
    symbol: str
    action: str  # 'BUY' or 'SELL'
    shares: int
    price: float
    total_amount: float
    commission: float
    reason: str  # 交易原因
    score_at_trade: float  # 交易时的得分


@dataclass
class PortfolioSummary:
    """投资组合摘要"""
    total_value: float
    cash: float
    invested_value: float
    total_pnl: float
    total_pnl_pct: float
    num_positions: int
    last_updated: str


class AutoTradingEngine:
    """自动交易引擎"""
    
    def __init__(
        self,
        initial_cash: float = 100000.0,
        max_position_size: float = 0.1,  # 单只股票最大仓位比例 10%
        min_score_buy: float = 75.0,     # 买入最低分数
        min_score_hold: float = 65.0,    # 持有最低分数
        max_positions: int = 10,         # 最大持仓数量
        commission_rate: float = 0.001,  # 手续费率 0.1%
        rebalance_threshold: float = 0.05,  # 重新平衡阈值 5%
    ):
        """
        初始化自动交易引擎
        
        Args:
            initial_cash: 初始资金
            max_position_size: 单只股票最大仓位比例
            min_score_buy: 买入最低分数阈值
            min_score_hold: 持有最低分数阈值
            max_positions: 最大持仓数量
            commission_rate: 交易手续费率
            rebalance_threshold: 重新平衡阈值
        """
        self.initial_cash = initial_cash
        self.max_position_size = max_position_size
        self.min_score_buy = min_score_buy
        self.min_score_hold = min_score_hold
        self.max_positions = max_positions
        self.commission_rate = commission_rate
        self.rebalance_threshold = rebalance_threshold
        
        # 数据文件路径
        self.portfolio_file = "data/portfolio.json"
        self.transactions_file = "data/transactions.json"
        
        # 初始化数据目录
        os.makedirs("data", exist_ok=True)
        
        # 加载或初始化投资组合数据
        self.portfolio = self._load_portfolio()
        self.transactions = self._load_transactions()
        
        # 初始化筛选器
        self.screener = StockScreener()
    
    def _load_portfolio(self) -> Dict:
        """加载投资组合数据"""
        if os.path.exists(self.portfolio_file):
            with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                'cash': self.initial_cash,
                'positions': {},
                'created_at': datetime.datetime.now().isoformat(),
                'last_updated': datetime.datetime.now().isoformat()
            }
    
    def _save_portfolio(self):
        """保存投资组合数据"""
        self.portfolio['last_updated'] = datetime.datetime.now().isoformat()
        with open(self.portfolio_file, 'w', encoding='utf-8') as f:
            json.dump(self.portfolio, f, ensure_ascii=False, indent=2)
    
    def _load_transactions(self) -> List[Dict]:
        """加载交易记录"""
        if os.path.exists(self.transactions_file):
            with open(self.transactions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
    
    def _save_transactions(self):
        """保存交易记录"""
        with open(self.transactions_file, 'w', encoding='utf-8') as f:
            json.dump(self.transactions, f, ensure_ascii=False, indent=2)
    
    def _add_transaction(
        self,
        symbol: str,
        action: str,
        shares: int,
        price: float,
        reason: str,
        score: float
    ):
        """添加交易记录"""
        total_amount = shares * price
        commission = total_amount * self.commission_rate
        
        transaction = Transaction(
            timestamp=datetime.datetime.now().isoformat(),
            symbol=symbol,
            action=action,
            shares=shares,
            price=price,
            total_amount=total_amount,
            commission=commission,
            reason=reason,
            score_at_trade=score
        )
        
        self.transactions.append(asdict(transaction))
        self._save_transactions()
        
        return commission
    
    def get_current_positions(self) -> List[Position]:
        """获取当前所有持仓"""
        positions = []
        
        for symbol, pos_data in self.portfolio['positions'].items():
            # 获取当前价格（这里需要实际的价格获取逻辑）
            current_price = self._get_current_price(symbol)
            
            shares = pos_data['shares']
            avg_cost = pos_data['avg_cost']
            market_value = shares * current_price
            cost_basis = shares * avg_cost
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
            
            position = Position(
                symbol=symbol,
                shares=shares,
                avg_cost=avg_cost,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
                last_updated=datetime.datetime.now().isoformat(),
                entry_date=pos_data['entry_date'],
                entry_score=pos_data['entry_score']
            )
            
            positions.append(position)
        
        return positions
    
    def _get_current_price(self, symbol: str) -> float:
        """获取股票当前价格（模拟）"""
        # TODO: 实现真实的价格获取逻辑
        # 这里暂时返回一个模拟价格
        import random
        return round(random.uniform(50, 200), 2)
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """获取投资组合摘要"""
        positions = self.get_current_positions()
        
        invested_value = sum(pos.market_value for pos in positions)
        total_value = self.portfolio['cash'] + invested_value
        
        # 计算总盈亏
        total_cost = sum(pos.shares * pos.avg_cost for pos in positions)
        total_pnl = invested_value - total_cost
        total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
        
        return PortfolioSummary(
            total_value=total_value,
            cash=self.portfolio['cash'],
            invested_value=invested_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            num_positions=len(positions),
            last_updated=datetime.datetime.now().isoformat()
        )
    
    def analyze_watchlist_for_trading(self) -> List[Dict]:
        """分析自选股池，生成交易建议"""
        print("🔍 分析自选股池，生成交易信号...")
        
        # 获取自选股列表
        watchlist_symbols = self.screener.get_watchlist_symbols()
        if not watchlist_symbols:
            print("📝 自选股池为空，请先添加股票")
            return []
        
        # 分析自选股
        results, _ = run_stock_screening('watchlist')
        
        trading_signals = []
        current_positions = {pos.symbol: pos for pos in self.get_current_positions()}
        
        for stock in results:
            symbol = stock['symbol']
            score = stock['total_score']
            price = stock.get('price', self._get_current_price(symbol))
            
            signal = self._generate_trading_signal(symbol, score, price, current_positions)
            if signal:
                trading_signals.append(signal)
        
        return trading_signals
    
    def _generate_trading_signal(
        self,
        symbol: str,
        score: float,
        price: float,
        current_positions: Dict
    ) -> Optional[Dict]:
        """为单只股票生成交易信号"""
        
        is_held = symbol in current_positions
        
        if not is_held:
            # 新买入信号
            if score >= self.min_score_buy and len(current_positions) < self.max_positions:
                max_investment = self.portfolio['cash'] * self.max_position_size
                max_shares = int(max_investment // price)
                
                if max_shares > 0:
                    return {
                        'symbol': symbol,
                        'action': 'BUY',
                        'shares': max_shares,
                        'price': price,
                        'score': score,
                        'reason': f'新买入 - 得分{score:.1f}超过买入阈值{self.min_score_buy}',
                        'priority': score  # 用得分作为优先级
                    }
        else:
            # 持仓股票信号
            position = current_positions[symbol]
            
            if score < self.min_score_hold:
                # 卖出信号
                return {
                    'symbol': symbol,
                    'action': 'SELL',
                    'shares': position.shares,
                    'price': price,
                    'score': score,
                    'reason': f'卖出 - 得分{score:.1f}低于持有阈值{self.min_score_hold}',
                    'priority': 100 - score  # 得分越低优先级越高
                }
            elif score >= self.min_score_buy:
                # 加仓信号（如果仓位未满）
                current_weight = position.market_value / self.get_portfolio_summary().total_value
                if current_weight < self.max_position_size:
                    additional_investment = (self.max_position_size - current_weight) * self.get_portfolio_summary().total_value
                    additional_shares = int(additional_investment // price)
                    
                    if additional_shares > 0:
                        return {
                            'symbol': symbol,
                            'action': 'BUY',
                            'shares': additional_shares,
                            'price': price,
                            'score': score,
                            'reason': f'加仓 - 得分{score:.1f}优秀且仓位未满',
                            'priority': score
                        }
        
        return None
    
    def execute_trading_signals(self, signals: List[Dict], dry_run: bool = True) -> Dict:
        """执行交易信号"""
        
        if not signals:
            print("📭 没有交易信号需要执行")
            return {'executed': 0, 'skipped': 0, 'errors': 0}
        
        # 按优先级排序（卖出优先，然后按得分排序）
        sell_signals = [s for s in signals if s['action'] == 'SELL']
        buy_signals = [s for s in signals if s['action'] == 'BUY']
        
        sell_signals.sort(key=lambda x: x['priority'], reverse=True)
        buy_signals.sort(key=lambda x: x['priority'], reverse=True)
        
        ordered_signals = sell_signals + buy_signals
        
        results = {'executed': 0, 'skipped': 0, 'errors': 0}
        
        mode_text = '模拟' if dry_run else '实际'
        print(f"\n📋 {mode_text}交易执行计划:")
        print("=" * 80)
        
        for i, signal in enumerate(ordered_signals, 1):
            symbol = signal['symbol']
            action = signal['action']
            shares = signal['shares']
            price = signal['price']
            reason = signal['reason']
            score = signal['score']
            
            print(f"\n{i}. {action} {symbol}")
            print(f"   股数: {shares:,}")
            print(f"   价格: ${price:.2f}")
            print(f"   总额: ${shares * price:,.2f}")
            print(f"   得分: {score:.1f}")
            print(f"   原因: {reason}")
            
            if dry_run:
                print(f"   状态: 🔍 模拟执行")
                results['executed'] += 1
            else:
                try:
                    success = self._execute_single_trade(signal)
                    if success:
                        print(f"   状态: ✅ 执行成功")
                        results['executed'] += 1
                    else:
                        print(f"   状态: ⚠️ 执行跳过")
                        results['skipped'] += 1
                except Exception as e:
                    print(f"   状态: ❌ 执行失败 - {e}")
                    results['errors'] += 1
        
        print("\n" + "=" * 80)
        print(f"📊 执行结果: 成功{results['executed']} | 跳过{results['skipped']} | 失败{results['errors']}")
        
        return results
    
    def _execute_single_trade(self, signal: Dict) -> bool:
        """执行单笔交易"""
        symbol = signal['symbol']
        action = signal['action']
        shares = signal['shares']
        price = signal['price']
        reason = signal['reason']
        score = signal['score']
        
        commission = self._add_transaction(symbol, action, shares, price, reason, score)
        
        if action == 'BUY':
            total_cost = shares * price + commission
            
            if self.portfolio['cash'] < total_cost:
                return False  # 资金不足
            
            # 更新现金
            self.portfolio['cash'] -= total_cost
            
            # 更新持仓
            if symbol in self.portfolio['positions']:
                # 加仓
                old_shares = self.portfolio['positions'][symbol]['shares']
                old_cost = self.portfolio['positions'][symbol]['avg_cost']
                old_total_cost = old_shares * old_cost
                
                new_shares = old_shares + shares
                new_avg_cost = (old_total_cost + shares * price) / new_shares
                
                self.portfolio['positions'][symbol].update({
                    'shares': new_shares,
                    'avg_cost': new_avg_cost
                })
            else:
                # 新建仓位
                self.portfolio['positions'][symbol] = {
                    'shares': shares,
                    'avg_cost': price,
                    'entry_date': datetime.datetime.now().isoformat(),
                    'entry_score': score
                }
        
        elif action == 'SELL':
            if symbol not in self.portfolio['positions']:
                return False  # 没有持仓
            
            position = self.portfolio['positions'][symbol]
            if position['shares'] < shares:
                return False  # 股数不足
            
            # 更新现金
            total_proceeds = shares * price - commission
            self.portfolio['cash'] += total_proceeds
            
            # 更新持仓
            position['shares'] -= shares
            if position['shares'] == 0:
                del self.portfolio['positions'][symbol]
        
        self._save_portfolio()
        return True
    
    def print_portfolio_status(self):
        """打印投资组合状态"""
        summary = self.get_portfolio_summary()
        positions = self.get_current_positions()
        
        print("\n" + "=" * 60)
        print("💼 智能投资组合状态")
        print("=" * 60)
        
        print(f"\n💰 投资组合摘要:")
        print(f"   总价值: ${summary.total_value:,.2f}")
        print(f"   现金: ${summary.cash:,.2f} ({summary.cash/summary.total_value*100:.1f}%)")
        print(f"   投资价值: ${summary.invested_value:,.2f} ({summary.invested_value/summary.total_value*100:.1f}%)")
        print(f"   总盈亏: ${summary.total_pnl:,.2f} ({summary.total_pnl_pct:+.2f}%)")
        print(f"   持仓数量: {summary.num_positions}")
        
        if positions:
            print(f"\n📊 当前持仓:")
            print(f"{'股票':<8} {'股数':<8} {'成本':<8} {'现价':<8} {'市值':<12} {'盈亏':<12} {'盈亏%':<8} {'入场分':<8}")
            print("-" * 80)
            
            for pos in sorted(positions, key=lambda x: x.market_value, reverse=True):
                pnl_color = "🟢" if pos.unrealized_pnl >= 0 else "🔴"
                print(f"{pos.symbol:<8} {pos.shares:<8} {pos.avg_cost:<8.2f} {pos.current_price:<8.2f} "
                      f"${pos.market_value:<11.2f} {pnl_color}${pos.unrealized_pnl:<10.2f} "
                      f"{pos.unrealized_pnl_pct:+<7.1f}% {pos.entry_score:<8.1f}")
        else:
            print("\n📝 当前无持仓")
        
        print("\n" + "=" * 60)
    
    def run_auto_trading(self, dry_run: bool = True):
        """运行自动交易"""
        print("\n🤖 启动智能自动交易系统")
        print("=" * 60)
        print(f"📊 交易配置:")
        print(f"   买入阈值: {self.min_score_buy}分")
        print(f"   持有阈值: {self.min_score_hold}分")
        print(f"   最大仓位: {self.max_position_size*100:.0f}%")
        print(f"   最大持仓数: {self.max_positions}只")
        print(f"   手续费率: {self.commission_rate*100:.2f}%")
        mode_text = '🔍 模拟模式' if dry_run else '⚡ 实际交易'
        print(f"   执行模式: {mode_text}")
        print("=" * 60)
        
        # 显示当前投资组合状态
        self.print_portfolio_status()
        
        # 分析并生成交易信号
        signals = self.analyze_watchlist_for_trading()
        
        if signals:
            # 执行交易
            results = self.execute_trading_signals(signals, dry_run=dry_run)
            
            # 显示更新后的投资组合状态
            if not dry_run and results['executed'] > 0:
                print("\n📊 交易后投资组合状态:")
                self.print_portfolio_status()
        
        print("\n🎯 自动交易完成!")


def main():
    """主程序"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    # 初始化交易引擎
    engine = AutoTradingEngine()
    
    if command == 'status' or command == 'portfolio':
        # 显示投资组合状态
        engine.print_portfolio_status()
        
    elif command == 'analyze':
        # 分析交易信号
        signals = engine.analyze_watchlist_for_trading()
        if signals:
            print(f"\n🎯 发现 {len(signals)} 个交易信号")
            engine.execute_trading_signals(signals, dry_run=True)
        
    elif command == 'trade':
        # 执行实际交易
        dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
        engine.run_auto_trading(dry_run=dry_run)
        
    elif command == 'simulate' or command == 'sim':
        # 模拟交易
        engine.run_auto_trading(dry_run=True)
        
    elif command == 'history' or command == 'transactions':
        # 显示交易历史
        show_transaction_history(engine)
        
    elif command == 'reset':
        # 重置投资组合
        reset_portfolio(engine)
        
    else:
        print(f"❌ 未知命令: {command}")
        print_help()


def print_help():
    """打印帮助信息"""
    print("\n💼 智能投资组合管理与自动交易系统")
    print("=" * 60)
    print("📋 可用命令:")
    print("   portfolio/status     显示投资组合状态")
    print("   analyze             分析交易信号（不执行）")
    print("   simulate/sim        模拟自动交易")
    print("   trade               执行实际自动交易")
    print("   trade --dry-run     模拟执行交易")
    print("   history/transactions 显示交易历史")
    print("   reset               重置投资组合")
    print("\n💡 使用示例:")
    print("   python3 portfolio_manager.py status     # 查看投资组合")
    print("   python3 portfolio_manager.py simulate   # 模拟交易")
    print("   python3 portfolio_manager.py trade      # 实际交易")
    print("=" * 60)


def show_transaction_history(engine: AutoTradingEngine):
    """显示交易历史"""
    transactions = engine.transactions
    
    if not transactions:
        print("📝 暂无交易记录")
        return
    
    print("\n📈 交易历史记录")
    print("=" * 100)
    print(f"{'时间':<20} {'股票':<8} {'操作':<6} {'股数':<8} {'价格':<8} {'总额':<12} {'手续费':<8} {'得分':<6} {'原因':<20}")
    print("-" * 100)
    
    total_commission = 0
    for txn in transactions[-20:]:  # 显示最近20笔交易
        timestamp = txn['timestamp'][:19].replace('T', ' ')
        action_color = "🟢" if txn['action'] == 'BUY' else "🔴"
        total_commission += txn['commission']
        
        print(f"{timestamp:<20} {txn['symbol']:<8} {action_color}{txn['action']:<5} "
              f"{txn['shares']:<8} ${txn['price']:<7.2f} ${txn['total_amount']:<11.2f} "
              f"${txn['commission']:<7.2f} {txn['score_at_trade']:<6.1f} {txn['reason']:<20}")
    
    print("-" * 100)
    print(f"💰 总手续费: ${total_commission:.2f}")
    print(f"📊 交易笔数: {len(transactions)}")


def reset_portfolio(engine: AutoTradingEngine):
    """重置投资组合"""
    confirm = input("⚠️ 确认要重置投资组合吗？这将清除所有持仓和交易记录 (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        # 重置投资组合
        engine.portfolio = {
            'cash': engine.initial_cash,
            'positions': {},
            'created_at': datetime.datetime.now().isoformat(),
            'last_updated': datetime.datetime.now().isoformat()
        }
        engine.transactions = []
        
        engine._save_portfolio()
        engine._save_transactions()
        
        print("✅ 投资组合已重置")
        print(f"💰 初始资金: ${engine.initial_cash:,.2f}")
    else:
        print("❌ 操作已取消")


if __name__ == "__main__":
    main()