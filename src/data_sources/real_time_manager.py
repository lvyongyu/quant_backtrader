"""
实时数据源管理器

统一管理所有数据源，提供：
1. 数据源注册和配置
2. 实时数据获取和分发
3. 数据缓存和存储
4. 数据质量监控
5. 异常处理和重试机制
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
import threading
import queue
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod

from . import BaseDataSource, MarketData, DataType, DataFrequency, DataSourceError
from .yahoo_finance import YahooFinanceSource
from .crypto_sources import CoinGeckoSource
from .economic_sources import FREDSource


@dataclass
class DataFeedConfig:
    """数据订阅配置"""
    symbol: str
    data_type: DataType
    frequency: DataFrequency
    source: str
    callback: Optional[Callable] = None
    active: bool = True
    last_update: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 5


@dataclass
class DataCache:
    """数据缓存"""
    data: Dict[str, List[MarketData]] = field(default_factory=dict)
    last_updated: Dict[str, datetime] = field(default_factory=dict)
    cache_duration: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    
    def get_cache_key(self, symbol: str, data_type: DataType, frequency: DataFrequency) -> str:
        """生成缓存键"""
        return f"{symbol}_{data_type.value}_{frequency.value}"
    
    def is_cached(self, symbol: str, data_type: DataType, frequency: DataFrequency) -> bool:
        """检查数据是否已缓存且有效"""
        cache_key = self.get_cache_key(symbol, data_type, frequency)
        
        if cache_key not in self.data:
            return False
        
        last_update = self.last_updated.get(cache_key)
        if not last_update:
            return False
        
        return datetime.now() - last_update < self.cache_duration
    
    def get_cached_data(self, symbol: str, data_type: DataType, frequency: DataFrequency) -> Optional[List[MarketData]]:
        """获取缓存数据"""
        if self.is_cached(symbol, data_type, frequency):
            cache_key = self.get_cache_key(symbol, data_type, frequency)
            return self.data[cache_key]
        return None
    
    def cache_data(self, symbol: str, data_type: DataType, frequency: DataFrequency, data: List[MarketData]):
        """缓存数据"""
        cache_key = self.get_cache_key(symbol, data_type, frequency)
        self.data[cache_key] = data
        self.last_updated[cache_key] = datetime.now()


class DataSubscriptionManager:
    """数据订阅管理器"""
    
    def __init__(self):
        self.subscriptions: Dict[str, DataFeedConfig] = {}
        self.data_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.update_interval = 1.0  # 秒
        
    def subscribe(self, symbol: str, data_type: DataType, frequency: DataFrequency,
                 source: str, callback: Optional[Callable] = None) -> str:
        """订阅数据流"""
        sub_id = f"{symbol}_{data_type.value}_{frequency.value}_{source}"
        
        config = DataFeedConfig(
            symbol=symbol,
            data_type=data_type,
            frequency=frequency,
            source=source,
            callback=callback
        )
        
        self.subscriptions[sub_id] = config
        logging.info(f"Subscribed to {sub_id}")
        
        return sub_id
    
    def unsubscribe(self, sub_id: str):
        """取消订阅"""
        if sub_id in self.subscriptions:
            del self.subscriptions[sub_id]
            logging.info(f"Unsubscribed from {sub_id}")
    
    def start(self):
        """启动订阅服务"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logging.info("Data subscription manager started")
    
    def stop(self):
        """停止订阅服务"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logging.info("Data subscription manager stopped")
    
    def _worker_loop(self):
        """工作线程循环"""
        while self.running:
            try:
                # 处理所有活跃订阅
                for sub_id, config in self.subscriptions.items():
                    if not config.active:
                        continue
                    
                    # 检查是否需要更新
                    now = datetime.now()
                    if config.last_update:
                        time_diff = now - config.last_update
                        min_interval = self._get_min_update_interval(config.frequency)
                        
                        if time_diff < min_interval:
                            continue
                    
                    # 将更新任务放入队列
                    self.data_queue.put(('update', sub_id, config))
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logging.error(f"Subscription manager error: {e}")
                time.sleep(5)  # 错误时等待更长时间
    
    def _get_min_update_interval(self, frequency: DataFrequency) -> timedelta:
        """获取最小更新间隔"""
        intervals = {
            DataFrequency.TICK: timedelta(seconds=1),
            DataFrequency.MINUTE_1: timedelta(minutes=1),
            DataFrequency.MINUTE_5: timedelta(minutes=5),
            DataFrequency.MINUTE_15: timedelta(minutes=15),
            DataFrequency.HOUR_1: timedelta(hours=1),
            DataFrequency.DAY_1: timedelta(hours=6),  # 日线数据6小时更新一次
            DataFrequency.WEEK_1: timedelta(days=1),
            DataFrequency.MONTH_1: timedelta(days=7)
        }
        return intervals.get(frequency, timedelta(minutes=5))


class RealTimeDataManager:
    """实时数据管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.data_sources: Dict[str, BaseDataSource] = {}
        self.cache = DataCache()
        self.subscription_manager = DataSubscriptionManager()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger("RealTimeDataManager")
        
        # 初始化数据源
        self._initialize_data_sources()
    
    def _initialize_data_sources(self):
        """初始化数据源"""
        try:
            # Yahoo Finance
            yahoo_config = self.config.get('yahoo_finance', {})
            self.data_sources['yahoo'] = YahooFinanceSource(yahoo_config)
            
            # CoinGecko
            coingecko_config = self.config.get('coingecko', {})
            self.data_sources['coingecko'] = CoinGeckoSource(coingecko_config)
            
            # FRED
            fred_config = self.config.get('fred', {})
            fred_api_key = fred_config.get('api_key')
            self.data_sources['fred'] = FREDSource(fred_api_key, fred_config)
            
            self.logger.info(f"Initialized {len(self.data_sources)} data sources")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize data sources: {e}")
    
    def register_data_source(self, name: str, source: BaseDataSource):
        """注册新的数据源"""
        self.data_sources[name] = source
        self.logger.info(f"Registered data source: {name}")
    
    async def get_real_time_data(self, symbol: str, data_type: DataType, 
                                source: str = None) -> Optional[Dict[str, Any]]:
        """获取实时数据"""
        try:
            # 确定数据源
            if not source:
                source = self._get_default_source(data_type)
            
            if source not in self.data_sources:
                raise DataSourceError(f"Data source '{source}' not available")
            
            data_source = self.data_sources[source]
            
            # 获取实时数据
            if hasattr(data_source, 'get_real_time_price'):
                data = data_source.get_real_time_price(symbol)
                return data
            else:
                self.logger.warning(f"Data source '{source}' doesn't support real-time data")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get real-time data for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, data_type: DataType,
                                 frequency: DataFrequency = DataFrequency.DAY_1,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 source: str = None,
                                 use_cache: bool = True) -> List[MarketData]:
        """获取历史数据"""
        try:
            # 检查缓存
            if use_cache:
                cached_data = self.cache.get_cached_data(symbol, data_type, frequency)
                if cached_data:
                    self.logger.debug(f"Returning cached data for {symbol}")
                    return cached_data
            
            # 确定数据源
            if not source:
                source = self._get_default_source(data_type)
            
            if source not in self.data_sources:
                raise DataSourceError(f"Data source '{source}' not available")
            
            data_source = self.data_sources[source]
            
            # 获取数据
            data = await data_source.get_data(symbol, data_type, frequency, start_date, end_date)
            
            # 缓存数据
            if use_cache and data:
                self.cache.cache_data(symbol, data_type, frequency, data)
            
            self.logger.info(f"Retrieved {len(data)} data points for {symbol} from {source}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            return []
    
    def subscribe_to_data(self, symbol: str, data_type: DataType, 
                         frequency: DataFrequency, callback: Callable,
                         source: str = None) -> str:
        """订阅实时数据流"""
        if not source:
            source = self._get_default_source(data_type)
        
        return self.subscription_manager.subscribe(
            symbol, data_type, frequency, source, callback
        )
    
    def unsubscribe_from_data(self, subscription_id: str):
        """取消数据订阅"""
        self.subscription_manager.unsubscribe(subscription_id)
    
    def start_real_time_feeds(self):
        """启动实时数据流"""
        self.subscription_manager.start()
        self.logger.info("Real-time data feeds started")
    
    def stop_real_time_feeds(self):
        """停止实时数据流"""
        self.subscription_manager.stop()
        self.logger.info("Real-time data feeds stopped")
    
    def get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览"""
        try:
            overview = {
                'timestamp': datetime.now(),
                'stocks': {},
                'crypto': {},
                'economic': {}
            }
            
            # 主要股票指数
            major_indices = ['^GSPC', '^DJI', '^IXIC']
            for index in major_indices:
                try:
                    data = self.data_sources['yahoo'].get_real_time_price(index)
                    overview['stocks'][index] = data
                except:
                    continue
            
            # 主要加密货币
            major_cryptos = ['BTC', 'ETH', 'BNB']
            for crypto in major_cryptos:
                try:
                    data = self.data_sources['coingecko'].get_real_time_price(crypto)
                    overview['crypto'][crypto] = data
                except:
                    continue
            
            # 主要经济指标（使用缓存的最新值）
            economic_indicators = ['FEDFUNDS', 'DGS10', 'VIXCLS']
            for indicator in economic_indicators:
                cache_key = self.cache.get_cache_key(indicator, DataType.ECONOMIC_INDICATOR, DataFrequency.DAY_1)
                if cache_key in self.cache.data and self.cache.data[cache_key]:
                    latest_data = self.cache.data[cache_key][-1]
                    overview['economic'][indicator] = {
                        'value': latest_data.value if hasattr(latest_data, 'value') else None,
                        'timestamp': latest_data.timestamp
                    }
            
            return overview
            
        except Exception as e:
            self.logger.error(f"Failed to get market overview: {e}")
            return {'error': str(e)}
    
    def _get_default_source(self, data_type: DataType) -> str:
        """根据数据类型获取默认数据源"""
        defaults = {
            DataType.STOCK_PRICE: 'yahoo',
            DataType.CRYPTO_PRICE: 'coingecko',
            DataType.ECONOMIC_INDICATOR: 'fred',
            DataType.NEWS_SENTIMENT: 'yahoo'  # 可以扩展
        }
        return defaults.get(data_type, 'yahoo')
    
    def get_available_symbols(self, data_type: DataType) -> List[str]:
        """获取可用的股票代码"""
        source = self._get_default_source(data_type)
        if source in self.data_sources:
            return self.data_sources[source].get_supported_symbols()
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            'timestamp': datetime.now(),
            'overall_status': 'healthy',
            'data_sources': {},
            'cache_status': {
                'cached_keys': len(self.cache.data),
                'cache_hit_rate': 0.0  # 可以实现缓存命中率统计
            },
            'subscriptions': len(self.subscription_manager.subscriptions)
        }
        
        # 检查每个数据源
        for name, source in self.data_sources.items():
            try:
                # 简单的连通性测试
                supported_symbols = source.get_supported_symbols()
                status['data_sources'][name] = {
                    'status': 'healthy',
                    'supported_symbols_count': len(supported_symbols)
                }
            except Exception as e:
                status['data_sources'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                status['overall_status'] = 'degraded'
        
        return status


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_real_time_manager():
        """测试实时数据管理器"""
        # 配置
        config = {
            'yahoo_finance': {},
            'coingecko': {},
            'fred': {
                'api_key': None  # 使用demo模式
            }
        }
        
        manager = RealTimeDataManager(config)
        
        try:
            # 健康检查
            print("🏥 数据源健康检查...")
            health = manager.health_check()
            print(f"✅ 总体状态: {health['overall_status']}")
            
            for source, status in health['data_sources'].items():
                print(f"   {source}: {status['status']}")
            
            # 获取实时数据
            print("\n💰 获取实时数据...")
            apple_data = await manager.get_real_time_data("AAPL", DataType.STOCK_PRICE)
            if apple_data:
                print(f"✅ AAPL: ${apple_data['price']:.2f}")
            
            btc_data = await manager.get_real_time_data("BTC", DataType.CRYPTO_PRICE)
            if btc_data:
                print(f"✅ BTC: ${btc_data['price']:,.2f}")
            
            # 获取历史数据
            print("\n📈 获取历史数据...")
            start_date = datetime.now() - timedelta(days=7)
            historical_data = await manager.get_historical_data(
                "AAPL", DataType.STOCK_PRICE, DataFrequency.DAY_1, start_date
            )
            print(f"✅ AAPL历史数据: {len(historical_data)}条记录")
            
            # 市场概览
            print("\n📊 市场概览...")
            overview = manager.get_market_overview()
            if 'stocks' in overview:
                for symbol, data in overview['stocks'].items():
                    print(f"   {symbol}: ${data.get('price', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    # 运行测试
    print("🧪 实时数据管理器测试")
    print("=" * 50)
    asyncio.run(test_real_time_manager())