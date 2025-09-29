"""
Position sizing implementations.

This module provides various position sizing algorithms
for risk management and portfolio optimization.
"""

import backtrader as bt
from abc import ABC, abstractmethod
from typing import Optional, Union
import math


class PositionSizer(ABC):
    """
    Abstract base class for position sizing algorithms.
    """
    
    @abstractmethod
    def get_size(self, price: float, cash: float, value: float) -> int:
        """
        Calculate position size.
        
        Args:
            price: Current price of the asset
            cash: Available cash
            value: Current portfolio value
            
        Returns:
            Number of shares to trade
        """
        pass


class FixedSizer(PositionSizer):
    """
    Fixed position size - always trade the same number of shares.
    """
    
    def __init__(self, size: int = 100):
        """
        Initialize fixed sizer.
        
        Args:
            size: Fixed number of shares per trade
        """
        self.size = size
    
    def get_size(self, price: float, cash: float, value: float) -> int:
        """
        Get fixed position size.
        
        Args:
            price: Current price of the asset
            cash: Available cash  
            value: Current portfolio value
            
        Returns:
            Fixed number of shares
        """
        # Check if we have enough cash
        required_cash = self.size * price
        if required_cash <= cash:
            return self.size
        else:
            # Return maximum shares we can afford
            return int(cash / price)


class PercentSizer(PositionSizer):
    """
    Percentage-based position sizer - risk a fixed percentage of portfolio.
    """
    
    def __init__(self, percent: float = 0.1):
        """
        Initialize percent sizer.
        
        Args:
            percent: Percentage of portfolio to risk (0.0 to 1.0)
        """
        self.percent = max(0.0, min(1.0, percent))
    
    def get_size(self, price: float, cash: float, value: float) -> int:
        """
        Get position size based on portfolio percentage.
        
        Args:
            price: Current price of the asset
            cash: Available cash
            value: Current portfolio value
            
        Returns:
            Number of shares based on percentage
        """
        target_value = value * self.percent
        size = int(target_value / price)
        
        # Make sure we don't exceed available cash
        max_size = int(cash / price)
        return min(size, max_size)


class KellySizer(PositionSizer):
    """
    Kelly Criterion position sizer.
    
    Uses win rate and average win/loss ratio to optimize position size.
    """
    
    def __init__(
        self, 
        win_rate: float = 0.5, 
        avg_win: float = 1.0, 
        avg_loss: float = 1.0,
        max_percent: float = 0.25
    ):
        """
        Initialize Kelly sizer.
        
        Args:
            win_rate: Historical win rate (0.0 to 1.0)
            avg_win: Average win amount
            avg_loss: Average loss amount  
            max_percent: Maximum percentage of portfolio to risk
        """
        self.win_rate = max(0.0, min(1.0, win_rate))
        self.avg_win = max(0.01, avg_win)
        self.avg_loss = max(0.01, avg_loss)
        self.max_percent = max(0.0, min(1.0, max_percent))
    
    def get_kelly_fraction(self) -> float:
        """
        Calculate Kelly fraction.
        
        Returns:
            Kelly fraction (percentage of bankroll to bet)
        """
        if self.win_rate == 0 or self.avg_loss == 0:
            return 0.0
        
        # Kelly formula: f = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        b = self.avg_win / self.avg_loss
        p = self.win_rate
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Cap at max_percent to avoid over-leveraging
        return max(0.0, min(kelly_fraction, self.max_percent))
    
    def get_size(self, price: float, cash: float, value: float) -> int:
        """
        Get position size using Kelly Criterion.
        
        Args:
            price: Current price of the asset
            cash: Available cash
            value: Current portfolio value
            
        Returns:
            Number of shares based on Kelly fraction
        """
        kelly_fraction = self.get_kelly_fraction()
        target_value = value * kelly_fraction
        size = int(target_value / price)
        
        # Make sure we don't exceed available cash
        max_size = int(cash / price)
        return min(size, max_size)


class VolatilityAdjustedSizer(PositionSizer):
    """
    Volatility-adjusted position sizer.
    
    Adjusts position size based on asset volatility to maintain
    consistent risk across different assets.
    """
    
    def __init__(
        self, 
        target_volatility: float = 0.15, 
        lookback_period: int = 20,
        base_percent: float = 0.1
    ):
        """
        Initialize volatility-adjusted sizer.
        
        Args:
            target_volatility: Target portfolio volatility
            lookback_period: Period for volatility calculation
            base_percent: Base percentage of portfolio
        """
        self.target_volatility = target_volatility
        self.lookback_period = lookback_period
        self.base_percent = base_percent
        self.price_history = []
    
    def update_price_history(self, price: float):
        """
        Update price history for volatility calculation.
        
        Args:
            price: Latest price
        """
        self.price_history.append(price)
        if len(self.price_history) > self.lookback_period:
            self.price_history.pop(0)
    
    def calculate_volatility(self) -> float:
        """
        Calculate historical volatility.
        
        Returns:
            Annualized volatility
        """
        if len(self.price_history) < 2:
            return self.target_volatility  # Default volatility
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(self.price_history)):
            ret = (self.price_history[i] / self.price_history[i-1]) - 1
            returns.append(ret)
        
        if not returns:
            return self.target_volatility
        
        # Calculate standard deviation and annualize
        import statistics
        daily_vol = statistics.stdev(returns)
        annual_vol = daily_vol * math.sqrt(252)  # 252 trading days per year
        
        return annual_vol
    
    def get_size(self, price: float, cash: float, value: float) -> int:
        """
        Get volatility-adjusted position size.
        
        Args:
            price: Current price of the asset
            cash: Available cash
            value: Current portfolio value
            
        Returns:
            Number of shares adjusted for volatility
        """
        self.update_price_history(price)
        
        current_vol = self.calculate_volatility()
        if current_vol == 0:
            vol_adjustment = 1.0
        else:
            vol_adjustment = self.target_volatility / current_vol
        
        # Adjust base percentage by volatility ratio
        adjusted_percent = self.base_percent * vol_adjustment
        adjusted_percent = max(0.01, min(0.5, adjusted_percent))  # Cap between 1% and 50%
        
        target_value = value * adjusted_percent
        size = int(target_value / price)
        
        # Make sure we don't exceed available cash
        max_size = int(cash / price)
        return min(size, max_size)