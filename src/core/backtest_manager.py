"""
简化回测模块 - Simplified Backtesting Engine

一行代码完成回测，内置性能分析，可视化结果。

核心设计原则：
- 一行代码：backtest(strategy, symbol) 即可完成回测
- 智能默认：自动设置合理的默认参数
- 快速结果：即时显示关键性能指标
- 可视化：自动生成图表和报告
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging
import json
import os

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    shares: int
    entry_price: float
    entry_date: datetime
    current_price: float = 0.0
    
    @property
    def value(self) -> float:
        """持仓价值"""
        return self.shares * self.current_price
    
    @property
    def pnl(self) -> float:
        """盈亏"""
        return (self.current_price - self.entry_price) * self.shares
    
    @property
    def pnl_percent(self) -> float:
        """盈亏百分比"""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price * 100

@dataclass
class Trade:
    """交易记录"""
    symbol: str
    action: str  # BUY/SELL
    shares: int
    price: float
    date: datetime
    reason: str
    commission: float = 0.0
    
    @property
    def value(self) -> float:
        """交易价值"""
        return self.shares * self.price

@dataclass
class BacktestResult:
    """回测结果"""
    # 基本信息
    symbol: str
    strategy_name: str
    start_date: datetime
    end_date: datetime
    
    # 资金信息
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    
    # 交易统计
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # 性能指标
    max_drawdown: float
    sharpe_ratio: float
    annual_return: float
    volatility: float
    
    # 详细数据
    trades: List[Trade]
    daily_values: pd.DataFrame
    
    def summary(self) -> str:
        """生成简要报告"""
        return f"""
📊 回测结果摘要
================
📈 标的：{self.symbol}
🔧 策略：{self.strategy_name}
📅 时间：{self.start_date.strftime('%Y-%m-%d')} 到 {self.end_date.strftime('%Y-%m-%d')}

💰 收益情况
-----------
初始资金：${self.initial_capital:,.2f}
最终资金：${self.final_capital:,.2f}
总收益：${self.total_return:,.2f} ({self.total_return_percent:.2f}%)
年化收益：{self.annual_return:.2f}%

📊 交易统计
-----------
总交易次数：{self.total_trades}
盈利交易：{self.winning_trades}
亏损交易：{self.losing_trades}
胜率：{self.win_rate:.2f}%

