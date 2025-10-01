"""
实时数据流引擎 - Real-time Data Stream Engine

高性能实时数据处理引擎，支持：
- 毫秒级数据获取和处理
- WebSocket实时连接
- 数据缓冲队列和分片处理
- 并发和异步处理
- 数据清洗和验证

性能目标：
- 数据延迟 < 10ms
- 支持1000+ TPS (Transactions Per Second)
- 内存使用 < 500MB
- CPU使用率 < 30%
"""

import asyncio
import websockets
import json
import random
import time
import threading
import queue
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import concurrent.futures
import weakref

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """市场数据结构"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: float = 0.0
    ask: float = 0.0
    bid_size: int = 0
    ask_size: int = 0
    last_trade_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat(),
            'bid': self.bid,
            'ask': self.ask,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size
        }

@dataclass
class DataStreamConfig:
    """数据流配置"""
    buffer_size: int = 10000
    batch_size: int = 100
    max_workers: int = 4
    cleanup_interval: int = 60  # 秒
    websocket_timeout: int = 30
    retry_attempts: int = 3
    data_sources: List[str] = field(default_factory=lambda: ['yahoo', 'polygon'])

class DataBuffer:
    """高性能数据缓冲区"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.RLock()
        self._subscribers = weakref.WeakSet()
        
    def append(self, data: MarketData):
        """添加数据"""
        with self.lock:
            self.buffer.append(data)
            # 通知订阅者
            self._notify_subscribers(data)
    
    def get_latest(self, count: int = 1) -> List[MarketData]:
        """获取最新数据"""
        with self.lock:
            if count == 1:
                return [self.buffer[-1]] if self.buffer else []
            return list(self.buffer)[-count:] if len(self.buffer) >= count else list(self.buffer)
    
    def get_by_symbol(self, symbol: str, count: int = 100) -> List[MarketData]:
        """按股票代码获取数据"""
        with self.lock:
            result = [data for data in self.buffer if data.symbol == symbol]
            return result[-count:] if len(result) >= count else result
    
    def subscribe(self, callback: Callable[[MarketData], None]):
        """订阅数据更新"""
        self._subscribers.add(callback)
    
    def _notify_subscribers(self, data: MarketData):
        """通知订阅者"""
        for callback in list(self._subscribers):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"订阅者回调错误: {e}")

class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_market_data(data: Dict[str, Any]) -> bool:
        """验证市场数据"""
        required_fields = ['symbol', 'price', 'volume', 'timestamp']
        
        # 检查必需字段
        for field in required_fields:
            if field not in data:
                return False
        
        # 检查数据类型和范围
        try:
            price = float(data['price'])
            volume = int(data['volume'])
            
            if price <= 0 or volume < 0:
                return False
                
            # 检查时间戳
            if isinstance(data['timestamp'], str):
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def clean_data(data: Dict[str, Any]) -> Optional[MarketData]:
        """清洗和转换数据"""
        if not DataValidator.validate_market_data(data):
            return None
        
        try:
            timestamp = data['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            return MarketData(
                symbol=data['symbol'].upper(),
                price=float(data['price']),
                volume=int(data['volume']),
                timestamp=timestamp,
                bid=float(data.get('bid', 0)),
                ask=float(data.get('ask', 0)),
                bid_size=int(data.get('bid_size', 0)),
                ask_size=int(data.get('ask_size', 0))
            )
        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            return None

class WebSocketDataFeed:
    """WebSocket数据源"""
    
    def __init__(self, url: str, symbols: List[str]):
        self.url = url
        self.symbols = symbols
        self.websocket = None
        self.is_connected = False
        self.callbacks = []
        
    async def connect(self):
        """连接WebSocket"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.is_connected = True
            logger.info(f"WebSocket连接成功: {self.url}")
            
            # 订阅股票数据
            await self._subscribe_symbols()
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            self.is_connected = False
    
    async def _subscribe_symbols(self):
        """订阅股票代码"""
        subscribe_msg = {
            "action": "subscribe",
            "symbols": self.symbols
        }
        await self.websocket.send(json.dumps(subscribe_msg))
        logger.info(f"已订阅股票: {self.symbols}")
    
    async def listen(self):
        """监听数据"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._process_message(data)
        except Exception as e:
            logger.error(f"WebSocket监听错误: {e}")
            self.is_connected = False
    
    async def _process_message(self, data: Dict[str, Any]):
        """处理接收到的消息"""
        # 清洗数据
        market_data = DataValidator.clean_data(data)
        if market_data:
            # 通知回调函数
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(market_data)
                    else:
                        callback(market_data)
                except Exception as e:
                    logger.error(f"回调处理错误: {e}")
    
    def add_callback(self, callback: Callable[[MarketData], None]):
        """添加数据回调"""
        self.callbacks.append(callback)
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False

