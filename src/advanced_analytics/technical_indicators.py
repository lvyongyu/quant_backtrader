"""
高级技术指标库

扩展传统技术指标，提供更深入的市场分析能力。
包括趋势、动量、波动率、成交量等多维度指标。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from scipy import stats
from scipy.signal import find_peaks
import talib
import warnings

from . import IndicatorResult, IndicatorType


class AdvancedIndicators:
    """高级技术指标计算器"""
    
    @staticmethod
    def adaptive_moving_average(data: pd.Series, period: int = 14, alpha: float = 2.0) -> pd.Series:
        """自适应移动平均线
        
        Args:
            data: 价格数据
            period: 计算周期
            alpha: 平滑因子
        """
        volatility = data.rolling(period).std()
        efficiency_ratio = (data.diff(period).abs() / 
                          data.diff().abs().rolling(period).sum())
        
        sc = ((efficiency_ratio * (alpha / (alpha + 1) - 2 / (period + 1)) + 
               2 / (period + 1)) ** 2)
        
        ama = pd.Series(index=data.index, dtype=float)
        ama.iloc[0] = data.iloc[0]
        
        for i in range(1, len(data)):
            ama.iloc[i] = ama.iloc[i-1] + sc.iloc[i] * (data.iloc[i] - ama.iloc[i-1])
        
        return ama
    
    @staticmethod
    def price_channel(high: pd.Series, low: pd.Series, period: int = 20) -> Dict[str, pd.Series]:
        """价格通道指标
        
        Args:
            high: 最高价
            low: 最低价
            period: 计算周期
        """
        upper_channel = high.rolling(period).max()
        lower_channel = low.rolling(period).min()
        middle_channel = (upper_channel + lower_channel) / 2
        
        return {
            'upper': upper_channel,
            'middle': middle_channel,
            'lower': lower_channel
        }
    
    @staticmethod
    def vwap_bands(high: pd.Series, low: pd.Series, close: pd.Series, 
                   volume: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """成交量加权平均价格通道
        
        Args:
            high, low, close: 价格数据
            volume: 成交量
            period: 计算周期
            std_dev: 标准差倍数
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).rolling(period).sum() / volume.rolling(period).sum()
        
        # 计算VWAP的标准差
        vwap_std = ((typical_price - vwap) ** 2 * volume).rolling(period).sum()
        vwap_std = np.sqrt(vwap_std / volume.rolling(period).sum())
        
        return {
            'vwap': vwap,
            'upper': vwap + std_dev * vwap_std,
            'lower': vwap - std_dev * vwap_std
        }
    
    @staticmethod
    def money_flow_index(high: pd.Series, low: pd.Series, close: pd.Series, 
                        volume: pd.Series, period: int = 14) -> pd.Series:
        """资金流量指数
        
        Args:
            high, low, close: 价格数据
            volume: 成交量
            period: 计算周期
        """
        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume
        
        # 判断资金流向
        positive_flow = pd.Series(0.0, index=close.index)
        negative_flow = pd.Series(0.0, index=close.index)
        
        price_change = typical_price.diff()
        positive_flow[price_change > 0] = raw_money_flow[price_change > 0]
        negative_flow[price_change < 0] = raw_money_flow[price_change < 0]
        
        # 计算资金比率
        positive_mf = positive_flow.rolling(period).sum()
        negative_mf = negative_flow.rolling(period).sum()
        
        money_ratio = positive_mf / negative_mf
        mfi = 100 - (100 / (1 + money_ratio))
        
        return mfi
    
    @staticmethod
    def chaikin_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, 
                          volume: pd.Series, fast: int = 3, slow: int = 10) -> pd.Series:
        """蔡金振荡器
        
        Args:
            high, low, close: 价格数据
            volume: 成交量
            fast: 快速周期
            slow: 慢速周期
        """
        # 计算累积/派发线
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0)  # 处理high=low的情况
        ad_line = (clv * volume).cumsum()
        
        # 计算快慢EMA的差值
        fast_ema = ad_line.ewm(span=fast).mean()
        slow_ema = ad_line.ewm(span=slow).mean()
        
        return fast_ema - slow_ema
    
    @staticmethod
    def volume_profile(close: pd.Series, volume: pd.Series, bins: int = 50) -> Dict[str, Any]:
        """成交量分布轮廓
        
        Args:
            close: 收盘价
            volume: 成交量
            bins: 价格区间数量
        """
        min_price = close.min()
        max_price = close.max()
        price_bins = np.linspace(min_price, max_price, bins + 1)
        
        # 计算每个价格区间的成交量
        volume_profile = []
        for i in range(len(price_bins) - 1):
            mask = (close >= price_bins[i]) & (close < price_bins[i + 1])
            vol_in_bin = volume[mask].sum()
            volume_profile.append(vol_in_bin)
        
        volume_profile = np.array(volume_profile)
        price_centers = (price_bins[:-1] + price_bins[1:]) / 2
        
        # 找到成交量最大的价格区间（POC - Point of Control）
        poc_index = np.argmax(volume_profile)
        poc_price = price_centers[poc_index]
        
        # 计算价值区域（70%成交量区间）
        total_volume = volume_profile.sum()
        target_volume = total_volume * 0.7
        
        # 从POC开始向两边扩展
        current_volume = volume_profile[poc_index]
        left_idx, right_idx = poc_index, poc_index
        
        while current_volume < target_volume and (left_idx > 0 or right_idx < len(volume_profile) - 1):
            left_vol = volume_profile[left_idx - 1] if left_idx > 0 else 0
            right_vol = volume_profile[right_idx + 1] if right_idx < len(volume_profile) - 1 else 0
            
            if left_vol >= right_vol and left_idx > 0:
                left_idx -= 1
                current_volume += left_vol
            elif right_idx < len(volume_profile) - 1:
                right_idx += 1
                current_volume += right_vol
            else:
                break
        
        value_area_high = price_centers[right_idx]
        value_area_low = price_centers[left_idx]
        
        return {
            'price_levels': price_centers,
            'volume_distribution': volume_profile,
            'poc_price': poc_price,
            'value_area_high': value_area_high,
            'value_area_low': value_area_low,
            'total_volume': total_volume
        }
    
    @staticmethod
    def market_facilitation_index(high: pd.Series, low: pd.Series, volume: pd.Series) -> pd.Series:
        """市场便利指数
        
        Args:
            high, low: 最高价和最低价
            volume: 成交量
        """
        return (high - low) / volume
    
    @staticmethod
    def true_strength_index(close: pd.Series, period1: int = 25, period2: int = 13) -> pd.Series:
        """真实强度指数
        
        Args:
            close: 收盘价
            period1: 第一次平滑周期
            period2: 第二次平滑周期
        """
        price_change = close.diff()
        
        # 双重平滑
        first_smooth = price_change.ewm(span=period1).mean()
        double_smooth = first_smooth.ewm(span=period2).mean()
        
        abs_first_smooth = price_change.abs().ewm(span=period1).mean()
        abs_double_smooth = abs_first_smooth.ewm(span=period2).mean()
        
        tsi = 100 * (double_smooth / abs_double_smooth)
        
        return tsi
    
    @staticmethod
    def ichimoku_cloud(high: pd.Series, low: pd.Series, close: pd.Series,
                      conversion_period: int = 9, base_period: int = 26, 
                      leading_span_b_period: int = 52, displacement: int = 26) -> Dict[str, pd.Series]:
        """一目均衡表
        
        Args:
            high, low, close: 价格数据
            conversion_period: 转换线周期
            base_period: 基准线周期
            leading_span_b_period: 先行线B周期
            displacement: 位移
        """
        # 转换线 (Tenkan-sen)
        conversion_line = (high.rolling(conversion_period).max() + 
                          low.rolling(conversion_period).min()) / 2
        
        # 基准线 (Kijun-sen)
        base_line = (high.rolling(base_period).max() + 
                    low.rolling(base_period).min()) / 2
        
        # 先行线A (Senkou Span A)
        leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)
        
        # 先行线B (Senkou Span B)
        leading_span_b = ((high.rolling(leading_span_b_period).max() + 
                          low.rolling(leading_span_b_period).min()) / 2).shift(displacement)
        
        # 延迟线 (Chikou Span)
        lagging_span = close.shift(-displacement)
        
        return {
            'conversion_line': conversion_line,
            'base_line': base_line,
            'leading_span_a': leading_span_a,
            'leading_span_b': leading_span_b,
            'lagging_span': lagging_span
        }