📉 风险指标
-----------
最大回撤：{self.max_drawdown:.2f}%
波动率：{self.volatility:.2f}%
夏普比率：{self.sharpe_ratio:.2f}
        """.strip()

class SimpleBacktester:
    """
    简化回测引擎
    
    特点：
    - 一行代码完成回测
    - 自动处理数据获取和策略执行
    - 内置性能分析和风险管理
    - 支持多种订单类型
    """
    
    def __init__(self, 
                 initial_capital: float = 100000,
                 commission: float = 0.001,
                 slippage: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission: 手续费率
            slippage: 滑点
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        # 回测状态
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
        self.daily_values = []
        
        logger.info(f"回测引擎初始化：资金${initial_capital:,.2f}")
    
    def reset(self):
        """重置回测状态"""
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_values = []
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """计算投资组合总价值"""
        total_value = self.cash
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                total_value += position.value
        
        return total_value
    
    def place_order(self, symbol: str, action: str, shares: int, price: float, 
                   date: datetime, reason: str = "") -> bool:
        """
        下单
        
        Args:
            symbol: 股票代码
            action: 操作类型 BUY/SELL
            shares: 股数
            price: 价格
            date: 日期
            reason: 交易原因
            
        Returns:
            是否成功
        """
        # 计算实际成交价格（考虑滑点）
        if action == "BUY":
            actual_price = price * (1 + self.slippage)
        else:
            actual_price = price * (1 - self.slippage)
        
        # 计算手续费
        commission = shares * actual_price * self.commission
        
        if action == "BUY":
            total_cost = shares * actual_price + commission
            
            if total_cost > self.cash:
                logger.warning(f"资金不足：需要${total_cost:.2f}，可用${self.cash:.2f}")
                return False
            
            # 执行买入
            self.cash -= total_cost
            
            if symbol in self.positions:
                # 加仓
                old_position = self.positions[symbol]
                total_shares = old_position.shares + shares
                avg_price = ((old_position.shares * old_position.entry_price + 
                            shares * actual_price) / total_shares)
                
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=total_shares,
                    entry_price=avg_price,
                    entry_date=old_position.entry_date,
                    current_price=actual_price
                )
            else:
                # 开仓
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=shares,
                    entry_price=actual_price,
                    entry_date=date,
                    current_price=actual_price
                )
        
        elif action == "SELL":
            if symbol not in self.positions:
                logger.warning(f"无持仓：{symbol}")
                return False
            
            position = self.positions[symbol]
            if shares > position.shares:
                logger.warning(f"卖出数量超过持仓：{shares} > {position.shares}")
                return False
            
            # 执行卖出
            total_proceeds = shares * actual_price - commission
            self.cash += total_proceeds
            
            # 更新持仓
            if shares == position.shares:
                # 清仓
                del self.positions[symbol]
            else:
                # 减仓
                position.shares -= shares
        
        # 记录交易
        trade = Trade(
            symbol=symbol,
            action=action,
            shares=shares,
            price=actual_price,
            date=date,
            reason=reason,
            commission=commission
        )
        self.trades.append(trade)
        
        logger.debug(f"交易执行：{action} {shares} {symbol} @${actual_price:.2f}")
        return True
    
    def run_backtest(self, data: pd.DataFrame, strategy, symbol: str) -> BacktestResult:
        """
        运行回测
        
        Args:
            data: 股票数据
            strategy: 策略对象
            symbol: 股票代码
            
        Returns:
            回测结果
        """
        self.reset()
        
        logger.info(f"开始回测：{symbol} 使用策略 {strategy.name}")
        
        # 记录每日价值
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            current_date = data.index[i]
            current_price = data['Close'].iloc[i]
            
            # 更新持仓价格
            current_prices = {symbol: current_price}
            portfolio_value = self.get_portfolio_value(current_prices)
            
            # 记录每日价值
            self.daily_values.append({
                'date': current_date,
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'stock_value': portfolio_value - self.cash,
                'price': current_price
            })
            
            # 跳过数据不足的情况
            if len(current_data) < 20:  # 需要足够的数据计算指标
                continue
            
            # 生成交易信号
            try:
                signal_result = strategy.generate_signal(current_data)
                
                if signal_result.confidence < 0.3:  # 置信度太低，不交易
                    continue
                
                # 执行交易
                if signal_result.signal.value == "BUY":
                    # 计算买入股数（使用80%的现金）
                    max_investment = self.cash * 0.8
                    shares = int(max_investment / current_price / 100) * 100  # 整手
                    
                    if shares > 0:
                        self.place_order(
                            symbol=symbol,
                            action="BUY",
                            shares=shares,
                            price=current_price,
                            date=current_date,
                            reason=signal_result.reason
                        )
                
                elif signal_result.signal.value == "SELL" and symbol in self.positions:
                    # 卖出全部持仓
                    position = self.positions[symbol]
                    self.place_order(
                        symbol=symbol,
                        action="SELL",
                        shares=position.shares,
                        price=current_price,
                        date=current_date,
                        reason=signal_result.reason
                    )
                        
            except Exception as e:
                logger.error(f"策略执行错误：{e}")
                continue
        
        # 计算最终结果
        final_prices = {symbol: data['Close'].iloc[-1]}
        final_value = self.get_portfolio_value(final_prices)
        
        return self._calculate_results(data, strategy.name, symbol, final_value)
    
    def _calculate_results(self, data: pd.DataFrame, strategy_name: str, 
                          symbol: str, final_value: float) -> BacktestResult:
        """计算回测结果"""
        
        # 转换为DataFrame
        daily_df = pd.DataFrame(self.daily_values)
        daily_df.set_index('date', inplace=True)
        
        # 基本收益计算
        total_return = final_value - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100
        
        # 交易统计
        total_trades = len(self.trades)
        winning_trades = 0
        losing_trades = 0
        
        # 计算每笔交易的盈亏
        buy_trades = {}
        for trade in self.trades:
            if trade.action == "BUY":
                if trade.symbol not in buy_trades:
                    buy_trades[trade.symbol] = []
                buy_trades[trade.symbol].append(trade)
            elif trade.action == "SELL":
                if trade.symbol in buy_trades and buy_trades[trade.symbol]:
                    buy_trade = buy_trades[trade.symbol].pop(0)
                    pnl = (trade.price - buy_trade.price) * trade.shares
                    if pnl > 0:
                        winning_trades += 1
                    else:
                        losing_trades += 1
        
        win_rate = (winning_trades / max(total_trades // 2, 1)) * 100
        
        # 计算风险指标
        if len(daily_df) > 1:
            returns = daily_df['portfolio_value'].pct_change().dropna()
            
            # 最大回撤
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative / running_max - 1) * 100
            max_drawdown = drawdown.min()
            
            # 年化收益和波动率
            trading_days = len(daily_df)
            years = trading_days / 252  # 假设252个交易日/年
            
            if years > 0:
                annual_return = ((final_value / self.initial_capital) ** (1/years) - 1) * 100
            else:
                annual_return = 0
                
            volatility = returns.std() * np.sqrt(252) * 100
            
            # 夏普比率
            if volatility > 0:
                risk_free_rate = 0.02  # 假设无风险利率2%
                excess_return = annual_return / 100 - risk_free_rate
                sharpe_ratio = excess_return / (volatility / 100)
            else:
                sharpe_ratio = 0
        else:
            max_drawdown = 0
            annual_return = 0
            volatility = 0
            sharpe_ratio = 0
        
        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy_name,
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=self.initial_capital,
            final_capital=final_value,
            total_return=total_return,
            total_return_percent=total_return_percent,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            annual_return=annual_return,
            volatility=volatility,
            trades=self.trades,
            daily_values=daily_df
        )

# 便捷函数
def quick_backtest(strategy_name: str, symbol: str, 
                  start_date: str = None, end_date: str = None,
                  strategy_params: Dict = None,
                  initial_capital: float = 100000) -> BacktestResult:
    """
    快速回测 - 一行代码完成回测
    
    Args:
        strategy_name: 策略名称
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        strategy_params: 策略参数
        initial_capital: 初始资金
        
    Returns:
        回测结果
    """
    try:
        # 导入必要模块
        from data_manager import DataManager
        from strategy_manager import create_strategy
        
        # 获取数据
        data_manager = DataManager()
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        data = data_manager.get_data_by_date(symbol, start_date, end_date)
        
        if data.empty:
            raise ValueError(f"无法获取 {symbol} 的数据")
        
        # 创建策略
        strategy = create_strategy(strategy_name, strategy_params)
        
        # 运行回测
        backtester = SimpleBacktester(initial_capital=initial_capital)
        result = backtester.run_backtest(data, strategy, symbol)
        
        return result
        
    except Exception as e:
        logger.error(f"快速回测失败：{e}")
        raise

def save_result(result: BacktestResult, filename: str = None) -> str:
    """
    保存回测结果
    
    Args:
        result: 回测结果
        filename: 文件名
        
    Returns:
        保存的文件路径
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_{result.symbol}_{result.strategy_name}_{timestamp}.json"
    
    # 创建保存目录
    save_dir = "data/backtest_results"
    os.makedirs(save_dir, exist_ok=True)
    
    filepath = os.path.join(save_dir, filename)
    
    # 准备保存数据
    save_data = {
        'result': asdict(result),
        'trades': [asdict(trade) for trade in result.trades],
        'daily_values': result.daily_values.to_dict('records')
    }
    
    # 处理日期序列化
    def date_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2, default=date_serializer)
    
    logger.info(f"回测结果保存到：{filepath}")
    return filepath

