"""
策略引擎基础模块

为日内交易系统提供策略基类和通用功能。
所有交易策略都应继承自BaseStrategy类。
"""

import backtrader as bt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod
from enum import Enum
import logging
import numpy as np


class SignalType(Enum):
    """交易信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(Enum):
    """信号强度"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


class TradingSignal:
    """交易信号数据结构"""
    
    def __init__(self, 
                 signal_type: SignalType,
                 strength: SignalStrength,
                 confidence: float,
                 strategy_name: str,
                 timestamp: datetime,
                 price: float,
                 volume: int = 0,
                 indicators: Dict[str, float] = None):
        """
        初始化交易信号
        
        Args:
            signal_type: 信号类型
            strength: 信号强度
            confidence: 信号置信度 (0-1)
            strategy_name: 策略名称
            timestamp: 信号时间戳
            price: 信号价格
            volume: 成交量
            indicators: 相关技术指标
        """
        self.signal_type = signal_type
        self.strength = strength
        self.confidence = confidence
        self.strategy_name = strategy_name
        self.timestamp = timestamp
        self.price = price
        self.volume = volume
        self.indicators = indicators or {}
        
        # 计算信号分数
        self.score = self._calculate_score()
    
    def _calculate_score(self) -> float:
        """计算信号综合分数 (0-100)"""
        # 基础分数
        base_score = {
            SignalType.STRONG_BUY: 90,
            SignalType.BUY: 70,
            SignalType.HOLD: 50,
            SignalType.SELL: 30,
            SignalType.STRONG_SELL: 10
        }.get(self.signal_type, 50)
        
        # 强度调整
        strength_multiplier = {
            SignalStrength.WEAK: 0.8,
            SignalStrength.MODERATE: 1.0,
            SignalStrength.STRONG: 1.2,
            SignalStrength.VERY_STRONG: 1.4
        }.get(self.strength, 1.0)
        
        # 置信度调整
        confidence_adjustment = self.confidence
        
        return min(100, base_score * strength_multiplier * confidence_adjustment)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'signal_type': self.signal_type.value,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'score': self.score,
            'strategy_name': self.strategy_name,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'volume': self.volume,
            'indicators': self.indicators
        }
    
    def __str__(self) -> str:
        return (f"{self.strategy_name}: {self.signal_type.value} "
                f"(强度:{self.strength.value}, 置信度:{self.confidence:.2f}, "
                f"分数:{self.score:.1f})")


