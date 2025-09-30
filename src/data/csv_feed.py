"""
CSV data feed implementation.

This module provides a data feed for loading historical market data
from CSV files with flexible column mapping.
"""

import backtrader as bt
from datetime import datetime
from typing import Optional
import logging
import os

try:
    import pandas as pd
except ImportError as e:
    print(f"警告: 缺少依赖包 {e}, CSV数据源功能可能受限")
    pd = None


class CSVDataFeed(bt.feeds.PandasData):
    """
    CSV data feed for Backtrader.
    
    Loads market data from CSV files with configurable column mapping.
    """
    
    params = (
        ('file_path', None),          # Path to CSV file
        ('datetime_col', 'Date'),     # DateTime column name
        ('open_col', 'Open'),         # Open price column name
        ('high_col', 'High'),         # High price column name  
        ('low_col', 'Low'),           # Low price column name
        ('close_col', 'Close'),       # Close price column name
        ('volume_col', 'Volume'),     # Volume column name
        ('datetime_format', None),    # DateTime format string
        ('separator', ','),           # CSV separator
        ('header', True),             # CSV has header row
    )
    
    def __init__(self):
        """Initialize the CSV data feed."""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @classmethod
    def create_data_feed(
        cls,
        file_path: str,
        datetime_col: str = 'Date',
        open_col: str = 'Open',
        high_col: str = 'High',
        low_col: str = 'Low', 
        close_col: str = 'Close',
        volume_col: str = 'Volume',
        datetime_format: Optional[str] = None,
        separator: str = ',',
        header: bool = True
    ) -> 'CSVDataFeed':
        """
        Create a CSV data feed.
        
        Args:
            file_path: Path to the CSV file
            datetime_col: Name of the datetime column
            open_col: Name of the open price column
            high_col: Name of the high price column
            low_col: Name of the low price column
            close_col: Name of the close price column
            volume_col: Name of the volume column
            datetime_format: DateTime format string (auto-detected if None)
            separator: CSV separator character
            header: Whether CSV has header row
            
        Returns:
            CSVDataFeed instance
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            
            # Read CSV file
            df = pd.read_csv(
                file_path,
                sep=separator,
                header=0 if header else None
            )
            
            if df.empty:
                raise ValueError(f"CSV file is empty: {file_path}")
            
            # Map column names
            column_mapping = {
                datetime_col: 'datetime',
                open_col: 'open',
                high_col: 'high', 
                low_col: 'low',
                close_col: 'close',
                volume_col: 'volume'
            }
            
            # Check required columns exist
            missing_cols = []
            for col in column_mapping.keys():
                if col not in df.columns:
                    missing_cols.append(col)
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Rename columns to standard names
            df = df.rename(columns=column_mapping)
            
            # Parse datetime column
            if datetime_format:
                df['datetime'] = pd.to_datetime(df['datetime'], format=datetime_format)
            else:
                df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Set datetime as index
            df.set_index('datetime', inplace=True)
            
            # Sort by datetime
            df.sort_index(inplace=True)
            
            # Remove any NaN values
            df = df.dropna()
            
            # Ensure numeric columns are float
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Create data feed
            data_feed = cls(
                dataname=df,
                file_path=file_path,
                datetime_col=datetime_col,
                open_col=open_col,
                high_col=high_col,
                low_col=low_col,
                close_col=close_col,
                volume_col=volume_col,
                datetime_format=datetime_format,
                separator=separator,
                header=header
            )
            
            logging.info("Created CSV data feed from %s: %d bars", file_path, len(df))
            return data_feed
            
        except (FileNotFoundError, ValueError, KeyError) as e:
            logging.error("Failed to create CSV data feed from %s: %s", file_path, str(e))
            raise
    
    @staticmethod
    def create_sample_csv(file_path: str, days: int = 100) -> str:
        """
        Create a sample CSV file with synthetic OHLCV data.
        
        Args:
            file_path: Path where to save the CSV file
            days: Number of days of data to generate
            
        Returns:
            Path to created CSV file
        """
        try:
            import numpy as np
        except ImportError:
            print("警告: 缺少numpy依赖，使用简化数据生成")
            # 简化的数据生成逻辑
            import random
            data = []
            base_price = 100.0
            for day in range(days):
                date = datetime.now() - pd.Timedelta(days=days-day)
                close = base_price + random.uniform(-5, 5)
                data.append([
                    date.strftime('%Y-%m-%d'),
                    close,
                    close + random.uniform(0, 2),
                    close - random.uniform(0, 2),
                    close,
                    random.randint(100000, 1000000)
                ])
                base_price = close
                
            df = pd.DataFrame(data, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df.to_csv(file_path, index=False)
            logging.info("Created sample CSV file: %s with %d rows", file_path, len(df))
            return file_path
        
        # Generate sample data
        dates = pd.date_range(
            start=datetime.now() - pd.Timedelta(days=days),
            periods=days,
            freq='D'
        )
        
        # Simple random walk for prices
        np.random.seed(42)  # For reproducible results
        base_price = 100.0
        returns = np.random.normal(0, 0.02, days)  # 2% daily volatility
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # Generate OHLCV data
        data = []
        for date, close in zip(dates, prices):
            # Generate realistic OHLC from close price
            volatility = abs(np.random.normal(0, 0.01))  # Intraday volatility
            high = close * (1 + volatility)
            low = close * (1 - volatility)
            open_price = low + (high - low) * np.random.random()
            volume = int(np.random.uniform(100000, 1000000))
            
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Open': round(open_price, 2),
                'High': round(high, 2),
                'Low': round(low, 2),
                'Close': round(close, 2),
                'Volume': volume
            })
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        
        logging.info("Created sample CSV file: %s with %d rows", file_path, len(df))
        return file_path