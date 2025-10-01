#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据源引擎 - Real Market Data Engine

集成真实市场数据源：
- Yahoo Finance (yfinance) - 实时股价、历史数据

性能目标：
- 数据延迟 < 15秒（Yahoo Finance限制）
- 支持多股票并发获取
- 自动重试和错误处理
- 数据缓存和验证
"""

import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RealMarketData:
    """真实市场数据结构"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: float = 0.0
    ask: float = 0.0
    bid_size: int = 0
    ask_size: int = 0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    previous_close: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    source: str = "unknown"
    metadata: Dict[str, Any] = None

class DataSourceConfig:
    """数据源配置"""
    def __init__(self):
        # 更新频率配置
        self.update_interval = 10  # 秒，Yahoo Finance建议最少5秒间隔
        self.retry_attempts = 3
        self.timeout = 30
        
        # 数据源优先级
        self.source_priority = ['yfinance']

class YahooFinanceDataSource:
    """Yahoo Finance数据源 - 免费但有延迟"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.is_running = False
        self.callbacks = []
        self.last_prices = {}
        self.data_task = None  # 保存数据获取任务引用
        
    async def start(self):
        """启动Yahoo Finance数据获取"""
        self.is_running = True
        logger.info("Yahoo Finance数据源已启动")
        
        # 启动数据获取循环并保存任务引用
        self.data_task = asyncio.create_task(self._fetch_data_loop())
    
    async def _fetch_data_loop(self):
        """数据获取循环"""
        while self.is_running:
            try:
                # 检查事件循环状态
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        logger.warning("事件循环已关闭，停止数据获取循环")
                        break
                except RuntimeError:
                    logger.warning("无法获取事件循环，停止数据获取循环")
                    break
                
                await self._fetch_realtime_data()
                await asyncio.sleep(5)  # Yahoo Finance建议5秒间隔
            except asyncio.CancelledError:
                logger.info("数据获取循环被取消")
                break
            except Exception as e:
                logger.error(f"Yahoo Finance数据获取错误: {e}")
                await asyncio.sleep(10)  # 错误时等待更长时间
    
    async def _fetch_realtime_data(self):
        """获取实时数据 - 使用同步方式避免事件循环问题"""
        try:
            # 直接使用同步方式，避免复杂的事件循环管理
            tickers = yf.Tickers(' '.join(self.symbols))
            
            for symbol in self.symbols:
                if not self.is_running:  # 检查运行状态
                    break
                    
                try:
                    ticker = tickers.tickers[symbol]
                    
                    # 直接同步获取数据，避免executor问题
                    try:
                        info = ticker.info if hasattr(ticker, 'info') else None
                    except Exception:
                        info = None
                    
                    current_price = 0
                    volume = 0
                    open_price = 0
                    high_price = 0 
                    low_price = 0
                    
                    if not info:
                        # 如果info不可用，尝试使用history方法
                        try:
                            hist = ticker.history(period="1d", interval="1m").tail(1)
                            
                            if not hist.empty:
                                latest = hist.iloc[-1]
                                current_price = float(latest['Close'])
                                volume = int(latest['Volume'])
                                open_price = float(latest['Open'])
                                high_price = float(latest['High'])
                                low_price = float(latest['Low'])
                            else:
                                continue
                        except Exception as e:
                            logger.warning(f"获取{symbol}历史数据失败: {e}")
                            continue
                    else:
                        # 使用info数据
                        current_price = float(info.get('regularMarketPrice', 0) or 
                                            info.get('currentPrice', 0) or 
                                            info.get('previousClose', 0))
                        volume = int(info.get('regularMarketVolume', 0) or 0)
                        open_price = float(info.get('regularMarketOpen', 0) or 0)
                        high_price = float(info.get('regularMarketDayHigh', 0) or 0)
                        low_price = float(info.get('regularMarketDayLow', 0) or 0)
                    
                    # 检查价格变化
                    if symbol in self.last_prices:
                        previous_close = self.last_prices[symbol]
                        change = current_price - previous_close
                        change_percent = (change / previous_close * 100) if previous_close != 0 else 0
                    else:
                        previous_close = current_price
                        change = 0
                        change_percent = 0
                    
                    # 更新最后价格
                    self.last_prices[symbol] = current_price
                    
                    # 创建市场数据
                    market_data = RealMarketData(
                        symbol=symbol,
                        price=current_price,
                        volume=volume,
                        timestamp=datetime.now(),
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        previous_close=previous_close,
                        change=change,
                        change_percent=change_percent,
                        source="yahoo_finance",
                        metadata={
                            'market_cap': info.get('marketCap', 0) if info else 0,
                            'pe_ratio': info.get('trailingPE', 0) if info else 0,
                            'beta': info.get('beta', 0) if info else 0
                        }
                    )
                    
                    # 通知回调
                    for callback in self.callbacks:
                        try:
                            callback(market_data)
                        except Exception as e:
                            logger.error(f"Yahoo Finance回调错误: {e}")
                            
                except Exception as e:
                    logger.error(f"获取{symbol}数据失败: {e}")
                    continue
                        
        except Exception as e:
            logger.error(f"Yahoo Finance数据获取失败: {e}")
    
    def add_callback(self, callback: Callable[[RealMarketData], None]):
        """添加数据回调"""
        self.callbacks.append(callback)
    
    def stop(self):
        """停止数据源"""
        self.is_running = False
        
        # 取消数据获取任务
        if self.data_task and not self.data_task.done():
            self.data_task.cancel()
            
        logger.info("Yahoo Finance数据源已停止")

class RealMarketDataEngine:
    """真实市场数据引擎 - 只使用Yahoo Finance"""
    
    def __init__(self, config: DataSourceConfig = None):
        self.config = config or DataSourceConfig()
        self.data_sources = {}
        self.is_running = False
        self.callbacks = []
        self.data_cache = {}  # symbol -> latest_data
        self.performance_stats = {
            'messages_processed': 0,
            'sources_active': 0,
            'start_time': 0,
            'last_update': 0
        }
        
    async def add_data_source(self, name: str, source):
        """添加数据源"""
        self.data_sources[name] = source
        source.add_callback(self._on_data_received)
        logger.info(f"真实数据源已添加: {name}")
    
    def _on_data_received(self, data: RealMarketData):
        """数据接收回调"""
        # 缓存最新数据
        self.data_cache[data.symbol] = data
        
        # 更新性能统计
        self.performance_stats['messages_processed'] += 1
        self.performance_stats['last_update'] = time.time()
        
        logger.debug(f"真实数据已处理: {data.symbol} @ ${data.price:.2f} ({data.source})")
        
        # 通知回调
        for callback in self.callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"数据回调错误: {e}")
    
    async def start(self, symbols: List[str]):
        """启动数据引擎"""
        self.is_running = True
        self.performance_stats['start_time'] = time.time()
        logger.info("真实市场数据引擎启动中...")
        
        # 初始化数据源
        await self._initialize_data_sources(symbols)
        
        # 启动数据源
        tasks = []
        for name, source in self.data_sources.items():
            task = asyncio.create_task(source.start())
            tasks.append(task)
            
        self.performance_stats['sources_active'] = len(tasks)
        logger.info(f"✅ 真实数据引擎已启动，活跃数据源: {len(tasks)}")
        
        # 等待所有数据源
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"数据源运行错误: {e}")
    
    async def _initialize_data_sources(self, symbols: List[str]):
        """初始化数据源"""
        # 只使用Yahoo Finance数据源
        yahoo_source = YahooFinanceDataSource(symbols)
        await self.add_data_source("yahoo_finance", yahoo_source)
        
    def subscribe_to_data(self, callback: Callable[[RealMarketData], None]):
        """订阅数据更新"""
        self.callbacks.append(callback)
        
    def get_latest_price(self, symbol: str) -> Dict[str, Any]:
        """获取最新价格"""
        if symbol in self.data_cache:
            data = self.data_cache[symbol]
            return {
                'symbol': data.symbol,
                'price': data.price,
                'volume': data.volume,
                'timestamp': data.timestamp,
                'change_percent': data.change_percent,
                'source': data.source
            }
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        runtime = time.time() - self.performance_stats['start_time'] if self.performance_stats['start_time'] > 0 else 0
        
        return {
            'messages_processed': self.performance_stats['messages_processed'],
            'sources_active': self.performance_stats['sources_active'],
            'runtime_seconds': runtime,
            'messages_per_second': self.performance_stats['messages_processed'] / runtime if runtime > 0 else 0,
            'last_update_ago': time.time() - self.performance_stats['last_update'] if self.performance_stats['last_update'] > 0 else 0,
            'cached_symbols': len(self.data_cache)
        }
    
    async def stop(self):
        """停止数据引擎"""
        self.is_running = False
        
        # 停止所有数据源
        for source in self.data_sources.values():
            try:
                if hasattr(source, 'stop'):
                    if asyncio.iscoroutinefunction(source.stop):
                        await source.stop()
                    else:
                        source.stop()
            except Exception as e:
                logger.error(f"停止数据源失败: {e}")
        
        logger.info("真实市场数据引擎已停止")

# 测试函数
async def test_real_data_engine():
    """测试真实数据引擎"""
    print("🧪 测试真实市场数据引擎...")
    
    config = DataSourceConfig()
    engine = RealMarketDataEngine(config)
    
    # 添加数据回调
    def on_market_data(data: RealMarketData):
        print(f"📊 真实数据: {data.symbol} @ ${data.price:.2f} "
              f"({data.change_percent:+.2f}%) 📈 成交量: {data.volume:,} "
              f"来源: {data.source}")
    
    engine.subscribe_to_data(on_market_data)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    
    try:
        print(f"🔄 开始获取真实数据: {symbols}")
        
        # 运行60秒
        await asyncio.wait_for(engine.start(symbols), timeout=60)
        
    except asyncio.TimeoutError:
        print("⏰ 测试超时，显示性能统计...")
        
        stats = engine.get_performance_stats()
        print(f"\n📈 性能统计:")
        print(f"  处理消息: {stats['messages_processed']}")
        print(f"  活跃数据源: {stats['sources_active']}")
        print(f"  运行时间: {stats['runtime_seconds']:.1f}s")
        print(f"  消息速率: {stats['messages_per_second']:.1f} MPS")
        print(f"  缓存股票: {stats['cached_symbols']}")
        print(f"  最后更新: {stats['last_update_ago']:.1f}s前")
        
    finally:
        await engine.stop()
        print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_real_data_engine())