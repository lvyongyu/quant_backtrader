"""
简化策略模块 - Simplified Strategy Framework

函数式策略设计，重用现有组合策略，支持自定义扩展。

核心设计原则：
- 重用现有策略：使用strategies文件夹下的组合策略
- 函数式设计：策略就是函数，简单直观
- 参数化：所有策略都支持参数自定义
- 组合策略：支持多策略组合
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import logging
import sys
import os
from datetime import datetime

# 添加src路径到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

# 配置日志
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class StrategyResult:
    """策略结果"""
    signal: SignalType
    confidence: float  # 信号置信度 0-1
    price: float       # 当前价格
    reason: str        # 信号原因
    indicators: Dict   # 相关指标

# 策略实例缓存
_strategy_instances = {}

class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class StrategyResult:
    """策略结果"""
    signal: SignalType
    confidence: float  # 信号置信度 0-1
    price: float       # 当前价格
    reason: str        # 信号原因
    indicators: Dict   # 相关指标

class Strategy:
    """
    简化的策略类
    
    特点：
    - 函数式设计，易于理解和扩展
    - 内置常用技术指标计算
    - 支持自定义策略函数
    """
    
    def __init__(self, name: str, strategy_func: Callable, params: Dict = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            strategy_func: 策略函数
            params: 策略参数
        """
        self.name = name
        self.strategy_func = strategy_func
        self.params = params or {}
        
        logger.info(f"策略初始化：{name}")
    
    def generate_signal(self, data: pd.DataFrame) -> StrategyResult:
        """
        生成交易信号
        
        Args:
            data: 股票数据，包含OHLCV
            
        Returns:
            策略结果
        """
        try:
            result = self.strategy_func(data, **self.params)
            logger.debug(f"策略信号生成：{self.name} -> {result.signal}")
            return result
        except Exception as e:
            logger.error(f"策略信号生成失败：{self.name} - {e}")
            return StrategyResult(
                signal=SignalType.HOLD,
                confidence=0.0,
                price=data['Close'].iloc[-1] if not data.empty else 0.0,
                reason=f"策略错误：{e}",
                indicators={}
            )

# 导入现有策略类的包装函数
def get_strategy_instance(strategy_name: str):
    """获取策略实例（单例模式）"""
    if strategy_name not in _strategy_instances:
        try:
            if strategy_name == "MomentumBreakout":
                from strategies.momentum_breakout_simple import MomentumBreakoutStrategy
                _strategy_instances[strategy_name] = MomentumBreakoutStrategy()
            elif strategy_name == "MeanReversion":
                from strategies.mean_reversion_simple import MeanReversionStrategy
                _strategy_instances[strategy_name] = MeanReversionStrategy()
            elif strategy_name == "VolumeConfirmation":
                from strategies.volume_confirmation_simple import VolumeConfirmationStrategy
                _strategy_instances[strategy_name] = VolumeConfirmationStrategy()
            else:
                logger.warning(f"未知策略: {strategy_name}")
                return None
        except ImportError as e:
            logger.error(f"无法导入策略 {strategy_name}: {e}")
            return None
    
    return _strategy_instances[strategy_name]

def convert_signal_to_result(trading_signal, current_price: float) -> StrategyResult:
    """将TradingSignal转换为StrategyResult"""
    if trading_signal is None:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=current_price,
            reason="无信号",
            indicators={}
        )
    
    # 转换信号类型
    signal_map = {
        'BUY': SignalType.BUY,
        'SELL': SignalType.SELL,
        'HOLD': SignalType.HOLD
    }
    
    signal_type = signal_map.get(trading_signal.signal_type.value, SignalType.HOLD)
    
    return StrategyResult(
        signal=signal_type,
        confidence=trading_signal.confidence,
        price=trading_signal.price,
        reason=trading_signal.indicators.get('signal_type', '策略信号'),
        indicators=trading_signal.indicators
    )

