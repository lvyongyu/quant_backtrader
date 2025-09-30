"""
Yahoo Finance data feed implementation.

This module provides a data feed that fetches historical and 
real-time data from Yahoo Finance using the yfinance library.
"""

import backtrader as bt
from datetime import datetime
from typing import Optional, Union
import logging

try:
    import yfinance as yf
    import pandas as pd
except ImportError as e:
    print(f"警告: 缺少依赖包 {e}, Yahoo数据源功能可能受限")
    yf = None
    pd = None


class YahooDataFeed(bt.feeds.PandasData):
    """
    Yahoo Finance data feed for Backtrader.
    
    Fetches historical data from Yahoo Finance and converts it
    to a format suitable for Backtrader strategies.
    """
    
    params = (
        ('symbol', 'AAPL'),           # Stock symbol
        ('period', '1y'),             # Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        ('interval', '1d'),           # Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        ('auto_adjust', True),        # Auto adjust prices for splits and dividends
        ('prepost', False),           # Include pre/post market data
        ('actions', True),            # Include dividends and stock splits
    )
    
    def __init__(self):
        """Initialize the Yahoo Finance data feed."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @classmethod
    def create_data_feed(
        cls,
        symbol: str,
        period: str = '1y',
        interval: str = '1d',
        start: Optional[Union[str, datetime]] = None,
        end: Optional[Union[str, datetime]] = None,
        auto_adjust: bool = True,
        prepost: bool = False,
        actions: bool = True
    ) -> 'YahooDataFeed':
        """
        Create a Yahoo Finance data feed.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL')
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date for data retrieval
            end: End date for data retrieval
            auto_adjust: Auto adjust prices for splits and dividends
            prepost: Include pre/post market data
            actions: Include dividends and stock splits
            
        Returns:
            YahooDataFeed instance
        """
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            if start and end:
                # Use date range if provided
                df = ticker.history(
                    start=start,
                    end=end,
                    interval=interval,
                    auto_adjust=auto_adjust,
                    prepost=prepost,
                    actions=actions
                )
            else:
                # Use period if no date range provided
                df = ticker.history(
                    period=period,
                    interval=interval,
                    auto_adjust=auto_adjust,
                    prepost=prepost,
                    actions=actions
                )
            
            if df.empty:
                raise ValueError(f"No data retrieved for symbol {symbol}")
            
            # Prepare data for Backtrader
            df.index = pd.to_datetime(df.index)
            df = df.dropna()
            
            # Create data feed
            data_feed = cls(
                dataname=df,
                symbol=symbol,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                prepost=prepost,
                actions=actions
            )
            
            logging.info("Created Yahoo data feed for %s: %d bars", symbol, len(df))
            return data_feed
            
        except (ValueError, ConnectionError, KeyError) as e:
            logging.error("Failed to create Yahoo data feed for %s: %s", symbol, str(e))
            raise
    
    @staticmethod
    def get_available_symbols() -> list:
        """
        Get a list of popular stock symbols for testing.
        
        Returns:
            List of stock symbols
        """
        return [
            # Tech stocks
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            # Financial
            'JPM', 'BAC', 'GS', 'MS', 'WFC', 'C',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON',
            # Consumer
            'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'TMO',
            # Energy
            'XOM', 'CVX', 'COP', 'SLB',
            # ETFs
            'SPY', 'QQQ', 'IWM', 'GLD', 'SLV'
        ]
    
    @staticmethod
    def get_ticker_info(symbol: str) -> dict:
        """
        Get basic information about a ticker.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with ticker information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 'N/A'),
                'price': info.get('currentPrice', 'N/A'),
                'currency': info.get('currency', 'USD')
            }
        except (ValueError, ConnectionError, KeyError) as e:
            logging.error("Failed to get info for %s: %s", symbol, str(e))
            return {'symbol': symbol, 'error': str(e)}