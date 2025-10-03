"""
实时数据流集成模块 - Real-time Data Stream Integration

集成真实市场数据流引擎到主交易系统，提供：
- Yahoo Finance实时数据
- Alpha Vantage API集成
- 简化的数据流接口
- 策略数据订阅
- 性能监控
- 数据流管理
"""

import asyncio
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging

from .real_market_data_engine import RealMarketDataEngine, RealMarketData, DataSourceConfig

logger = logging.getLogger(__name__)

class DataStreamManager:
    """数据流管理器 - 真实市场数据接口"""
    
    def __init__(self):
        self.engine = None
        self.is_running = False
        self.loop = None
        self.thread = None
        self.subscribers = {}  # symbol -> [callbacks]
        
    def start_data_stream(self, symbols: List[str], config: DataSourceConfig = None):
        """启动真实数据流"""
        if self.is_running:
            logger.warning("数据流已在运行")
            return
        
        self.config = config or DataSourceConfig()
        
        # 在新线程中运行异步事件循环
        self.thread = threading.Thread(target=self._run_async_loop, args=(symbols,))
        self.thread.daemon = True
        self.thread.start()
        
        # 等待引擎启动
        import time
        time.sleep(2)  # 真实数据源需要更多启动时间
        
        logger.info(f"真实数据流已启动，订阅股票: {symbols}")
    
    def _run_async_loop(self, symbols: List[str]):
        """在独立线程中运行异步事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._start_engine(symbols))
        except Exception as e:
            logger.error(f"真实数据流引擎错误: {e}")
        finally:
            self.loop.close()
    
    async def _start_engine(self, symbols: List[str]):
        """启动真实数据引擎"""
        self.engine = RealMarketDataEngine(self.config)
        
        # 订阅数据更新
        self.engine.subscribe_to_data(self._on_data_received)
        
        self.is_running = True
        
        try:
            await self.engine.start(symbols)
        except Exception as e:
            logger.error(f"真实数据引擎启动失败: {e}")
        finally:
            self.is_running = False
    
    def _on_data_received(self, data: RealMarketData):
        """数据接收回调"""
        # 通知订阅者
        if data.symbol in self.subscribers:
            for callback in self.subscribers[data.symbol]:
                try:
                    # 转换为兼容的数据格式
                    callback({
                        'symbol': data.symbol,
                        'price': data.price,
                        'volume': data.volume,
                        'timestamp': data.timestamp,
                        'change_percent': data.change_percent,
                        'source': data.source,
                        'metadata': data.metadata
                    })
                except Exception as e:
                    logger.error(f"订阅者回调错误: {e}")
    
    def subscribe(self, symbol: str, callback: Callable[[Dict], None]):
        """订阅股票数据"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        
        self.subscribers[symbol].append(callback)
        logger.info(f"已订阅 {symbol} 真实数据更新")
    
    def unsubscribe(self, symbol: str, callback: Callable[[Dict], None]):
        """取消订阅"""
        if symbol in self.subscribers:
            try:
                self.subscribers[symbol].remove(callback)
                logger.info(f"已取消订阅 {symbol}")
            except ValueError:
                logger.warning(f"回调函数不在 {symbol} 订阅列表中")
    
    def stop(self):
        """停止数据流"""
        if self.is_running and self.engine:
            # 在数据引擎的事件循环中执行停止操作
            if self.loop and not self.loop.is_closed():
                asyncio.run_coroutine_threadsafe(self.engine.stop(), self.loop)
            
        self.is_running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("真实数据流已停止")
    
    def get_latest_data(self, symbol: str) -> Optional[Dict]:
        """获取最新数据"""
        if self.engine:
            return self.engine.get_latest_price(symbol)
        return None
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        if self.engine:
            return self.engine.get_performance_stats()
        return {
            'messages_processed': 0,
            'sources_active': 0,
            'runtime_seconds': 0,
            'messages_per_second': 0,
            'cached_symbols': 0
        }
    
    async def _start_engine(self, symbols: List[str]):
        """启动数据引擎"""
        self.engine = RealtimeDataEngine(self.config)
        
        # 订阅数据更新
        self.engine.subscribe_to_data(self._on_data_received)
        
        self.is_running = True
        
        try:
            await self.engine.start(symbols)
        except Exception as e:
            logger.error(f"数据引擎启动失败: {e}")
        finally:
            self.is_running = False
    
    def _on_data_received(self, data: MarketData):
        """数据接收回调"""
        # 通知订阅者
        if data.symbol in self.subscribers:
            for callback in self.subscribers[data.symbol]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"订阅者回调错误: {e}")
    
    def subscribe(self, symbol: str, callback: Callable[[MarketData], None]):
        """订阅股票数据"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        
        self.subscribers[symbol].append(callback)
        logger.info(f"已订阅 {symbol} 数据更新")
    
    def unsubscribe(self, symbol: str, callback: Callable[[MarketData], None]):
        """取消订阅"""
        if symbol in self.subscribers:
            try:
                self.subscribers[symbol].remove(callback)
                if not self.subscribers[symbol]:
                    del self.subscribers[symbol]
                logger.info(f"已取消订阅 {symbol}")
            except ValueError:
                pass
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """获取最新价格"""
        if not self.engine:
            return None
        
        latest_data = self.engine.get_latest_data(symbol, 1)
        return latest_data[0].price if latest_data else None
    
    def get_latest_data(self, symbol: str, count: int = 1) -> List[MarketData]:
        """获取最新数据"""
        if not self.engine:
            return []
        
        return self.engine.get_latest_data(symbol, count)
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        if not self.engine:
            return {}
        
        return self.engine.get_performance_stats()
    
    def stop(self):
        """停止数据流"""
        if not self.is_running:
            return
        
        if self.loop and self.engine:
            # 在异步循环中停止引擎
            future = asyncio.run_coroutine_threadsafe(
                self.engine.stop(), self.loop
            )
            try:
                future.result(timeout=5)
            except Exception as e:
                logger.error(f"停止数据引擎失败: {e}")
        
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("数据流已停止")

# 全局数据流管理器实例
_data_stream_manager = None

def get_data_stream_manager() -> DataStreamManager:
    """获取全局数据流管理器"""
    global _data_stream_manager
    if _data_stream_manager is None:
        _data_stream_manager = DataStreamManager()
    return _data_stream_manager

def start_realtime_data(symbols: List[str]) -> DataStreamManager:
    """启动实时数据流 - 便捷函数"""
    manager = get_data_stream_manager()
    manager.start_data_stream(symbols)
    return manager

def stop_realtime_data():
    """停止实时数据流 - 便捷函数"""
    global _data_stream_manager
    if _data_stream_manager:
        _data_stream_manager.stop()
        _data_stream_manager = None

def subscribe_to_symbol(symbol: str, callback: Callable[[MarketData], None]):
    """订阅股票数据 - 便捷函数"""
    manager = get_data_stream_manager()
    manager.subscribe(symbol, callback)

def get_latest_price(symbol: str) -> Optional[float]:
    """获取最新价格 - 便捷函数"""
    manager = get_data_stream_manager()
    return manager.get_latest_price(symbol)

# 使用示例
if __name__ == "__main__":
    # 测试数据流管理器
    def on_price_update(data: MarketData):
        print(f"📈 {data.symbol}: ${data.price:.2f}")
    
    # 启动数据流
    manager = start_realtime_data(['AAPL', 'MSFT'])
    
    # 订阅价格更新
    subscribe_to_symbol('AAPL', on_price_update)
    subscribe_to_symbol('MSFT', on_price_update)
    
    try:
        import time
        time.sleep(5)
        
        # 获取性能统计
        stats = manager.get_performance_stats()
        print(f"\n性能统计: {stats}")
        
    finally:
        stop_realtime_data()