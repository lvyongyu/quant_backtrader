"""
Live data feed implementation.

This module provides a real-time data feed interface
for live trading applications. If data sources are unavailable,
the feed will fail rather than providing mock data.
"""

import backtrader as bt
from datetime import datetime
from typing import Optional
import logging
import threading
import time
import queue

try:
    import pandas as pd
except ImportError:
    print("错误: 缺少pandas依赖，实时数据源无法工作")
    pd = None


class LiveDataFeed(bt.feeds.DataBase):
    """
    Live data feed for real-time trading.
    
    This feed fetches real-time market data and fails gracefully
    if data sources are unavailable. No mock data is provided.
    """
    
    params = (
        ('symbol', 'AAPL'),
        ('update_interval', 60),
        ('buffer_size', 1000),
    )
    
    def __init__(self):
        """Initialize the live data feed."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Check dependencies
        if pd is None:
            raise ImportError("pandas is required for live data feed")
            
        self.data_queue = queue.Queue(maxsize=self.p.buffer_size)
        self.running = False
        self.data_thread = None
    
    def start(self):
        """Start the live data feed."""
        if not self.running:
            self.running = True
            self.data_thread = threading.Thread(target=self._data_worker, daemon=True)
            self.data_thread.start()
            self.logger.info("Started live data feed for %s", self.p.symbol)
    
    def stop(self):
        """Stop the live data feed."""
        if self.running:
            self.running = False
            if self.data_thread:
                self.data_thread.join(timeout=5)
            self.logger.info("Stopped live data feed for %s", self.p.symbol)
    
    def _data_worker(self):
        """Background worker thread for fetching live data."""
        while self.running:
            try:
                data_point = self._fetch_live_data()
                if data_point:
                    try:
                        self.data_queue.put_nowait(data_point)
                    except queue.Full:
                        self.logger.warning("Data queue full, dropping old data")
                        try:
                            self.data_queue.get_nowait()
                            self.data_queue.put_nowait(data_point)
                        except queue.Empty:
                            pass
                else:
                    self.logger.warning("No data received from source")
                
                time.sleep(self.p.update_interval)
                
            except (ConnectionError, ValueError, KeyError) as e:
                self.logger.error("Error in data worker: %s", str(e))
                self.logger.error("Live data feed failed - stopping")
                self.running = False
                break
    
    def _fetch_live_data(self) -> Optional[dict]:
        """Fetch live market data from real sources only."""
        try:
            try:
                import yfinance as yf
            except ImportError:
                self.logger.error("yfinance not available - cannot fetch live data")
                raise ImportError("yfinance is required for live data")
            
            ticker = yf.Ticker(self.p.symbol)
            df = ticker.history(period='1d', interval='1m')
            
            if df.empty:
                self.logger.warning("No data returned for %s", self.p.symbol)
                return None
            
            last_row = df.iloc[-1]
            timestamp = df.index[-1]
            
            return {
                'datetime': timestamp.to_pydatetime(),
                'open': float(last_row['Open']),
                'high': float(last_row['High']),
                'low': float(last_row['Low']),
                'close': float(last_row['Close']),
                'volume': int(last_row['Volume'])
            }
            
        except ImportError:
            raise
        except (ConnectionError, ValueError, KeyError) as e:
            self.logger.error("Failed to fetch live data: %s", str(e))
            raise
    
    def _load(self):
        """Load data from queue."""
        try:
            data_point = self.data_queue.get_nowait()
            
            # Set the data fields (Backtrader dynamic attributes)
            self.lines.datetime[0] = bt.date2num(data_point['datetime'])  # type: ignore
            self.lines.open[0] = data_point['open']  # type: ignore
            self.lines.high[0] = data_point['high']  # type: ignore
            self.lines.low[0] = data_point['low']  # type: ignore
            self.lines.close[0] = data_point['close']  # type: ignore
            self.lines.volume[0] = data_point['volume']  # type: ignore
            
            return True
            
        except queue.Empty:
            return False
        except (KeyError, ValueError, IndexError) as e:
            self.logger.error("Error loading data: %s", str(e))
            return False
