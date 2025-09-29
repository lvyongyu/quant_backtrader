"""
Stop loss management system.

This module provides various stop loss implementations
for risk management and position protection.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum


class StopLossType(Enum):
    """Stop loss types."""
    FIXED = "fixed"
    TRAILING = "trailing"
    PERCENTAGE = "percentage"
    ATR = "atr"


class StopLossManager:
    """
    Stop loss management system.
    
    Manages different types of stop losses for active positions.
    """
    
    def __init__(self):
        """Initialize stop loss manager."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_stops = {}  # symbol -> stop loss config
    
    def add_fixed_stop(
        self, 
        symbol: str, 
        entry_price: float, 
        stop_price: float,
        position_size: int
    ) -> str:
        """
        Add a fixed stop loss.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_price: Fixed stop price
            position_size: Position size
            
        Returns:
            Stop loss ID
        """
        stop_id = f"{symbol}_fixed"
        self.active_stops[stop_id] = {
            'type': StopLossType.FIXED,
            'symbol': symbol,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'position_size': position_size,
            'triggered': False
        }
        
        self.logger.info("Added fixed stop loss for %s at $%.2f", symbol, stop_price)
        return stop_id
    
    def add_percentage_stop(
        self, 
        symbol: str, 
        entry_price: float, 
        stop_percentage: float,
        position_size: int,
        is_long: bool = True
    ) -> str:
        """
        Add a percentage-based stop loss.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_percentage: Stop percentage (e.g., 0.05 for 5%)
            position_size: Position size
            is_long: True for long positions, False for short
            
        Returns:
            Stop loss ID
        """
        if is_long:
            stop_price = entry_price * (1 - stop_percentage)
        else:
            stop_price = entry_price * (1 + stop_percentage)
        
        stop_id = f"{symbol}_percentage"
        self.active_stops[stop_id] = {
            'type': StopLossType.PERCENTAGE,
            'symbol': symbol,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'stop_percentage': stop_percentage,
            'position_size': position_size,
            'is_long': is_long,
            'triggered': False
        }
        
        self.logger.info(
            "Added percentage stop loss for %s at $%.2f (%.1f%%)", 
            symbol, stop_price, stop_percentage * 100
        )
        return stop_id
    
    def add_trailing_stop(
        self, 
        symbol: str, 
        entry_price: float, 
        trail_amount: float,
        position_size: int,
        is_long: bool = True
    ) -> str:
        """
        Add a trailing stop loss.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            trail_amount: Trailing amount (absolute or percentage)
            position_size: Position size
            is_long: True for long positions, False for short
            
        Returns:
            Stop loss ID
        """
        if is_long:
            stop_price = entry_price - trail_amount
        else:
            stop_price = entry_price + trail_amount
        
        stop_id = f"{symbol}_trailing"
        self.active_stops[stop_id] = {
            'type': StopLossType.TRAILING,
            'symbol': symbol,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'trail_amount': trail_amount,
            'position_size': position_size,
            'is_long': is_long,
            'highest_price': entry_price if is_long else entry_price,
            'lowest_price': entry_price if not is_long else entry_price,
            'triggered': False
        }
        
        self.logger.info(
            "Added trailing stop loss for %s at $%.2f (trail: $%.2f)", 
            symbol, stop_price, trail_amount
        )
        return stop_id
    
    def update_trailing_stop(self, symbol: str, current_price: float) -> bool:
        """
        Update trailing stop based on current price.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            True if stop was updated
        """
        stop_id = f"{symbol}_trailing"
        if stop_id not in self.active_stops:
            return False
        
        stop = self.active_stops[stop_id]
        if stop['triggered']:
            return False
        
        updated = False
        
        if stop['is_long']:
            # For long positions, trail up
            if current_price > stop['highest_price']:
                stop['highest_price'] = current_price
                new_stop = current_price - stop['trail_amount']
                if new_stop > stop['stop_price']:
                    stop['stop_price'] = new_stop
                    updated = True
                    self.logger.info(
                        "Updated trailing stop for %s to $%.2f", 
                        symbol, new_stop
                    )
        else:
            # For short positions, trail down
            if current_price < stop['lowest_price']:
                stop['lowest_price'] = current_price
                new_stop = current_price + stop['trail_amount']
                if new_stop < stop['stop_price']:
                    stop['stop_price'] = new_stop
                    updated = True
                    self.logger.info(
                        "Updated trailing stop for %s to $%.2f", 
                        symbol, new_stop
                    )
        
        return updated
    
    def check_stop_triggers(self, symbol: str, current_price: float) -> Optional[Dict[str, Any]]:
        """
        Check if any stop losses are triggered for a symbol.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Triggered stop loss info or None
        """
        triggered_stops = []
        
        for stop_id, stop in self.active_stops.items():
            if stop['symbol'] != symbol or stop['triggered']:
                continue
            
            triggered = False
            
            if stop['is_long']:
                # For long positions, trigger if price falls below stop
                if current_price <= stop['stop_price']:
                    triggered = True
            else:
                # For short positions, trigger if price rises above stop
                if current_price >= stop['stop_price']:
                    triggered = True
            
            if triggered:
                stop['triggered'] = True
                stop['trigger_price'] = current_price
                triggered_stops.append(stop)
                
                self.logger.warning(
                    "Stop loss triggered for %s at $%.2f (stop: $%.2f)", 
                    symbol, current_price, stop['stop_price']
                )
        
        return triggered_stops[0] if triggered_stops else None
    
    def remove_stop(self, symbol: str, stop_type: StopLossType = None) -> bool:
        """
        Remove stop loss for a symbol.
        
        Args:
            symbol: Trading symbol
            stop_type: Specific stop type to remove (None for all)
            
        Returns:
            True if stop was removed
        """
        removed = False
        
        if stop_type:
            stop_id = f"{symbol}_{stop_type.value}"
            if stop_id in self.active_stops:
                del self.active_stops[stop_id]
                removed = True
        else:
            # Remove all stops for symbol
            keys_to_remove = [k for k in self.active_stops.keys() if k.startswith(symbol)]
            for key in keys_to_remove:
                del self.active_stops[key]
                removed = True
        
        if removed:
            self.logger.info("Removed stop loss for %s", symbol)
        
        return removed
    
    def get_stop_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get stop loss information for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Stop loss information
        """
        symbol_stops = {
            k: v for k, v in self.active_stops.items() 
            if v['symbol'] == symbol and not v['triggered']
        }
        
        return {
            'symbol': symbol,
            'active_stops': len(symbol_stops),
            'stops': symbol_stops
        }
    
    def get_all_stops(self) -> Dict[str, Any]:
        """
        Get all active stop losses.
        
        Returns:
            All stop loss information
        """
        active_count = sum(1 for stop in self.active_stops.values() if not stop['triggered'])
        triggered_count = sum(1 for stop in self.active_stops.values() if stop['triggered'])
        
        return {
            'total_stops': len(self.active_stops),
            'active_stops': active_count,
            'triggered_stops': triggered_count,
            'stops': self.active_stops
        }