"""
趋势分析模型

提供高级趋势识别和分析功能：
1. 趋势检测算法
2. 趋势强度分析
3. 趋势转折点识别
4. 多时间框架趋势分析
5. 趋势预测模型
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import warnings

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from scipy import stats
    from scipy.signal import find_peaks, argrelextrema
    SCIPY_SKLEARN_AVAILABLE = True
except ImportError:
    SCIPY_SKLEARN_AVAILABLE = False
    warnings.warn("scipy and scikit-learn not available, some trend analysis features will be limited")

from . import ModelPrediction, PredictionType


class TrendDirection(Enum):
    """趋势方向"""
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class TrendStrength(Enum):
    """趋势强度"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class TrendTimeframe(Enum):
    """趋势时间框架"""
    SHORT_TERM = "short_term"      # 1-5 天
    MEDIUM_TERM = "medium_term"    # 5-20 天
    LONG_TERM = "long_term"        # 20+ 天


@dataclass
class TrendPoint:
    """趋势点"""
    timestamp: datetime
    price: float
    point_type: str  # 'peak', 'valley', 'support', 'resistance'
    significance: float  # 0-1，重要性评分
    volume: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'point_type': self.point_type,
            'significance': self.significance,
            'volume': self.volume
        }


@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    symbol: str
    timeframe: TrendTimeframe
    direction: TrendDirection
    strength: TrendStrength
    confidence: float
    start_date: datetime
    end_date: datetime
    slope: float
    r_squared: float
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    trend_points: List[TrendPoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe.value,
            'direction': self.direction.value,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'slope': self.slope,
            'r_squared': self.r_squared,
            'support_levels': self.support_levels,
            'resistance_levels': self.resistance_levels,
            'trend_points': [tp.to_dict() for tp in self.trend_points],
            'metadata': self.metadata
        }


