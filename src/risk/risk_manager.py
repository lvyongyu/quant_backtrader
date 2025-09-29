"""
Risk management system.

This module provides comprehensive risk management capabilities
including portfolio-level risk controls and monitoring.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class RiskManager:
    """
    Portfolio risk management system.
    
    Monitors and controls portfolio risk across multiple positions
    and trading strategies.
    """
    
    def __init__(
        self,
        max_portfolio_risk: float = 0.02,  # 2% max portfolio risk per trade
        max_daily_loss: float = 0.05,      # 5% max daily loss
        max_drawdown: float = 0.10,        # 10% max drawdown
        position_limit: int = 10,          # Max number of positions
        correlation_limit: float = 0.7,    # Max correlation between positions
    ):
        """
        Initialize risk manager.
        
        Args:
            max_portfolio_risk: Maximum risk per trade as % of portfolio
            max_daily_loss: Maximum daily loss as % of portfolio  
            max_drawdown: Maximum drawdown as % of portfolio
            position_limit: Maximum number of open positions
            correlation_limit: Maximum correlation between positions
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.position_limit = position_limit
        self.correlation_limit = correlation_limit
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.daily_pnl = 0.0
        self.daily_start_value = 0.0
        self.peak_value = 0.0
        self.current_positions = []
        
    def check_trade_risk(
        self,
        symbol: str,
        size: int,
        price: float,
        portfolio_value: float,
        stop_loss: float = None
    ) -> Dict[str, Any]:
        """
        Check if a proposed trade meets risk criteria.
        
        Args:
            symbol: Trading symbol
            size: Position size
            price: Entry price
            portfolio_value: Current portfolio value
            stop_loss: Stop loss price
            
        Returns:
            Dictionary with risk check results
        """
        trade_value = abs(size * price)
        
        # Check portfolio risk limit
        portfolio_risk = trade_value / portfolio_value
        risk_check = portfolio_risk <= self.max_portfolio_risk
        
        # Check position limit
        position_check = len(self.current_positions) < self.position_limit
        
        # Check if symbol already has position
        duplicate_check = symbol not in [pos['symbol'] for pos in self.current_positions]
        
        # Calculate potential loss if stop loss provided
        potential_loss = 0.0
        if stop_loss:
            potential_loss = abs(size * (price - stop_loss))
            loss_risk = potential_loss / portfolio_value
            loss_check = loss_risk <= self.max_portfolio_risk
        else:
            loss_check = True
        
        return {
            'approved': risk_check and position_check and duplicate_check and loss_check,
            'portfolio_risk': portfolio_risk,
            'max_portfolio_risk': self.max_portfolio_risk,
            'position_count': len(self.current_positions),
            'position_limit': self.position_limit,
            'duplicate_position': not duplicate_check,
            'potential_loss': potential_loss,
            'trade_value': trade_value,
            'reasons': self._get_rejection_reasons(
                risk_check, position_check, duplicate_check, loss_check
            )
        }
    
    def _get_rejection_reasons(
        self, 
        risk_check: bool, 
        position_check: bool, 
        duplicate_check: bool,
        loss_check: bool
    ) -> List[str]:
        """Get list of rejection reasons."""
        reasons = []
        if not risk_check:
            reasons.append("Exceeds portfolio risk limit")
        if not position_check:
            reasons.append("Exceeds position limit")
        if not duplicate_check:
            reasons.append("Duplicate position exists")
        if not loss_check:
            reasons.append("Potential loss exceeds risk limit")
        return reasons
    
    def update_daily_pnl(self, current_value: float):
        """
        Update daily P&L tracking.
        
        Args:
            current_value: Current portfolio value
        """
        if self.daily_start_value == 0:
            self.daily_start_value = current_value
            self.peak_value = current_value
        
        self.daily_pnl = current_value - self.daily_start_value
        
        # Update peak value for drawdown calculation
        if current_value > self.peak_value:
            self.peak_value = current_value
    
    def check_daily_loss_limit(self, current_value: float) -> bool:
        """
        Check if daily loss limit has been breached.
        
        Args:
            current_value: Current portfolio value
            
        Returns:
            True if within daily loss limit
        """
        if self.daily_start_value == 0:
            return True
        
        daily_loss_pct = (self.daily_start_value - current_value) / self.daily_start_value
        return daily_loss_pct <= self.max_daily_loss
    
    def check_drawdown_limit(self, current_value: float) -> bool:
        """
        Check if maximum drawdown limit has been breached.
        
        Args:
            current_value: Current portfolio value
            
        Returns:
            True if within drawdown limit
        """
        if self.peak_value == 0:
            return True
        
        drawdown_pct = (self.peak_value - current_value) / self.peak_value
        return drawdown_pct <= self.max_drawdown
    
    def add_position(self, symbol: str, size: int, price: float, timestamp: datetime = None):
        """
        Add a position to tracking.
        
        Args:
            symbol: Trading symbol
            size: Position size
            price: Entry price
            timestamp: Entry timestamp
        """
        position = {
            'symbol': symbol,
            'size': size,
            'price': price,
            'timestamp': timestamp or datetime.now(),
            'value': abs(size * price)
        }
        self.current_positions.append(position)
        self.logger.info(f"Added position: {symbol} {size}@{price}")
    
    def remove_position(self, symbol: str) -> bool:
        """
        Remove a position from tracking.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if position was removed
        """
        for i, pos in enumerate(self.current_positions):
            if pos['symbol'] == symbol:
                self.current_positions.pop(i)
                self.logger.info(f"Removed position: {symbol}")
                return True
        return False
    
    def get_risk_summary(self, current_value: float) -> Dict[str, Any]:
        """
        Get comprehensive risk summary.
        
        Args:
            current_value: Current portfolio value
            
        Returns:
            Risk summary dictionary
        """
        self.update_daily_pnl(current_value)
        
        daily_loss_ok = self.check_daily_loss_limit(current_value)
        drawdown_ok = self.check_drawdown_limit(current_value)
        
        daily_return = (self.daily_pnl / self.daily_start_value) * 100 if self.daily_start_value > 0 else 0
        drawdown_pct = ((self.peak_value - current_value) / self.peak_value) * 100 if self.peak_value > 0 else 0
        
        return {
            'portfolio_value': current_value,
            'daily_pnl': self.daily_pnl,
            'daily_return_pct': daily_return,
            'drawdown_pct': drawdown_pct,
            'position_count': len(self.current_positions),
            'daily_loss_limit_ok': daily_loss_ok,
            'drawdown_limit_ok': drawdown_ok,
            'risk_limits': {
                'max_daily_loss': self.max_daily_loss * 100,
                'max_drawdown': self.max_drawdown * 100,
                'max_portfolio_risk': self.max_portfolio_risk * 100,
                'position_limit': self.position_limit
            }
        }
    
    def reset_daily_tracking(self, start_value: float):
        """
        Reset daily tracking (call at start of each trading day).
        
        Args:
            start_value: Starting portfolio value for the day
        """
        self.daily_start_value = start_value
        self.daily_pnl = 0.0
        self.logger.info(f"Reset daily tracking with start value: ${start_value:,.2f}")