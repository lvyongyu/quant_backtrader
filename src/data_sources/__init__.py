"""
实时数据源集成模块

提供统一的金融数据接入接口，支持多种数据源：
- 股票市场数据 (Yahoo Finance, Alpha Vantage, IEX)
- 加密货币数据 (Binance, CoinGecko)
- 宏观经济数据 (FRED, World Bank)
- 新闻情感数据 (News API, Twitter)

核心功能：
1. 数据源适配器统一接口
2. 实时数据获取和缓存
3. 数据质量验证和清洗
4. 数据存储和历史管理
5. API限制和错误处理
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
import logging
import asyncio
import aiohttp
import time
from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    """数据类型枚举"""
    STOCK_PRICE = "stock_price"
    CRYPTO_PRICE = "crypto_price" 
    ECONOMIC_INDICATOR = "economic_indicator"
    NEWS_SENTIMENT = "news_sentiment"
    MARKET_DEPTH = "market_depth"
    VOLUME_PROFILE = "volume_profile"


class DataFrequency(Enum):
    """数据频率枚举"""
    TICK = "tick"           # 逐笔数据
    MINUTE_1 = "1m"         # 1分钟
    MINUTE_5 = "5m"         # 5分钟
    MINUTE_15 = "15m"       # 15分钟
    HOUR_1 = "1h"           # 1小时
    DAY_1 = "1d"            # 日线
    WEEK_1 = "1w"           # 周线
    MONTH_1 = "1M"          # 月线


@dataclass
class MarketData:
    """市场数据基础类"""
    symbol: str
    timestamp: datetime
    data_type: DataType
    frequency: DataFrequency
    data: Dict[str, Any]
    source: str
    
    def __post_init__(self):
        """数据验证"""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not isinstance(self.timestamp, datetime):
            raise TypeError("Timestamp must be datetime object")


@dataclass
class StockData(MarketData):
    """股票数据"""
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adjusted_close: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.data_type = DataType.STOCK_PRICE
        
        # 价格验证
        prices = [self.open_price, self.high_price, self.low_price, self.close_price]
        if any(p <= 0 for p in prices):
            raise ValueError("All prices must be positive")
        
        # 高低价关系验证
        if self.high_price < max(self.open_price, self.close_price):
            raise ValueError("High price cannot be less than open/close price")
        if self.low_price > min(self.open_price, self.close_price):
            raise ValueError("Low price cannot be greater than open/close price")


@dataclass
class CryptoData(MarketData):
    """加密货币数据"""
    price: float
    volume_24h: float
    market_cap: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.data_type = DataType.CRYPTO_PRICE
        
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.volume_24h < 0:
            raise ValueError("Volume cannot be negative")


@dataclass
class EconomicData(MarketData):
    """经济指标数据"""
    indicator_name: str
    value: float
    unit: str
    release_date: datetime
    previous_value: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.data_type = DataType.ECONOMIC_INDICATOR


@dataclass 
class NewsData(MarketData):
    """新闻数据"""
    headline: str
    content: str
    sentiment_score: float  # -1 to 1
    confidence: float       # 0 to 1
    source_url: str
    
    def __post_init__(self):
        super().__post_init__()
        self.data_type = DataType.NEWS_SENTIMENT
        
        if not (-1 <= self.sentiment_score <= 1):
            raise ValueError("Sentiment score must be between -1 and 1")
        if not (0 <= self.confidence <= 1):
            raise ValueError("Confidence must be between 0 and 1")


class DataSourceError(Exception):
    """数据源异常基类"""
    pass


class APILimitError(DataSourceError):
    """API限制异常"""
    pass


class DataQualityError(DataSourceError):
    """数据质量异常"""
    pass


class BaseDataSource(ABC):
    """数据源基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"DataSource.{name}")
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit = self.config.get('rate_limit', 100)  # 每分钟请求数
        
    @abstractmethod
    async def get_data(self, symbol: str, data_type: DataType, 
                      frequency: DataFrequency = DataFrequency.DAY_1,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[MarketData]:
        """获取数据的抽象方法"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """获取支持的股票代码"""
        pass
    
    def _check_rate_limit(self):
        """检查API限制"""
        current_time = time.time()
        time_diff = current_time - self._last_request_time
        
        if time_diff < 60:  # 一分钟内
            if self._request_count >= self._rate_limit:
                wait_time = 60 - time_diff
                raise APILimitError(f"Rate limit exceeded, wait {wait_time:.1f} seconds")
        else:
            self._request_count = 0
        
        self._request_count += 1
        self._last_request_time = current_time
    
    def validate_data(self, data: MarketData) -> bool:
        """验证数据质量"""
        try:
            # 基础验证
            if not data.symbol or not data.timestamp:
                return False
            
            # 特定类型验证
            if isinstance(data, StockData):
                return self._validate_stock_data(data)
            elif isinstance(data, CryptoData):
                return self._validate_crypto_data(data)
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Data validation failed: {e}")
            return False
    
    def _validate_stock_data(self, data: StockData) -> bool:
        """验证股票数据"""
        # 价格合理性检查
        prices = [data.open_price, data.high_price, data.low_price, data.close_price]
        if any(p <= 0 or p > 10000 for p in prices):  # 假设最高价格不超过10000
            return False
        
        # 成交量检查
        if data.volume < 0 or data.volume > 1e12:  # 成交量上限
            return False
        
        return True
    
    def _validate_crypto_data(self, data: CryptoData) -> bool:
        """验证加密货币数据"""
        if data.price <= 0 or data.price > 1e6:  # 价格范围检查
            return False
        
        if data.volume_24h < 0:
            return False
        
        return True