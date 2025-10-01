#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略信号融合系统 - 实时多策略并行执行和信号聚合
用于实时响应式高频交易的策略信号处理引擎

功能特点:
- 多策略并行执行（RSI、MACD、SMA、BB等）
- 智能权重分配和信号强度计算
- 实时信号聚合和冲突解决
- 性能监控和延迟追踪
- 异步处理，目标延迟<50ms
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from threading import Lock
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"

@dataclass
class TradingSignal:
    """交易信号数据结构"""
    symbol: str
    strategy_name: str
    signal_type: SignalType
    strength: float  # 信号强度 0-1
    confidence: float  # 置信度 0-1
    price: float
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['signal_type'] = self.signal_type.value
        return data

@dataclass
class FusedSignal:
    """融合后的信号"""
    symbol: str
    final_signal: SignalType
    aggregated_strength: float
    confidence_score: float
    contributing_strategies: List[str]
    signal_weights: Dict[str, float]
    processing_time_ms: float
    timestamp: float

class StrategySignalEngine:
    """策略信号生成引擎"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.is_running = False
        self.signal_history = []
        
    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """生成交易信号（由子类实现）"""
        raise NotImplementedError("子类必须实现generate_signal方法")
    
    def generate_signal_sync(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """同步生成交易信号（默认实现）"""
        import asyncio
        try:
            # 尝试运行异步方法
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环已经在运行，使用同步版本
                return self._generate_signal_sync_impl(symbol, market_data)
            else:
                return loop.run_until_complete(self.generate_signal(symbol, market_data))
        except Exception:
            # 回退到同步实现
            return self._generate_signal_sync_impl(symbol, market_data)
    
    def _generate_signal_sync_impl(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """同步信号生成的默认实现（由子类重写）"""
        return None

class RSISignalEngine(StrategySignalEngine):
    """RSI策略信号引擎"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.price_history = {}
        
    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """生成RSI信号"""
        try:
            price = market_data.get('price', 0)
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(price)
            
            # 保持最近period+1个价格点
            if len(self.price_history[symbol]) > self.period + 1:
                self.price_history[symbol] = self.price_history[symbol][-(self.period + 1):]
            
            # 需要足够的数据计算RSI
            if len(self.price_history[symbol]) < self.period + 1:
                return None
                
            # 计算RSI
            prices = np.array(self.price_history[symbol])
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-self.period:])
            avg_loss = np.mean(losses[-self.period:])
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # 生成信号
            signal_type = SignalType.HOLD
            strength = 0.5
            confidence = 0.7
            
            if rsi <= self.oversold:
                signal_type = SignalType.BUY
                strength = min(1.0, (self.oversold - rsi) / self.oversold + 0.5)
                confidence = 0.8
            elif rsi >= self.overbought:
                signal_type = SignalType.SELL
                strength = min(1.0, (rsi - self.overbought) / (100 - self.overbought) + 0.5)
                confidence = 0.8
            
            return TradingSignal(
                symbol=symbol,
                strategy_name=self.strategy_name,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                price=price,
                timestamp=time.time(),
                metadata={'rsi': rsi}
            )
            
        except Exception as e:
            logger.error(f"RSI信号生成失败 {symbol}: {e}")
            return None
    
    def _generate_signal_sync_impl(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """RSI同步信号生成实现"""
        try:
            price = market_data.get('price', 0)
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(price)
            
            # 保持最近period+1个价格点
            if len(self.price_history[symbol]) > self.period + 1:
                self.price_history[symbol] = self.price_history[symbol][-(self.period + 1):]
            
            # 需要足够的数据计算RSI
            if len(self.price_history[symbol]) < self.period + 1:
                return None
                
            # 计算RSI
            prices = np.array(self.price_history[symbol])
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-self.period:])
            avg_loss = np.mean(losses[-self.period:])
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            # 生成信号
            signal_type = SignalType.HOLD
            strength = 0.5
            confidence = 0.7
            
            if rsi <= self.oversold:
                signal_type = SignalType.BUY
                strength = min(1.0, (self.oversold - rsi) / self.oversold + 0.5)
                confidence = 0.8
            elif rsi >= self.overbought:
                signal_type = SignalType.SELL
                strength = min(1.0, (rsi - self.overbought) / (100 - self.overbought) + 0.5)
                confidence = 0.8
            
            return TradingSignal(
                symbol=symbol,
                strategy_name=self.strategy_name,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                price=price,
                timestamp=time.time(),
                metadata={'rsi': rsi}
            )
            
        except Exception as e:
            logger.error(f"RSI同步信号生成失败 {symbol}: {e}")
            return None

