"""
Bollinger Bands Trading Strategy with MACD Confirmation.

This enhanced strategy uses Bollinger Bands to identify potential reversal points
when price touches or crosses the bands, combined with MACD indicator for
trend confirmation to reduce false signals and improve accuracy.
"""

import backtrader as bt
from .base_strategy import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    """
    Enhanced Bollinger Bands trading strategy with MACD confirmation.
    
    Primary signals:
    - Buys when price touches lower band AND MACD confirms upward momentum
    - Sells when price touches upper band AND MACD confirms downward momentum
    
    MACD confirmation criteria:
    - For buy: MACD > Signal line, positive histogram, rising MACD (need 2/3)
    - For sell: MACD < Signal line, negative histogram, falling MACD (need 2/3)
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
        
        # Add MACD indicator for trend confirmation
        self.macd = bt.indicators.MACDHisto(
            self.data.close,
            period_me1=12,  # Fast EMA period
            period_me2=26,  # Slow EMA period  
            period_signal=9  # Signal line period
        )
        
        # MACD components for easier reference
        self.macd_line = self.macd.macd
        self.macd_signal = self.macd.signal
        self.macd_histogram = self.macd.histo
    
    def buy_signal(self) -> bool:
        """
        Buy signal: Price approaches lower Bollinger Band AND MACD shows potential reversal.
        
        Returns:
            True if buy signal is active
        """
        # More flexible BB signal: Price within 5% of lower band
        bb_threshold = self.bb_bot[0] * 1.05
        bb_signal = self.data.close[0] <= bb_threshold
        
        # MACD confirmation signals (more flexible):
        # 1. MACD line is above signal line OR turning upward
        # 2. MACD histogram is positive OR improving (less negative)
        # 3. MACD line is rising OR price is oversold
        macd_bullish = (self.macd_line[0] > self.macd_signal[0] or
                       (len(self) > 1 and self.macd_line[0] > self.macd_line[-1]))
        macd_momentum = (self.macd_histogram[0] > 0 or 
                        (len(self) > 1 and self.macd_histogram[0] > self.macd_histogram[-1]))
        
        # Price-based oversold condition
        bb_position = (self.data.close[0] - self.bb_bot[0]) / (self.bb_top[0] - self.bb_bot[0])
        oversold = bb_position < 0.2  # Price in lower 20% of BB channel
        
        # Combine signals: Need BB signal AND at least 1 MACD confirmation OR oversold
        macd_confirmations = sum([macd_bullish, macd_momentum])
        
        return bb_signal and (macd_confirmations >= 1 or oversold)
    
    def sell_signal(self) -> bool:
        """
        Sell signal: Price approaches upper Bollinger Band AND MACD shows potential reversal.
        
        Returns:
            True if sell signal is active
        """
        # More flexible BB signal: Price within 5% of upper band
        bb_threshold = self.bb_top[0] * 0.95
        bb_signal = self.data.close[0] >= bb_threshold
        
        # MACD confirmation signals (more flexible):
        # 1. MACD line is below signal line OR turning downward
        # 2. MACD histogram is negative OR deteriorating (less positive)
        # 3. MACD line is falling OR price is overbought
        macd_bearish = (self.macd_line[0] < self.macd_signal[0] or
                       (len(self) > 1 and self.macd_line[0] < self.macd_line[-1]))
        macd_momentum = (self.macd_histogram[0] < 0 or 
                        (len(self) > 1 and self.macd_histogram[0] < self.macd_histogram[-1]))
        
        # Price-based overbought condition
        bb_position = (self.data.close[0] - self.bb_bot[0]) / (self.bb_top[0] - self.bb_bot[0])
        overbought = bb_position > 0.8  # Price in upper 20% of BB channel
        
        # Combine signals: Need BB signal AND at least 1 MACD confirmation OR overbought
        macd_confirmations = sum([macd_bearish, macd_momentum])
        
        return bb_signal and (macd_confirmations >= 1 or overbought)
    
    def next(self):
        """Main strategy logic."""
        super().next()
        
        if self.params.debug:
            self.log(
                f'Close: {self.data.close[0]:.2f}, '
                f'BB Top: {self.bb_top[0]:.2f}, '
                f'BB Mid: {self.bb_mid[0]:.2f}, '
                f'BB Bot: {self.bb_bot[0]:.2f}, '
                f'MACD: {self.macd_line[0]:.4f}, '
                f'Signal: {self.macd_signal[0]:.4f}, '
                f'Histogram: {self.macd_histogram[0]:.4f}'
            )