class BaseStrategy:
    """
    策略基类
    
    所有日内交易策略的基础类，提供通用功能和标准接口。
    注意：这个基类不直接继承bt.Strategy，避免元类冲突。
    具体策略类可以根据需要选择继承bt.Strategy或独立实现。
    """
    
    params = (
        ('strategy_name', 'BaseStrategy'),
        ('min_confidence', 0.6),  # 最小信号置信度
        ('lookback_period', 20),  # 回看周期
        ('signal_cooldown', 5),   # 信号冷却时间(分钟)
    )
    
    def __init__(self):
        """初始化策略"""
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # 信号管理
        self.signals_history: List[TradingSignal] = []
        self.last_signal_time: Optional[datetime] = None
        
        # 策略状态
        self.strategy_active = True
        self.strategy_start_time = datetime.now()
        
        # 性能统计
        self.signal_count = 0
        self.successful_signals = 0
        
        # 参数设置
        self.params = type('Params', (), {
            'strategy_name': 'BaseStrategy',
            'min_confidence': 0.6,
            'lookback_period': 20,
            'signal_cooldown': 5
        })()
        
        # 初始化技术指标
        self._init_indicators()
        
        self.logger.info(f"策略初始化完成: {self.params.strategy_name}")
    
    def _init_indicators(self):
        """初始化技术指标 - 子类需要实现"""
        pass
    
    def generate_signal(self) -> Optional[TradingSignal]:
        """生成交易信号 - 子类需要实现"""
        return self._generate_signal()
    
    def _generate_signal(self) -> Optional[TradingSignal]:
        """内部信号生成方法 - 子类需要实现"""
        pass
    
    def next(self):
        """策略主循环"""
        if not self.strategy_active:
            return
        
        try:
            # 检查信号冷却时间
            if self._is_in_cooldown():
                return
            
            # 生成交易信号
            signal = self._generate_signal()
            
            if signal and self._validate_signal(signal):
                self._process_signal(signal)
                
        except Exception as e:
            self.logger.error(f"策略执行错误: {e}")
    
    def _is_in_cooldown(self) -> bool:
        """检查是否在信号冷却期"""
        if not self.last_signal_time:
            return False
        
        cooldown_end = self.last_signal_time + timedelta(minutes=self.params.signal_cooldown)
        return datetime.now() < cooldown_end
    
    def _validate_signal(self, signal: TradingSignal) -> bool:
        """验证信号有效性"""
        # 检查置信度
        if signal.confidence < self.params.min_confidence:
            self.logger.debug(f"信号置信度过低: {signal.confidence:.2f}")
            return False
        
        # 检查信号时间
        signal_age = (datetime.now() - signal.timestamp).total_seconds()
        if signal_age > 300:  # 5分钟内的信号才有效
            self.logger.debug(f"信号过期: {signal_age:.1f}秒前")
            return False
        
        return True
    
    def _process_signal(self, signal: TradingSignal):
        """处理有效信号"""
        self.signals_history.append(signal)
        self.signal_count += 1
        self.last_signal_time = signal.timestamp
        
        self.logger.info(f"新信号: {signal}")
        
        # 执行交易逻辑
        self._execute_signal(signal)
    
    def _execute_signal(self, signal: TradingSignal):
        """执行信号对应的交易操作"""
        # 这里将来集成订单执行模块
        
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            self.logger.info(f"执行买入信号: {signal.price}")
            # TODO: 实际买入逻辑
            
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            self.logger.info(f"执行卖出信号: {signal.price}")
            # TODO: 实际卖出逻辑
        
        else:  # HOLD
            self.logger.debug(f"持有信号: {signal.price}")
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """获取策略性能统计"""
        runtime = (datetime.now() - self.strategy_start_time).total_seconds()
        signal_rate = self.signal_count / (runtime / 3600) if runtime > 0 else 0
        
        return {
            'strategy_name': self.params.strategy_name,
            'runtime_hours': runtime / 3600,
            'total_signals': self.signal_count,
            'successful_signals': self.successful_signals,
            'signal_rate_per_hour': signal_rate,
            'success_rate': self.successful_signals / self.signal_count if self.signal_count > 0 else 0,
            'active': self.strategy_active
        }
    
    def get_recent_signals(self, count: int = 10) -> List[TradingSignal]:
        """获取最近的信号"""
        return self.signals_history[-count:] if self.signals_history else []
    
    def stop_strategy(self):
        """停止策略"""
        self.strategy_active = False
        self.logger.info(f"策略已停止: {self.params.strategy_name}")
    
    def start_strategy(self):
        """启动策略"""
        self.strategy_active = True
        self.logger.info(f"策略已启动: {self.params.strategy_name}")