# 重用现有组合策略的包装函数
def momentum_breakout_strategy(data: pd.DataFrame, **params) -> StrategyResult:
    """
    动量突破策略 - 基于真实数据的实现
    
    基于价格动量和突破信号的日内交易策略。
    适用于趋势明显、波动性适中的股票。
    """
    if len(data) < 20:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason="数据不足",
            indicators={}
        )
    
    try:
        close = data['Close']
        volume = data['Volume']
        high = data['High']
        low = data['Low']
        
        current_price = close.iloc[-1]
        current_volume = volume.iloc[-1]
        
        # 计算突破条件
        lookback = params.get('lookback_period', 20)
        recent_high = high.iloc[-lookback:].max()
        recent_low = low.iloc[-lookback:].min()
        avg_volume = volume.iloc[-lookback:].mean()
        
        # RSI计算
        rsi = calculate_rsi(close, 14).iloc[-1]
        
        # 突破阈值
        breakout_threshold = params.get('breakout_threshold', 0.02)
        volume_multiplier = params.get('volume_multiplier', 1.5)
        
        # 买入信号：价格突破近期高点且成交量放大
        if (current_price > recent_high * (1 + breakout_threshold) and 
            current_volume > avg_volume * volume_multiplier and
            rsi < 70):
            
            price_momentum = (current_price - recent_high) / recent_high
            volume_strength = current_volume / avg_volume
            confidence = min(0.95, 0.6 + price_momentum * 5 + (volume_strength - 1) * 0.1)
            
            return StrategyResult(
                signal=SignalType.BUY,
                confidence=confidence,
                price=current_price,
                reason=f"突破买入：价格突破{breakout_threshold*100:.1f}%，放量{volume_strength:.1f}倍",
                indicators={
                    'breakout_level': recent_high,
                    'price_momentum': price_momentum,
                    'volume_ratio': volume_strength,
                    'rsi': rsi
                }
            )
        
        # 卖出信号：价格跌破近期低点
        elif (current_price < recent_low * (1 - breakout_threshold) and
              rsi > 30):
            
            price_decline = (recent_low - current_price) / recent_low
            confidence = min(0.90, 0.6 + price_decline * 5)
            
            return StrategyResult(
                signal=SignalType.SELL,
                confidence=confidence,
                price=current_price,
                reason=f"跌破卖出：价格跌破支撑{breakout_threshold*100:.1f}%",
                indicators={
                    'breakdown_level': recent_low,
                    'price_decline': price_decline,
                    'rsi': rsi
                }
            )
        
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=current_price,
            reason="无明确突破信号",
            indicators={
                'recent_high': recent_high,
                'recent_low': recent_low,
                'rsi': rsi
            }
        )
        
    except Exception as e:
        logger.error(f"动量突破策略执行失败: {e}")
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason=f"策略执行错误: {e}",
            indicators={}
        )