class TrendDetector:
    """趋势检测器"""
    
    def __init__(self):
        self.scaler = StandardScaler() if SCIPY_SKLEARN_AVAILABLE else None
    
    def detect_linear_trend(self, data: pd.Series, min_periods: int = 10) -> TrendAnalysis:
        """线性趋势检测"""
        if len(data) < min_periods:
            return self._create_unknown_trend(data)
        
        # 准备数据
        x = np.arange(len(data))
        y = data.values
        
        if SCIPY_SKLEARN_AVAILABLE:
            # 线性回归
            model = LinearRegression()
            model.fit(x.reshape(-1, 1), y)
            
            # 计算R²
            y_pred = model.predict(x.reshape(-1, 1))
            r_squared = stats.pearsonr(y, y_pred)[0] ** 2
            slope = model.coef_[0]
        else:
            # 简单线性回归
            slope = np.polyfit(x, y, 1)[0]
            r_squared = np.corrcoef(x, y)[0, 1] ** 2
        
        # 判断趋势方向
        direction = self._classify_trend_direction(slope, r_squared)
        
        # 计算趋势强度
        strength = self._calculate_trend_strength(slope, r_squared, data)
        
        # 计算置信度
        confidence = min(r_squared, 1.0)
        
        # 确定时间框架
        timeframe = self._determine_timeframe(len(data))
        
        return TrendAnalysis(
            symbol=getattr(data, 'name', 'UNKNOWN'),
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            confidence=confidence,
            start_date=data.index[0] if hasattr(data.index[0], 'to_pydatetime') else datetime.now(),
            end_date=data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now(),
            slope=slope,
            r_squared=r_squared,
            metadata={'method': 'linear_regression', 'periods': len(data)}
        )
    
    def detect_moving_average_trend(self, data: pd.Series, 
                                  short_window: int = 20,
                                  long_window: int = 50) -> TrendAnalysis:
        """移动平均趋势检测"""
        if len(data) < long_window:
            return self._create_unknown_trend(data)
        
        # 计算移动平均
        short_ma = data.rolling(window=short_window).mean()
        long_ma = data.rolling(window=long_window).mean()
        
        # 最新的移动平均值
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        current_price = data.iloc[-1]
        
        # 趋势方向判断
        if current_short > current_long and current_price > current_short:
            direction = TrendDirection.UPTREND
        elif current_short < current_long and current_price < current_short:
            direction = TrendDirection.DOWNTREND
        else:
            direction = TrendDirection.SIDEWAYS
        
        # 计算趋势强度（基于MA分离度和价格位置）
        ma_separation = abs(current_short - current_long) / current_long
        price_position = (current_price - min(current_short, current_long)) / abs(current_short - current_long) if current_short != current_long else 0.5
        
        strength = self._calculate_ma_trend_strength(ma_separation, price_position)
        
        # 置信度（基于MA的一致性）
        ma_diff_trend = (short_ma - long_ma).tail(10)
        consistency = len(ma_diff_trend[ma_diff_trend * ma_diff_trend.iloc[-1] > 0]) / len(ma_diff_trend)
        confidence = consistency
        
        timeframe = self._determine_timeframe(len(data))
        
        return TrendAnalysis(
            symbol=getattr(data, 'name', 'UNKNOWN'),
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            confidence=confidence,
            start_date=data.index[0] if hasattr(data.index[0], 'to_pydatetime') else datetime.now(),
            end_date=data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now(),
            slope=ma_separation,
            r_squared=consistency,
            metadata={
                'method': 'moving_average',
                'short_window': short_window,
                'long_window': long_window,
                'ma_separation': ma_separation
            }
        )
    
    def detect_zigzag_trend(self, data: pd.Series, threshold: float = 0.05) -> TrendAnalysis:
        """ZigZag趋势检测"""
        if len(data) < 10:
            return self._create_unknown_trend(data)
        
        # 简化的ZigZag实现
        zigzag_points = self._calculate_zigzag(data, threshold)
        
        if len(zigzag_points) < 3:
            return self._create_unknown_trend(data)
        
        # 分析最近的趋势
        recent_points = zigzag_points[-3:]
        trend_changes = []
        
        for i in range(1, len(recent_points)):
            change = (recent_points[i][1] - recent_points[i-1][1]) / recent_points[i-1][1]
            trend_changes.append(change)
        
        # 判断总体趋势
        avg_change = np.mean(trend_changes)
        
        if avg_change > threshold:
            direction = TrendDirection.UPTREND
        elif avg_change < -threshold:
            direction = TrendDirection.DOWNTREND
        else:
            direction = TrendDirection.SIDEWAYS
        
        # 趋势强度基于变化幅度
        strength = self._calculate_zigzag_strength(trend_changes, threshold)
        
        # 置信度基于一致性
        confidence = self._calculate_zigzag_confidence(trend_changes)
        
        timeframe = self._determine_timeframe(len(data))
        
        # 创建趋势点
        trend_points = []
        for i, (idx, price) in enumerate(zigzag_points):
            point_type = 'peak' if i % 2 == 0 else 'valley'
            significance = min(abs(trend_changes[i-1]) / threshold, 1.0) if i > 0 else 0.5
            
            trend_points.append(TrendPoint(
                timestamp=data.index[idx] if hasattr(data.index[idx], 'to_pydatetime') else datetime.now(),
                price=price,
                point_type=point_type,
                significance=significance
            ))
        
        return TrendAnalysis(
            symbol=getattr(data, 'name', 'UNKNOWN'),
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            confidence=confidence,
            start_date=data.index[0] if hasattr(data.index[0], 'to_pydatetime') else datetime.now(),
            end_date=data.index[-1] if hasattr(data.index[-1], 'to_pydatetime') else datetime.now(),
            slope=avg_change,
            r_squared=confidence,
            trend_points=trend_points,
            metadata={'method': 'zigzag', 'threshold': threshold, 'zigzag_points': len(zigzag_points)}
        )
    
    def _calculate_zigzag(self, data: pd.Series, threshold: float) -> List[Tuple[int, float]]:
        """计算ZigZag点"""
        points = []
        current_trend = None  # 1 for up, -1 for down
        last_extreme_idx = 0
        last_extreme_value = data.iloc[0]
        
        for i in range(1, len(data)):
            current_value = data.iloc[i]
            change = (current_value - last_extreme_value) / last_extreme_value
            
            if current_trend is None:
                if abs(change) >= threshold:
                    current_trend = 1 if change > 0 else -1
                    points.append((last_extreme_idx, last_extreme_value))
                    last_extreme_idx = i
                    last_extreme_value = current_value
            elif current_trend == 1:  # 上升趋势
                if current_value > last_extreme_value:
                    # 继续上升，更新极值
                    last_extreme_idx = i
                    last_extreme_value = current_value
                elif change <= -threshold:
                    # 趋势反转
                    points.append((last_extreme_idx, last_extreme_value))
                    current_trend = -1
                    last_extreme_idx = i
                    last_extreme_value = current_value
            else:  # 下降趋势
                if current_value < last_extreme_value:
                    # 继续下降，更新极值
                    last_extreme_idx = i
                    last_extreme_value = current_value
                elif change >= threshold:
                    # 趋势反转
                    points.append((last_extreme_idx, last_extreme_value))
                    current_trend = 1
                    last_extreme_idx = i
                    last_extreme_value = current_value
        
        # 添加最后一个点
        points.append((last_extreme_idx, last_extreme_value))
        return points
    
    def _classify_trend_direction(self, slope: float, r_squared: float) -> TrendDirection:
        """分类趋势方向"""
        # 需要足够的拟合度才能确定趋势
        if r_squared < 0.5:
            return TrendDirection.SIDEWAYS
        
        # 基于斜率判断方向
        if slope > 0.001:  # 0.1% 每单位时间
            return TrendDirection.UPTREND
        elif slope < -0.001:
            return TrendDirection.DOWNTREND
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_trend_strength(self, slope: float, r_squared: float, data: pd.Series) -> TrendStrength:
        """计算趋势强度"""
        # 结合斜率大小和拟合度
        slope_magnitude = abs(slope)
        strength_score = slope_magnitude * r_squared
        
        # 考虑波动性
        volatility = data.pct_change().std()
        adjusted_strength = strength_score / max(volatility, 0.001)
        
        if adjusted_strength >= 0.5:
            return TrendStrength.VERY_STRONG
        elif adjusted_strength >= 0.3:
            return TrendStrength.STRONG
        elif adjusted_strength >= 0.1:
            return TrendStrength.MODERATE
        else:
            return TrendStrength.WEAK
    
    def _calculate_ma_trend_strength(self, ma_separation: float, price_position: float) -> TrendStrength:
        """计算移动平均趋势强度"""
        strength_score = ma_separation * abs(price_position - 0.5) * 2
        
        if strength_score >= 0.05:  # 5%
            return TrendStrength.VERY_STRONG
        elif strength_score >= 0.03:
            return TrendStrength.STRONG
        elif strength_score >= 0.01:
            return TrendStrength.MODERATE
        else:
            return TrendStrength.WEAK
    
    def _calculate_zigzag_strength(self, trend_changes: List[float], threshold: float) -> TrendStrength:
        """计算ZigZag趋势强度"""
        avg_magnitude = np.mean([abs(change) for change in trend_changes])
        
        if avg_magnitude >= threshold * 3:
            return TrendStrength.VERY_STRONG
        elif avg_magnitude >= threshold * 2:
            return TrendStrength.STRONG
        elif avg_magnitude >= threshold * 1.5:
            return TrendStrength.MODERATE
        else:
            return TrendStrength.WEAK
    
    def _calculate_zigzag_confidence(self, trend_changes: List[float]) -> float:
        """计算ZigZag趋势置信度"""
        if not trend_changes:
            return 0.0
        
        # 基于变化方向的一致性
        positive_changes = sum(1 for change in trend_changes if change > 0)
        negative_changes = sum(1 for change in trend_changes if change < 0)
        total_changes = len(trend_changes)
        
        consistency = max(positive_changes, negative_changes) / total_changes
        return consistency
    
    def _determine_timeframe(self, periods: int) -> TrendTimeframe:
        """确定时间框架"""
        if periods <= 5:
            return TrendTimeframe.SHORT_TERM
        elif periods <= 20:
            return TrendTimeframe.MEDIUM_TERM
        else:
            return TrendTimeframe.LONG_TERM
    
    def _create_unknown_trend(self, data: pd.Series) -> TrendAnalysis:
        """创建未知趋势分析"""
        return TrendAnalysis(
            symbol=getattr(data, 'name', 'UNKNOWN'),
            timeframe=TrendTimeframe.SHORT_TERM,
            direction=TrendDirection.UNKNOWN,
            strength=TrendStrength.WEAK,
            confidence=0.0,
            start_date=data.index[0] if len(data) > 0 and hasattr(data.index[0], 'to_pydatetime') else datetime.now(),
            end_date=data.index[-1] if len(data) > 0 and hasattr(data.index[-1], 'to_pydatetime') else datetime.now(),
            slope=0.0,
            r_squared=0.0,
            metadata={'method': 'insufficient_data', 'periods': len(data)}
        )


