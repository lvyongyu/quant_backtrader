"""
仓位控制系统

实现智能仓位管理，支持多种仓位计算方法，包括Kelly公式、
固定比例、ATR仓位等算法，防止过度投资，优化资金配置。

核心功能：
1. Kelly公式仓位计算
2. 固定比例仓位控制
3. ATR基础仓位调整
4. 波动率调整仓位
5. 动态仓位优化
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import math

from . import PositionSizeMethod, RiskLevel


@dataclass
class PositionInfo:
    """仓位信息数据类"""
    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight: float  # 在投资组合中的权重
    entry_time: datetime
    
    def update_price(self, new_price: float):
        """更新价格和相关计算"""
        self.current_price = new_price
        self.market_value = self.quantity * new_price
        self.unrealized_pnl = (new_price - self.entry_price) * self.quantity
        self.unrealized_pnl_pct = (new_price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'market_value': self.market_value,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_pct': self.unrealized_pnl_pct,
            'weight': self.weight,
            'entry_time': self.entry_time.isoformat()
        }


@dataclass
class PositionLimits:
    """仓位限制配置"""
    max_single_position_pct: float = 0.1    # 单个仓位最大比例 10%
    max_total_position_pct: float = 0.8     # 总仓位最大比例 80%
    max_positions_count: int = 10           # 最大持仓数量
    min_position_value: float = 1000        # 最小仓位价值
    max_correlation: float = 0.7            # 最大相关性
    max_sector_exposure: float = 0.3        # 单一行业最大敞口 30%
    
    def validate(self) -> bool:
        """验证参数有效性"""
        return (0 < self.max_single_position_pct <= 1 and
                0 < self.max_total_position_pct <= 1 and
                self.max_positions_count > 0 and
                self.min_position_value > 0 and
                0 < self.max_correlation <= 1 and
                0 < self.max_sector_exposure <= 1)


class PositionManager:
    """
    仓位管理器
    
    负责管理所有持仓，计算仓位大小，控制风险敞口，
    优化资金配置，确保投资组合的安全性和盈利性。
    """
    
    def __init__(self, position_limits: PositionLimits = None):
        self.position_limits = position_limits or PositionLimits()
        self.positions: Dict[str, PositionInfo] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 历史数据（用于Kelly公式等计算）
        self.trade_history: List[Dict] = []
        self.return_history: List[float] = []
        
        # 统计数据
        self.total_trades = 0
        self.winning_trades = 0
        self.total_return = 0.0
        
        self.logger.info("仓位管理器初始化完成")
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              account_value: float, method: PositionSizeMethod,
                              **kwargs) -> int:
        """
        计算仓位大小
        
        Args:
            symbol: 股票代码
            entry_price: 入场价格
            account_value: 账户价值
            method: 仓位计算方法
            **kwargs: 其他参数
            
        Returns:
            建议仓位数量
        """
        if method == PositionSizeMethod.FIXED_PERCENTAGE:
            return self._calculate_fixed_percentage(entry_price, account_value, kwargs.get('percentage', 0.05))
            
        elif method == PositionSizeMethod.FIXED_AMOUNT:
            return self._calculate_fixed_amount(entry_price, kwargs.get('amount', 5000))
            
        elif method == PositionSizeMethod.KELLY_CRITERION:
            return self._calculate_kelly_position(symbol, entry_price, account_value, kwargs)
            
        elif method == PositionSizeMethod.ATR_BASED:
            return self._calculate_atr_position(entry_price, account_value, kwargs)
            
        elif method == PositionSizeMethod.VOLATILITY_ADJUSTED:
            return self._calculate_volatility_adjusted(entry_price, account_value, kwargs)
            
        else:
            # 默认使用固定比例 5%
            return self._calculate_fixed_percentage(entry_price, account_value, 0.05)
    
    def _calculate_fixed_percentage(self, entry_price: float, account_value: float, 
                                  percentage: float) -> int:
        """固定比例仓位计算"""
        # 限制在最大单仓位比例内
        actual_percentage = min(percentage, self.position_limits.max_single_position_pct)
        position_value = account_value * actual_percentage
        quantity = int(position_value / entry_price)
        
        self.logger.debug("固定比例仓位: %.1f%% = %d股", actual_percentage * 100, quantity)
        return quantity
    
    def _calculate_fixed_amount(self, entry_price: float, amount: float) -> int:
        """固定金额仓位计算"""
        quantity = int(amount / entry_price)
        self.logger.debug("固定金额仓位: $%.2f = %d股", amount, quantity)
        return quantity
    
    def _calculate_kelly_position(self, symbol: str, entry_price: float, 
                                account_value: float, kwargs: Dict) -> int:
        """Kelly公式仓位计算"""
        # 获取历史胜率和盈亏比
        win_rate = self.winning_trades / max(1, self.total_trades)
        
        if len(self.return_history) < 10:
            # 数据不足，使用保守的固定比例
            return self._calculate_fixed_percentage(entry_price, account_value, 0.02)
        
        # 计算平均盈利和亏损
        positive_returns = [r for r in self.return_history if r > 0]
        negative_returns = [r for r in self.return_history if r < 0]
        
        if not positive_returns or not negative_returns:
            return self._calculate_fixed_percentage(entry_price, account_value, 0.02)
        
        avg_win = sum(positive_returns) / len(positive_returns)
        avg_loss = abs(sum(negative_returns) / len(negative_returns))
        
        # Kelly公式: f = (bp - q) / b
        # 其中 b = 盈亏比, p = 胜率, q = 败率
        if avg_loss > 0:
            b = avg_win / avg_loss  # 盈亏比
            p = win_rate             # 胜率
            q = 1 - win_rate        # 败率
            
            kelly_fraction = (b * p - q) / b
            
            # 限制Kelly比例在合理范围内
            kelly_fraction = max(0, min(0.25, kelly_fraction))  # 0-25%
            
            # 应用Kelly分数的一半（更保守）
            conservative_kelly = kelly_fraction * 0.5
            
            position_value = account_value * conservative_kelly
            quantity = int(position_value / entry_price)
            
            self.logger.debug("Kelly仓位: %.1f%% (原始Kelly: %.1f%%) = %d股", 
                            conservative_kelly * 100, kelly_fraction * 100, quantity)
            return quantity
        
        # 无法计算Kelly，使用固定比例
        return self._calculate_fixed_percentage(entry_price, account_value, 0.02)
    
    def _calculate_atr_position(self, entry_price: float, account_value: float, 
                              kwargs: Dict) -> int:
        """ATR基础仓位计算"""
        atr = kwargs.get('atr', entry_price * 0.02)  # 默认ATR为价格的2%
        risk_amount = account_value * kwargs.get('risk_pct', 0.01)  # 默认风险1%
        atr_multiplier = kwargs.get('atr_multiplier', 2.0)
        
        # 基于ATR计算仓位
        if atr > 0:
            quantity = int(risk_amount / (atr * atr_multiplier))
            
            # 确保不超过最大仓位限制
            max_position_value = account_value * self.position_limits.max_single_position_pct
            max_quantity = int(max_position_value / entry_price)
            quantity = min(quantity, max_quantity)
            
            self.logger.debug("ATR仓位: ATR=%.2f 风险=$%.2f = %d股", atr, risk_amount, quantity)
            return quantity
        
        return self._calculate_fixed_percentage(entry_price, account_value, 0.02)
    
    def _calculate_volatility_adjusted(self, entry_price: float, account_value: float, 
                                     kwargs: Dict) -> int:
        """波动率调整仓位计算"""
        volatility = kwargs.get('volatility', 0.02)  # 默认波动率2%
        base_percentage = kwargs.get('base_percentage', 0.05)  # 基础比例5%
        
        # 根据波动率调整仓位
        # 波动率越高，仓位越小
        volatility_adjustment = 1 / (1 + volatility * 10)
        adjusted_percentage = base_percentage * volatility_adjustment
        
        # 确保在限制范围内
        adjusted_percentage = min(adjusted_percentage, self.position_limits.max_single_position_pct)
        
        position_value = account_value * adjusted_percentage
        quantity = int(position_value / entry_price)
        
        self.logger.debug("波动率调整仓位: 波动率=%.2f%% 调整后比例=%.1f%% = %d股", 
                         volatility * 100, adjusted_percentage * 100, quantity)
        return quantity
    
    def add_position(self, symbol: str, quantity: int, entry_price: float) -> bool:
        """
        添加新仓位
        
        Args:
            symbol: 股票代码
            quantity: 数量
            entry_price: 入场价格
            
        Returns:
            是否成功添加
        """
        # 检查是否超过最大持仓数量
        if len(self.positions) >= self.position_limits.max_positions_count:
            self.logger.warning("达到最大持仓数量限制: %d", self.position_limits.max_positions_count)
            return False
        
        # 检查最小仓位价值
        position_value = quantity * entry_price
        if position_value < self.position_limits.min_position_value:
            self.logger.warning("仓位价值 $%.2f 低于最小要求 $%.2f", 
                              position_value, self.position_limits.min_position_value)
            return False
        
        # 创建仓位信息
        position = PositionInfo(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            market_value=position_value,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
            weight=0.0,  # 稍后计算
            entry_time=datetime.now()
        )
        
        self.positions[symbol] = position
        self.total_trades += 1
        
        self.logger.info("添加仓位: %s %d股 @$%.2f", symbol, quantity, entry_price)
        return True
    
    def remove_position(self, symbol: str, exit_price: Optional[float] = None) -> bool:
        """
        移除仓位
        
        Args:
            symbol: 股票代码
            exit_price: 退出价格
            
        Returns:
            是否成功移除
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # 记录交易结果
        if exit_price:
            profit_loss = (exit_price - position.entry_price) * position.quantity
            return_pct = (exit_price - position.entry_price) / position.entry_price
            
            self.return_history.append(return_pct)
            self.total_return += return_pct
            
            if profit_loss > 0:
                self.winning_trades += 1
            
            # 记录交易历史
            trade_record = {
                'symbol': symbol,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'profit_loss': profit_loss,
                'return_pct': return_pct,
                'entry_time': position.entry_time,
                'exit_time': datetime.now()
            }
            self.trade_history.append(trade_record)
            
            self.logger.info("移除仓位: %s 盈亏=$%.2f (%.2f%%)", symbol, profit_loss, return_pct * 100)
        
        del self.positions[symbol]
        return True
    
    def update_prices(self, price_updates: Dict[str, float]):
        """批量更新仓位价格"""
        for symbol, price in price_updates.items():
            if symbol in self.positions:
                self.positions[symbol].update_price(price)
        
        # 重新计算权重
        self._recalculate_weights()
    
    def _recalculate_weights(self):
        """重新计算各仓位权重"""
        total_value = sum(pos.market_value for pos in self.positions.values())
        
        if total_value > 0:
            for position in self.positions.values():
                position.weight = position.market_value / total_value
    
    def get_portfolio_summary(self, account_value: float) -> Dict:
        """获取投资组合摘要"""
        total_market_value = sum(pos.market_value for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        position_pct = total_market_value / account_value if account_value > 0 else 0
        
        return {
            'positions_count': len(self.positions),
            'total_market_value': total_market_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'position_percentage': position_pct,
            'available_cash': account_value - total_market_value,
            'largest_position': max((pos.weight for pos in self.positions.values()), default=0),
            'win_rate': self.winning_trades / max(1, self.total_trades),
            'total_return': self.total_return
        }
    
    def get_position_info(self, symbol: str) -> Optional[Dict]:
        """获取特定仓位信息"""
        if symbol in self.positions:
            return self.positions[symbol].to_dict()
        return None
    
    def get_all_positions(self) -> Dict[str, Dict]:
        """获取所有仓位信息"""
        return {symbol: pos.to_dict() for symbol, pos in self.positions.items()}
    
    def check_position_limits(self, symbol: str, quantity: int, entry_price: float,
                            account_value: float) -> Tuple[bool, str]:
        """
        检查仓位是否符合限制
        
        Args:
            symbol: 股票代码
            quantity: 数量
            entry_price: 入场价格
            account_value: 账户价值
            
        Returns:
            (是否通过检查, 原因说明)
        """
        position_value = quantity * entry_price
        position_pct = position_value / account_value
        
        # 检查单仓位比例
        if position_pct > self.position_limits.max_single_position_pct:
            return False, f"单仓位比例 {position_pct:.1%} 超过限制 {self.position_limits.max_single_position_pct:.1%}"
        
        # 检查总仓位比例
        current_total_value = sum(pos.market_value for pos in self.positions.values())
        new_total_value = current_total_value + position_value
        total_pct = new_total_value / account_value
        
        if total_pct > self.position_limits.max_total_position_pct:
            return False, f"总仓位比例 {total_pct:.1%} 超过限制 {self.position_limits.max_total_position_pct:.1%}"
        
        # 检查持仓数量
        if len(self.positions) >= self.position_limits.max_positions_count:
            return False, f"持仓数量 {len(self.positions)} 达到限制 {self.position_limits.max_positions_count}"
        
        # 检查最小仓位价值
        if position_value < self.position_limits.min_position_value:
            return False, f"仓位价值 ${position_value:,.2f} 低于最小要求 ${self.position_limits.min_position_value:,.2f}"
        
        return True, "仓位检查通过"
    
    def suggest_position_adjustment(self, account_value: float) -> List[Dict]:
        """建议仓位调整"""
        suggestions = []
        
        # 检查过大的仓位
        for symbol, position in self.positions.items():
            if position.weight > self.position_limits.max_single_position_pct:
                reduce_quantity = int(position.quantity * 
                                    (position.weight - self.position_limits.max_single_position_pct) / position.weight)
                suggestions.append({
                    'type': 'reduce',
                    'symbol': symbol,
                    'current_weight': position.weight,
                    'target_weight': self.position_limits.max_single_position_pct,
                    'reduce_quantity': reduce_quantity,
                    'reason': '仓位过大'
                })
        
        # 检查总仓位是否过高
        total_market_value = sum(pos.market_value for pos in self.positions.values())
        total_pct = total_market_value / account_value
        
        if total_pct > self.position_limits.max_total_position_pct:
            excess_value = total_market_value - (account_value * self.position_limits.max_total_position_pct)
            suggestions.append({
                'type': 'reduce_total',
                'excess_value': excess_value,
                'current_total_pct': total_pct,
                'target_total_pct': self.position_limits.max_total_position_pct,
                'reason': '总仓位过高'
            })
        
        return suggestions
    
    def optimize_portfolio(self, account_value: float, target_volatility: float = 0.15) -> List[Dict]:
        """投资组合优化建议"""
        suggestions = []
        
        if len(self.positions) < 2:
            return suggestions
        
        # 计算当前组合波动率（简化版）
        returns = [pos.unrealized_pnl_pct for pos in self.positions.values()]
        if returns:
            portfolio_volatility = math.sqrt(sum((r - sum(returns)/len(returns))**2 for r in returns) / len(returns))
            
            if portfolio_volatility > target_volatility * 1.2:
                suggestions.append({
                    'type': 'reduce_volatility',
                    'current_volatility': portfolio_volatility,
                    'target_volatility': target_volatility,
                    'recommendation': '考虑减少高波动性仓位或增加防御性资产'
                })
            elif portfolio_volatility < target_volatility * 0.8:
                suggestions.append({
                    'type': 'increase_return',
                    'current_volatility': portfolio_volatility,
                    'target_volatility': target_volatility,
                    'recommendation': '可以适当增加成长性资产以提高收益潜力'
                })
        
        return suggestions


def calculate_optimal_portfolio_weights(returns_matrix: List[List[float]], 
                                      target_return: float = 0.1) -> List[float]:
    """
    计算最优投资组合权重（简化版马科维茨模型）
    
    Args:
        returns_matrix: 收益率矩阵
        target_return: 目标收益率
        
    Returns:
        最优权重分配
    """
    n = len(returns_matrix)
    if n == 0:
        return []
    
    # 简化实现：等权重分配
    equal_weight = 1.0 / n
    return [equal_weight] * n


# 使用示例
if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("📊 仓位控制系统演示")
    print("=" * 50)
    
    # 创建仓位管理器
    position_manager = PositionManager()
    
    # 模拟账户
    account_value = 100000
    
    # 计算不同方法的仓位大小
    entry_price = 150.0
    
    methods = [
        (PositionSizeMethod.FIXED_PERCENTAGE, {'percentage': 0.05}),
        (PositionSizeMethod.KELLY_CRITERION, {}),
        (PositionSizeMethod.ATR_BASED, {'atr': 3.0, 'risk_pct': 0.01}),
        (PositionSizeMethod.VOLATILITY_ADJUSTED, {'volatility': 0.03})
    ]
    
    print("仓位计算方法对比:")
    for method, params in methods:
        size = position_manager.calculate_position_size("AAPL", entry_price, account_value, method, **params)
        value = size * entry_price
        pct = value / account_value
        print(f"  {method.value}: {size}股 (${value:,.0f}, {pct:.1%})")
    
    # 添加仓位
    position_manager.add_position("AAPL", 333, 150.0)
    position_manager.add_position("TSLA", 100, 200.0)
    
    # 更新价格
    position_manager.update_prices({"AAPL": 155.0, "TSLA": 195.0})
    
    # 获取组合摘要
    summary = position_manager.get_portfolio_summary(account_value)
    print(f"\\n投资组合摘要:")
    print(f"  持仓数量: {summary['positions_count']}")
    print(f"  总市值: ${summary['total_market_value']:,.2f}")
    print(f"  未实现盈亏: ${summary['total_unrealized_pnl']:,.2f}")
    print(f"  仓位比例: {summary['position_percentage']:.1%}")
    
    print("\\n⚠️ 仓位控制功能:")
    print("- Kelly公式智能仓位")
    print("- ATR基础风险调整")
    print("- 波动率适应性配置")
    print("- 多重限制保护机制")