def mean_reversion_strategy(data: pd.DataFrame, **params) -> StrategyResult:
    """
    均线反转策略 - 基于真实数据的实现
    
    基于移动平均线的反转交易策略，适用于横盘震荡市场。
    通过识别价格在均线附近的反转信号来捕获短期波动收益。
    """
    if len(data) < 30:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason="数据不足",
            indicators={}
        )
    
    try:
        close = data['Close']
        volume = data['Volume']
        
        current_price = close.iloc[-1]
        
        # 计算多条移动平均线
        ma_periods = params.get('ma_periods', [5, 10, 20, 50])
        mas = {}
        for period in ma_periods:
            if len(close) >= period:
                mas[f'ma_{period}'] = calculate_sma(close, period).iloc[-1]
        
        # 计算MACD
        macd_data = calculate_macd(close)
        current_macd = macd_data['macd'].iloc[-1]
        macd_signal = macd_data['signal'].iloc[-1]
        
        # 偏离阈值
        deviation_threshold = params.get('deviation_threshold', 0.015)
        
        # 检测均线支撑/阻力
        support_levels = []
        resistance_levels = []
        
        for ma_name, ma_value in mas.items():
            if current_price < ma_value * (1 - deviation_threshold):
                support_levels.append(ma_value)
            elif current_price > ma_value * (1 + deviation_threshold):
                resistance_levels.append(ma_value)
        
        # 买入信号：价格接近重要支撑且MACD向上
        if (support_levels and 
            current_macd > macd_signal and 
            len(support_levels) >= 2):  # 多条均线支撑
            
            nearest_support = max(support_levels)
            deviation = abs(current_price - nearest_support) / nearest_support
            confidence = min(0.85, 0.7 - deviation * 10)  # 越接近支撑置信度越高
            
            return StrategyResult(
                signal=SignalType.BUY,
                confidence=confidence,
                price=current_price,
                reason=f"均线支撑反弹：{len(support_levels)}条均线支撑，MACD向上",
                indicators={
                    'support_level': nearest_support,
                    'deviation': deviation,
                    'macd': current_macd,
                    'support_count': len(support_levels)
                }
            )
        
        # 卖出信号：价格触及重要阻力且MACD向下
        elif (resistance_levels and 
              current_macd < macd_signal and 
              len(resistance_levels) >= 2):  # 多条均线阻力
            
            nearest_resistance = min(resistance_levels)
            deviation = (current_price - nearest_resistance) / nearest_resistance
            confidence = min(0.80, 0.65 + deviation * 10)
            
            return StrategyResult(
                signal=SignalType.SELL,
                confidence=confidence,
                price=current_price,
                reason=f"均线阻力反转：{len(resistance_levels)}条均线阻力，MACD向下",
                indicators={
                    'resistance_level': nearest_resistance,
                    'deviation': deviation,
                    'macd': current_macd,
                    'resistance_count': len(resistance_levels)
                }
            )
        
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=current_price,
            reason="无明确反转信号",
            indicators={
                'mas': mas,
                'macd': current_macd
            }
        )
        
    except Exception as e:
        logger.error(f"均线反转策略执行失败: {e}")
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason=f"策略执行错误: {e}",
            indicators={}
        )