class MACDSignalEngine(StrategySignalEngine):
    """MACD策略信号引擎"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__("MACD")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.price_history = {}
        
    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """生成MACD信号"""
        try:
            price = market_data.get('price', 0)
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(price)
            
            # 保持足够的历史数据
            required_length = self.slow_period + self.signal_period + 10
            if len(self.price_history[symbol]) > required_length:
                self.price_history[symbol] = self.price_history[symbol][-required_length:]
            
            # 需要足够的数据计算MACD
            if len(self.price_history[symbol]) < self.slow_period + self.signal_period:
                return None
                
            # 计算MACD
            prices = pd.Series(self.price_history[symbol])
            ema_fast = prices.ewm(span=self.fast_period).mean()
            ema_slow = prices.ewm(span=self.slow_period).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=self.signal_period).mean()
            histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]
            prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0
            
            # 生成信号
            signal_type = SignalType.HOLD
            strength = 0.5
            confidence = 0.7
            
            # MACD线上穿信号线且柱状图为正
            if current_macd > current_signal and current_histogram > 0 and prev_histogram <= 0:
                signal_type = SignalType.BUY
                strength = min(1.0, abs(current_histogram) * 10 + 0.6)
                confidence = 0.8
            # MACD线下穿信号线且柱状图为负
            elif current_macd < current_signal and current_histogram < 0 and prev_histogram >= 0:
                signal_type = SignalType.SELL
                strength = min(1.0, abs(current_histogram) * 10 + 0.6)
                confidence = 0.8
            
            return TradingSignal(
                symbol=symbol,
                strategy_name=self.strategy_name,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                price=price,
                timestamp=time.time(),
                metadata={
                    'macd': current_macd,
                    'signal': current_signal,
                    'histogram': current_histogram
                }
            )
            
        except Exception as e:
            logger.error(f"MACD信号生成失败 {symbol}: {e}")
            return None
    
    def _generate_signal_sync_impl(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """MACD同步信号生成实现"""
        try:
            price = market_data.get('price', 0)
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(price)
            
            # 保持足够的历史数据
            required_length = self.slow_period + self.signal_period + 10
            if len(self.price_history[symbol]) > required_length:
                self.price_history[symbol] = self.price_history[symbol][-required_length:]
            
            # 需要足够的数据计算MACD
            if len(self.price_history[symbol]) < self.slow_period + self.signal_period:
                return None
                
            # 计算MACD
            prices = pd.Series(self.price_history[symbol])
            ema_fast = prices.ewm(span=self.fast_period).mean()
            ema_slow = prices.ewm(span=self.slow_period).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=self.signal_period).mean()
            histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]
            prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0
            
            # 生成信号
            signal_type = SignalType.HOLD
            strength = 0.5
            confidence = 0.7
            
            # MACD线上穿信号线且柱状图为正
            if current_macd > current_signal and current_histogram > 0 and prev_histogram <= 0:
                signal_type = SignalType.BUY
                strength = min(1.0, abs(current_histogram) * 10 + 0.6)
                confidence = 0.8
            # MACD线下穿信号线且柱状图为负
            elif current_macd < current_signal and current_histogram < 0 and prev_histogram >= 0:
                signal_type = SignalType.SELL
                strength = min(1.0, abs(current_histogram) * 10 + 0.6)
                confidence = 0.8
            
            return TradingSignal(
                symbol=symbol,
                strategy_name=self.strategy_name,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                price=price,
                timestamp=time.time(),
                metadata={
                    'macd': current_macd,
                    'signal': current_signal,
                    'histogram': current_histogram
                }
            )
            
        except Exception as e:
            logger.error(f"MACD同步信号生成失败 {symbol}: {e}")
            return None

class SMASignalEngine(StrategySignalEngine):
    """SMA策略信号引擎（双均线）"""
    
    def __init__(self, short_period: int = 10, long_period: int = 20):
        super().__init__("SMA")
        self.short_period = short_period
        self.long_period = long_period
        self.price_history = {}
        
    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """生成SMA信号"""
        try:
            price = market_data.get('price', 0)
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append(price)
            
            # 保持历史数据
            if len(self.price_history[symbol]) > self.long_period + 10:
                self.price_history[symbol] = self.price_history[symbol][-(self.long_period + 10):]
            
            if len(self.price_history[symbol]) < self.long_period:
                return None
                
            # 计算SMA
            prices = np.array(self.price_history[symbol])
            sma_short = np.mean(prices[-self.short_period:])
            sma_long = np.mean(prices[-self.long_period:])
            prev_sma_short = np.mean(prices[-self.short_period-1:-1]) if len(prices) > self.short_period else sma_short
            prev_sma_long = np.mean(prices[-self.long_period-1:-1]) if len(prices) > self.long_period else sma_long
            
            # 生成信号
            signal_type = SignalType.HOLD
            strength = 0.5
            confidence = 0.6
            
            # 短期均线上穿长期均线
            if sma_short > sma_long and prev_sma_short <= prev_sma_long:
                signal_type = SignalType.BUY
                strength = min(1.0, abs(sma_short - sma_long) / sma_long * 100 + 0.6)
                confidence = 0.75
            # 短期均线下穿长期均线
            elif sma_short < sma_long and prev_sma_short >= prev_sma_long:
                signal_type = SignalType.SELL
                strength = min(1.0, abs(sma_short - sma_long) / sma_long * 100 + 0.6)
                confidence = 0.75
            
            return TradingSignal(
                symbol=symbol,
                strategy_name=self.strategy_name,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                price=price,
                timestamp=time.time(),
                metadata={
                    'sma_short': sma_short,
                    'sma_long': sma_long,
                    'divergence_pct': abs(sma_short - sma_long) / sma_long * 100
                }
            )
            
        except Exception as e:
            logger.error(f"SMA信号生成失败 {symbol}: {e}")
            return None

class GenericStrategyEngine:
    """通用策略引擎包装器"""
    
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        self.logger = logging.getLogger(f"GenericEngine_{strategy_name}")
    
    def generate_signal(self, symbol, data):
        """为策略生成通用信号"""
        try:
            # 处理不同的数据格式
            if isinstance(data, dict):
                # 如果是字典格式，提取DataFrame
                if 'data' in data and hasattr(data['data'], 'iloc'):
                    df = data['data']
                    # 转换DataFrame为列表格式
                    data_list = []
                    for i in range(len(df)):
                        row_data = {
                            'close': float(df['Close'].iloc[i]) if 'Close' in df.columns else 150.0,
                            'volume': int(df['Volume'].iloc[i]) if 'Volume' in df.columns else 1000,
                            'timestamp': time.time()
                        }
                        data_list.append(row_data)
                    data_to_use = data_list
                else:
                    # 如果是简单字典，创建单个数据点
                    data_to_use = [{
                        'close': data.get('price', 150.0),
                        'volume': data.get('volume', 1000),
                        'timestamp': data.get('timestamp', time.time())
                    }]
            else:
                # 假设已经是正确格式的列表
                data_to_use = data
            
            # 简单的技术指标信号生成
            if len(data_to_use) < 5:
                return 0.0
            
            close_prices = [d['close'] for d in data_to_use[-20:] if 'close' in d]
            if not close_prices:
                return 0.0
            
            if self.strategy_name == "MomentumBreakout":
                # 动量突破策略
                if len(close_prices) >= 2:
                    momentum = (close_prices[-1] - close_prices[-2]) / close_prices[-2]
                    return min(max(momentum * 10, -1.0), 1.0)
            
            elif self.strategy_name == "MeanReversion":
                # 均值回归策略
                if len(close_prices) >= 10:
                    avg = sum(close_prices[-10:]) / 10
                    deviation = (close_prices[-1] - avg) / avg
                    return min(max(-deviation * 5, -1.0), 1.0)
            
            elif self.strategy_name == "VolumeConfirmation":
                # 成交量确认策略
                volumes = [d.get('volume', 0) for d in data_to_use[-5:]]
                if volumes and len(volumes) > 1:
                    avg_vol = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else volumes[0]
                    if avg_vol > 0:
                        vol_signal = min(max((volumes[-1] - avg_vol) / avg_vol, -1.0), 1.0)
                        return vol_signal
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"❌ {self.strategy_name}信号生成失败: {e}")
            return 0.0

    def generate_signal_sync(self, symbol, data):
        """同步信号生成方法（兼容性）"""
        from dataclasses import dataclass
        from enum import Enum
        
        class SignalType(Enum):
            BUY = 1
            SELL = -1
            HOLD = 0
        
        @dataclass
        class TradingSignal:
            symbol: str
            strategy_name: str
            signal_type: SignalType
            strength: float
            confidence: float
            price: float
            timestamp: float
            metadata: dict = None
        
        try:
            # 获取信号值
            signal_value = self.generate_signal(symbol, data)
            
            # 转换为信号对象
            if signal_value > 0.1:
                signal_type = SignalType.BUY
            elif signal_value < -0.1:
                signal_type = SignalType.SELL
            else:
                signal_type = SignalType.HOLD
            
            # 获取价格信息
            if isinstance(data, dict):
                price = data.get('price', 100.0)
            else:
                price = 100.0
            
            return TradingSignal(
                symbol=symbol,
                strategy_name=self.strategy_name,
                signal_type=signal_type,
                strength=abs(signal_value),
                confidence=0.8,
                price=price,
                timestamp=time.time(),
                metadata={'strategy': self.strategy_name, 'signal_value': signal_value}
            )
        
        except Exception as e:
            self.logger.error(f"❌ {self.strategy_name} 同步信号生成失败: {e}")
            # 返回一个默认的HOLD信号而不是None
            return TradingSignal(
                symbol=symbol,
                strategy_name=self.strategy_name,
                signal_type=SignalType.HOLD,
                strength=0.0,
                confidence=0.0,
                price=100.0,
                timestamp=time.time(),
                metadata={'error': str(e)}
            )


class StrategySignalFusion:
    """策略信号融合系统"""
    
    def __init__(self):
        self.strategy_engines = {}
        self.strategy_weights = {}
        self.signal_callbacks = []
        self.performance_stats = {
            'signals_processed': 0,
            'fusion_times': [],
            'signal_conflicts': 0,
            'start_time': time.time()
        }
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.lock = Lock()
        self.is_running = False
        
        # 添加 strategies 属性（兼容性）
        self.strategies = {}
        
        # 初始化默认策略
        self._initialize_default_strategies()
        
    def _initialize_default_strategies(self):
        """初始化默认策略"""
        try:
            # 导入策略配置管理器
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            
            from strategy_config import StrategyConfigManager
            
            # 获取默认的balanced配置
            config_manager = StrategyConfigManager()
            balanced_config = config_manager.get_config("balanced")
            
            if balanced_config:
                logger.info(f"使用balanced配置策略: {balanced_config.strategies}")
                
                # 根据配置创建策略引擎
                for i, strategy_name in enumerate(balanced_config.strategies):
                    weight = balanced_config.weights[i] if i < len(balanced_config.weights) else 1.0
                    
                    # 根据策略名称创建对应的引擎
                    if strategy_name == "RSI":
                        engine = RSISignalEngine()
                        self.add_strategy(engine, weight=weight)
                        self.strategies[strategy_name] = engine
                    elif strategy_name == "MACD":
                        engine = MACDSignalEngine()
                        self.add_strategy(engine, weight=weight)
                        self.strategies[strategy_name] = engine
                    elif strategy_name in ["MomentumBreakout", "MeanReversion", "VolumeConfirmation"]:
                        # 对于其他策略，创建通用的策略引擎包装器
                        engine = GenericStrategyEngine(strategy_name)
                        self.add_strategy(engine, weight=weight)
                        self.strategies[strategy_name] = engine
                    else:
                        logger.warning(f"未知策略类型: {strategy_name}")
                
                logger.info(f"✅ 初始化了 {len(self.strategies)} 个策略")
            else:
                # 回退到简单的RSI+MACD组合
                logger.info("使用简单的RSI+MACD策略组合")
                rsi_strategy = RSISignalEngine()
                self.add_strategy(rsi_strategy, weight=1.0)
                self.strategies['RSI'] = rsi_strategy
                
                macd_strategy = MACDSignalEngine()
                self.add_strategy(macd_strategy, weight=1.0)
                self.strategies['MACD'] = macd_strategy
                
                logger.info(f"✅ 初始化了 {len(self.strategies)} 个默认策略")
            
        except Exception as e:
            logger.warning(f"⚠️ 默认策略初始化失败: {e}")
            # 最简单的回退策略
            self.strategies = {}
            try:
                rsi_strategy = RSISignalEngine()
                self.add_strategy(rsi_strategy, weight=1.0)
                self.strategies['RSI'] = rsi_strategy
                logger.info("✅ 使用最小RSI策略")
            except Exception as e2:
                logger.error(f"RSI策略初始化也失败: {e2}")
                self.strategies = {}
        
    def add_strategy(self, engine: StrategySignalEngine, weight: float = 1.0):
        """添加策略引擎"""
        self.strategy_engines[engine.strategy_name] = engine
        self.strategy_weights[engine.strategy_name] = weight
        logger.info(f"策略已添加: {engine.strategy_name} (权重: {weight})")
        
    def set_strategy_weight(self, strategy_name: str, weight: float):
        """设置策略权重"""
        if strategy_name in self.strategy_weights:
            self.strategy_weights[strategy_name] = weight
            logger.info(f"策略权重已更新: {strategy_name} -> {weight}")
        
    def add_signal_callback(self, callback: Callable[[FusedSignal], None]):
        """添加信号回调函数"""
        self.signal_callbacks.append(callback)
    
    def generate_signals(self, symbol: str, data) -> List[Dict]:
        """生成信号（兼容性方法）"""
        try:
            if data is None or (hasattr(data, 'empty') and data.empty):
                return []
            
            signals = []
            
            # 获取最新价格
            if hasattr(data, 'iloc') and len(data) > 0:
                latest_price = float(data['Close'].iloc[-1]) if 'Close' in data.columns else 150.0
                volume = int(data['Volume'].iloc[-1]) if 'Volume' in data.columns else 1000
            else:
                latest_price = 150.0
                volume = 1000
            
            market_data = {
                'symbol': symbol,
                'price': latest_price,
                'volume': volume,
                'timestamp': time.time(),
                'data': data
            }
            
            # 为每个策略生成信号，如果策略引擎存在
            if self.strategy_engines:
                for strategy_name, engine in self.strategy_engines.items():
                    try:
                        # 使用同步方法生成信号
                        signal = engine.generate_signal_sync(symbol, market_data)
                        if signal:
                            signals.append({
                                'strategy': strategy_name,
                                'signal': signal.signal_type.value,
                                'strength': signal.strength,
                                'confidence': signal.confidence,
                                'timestamp': signal.timestamp,
                                'price': signal.price
                            })
                    except Exception as e:
                        logger.warning(f"策略 {strategy_name} 信号生成失败: {e}")
                        # 添加默认信号以确保至少有一些输出
                        signals.append({
                            'strategy': strategy_name,
                            'signal': 'hold',
                            'strength': 0.5,
                            'confidence': 0.3,
                            'timestamp': time.time(),
                            'price': latest_price,
                            'error': str(e)
                        })
            else:
                # 如果没有策略引擎，生成一些基本信号用于测试
                logger.info("没有策略引擎，生成基本测试信号")
                signals.append({
                    'strategy': 'basic_trend',
                    'signal': 'hold',
                    'strength': 0.5,
                    'confidence': 0.6,
                    'timestamp': time.time(),
                    'price': latest_price
                })
            
            return signals
            
        except Exception as e:
            logger.error(f"信号生成失败 {symbol}: {e}")
            # 返回至少一个基本信号，避免完全失败
            return [{
                'strategy': 'fallback',
                'signal': 'hold',
                'strength': 0.5,
                'confidence': 0.3,
                'timestamp': time.time(),
                'price': 150.0,
                'error': str(e)
            }]
        
    async def process_market_data(self, symbol: str, market_data: Dict):
        """处理市场数据并生成融合信号"""
        if not self.is_running:
            return
            
        start_time = time.time()
        
        try:
            # 并行生成所有策略信号
            tasks = []
            for engine in self.strategy_engines.values():
                task = asyncio.create_task(
                    engine.generate_signal(symbol, market_data)
                )
                tasks.append(task)
            
            # 等待所有信号生成完成
            signals = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤有效信号
            valid_signals = []
            for signal in signals:
                if isinstance(signal, TradingSignal):
                    valid_signals.append(signal)
                elif isinstance(signal, Exception):
                    logger.warning(f"策略信号生成异常: {signal}")
            
            # 融合信号
            if valid_signals:
                fused_signal = await self._fuse_signals(symbol, valid_signals)
                
                if fused_signal:
                    # 记录性能统计
                    processing_time = (time.time() - start_time) * 1000
                    fused_signal.processing_time_ms = processing_time
                    
                    with self.lock:
                        self.performance_stats['signals_processed'] += 1
                        self.performance_stats['fusion_times'].append(processing_time)
                        
                        # 保持最近1000次记录
                        if len(self.performance_stats['fusion_times']) > 1000:
                            self.performance_stats['fusion_times'] = self.performance_stats['fusion_times'][-1000:]
                    
                    # 触发回调
                    for callback in self.signal_callbacks:
                        try:
                            callback(fused_signal)
                        except Exception as e:
                            logger.error(f"信号回调执行失败: {e}")
                            
        except Exception as e:
            logger.error(f"市场数据处理失败 {symbol}: {e}")
    
    async def _fuse_signals(self, symbol: str, signals: List[TradingSignal]) -> Optional[FusedSignal]:
        """融合多个策略信号"""
        if not signals:
            return None
            
        try:
            # 按信号类型分组
            signal_groups = {}
            for signal in signals:
                signal_type = signal.signal_type
                if signal_type not in signal_groups:
                    signal_groups[signal_type] = []
                signal_groups[signal_type].append(signal)
            
            # 计算加权分数
            signal_scores = {}
            contributing_strategies = []
            signal_weights = {}
            
            for signal_type, signal_list in signal_groups.items():
                total_score = 0
                total_weight = 0
                
                for signal in signal_list:
                    strategy_weight = self.strategy_weights.get(signal.strategy_name, 1.0)
                    weighted_score = signal.strength * signal.confidence * strategy_weight
                    total_score += weighted_score
                    total_weight += strategy_weight
                    
                    contributing_strategies.append(signal.strategy_name)
                    signal_weights[signal.strategy_name] = strategy_weight
                
                if total_weight > 0:
                    signal_scores[signal_type] = total_score / total_weight
            
            # 确定最终信号
            if not signal_scores:
                return None
                
            # 找到得分最高的信号类型
            final_signal_type = max(signal_scores.keys(), key=lambda x: signal_scores[x])
            aggregated_strength = signal_scores[final_signal_type]
            
            # 计算置信度（基于信号一致性）
            confidence_score = self._calculate_confidence(signal_groups, final_signal_type)
            
            # 检测信号冲突
            conflicting_signals = len([s for s in signal_scores.keys() 
                                    if s != final_signal_type and signal_scores[s] > 0.3])
            if conflicting_signals > 0:
                with self.lock:
                    self.performance_stats['signal_conflicts'] += 1
                confidence_score *= 0.8  # 降低置信度
            
            return FusedSignal(
                symbol=symbol,
                final_signal=final_signal_type,
                aggregated_strength=aggregated_strength,
                confidence_score=confidence_score,
                contributing_strategies=list(set(contributing_strategies)),
                signal_weights=signal_weights,
                processing_time_ms=0,  # 将在外部设置
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"信号融合失败 {symbol}: {e}")
            return None
    
    def _calculate_confidence(self, signal_groups: Dict, final_signal_type: SignalType) -> float:
        """计算信号置信度"""
        total_signals = sum(len(signals) for signals in signal_groups.values())
        final_signal_count = len(signal_groups.get(final_signal_type, []))
        
        if total_signals == 0:
            return 0.5
            
        # 基础置信度基于信号一致性
        consistency_ratio = final_signal_count / total_signals
        
        # 考虑信号强度
        final_signals = signal_groups.get(final_signal_type, [])
        avg_strength = np.mean([s.strength for s in final_signals]) if final_signals else 0.5
        avg_confidence = np.mean([s.confidence for s in final_signals]) if final_signals else 0.5
        
        # 综合置信度
        confidence = (consistency_ratio * 0.4 + avg_strength * 0.3 + avg_confidence * 0.3)
        return min(1.0, max(0.0, confidence))
    
    def start(self):
        """启动信号融合系统"""
        self.is_running = True
        logger.info("策略信号融合系统已启动")
        
    def stop(self):
        """停止信号融合系统"""
        self.is_running = False
        self.executor.shutdown(wait=True)
        logger.info("策略信号融合系统已停止")
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        with self.lock:
            fusion_times = self.performance_stats['fusion_times']
            runtime = time.time() - self.performance_stats['start_time']
            
            stats = {
                'signals_processed': self.performance_stats['signals_processed'],
                'signal_conflicts': self.performance_stats['signal_conflicts'],
                'runtime_seconds': runtime,
                'signals_per_second': self.performance_stats['signals_processed'] / runtime if runtime > 0 else 0,
                'avg_fusion_time_ms': np.mean(fusion_times) if fusion_times else 0,
                'max_fusion_time_ms': np.max(fusion_times) if fusion_times else 0,
                'min_fusion_time_ms': np.min(fusion_times) if fusion_times else 0,
                'fusion_time_p95_ms': np.percentile(fusion_times, 95) if fusion_times else 0,
                'conflict_rate': self.performance_stats['signal_conflicts'] / max(1, self.performance_stats['signals_processed'])
            }
            
            return stats

def create_default_fusion_system() -> StrategySignalFusion:
    """创建默认的信号融合系统"""
    fusion_system = StrategySignalFusion()
    
    # 添加默认策略
    fusion_system.add_strategy(RSISignalEngine(), weight=1.0)
    fusion_system.add_strategy(MACDSignalEngine(), weight=1.2)
    fusion_system.add_strategy(SMASignalEngine(), weight=0.8)
    
    return fusion_system

# 测试函数
async def test_strategy_fusion():
    """测试策略信号融合系统"""
    print("🧪 测试策略信号融合系统...")
    
    # 创建融合系统
    fusion_system = create_default_fusion_system()
    
    # 添加信号回调
    def on_fused_signal(signal: FusedSignal):
        print(f"📊 融合信号: {signal.symbol} -> {signal.final_signal.value} "
              f"(强度: {signal.aggregated_strength:.2f}, 置信度: {signal.confidence_score:.2f}, "
              f"处理时间: {signal.processing_time_ms:.2f}ms)")
        print(f"   贡献策略: {', '.join(signal.contributing_strategies)}")
    
    fusion_system.add_signal_callback(on_fused_signal)
    fusion_system.start()
    
    # 模拟市场数据
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    base_prices = {'AAPL': 150.0, 'MSFT': 300.0, 'GOOGL': 2500.0}
    
    try:
        print("🔄 开始信号生成测试...")
        for i in range(50):  # 生成50个数据点
            for symbol in symbols:
                # 模拟价格波动
                price_change = np.random.normal(0, 0.02)  # 2%标准差
                base_prices[symbol] *= (1 + price_change)
                
                market_data = {
                    'symbol': symbol,
                    'price': base_prices[symbol],
                    'volume': np.random.randint(1000, 10000),
                    'timestamp': time.time()
                }
                
                await fusion_system.process_market_data(symbol, market_data)
            
            await asyncio.sleep(0.1)  # 100ms间隔
        
        # 显示性能统计
        stats = fusion_system.get_performance_stats()
        print(f"\n📈 性能统计:")
        print(f"  处理信号数: {stats['signals_processed']}")
        print(f"  信号冲突数: {stats['signal_conflicts']}")
        print(f"  平均融合时间: {stats['avg_fusion_time_ms']:.2f}ms")
        print(f"  P95融合时间: {stats['fusion_time_p95_ms']:.2f}ms")
        print(f"  冲突率: {stats['conflict_rate']:.1%}")
        print(f"  信号速率: {stats['signals_per_second']:.1f} SPS")
        
    finally:
        fusion_system.stop()

if __name__ == "__main__":
    asyncio.run(test_strategy_fusion())