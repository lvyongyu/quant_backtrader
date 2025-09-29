"""
Bollinger Bands Trading Strategy.

This strategy uses Bollinger Bands to identify potential reversal points
when price touches or crosses the bands.
"""

import backtrader as bt
from .base_strategy import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands trading strategy.
    
    Buys when price touches lower band and sells when price touches upper band.
    """
    
    params = (
        ('bb_period', 20),     # Bollinger Bands period
        ('bb_devfactor', 2),   # Standard deviation factor
    )
    
    def __init__(self):
        """Initialize the Bollinger Bands strategy."""
        super().__init__()
        
        # Create Bollinger Bands
        self.bollinger = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor
        )
        
        # Extract individual bands for easier reference
        self.bb_top = self.bollinger.lines.top
        self.bb_mid = self.bollinger.lines.mid
        self.bb_bot = self.bollinger.lines.bot
    
    def buy_signal(self) -> bool:
        """
        Buy signal: Price touches or goes below lower Bollinger Band.
        
        Returns:
            True if buy signal is active
        """
        return self.data.close[0] <= self.bb_bot[0]
    
    def sell_signal(self) -> bool:
        """
        Sell signal: Price touches or goes above upper Bollinger Band.
        
        Returns:
            True if sell signal is active
        """
        return self.data.close[0] >= self.bb_top[0]
    
    def next(self):
        """Main strategy logic."""
        super().next()
        
        if self.params.debug:
            self.log(
                f'Close: {self.data.close[0]:.2f}, '
                f'BB Top: {self.bb_top[0]:.2f}, '
                f'BB Mid: {self.bb_mid[0]:.2f}, '
                f'BB Bot: {self.bb_bot[0]:.2f}'
            )