def volume_confirmation_strategy(data: pd.DataFrame, **params) -> StrategyResult:
    """
    成交量确认策略 - 基于真实数据的实现
    
    基于成交量分析的交易策略，通过识别成交量异常和价量配合来发现交易机会。
    适用于捕获主力资金进出动作和市场情绪变化。
    """
    if len(data) < 30:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason="数据不足",
            indicators={}
        )
    
    try:
        close = data['Close']
        volume = data['Volume']
        
        current_price = close.iloc[-1]
        current_volume = volume.iloc[-1]
        
        # 成交量参数
        volume_ma_period = params.get('volume_ma_period', 20)
        volume_surge_ratio = params.get('volume_surge_ratio', 2.0)
        price_volume_periods = params.get('price_volume_periods', 10)
        
        # 计算成交量均线
        volume_ma = calculate_sma(volume, volume_ma_period).iloc[-1]
        
        # 计算价格变化
        price_change = (current_price - close.iloc[-2]) / close.iloc[-2]
        
        # 计算OBV（能量潮）
        obv = []
        obv_value = 0
        for i in range(1, len(data)):
            if close.iloc[i] > close.iloc[i-1]:
                obv_value += volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv_value -= volume.iloc[i]
            obv.append(obv_value)
        
        current_obv = obv[-1]
        prev_obv = obv[-2] if len(obv) > 1 else current_obv
        obv_change = current_obv - prev_obv
        
        # 计算价量配合度
        recent_data = data.iloc[-price_volume_periods:]
        price_changes = recent_data['Close'].pct_change().dropna()
        volume_changes = recent_data['Volume'].pct_change().dropna()
        
        if len(price_changes) > 0 and len(volume_changes) > 0:
            correlation = np.corrcoef(price_changes, volume_changes)[0, 1]
            if np.isnan(correlation):
                correlation = 0
        else:
            correlation = 0
        
        # 成交量放大信号
        volume_ratio = current_volume / volume_ma
        
        # 买入信号：价格上涨 + 成交量放大 + 价量配合
        if (price_change > 0.01 and  # 价格上涨1%以上
            volume_ratio > volume_surge_ratio and  # 成交量放大
            obv_change > 0 and  # OBV上升
            correlation > 0.3):  # 价量正相关
            
            confidence = min(0.90, 0.6 + 
                           price_change * 10 + 
                           (volume_ratio - 1) * 0.1 + 
                           correlation * 0.2)
            
            return StrategyResult(
                signal=SignalType.BUY,
                confidence=confidence,
                price=current_price,
                reason=f"量价配合买入：涨{price_change*100:.1f}%，放量{volume_ratio:.1f}倍",
                indicators={
                    'price_change': price_change,
                    'volume_ratio': volume_ratio,
                    'obv_change': obv_change,
                    'price_volume_correlation': correlation
                }
            )
        
        # 卖出信号：价格下跌 + 成交量放大 + 价量背离
        elif (price_change < -0.01 and  # 价格下跌1%以上
              volume_ratio > volume_surge_ratio and  # 成交量放大
              obv_change < 0):  # OBV下降
            
            confidence = min(0.85, 0.6 + 
                           abs(price_change) * 10 + 
                           (volume_ratio - 1) * 0.1)
            
            return StrategyResult(
                signal=SignalType.SELL,
                confidence=confidence,
                price=current_price,
                reason=f"放量下跌卖出：跌{abs(price_change)*100:.1f}%，放量{volume_ratio:.1f}倍",
                indicators={
                    'price_change': price_change,
                    'volume_ratio': volume_ratio,
                    'obv_change': obv_change,
                    'price_volume_correlation': correlation
                }
            )
        
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=current_price,
            reason="无明确量价信号",
            indicators={
                'volume_ratio': volume_ratio,
                'price_change': price_change,
                'obv_change': obv_change
            }
        )
        
    except Exception as e:
        logger.error(f"成交量确认策略执行失败: {e}")
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason=f"策略执行错误: {e}",
            indicators={}
        )

# 技术指标计算函数
def calculate_sma(data: pd.Series, window: int) -> pd.Series:
    """计算简单移动平均"""
    return data.rolling(window=window).mean()

def calculate_ema(data: pd.Series, window: int) -> pd.Series:
    """计算指数移动平均"""
    return data.ewm(span=window).mean()