class StrategyManager:
    """
    策略管理器
    
    负责管理多个策略实例，信号融合和权重分配。
    """
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_weights: Dict[str, float] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 信号融合配置
        self.fusion_enabled = True
        self.min_strategies_for_fusion = 2
        
    def add_strategy(self, strategy: BaseStrategy, weight: float = 1.0):
        """添加策略"""
        strategy_name = strategy.params.strategy_name
        self.strategies[strategy_name] = strategy
        self.strategy_weights[strategy_name] = weight
        
        self.logger.info(f"添加策略: {strategy_name} (权重: {weight})")
    
    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            del self.strategy_weights[strategy_name]
            self.logger.info(f"移除策略: {strategy_name}")
    
    def get_all_signals(self) -> List[TradingSignal]:
        """获取所有策略的最新信号"""
        all_signals = []
        
        for strategy in self.strategies.values():
            recent_signals = strategy.get_recent_signals(1)
            if recent_signals:
                all_signals.extend(recent_signals)
        
        return all_signals
    
    def fuse_signals(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """融合多个策略信号"""
        if not signals or len(signals) < self.min_strategies_for_fusion:
            return None
        
        # 按信号类型分组
        signal_groups = {}
        for signal in signals:
            signal_type = signal.signal_type
            if signal_type not in signal_groups:
                signal_groups[signal_type] = []
            signal_groups[signal_type].append(signal)
        
        # 计算加权分数
        weighted_scores = {}
        for signal_type, group_signals in signal_groups.items():
            total_weighted_score = 0
            total_weight = 0
            
            for signal in group_signals:
                weight = self.strategy_weights.get(signal.strategy_name, 1.0)
                total_weighted_score += signal.score * weight
                total_weight += weight
            
            if total_weight > 0:
                weighted_scores[signal_type] = total_weighted_score / total_weight
        
        # 选择最高分数的信号类型
        if not weighted_scores:
            return None
        
        best_signal_type = max(weighted_scores.keys(), key=lambda x: weighted_scores[x])
        best_score = weighted_scores[best_signal_type]
        
        # 计算融合信号的属性
        relevant_signals = signal_groups[best_signal_type]
        avg_confidence = sum(s.confidence for s in relevant_signals) / len(relevant_signals)
        avg_price = sum(s.price for s in relevant_signals) / len(relevant_signals)
        
        # 创建融合信号
        fused_signal = TradingSignal(
            signal_type=best_signal_type,
            strength=SignalStrength.STRONG if best_score > 80 else SignalStrength.MODERATE,
            confidence=avg_confidence,
            strategy_name="FusedStrategy",
            timestamp=datetime.now(),
            price=avg_price,
            indicators={'fused_score': best_score, 'strategies_count': len(relevant_signals)}
        )
        
        self.logger.info(f"信号融合完成: {fused_signal}")
        return fused_signal
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        status = {
            'total_strategies': len(self.strategies),
            'active_strategies': sum(1 for s in self.strategies.values() if s.strategy_active),
            'fusion_enabled': self.fusion_enabled,
            'strategies': {}
        }
        
        for name, strategy in self.strategies.items():
            status['strategies'][name] = {
                'weight': self.strategy_weights[name],
                'performance': strategy.get_strategy_performance(),
                'recent_signals_count': len(strategy.get_recent_signals(5))
            }
        
        return status


# 工具函数
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """计算RSI指标"""
    if len(prices) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50.0
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_moving_average(prices: List[float], period: int) -> float:
    """计算移动平均线"""
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0.0
    
    return sum(prices[-period:]) / period


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
    """计算布林带 (上轨, 中轨, 下轨)"""
    if len(prices) < period:
        avg = sum(prices) / len(prices) if prices else 0.0
        return avg, avg, avg
    
    recent_prices = prices[-period:]
    middle = sum(recent_prices) / period
    
    variance = sum((p - middle) ** 2 for p in recent_prices) / period
    std = variance ** 0.5
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def create_integrated_strategy_manager(confidence_threshold: float = 0.7) -> StrategyManager:
    """
    创建集成的三策略管理器
    
    集成动量突破、均值回归和成交量确认三个核心策略，
    通过加权融合提供统一的交易信号。
    
    Args:
        confidence_threshold: 信号置信度阈值
        
    Returns:
        配置好的策略管理器实例
    """
    manager = StrategyManager()
    
    try:
        # 动态导入简化版策略模块
        from .momentum_breakout_simple import MomentumBreakoutStrategy
        from .mean_reversion_simple import MeanReversionStrategy  
        from .volume_confirmation_simple import VolumeConfirmationStrategy
        
        # 创建策略实例并添加到管理器
        momentum_strategy = MomentumBreakoutStrategy()
        manager.add_strategy(momentum_strategy, weight=0.4)  # 最高权重
        
        mean_reversion_strategy = MeanReversionStrategy()
        manager.add_strategy(mean_reversion_strategy, weight=0.35)
        
        volume_strategy = VolumeConfirmationStrategy()
        manager.add_strategy(volume_strategy, weight=0.25)
        
        # 配置融合参数
        manager.min_strategies_for_fusion = 2  # 至少两个策略信号才融合
        
        logging.getLogger("StrategyIntegration").info(
            f"三策略管理器创建成功: 动量突破(40%) + 均值回归(35%) + 成交量确认(25%)"
        )
        
    except ImportError as e:
        logging.getLogger("StrategyIntegration").error(f"策略导入失败: {e}")
        raise
    
    return manager


def validate_strategy_integration() -> bool:
    """
    验证策略集成完整性
    
    检查所有策略模块是否正确实现并可以集成。
    
    Returns:
        集成验证是否通过
    """
    try:
        manager = create_integrated_strategy_manager()
        
        # 检查策略数量
        if len(manager.strategies) != 3:
            return False
        
        # 检查权重总和
        total_weight = sum(manager.strategy_weights.values())
        if abs(total_weight - 1.0) > 0.01:  # 允许小误差
            return False
        
        # 检查每个策略的基本方法
        for strategy in manager.strategies.values():
            if not hasattr(strategy, 'generate_signal'):
                return False
            if not hasattr(strategy, 'get_strategy_performance'):
                return False
        
        logging.getLogger("StrategyValidation").info("策略集成验证通过")
        return True
        
    except Exception as e:
        logging.getLogger("StrategyValidation").error(f"策略集成验证失败: {e}")
        return False