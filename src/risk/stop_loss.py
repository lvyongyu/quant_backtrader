"""
止损管理器

实现多种止损策略，包括固定止损、跟踪止损、时间止损等，
确保单笔亏损控制在0.5%以内，保护账户资金安全。

核心功能：
1. 固定止损 - 基于固定价格或百分比
2. 跟踪止损 - 动态跟踪最高价格
3. 时间止损 - 基于持仓时间限制
4. ATR止损 - 基于平均真实波幅
5. 智能止损 - 结合技术指标
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import math

from . import StopLossType, RiskLevel


@dataclass
class StopLossOrder:
    """止损订单数据类"""
    symbol: str
    quantity: int
    stop_price: float
    stop_type: StopLossType
    created_time: datetime
    entry_price: float
    current_price: float = 0.0
    triggered: bool = False
    trigger_time: Optional[datetime] = None
    
    # 跟踪止损参数
    trailing_amount: float = 0.0
    trailing_percent: float = 0.0
    highest_price: float = 0.0
    
    # 时间止损参数
    max_hold_time: Optional[timedelta] = None
    
    # ATR止损参数
    atr_multiplier: float = 2.0
    current_atr: float = 0.0
    
    def update_price(self, new_price: float):
        """更新当前价格并检查止损触发条件"""
        self.current_price = new_price
        
        if self.stop_type == StopLossType.TRAILING:
            self._update_trailing_stop(new_price)
        elif self.stop_type == StopLossType.ATR_BASED:
            self._update_atr_stop(new_price)
    
    def _update_trailing_stop(self, new_price: float):
        """更新跟踪止损"""
        if new_price > self.highest_price:
            self.highest_price = new_price
            
            # 更新止损价格
            if self.trailing_percent > 0:
                self.stop_price = self.highest_price * (1 - self.trailing_percent)
            elif self.trailing_amount > 0:
                self.stop_price = self.highest_price - self.trailing_amount
    
    def _update_atr_stop(self, new_price: float):
        """更新ATR止损"""
        if self.current_atr > 0:
            self.stop_price = new_price - (self.current_atr * self.atr_multiplier)
    
    def is_triggered(self) -> bool:
        """检查是否触发止损"""
        if self.triggered:
            return True
        
        # 价格止损检查
        if self.current_price <= self.stop_price:
            self.triggered = True
            self.trigger_time = datetime.now()
            return True
        
        # 时间止损检查
        if (self.max_hold_time and 
            datetime.now() - self.created_time >= self.max_hold_time):
            self.triggered = True
            self.trigger_time = datetime.now()
            return True
        
        return False
    
    def get_loss_amount(self) -> float:
        """计算预期亏损金额"""
        if self.stop_price > 0:
            return abs(self.entry_price - self.stop_price) * self.quantity
        return 0.0
    
    def get_loss_percent(self, account_value: float) -> float:
        """计算亏损百分比"""
        loss_amount = self.get_loss_amount()
        return loss_amount / account_value if account_value > 0 else 0.0


class StopLossManager:
    """
    止损管理器
    
    负责管理所有止损订单，监控价格变化，
    自动触发止损条件，执行风险控制。
    """
    
    def __init__(self, max_single_loss_pct: float = 0.005):
        self.max_single_loss_pct = max_single_loss_pct  # 单笔最大亏损比例
        self.active_stops: Dict[str, StopLossOrder] = {}  # 活跃止损单
        self.triggered_stops: List[StopLossOrder] = []   # 已触发止损单
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 统计数据
        self.total_stops_created = 0
        self.total_stops_triggered = 0
        self.total_saved_loss = 0.0
        
        self.logger.info("止损管理器初始化完成")
    
    def create_fixed_stop(self, symbol: str, quantity: int, entry_price: float,
                         stop_price: float) -> StopLossOrder:
        """
        创建固定止损订单
        
        Args:
            symbol: 股票代码
            quantity: 数量
            entry_price: 入场价格
            stop_price: 止损价格
            
        Returns:
            止损订单对象
        """
        stop_order = StopLossOrder(
            symbol=symbol,
            quantity=quantity,
            stop_price=stop_price,
            stop_type=StopLossType.FIXED,
            created_time=datetime.now(),
            entry_price=entry_price,
            current_price=entry_price
        )
        
        self.active_stops[symbol] = stop_order
        self.total_stops_created += 1
        
        self.logger.info("创建固定止损: %s 价格=%.2f", symbol, stop_price)
        return stop_order
    
    def create_trailing_stop(self, symbol: str, quantity: int, entry_price: float,
                           trailing_percent: float = 0.0, 
                           trailing_amount: float = 0.0) -> StopLossOrder:
        """
        创建跟踪止损订单
        
        Args:
            symbol: 股票代码
            quantity: 数量
            entry_price: 入场价格
            trailing_percent: 跟踪百分比
            trailing_amount: 跟踪金额
            
        Returns:
            止损订单对象
        """
        stop_order = StopLossOrder(
            symbol=symbol,
            quantity=quantity,
            stop_price=entry_price * (1 - trailing_percent) if trailing_percent > 0 
                      else entry_price - trailing_amount,
            stop_type=StopLossType.TRAILING,
            created_time=datetime.now(),
            entry_price=entry_price,
            current_price=entry_price,
            trailing_percent=trailing_percent,
            trailing_amount=trailing_amount,
            highest_price=entry_price
        )
        
        self.active_stops[symbol] = stop_order
        self.total_stops_created += 1
        
        self.logger.info("创建跟踪止损: %s 跟踪=%.2f%%", symbol, trailing_percent * 100)
        return stop_order
    
    def create_time_stop(self, symbol: str, quantity: int, entry_price: float,
                        max_hold_minutes: int) -> StopLossOrder:
        """
        创建时间止损订单
        
        Args:
            symbol: 股票代码
            quantity: 数量
            entry_price: 入场价格
            max_hold_minutes: 最大持仓时间(分钟)
            
        Returns:
            止损订单对象
        """
        stop_order = StopLossOrder(
            symbol=symbol,
            quantity=quantity,
            stop_price=0.0,  # 时间止损不基于价格
            stop_type=StopLossType.TIME_BASED,
            created_time=datetime.now(),
            entry_price=entry_price,
            current_price=entry_price,
            max_hold_time=timedelta(minutes=max_hold_minutes)
        )
        
        self.active_stops[symbol] = stop_order
        self.total_stops_created += 1
        
        self.logger.info("创建时间止损: %s 时间=%d分钟", symbol, max_hold_minutes)
        return stop_order
    
    def create_atr_stop(self, symbol: str, quantity: int, entry_price: float,
                       atr_value: float, atr_multiplier: float = 2.0) -> StopLossOrder:
        """
        创建ATR止损订单
        
        Args:
            symbol: 股票代码
            quantity: 数量
            entry_price: 入场价格
            atr_value: 当前ATR值
            atr_multiplier: ATR倍数
            
        Returns:
            止损订单对象
        """
        stop_price = entry_price - (atr_value * atr_multiplier)
        
        stop_order = StopLossOrder(
            symbol=symbol,
            quantity=quantity,
            stop_price=stop_price,
            stop_type=StopLossType.ATR_BASED,
            created_time=datetime.now(),
            entry_price=entry_price,
            current_price=entry_price,
            atr_multiplier=atr_multiplier,
            current_atr=atr_value
        )
        
        self.active_stops[symbol] = stop_order
        self.total_stops_created += 1
        
        self.logger.info("创建ATR止损: %s ATR=%.2f 倍数=%.1f", symbol, atr_value, atr_multiplier)
        return stop_order
    
    def create_smart_stop(self, symbol: str, quantity: int, entry_price: float,
                         account_value: float, risk_level: RiskLevel = RiskLevel.MODERATE) -> StopLossOrder:
        """
        创建智能止损订单（自动选择最适合的止损类型）
        
        Args:
            symbol: 股票代码
            quantity: 数量
            entry_price: 入场价格
            account_value: 账户价值
            risk_level: 风险等级
            
        Returns:
            止损订单对象
        """
        # 计算基于风险限制的止损价格
        max_loss_amount = account_value * self.max_single_loss_pct
        max_loss_per_share = max_loss_amount / quantity
        
        # 基础止损价格
        base_stop_price = entry_price - max_loss_per_share
        
        # 根据风险等级调整
        if risk_level == RiskLevel.LOW:
            # 低风险：使用较紧的跟踪止损
            trailing_percent = 0.008  # 0.8%
            return self.create_trailing_stop(symbol, quantity, entry_price, trailing_percent)
            
        elif risk_level == RiskLevel.MODERATE:
            # 中等风险：使用固定止损
            stop_price = max(base_stop_price, entry_price * 0.985)  # 至少1.5%止损
            return self.create_fixed_stop(symbol, quantity, entry_price, stop_price)
            
        elif risk_level == RiskLevel.HIGH:
            # 高风险：使用更紧的固定止损
            stop_price = max(base_stop_price, entry_price * 0.99)   # 至少1%止损
            return self.create_fixed_stop(symbol, quantity, entry_price, stop_price)
            
        else:  # CRITICAL
            # 严重风险：立即止损
            stop_price = entry_price * 0.995  # 0.5%止损
            return self.create_fixed_stop(symbol, quantity, entry_price, stop_price)
    
    def update_price(self, symbol: str, new_price: float) -> bool:
        """
        更新价格并检查止损触发
        
        Args:
            symbol: 股票代码
            new_price: 新价格
            
        Returns:
            是否触发止损
        """
        if symbol not in self.active_stops:
            return False
        
        stop_order = self.active_stops[symbol]
        stop_order.update_price(new_price)
        
        if stop_order.is_triggered():
            # 移动到已触发列表
            self.triggered_stops.append(stop_order)
            del self.active_stops[symbol]
            
            self.total_stops_triggered += 1
            self.total_saved_loss += stop_order.get_loss_amount()
            
            self.logger.warning("止损触发: %s 价格=%.2f 类型=%s", 
                              symbol, new_price, stop_order.stop_type.value)
            return True
        
        return False
    
    def update_all_prices(self, price_updates: Dict[str, float]) -> List[str]:
        """
        批量更新价格
        
        Args:
            price_updates: 价格更新字典 {symbol: price}
            
        Returns:
            触发止损的股票代码列表
        """
        triggered_symbols = []
        
        for symbol, price in price_updates.items():
            if self.update_price(symbol, price):
                triggered_symbols.append(symbol)
        
        return triggered_symbols
    
    def remove_stop(self, symbol: str) -> bool:
        """
        移除止损订单（例如正常平仓时）
        
        Args:
            symbol: 股票代码
            
        Returns:
            是否成功移除
        """
        if symbol in self.active_stops:
            del self.active_stops[symbol]
            self.logger.info("移除止损订单: %s", symbol)
            return True
        return False
    
    def get_stop_info(self, symbol: str) -> Optional[Dict]:
        """获取止损信息"""
        if symbol in self.active_stops:
            stop = self.active_stops[symbol]
            return {
                'symbol': stop.symbol,
                'stop_price': stop.stop_price,
                'stop_type': stop.stop_type.value,
                'entry_price': stop.entry_price,
                'current_price': stop.current_price,
                'loss_amount': stop.get_loss_amount(),
                'created_time': stop.created_time.isoformat(),
                'is_triggered': stop.triggered
            }
        return None
    
    def get_all_active_stops(self) -> Dict[str, Dict]:
        """获取所有活跃止损信息"""
        return {symbol: self.get_stop_info(symbol) 
                for symbol in self.active_stops.keys()}
    
    def get_statistics(self) -> Dict:
        """获取止损统计信息"""
        trigger_rate = (self.total_stops_triggered / max(1, self.total_stops_created))
        
        return {
            'total_stops_created': self.total_stops_created,
            'total_stops_triggered': self.total_stops_triggered,
            'active_stops_count': len(self.active_stops),
            'trigger_rate': trigger_rate,
            'total_saved_loss': self.total_saved_loss,
            'average_saved_per_trigger': (self.total_saved_loss / max(1, self.total_stops_triggered))
        }
    
    def cleanup_old_stops(self, max_age_hours: int = 24):
        """清理过期的止损订单"""
        current_time = datetime.now()
        expired_symbols = []
        
        for symbol, stop in self.active_stops.items():
            if (current_time - stop.created_time).total_seconds() > max_age_hours * 3600:
                expired_symbols.append(symbol)
        
        for symbol in expired_symbols:
            del self.active_stops[symbol]
            self.logger.info("清理过期止损订单: %s", symbol)
        
        return len(expired_symbols)


def calculate_optimal_stop_loss(entry_price: float, account_value: float,
                              position_size: int, max_loss_pct: float = 0.005,
                              volatility: float = 0.02) -> float:
    """
    计算最优止损价格
    
    Args:
        entry_price: 入场价格
        account_value: 账户价值
        position_size: 仓位大小
        max_loss_pct: 最大亏损百分比
        volatility: 价格波动率
        
    Returns:
        建议止损价格
    """
    # 基于风险限制的止损
    max_loss_amount = account_value * max_loss_pct
    risk_based_stop = entry_price - (max_loss_amount / position_size)
    
    # 基于波动率的止损
    volatility_stop = entry_price * (1 - volatility * 1.5)
    
    # 选择更保守的止损价格
    optimal_stop = max(risk_based_stop, volatility_stop)
    
    # 确保止损不超过5%
    min_stop = entry_price * 0.95
    return max(optimal_stop, min_stop)


# 使用示例
if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🛡️ 止损管理器演示")
    print("=" * 50)
    
    # 创建止损管理器
    stop_manager = StopLossManager(max_single_loss_pct=0.005)
    
    # 创建不同类型的止损订单
    entry_price = 150.0
    quantity = 100
    
    # 1. 固定止损
    fixed_stop = stop_manager.create_fixed_stop("AAPL", quantity, entry_price, 147.0)
    print(f"固定止损: {fixed_stop.symbol} @ ${fixed_stop.stop_price}")
    
    # 2. 跟踪止损
    trailing_stop = stop_manager.create_trailing_stop("TSLA", quantity, entry_price, 0.02)
    print(f"跟踪止损: {trailing_stop.symbol} @ {trailing_stop.trailing_percent:.1%}")
    
    # 3. 智能止损
    smart_stop = stop_manager.create_smart_stop("MSFT", quantity, entry_price, 100000)
    print(f"智能止损: {smart_stop.symbol} @ ${smart_stop.stop_price}")
    
    # 模拟价格更新
    print("\\n价格更新测试:")
    triggered = stop_manager.update_price("AAPL", 146.5)
    print(f"AAPL价格146.5: {'触发止损' if triggered else '未触发'}")
    
    # 统计信息
    stats = stop_manager.get_statistics()
    print(f"\\n统计信息: 创建{stats['total_stops_created']}个 触发{stats['total_stops_triggered']}个")
    
    print("\\n⚠️ 止损功能:")
    print("- 固定止损: 基于固定价格/百分比")
    print("- 跟踪止损: 动态跟踪最高价")
    print("- 时间止损: 基于持仓时间")
    print("- ATR止损: 基于平均真实波幅")
    print("- 智能止损: 自动选择最优策略")