class PolygonDataFeed:
    """Polygon.io数据源 (模拟实现)"""
    
    def __init__(self, api_key: str, symbols: List[str]):
        self.api_key = api_key
        self.symbols = symbols
        self.is_running = False
        self.callbacks = []
        
        # 初始化价格和趋势状态
        self.base_prices = {
            'AAPL': 150.0,
            'MSFT': 300.0, 
            'GOOGL': 2500.0,
            'TSLA': 250.0,
            'AMZN': 3200.0
        }
        # 趋势状态: -1下跌, 1上涨
        self.trends = {symbol: random.choice([-1, 1]) for symbol in symbols}
        self.trend_duration = {symbol: 0 for symbol in symbols}
        self.momentum = {symbol: 1.0 for symbol in symbols}
        
    async def start(self):
        """开始数据流"""
        self.is_running = True
        logger.info("Polygon数据源已启动")
        
        # 模拟数据生成
        while self.is_running:
            for symbol in self.symbols:
                # 生成真实的价格波动
                mock_data = self._generate_realistic_data(symbol)
                
                for callback in self.callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(mock_data)
                        else:
                            callback(mock_data)
                    except Exception as e:
                        logger.error(f"Polygon回调错误: {e}")
            
            await asyncio.sleep(0.1)  # 100ms间隔
    
    def _generate_realistic_data(self, symbol: str) -> MarketData:
        """生成更真实的模拟数据"""
        import random
        
        # 获取当前价格，如果没有则使用默认值
        if symbol not in self.base_prices:
            self.base_prices[symbol] = 100.0
            self.trends[symbol] = random.choice([-1, 1])
            self.trend_duration[symbol] = 0
            self.momentum[symbol] = 1.0
        
        current_trend = self.trends[symbol]
        current_momentum = self.momentum[symbol]
        
        # 更真实的价格变化模型
        # 1. 基础波动：0.1% - 1.5%
        base_volatility = random.uniform(0.001, 0.015)
        
        # 2. 趋势影响：有方向性的变化
        trend_strength = random.uniform(0.3, 1.0)
        trend_effect = current_trend * base_volatility * trend_strength * current_momentum
        
        # 3. 随机噪音：±0.3%
        noise = random.uniform(-0.003, 0.003)
        
        # 4. 偶发的大波动（5%概率）
        shock_effect = 0
        if random.random() < 0.05:
            shock_effect = random.uniform(-0.02, 0.02)  # ±2%的突发波动
        
        # 总价格变化
        total_change = trend_effect + noise + shock_effect
        
        # 更新价格
        self.base_prices[symbol] *= (1 + total_change)
        
        # 更新趋势逻辑
        self.trend_duration[symbol] += 1
        
        # 趋势反转逻辑：每20-50次迭代检查一次
        if self.trend_duration[symbol] > random.randint(20, 50):
            # 25%概率反转趋势
            if random.random() < 0.25:
                self.trends[symbol] *= -1
                self.momentum[symbol] = random.uniform(0.6, 1.4)
                self.trend_duration[symbol] = 0
                logger.debug(f"{symbol} 趋势反转: {'上涨' if self.trends[symbol] > 0 else '下跌'}")
        
        # 动量衰减
        if self.trend_duration[symbol] > 15:
            self.momentum[symbol] *= 0.995  # 缓慢衰减
        
        current_price = self.base_prices[symbol]
        spread = current_price * 0.0001  # 0.01% spread
        
        return MarketData(
            symbol=symbol,
            price=current_price,
            volume=random.randint(1000, 10000),
            timestamp=datetime.now(),
            bid=current_price - spread,
            ask=current_price + spread,
            bid_size=random.randint(100, 1000),
            ask_size=random.randint(100, 1000),
            metadata={
                'trend': current_trend,
                'momentum': current_momentum,
                'change_pct': total_change * 100,
                'duration': self.trend_duration[symbol]
            }
        )
    
    def add_callback(self, callback: Callable[[MarketData], None]):
        """添加数据回调"""
        self.callbacks.append(callback)
    
    def stop(self):
        """停止数据流"""
        self.is_running = False

