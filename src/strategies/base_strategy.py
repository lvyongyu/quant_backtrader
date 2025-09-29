"""
Base strategy class for all trading strategies.

This module provides the foundation class that all trading strategies
should inherit from, providing common functionality and interface.
"""

import backtrader as bt
from typing import Dict, Any, Optional
import logging


class BaseStrategy(bt.Strategy):
    """
    Base strategy class that provides common functionality for all trading strategies.
    
    All custom strategies should inherit from this class to ensure
    consistent behavior and logging.
    """
    
    params = (
        ('stake_percentage', 0.95),  # Percentage of cash to use per trade
        ('stop_loss', 0.02),         # Stop loss as percentage (2%)
        ('take_profit', 0.05),       # Take profit as percentage (5%)
        ('debug', False),            # Enable debug logging
    )
    
    def __init__(self):
        """Initialize the base strategy."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
        # Set up logging
        if self.params.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def log(self, txt: str, dt: Optional[Any] = None):
        """Log strategy events with timestamp."""
        dt = dt or self.datas[0].datetime.date(0)
        self.logger.info(f'{dt.isoformat()}: {txt}')
    
    def notify_order(self, order: bt.Order):
        """
        Notify when order status changes.
        
        Args:
            order: The order object
        """
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                )
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
            else:
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                )
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
    
    def notify_trade(self, trade: bt.Trade):
        """
        Notify when trade is closed.
        
        Args:
            trade: The completed trade
        """
        if not trade.isclosed:
            return
        
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')
    
    def get_position_size(self) -> int:
        """
        Calculate position size based on available cash and stake percentage.
        
        Returns:
            Number of shares to buy
        """
        cash = self.broker.get_cash()
        price = self.data.close[0]
        stake = int((cash * self.params.stake_percentage) / price)
        return max(stake, 1) if stake > 0 else 0
    
    def can_buy(self) -> bool:
        """
        Check if we can place a buy order.
        
        Returns:
            True if no pending orders and not already in position
        """
        return self.order is None and not self.position
    
    def can_sell(self) -> bool:
        """
        Check if we can place a sell order.
        
        Returns:
            True if no pending orders and we have a position
        """
        return self.order is None and self.position
    
    def buy_signal(self) -> bool:
        """
        Override this method to implement buy signal logic.
        
        Returns:
            True if buy signal is triggered
        """
        raise NotImplementedError("Subclasses must implement buy_signal method")
    
    def sell_signal(self) -> bool:
        """
        Override this method to implement sell signal logic.
        
        Returns:
            True if sell signal is triggered
        """
        raise NotImplementedError("Subclasses must implement sell_signal method")
    
    def next(self):
        """
        Main strategy logic - called for each bar.
        Override this method in subclasses for custom logic.
        """
        if self.can_buy() and self.buy_signal():
            size = self.get_position_size()
            if size > 0:
                self.log(f'BUY CREATE, {size} shares at {self.data.close[0]:.2f}')
                self.order = self.buy(size=size)
        
        elif self.can_sell() and self.sell_signal():
            self.log(f'SELL CREATE, {self.position.size} shares at {self.data.close[0]:.2f}')
            self.order = self.sell(size=self.position.size)
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """
        Get strategy statistics.
        
        Returns:
            Dictionary with strategy performance stats
        """
        return {
            'cash': self.broker.get_cash(),
            'value': self.broker.get_value(),
            'position_size': self.position.size if self.position else 0,
            'position_price': self.position.price if self.position else 0.0,
        }