"""
Simple Moving Average Crossover Strategy.

This strategy implements a classic SMA crossover system where:
- Buy when fast SMA crosses above slow SMA
- Sell when fast SMA crosses below slow SMA
"""

import backtrader as bt
from .base_strategy import BaseStrategy


class SMACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average crossover strategy.
    
    Uses two SMAs of different periods to generate buy/sell signals.
    """
    
    params = (
        ('fast_period', 10),   # Fast SMA period
        ('slow_period', 30),   # Slow SMA period
    )
    
    def __init__(self):
        """Initialize the SMA crossover strategy."""
        super().__init__()
        
        # Create the moving averages
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, 
            period=self.params.fast_period
        )
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, 
            period=self.params.slow_period
        )
        
        # Crossover signals
        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)
    
    def buy_signal(self) -> bool:
        """
        Buy signal: Fast SMA crosses above slow SMA.
        
        Returns:
            True if buy signal is active
        """
        return self.crossover > 0
    
    def sell_signal(self) -> bool:
        """
        Sell signal: Fast SMA crosses below slow SMA.
        
        Returns:
            True if sell signal is active
        """
        return self.crossover < 0
    
    def next(self):
        """Main strategy logic."""
        super().next()
        
        if self.params.debug:
            self.log(
                f'Close: {self.data.close[0]:.2f}, '
                f'Fast SMA: {self.fast_sma[0]:.2f}, '
                f'Slow SMA: {self.slow_sma[0]:.2f}, '
                f'Crossover: {self.crossover[0]:.2f}'
            )