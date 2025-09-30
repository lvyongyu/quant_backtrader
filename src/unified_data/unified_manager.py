"""
统一数据管理器

整合高性能实时数据流和多源数据集成的核心管理器，
提供完整的数据访问解决方案。
"""

import asyncio
import logging
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import json

from . import (
    MarketData, StockData, CryptoData, EconomicData,
    DataType, DataFrequency, SourceType,
    BaseDataSource, WebSocketDataSource, DataSourceError
)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    source_name: str
    timestamp: datetime
    latency_ms: float
    success_rate: float
    data_points: int
    error_count: int
    quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_name': self.source_name,
            'timestamp': self.timestamp.isoformat(),
            'latency_ms': self.latency_ms,
            'success_rate': self.success_rate,
            'data_points': self.data_points,
            'error_count': self.error_count,
            'quality_score': self.quality_score
        }


@dataclass
class DataSubscription:
    """数据订阅配置"""
    symbol: str
    data_type: DataType
    frequency: DataFrequency
    source: str
    callback: Optional[Callable[[MarketData], None]] = None
    active: bool = True
    last_update: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 5
    
    @property
    def subscription_id(self) -> str:
        """订阅ID"""
        return f"{self.symbol}_{self.data_type.value}_{self.frequency.value}_{self.source}"


class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.latencies = deque(maxlen=window_size)
        self.prices = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)
        self.error_count = 0
        self.total_count = 0
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def add_data_point(self, data: MarketData):
        """添加数据点进行质量监控"""
        self.total_count += 1
        
        if data.latency_ms is not None:
            self.latencies.append(data.latency_ms)
            
            # 检查异常延迟
            if data.latency_ms > 500:  # 超过500ms警告
                self.logger.warning(f"High latency detected: {data.latency_ms:.2f}ms for {data.symbol}")
        
        if data.price is not None:
            self.prices.append(data.price)
        
        self.timestamps.append(data.timestamp)
    
    def add_error(self):
        """记录错误"""
        self.error_count += 1
    
    @property
    def avg_latency_ms(self) -> float:
        """平均延迟"""
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0
    
    @property
    def max_latency_ms(self) -> float:
        """最大延迟"""
        return max(self.latencies) if self.latencies else 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_count == 0:
            return 1.0
        return (self.total_count - self.error_count) / self.total_count
    
    @property
    def quality_score(self) -> float:
        """质量分数 (0-100)"""
        if not self.latencies:
            return 100.0
        
        # 基于延迟和成功率计算质量分数
        avg_latency = self.avg_latency_ms
        success_rate = self.success_rate
        
        # 延迟分数 (越低越好)
        latency_score = max(0, 100 - avg_latency / 10)  # 1000ms对应0分
        
        # 成功率分数
        success_score = success_rate * 100
        
        # 综合分数
        return (latency_score * 0.6 + success_score * 0.4)


class DataCache:
    """高性能数据缓存"""
    
    def __init__(self, default_ttl: timedelta = timedelta(minutes=5)):
        self.data: Dict[str, List[MarketData]] = {}
        self.last_updated: Dict[str, datetime] = {}
        self.ttl: Dict[str, timedelta] = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.RLock()
    
    def _get_cache_key(self, symbol: str, data_type: DataType, frequency: DataFrequency) -> str:
        """生成缓存键"""
        return f"{symbol}_{data_type.value}_{frequency.value}"
    
    def is_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        with self._lock:
            if cache_key not in self.data:
                return False
            
            last_update = self.last_updated.get(cache_key)
            if not last_update:
                return False
            
            ttl = self.ttl.get(cache_key, self.default_ttl)
            return datetime.now() - last_update < ttl
    
    def get(self, symbol: str, data_type: DataType, frequency: DataFrequency) -> Optional[List[MarketData]]:
        """获取缓存数据"""
        cache_key = self._get_cache_key(symbol, data_type, frequency)
        
        with self._lock:
            if self.is_valid(cache_key):
                self.hit_count += 1
                return self.data[cache_key].copy()
            else:
                self.miss_count += 1
                return None
    
    def set(self, symbol: str, data_type: DataType, frequency: DataFrequency, 
            data: List[MarketData], ttl: Optional[timedelta] = None):
        """设置缓存数据"""
        cache_key = self._get_cache_key(symbol, data_type, frequency)
        
        with self._lock:
            self.data[cache_key] = data.copy()
            self.last_updated[cache_key] = datetime.now()
            if ttl:
                self.ttl[cache_key] = ttl
    
    def invalidate(self, symbol: str, data_type: DataType, frequency: DataFrequency):
        """清除缓存"""
        cache_key = self._get_cache_key(symbol, data_type, frequency)
        
        with self._lock:
            self.data.pop(cache_key, None)
            self.last_updated.pop(cache_key, None)
            self.ttl.pop(cache_key, None)
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self.data.clear()
            self.last_updated.clear()
            self.ttl.clear()
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            return {
                'cached_keys': len(self.data),
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': self.hit_rate,
                'total_entries': sum(len(data) for data in self.data.values())
            }


