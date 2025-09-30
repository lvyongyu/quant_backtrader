"""
智能动态止损管理器
基于ATR和波动率的自适应止损
"""

import backtrader as bt
import numpy as np


class IntelligentStopLoss(bt.Strategy):
    """
    智能止损管理器 - 替代固定止损的动态方案
    
    特点：
    - ATR基础的动态止损
    - 波动率自适应调整  
    - 趋势保护机制
    - 利润保护阶梯
    """
    
    params = (
        ('atr_period', 14),           # ATR计算周期
        ('atr_multiplier', 2.0),      # ATR止损倍数
        ('volatility_period', 20),    # 波动率计算周期
        ('min_stop_distance', 0.02),  # 最小止损距离 (2%)
        ('max_stop_distance', 0.08),  # 最大止损距离 (8%)
        ('profit_protection', True),   # 启用利润保护
        ('trailing_factor', 0.5),     # 移动止损系数
    )
    
    def __init__(self):
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # 价格波动率
        self.price_volatility = bt.indicators.StandardDeviation(
            self.data.close,
            period=self.params.volatility_period
        ) / self.data.close
        
        # 存储止损价格
        self.stop_prices = {}
        self.entry_prices = {}
        self.highest_profit = {}
        
    def calculate_stop_loss(self, entry_price: float, is_long: bool) -> float:
        """
        计算智能止损价格
        
        Args:
            entry_price: 入场价格
            is_long: 是否多头位置
            
        Returns:
            止损价格
        """
        # ATR基础止损距离
        atr_distance = self.atr[0] * self.params.atr_multiplier
        
        # 波动率调整
        volatility = self.price_volatility[0]
        volatility_adjustment = 1.0 + volatility * 2  # 高波动率增加止损距离
        
        # 计算调整后的止损距离
        stop_distance = atr_distance * volatility_adjustment
        
        # 确保在合理范围内
        min_distance = entry_price * self.params.min_stop_distance
        max_distance = entry_price * self.params.max_stop_distance
        stop_distance = max(min_distance, min(stop_distance, max_distance))
        
        if is_long:
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def update_trailing_stop(self, order_id: str, is_long: bool):
        """更新移动止损"""
        if order_id not in self.stop_prices:
            return
            
        current_price = self.data.close[0]
        entry_price = self.entry_prices[order_id]
        current_stop = self.stop_prices[order_id]
        
        if is_long:
            # 多头：价格上涨时提高止损
            profit = current_price - entry_price
            if profit > 0:
                # 计算新的止损价格（保护部分利润）
                new_stop = entry_price + profit * self.params.trailing_factor
                self.stop_prices[order_id] = max(current_stop, new_stop)
                
                # 记录最高利润
                self.highest_profit[order_id] = max(
                    self.highest_profit.get(order_id, 0), profit
                )
        else:
            # 空头：价格下跌时降低止损
            profit = entry_price - current_price
            if profit > 0:
                new_stop = entry_price - profit * self.params.trailing_factor
                self.stop_prices[order_id] = min(current_stop, new_stop)
                
                self.highest_profit[order_id] = max(
                    self.highest_profit.get(order_id, 0), profit
                )
    
    def check_stop_loss(self, order_id: str, is_long: bool) -> bool:
        """检查是否触发止损"""
        if order_id not in self.stop_prices:
            return False
            
        current_price = self.data.close[0]
        stop_price = self.stop_prices[order_id]
        
        if is_long:
            return current_price <= stop_price
        else:
            return current_price >= stop_price
    
    def create_stop_order(self, main_order_id: str, size: float, is_long: bool):
        """创建智能止损单"""
        entry_price = self.data.close[0]
        stop_price = self.calculate_stop_loss(entry_price, is_long)
        
        # 存储关键信息
        self.entry_prices[main_order_id] = entry_price
        self.stop_prices[main_order_id] = stop_price
        self.highest_profit[main_order_id] = 0
        
        self.log(f"创建智能止损: 入场价格=${entry_price:.2f}, "
                f"初始止损=${stop_price:.2f}, "
                f"止损距离={abs(entry_price-stop_price)/entry_price*100:.2f}%")
        
        return stop_price
    
    def log(self, txt):
        """日志输出"""
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')


class IntelligentStopLossOrder:
    """智能止损订单类"""
    
    def __init__(self, order_id: str, entry_price: float, stop_price: float, 
                 size: float, is_long: bool):
        self.order_id = order_id
        self.entry_price = entry_price
        self.stop_price = stop_price
        self.size = size
        self.is_long = is_long
        self.created_time = None
        self.status = 'active'  # active, triggered, cancelled
        
    def update_stop(self, new_stop: float):
        """更新止损价格"""
        if self.is_long:
            self.stop_price = max(self.stop_price, new_stop)  # 只能提高多头止损
        else:
            self.stop_price = min(self.stop_price, new_stop)  # 只能降低空头止损
    
    def is_triggered(self, current_price: float) -> bool:
        """检查是否触发"""
        if self.is_long:
            return current_price <= self.stop_price
        else:
            return current_price >= self.stop_price
    
    def get_profit_loss(self, current_price: float) -> float:
        """计算当前盈亏"""
        if self.is_long:
            return (current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - current_price) / self.entry_price