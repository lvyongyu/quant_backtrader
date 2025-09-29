"""
Paper Trading Broker Implementation.

This module provides a paper trading broker with enhanced
features for backtesting and strategy development.
"""

import backtrader as bt
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging


class PaperBroker:
    """
    Enhanced paper trading broker for Backtrader.
    
    Provides realistic trading simulation with configurable
    commission, slippage, and other trading costs.
    """
    
    def __init__(
        self,
        cash: float = 10000.0,
        commission: float = 0.001,  # 0.1% commission
        margin: Optional[float] = None,
        mult: float = 1.0,
        interest: float = 0.0,
        interest_long: bool = False,
        leverage: float = 1.0,
        slip_perc: float = 0.0,  # Slippage percentage
        slip_fixed: float = 0.0,  # Fixed slippage
        slip_open: bool = True,   # Apply slippage to market orders
        slip_match: bool = True,  # Match slippage to limit orders
        slip_limit: bool = True,  # Apply slippage to limit orders
        slip_out: bool = False,   # Slippage only on market exit
        coc: bool = False,        # Cheat-on-close
        coo: bool = False,        # Cheat-on-open
        shortcash: bool = True,   # Use short cash
        fundstartval: float = 100.0,  # Starting fund value
        fundmode: bool = False,   # Fund mode
    ):
        """
        Initialize the paper broker.
        
        Args:
            cash: Starting cash amount
            commission: Commission rate (as percentage of trade value)
            margin: Margin requirement (None for cash account)
            mult: Multiplier for position sizing
            interest: Interest rate for borrowed funds
            interest_long: Apply interest to long positions
            leverage: Maximum leverage allowed
            slip_perc: Slippage as percentage of price
            slip_fixed: Fixed slippage amount
            slip_open: Apply slippage to market orders on open
            slip_match: Match slippage for limit orders
            slip_limit: Apply slippage to limit orders
            slip_out: Apply slippage only on exit
            coc: Cheat-on-close (execute at close price)
            coo: Cheat-on-open (execute at open price)
            shortcash: Allow short selling with cash requirement
            fundstartval: Starting value for fund mode
            fundmode: Enable fund mode
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.config = {
            'cash': cash,
            'commission': commission,
            'margin': margin,
            'mult': mult,
            'interest': interest,
            'interest_long': interest_long,
            'leverage': leverage,
            'slip_perc': slip_perc,
            'slip_fixed': slip_fixed,
            'slip_open': slip_open,
            'slip_match': slip_match,
            'slip_limit': slip_limit,
            'slip_out': slip_out,
            'coc': coc,
            'coo': coo,
            'shortcash': shortcash,
            'fundstartval': fundstartval,
            'fundmode': fundmode
        }
    
    def setup_broker(self, cerebro: bt.Cerebro) -> bt.brokers.BackBroker:
        """
        Set up the broker with Cerebro.
        
        Args:
            cerebro: Backtrader Cerebro instance
            
        Returns:
            Configured broker instance
        """
        # Set initial cash
        cerebro.broker.set_cash(self.config['cash'])
        
        # Set commission
        cerebro.broker.setcommission(
            commission=self.config['commission'],
            margin=self.config['margin'],
            mult=self.config['mult'],
            interest=self.config['interest'],
            interest_long=self.config['interest_long'],
            leverage=self.config['leverage']
        )
        
        # Set slippage
        if self.config['slip_perc'] > 0 or self.config['slip_fixed'] > 0:
            cerebro.broker.set_slippage_perc(
                perc=self.config['slip_perc'],
                slip_open=self.config['slip_open'],
                slip_limit=self.config['slip_limit'],
                slip_match=self.config['slip_match'],
                slip_out=self.config['slip_out']
            )
            
            if self.config['slip_fixed'] > 0:
                cerebro.broker.set_slippage_fixed(
                    fixed=self.config['slip_fixed'],
                    slip_open=self.config['slip_open'],
                    slip_limit=self.config['slip_limit'],
                    slip_match=self.config['slip_match'],
                    slip_out=self.config['slip_out']
                )
        
        # Set other options
        if self.config['coc']:
            cerebro.broker.set_coc(True)
        if self.config['coo']:
            cerebro.broker.set_coo(True)
        if not self.config['shortcash']:
            cerebro.broker.set_shortcash(False)
        if self.config['fundmode']:
            cerebro.broker.set_fundmode(True, self.config['fundstartval'])
        
        self.logger.info(f"Set up paper broker with ${self.config['cash']} initial cash")
        return cerebro.broker
    
    @staticmethod
    def create_conservative_broker(cash: float = 10000.0) -> 'PaperBroker':
        """
        Create a conservative paper broker setup.
        
        Args:
            cash: Starting cash amount
            
        Returns:
            PaperBroker instance with conservative settings
        """
        return PaperBroker(
            cash=cash,
            commission=0.002,  # 0.2% commission
            slip_perc=0.001,   # 0.1% slippage
            slip_fixed=0.01,   # $0.01 fixed slippage
            leverage=1.0       # No leverage
        )
    
    @staticmethod
    def create_aggressive_broker(cash: float = 10000.0) -> 'PaperBroker':
        """
        Create an aggressive paper broker setup for active trading.
        
        Args:
            cash: Starting cash amount
            
        Returns:
            PaperBroker instance with aggressive settings
        """
        return PaperBroker(
            cash=cash,
            commission=0.0005,  # 0.05% commission (discount broker)
            slip_perc=0.0005,   # 0.05% slippage
            leverage=2.0,       # 2:1 leverage
            margin=0.5          # 50% margin requirement
        )
    
    @staticmethod
    def create_realistic_broker(cash: float = 10000.0) -> 'PaperBroker':
        """
        Create a realistic paper broker that mimics typical retail brokers.
        
        Args:
            cash: Starting cash amount
            
        Returns:
            PaperBroker instance with realistic settings
        """
        return PaperBroker(
            cash=cash,
            commission=0.001,   # 0.1% commission
            slip_perc=0.0005,   # 0.05% slippage
            slip_fixed=0.005,   # $0.005 fixed slippage
            leverage=1.0,       # Cash account
            interest=0.05,      # 5% annual interest on margin
            shortcash=True      # Allow short selling
        )
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get broker configuration summary.
        
        Returns:
            Dictionary with broker settings
        """
        return {
            'type': 'PaperBroker',
            'cash': self.config['cash'],
            'commission_rate': f"{self.config['commission']*100:.3f}%",
            'slippage_perc': f"{self.config['slip_perc']*100:.3f}%",
            'slippage_fixed': f"${self.config['slip_fixed']:.3f}",
            'leverage': f"{self.config['leverage']:.1f}:1",
            'margin_req': f"{self.config['margin']*100:.1f}%" if self.config['margin'] else "Cash Account",
            'short_selling': self.config['shortcash']
        }