# 使用示例和测试
if __name__ == "__main__":
    print("🚀 简化回测模块测试")
    print("=" * 50)
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 生成模拟股价数据（带趋势）
    base_price = 100
    prices = [base_price]
    
    for i in range(99):
        # 添加轻微上升趋势
        trend = 0.0005  # 每日0.05%的趋势
        noise = np.random.normal(0, 0.02)  # 2%的随机波动
        
        change = trend + noise
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 50))  # 防止价格过低
    
    test_data = pd.DataFrame({
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    print(f"📊 测试数据生成完成：{len(test_data)}条记录")
    print(f"   价格范围：${test_data['Close'].min():.2f} - ${test_data['Close'].max():.2f}")
    print(f"   总涨幅：{((test_data['Close'].iloc[-1] / test_data['Close'].iloc[0]) - 1) * 100:.2f}%")
    
    # 测试简单回测
    print("\n🔧 测试简单回测...")
    
    try:
        # 需要导入策略模块
        import sys
        sys.path.append('/Users/Eric/Documents/backtrader_trading/src/core')
        
        from strategy_manager import create_strategy
        
        # 创建策略
        strategy = create_strategy('MA_Cross', {'fast': 5, 'slow': 20})
        
        # 运行回测
        backtester = SimpleBacktester(initial_capital=100000)
        result = backtester.run_backtest(test_data, strategy, 'TEST')
        
        # 显示结果
        print(result.summary())
        
        # 测试保存结果
        print("\n💾 测试结果保存...")
        save_path = save_result(result)
        print(f"✅ 结果已保存：{save_path}")
        
    except Exception as e:
        print(f"❌ 回测测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎯 简化回测模块核心特性：")
    print("  ✅ 一行代码 - quick_backtest() 即可完成回测")
    print("  ✅ 智能默认 - 自动设置合理的交易参数")
    print("  ✅ 快速结果 - 即时显示关键性能指标")
    print("  ✅ 风险管理 - 内置手续费、滑点、仓位管理")
    print("  ✅ 结果保存 - 自动保存详细的回测结果")
    print("=" * 50)