"""
简化模拟交易模块 - Simplified Paper Trading

实时模拟交易，自动策略执行，风险控制。

核心设计原则：
- 实时交易：连接实时数据，自动执行策略
- 风险控制：内置止损、止盈、仓位管理
- 简单接口：一行代码启动模拟交易
- 实时监控：显示实时盈亏和持仓状态
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import time
import logging
import json
import os

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class PaperPosition:
    """模拟持仓"""
    symbol: str
    shares: int
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    
    @property
    def value(self) -> float:
        """持仓价值"""
        return self.shares * self.current_price
    
    @property
    def pnl(self) -> float:
        """盈亏金额"""
        return (self.current_price - self.entry_price) * self.shares
    
    @property
    def pnl_percent(self) -> float:
        """盈亏百分比"""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price * 100
    
    def should_stop_loss(self) -> bool:
        """是否触发止损"""
        return self.stop_loss > 0 and self.current_price <= self.stop_loss
    
    def should_take_profit(self) -> bool:
        """是否触发止盈"""
        return self.take_profit > 0 and self.current_price >= self.take_profit

@dataclass
class PaperTrade:
    """模拟交易记录"""
    symbol: str
    action: str  # BUY/SELL
    shares: int
    price: float
    timestamp: datetime
    reason: str
    commission: float = 0.0
    pnl: float = 0.0  # 对于卖出交易的盈亏

@dataclass
class TradingAccount:
    """交易账户状态"""
    cash: float
    total_value: float
    positions: Dict[str, PaperPosition]
    daily_pnl: float
    total_pnl: float
    
    def to_dict(self) -> Dict:
        """转为字典"""
        return {
            'cash': self.cash,
            'total_value': self.total_value,
            'position_count': len(self.positions),
            'position_value': sum(pos.value for pos in self.positions.values()),
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'positions': {symbol: {
                'shares': pos.shares,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'pnl': pos.pnl,
                'pnl_percent': pos.pnl_percent
            } for symbol, pos in self.positions.items()}
        }

class PaperTrader:
    """
    简化模拟交易器
    
    特点：
    - 实时模拟交易
    - 自动策略执行
    - 风险控制（止损止盈）
    - 实时监控和报告
    """
    
    def __init__(self,
                 initial_capital: float = 100000,
                 commission: float = 0.001,
                 max_position_size: float = 0.2,  # 单个股票最大仓位比例
                 stop_loss_percent: float = 0.05,  # 默认止损5%
                 take_profit_percent: float = 0.10):  # 默认止盈10%
        """
        初始化模拟交易器
        
        Args:
            initial_capital: 初始资金
            commission: 手续费率
            max_position_size: 单个股票最大仓位比例
            stop_loss_percent: 止损百分比
            take_profit_percent: 止盈百分比
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.max_position_size = max_position_size
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent
        
        # 账户状态
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
        
        # 运行状态
        self.is_running = False
        self.trading_thread = None
        self.data_manager = None
        self.strategy = None
        self.symbols = []
        
        # 监控数据
        self.account_history = []
        self.last_update = None
        
        logger.info(f"模拟交易器初始化：资金${initial_capital:,.2f}")
    
    def set_strategy(self, strategy, symbols: List[str]):
        """
        设置交易策略和标的
        
        Args:
            strategy: 策略对象
            symbols: 交易标的列表
        """
        self.strategy = strategy
        self.symbols = symbols
        logger.info(f"设置策略：{strategy.name}，标的：{symbols}")
    
    def start_trading(self, update_interval: int = 60):
        """
        开始模拟交易
        
        Args:
            update_interval: 更新间隔（秒）
        """
        if self.is_running:
            logger.warning("模拟交易已在运行")
            return
        
        if not self.strategy or not self.symbols:
            raise ValueError("请先设置策略和交易标的")
        
        self.is_running = True
        
        # 启动交易线程
        self.trading_thread = threading.Thread(
            target=self._trading_loop,
            args=(update_interval,),
            daemon=True
        )
        self.trading_thread.start()
        
        logger.info("模拟交易已启动")
    
    def stop_trading(self):
        """停止模拟交易"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.trading_thread:
            self.trading_thread.join(timeout=5)
        
        logger.info("模拟交易已停止")
    
    def _trading_loop(self, update_interval: int):
        """交易主循环"""
        try:
            # 导入数据管理器
            from data_manager import DataManager
            self.data_manager = DataManager()
            
            while self.is_running:
                try:
                    # 更新所有持仓的当前价格
                    self._update_positions()
                    
                    # 检查止损止盈
                    self._check_risk_management()
                    
                    # 执行策略
                    self._execute_strategy()
                    
                    # 更新账户状态
                    self._update_account_status()
                    
                    # 保存历史记录
                    self._save_account_history()
                    
                    self.last_update = datetime.now()
                    
                    # 等待下次更新
                    time.sleep(update_interval)
                    
                except Exception as e:
                    logger.error(f"交易循环错误：{e}")
                    time.sleep(update_interval)
                    
        except Exception as e:
            logger.error(f"交易循环致命错误：{e}")
            self.is_running = False
    
    def _update_positions(self):
        """更新持仓价格"""
        for symbol in self.positions:
            try:
                # 获取最新价格
                current_price = self.data_manager.get_realtime_price(symbol)
                if current_price > 0:
                    self.positions[symbol].current_price = current_price
            except Exception as e:
                logger.warning(f"更新{symbol}价格失败：{e}")
    
    def _check_risk_management(self):
        """检查风险管理（止损止盈）"""
        to_sell = []
        
        for symbol, position in self.positions.items():
            if position.should_stop_loss():
                reason = f"止损：{position.current_price:.2f} <= {position.stop_loss:.2f}"
                to_sell.append((symbol, reason))
            elif position.should_take_profit():
                reason = f"止盈：{position.current_price:.2f} >= {position.take_profit:.2f}"
                to_sell.append((symbol, reason))
        
        # 执行止损止盈
        for symbol, reason in to_sell:
            self._sell_position(symbol, reason)
    
    def _execute_strategy(self):
        """执行策略"""
        for symbol in self.symbols:
            try:
                # 获取历史数据（最近30天）
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                data = self.data_manager.get_data(symbol, start_date, end_date)
                if data.empty or len(data) < 20:
                    continue
                
                # 生成交易信号
                signal_result = self.strategy.generate_signal(data)
                
                if signal_result.confidence < 0.5:  # 置信度不够
                    continue
                
                current_price = signal_result.price
                
                # 执行交易决策
                if signal_result.signal.value == "BUY" and symbol not in self.positions:
                    self._buy_stock(symbol, current_price, signal_result.reason)
                
                elif signal_result.signal.value == "SELL" and symbol in self.positions:
                    self._sell_position(symbol, signal_result.reason)
                
            except Exception as e:
                logger.warning(f"执行策略失败 {symbol}：{e}")
    
    def _buy_stock(self, symbol: str, price: float, reason: str):
        """买入股票"""
        # 计算买入金额（考虑最大仓位限制）
        total_value = self.get_total_value()
        max_investment = total_value * self.max_position_size
        
        # 使用可用现金的80%或最大仓位限制，取较小值
        available_cash = self.cash * 0.8
        investment = min(available_cash, max_investment)
        
        if investment < 1000:  # 最小投资额
            return
        
        # 计算股数（整手）
        shares = int(investment / price / 100) * 100
        if shares <= 0:
            return
        
        # 计算实际成本
        total_cost = shares * price * (1 + self.commission)
        
        if total_cost > self.cash:
            return
        
        # 执行买入
        self.cash -= total_cost
        
        # 计算止损止盈价格
        stop_loss = price * (1 - self.stop_loss_percent)
        take_profit = price * (1 + self.take_profit_percent)
        
        # 创建持仓
        position = PaperPosition(
            symbol=symbol,
            shares=shares,
            entry_price=price,
            entry_time=datetime.now(),
            current_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        
        # 记录交易
        trade = PaperTrade(
            symbol=symbol,
            action="BUY",
            shares=shares,
            price=price,
            timestamp=datetime.now(),
            reason=reason,
            commission=shares * price * self.commission
        )
        
        self.trades.append(trade)
        
        logger.info(f"买入：{shares} {symbol} @${price:.2f} - {reason}")
    
    def _sell_position(self, symbol: str, reason: str):
        """卖出持仓"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        current_price = position.current_price
        
        # 计算收益
        proceeds = position.shares * current_price * (1 - self.commission)
        self.cash += proceeds
        
        # 计算盈亏
        pnl = position.pnl
        
        # 记录交易
        trade = PaperTrade(
            symbol=symbol,
            action="SELL",
            shares=position.shares,
            price=current_price,
            timestamp=datetime.now(),
            reason=reason,
            commission=position.shares * current_price * self.commission,
            pnl=pnl
        )
        
        self.trades.append(trade)
        
        # 删除持仓
        del self.positions[symbol]
        
        logger.info(f"卖出：{position.shares} {symbol} @${current_price:.2f} "
                   f"盈亏：${pnl:.2f} - {reason}")
    
    def get_total_value(self) -> float:
        """获取总资产价值"""
        total = self.cash
        for position in self.positions.values():
            total += position.value
        return total
    
    def get_account_status(self) -> TradingAccount:
        """获取账户状态"""
        total_value = self.get_total_value()
        total_pnl = total_value - self.initial_capital
        
        # 计算当日盈亏（简化版）
        daily_pnl = 0.0
        if self.account_history:
            last_value = self.account_history[-1]['total_value']
            daily_pnl = total_value - last_value
        
        return TradingAccount(
            cash=self.cash,
            total_value=total_value,
            positions=self.positions.copy(),
            daily_pnl=daily_pnl,
            total_pnl=total_pnl
        )
    
    def _update_account_status(self):
        """更新账户状态"""
        pass  # 当前在get_account_status中实时计算
    
    def _save_account_history(self):
        """保存账户历史"""
        status = self.get_account_status()
        
        history_record = {
            'timestamp': datetime.now().isoformat(),
            'total_value': status.total_value,
            'cash': status.cash,
            'position_count': len(status.positions),
            'total_pnl': status.total_pnl
        }
        
        self.account_history.append(history_record)
        
        # 保持最近1000条记录
        if len(self.account_history) > 1000:
            self.account_history = self.account_history[-1000:]
    
    def get_performance_summary(self) -> str:
        """获取性能摘要"""
        status = self.get_account_status()
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.action == "SELL" and t.pnl > 0])
        
        win_rate = (winning_trades / max(total_trades // 2, 1)) * 100 if total_trades > 0 else 0
        
        return f"""
💰 模拟交易账户状态
==================
💵 现金：${status.cash:,.2f}
📈 总资产：${status.total_value:,.2f}
📊 总盈亏：${status.total_pnl:,.2f} ({status.total_pnl/self.initial_capital*100:.2f}%)
📅 今日盈亏：${status.daily_pnl:,.2f}

📋 持仓情况 ({len(status.positions)}个)
{self._format_positions(status.positions)}

📊 交易统计
-----------
总交易：{total_trades}笔
获利交易：{winning_trades}笔
胜率：{win_rate:.1f}%

⏰ 最后更新：{self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else '未更新'}
        """.strip()
    
    def _format_positions(self, positions: Dict[str, PaperPosition]) -> str:
        """格式化持仓显示"""
        if not positions:
            return "  无持仓"
        
        lines = []
        for symbol, pos in positions.items():
            lines.append(f"  {symbol}: {pos.shares}股 @${pos.entry_price:.2f} "
                        f"当前${pos.current_price:.2f} "
                        f"盈亏${pos.pnl:.2f}({pos.pnl_percent:.1f}%)")
        
        return "\n".join(lines)
    
    def save_results(self, filename: str = None) -> str:
        """保存交易结果"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"paper_trading_{timestamp}.json"
        
        save_dir = "data/paper_trading"
        os.makedirs(save_dir, exist_ok=True)
        
        filepath = os.path.join(save_dir, filename)
        
        # 准备保存数据
        save_data = {
            'account_status': self.get_account_status().to_dict(),
            'trades': [asdict(trade) for trade in self.trades],
            'account_history': self.account_history,
            'config': {
                'initial_capital': self.initial_capital,
                'commission': self.commission,
                'max_position_size': self.max_position_size,
                'stop_loss_percent': self.stop_loss_percent,
                'take_profit_percent': self.take_profit_percent
            }
        }
        
        # 处理日期序列化
        def date_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=date_serializer)
        
        logger.info(f"交易结果保存到：{filepath}")
        return filepath

# 便捷函数
def start_paper_trading(strategy_name: str, symbols: List[str],
                       strategy_params: Dict = None,
                       initial_capital: float = 100000,
                       update_interval: int = 300) -> PaperTrader:
    """
    启动模拟交易 - 一行代码开始交易
    
    Args:
        strategy_name: 策略名称
        symbols: 交易标的列表
        strategy_params: 策略参数
        initial_capital: 初始资金
        update_interval: 更新间隔（秒）
        
    Returns:
        模拟交易器
    """
    try:
        from strategy_manager import create_strategy
        
        # 创建策略
        strategy = create_strategy(strategy_name, strategy_params)
        
        # 创建交易器
        trader = PaperTrader(initial_capital=initial_capital)
        trader.set_strategy(strategy, symbols)
        
        # 启动交易
        trader.start_trading(update_interval)
        
        return trader
        
    except Exception as e:
        logger.error(f"启动模拟交易失败：{e}")
        raise

# 使用示例和测试
if __name__ == "__main__":
    print("🚀 简化模拟交易模块测试")
    print("=" * 50)
    
    try:
        # 创建模拟交易器
        trader = PaperTrader(initial_capital=100000)
        
        print(f"✅ 模拟交易器创建成功")
        print(f"   初始资金：${trader.initial_capital:,.2f}")
        print(f"   手续费率：{trader.commission:.1%}")
        print(f"   最大仓位：{trader.max_position_size:.1%}")
        
        # 模拟添加持仓
        print("\n🔧 测试持仓管理...")
        
        position = PaperPosition(
            symbol="TEST",
            shares=1000,
            entry_price=100.0,
            entry_time=datetime.now(),
            current_price=105.0,
            stop_loss=95.0,
            take_profit=110.0
        )
        
        trader.positions["TEST"] = position
        
        print(f"✅ 添加测试持仓：1000股TEST @$100.00")
        print(f"   当前价格：${position.current_price:.2f}")
        print(f"   盈亏：${position.pnl:.2f} ({position.pnl_percent:.1f}%)")
        print(f"   止损：${position.stop_loss:.2f}")
        print(f"   止盈：${position.take_profit:.2f}")
        
        # 测试账户状态
        print("\n📊 测试账户状态...")
        status = trader.get_account_status()
        
        print(f"✅ 总资产：${status.total_value:,.2f}")
        print(f"   现金：${status.cash:,.2f}")
        print(f"   持仓价值：${sum(pos.value for pos in status.positions.values()):,.2f}")
        print(f"   总盈亏：${status.total_pnl:,.2f}")
        
        # 测试性能摘要
        print("\n📈 性能摘要:")
        print(trader.get_performance_summary())
        
        # 测试保存结果
        print("\n💾 测试结果保存...")
        save_path = trader.save_results()
        print(f"✅ 结果已保存：{save_path}")
        
    except Exception as e:
        print(f"❌ 模拟交易测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 简化模拟交易模块核心特性：")
    print("  ✅ 实时交易 - 自动获取实时数据执行策略")
    print("  ✅ 风险控制 - 内置止损、止盈、仓位管理")
    print("  ✅ 简单接口 - start_paper_trading() 一行代码启动")
    print("  ✅ 实时监控 - 显示实时盈亏和持仓状态")
    print("  ✅ 历史记录 - 自动保存交易记录和账户历史")
    print("=" * 50)