def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    """计算RSI指标"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """计算MACD指标"""
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

def calculate_bollinger_bands(data: pd.Series, window: int = 20, std_dev: float = 2) -> Dict:
    """计算布林带"""
    sma = calculate_sma(data, window)
    std = data.rolling(window=window).std()
    
    return {
        'upper': sma + (std * std_dev),
        'middle': sma,
        'lower': sma - (std * std_dev)
    }

# 内置策略函数
def ma_cross_strategy(data: pd.DataFrame, fast: int = 10, slow: int = 20) -> StrategyResult:
    """
    移动平均交叉策略
    
    Args:
        data: 股票数据
        fast: 快线周期
        slow: 慢线周期
        
    Returns:
        策略结果
    """
    if len(data) < slow:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason="数据不足",
            indicators={}
        )
    
    close = data['Close']
    fast_ma = calculate_sma(close, fast)
    slow_ma = calculate_sma(close, slow)
    
    current_fast = fast_ma.iloc[-1]
    current_slow = slow_ma.iloc[-1]
    prev_fast = fast_ma.iloc[-2]
    prev_slow = slow_ma.iloc[-2]
    
    current_price = close.iloc[-1]
    
    # 判断交叉
    if current_fast > current_slow and prev_fast <= prev_slow:
        # 金叉
        signal = SignalType.BUY
        confidence = min(0.8, (current_fast - current_slow) / current_slow)
        reason = f"金叉信号：快线({fast})上穿慢线({slow})"
    elif current_fast < current_slow and prev_fast >= prev_slow:
        # 死叉
        signal = SignalType.SELL
        confidence = min(0.8, (current_slow - current_fast) / current_slow)
        reason = f"死叉信号：快线({fast})下穿慢线({slow})"
    else:
        signal = SignalType.HOLD
        confidence = 0.0
        reason = "无交叉信号"
    
    return StrategyResult(
        signal=signal,
        confidence=confidence,
        price=current_price,
        reason=reason,
        indicators={
            'fast_ma': current_fast,
            'slow_ma': current_slow,
            'fast_period': fast,
            'slow_period': slow
        }
    )

def rsi_strategy(data: pd.DataFrame, period: int = 14, oversold: float = 30, overbought: float = 70) -> StrategyResult:
    """
    RSI策略
    
    Args:
        data: 股票数据
        period: RSI周期
        oversold: 超卖阈值
        overbought: 超买阈值
        
    Returns:
        策略结果
    """
    if len(data) < period + 1:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason="数据不足",
            indicators={}
        )
    
    close = data['Close']
    rsi = calculate_rsi(close, period)
    
    current_rsi = rsi.iloc[-1]
    current_price = close.iloc[-1]
    
    if current_rsi < oversold:
        signal = SignalType.BUY
        confidence = min(0.9, (oversold - current_rsi) / oversold)
        reason = f"RSI超卖信号：{current_rsi:.1f} < {oversold}"
    elif current_rsi > overbought:
        signal = SignalType.SELL
        confidence = min(0.9, (current_rsi - overbought) / (100 - overbought))
        reason = f"RSI超买信号：{current_rsi:.1f} > {overbought}"
    else:
        signal = SignalType.HOLD
        confidence = 0.0
        reason = f"RSI正常：{current_rsi:.1f}"
    
    return StrategyResult(
        signal=signal,
        confidence=confidence,
        price=current_price,
        reason=reason,
        indicators={
            'rsi': current_rsi,
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        }
    )

def macd_strategy(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal_period: int = 9) -> StrategyResult:
    """
    MACD策略
    
    Args:
        data: 股票数据
        fast: 快线周期
        slow: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        策略结果
    """
    if len(data) < slow + signal_period:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason="数据不足",
            indicators={}
        )
    
    close = data['Close']
    macd_data = calculate_macd(close, fast, slow, signal_period)
    
    current_macd = macd_data['macd'].iloc[-1]
    current_signal = macd_data['signal'].iloc[-1]
    current_histogram = macd_data['histogram'].iloc[-1]
    prev_histogram = macd_data['histogram'].iloc[-2]
    
    current_price = close.iloc[-1]
    
    # MACD信号判断
    if current_histogram > 0 and prev_histogram <= 0:
        # MACD金叉
        signal = SignalType.BUY
        confidence = min(0.8, abs(current_histogram) / current_price * 1000)
        reason = "MACD金叉信号"
    elif current_histogram < 0 and prev_histogram >= 0:
        # MACD死叉
        signal = SignalType.SELL
        confidence = min(0.8, abs(current_histogram) / current_price * 1000)
        reason = "MACD死叉信号"
    else:
        signal = SignalType.HOLD
        confidence = 0.0
        reason = "MACD无明确信号"
    
    return StrategyResult(
        signal=signal,
        confidence=confidence,
        price=current_price,
        reason=reason,
        indicators={
            'macd': current_macd,
            'signal': current_signal,
            'histogram': current_histogram,
            'fast': fast,
            'slow': slow,
            'signal_period': signal_period
        }
    )

def bollinger_bands_strategy(data: pd.DataFrame, window: int = 20, std_dev: float = 2) -> StrategyResult:
    """
    布林带策略
    
    Args:
        data: 股票数据
        window: 移动平均窗口
        std_dev: 标准差倍数
        
    Returns:
        策略结果
    """
    if len(data) < window:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1],
            reason="数据不足",
            indicators={}
        )
    
    close = data['Close']
    bb = calculate_bollinger_bands(close, window, std_dev)
    
    current_price = close.iloc[-1]
    current_upper = bb['upper'].iloc[-1]
    current_lower = bb['lower'].iloc[-1]
    current_middle = bb['middle'].iloc[-1]
    
    # 布林带位置判断
    bb_position = (current_price - current_lower) / (current_upper - current_lower)
    
    if current_price <= current_lower:
        signal = SignalType.BUY
        confidence = min(0.8, (current_lower - current_price) / current_price)
        reason = f"价格触及下轨：{current_price:.2f} <= {current_lower:.2f}"
    elif current_price >= current_upper:
        signal = SignalType.SELL
        confidence = min(0.8, (current_price - current_upper) / current_price)
        reason = f"价格触及上轨：{current_price:.2f} >= {current_upper:.2f}"
    else:
        signal = SignalType.HOLD
        confidence = 0.0
        reason = f"价格在布林带内：位置{bb_position:.2%}"
    
    return StrategyResult(
        signal=signal,
        confidence=confidence,
        price=current_price,
        reason=reason,
        indicators={
            'upper': current_upper,
            'middle': current_middle,
            'lower': current_lower,
            'position': bb_position,
            'window': window,
            'std_dev': std_dev
        }
    )

# 组合策略
def multi_strategy(data: pd.DataFrame, strategies: List[Strategy], weights: List[float] = None) -> StrategyResult:
    """
    多策略组合
    
    Args:
        data: 股票数据
        strategies: 策略列表
        weights: 策略权重
        
    Returns:
        组合策略结果
    """
    if not strategies:
        return StrategyResult(
            signal=SignalType.HOLD,
            confidence=0.0,
            price=data['Close'].iloc[-1] if not data.empty else 0.0,
            reason="无策略",
            indicators={}
        )
    
    if weights is None:
        weights = [1.0 / len(strategies)] * len(strategies)
    
    if len(weights) != len(strategies):
        raise ValueError("策略数量与权重数量不匹配")
    
    # 获取所有策略结果
    results = []
    for strategy in strategies:
        result = strategy.generate_signal(data)
        results.append(result)
    
    # 计算加权信号
    buy_score = 0.0
    sell_score = 0.0
    total_confidence = 0.0
    
    for result, weight in zip(results, weights):
        weighted_confidence = result.confidence * weight
        total_confidence += weighted_confidence
        
        if result.signal == SignalType.BUY:
            buy_score += weighted_confidence
        elif result.signal == SignalType.SELL:
            sell_score += weighted_confidence
    
    # 决定最终信号
    if buy_score > sell_score and buy_score > 0.3:
        final_signal = SignalType.BUY
        final_confidence = buy_score
        reason = f"多策略买入：买入分数{buy_score:.2f} > 卖出分数{sell_score:.2f}"
    elif sell_score > buy_score and sell_score > 0.3:
        final_signal = SignalType.SELL
        final_confidence = sell_score
        reason = f"多策略卖出：卖出分数{sell_score:.2f} > 买入分数{buy_score:.2f}"
    else:
        final_signal = SignalType.HOLD
        final_confidence = 0.0
        reason = f"多策略无明确信号：买入{buy_score:.2f}，卖出{sell_score:.2f}"
    
    return StrategyResult(
        signal=final_signal,
        confidence=final_confidence,
        price=data['Close'].iloc[-1],
        reason=reason,
        indicators={
            'buy_score': buy_score,
            'sell_score': sell_score,
            'strategy_count': len(strategies),
            'individual_results': [r.reason for r in results]
        }
    )

# 策略工厂函数
def create_strategy(name: str, params: Dict = None) -> Strategy:
    """
    创建预定义策略
    
    Args:
        name: 策略名称
        params: 策略参数
        
    Returns:
        策略对象
    """
    strategy_map = {
        # 现有组合策略（优先使用）
        'MomentumBreakout': momentum_breakout_strategy,
        'MeanReversion': mean_reversion_strategy,
        'VolumeConfirmation': volume_confirmation_strategy,
        
        # 基础技术分析策略（保留作为备用）
        'MA_Cross': ma_cross_strategy,
        'RSI': rsi_strategy,
        'MACD': macd_strategy,
        'BollingerBands': bollinger_bands_strategy
    }
    
    if name not in strategy_map:
        available = list(strategy_map.keys())
        raise ValueError(f"未知策略：{name}，可用策略：{available}")
    
    return Strategy(name, strategy_map[name], params)

# 便捷函数
def get_available_strategies() -> List[str]:
    """获取可用策略列表"""
    return ['MomentumBreakout', 'MeanReversion', 'VolumeConfirmation', 'MA_Cross', 'RSI', 'MACD', 'BollingerBands']

def create_multi_strategy(strategy_names: List[str], weights: List[float] = None) -> Callable:
    """
    创建多策略组合函数
    
    Args:
        strategy_names: 策略名称列表
        weights: 策略权重
        
    Returns:
        组合策略函数
    """
    strategies = [create_strategy(name) for name in strategy_names]
    
    def combined_strategy(data: pd.DataFrame) -> StrategyResult:
        return multi_strategy(data, strategies, weights)
    
    return combined_strategy

# 使用示例和测试
if __name__ == "__main__":
    print("🚀 简化策略模块测试")
    print("=" * 50)
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    # 生成模拟股价数据
    prices = [100]
    for _ in range(99):
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 50))  # 防止价格过低
    
    test_data = pd.DataFrame({
        'Open': prices,
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    print(f"📊 测试数据生成完成：{len(test_data)}条记录")
    print(f"   价格范围：${test_data['Close'].min():.2f} - ${test_data['Close'].max():.2f}")
    
    # 测试单个策略
    print("\n🔧 测试单个策略...")
    
    strategies_to_test = [
        ('MA_Cross', {'fast': 5, 'slow': 20}),
        ('RSI', {'period': 14, 'oversold': 30, 'overbought': 70}),
        ('MACD', {'fast': 12, 'slow': 26, 'signal_period': 9}),
        ('BollingerBands', {'window': 20, 'std_dev': 2})
    ]
    
    for strategy_name, params in strategies_to_test:
        try:
            strategy = create_strategy(strategy_name, params)
            result = strategy.generate_signal(test_data)
            
            print(f"✅ {strategy_name}: {result.signal.value} "
                  f"(置信度: {result.confidence:.2f}) - {result.reason}")
            
        except Exception as e:
            print(f"❌ {strategy_name}: 测试失败 - {e}")
    
    # 测试多策略组合
    print("\n🎯 测试多策略组合...")
    try:
        strategy_names = ['MA_Cross', 'RSI', 'MACD']
        weights = [0.4, 0.3, 0.3]
        
        strategies = [create_strategy(name) for name in strategy_names]
        combined_result = multi_strategy(test_data, strategies, weights)
        
        print(f"✅ 多策略组合: {combined_result.signal.value} "
              f"(置信度: {combined_result.confidence:.2f})")
        print(f"   {combined_result.reason}")
        
    except Exception as e:
        print(f"❌ 多策略组合测试失败：{e}")
    
    # 测试便捷函数
    print("\n🛠️ 测试便捷函数...")
    available = get_available_strategies()
    print(f"✅ 可用策略：{', '.join(available)}")
    
    print("\n" + "=" * 50)
    print("🎯 简化策略模块核心特性：")
    print("  ✅ 函数式设计 - 策略就是函数，简单直观")
    print("  ✅ 内置策略 - 提供4种常用技术分析策略")
    print("  ✅ 参数化 - 所有策略都支持参数自定义")
    print("  ✅ 组合策略 - 支持多策略加权组合")
    print("  ✅ 置信度 - 每个信号都有置信度评分")
    print("=" * 50)