class TechnicalPatterns:
    """技术形态识别"""
    
    @staticmethod
    def detect_support_resistance(close: pd.Series, window: int = 20, 
                                 min_touches: int = 2) -> Dict[str, List[float]]:
        """检测支撑阻力位
        
        Args:
            close: 收盘价
            window: 检测窗口
            min_touches: 最小触及次数
        """
        # 找到局部最高点和最低点
        highs = []
        lows = []
        
        for i in range(window, len(close) - window):
            if close.iloc[i] == close.iloc[i-window:i+window+1].max():
                highs.append(close.iloc[i])
            if close.iloc[i] == close.iloc[i-window:i+window+1].min():
                lows.append(close.iloc[i])
        
        # 聚类相近的价格水平
        resistance_levels = []
        support_levels = []
        
        if highs:
            resistance_levels = TechnicalPatterns._cluster_levels(highs, min_touches)
        if lows:
            support_levels = TechnicalPatterns._cluster_levels(lows, min_touches)
        
        return {
            'resistance': resistance_levels,
            'support': support_levels
        }
    
    @staticmethod
    def _cluster_levels(levels: List[float], min_touches: int, 
                       tolerance: float = 0.02) -> List[float]:
        """聚类价格水平"""
        if not levels:
            return []
        
        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                current_cluster.append(level)
            else:
                if len(current_cluster) >= min_touches:
                    clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]
        
        if len(current_cluster) >= min_touches:
            clusters.append(sum(current_cluster) / len(current_cluster))
        
        return clusters
    
    @staticmethod
    def detect_chart_patterns(high: pd.Series, low: pd.Series, close: pd.Series,
                            window: int = 20) -> Dict[str, List[Dict[str, Any]]]:
        """检测图表形态
        
        Args:
            high, low, close: 价格数据
            window: 检测窗口
        """
        patterns = {
            'double_top': [],
            'double_bottom': [],
            'head_shoulders': [],
            'triangles': []
        }
        
        # 简化的双顶双底检测
        peaks, _ = find_peaks(high, distance=window//2)
        troughs, _ = find_peaks(-low, distance=window//2)
        
        # 检测双顶
        for i in range(len(peaks) - 1):
            for j in range(i + 1, len(peaks)):
                peak1_idx, peak2_idx = peaks[i], peaks[j]
                peak1_price, peak2_price = high.iloc[peak1_idx], high.iloc[peak2_idx]
                
                # 双顶条件：两个峰值接近，中间有谷底
                if (abs(peak1_price - peak2_price) / peak1_price < 0.05 and
                    peak2_idx - peak1_idx > window):
                    
                    # 找中间的谷底
                    valley_range = range(peak1_idx, peak2_idx + 1)
                    valley_idx = valley_range[np.argmin(low.iloc[valley_range])]
                    
                    patterns['double_top'].append({
                        'start_idx': peak1_idx,
                        'end_idx': peak2_idx,
                        'valley_idx': valley_idx,
                        'peak1_price': peak1_price,
                        'peak2_price': peak2_price,
                        'valley_price': low.iloc[valley_idx],
                        'confidence': 0.8 if abs(peak1_price - peak2_price) / peak1_price < 0.02 else 0.6
                    })
        
        # 检测双底（类似逻辑）
        for i in range(len(troughs) - 1):
            for j in range(i + 1, len(troughs)):
                trough1_idx, trough2_idx = troughs[i], troughs[j]
                trough1_price, trough2_price = low.iloc[trough1_idx], low.iloc[trough2_idx]
                
                if (abs(trough1_price - trough2_price) / trough1_price < 0.05 and
                    trough2_idx - trough1_idx > window):
                    
                    # 找中间的峰顶
                    peak_range = range(trough1_idx, trough2_idx + 1)
                    peak_idx = peak_range[np.argmax(high.iloc[peak_range])]
                    
                    patterns['double_bottom'].append({
                        'start_idx': trough1_idx,
                        'end_idx': trough2_idx,
                        'peak_idx': peak_idx,
                        'trough1_price': trough1_price,
                        'trough2_price': trough2_price,
                        'peak_price': high.iloc[peak_idx],
                        'confidence': 0.8 if abs(trough1_price - trough2_price) / trough1_price < 0.02 else 0.6
                    })
        
        return patterns


class IndicatorEngine:
    """技术指标引擎"""
    
    def __init__(self):
        self.advanced_indicators = AdvancedIndicators()
        self.pattern_detector = TechnicalPatterns()
        self.cache = {}
    
    def calculate_indicator(self, indicator_name: str, data: Dict[str, pd.Series],
                          **params) -> IndicatorResult:
        """计算技术指标
        
        Args:
            indicator_name: 指标名称
            data: 价格数据字典 (包含open, high, low, close, volume)
            **params: 指标参数
        """
        # 生成缓存键
        cache_key = f"{indicator_name}_{hash(str(params))}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            if indicator_name == 'adaptive_ma':
                values = self.advanced_indicators.adaptive_moving_average(
                    data['close'], **params
                )
                result = IndicatorResult(
                    name='Adaptive Moving Average',
                    type=IndicatorType.TREND,
                    values=values,
                    parameters=params
                )
            
            elif indicator_name == 'price_channel':
                values = self.advanced_indicators.price_channel(
                    data['high'], data['low'], **params
                )
                result = IndicatorResult(
                    name='Price Channel',
                    type=IndicatorType.SUPPORT_RESISTANCE,
                    values=values,
                    parameters=params
                )
            
            elif indicator_name == 'vwap_bands':
                values = self.advanced_indicators.vwap_bands(
                    data['high'], data['low'], data['close'], data['volume'], **params
                )
                result = IndicatorResult(
                    name='VWAP Bands',
                    type=IndicatorType.TREND,
                    values=values,
                    parameters=params
                )
            
            elif indicator_name == 'mfi':
                values = self.advanced_indicators.money_flow_index(
                    data['high'], data['low'], data['close'], data['volume'], **params
                )
                result = IndicatorResult(
                    name='Money Flow Index',
                    type=IndicatorType.MOMENTUM,
                    values=values,
                    parameters=params
                )
            
            elif indicator_name == 'chaikin_osc':
                values = self.advanced_indicators.chaikin_oscillator(
                    data['high'], data['low'], data['close'], data['volume'], **params
                )
                result = IndicatorResult(
                    name='Chaikin Oscillator',
                    type=IndicatorType.VOLUME,
                    values=values,
                    parameters=params
                )
            
            elif indicator_name == 'volume_profile':
                values = self.advanced_indicators.volume_profile(
                    data['close'], data['volume'], **params
                )
                result = IndicatorResult(
                    name='Volume Profile',
                    type=IndicatorType.VOLUME,
                    values=values,
                    parameters=params
                )
            
            elif indicator_name == 'tsi':
                values = self.advanced_indicators.true_strength_index(
                    data['close'], **params
                )
                result = IndicatorResult(
                    name='True Strength Index',
                    type=IndicatorType.MOMENTUM,
                    values=values,
                    parameters=params
                )
            
            elif indicator_name == 'ichimoku':
                values = self.advanced_indicators.ichimoku_cloud(
                    data['high'], data['low'], data['close'], **params
                )
                result = IndicatorResult(
                    name='Ichimoku Cloud',
                    type=IndicatorType.TREND,
                    values=values,
                    parameters=params
                )
            
            else:
                raise ValueError(f"Unknown indicator: {indicator_name}")
            
            # 缓存结果
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            raise ValueError(f"Error calculating {indicator_name}: {str(e)}")
    
    def detect_patterns(self, data: Dict[str, pd.Series], **params) -> Dict[str, Any]:
        """检测技术形态"""
        support_resistance = self.pattern_detector.detect_support_resistance(
            data['close'], **params
        )
        
        chart_patterns = self.pattern_detector.detect_chart_patterns(
            data['high'], data['low'], data['close'], **params
        )
        
        return {
            'support_resistance': support_resistance,
            'chart_patterns': chart_patterns
        }
    
    def get_available_indicators(self) -> Dict[str, Dict[str, Any]]:
        """获取可用指标列表"""
        return {
            'adaptive_ma': {
                'name': 'Adaptive Moving Average',
                'type': 'trend',
                'params': ['period', 'alpha'],
                'description': '自适应移动平均线，根据市场效率调整平滑系数'
            },
            'price_channel': {
                'name': 'Price Channel',
                'type': 'support_resistance',
                'params': ['period'],
                'description': '价格通道，显示价格的上下边界'
            },
            'vwap_bands': {
                'name': 'VWAP Bands',
                'type': 'trend',
                'params': ['period', 'std_dev'],
                'description': '成交量加权平均价格通道'
            },
            'mfi': {
                'name': 'Money Flow Index',
                'type': 'momentum',
                'params': ['period'],
                'description': '资金流量指数，衡量买卖压力'
            },
            'chaikin_osc': {
                'name': 'Chaikin Oscillator',
                'type': 'volume',
                'params': ['fast', 'slow'],
                'description': '蔡金振荡器，基于成交量的动量指标'
            },
            'volume_profile': {
                'name': 'Volume Profile',
                'type': 'volume',
                'params': ['bins'],
                'description': '成交量分布轮廓分析'
            },
            'tsi': {
                'name': 'True Strength Index',
                'type': 'momentum',
                'params': ['period1', 'period2'],
                'description': '真实强度指数，双重平滑的动量指标'
            },
            'ichimoku': {
                'name': 'Ichimoku Cloud',
                'type': 'trend',
                'params': ['conversion_period', 'base_period', 'leading_span_b_period', 'displacement'],
                'description': '一目均衡表，综合趋势分析系统'
            }
        }


# 导出
__all__ = [
    'AdvancedIndicators', 'TechnicalPatterns', 'IndicatorEngine'
]