class RealtimeDataEngine:
    """实时数据流引擎"""
    
    def __init__(self, config: DataStreamConfig = None):
        self.config = config or DataStreamConfig()
        self.data_buffer = DataBuffer(self.config.buffer_size)
        self.data_feeds = {}
        self.is_running = False
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_workers
        )
        self.event_loop = None
        self.performance_stats = {
            'messages_processed': 0,
            'errors': 0,
            'avg_latency': 0,
            'start_time': None
        }
        
    async def add_data_feed(self, name: str, feed):
        """添加数据源"""
        self.data_feeds[name] = feed
        feed.add_callback(self._on_data_received)
        logger.info(f"数据源已添加: {name}")
    
    def _on_data_received(self, data: MarketData):
        """数据接收回调"""
        start_time = time.perf_counter()
        
        # 添加到缓冲区
        self.data_buffer.append(data)
        
        # 更新性能统计
        self._update_performance_stats(start_time)
        
        logger.debug(f"数据已处理: {data.symbol} @ {data.price}")
    
    def _update_performance_stats(self, start_time: float):
        """更新性能统计"""
        latency = (time.perf_counter() - start_time) * 1000  # 转换为毫秒
        
        self.performance_stats['messages_processed'] += 1
        
        # 计算平均延迟
        current_avg = self.performance_stats['avg_latency']
        count = self.performance_stats['messages_processed']
        self.performance_stats['avg_latency'] = (current_avg * (count - 1) + latency) / count
    
    async def start(self, symbols: List[str]):
        """启动数据引擎"""
        self.is_running = True
        self.performance_stats['start_time'] = datetime.now()
        logger.info("实时数据引擎启动中...")
        
        # 初始化数据源
        await self._initialize_data_feeds(symbols)
        
        # 启动数据源
        tasks = []
        for name, feed in self.data_feeds.items():
            if hasattr(feed, 'connect'):
                await feed.connect()
                if hasattr(feed, 'listen'):
                    tasks.append(asyncio.create_task(feed.listen()))
            elif hasattr(feed, 'start'):
                tasks.append(asyncio.create_task(feed.start()))
        
        logger.info("实时数据引擎已启动")
        
        # 等待所有任务完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _initialize_data_feeds(self, symbols: List[str]):
        """初始化数据源"""
        # Polygon数据源 (模拟)
        polygon_feed = PolygonDataFeed("mock_api_key", symbols)
        await self.add_data_feed("polygon", polygon_feed)
        
        # 可以添加更多数据源
        # yahoo_feed = YahooDataFeed(symbols)
        # await self.add_data_feed("yahoo", yahoo_feed)
    
    def subscribe_to_data(self, callback: Callable[[MarketData], None]):
        """订阅数据更新"""
        self.data_buffer.subscribe(callback)
    
    def get_latest_data(self, symbol: str, count: int = 1) -> List[MarketData]:
        """获取最新数据"""
        return self.data_buffer.get_by_symbol(symbol, count)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if self.performance_stats['start_time']:
            runtime = (datetime.now() - self.performance_stats['start_time']).total_seconds()
            tps = self.performance_stats['messages_processed'] / runtime if runtime > 0 else 0
            
            return {
                **self.performance_stats,
                'runtime_seconds': runtime,
                'tps': tps,
                'latency_ms': self.performance_stats['avg_latency']
            }
        return self.performance_stats
    
    async def stop(self):
        """停止数据引擎"""
        self.is_running = False
        logger.info("正在停止数据引擎...")
        
        # 停止所有数据源
        for name, feed in self.data_feeds.items():
            try:
                if hasattr(feed, 'disconnect'):
                    await feed.disconnect()
                elif hasattr(feed, 'stop'):
                    feed.stop()
            except Exception as e:
                logger.error(f"停止数据源失败 {name}: {e}")
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("实时数据引擎已停止")

# 使用示例和测试
async def main():
    """主函数 - 测试实时数据引擎"""
    
    # 创建配置
    config = DataStreamConfig(
        buffer_size=5000,
        batch_size=50,
        max_workers=2
    )
    
    # 创建数据引擎
    engine = RealtimeDataEngine(config)
    
    # 订阅数据更新
    def on_data_update(data: MarketData):
        print(f"📊 {data.symbol}: ${data.price:.2f} | 成交量: {data.volume} | 时间: {data.timestamp.strftime('%H:%M:%S.%f')[:-3]}")
    
    engine.subscribe_to_data(on_data_update)
    
    # 启动引擎
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    try:
        print("🚀 启动实时数据引擎...")
        
        # 运行5秒后停止
        engine_task = asyncio.create_task(engine.start(symbols))
        
        await asyncio.sleep(5)
        
        # 显示性能统计
        stats = engine.get_performance_stats()
        print(f"\n📈 性能统计:")
        print(f"  处理消息数: {stats['messages_processed']}")
        print(f"  平均延迟: {stats['latency_ms']:.2f}ms")
        print(f"  TPS: {stats.get('tps', 0):.1f}")
        print(f"  运行时间: {stats.get('runtime_seconds', 0):.1f}秒")
        
        # 停止引擎
        await engine.stop()
        
    except KeyboardInterrupt:
        print("\n⏹️ 手动停止")
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())