"""
Backtrader 集成接口

将统一数据源与Backtrader框架无缝集成，
保持现有策略的兼容性。
"""

import backtrader as bt
import asyncio
import threading
import queue
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

from .unified_manager import UnifiedDataManager
from .adapters import create_unified_data_sources
from . import DataType, DataFrequency, MarketData


class UnifiedBacktraderFeed(bt.feeds.DataBase):
    """统一Backtrader数据源
    
    集成高性能实时数据和多源数据访问能力
    """
    
    params = (
        ('symbol', 'AAPL'),                    # 股票代码
        ('data_type', 'stock'),                # 数据类型: stock, crypto, economic
        ('frequency', '1d'),                   # 数据频率
        ('update_interval_ms', 1000),          # 更新间隔(毫秒)
        ('buffer_size', 10000),                # 数据缓冲区大小
        ('use_cache', True),                   # 是否使用缓存
        ('data_source', None),                 # 指定数据源
        ('config', None),                      # 数据源配置
    )
    
    def __init__(self):
        """初始化统一数据源"""
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 数据缓冲区
        self.data_queue = queue.Queue(maxsize=self.p.buffer_size)
        
        # 统一数据管理器
        self.data_manager = None
        self.subscription_id = None
        
        # 运行状态
        self.running = False
        self.data_thread = None
        
        # 性能监控
        self.data_count = 0
        self.start_time = None
        self.last_data_time = None
        
        # 转换参数
        self.data_type = self._parse_data_type(self.p.data_type)
        self.frequency = self._parse_frequency(self.p.frequency)
    
    def start(self):
        """启动数据源"""
        if self.running:
            return
        
        self.running = True
        self.start_time = time.time()
        
        self.logger.info(f"Starting unified data feed for {self.p.symbol}")
        
        try:
            # 初始化数据管理器
            self._initialize_data_manager()
            
            # 启动数据流
            self.data_manager.start_streams()
            
            # 订阅数据
            self.subscription_id = self.data_manager.subscribe_to_stream(
                symbol=self.p.symbol,
                data_type=self.data_type,
                frequency=self.frequency,
                callback=self._on_market_data,
                source=self.p.data_source
            )
            
            # 启动数据处理线程
            self.data_thread = threading.Thread(target=self._data_worker, daemon=True)
            self.data_thread.start()
            
            self.logger.info(f"Data feed started for {self.p.symbol}")
            
        except Exception as e:
            self.logger.error(f"Failed to start data feed: {e}")
            self.running = False
            raise
    
    def stop(self):
        """停止数据源"""
        if not self.running:
            return
        
        self.logger.info(f"Stopping data feed for {self.p.symbol}")
        self.running = False
        
        try:
            # 取消订阅
            if self.subscription_id and self.data_manager:
                self.data_manager.unsubscribe_from_stream(self.subscription_id)
            
            # 停止数据流
            if self.data_manager:
                self.data_manager.stop_streams()
            
            # 等待数据处理线程结束
            if self.data_thread and self.data_thread.is_alive():
                self.data_thread.join(timeout=5)
            
            # 打印性能统计
            self._print_performance_stats()
            
        except Exception as e:
            self.logger.error(f"Error stopping data feed: {e}")
    
    def _initialize_data_manager(self):
        """初始化数据管理器"""
        config = self.p.config or {}
        
        # 创建数据管理器
        self.data_manager = UnifiedDataManager(config)
        
        # 注册数据源
        data_sources = create_unified_data_sources(config)
        for name, source in data_sources.items():
            self.data_manager.register_data_source(name, source)
        
        self.logger.info(f"Initialized data manager with {len(data_sources)} sources")
    
    def _on_market_data(self, market_data: MarketData):
        """处理市场数据回调"""
        try:
            # 更新统计
            self.data_count += 1
            self.last_data_time = time.time()
            
            # 转换为Backtrader数据格式
            bt_data = self._convert_to_bt_format(market_data)
            
            # 添加到队列
            try:
                self.data_queue.put_nowait(bt_data)
            except queue.Full:
                # 队列满了，移除最老的数据
                try:
                    self.data_queue.get_nowait()
                    self.data_queue.put_nowait(bt_data)
                except queue.Empty:
                    pass
                
        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")
    
    def _convert_to_bt_format(self, market_data: MarketData) -> Dict[str, Any]:
        """转换MarketData为Backtrader格式"""
        # 使用close价格作为主要价格，如果没有则使用price
        price = market_data.close or market_data.price or 0.0
        
        return {
            'datetime': market_data.timestamp,
            'open': market_data.open or price,
            'high': market_data.high or price,
            'low': market_data.low or price,
            'close': price,
            'volume': market_data.volume or 0,
            'openinterest': 0,
            # 额外信息
            'latency_ms': market_data.latency_ms,
            'source': market_data.source,
            'data_type': market_data.data_type.value
        }
    
    def _data_worker(self):
        """数据处理工作线程"""
        self.logger.info("Data worker thread started")
        
        while self.running:
            try:
                # 检查是否有待处理的数据
                if not self.data_queue.empty():
                    # 让Backtrader处理数据
                    continue
                
                time.sleep(0.001)  # 1ms间隔
                
            except Exception as e:
                self.logger.error(f"Data worker error: {e}")
                time.sleep(1)
        
        self.logger.info("Data worker thread stopped")
    
    def _load(self):
        """Backtrader数据加载接口"""
        if not self.running:
            return False
        
        try:
            # 从队列获取数据
            data_point = self.data_queue.get_nowait()
            
            # 设置Backtrader数据线
            self.lines.datetime[0] = bt.date2num(data_point['datetime'])
            self.lines.open[0] = data_point['open']
            self.lines.high[0] = data_point['high']
            self.lines.low[0] = data_point['low']
            self.lines.close[0] = data_point['close']
            self.lines.volume[0] = data_point['volume']
            self.lines.openinterest[0] = data_point['openinterest']
            
            return True
            
        except queue.Empty:
            return False
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return False
    
    def _parse_data_type(self, data_type_str: str) -> DataType:
        """解析数据类型"""
        mapping = {
            'stock': DataType.STOCK_PRICE,
            'crypto': DataType.CRYPTO_PRICE,
            'economic': DataType.ECONOMIC_INDICATOR,
        }
        return mapping.get(data_type_str.lower(), DataType.STOCK_PRICE)
    
    def _parse_frequency(self, frequency_str: str) -> DataFrequency:
        """解析数据频率"""
        mapping = {
            'tick': DataFrequency.TICK,
            '1s': DataFrequency.SECOND_1,
            '1m': DataFrequency.MINUTE_1,
            '5m': DataFrequency.MINUTE_5,
            '15m': DataFrequency.MINUTE_15,
            '30m': DataFrequency.MINUTE_30,
            '1h': DataFrequency.HOUR_1,
            '4h': DataFrequency.HOUR_4,
            '1d': DataFrequency.DAY_1,
            '1w': DataFrequency.WEEK_1,
            '1M': DataFrequency.MONTH_1,
        }
        return mapping.get(frequency_str, DataFrequency.DAY_1)
    
    def _print_performance_stats(self):
        """打印性能统计"""
        if not self.start_time:
            return
        
        runtime = time.time() - self.start_time
        data_rate = self.data_count / runtime if runtime > 0 else 0
        
        self.logger.info(
            f"Performance Stats for {self.p.symbol}:\n"
            f"  - Total Data Points: {self.data_count}\n"
            f"  - Runtime: {runtime:.1f}s\n"
            f"  - Data Rate: {data_rate:.1f} points/sec\n"
            f"  - Queue Size: {self.data_queue.qsize()}"
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        current_time = time.time()
        runtime = current_time - self.start_time if self.start_time else 0
        data_rate = self.data_count / runtime if runtime > 0 else 0
        
        metrics = {
            'symbol': self.p.symbol,
            'data_type': self.p.data_type,
            'frequency': self.p.frequency,
            'data_count': self.data_count,
            'runtime_seconds': runtime,
            'data_rate_per_second': data_rate,
            'queue_size': self.data_queue.qsize(),
            'running': self.running
        }
        
        # 添加数据管理器的性能报告
        if self.data_manager:
            try:
                performance_report = self.data_manager.get_performance_report()
                metrics['data_sources'] = performance_report.get('data_sources', {})
                metrics['cache_stats'] = performance_report.get('cache_stats', {})
            except Exception as e:
                self.logger.error(f"Error getting performance report: {e}")
        
        return metrics


class MultiSymbolUnifiedFeed:
    """多符号统一数据源"""
    
    def __init__(self, symbols: List[str], config: Dict[str, Any] = None):
        self.symbols = symbols
        self.config = config or {}
        self.feeds = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_feeds(self, **feed_params) -> Dict[str, UnifiedBacktraderFeed]:
        """为每个符号创建数据源"""
        for symbol in self.symbols:
            feed = UnifiedBacktraderFeed()
            
            # 设置参数
            feed.p.symbol = symbol
            feed.p.config = self.config
            
            # 应用其他参数
            for key, value in feed_params.items():
                if hasattr(feed.p, key):
                    setattr(feed.p, key, value)
            
            self.feeds[symbol] = feed
        
        self.logger.info(f"Created feeds for {len(self.feeds)} symbols")
        return self.feeds
    
    def start_all(self):
        """启动所有数据源"""
        for symbol, feed in self.feeds.items():
            try:
                feed.start()
                self.logger.info(f"Started feed for {symbol}")
            except Exception as e:
                self.logger.error(f"Failed to start feed for {symbol}: {e}")
    
    def stop_all(self):
        """停止所有数据源"""
        for symbol, feed in self.feeds.items():
            try:
                feed.stop()
                self.logger.info(f"Stopped feed for {symbol}")
            except Exception as e:
                self.logger.error(f"Failed to stop feed for {symbol}: {e}")
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据源的性能指标"""
        metrics = {}
        for symbol, feed in self.feeds.items():
            try:
                metrics[symbol] = feed.get_performance_metrics()
            except Exception as e:
                self.logger.error(f"Failed to get metrics for {symbol}: {e}")
                metrics[symbol] = {'error': str(e)}
        
        return metrics


# 便捷函数
def create_unified_feed(symbol: str = 'AAPL', data_type: str = 'stock', 
                       frequency: str = '1d', **kwargs) -> UnifiedBacktraderFeed:
    """创建统一数据源的便捷函数"""
    feed = UnifiedBacktraderFeed()
    feed.p.symbol = symbol
    feed.p.data_type = data_type
    feed.p.frequency = frequency
    
    # 应用其他参数
    for key, value in kwargs.items():
        if hasattr(feed.p, key):
            setattr(feed.p, key, value)
    
    return feed


# 导出
__all__ = [
    'UnifiedBacktraderFeed', 'MultiSymbolUnifiedFeed', 'create_unified_feed'
]