class SubscriptionManager:
    """数据订阅管理器"""
    
    def __init__(self, update_interval: float = 1.0):
        self.subscriptions: Dict[str, DataSubscription] = {}
        self.data_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.update_interval = update_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def subscribe(self, symbol: str, data_type: DataType, frequency: DataFrequency,
                 source: str, callback: Optional[Callable[[MarketData], None]] = None) -> str:
        """订阅数据流"""
        subscription = DataSubscription(
            symbol=symbol,
            data_type=data_type,
            frequency=frequency,
            source=source,
            callback=callback
        )
        
        sub_id = subscription.subscription_id
        self.subscriptions[sub_id] = subscription
        self.logger.info(f"Subscribed to {sub_id}")
        
        return sub_id
    
    def unsubscribe(self, subscription_id: str):
        """取消订阅"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            self.logger.info(f"Unsubscribed from {subscription_id}")
    
    def start(self):
        """启动订阅服务"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Subscription manager started")
    
    def stop(self):
        """停止订阅服务"""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        self.logger.info("Subscription manager stopped")
    
    def _worker_loop(self):
        """工作线程循环"""
        while self.running:
            try:
                # 处理所有活跃订阅
                for sub_id, subscription in list(self.subscriptions.items()):
                    if not subscription.active:
                        continue
                    
                    # 检查是否需要更新
                    if self._should_update(subscription):
                        self.data_queue.put(('update', sub_id, subscription))
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Subscription manager error: {e}")
                time.sleep(5)
    
    def _should_update(self, subscription: DataSubscription) -> bool:
        """检查是否需要更新数据"""
        if not subscription.last_update:
            return True
        
        now = datetime.now()
        time_diff = now - subscription.last_update
        min_interval = self._get_min_update_interval(subscription.frequency)
        
        return time_diff >= min_interval
    
    def _get_min_update_interval(self, frequency: DataFrequency) -> timedelta:
        """获取最小更新间隔"""
        intervals = {
            DataFrequency.TICK: timedelta(seconds=0.1),
            DataFrequency.SECOND_1: timedelta(seconds=1),
            DataFrequency.MINUTE_1: timedelta(minutes=1),
            DataFrequency.MINUTE_5: timedelta(minutes=5),
            DataFrequency.MINUTE_15: timedelta(minutes=15),
            DataFrequency.MINUTE_30: timedelta(minutes=30),
            DataFrequency.HOUR_1: timedelta(hours=1),
            DataFrequency.HOUR_4: timedelta(hours=4),
            DataFrequency.DAY_1: timedelta(hours=6),  # 日线数据6小时更新一次
            DataFrequency.WEEK_1: timedelta(days=1),
            DataFrequency.MONTH_1: timedelta(days=7)
        }
        return intervals.get(frequency, timedelta(minutes=5))


