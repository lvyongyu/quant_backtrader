"""
数据源适配器

将现有的数据源实现适配到统一架构中，
确保兼容性和功能完整性。
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# 导入统一架构
from . import (
    BaseDataSource, WebSocketDataSource, DataType, DataFrequency, 
    MarketData, StockData, CryptoData, EconomicData
)

# 导入现有数据源
try:
    from ..data_sources.yahoo_finance import YahooFinanceSource
    from ..data_sources.crypto_sources import CoinGeckoSource  
    from ..data_sources.economic_sources import FREDSource
except ImportError:
    # 如果导入失败，创建占位符类
    class YahooFinanceSource:
        def __init__(self, config): pass
        def get_real_time_price(self, symbol): return {}
        def get_historical_data(self, *args): return []
        def get_supported_symbols(self): return []
    
    class CoinGeckoSource:
        def __init__(self, config): pass
        def get_real_time_price(self, symbol): return {}
        def get_historical_data(self, *args): return []
        def get_supported_symbols(self): return []
    
    class FREDSource:
        def __init__(self, api_key, config): pass
        def get_real_time_price(self, symbol): return {}
        def get_historical_data(self, *args): return []
        def get_supported_symbols(self): return []


class YahooFinanceAdapter(BaseDataSource):
    """Yahoo Finance 数据源适配器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_data_types = [DataType.STOCK_PRICE]
        self.rate_limit_ms = 200  # Yahoo Finance 限制
        
        # 创建原始数据源
        self.yahoo_source = YahooFinanceSource(config or {})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        if not self.check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        try:
            return self.yahoo_source.get_real_time_price(symbol)
        except Exception as e:
            self.logger.error(f"Yahoo Finance real-time error for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, frequency: DataFrequency,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[MarketData]:
        """获取历史数据"""
        try:
            # 调用原始数据源
            raw_data = self.yahoo_source.get_historical_data(
                symbol, frequency, start_date, end_date
            )
            
            # 转换为统一格式
            market_data = []
            for item in raw_data:
                if hasattr(item, 'timestamp'):
                    # 如果已经是MarketData格式
                    market_data.append(item)
                else:
                    # 转换字典格式数据
                    stock_data = StockData(
                        symbol=symbol,
                        timestamp=item.get('timestamp', datetime.now()),
                        data_type=DataType.STOCK_PRICE,
                        frequency=frequency,
                        open=item.get('open'),
                        high=item.get('high'),
                        low=item.get('low'),
                        close=item.get('close'),
                        volume=item.get('volume'),
                        source='yahoo'
                    )
                    market_data.append(stock_data)
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Yahoo Finance historical error for {symbol}: {e}")
            return []
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的符号列表"""
        try:
            return self.yahoo_source.get_supported_symbols()
        except Exception as e:
            self.logger.error(f"Yahoo Finance symbols error: {e}")
            return []


class CoinGeckoAdapter(BaseDataSource):
    """CoinGecko 数据源适配器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_data_types = [DataType.CRYPTO_PRICE]
        self.rate_limit_ms = 1000  # CoinGecko 限制
        
        # 创建原始数据源
        self.coingecko_source = CoinGeckoSource(config or {})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        if not self.check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        try:
            return self.coingecko_source.get_real_time_price(symbol)
        except Exception as e:
            self.logger.error(f"CoinGecko real-time error for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, frequency: DataFrequency,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[MarketData]:
        """获取历史数据"""
        try:
            raw_data = self.coingecko_source.get_historical_data(
                symbol, frequency, start_date, end_date
            )
            
            # 转换为统一格式
            market_data = []
            for item in raw_data:
                if hasattr(item, 'timestamp'):
                    market_data.append(item)
                else:
                    crypto_data = CryptoData(
                        symbol=symbol,
                        timestamp=item.get('timestamp', datetime.now()),
                        data_type=DataType.CRYPTO_PRICE,
                        frequency=frequency,
                        price=item.get('price'),
                        volume=item.get('volume'),
                        market_cap=item.get('market_cap'),
                        volume_24h=item.get('volume_24h'),
                        change_24h=item.get('change_24h'),
                        source='coingecko'
                    )
                    market_data.append(crypto_data)
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"CoinGecko historical error for {symbol}: {e}")
            return []
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的符号列表"""
        try:
            return self.coingecko_source.get_supported_symbols()
        except Exception as e:
            self.logger.error(f"CoinGecko symbols error: {e}")
            return []


class FREDAdapter(BaseDataSource):
    """FRED 数据源适配器"""
    
    def __init__(self, api_key: Optional[str] = None, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_data_types = [DataType.ECONOMIC_INDICATOR]
        self.rate_limit_ms = 5000  # FRED 限制较严格
        
        # 创建原始数据源
        self.fred_source = FREDSource(api_key, config or {})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时经济指标"""
        if not self.check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        try:
            # FRED通常没有实时数据，返回最新数据
            historical = self.get_historical_data(symbol, DataFrequency.DAY_1)
            if historical:
                latest = historical[-1]
                return {
                    'price': latest.price,
                    'timestamp': latest.timestamp,
                    'symbol': symbol
                }
            return {}
        except Exception as e:
            self.logger.error(f"FRED real-time error for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, frequency: DataFrequency,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[MarketData]:
        """获取历史数据"""
        try:
            raw_data = self.fred_source.get_historical_data(
                symbol, frequency, start_date, end_date
            )
            
            # 转换为统一格式
            market_data = []
            for item in raw_data:
                if hasattr(item, 'timestamp'):
                    market_data.append(item)
                else:
                    economic_data = EconomicData(
                        symbol=symbol,
                        timestamp=item.get('timestamp', datetime.now()),
                        data_type=DataType.ECONOMIC_INDICATOR,
                        frequency=frequency,
                        price=item.get('value'),  # 经济指标用value作为price
                        indicator_name=item.get('indicator_name'),
                        unit=item.get('unit'),
                        release_date=item.get('release_date'),
                        source='fred'
                    )
                    market_data.append(economic_data)
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"FRED historical error for {symbol}: {e}")
            return []
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的符号列表"""
        try:
            return self.fred_source.get_supported_symbols()
        except Exception as e:
            self.logger.error(f"FRED symbols error: {e}")
            return []


class HighPerformanceWebSocketAdapter(WebSocketDataSource):
    """高性能WebSocket适配器
    
    将现有的WebSocket实现适配到统一架构
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.supported_data_types = [DataType.STOCK_PRICE, DataType.CRYPTO_PRICE]
        self.websocket_url = config.get('websocket_url') if config else None
        self.update_interval_ms = config.get('update_interval_ms', 100) if config else 100
        
        # 导入高性能实时数据源
        try:
            from ..data.realtime_feed import RealTimeDataFeed
            self.realtime_feed = None
            self.RealTimeDataFeed = RealTimeDataFeed
        except ImportError:
            self.RealTimeDataFeed = None
            self.logger.warning("High-performance WebSocket feed not available")
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def connect(self) -> bool:
        """建立WebSocket连接"""
        if not self.RealTimeDataFeed:
            return False
        
        try:
            # 创建高性能数据源
            self.realtime_feed = self.RealTimeDataFeed(
                symbols=list(self.subscriptions),
                data_callback=self._on_data_received,
                update_interval_ms=self.update_interval_ms
            )
            
            # 启动数据流
            self.realtime_feed.start()
            self.logger.info("WebSocket connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.realtime_feed:
            try:
                self.realtime_feed.stop()
                self.realtime_feed = None
                self.logger.info("WebSocket connection closed")
            except Exception as e:
                self.logger.error(f"Error closing WebSocket: {e}")
    
    async def subscribe(self, symbol: str, data_type: DataType) -> bool:
        """订阅数据流"""
        if data_type not in self.supported_data_types:
            return False
        
        self.subscriptions.add(symbol)
        
        # 如果已连接，重新配置数据源
        if self.realtime_feed:
            # 这里需要根据实际的RealTimeDataFeed API来实现
            pass
        
        self.logger.info(f"Subscribed to {symbol} {data_type.value}")
        return True
    
    async def unsubscribe(self, symbol: str, data_type: DataType) -> bool:
        """取消订阅"""
        self.subscriptions.discard(symbol)
        self.logger.info(f"Unsubscribed from {symbol} {data_type.value}")
        return True
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格（WebSocket源通过回调提供数据）"""
        # WebSocket源主要通过回调提供数据
        # 这里可以返回缓存的最新数据
        return {}
    
    def get_historical_data(self, symbol: str, frequency: DataFrequency,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[MarketData]:
        """获取历史数据（WebSocket源主要提供实时数据）"""
        # WebSocket源通常不提供历史数据
        return []
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的符号列表"""
        # 返回常见股票符号
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'BTC-USD', 'ETH-USD', 'ADA-USD', 'BNB-USD'
        ]
    
    def _on_data_received(self, market_data):
        """数据接收回调"""
        # 这里可以进一步处理数据，通知订阅者等
        # 具体实现取决于需求
        pass


# 便捷函数
def create_unified_data_sources(config: Dict[str, Any] = None) -> Dict[str, BaseDataSource]:
    """创建所有统一数据源"""
    config = config or {}
    sources = {}
    
    # Yahoo Finance
    yahoo_config = config.get('yahoo_finance', {})
    sources['yahoo'] = YahooFinanceAdapter(yahoo_config)
    
    # CoinGecko
    coingecko_config = config.get('coingecko', {})
    sources['coingecko'] = CoinGeckoAdapter(coingecko_config)
    
    # FRED
    fred_config = config.get('fred', {})
    fred_api_key = fred_config.get('api_key')
    sources['fred'] = FREDAdapter(fred_api_key, fred_config)
    
    # 高性能WebSocket（如果可用）
    websocket_config = config.get('websocket', {})
    if websocket_config.get('enabled', False):
        sources['websocket'] = HighPerformanceWebSocketAdapter(websocket_config)
    
    return sources


# 导出
__all__ = [
    'YahooFinanceAdapter', 'CoinGeckoAdapter', 'FREDAdapter', 
    'HighPerformanceWebSocketAdapter', 'create_unified_data_sources'
]