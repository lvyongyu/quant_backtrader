"""
Mean Reversion Trading Strategy.

This strategy identifies when prices deviate significantly from their
moving average and trades expecting a reversion to the mean.
"""

import backtrader as bt
from .base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion trading strategy.
    
    Buys when price is significantly below moving average,
    sells when price is significantly above moving average.
    """
    
    params = (
        ('ma_period', 20),          # Moving average period
        ('deviation_threshold', 2), # Standard deviation threshold
        ('lookback_period', 20),    # Period for calculating standard deviation
    )
    
    def __init__(self):
        """Initialize the mean reversion strategy."""
        super().__init__()
        
        # Create moving average
        self.moving_avg = bt.indicators.SimpleMovingAverage(
            self.data.close, 
            period=self.params.ma_period
        )
        
        # Calculate standard deviation
        self.std_dev = bt.indicators.StandardDeviation(
            self.data.close,
            period=self.params.lookback_period
        )
        
        # Calculate z-score (how many standard deviations from mean)
        self.z_score = (self.data.close - self.moving_avg) / self.std_dev
    
    def buy_signal(self) -> bool:
        """
        Buy signal: Price is significantly below moving average.
        
        Returns:
            True if buy signal is active
        """
        return self.z_score[0] < -self.params.deviation_threshold
    
    def sell_signal(self) -> bool:
        """
        Sell signal: Price is significantly above moving average.
        
        Returns:
            True if sell signal is active
        """
        return self.z_score[0] > self.params.deviation_threshold
    
    def next(self):
        """Main strategy logic."""
        super().next()
        
        if self.params.debug:
            self.log(
                f'Close: {self.data.close[0]:.2f}, '
                f'MA: {self.moving_avg[0]:.2f}, '
                f'Std Dev: {self.std_dev[0]:.2f}, '
                f'Z-Score: {self.z_score[0]:.2f}'
            )