class SupportResistanceDetector:
    """支撑阻力位检测器"""
    
    def __init__(self):
        pass
    
    def detect_levels(self, data: pd.Series, window: int = 20,
                     min_touches: int = 2) -> Tuple[List[float], List[float]]:
        """检测支撑和阻力位"""
        if len(data) < window * 2:
            return [], []
        
        # 寻找局部极值
        highs, lows = self._find_local_extrema(data, window)
        
        # 聚类相近的价格水平
        support_levels = self._cluster_levels(lows, data, min_touches)
        resistance_levels = self._cluster_levels(highs, data, min_touches)
        
        return support_levels, resistance_levels
    
    def _find_local_extrema(self, data: pd.Series, window: int) -> Tuple[List[float], List[float]]:
        """寻找局部极值"""
        if SCIPY_SKLEARN_AVAILABLE:
            # 使用scipy寻找峰值和谷值
            highs_idx = argrelextrema(data.values, np.greater, order=window)[0]
            lows_idx = argrelextrema(data.values, np.less, order=window)[0]
            
            highs = data.iloc[highs_idx].tolist()
            lows = data.iloc[lows_idx].tolist()
        else:
            # 简单的滑动窗口方法
            highs = []
            lows = []
            
            for i in range(window, len(data) - window):
                window_data = data.iloc[i-window:i+window+1]
                current_price = data.iloc[i]
                
                if current_price == window_data.max():
                    highs.append(current_price)
                elif current_price == window_data.min():
                    lows.append(current_price)
        
        return highs, lows
    
    def _cluster_levels(self, prices: List[float], data: pd.Series,
                       min_touches: int) -> List[float]:
        """聚类价格水平"""
        if not prices or len(prices) < min_touches:
            return []
        
        if SCIPY_SKLEARN_AVAILABLE and len(prices) >= 2:
            # 使用K-means聚类
            price_array = np.array(prices).reshape(-1, 1)
            
            # 动态确定聚类数量
            n_clusters = min(len(prices) // min_touches, 5)
            if n_clusters < 1:
                return []
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(price_array)
            
            # 筛选有足够触碰次数的聚类
            levels = []
            for i in range(n_clusters):
                cluster_prices = [prices[j] for j, c in enumerate(clusters) if c == i]
                if len(cluster_prices) >= min_touches:
                    levels.append(np.mean(cluster_prices))
            
            return sorted(levels)
        else:
            # 简单的价格区间聚类
            levels = []
            price_range = data.max() - data.min()
            tolerance = price_range * 0.02  # 2% tolerance
            
            sorted_prices = sorted(prices)
            current_group = [sorted_prices[0]]
            
            for price in sorted_prices[1:]:
                if price - current_group[-1] <= tolerance:
                    current_group.append(price)
                else:
                    if len(current_group) >= min_touches:
                        levels.append(np.mean(current_group))
                    current_group = [price]
            
            # 检查最后一组
            if len(current_group) >= min_touches:
                levels.append(np.mean(current_group))
            
            return levels


class TrendAnalysisEngine:
    """趋势分析引擎"""
    
    def __init__(self):
        self.trend_detector = TrendDetector()
        self.support_resistance_detector = SupportResistanceDetector()
    
    def comprehensive_trend_analysis(self, data: pd.Series,
                                   symbol: str = None) -> Dict[str, TrendAnalysis]:
        """综合趋势分析"""
        if symbol:
            data.name = symbol
        
        results = {}
        
        # 线性趋势分析
        results['linear'] = self.trend_detector.detect_linear_trend(data)
        
        # 移动平均趋势分析
        results['moving_average'] = self.trend_detector.detect_moving_average_trend(data)
        
        # ZigZag趋势分析
        results['zigzag'] = self.trend_detector.detect_zigzag_trend(data)
        
        # 添加支撑阻力位
        support_levels, resistance_levels = self.support_resistance_detector.detect_levels(data)
        
        for analysis in results.values():
            analysis.support_levels = support_levels
            analysis.resistance_levels = resistance_levels
        
        return results
    
    def multi_timeframe_analysis(self, data: pd.DataFrame,
                                price_column: str = 'close',
                                timeframes: List[int] = None) -> Dict[str, Dict[str, TrendAnalysis]]:
        """多时间框架趋势分析"""
        if timeframes is None:
            timeframes = [5, 20, 50]
        
        results = {}
        
        for tf in timeframes:
            if len(data) >= tf:
                # 重采样到指定时间框架
                tf_data = data[price_column].rolling(tf).mean().dropna()
                
                if len(tf_data) > 10:  # 确保有足够数据
                    tf_data.name = f"{getattr(data[price_column], 'name', 'UNKNOWN')}_{tf}D"
                    results[f'{tf}D'] = self.comprehensive_trend_analysis(tf_data)
        
        return results
    
    def generate_trend_signals(self, analysis: TrendAnalysis) -> List[str]:
        """生成趋势信号"""
        signals = []
        
        # 基于趋势方向和强度的信号
        if analysis.direction == TrendDirection.UPTREND:
            if analysis.strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
                signals.append("STRONG_BUY")
            elif analysis.strength == TrendStrength.MODERATE:
                signals.append("BUY")
            else:
                signals.append("WEAK_BUY")
        elif analysis.direction == TrendDirection.DOWNTREND:
            if analysis.strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
                signals.append("STRONG_SELL")
            elif analysis.strength == TrendStrength.MODERATE:
                signals.append("SELL")
            else:
                signals.append("WEAK_SELL")
        else:
            signals.append("HOLD")
        
        # 基于置信度的信号修正
        if analysis.confidence < 0.5:
            signals.append("LOW_CONFIDENCE")
        elif analysis.confidence > 0.8:
            signals.append("HIGH_CONFIDENCE")
        
        # 支撑阻力位信号
        if analysis.support_levels:
            signals.append("SUPPORT_DETECTED")
        if analysis.resistance_levels:
            signals.append("RESISTANCE_DETECTED")
        
        return signals


# 导出
__all__ = [
    'TrendDirection', 'TrendStrength', 'TrendTimeframe',
    'TrendPoint', 'TrendAnalysis', 'TrendDetector',
    'SupportResistanceDetector', 'TrendAnalysisEngine'
]