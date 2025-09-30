"""
风险管理框架 - 核心模块

提供日内交易系统的风险控制功能，包括止损机制、仓位控制、
风险监控等核心组件，确保交易安全和资金保护。

核心功能：
1. 动态止损管理
2. 智能仓位控制  
3. 实时风险监控
4. 风险参数配置
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import logging
import math


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"          # 低风险
    MODERATE = "moderate" # 中等风险
    HIGH = "high"        # 高风险
    CRITICAL = "critical" # 严重风险


class StopLossType(Enum):
    """止损类型枚举"""
    FIXED = "fixed"           # 固定止损
    TRAILING = "trailing"     # 跟踪止损
    TIME_BASED = "time_based" # 时间止损
    ATR_BASED = "atr_based"   # ATR基础止损


class PositionSizeMethod(Enum):
    """仓位控制方法枚举"""
    FIXED_AMOUNT = "fixed_amount"     # 固定金额
    FIXED_PERCENTAGE = "fixed_percentage" # 固定比例
    KELLY_CRITERION = "kelly_criterion"   # Kelly公式
    ATR_BASED = "atr_based"              # ATR基础
    VOLATILITY_ADJUSTED = "volatility_adjusted" # 波动率调整


@dataclass
class RiskMetrics:
    """风险指标数据类"""
    account_value: float = 0.0      # 账户总值
    available_cash: float = 0.0     # 可用现金
    position_value: float = 0.0     # 持仓价值
    unrealized_pnl: float = 0.0     # 未实现盈亏
    realized_pnl: float = 0.0       # 已实现盈亏
    daily_pnl: float = 0.0          # 当日盈亏
    max_drawdown: float = 0.0       # 最大回撤
    consecutive_losses: int = 0      # 连续亏损次数
    var_95: float = 0.0             # 95% VaR
    sharpe_ratio: float = 0.0       # 夏普比率
    risk_level: RiskLevel = RiskLevel.LOW
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'account_value': self.account_value,
            'available_cash': self.available_cash,
            'position_value': self.position_value,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'daily_pnl': self.daily_pnl,
            'max_drawdown': self.max_drawdown,
            'consecutive_losses': self.consecutive_losses,
            'var_95': self.var_95,
            'sharpe_ratio': self.sharpe_ratio,
            'risk_level': self.risk_level.value
        }


@dataclass
class RiskLimits:
    """风险限制配置"""
    max_single_loss_pct: float = 0.005    # 单笔最大亏损比例 0.5%
    max_daily_loss_pct: float = 0.02      # 日最大亏损比例 2%
    max_position_pct: float = 0.1         # 单仓位最大比例 10%
    max_total_position_pct: float = 0.8   # 总仓位最大比例 80%
    max_consecutive_losses: int = 5        # 最大连续亏损次数
    min_account_value: float = 10000      # 最小账户价值
    max_correlation: float = 0.7          # 最大相关性
    max_leverage: float = 1.0             # 最大杠杆率
    
    def validate(self) -> bool:
        """验证风险限制参数"""
        return (0 < self.max_single_loss_pct < 1 and
                0 < self.max_daily_loss_pct < 1 and
                0 < self.max_position_pct <= 1 and
                0 < self.max_total_position_pct <= 1 and
                self.max_consecutive_losses > 0 and
                self.min_account_value > 0)


@dataclass
class TradeRisk:
    """单笔交易风险评估"""
    symbol: str
    quantity: int
    entry_price: float
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    estimated_loss: float = 0.0
    estimated_gain: float = 0.0
    risk_reward_ratio: float = 0.0
    position_size_pct: float = 0.0
    correlation_risk: float = 0.0
    volatility: float = 0.0
    
    def calculate_risk_metrics(self):
        """计算风险指标"""
        if self.stop_loss_price:
            self.estimated_loss = abs(self.entry_price - self.stop_loss_price) * self.quantity
        
        if self.take_profit_price:
            self.estimated_gain = abs(self.take_profit_price - self.entry_price) * self.quantity
        
        if self.estimated_loss > 0 and self.estimated_gain > 0:
            self.risk_reward_ratio = self.estimated_gain / self.estimated_loss


class RiskController:
    """
    风险控制器
    
    负责所有风险相关的决策和监控，包括：
    - 交易前风险检查
    - 仓位控制
    - 止损管理
    - 风险监控
    """
    
    def __init__(self, risk_limits: RiskLimits = None):
        self.risk_limits = risk_limits or RiskLimits()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 风险状态
        self.current_metrics = RiskMetrics()
        self.daily_trades = []
        self.daily_pnl_history = []
        self.position_history = []
        
        # 风险监控
        self.emergency_stop = False
        self.daily_loss_exceeded = False
        self.max_positions_reached = False
        
        # 统计数据
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        self.logger.info(f"风险控制器初始化完成: {self.risk_limits.__dict__}")
    
    def validate_trade_dict(self, trade_dict: Dict, account_value: float) -> Tuple[bool, str]:
        """
        验证交易字典格式的交易请求
        
        Args:
            trade_dict: 包含交易信息的字典
            account_value: 当前账户价值
            
        Returns:
            (是否通过验证, 原因说明)
        """
        # 从字典创建TradeRisk对象
        trade_risk = TradeRisk(
            symbol=trade_dict.get('symbol', 'UNKNOWN'),
            quantity=trade_dict.get('quantity', 0),
            entry_price=trade_dict.get('price', 0.0),
            estimated_loss=trade_dict.get('estimated_loss', 0.0) * account_value  # 转换百分比为绝对值
        )
        
        # 计算风险指标
        trade_risk.calculate_risk_metrics()
        
        return self.validate_trade(trade_risk, account_value)
    
    def validate_trade(self, trade_risk: TradeRisk, account_value: float) -> Tuple[bool, str]:
        """
        验证交易是否符合风险控制要求
        
        Args:
            trade_risk: 交易风险评估
            account_value: 当前账户价值
            
        Returns:
            (是否通过验证, 原因说明)
        """
        # 检查紧急停止状态
        if self.emergency_stop:
            return False, "系统紧急停止状态"
        
        # 检查日亏损限制
        if self.daily_loss_exceeded:
            return False, f"已达到日亏损限制 {self.risk_limits.max_daily_loss_pct:.1%}"
        
        # 计算预期亏损占账户比例
        if trade_risk.estimated_loss > 0:
            loss_pct = trade_risk.estimated_loss / account_value
            if loss_pct > self.risk_limits.max_single_loss_pct:
                return False, f"单笔亏损风险 {loss_pct:.2%} 超过限制 {self.risk_limits.max_single_loss_pct:.2%}"
        
        # 检查仓位限制
        position_value = trade_risk.quantity * trade_risk.entry_price
        position_pct = position_value / account_value
        
        if position_pct > self.risk_limits.max_position_pct:
            return False, f"单仓位比例 {position_pct:.1%} 超过限制 {self.risk_limits.max_position_pct:.1%}"
        
        # 检查连续亏损
        if self.current_metrics.consecutive_losses >= self.risk_limits.max_consecutive_losses:
            return False, f"连续亏损 {self.current_metrics.consecutive_losses} 次，达到限制"
        
        # 检查风险回报比
        if trade_risk.risk_reward_ratio > 0 and trade_risk.risk_reward_ratio < 1.0:
            return False, f"风险回报比 {trade_risk.risk_reward_ratio:.2f} 过低"
        
        # 检查账户最小值
        if account_value < self.risk_limits.min_account_value:
            return False, f"账户价值 ${account_value:,.2f} 低于最小要求 ${self.risk_limits.min_account_value:,.2f}"
        
        return True, "风险检查通过"
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                              stop_loss_price: float, account_value: float,
                              method: PositionSizeMethod = PositionSizeMethod.FIXED_PERCENTAGE) -> int:
        """
        计算合适的仓位大小
        
        Args:
            symbol: 股票代码
            entry_price: 入场价格
            stop_loss_price: 止损价格
            account_value: 账户价值
            method: 仓位计算方法
            
        Returns:
            建议仓位数量
        """
        if method == PositionSizeMethod.FIXED_PERCENTAGE:
            # 固定比例法
            position_value = account_value * self.risk_limits.max_position_pct
            quantity = int(position_value / entry_price)
            
        elif method == PositionSizeMethod.FIXED_AMOUNT:
            # 固定金额法
            risk_amount = account_value * self.risk_limits.max_single_loss_pct
            price_diff = abs(entry_price - stop_loss_price)
            quantity = int(risk_amount / price_diff) if price_diff > 0 else 0
            
        elif method == PositionSizeMethod.KELLY_CRITERION:
            # Kelly公式法（简化版）
            win_rate = self.winning_trades / max(1, self.total_trades)
            avg_win = 0.01  # 假设平均收益1%
            avg_loss = 0.005  # 假设平均亏损0.5%
            
            if avg_loss > 0:
                kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                kelly_fraction = max(0, min(0.25, kelly_fraction))  # 限制在0-25%
                position_value = account_value * kelly_fraction
                quantity = int(position_value / entry_price)
            else:
                quantity = 0
                
        elif method == PositionSizeMethod.ATR_BASED:
            # ATR基础法（简化，需要ATR数据）
            atr_multiplier = 2.0
            estimated_atr = entry_price * 0.02  # 假设ATR为价格的2%
            risk_amount = account_value * self.risk_limits.max_single_loss_pct
            quantity = int(risk_amount / (estimated_atr * atr_multiplier))
            
        else:
            # 默认固定比例
            position_value = account_value * 0.05  # 5%
            quantity = int(position_value / entry_price)
        
        # 确保不超过最大仓位限制
        max_position_value = account_value * self.risk_limits.max_position_pct
        max_quantity = int(max_position_value / entry_price)
        quantity = min(quantity, max_quantity)
        
        self.logger.info(f"仓位计算: {symbol} 方法={method.value} 数量={quantity}")
        return max(0, quantity)
    
    def update_metrics(self, account_value: float, positions: Dict[str, Dict], 
                      daily_pnl: float = None):
        """
        更新风险指标
        
        Args:
            account_value: 当前账户价值
            positions: 当前持仓信息
            daily_pnl: 当日盈亏
        """
        self.current_metrics.account_value = account_value
        
        # 计算持仓价值和未实现盈亏
        total_position_value = 0
        total_unrealized_pnl = 0
        
        for symbol, pos_info in positions.items():
            position_value = pos_info.get('quantity', 0) * pos_info.get('current_price', 0)
            total_position_value += position_value
            total_unrealized_pnl += pos_info.get('unrealized_pnl', 0)
        
        self.current_metrics.position_value = total_position_value
        self.current_metrics.unrealized_pnl = total_unrealized_pnl
        self.current_metrics.available_cash = account_value - total_position_value
        
        # 更新当日盈亏
        if daily_pnl is not None:
            self.current_metrics.daily_pnl = daily_pnl
            self.daily_pnl_history.append(daily_pnl)
        
        # 计算最大回撤
        if len(self.daily_pnl_history) > 1:
            cumulative_pnl = [sum(self.daily_pnl_history[:i+1]) for i in range(len(self.daily_pnl_history))]
            peak = max(cumulative_pnl)
            current = cumulative_pnl[-1]
            self.current_metrics.max_drawdown = (peak - current) / account_value if account_value > 0 else 0
        
        # 评估风险等级
        self.current_metrics.risk_level = self._assess_risk_level()
        
        # 检查风险限制
        self._check_risk_limits()
    
    def _assess_risk_level(self) -> RiskLevel:
        """评估当前风险等级"""
        risk_score = 0
        
        # 基于当日亏损
        if self.current_metrics.daily_pnl < 0:
            daily_loss_pct = abs(self.current_metrics.daily_pnl) / self.current_metrics.account_value
            if daily_loss_pct > self.risk_limits.max_daily_loss_pct * 0.8:
                risk_score += 3
            elif daily_loss_pct > self.risk_limits.max_daily_loss_pct * 0.5:
                risk_score += 2
            elif daily_loss_pct > self.risk_limits.max_daily_loss_pct * 0.3:
                risk_score += 1
        
        # 基于最大回撤
        if self.current_metrics.max_drawdown > 0.05:  # 5%
            risk_score += 2
        elif self.current_metrics.max_drawdown > 0.03:  # 3%
            risk_score += 1
        
        # 基于连续亏损
        if self.current_metrics.consecutive_losses >= 4:
            risk_score += 2
        elif self.current_metrics.consecutive_losses >= 3:
            risk_score += 1
        
        # 基于仓位比例
        position_pct = self.current_metrics.position_value / self.current_metrics.account_value
        if position_pct > 0.7:
            risk_score += 1
        
        # 确定风险等级
        if risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def _check_risk_limits(self):
        """检查是否超过风险限制"""
        # 检查日亏损限制
        if self.current_metrics.daily_pnl < 0:
            daily_loss_pct = abs(self.current_metrics.daily_pnl) / self.current_metrics.account_value
            if daily_loss_pct >= self.risk_limits.max_daily_loss_pct:
                self.daily_loss_exceeded = True
                self.logger.warning(f"达到日亏损限制: {daily_loss_pct:.2%}")
        
        # 检查紧急停止条件
        if (self.current_metrics.risk_level == RiskLevel.CRITICAL or
            self.current_metrics.consecutive_losses >= self.risk_limits.max_consecutive_losses):
            self.emergency_stop = True
            self.logger.error("触发紧急停止机制")
    
    def record_trade_result(self, profit_loss: float):
        """记录交易结果"""
        self.total_trades += 1
        
        if profit_loss > 0:
            self.winning_trades += 1
            self.current_metrics.consecutive_losses = 0
        else:
            self.losing_trades += 1
            self.current_metrics.consecutive_losses += 1
        
        self.current_metrics.realized_pnl += profit_loss
    
    def get_risk_status(self) -> Dict:
        """获取风险状态报告"""
        win_rate = self.winning_trades / max(1, self.total_trades)
        
        return {
            'metrics': self.current_metrics.to_dict(),
            'limits': self.risk_limits.__dict__,
            'status': {
                'emergency_stop': self.emergency_stop,
                'daily_loss_exceeded': self.daily_loss_exceeded,
                'max_positions_reached': self.max_positions_reached
            },
            'statistics': {
                'total_trades': self.total_trades,
                'win_rate': win_rate,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades
            }
        }
    
    def reset_daily_limits(self):
        """重置日限制（每日开盘前调用）"""
        self.daily_loss_exceeded = False
        self.current_metrics.daily_pnl = 0.0
        self.daily_trades.clear()
        self.logger.info("日风险限制已重置")
    
    def is_trading_allowed(self) -> Tuple[bool, str]:
        """检查是否允许交易"""
        if self.emergency_stop:
            return False, "紧急停止状态"
        
        if self.daily_loss_exceeded:
            return False, "日亏损限制"
        
        if self.current_metrics.account_value < self.risk_limits.min_account_value:
            return False, "账户价值过低"
        
        return True, "允许交易"


# 工具函数
def calculate_var(returns: List[float], confidence: float = 0.95) -> float:
    """计算风险价值(VaR)"""
    if not returns:
        return 0.0
    
    returns_sorted = sorted(returns)
    index = int((1 - confidence) * len(returns_sorted))
    return abs(returns_sorted[index]) if index < len(returns_sorted) else 0.0


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """计算夏普比率"""
    if not returns or len(returns) < 2:
        return 0.0
    
    avg_return = sum(returns) / len(returns)
    std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1))
    
    if std_return == 0:
        return 0.0
    
    return (avg_return - risk_free_rate / 252) / std_return  # 252个交易日


def create_default_risk_config() -> RiskLimits:
    """创建默认风险配置"""
    return RiskLimits(
        max_single_loss_pct=0.005,    # 0.5%
        max_daily_loss_pct=0.02,      # 2%
        max_position_pct=0.1,         # 10%
        max_total_position_pct=0.8,   # 80%
        max_consecutive_losses=5,
        min_account_value=10000,
        max_correlation=0.7,
        max_leverage=1.0
    )


# 使用示例
if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🛡️ 风险管理框架演示")
    print("=" * 50)
    
    # 创建风险控制器
    risk_controller = RiskController()
    
    # 模拟交易风险评估
    trade_risk = TradeRisk(
        symbol="AAPL",
        quantity=100,
        entry_price=150.0,
        stop_loss_price=147.0,
        take_profit_price=156.0
    )
    trade_risk.calculate_risk_metrics()
    
    # 验证交易
    account_value = 100000
    is_valid, reason = risk_controller.validate_trade(trade_risk, account_value)
    
    print(f"交易验证: {is_valid}")
    print(f"原因: {reason}")
    print(f"风险回报比: {trade_risk.risk_reward_ratio:.2f}")
    
    # 计算仓位大小
    position_size = risk_controller.calculate_position_size(
        "AAPL", 150.0, 147.0, account_value, PositionSizeMethod.FIXED_AMOUNT
    )
    print(f"建议仓位: {position_size} 股")
    
    print("\\n⚠️ 风险控制功能:")
    print("- 单笔亏损限制: 0.5%")
    print("- 日亏损限制: 2%")
    print("- 动态止损管理")
    print("- 实时风险监控")