"""
成交量确认策略

基于成交量分析的交易策略，通过识别成交量异常和价量配合来发现交易机会。
适用于捕获主力资金进出动作和市场情绪变化。

策略逻辑：
1. 监测成交量突然放大和缩量
2. 价量配合关系分析
3. 成交量分布和量价背离识别
4. OBV(能量潮)指标趋势确认
"""

import backtrader as bt
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import logging

from . import (BaseStrategy, TradingSignal, SignalType, SignalStrength,
               calculate_rsi, calculate_moving_average, calculate_bollinger_bands)


class VolumeConfirmationStrategy(BaseStrategy):
    """
    成交量确认策略
    
    核心特征：
    - 成交量异常识别
    - 价量配合分析
    - 量价背离检测
    - OBV趋势确认
    """
    
    params = (
        ('strategy_name', 'VolumeConfirmation'),
        ('min_confidence', 0.65),
        ('lookback_period', 30),
        ('volume_surge_ratio', 2.0),      # 放量倍数
        ('volume_dry_ratio', 0.5),        # 缩量倍数
        ('price_volume_periods', 10),     # 价量分析周期
        ('obv_ma_period', 10),           # OBV均线周期
        ('volume_ma_period', 20),        # 成交量均线周期
        ('min_volume_threshold', 5000),   # 最小成交量阈值
        ('divergence_periods', 15),      # 背离分析周期
        ('confirmation_periods', 3),     # 确认周期
        ('volume_distribution_bins', 5), # 成交量分布区间
    )
    
    def _init_indicators(self):
        """初始化技术指标"""
        # 基础数据
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        
        # 成交量相关指标
        self.volume_ma = bt.indicators.SimpleMovingAverage(
            self.datavolume, period=self.params.volume_ma_period
        )
        
        # 价格指标
        self.price_ma = bt.indicators.SimpleMovingAverage(
            self.dataclose, period=10
        )
        
        # RSI指标
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.dataclose, period=14
        )
        
        # 自定义OBV指标
        self.obv_values = []
        self.obv_ma_values = []
        
        # 历史数据存储
        self.price_history = []
        self.volume_history = []
        self.high_history = []
        self.low_history = []
        
        # 成交量分析数据
        self.volume_surges = []  # 放量记录
        self.volume_drys = []    # 缩量记录
        self.price_volume_correlation = []
        
        # 策略状态
        self.position_entry_bar = None
        self.entry_volume_signal = None
        
        self.logger.info("成交量确认策略指标初始化完成")
    
    def _generate_signal(self) -> Optional[TradingSignal]:
        """生成成交量确认信号"""
        current_price = float(self.dataclose[0])
        current_volume = float(self.datavolume[0])
        current_high = float(self.datahigh[0])
        current_low = float(self.datalow[0])
        
        # 更新历史数据
        self.price_history.append(current_price)
        self.volume_history.append(current_volume)
        self.high_history.append(current_high)
        self.low_history.append(current_low)
        
        # 计算OBV
        self._update_obv(current_price, current_volume)
        
        # 保持历史记录长度
        max_history = self.params.lookback_period + 10
        if len(self.price_history) > max_history:
            self.price_history.pop(0)
            self.volume_history.pop(0)
            self.high_history.pop(0)
            self.low_history.pop(0)
        
        # 需要足够的历史数据
        if len(self.price_history) < self.params.volume_ma_period:
            return None
        
        # 检查基本成交量条件
        if current_volume < self.params.min_volume_threshold:
            return None
        
        # 检查平仓信号
        if self.position_entry_bar is not None:
            exit_signal = self._check_exit_conditions(current_price, current_volume)
            if exit_signal:
                return exit_signal
        
        # 生成买入信号
        if self.position_entry_bar is None:
            buy_signal = self._check_volume_buy_signal(current_price, current_volume)
            if buy_signal:
                return buy_signal
        
        # 生成卖出信号
        if self.position_entry_bar is None:
            sell_signal = self._check_volume_sell_signal(current_price, current_volume)
            if sell_signal:
                return sell_signal
        
        return None
    
    def _update_obv(self, price: float, volume: float):
        """更新OBV指标"""
        if not self.obv_values:
            self.obv_values.append(volume)
        else:
            prev_price = self.price_history[-2] if len(self.price_history) > 1 else price
            prev_obv = self.obv_values[-1]
            
            if price > prev_price:
                new_obv = prev_obv + volume
            elif price < prev_price:
                new_obv = prev_obv - volume
            else:
                new_obv = prev_obv
            
            self.obv_values.append(new_obv)
        
        # 计算OBV移动平均
        if len(self.obv_values) >= self.params.obv_ma_period:
            obv_ma = sum(self.obv_values[-self.params.obv_ma_period:]) / self.params.obv_ma_period
            self.obv_ma_values.append(obv_ma)
        
        # 保持OBV历史长度
        if len(self.obv_values) > self.params.lookback_period:
            self.obv_values.pop(0)
        if len(self.obv_ma_values) > self.params.lookback_period:
            self.obv_ma_values.pop(0)
    
    def _check_volume_buy_signal(self, price: float, volume: float) -> Optional[TradingSignal]:
        """检查成交量买入信号"""
        # 分析成交量异常
        volume_analysis = self._analyze_volume_anomaly(volume)
        if not volume_analysis['is_surge']:
            return None
        
        # 价量配合分析
        price_volume_analysis = self._analyze_price_volume_relationship(price, volume, 'buy')
        if not price_volume_analysis['is_bullish']:
            return None
        
        # OBV趋势确认
        obv_analysis = self._analyze_obv_trend('buy')
        if not obv_analysis['is_bullish']:
            return None
        
        # 量价背离检测
        divergence_analysis = self._detect_volume_price_divergence('buy')
        
        # 计算信号置信度
        confidence = self._calculate_volume_confidence(
            volume_analysis, price_volume_analysis, obv_analysis, divergence_analysis, 'buy'
        )
        
        if confidence < self.params.min_confidence:
            return None
        
        # 确定信号强度
        strength = self._determine_volume_signal_strength(
            confidence, volume_analysis, price_volume_analysis
        )
        signal_type = SignalType.STRONG_BUY if confidence > 0.8 else SignalType.BUY
        
        return TradingSignal(
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            strategy_name=self.params.strategy_name,
            timestamp=datetime.now(),
            price=price,
            volume=int(volume),
            indicators={
                'signal_type': 'volume_surge_buy',
                'volume_ratio': volume_analysis['surge_ratio'],
                'price_momentum': price_volume_analysis['momentum'],
                'obv_trend': obv_analysis['trend_strength'],
                'divergence_detected': divergence_analysis['has_bullish_divergence'],
                'volume_distribution': self._analyze_volume_distribution()
            }
        )
    
    def _check_volume_sell_signal(self, price: float, volume: float) -> Optional[TradingSignal]:
        """检查成交量卖出信号"""
        # 分析成交量异常
        volume_analysis = self._analyze_volume_anomaly(volume)
        
        # 对于卖出信号，既可以是放量下跌，也可以是缩量上涨
        is_volume_signal = volume_analysis['is_surge'] or volume_analysis['is_dry']
        if not is_volume_signal:
            return None
        
        # 价量配合分析
        price_volume_analysis = self._analyze_price_volume_relationship(price, volume, 'sell')
        if not price_volume_analysis['is_bearish']:
            return None
        
        # OBV趋势确认
        obv_analysis = self._analyze_obv_trend('sell')
        if not obv_analysis['is_bearish']:
            return None
        
        # 量价背离检测
        divergence_analysis = self._detect_volume_price_divergence('sell')
        
        # 计算信号置信度
        confidence = self._calculate_volume_confidence(
            volume_analysis, price_volume_analysis, obv_analysis, divergence_analysis, 'sell'
        )
        
        if confidence < self.params.min_confidence:
            return None
        
        # 确定信号强度
        strength = self._determine_volume_signal_strength(
            confidence, volume_analysis, price_volume_analysis
        )
        signal_type = SignalType.STRONG_SELL if confidence > 0.8 else SignalType.SELL
        
        return TradingSignal(
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            strategy_name=self.params.strategy_name,
            timestamp=datetime.now(),
            price=price,
            volume=int(volume),
            indicators={
                'signal_type': 'volume_confirm_sell',
                'volume_ratio': volume_analysis.get('surge_ratio', volume_analysis.get('dry_ratio', 1.0)),
                'price_momentum': price_volume_analysis['momentum'],
                'obv_trend': obv_analysis['trend_strength'],
                'divergence_detected': divergence_analysis['has_bearish_divergence'],
                'volume_distribution': self._analyze_volume_distribution()
            }
        )
    
    def _analyze_volume_anomaly(self, current_volume: float) -> Dict:
        """分析成交量异常"""
        if len(self.volume_history) < self.params.volume_ma_period:
            return {'is_surge': False, 'is_dry': False}
        
        # 计算成交量移动平均
        recent_volumes = self.volume_history[-self.params.volume_ma_period:]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        # 放量检测
        surge_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        is_surge = surge_ratio >= self.params.volume_surge_ratio
        
        # 缩量检测
        dry_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        is_dry = dry_ratio <= self.params.volume_dry_ratio
        
        return {
            'is_surge': is_surge,
            'is_dry': is_dry,
            'surge_ratio': surge_ratio,
            'dry_ratio': dry_ratio,
            'avg_volume': avg_volume
        }
    
    def _analyze_price_volume_relationship(self, price: float, volume: float, direction: str) -> Dict:
        """分析价量关系"""
        if len(self.price_history) < self.params.price_volume_periods:
            return {'is_bullish': False, 'is_bearish': False, 'momentum': 0}
        
        # 计算价格动量
        recent_prices = self.price_history[-self.params.price_volume_periods:]
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # 计算成交量趋势
        recent_volumes = self.volume_history[-self.params.price_volume_periods:]
        volume_trend = (recent_volumes[-1] - recent_volumes[0]) / recent_volumes[0] if recent_volumes[0] > 0 else 0
        
        # 价量配合度
        if direction == 'buy':
            # 买入：价格上涨且成交量放大
            is_bullish = price_change > 0 and volume_trend > 0
            momentum = price_change * (1 + volume_trend)
            return {'is_bullish': is_bullish, 'momentum': momentum}
        
        else:  # sell
            # 卖出：价格下跌且成交量放大，或价格上涨但成交量萎缩
            is_bearish = (price_change < 0 and volume_trend > 0) or (price_change > 0 and volume_trend < -0.2)
            momentum = abs(price_change) * (1 + abs(volume_trend))
            return {'is_bearish': is_bearish, 'momentum': momentum}
    
    def _analyze_obv_trend(self, direction: str) -> Dict:
        """分析OBV趋势"""
        if len(self.obv_values) < self.params.obv_ma_period or len(self.obv_ma_values) < 2:
            return {'is_bullish': False, 'is_bearish': False, 'trend_strength': 0}
        
        # OBV趋势
        current_obv = self.obv_values[-1]
        current_obv_ma = self.obv_ma_values[-1]
        prev_obv_ma = self.obv_ma_values[-2]
        
        obv_trend = (current_obv_ma - prev_obv_ma) / abs(prev_obv_ma) if prev_obv_ma != 0 else 0
        obv_position = (current_obv - current_obv_ma) / abs(current_obv_ma) if current_obv_ma != 0 else 0
        
        if direction == 'buy':
            is_bullish = obv_trend > 0 and obv_position > 0
            return {'is_bullish': is_bullish, 'trend_strength': obv_trend}
        else:  # sell
            is_bearish = obv_trend < 0 or obv_position < -0.1
            return {'is_bearish': is_bearish, 'trend_strength': abs(obv_trend)}
    
    def _detect_volume_price_divergence(self, direction: str) -> Dict:
        """检测量价背离"""
        if len(self.price_history) < self.params.divergence_periods:
            return {'has_bullish_divergence': False, 'has_bearish_divergence': False}
        
        # 取最近N期数据
        recent_prices = self.price_history[-self.params.divergence_periods:]
        recent_volumes = self.volume_history[-self.params.divergence_periods:]
        
        # 价格趋势
        price_highs = []
        price_lows = []
        for i in range(2, len(recent_prices)-1):
            if recent_prices[i] > recent_prices[i-1] and recent_prices[i] > recent_prices[i+1]:
                price_highs.append((i, recent_prices[i]))
            if recent_prices[i] < recent_prices[i-1] and recent_prices[i] < recent_prices[i+1]:
                price_lows.append((i, recent_prices[i]))
        
        # 成交量趋势
        volume_peaks = []
        for i in range(2, len(recent_volumes)-1):
            if recent_volumes[i] > recent_volumes[i-1] and recent_volumes[i] > recent_volumes[i+1]:
                volume_peaks.append((i, recent_volumes[i]))
        
        # 背离检测
        has_bullish_divergence = False
        has_bearish_divergence = False
        
        if len(price_lows) >= 2 and len(volume_peaks) >= 2:
            # 底背离：价格新低，成交量不创新低
            last_price_low = price_lows[-1][1]
            prev_price_low = price_lows[-2][1]
            if last_price_low < prev_price_low:
                # 检查对应时间的成交量
                has_bullish_divergence = len(volume_peaks) > 0
        
        if len(price_highs) >= 2 and len(volume_peaks) >= 2:
            # 顶背离：价格新高，成交量不创新高
            last_price_high = price_highs[-1][1]
            prev_price_high = price_highs[-2][1] 
            if last_price_high > prev_price_high:
                # 检查成交量是否减少
                recent_volume_avg = sum(recent_volumes[-3:]) / 3
                earlier_volume_avg = sum(recent_volumes[-6:-3]) / 3
                has_bearish_divergence = recent_volume_avg < earlier_volume_avg
        
        return {
            'has_bullish_divergence': has_bullish_divergence,
            'has_bearish_divergence': has_bearish_divergence
        }
    
    def _analyze_volume_distribution(self) -> Dict:
        """分析成交量分布"""
        if len(self.volume_history) < self.params.volume_ma_period:
            return {'distribution_type': 'normal'}
        
        recent_volumes = self.volume_history[-self.params.volume_ma_period:]
        avg_volume = sum(recent_volumes) / len(recent_volumes)
        
        # 统计各区间的成交量
        high_volume_count = sum(1 for v in recent_volumes if v > avg_volume * 1.5)
        low_volume_count = sum(1 for v in recent_volumes if v < avg_volume * 0.5)
        
        if high_volume_count > len(recent_volumes) * 0.3:
            distribution_type = 'high_volume_dominant'
        elif low_volume_count > len(recent_volumes) * 0.3:
            distribution_type = 'low_volume_dominant'
        else:
            distribution_type = 'normal'
        
        return {
            'distribution_type': distribution_type,
            'high_volume_ratio': high_volume_count / len(recent_volumes),
            'low_volume_ratio': low_volume_count / len(recent_volumes)
        }
    
    def _calculate_volume_confidence(self, volume_analysis: Dict, price_volume_analysis: Dict,
                                   obv_analysis: Dict, divergence_analysis: Dict, direction: str) -> float:
        """计算成交量信号置信度"""
        confidence_factors = []
        
        # 成交量异常强度
        if direction == 'buy' and volume_analysis['is_surge']:
            surge_score = min(1.0, (volume_analysis['surge_ratio'] - 1) / 
                            (self.params.volume_surge_ratio - 1))
            confidence_factors.append(surge_score * 0.3)
        elif direction == 'sell':
            if volume_analysis['is_surge']:
                surge_score = min(1.0, (volume_analysis['surge_ratio'] - 1) / 
                                (self.params.volume_surge_ratio - 1))
                confidence_factors.append(surge_score * 0.25)
            elif volume_analysis['is_dry']:
                dry_score = min(1.0, (1 - volume_analysis['dry_ratio']) / 
                              (1 - self.params.volume_dry_ratio))
                confidence_factors.append(dry_score * 0.2)
        
        # 价量配合度
        momentum_score = min(1.0, abs(price_volume_analysis['momentum']) * 10)
        confidence_factors.append(momentum_score * 0.25)
        
        # OBV趋势强度
        obv_score = min(1.0, abs(obv_analysis['trend_strength']) * 50)
        confidence_factors.append(obv_score * 0.2)
        
        # 背离加分
        if direction == 'buy' and divergence_analysis['has_bullish_divergence']:
            confidence_factors.append(0.15)
        elif direction == 'sell' and divergence_analysis['has_bearish_divergence']:
            confidence_factors.append(0.15)
        
        # RSI确认
        if hasattr(self.rsi, '__getitem__') and len(self.rsi) > 0:
            rsi_value = float(self.rsi[0])
            if direction == 'buy' and rsi_value < 70:
                rsi_score = (70 - rsi_value) / 70
                confidence_factors.append(rsi_score * 0.1)
            elif direction == 'sell' and rsi_value > 30:
                rsi_score = (rsi_value - 30) / 70
                confidence_factors.append(rsi_score * 0.1)
        
        return sum(confidence_factors)
    
    def _determine_volume_signal_strength(self, confidence: float, volume_analysis: Dict,
                                        price_volume_analysis: Dict) -> SignalStrength:
        """确定成交量信号强度"""
        # 基于置信度和关键指标
        surge_ratio = volume_analysis.get('surge_ratio', 1.0)
        momentum = abs(price_volume_analysis.get('momentum', 0))
        
        if confidence > 0.85 and surge_ratio > 3.0:
            return SignalStrength.VERY_STRONG
        elif confidence > 0.75 and (surge_ratio > 2.5 or momentum > 0.1):
            return SignalStrength.STRONG
        elif confidence > 0.65:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _check_exit_conditions(self, price: float, volume: float) -> Optional[TradingSignal]:
        """检查平仓条件"""
        if self.position_entry_bar is None:
            return None
        
        bars_held = len(self.price_history) - self.position_entry_bar
        
        # 成交量萎缩平仓
        if len(self.volume_history) >= 5:
            recent_avg_volume = sum(self.volume_history[-5:]) / 5
            if volume < recent_avg_volume * 0.3:  # 成交量极度萎缩
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    strength=SignalStrength.MODERATE,
                    confidence=0.7,
                    strategy_name=self.params.strategy_name,
                    timestamp=datetime.now(),
                    price=price,
                    volume=int(volume),
                    indicators={
                        'exit_type': 'volume_dry_up',
                        'volume_ratio': volume / recent_avg_volume,
                        'bars_held': bars_held
                    }
                )
        
        # 时间止损
        if bars_held >= 20:  # 持仓超过20个周期
            return TradingSignal(
                signal_type=SignalType.SELL,
                strength=SignalStrength.WEAK,
                confidence=0.6,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=price,
                volume=int(volume),
                indicators={
                    'exit_type': 'time_exit',
                    'bars_held': bars_held
                }
            )
        
        return None
    
    def _execute_signal(self, signal: TradingSignal):
        """执行交易信号"""
        super()._execute_signal(signal)
        
        # 更新仓位状态
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            self.position_entry_bar = len(self.price_history)
            self.entry_volume_signal = signal.indicators
            
            self.logger.info(f"成交量买入: 价格={signal.price:.2f}, "
                           f"成交量={signal.volume}, "
                           f"类型={signal.indicators.get('signal_type')}")
            
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            if self.position_entry_bar is not None:
                bars_held = len(self.price_history) - self.position_entry_bar
                self.logger.info(f"成交量平仓: 价格={signal.price:.2f}, "
                               f"持仓={bars_held}周期, "
                               f"退出类型={signal.indicators.get('exit_type', 'normal')}")
                
                # 统计成功信号(简单以持仓时间判断)
                if bars_held >= 3:
                    self.successful_signals += 1
            
            self.position_entry_bar = None
            self.entry_volume_signal = None
    
    def get_strategy_status(self) -> dict:
        """获取策略状态"""
        base_status = self.get_strategy_performance()
        
        volume_status = {
            'in_position': self.position_entry_bar is not None,
            'bars_held': (len(self.price_history) - self.position_entry_bar) 
                        if self.position_entry_bar else 0,
            'current_volume': self.volume_history[-1] if self.volume_history else 0,
            'avg_volume': sum(self.volume_history[-20:]) / 20 if len(self.volume_history) >= 20 else 0,
            'current_obv': self.obv_values[-1] if self.obv_values else 0,
            'obv_ma': self.obv_ma_values[-1] if self.obv_ma_values else 0,
            'volume_surges_count': len(self.volume_surges),
            'entry_signal_type': self.entry_volume_signal.get('signal_type') if self.entry_volume_signal else None
        }
        
        base_status.update(volume_status)
        return base_status


# 使用示例和测试
if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("📊 成交量确认策略演示")
    print("=" * 50)
    
    print("策略特点:")
    print("- 识别成交量异常放大和萎缩")
    print("- 分析价量配合关系")
    print("- 检测量价背离现象")
    print("- OBV指标趋势确认")
    print("- 适用于捕获主力资金动向")
    
    print("\\n参数设置:")
    print("- 放量倍数: 2.0倍")
    print("- 缩量倍数: 0.5倍")
    print("- 价量分析周期: 10")
    print("- OBV均线周期: 10")
    print("- 背离分析周期: 15")
    
    print("\\n⚠️  注意事项:")
    print("- 成交量数据质量要求高")
    print("- 避免在特殊时段(开盘/收盘)交易")
    print("- 结合基本面消息验证")
    print("- 严格执行成交量萎缩止损")