class UnifiedDataManager:
    """统一数据管理器
    
    整合高性能实时数据流和多源数据集成的核心管理器
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 核心组件
        self.data_sources: Dict[str, BaseDataSource] = {}
        self.websocket_sources: Dict[str, WebSocketDataSource] = {}
        self.cache = DataCache()
        self.subscription_manager = SubscriptionManager()
        self.quality_monitors: Dict[str, DataQualityMonitor] = {}
        
        # 执行器和线程管理
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.websocket_loop = None
        self.websocket_thread = None
        
        # 性能监控
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.start_time = datetime.now()
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def register_data_source(self, name: str, source: BaseDataSource):
        """注册数据源"""
        self.data_sources[name] = source
        
        if isinstance(source, WebSocketDataSource):
            self.websocket_sources[name] = source
        
        # 创建质量监控器
        self.quality_monitors[name] = DataQualityMonitor()
        
        self.logger.info(f"Registered data source: {name} ({type(source).__name__})")
    
    def get_available_sources(self, data_type: DataType) -> List[str]:
        """获取支持指定数据类型的数据源"""
        sources = []
        for name, source in self.data_sources.items():
            if source.supports_data_type(data_type):
                sources.append(name)
        return sources
    
    def get_default_source(self, data_type: DataType) -> Optional[str]:
        """获取默认数据源"""
        sources = self.get_available_sources(data_type)
        if not sources:
            return None
        
        # 优先选择WebSocket源
        for source_name in sources:
            if source_name in self.websocket_sources:
                return source_name
        
        # 否则返回第一个可用源
        return sources[0]
    
    async def get_real_time_data(self, symbol: str, data_type: DataType, 
                                source: Optional[str] = None) -> Optional[MarketData]:
        """获取实时数据"""
        if not source:
            source = self.get_default_source(data_type)
        
        if not source or source not in self.data_sources:
            raise DataSourceError(f"No available source for {data_type.value}")
        
        try:
            start_time = time.time()
            data_source = self.data_sources[source]
            
            # 获取原始数据
            raw_data = data_source.get_real_time_price(symbol)
            
            if not raw_data:
                return None
            
            # 计算延迟
            latency_ms = (time.time() - start_time) * 1000
            
            # 转换为统一格式
            market_data = self._convert_to_market_data(
                symbol, data_type, raw_data, source, latency_ms
            )
            
            # 更新质量监控
            if source in self.quality_monitors:
                self.quality_monitors[source].add_data_point(market_data)
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time data for {symbol}: {e}")
            if source in self.quality_monitors:
                self.quality_monitors[source].add_error()
            return None
    
    async def get_historical_data(self, symbol: str, data_type: DataType,
                                 frequency: DataFrequency = DataFrequency.DAY_1,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 source: Optional[str] = None,
                                 use_cache: bool = True) -> List[MarketData]:
        """获取历史数据"""
        # 检查缓存
        if use_cache:
            cached_data = self.cache.get(symbol, data_type, frequency)
            if cached_data:
                self.logger.debug(f"Cache hit for {symbol} {data_type.value} {frequency.value}")
                return cached_data
        
        if not source:
            source = self.get_default_source(data_type)
        
        if not source or source not in self.data_sources:
            raise DataSourceError(f"No available source for {data_type.value}")
        
        try:
            data_source = self.data_sources[source]
            data = data_source.get_historical_data(symbol, frequency, start_date, end_date)
            
            # 设置数据源信息
            for item in data:
                item.source = source
            
            # 缓存数据
            if use_cache and data:
                self.cache.set(symbol, data_type, frequency, data)
            
            self.logger.info(f"Retrieved {len(data)} data points for {symbol} from {source}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            if source in self.quality_monitors:
                self.quality_monitors[source].add_error()
            return []
    
    def subscribe_to_stream(self, symbol: str, data_type: DataType, 
                          frequency: DataFrequency, callback: Callable[[MarketData], None],
                          source: Optional[str] = None) -> str:
        """订阅数据流"""
        if not source:
            source = self.get_default_source(data_type)
        
        if not source:
            raise DataSourceError(f"No available source for {data_type.value}")
        
        return self.subscription_manager.subscribe(
            symbol, data_type, frequency, source, callback
        )
    
    def unsubscribe_from_stream(self, subscription_id: str):
        """取消数据订阅"""
        self.subscription_manager.unsubscribe(subscription_id)
    
    def start_streams(self):
        """启动数据流"""
        self.subscription_manager.start()
        
        # 启动WebSocket连接
        if self.websocket_sources:
            self._start_websocket_loop()
        
        self.logger.info("Data streams started")
    
    def stop_streams(self):
        """停止数据流"""
        self.subscription_manager.stop()
        
        # 停止WebSocket连接
        if self.websocket_loop:
            self._stop_websocket_loop()
        
        self.logger.info("Data streams stopped")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        report = {
            'timestamp': datetime.now(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'data_sources': {},
            'cache_stats': self.cache.get_stats(),
            'subscriptions': len(self.subscription_manager.subscriptions)
        }
        
        # 数据源性能
        for name, monitor in self.quality_monitors.items():
            report['data_sources'][name] = {
                'avg_latency_ms': monitor.avg_latency_ms,
                'max_latency_ms': monitor.max_latency_ms,
                'success_rate': monitor.success_rate,
                'quality_score': monitor.quality_score,
                'total_requests': monitor.total_count,
                'error_count': monitor.error_count
            }
        
        return report
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            'timestamp': datetime.now(),
            'overall_status': 'healthy',
            'data_sources': {},
            'cache_status': self.cache.get_stats(),
            'subscriptions': len(self.subscription_manager.subscriptions),
            'websocket_connections': len(self.websocket_sources)
        }
        
        # 检查每个数据源
        for name, source in self.data_sources.items():
            try:
                symbols = source.get_supported_symbols()
                monitor = self.quality_monitors.get(name)
                
                source_status = {
                    'status': 'healthy',
                    'type': source.source_type.value,
                    'supported_symbols': len(symbols)
                }
                
                if monitor:
                    source_status.update({
                        'quality_score': monitor.quality_score,
                        'success_rate': monitor.success_rate
                    })
                    
                    # 判断状态
                    if monitor.quality_score < 70:
                        source_status['status'] = 'degraded'
                        status['overall_status'] = 'degraded'
                    elif monitor.success_rate < 0.8:
                        source_status['status'] = 'error'
                        status['overall_status'] = 'degraded'
                
                status['data_sources'][name] = source_status
                
            except Exception as e:
                status['data_sources'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                status['overall_status'] = 'degraded'
        
        return status
    
    def _convert_to_market_data(self, symbol: str, data_type: DataType, 
                               raw_data: Dict[str, Any], source: str, 
                               latency_ms: float) -> MarketData:
        """转换原始数据为MarketData格式"""
        timestamp = datetime.now()
        
        # 根据数据类型创建相应的数据对象
        if data_type == DataType.STOCK_PRICE:
            return StockData(
                symbol=symbol,
                timestamp=timestamp,
                data_type=data_type,
                frequency=DataFrequency.TICK,
                price=raw_data.get('price'),
                open=raw_data.get('open'),
                high=raw_data.get('high'),
                low=raw_data.get('low'),
                close=raw_data.get('close'),
                volume=raw_data.get('volume'),
                bid=raw_data.get('bid'),
                ask=raw_data.get('ask'),
                latency_ms=latency_ms,
                source=source,
                extra_data=raw_data
            )
        elif data_type == DataType.CRYPTO_PRICE:
            return CryptoData(
                symbol=symbol,
                timestamp=timestamp,
                data_type=data_type,
                frequency=DataFrequency.TICK,
                price=raw_data.get('price'),
                volume=raw_data.get('volume'),
                latency_ms=latency_ms,
                source=source,
                market_cap=raw_data.get('market_cap'),
                volume_24h=raw_data.get('volume_24h'),
                change_24h=raw_data.get('change_24h'),
                extra_data=raw_data
            )
        else:
            return MarketData(
                symbol=symbol,
                timestamp=timestamp,
                data_type=data_type,
                frequency=DataFrequency.TICK,
                price=raw_data.get('price'),
                volume=raw_data.get('volume'),
                latency_ms=latency_ms,
                source=source,
                extra_data=raw_data
            )
    
    def _start_websocket_loop(self):
        """启动WebSocket事件循环"""
        if self.websocket_thread and self.websocket_thread.is_alive():
            return
        
        self.websocket_thread = threading.Thread(
            target=self._run_websocket_loop, daemon=True
        )
        self.websocket_thread.start()
    
    def _run_websocket_loop(self):
        """运行WebSocket事件循环"""
        try:
            self.websocket_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.websocket_loop)
            
            # 连接所有WebSocket源
            tasks = []
            for source in self.websocket_sources.values():
                tasks.append(source.connect())
            
            if tasks:
                self.websocket_loop.run_until_complete(asyncio.gather(*tasks))
                
        except Exception as e:
            self.logger.error(f"WebSocket loop error: {e}")
        finally:
            if self.websocket_loop:
                self.websocket_loop.close()
    
    def _stop_websocket_loop(self):
        """停止WebSocket事件循环"""
        if self.websocket_loop:
            # 断开所有WebSocket连接
            for source in self.websocket_sources.values():
                asyncio.run_coroutine_threadsafe(
                    source.disconnect(), self.websocket_loop
                )
            
            # 停止事件循环
            self.websocket_loop.call_soon_threadsafe(self.websocket_loop.stop)
            
        if self.websocket_thread and self.websocket_thread.is_alive():
            self.websocket_thread.join(timeout=5)


# 导出
__all__ = [
    'PerformanceMetrics', 'DataSubscription', 'DataQualityMonitor',
    'DataCache', 'SubscriptionManager', 'UnifiedDataManager'
]