"""
统一数据源架构

整合P1-1的高性能实时功能和P1-2的多源集成能力，
提供完整的数据解决方案：
1. 高性能WebSocket实时数据 (<100ms延迟)
2. 多数据源支持 (股票、加密货币、经济指标)
3. 统一的数据接口和缓存机制
4. Backtrader无缝集成
5. 数据质量监控和性能优化
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class DataType(Enum):
    """数据类型枚举"""
    STOCK_PRICE = "stock_price"
    CRYPTO_PRICE = "crypto_price"
    ECONOMIC_INDICATOR = "economic_indicator"
    NEWS_SENTIMENT = "news_sentiment"
    OPTIONS = "options"
    FUTURES = "futures"


class DataFrequency(Enum):
    """数据频率枚举"""
    TICK = "tick"              # 逐笔
    SECOND_1 = "1s"            # 1秒
    MINUTE_1 = "1m"            # 1分钟
    MINUTE_5 = "5m"            # 5分钟
    MINUTE_15 = "15m"          # 15分钟
    MINUTE_30 = "30m"          # 30分钟
    HOUR_1 = "1h"              # 1小时
    HOUR_4 = "4h"              # 4小时
    DAY_1 = "1d"               # 日线
    WEEK_1 = "1w"              # 周线
    MONTH_1 = "1M"             # 月线


class SourceType(Enum):
    """数据源类型"""
    WEBSOCKET = "websocket"    # WebSocket实时流
    REST_API = "rest_api"      # REST API
    FILE = "file"              # 文件数据
    DATABASE = "database"      # 数据库


@dataclass
class MarketData:
    """通用市场数据结构"""
    symbol: str
    timestamp: datetime
    data_type: DataType
    frequency: DataFrequency
    
    # 价格数据
    price: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    
    # 买卖盘
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    
    # 质量指标
    latency_ms: Optional[float] = None
    source: Optional[str] = None
    
    # 扩展数据
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def spread(self) -> Optional[float]:
        """买卖价差"""
        if self.bid is not None and self.ask is not None:
            return self.ask - self.bid
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'data_type': self.data_type.value,
            'frequency': self.frequency.value,
            'price': self.price,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'bid': self.bid,
            'ask': self.ask,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'latency_ms': self.latency_ms,
            'source': self.source,
            'spread': self.spread,
            **self.extra_data
        }


@dataclass
class StockData(MarketData):
    """股票数据扩展"""
    dividend_yield: Optional[float] = None
    pe_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    
    def __post_init__(self):
        if self.data_type != DataType.STOCK_PRICE:
            self.data_type = DataType.STOCK_PRICE


@dataclass
class CryptoData(MarketData):
    """加密货币数据扩展"""
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    
    def __post_init__(self):
        if self.data_type != DataType.CRYPTO_PRICE:
            self.data_type = DataType.CRYPTO_PRICE


@dataclass
class EconomicData(MarketData):
    """经济指标数据扩展"""
    indicator_name: Optional[str] = None
    unit: Optional[str] = None
    frequency_text: Optional[str] = None
    release_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.data_type != DataType.ECONOMIC_INDICATOR:
            self.data_type = DataType.ECONOMIC_INDICATOR


class DataSourceError(Exception):
    """数据源异常"""
    pass


class DataSourceProtocol(Protocol):
    """数据源协议接口"""
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        ...
    
    def get_historical_data(self, symbol: str, frequency: DataFrequency, 
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[MarketData]:
        """获取历史数据"""
        ...
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的符号列表"""
        ...


class BaseDataSource(ABC):
    """数据源基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.source_type = SourceType.REST_API
        self.supported_data_types = [DataType.STOCK_PRICE]
        self.rate_limit_ms = 1000  # 默认1秒间隔
        self.last_request_time = datetime.min
        
    @abstractmethod
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, frequency: DataFrequency,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[MarketData]:
        """获取历史数据"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """获取支持的符号列表"""
        pass
    
    def supports_data_type(self, data_type: DataType) -> bool:
        """检查是否支持指定数据类型"""
        return data_type in self.supported_data_types
    
    def supports_frequency(self, frequency: DataFrequency) -> bool:
        """检查是否支持指定频率"""
        # 默认支持所有频率，子类可以重写
        return True
    
    def check_rate_limit(self) -> bool:
        """检查速率限制"""
        now = datetime.now()
        if (now - self.last_request_time).total_seconds() * 1000 < self.rate_limit_ms:
            return False
        self.last_request_time = now
        return True


class WebSocketDataSource(BaseDataSource):
    """WebSocket数据源基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.source_type = SourceType.WEBSOCKET
        self.websocket_url = None
        self.connection = None
        self.subscriptions = set()
        
    @abstractmethod
    async def connect(self) -> bool:
        """建立WebSocket连接"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开WebSocket连接"""
        pass
    
    @abstractmethod
    async def subscribe(self, symbol: str, data_type: DataType) -> bool:
        """订阅数据流"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, symbol: str, data_type: DataType) -> bool:
        """取消订阅"""
        pass


# 导出主要接口
__all__ = [
    'DataType', 'DataFrequency', 'SourceType',
    'MarketData', 'StockData', 'CryptoData', 'EconomicData',
    'DataSourceError', 'DataSourceProtocol', 'BaseDataSource', 'WebSocketDataSource'
]