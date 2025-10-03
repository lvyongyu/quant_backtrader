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
import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from real_market_data_engine import RealMarketDataEngine, RealMarketData, DataSourceConfig
except ImportError:
    # 如果直接导入失败，尝试相对导入
    try:
        from .real_market_data_engine import RealMarketDataEngine, RealMarketData, DataSourceConfig
    except ImportError as e:
        logging.error(f"无法导入real_market_data_engine: {e}")
        # 提供备用类定义
        class RealMarketDataEngine:
            def __init__(self, config=None): pass
            def start(self): pass
            def stop(self): pass
            def subscribe(self, symbol, callback): pass
        
        class RealMarketData:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class DataSourceConfig:
            def __init__(self): pass

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
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """获取最新价格（兼容方法）"""
        return self.get_latest_data(symbol)
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        if self.engine:
            stats = self.engine.get_performance_stats()
            # 转换为兼容格式
            return {
                'tps': stats.get('messages_per_second', 0),
                'latency_ms': 5000,  # 真实数据源延迟约5秒
                'messages_processed': stats.get('messages_processed', 0),
                'sources_active': stats.get('sources_active', 0),
                'cached_symbols': stats.get('cached_symbols', 0)
            }
        return {
            'tps': 0,
            'latency_ms': 0,
            'messages_processed': 0,
            'sources_active': 0,
            'cached_symbols': 0
        }

# 全局数据流管理器实例
_global_data_manager: Optional[DataStreamManager] = None

def get_data_stream_manager() -> DataStreamManager:
    """获取全局数据流管理器"""
    global _global_data_manager
    if _global_data_manager is None:
        _global_data_manager = DataStreamManager()
    return _global_data_manager

def start_realtime_data(symbols: List[str], config: DataSourceConfig = None) -> DataStreamManager:
    """启动真实数据流"""
    manager = get_data_stream_manager()
    manager.start_data_stream(symbols, config)
    return manager

def subscribe_to_symbol(symbol: str, callback: Callable[[Dict], None]):
    """订阅股票的真实数据更新"""
    manager = get_data_stream_manager()
    manager.subscribe(symbol, callback)

def stop_realtime_data():
    """停止真实数据流"""
    manager = get_data_stream_manager()
    manager.stop()

# 示例使用
def example_usage():
    """真实数据流使用示例"""
    print("🌟 真实数据流使用示例")
    
    def on_price_update(data: Dict):
        """价格更新回调"""
        print(f"📊 真实价格更新: {data['symbol']} @ ${data['price']:.2f} "
              f"({data.get('change_percent', 0):+.2f}%) 来源: {data.get('source', 'unknown')}")
    
    # 启动真实数据流
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    manager = start_realtime_data(symbols)
    
    # 订阅价格更新
    for symbol in symbols:
        subscribe_to_symbol(symbol, on_price_update)
    
    print(f"✅ 已启动真实数据监控: {symbols}")
    print("💡 这是Yahoo Finance等真实数据源，数据会有5-15秒延迟")
    
    import time
    try:
        # 运行30秒
        time.sleep(30)
        
        # 显示统计信息
        stats = manager.get_performance_stats()
        print(f"\n📈 真实数据统计:")
        print(f"  消息处理: {stats['messages_processed']}")
        print(f"  活跃数据源: {stats['sources_active']}")
        print(f"  缓存股票: {stats['cached_symbols']}")
        
    finally:
        stop_realtime_data()
        print("✅ 真实数据流已停止")

if __name__ == "__main__":
    example_usage()