"""
RSI-based Trading Strategy.

This strategy uses the Relative Strength Index (RSI) to identify
overbought and oversold conditions for trading signals.
"""

import backtrader as bt
from .base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI-based trading strategy.
    
    Buys when RSI is oversold and sells when RSI is overbought.
    """
    
    params = (
        ('rsi_period', 14),      # RSI calculation period
        ('rsi_overbought', 70),  # Overbought level
        ('rsi_oversold', 30),    # Oversold level
    )
    
    def __init__(self):
        """Initialize the RSI strategy."""
        super().__init__()
        
        # Create RSI indicator
        self.rsi = bt.indicators.RSI(
            self.data.close, 
            period=self.params.rsi_period
        )
    
    def buy_signal(self) -> bool:
        """
        Buy signal: RSI crosses above oversold level.
        
        Returns:
            True if buy signal is active
        """
        return (self.rsi[0] > self.params.rsi_oversold and 
                self.rsi[-1] <= self.params.rsi_oversold)
    
    def sell_signal(self) -> bool:
        """
        Sell signal: RSI crosses below overbought level.
        
        Returns:
            True if sell signal is active
        """
        return (self.rsi[0] < self.params.rsi_overbought and 
                self.rsi[-1] >= self.params.rsi_overbought)
    
    def next(self):
        """Main strategy logic."""
        super().next()
        
        if self.params.debug:
            self.log(
                f'Close: {self.data.close[0]:.2f}, '
                f'RSI: {self.rsi[0]:.2f}'
            )