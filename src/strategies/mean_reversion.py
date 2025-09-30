"""
均线反转策略

基于移动平均线的反转交易策略，适用于横盘震荡市场。
通过识别价格在均线附近的反转信号来捕获短期波动收益。

策略逻辑：
1. 多条移动平均线构建支撑阻力网络
2. 价格触及均线后的反转信号识别
3. MACD指标确认趋势反转
4. 振荡指标(Stochastic)辅助入场时机
"""

import backtrader as bt
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import logging

from . import (BaseStrategy, TradingSignal, SignalType, SignalStrength,
               calculate_rsi, calculate_moving_average, calculate_bollinger_bands)


class MeanReversionStrategy(BaseStrategy):
    """
    均线反转策略
    
    核心特征：
    - 均线支撑阻力识别
    - 反转信号确认
    - MACD趋势验证
    - 振荡器时机选择
    """
    
    params = (
        ('strategy_name', 'MeanReversion'),
        ('min_confidence', 0.6),
        ('lookback_period', 30),
        ('ma_periods', [5, 10, 20, 50]),  # 多条均线周期
        ('deviation_threshold', 0.015),   # 偏离阈值 1.5%
        ('volume_confirm', True),         # 成交量确认
        ('macd_fast', 12),               # MACD快线
        ('macd_slow', 26),               # MACD慢线
        ('macd_signal', 9),              # MACD信号线
        ('stoch_k', 14),                 # 随机指标K值
        ('stoch_d', 3),                  # 随机指标D值
        ('min_distance_pct', 0.005),     # 最小距离百分比 0.5%
        ('max_hold_periods', 20),        # 最大持仓周期
    )
    
    def _init_indicators(self):
        """初始化技术指标"""
        # 基础数据
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        
        # 多条移动平均线
        self.moving_averages = {}
        for period in self.params.ma_periods:
            self.moving_averages[period] = bt.indicators.SimpleMovingAverage(
                self.dataclose, period=period
            )
        
        # MACD指标
        self.macd = bt.indicators.MACD(
            self.dataclose,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        
        # 随机指标
        self.stochastic = bt.indicators.Stochastic(
            self.datas[0],
            period=self.params.stoch_k,
            period_dfast=self.params.stoch_d
        )
        
        # RSI指标
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.dataclose, period=14
        )
        
        # 布林带
        self.bollinger = bt.indicators.BollingerBands(
            self.dataclose, period=20, devfactor=2.0
        )
        
        # 成交量指标
        self.volume_ma = bt.indicators.SimpleMovingAverage(
            self.datavolume, period=20
        )
        
        # 策略状态
        self.position_entry_time = None
        self.position_entry_price = 0.0
        self.reversal_level = 0.0
        self.target_level = 0.0
        
        # 历史数据
        self.price_history = []
        self.volume_history = []
        
        self.logger.info("均线反转策略指标初始化完成")
    
    def _generate_signal(self) -> Optional[TradingSignal]:
        """生成均线反转信号"""
        current_price = float(self.dataclose[0])
        current_volume = float(self.datavolume[0])
        
        # 更新历史数据
        self.price_history.append(current_price)
        self.volume_history.append(current_volume)
        
        # 保持历史记录长度
        max_history = max(self.params.ma_periods) + 10
        if len(self.price_history) > max_history:
            self.price_history.pop(0)
            self.volume_history.pop(0)
        
        # 需要足够的历史数据
        if len(self.price_history) < max(self.params.ma_periods):
            return None
        
        # 检查是否需要平仓
        if self.position_entry_time:
            exit_signal = self._check_exit_conditions(current_price)
            if exit_signal:
                return exit_signal
        
        # 检查反转买入信号
        if not self.position_entry_time:
            buy_signal = self._check_reversal_buy(current_price, current_volume)
            if buy_signal:
                return buy_signal
        
        # 检查反转卖出信号  
        if not self.position_entry_time:
            sell_signal = self._check_reversal_sell(current_price, current_volume)
            if sell_signal:
                return sell_signal
        
        return None
    
    def _check_reversal_buy(self, price: float, volume: float) -> Optional[TradingSignal]:
        """检查反转买入信号"""
        # 寻找支撑位均线
        support_ma = self._find_support_resistance(price, 'support')
        if not support_ma:
            return None
        
        ma_value, ma_period = support_ma
        
        # 检查价格是否接近支撑位
        distance_pct = abs(price - ma_value) / ma_value
        if distance_pct > self.params.deviation_threshold:
            return None
        
        # 确保价格在均线下方（反转买入）
        if price >= ma_value:
            return None
        
        # 检查反转确认条件
        reversal_conditions = self._check_reversal_conditions(price, ma_value, 'buy')
        if not reversal_conditions['confirmed']:
            return None
        
        # 计算置信度
        confidence = self._calculate_reversal_confidence(
            price, ma_value, volume, reversal_conditions, 'buy'
        )
        
        if confidence < self.params.min_confidence:
            return None
        
        # 确定信号强度
        strength = self._determine_signal_strength(confidence, reversal_conditions)
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
                'reversal_type': 'support_bounce',
                'support_ma_period': ma_period,
                'support_level': ma_value,
                'distance_pct': distance_pct,
                'macd_signal': reversal_conditions.get('macd_signal'),
                'stoch_oversold': reversal_conditions.get('stoch_oversold'),
                'volume_confirm': reversal_conditions.get('volume_confirm')
            }
        )
    
    def _check_reversal_sell(self, price: float, volume: float) -> Optional[TradingSignal]:
        """检查反转卖出信号"""
        # 寻找阻力位均线
        resistance_ma = self._find_support_resistance(price, 'resistance')
        if not resistance_ma:
            return None
        
        ma_value, ma_period = resistance_ma
        
        # 检查价格是否接近阻力位
        distance_pct = abs(price - ma_value) / ma_value
        if distance_pct > self.params.deviation_threshold:
            return None
        
        # 确保价格在均线上方（反转卖出）
        if price <= ma_value:
            return None
        
        # 检查反转确认条件
        reversal_conditions = self._check_reversal_conditions(price, ma_value, 'sell')
        if not reversal_conditions['confirmed']:
            return None
        
        # 计算置信度
        confidence = self._calculate_reversal_confidence(
            price, ma_value, volume, reversal_conditions, 'sell'
        )
        
        if confidence < self.params.min_confidence:
            return None
        
        # 确定信号强度
        strength = self._determine_signal_strength(confidence, reversal_conditions)
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
                'reversal_type': 'resistance_rejection',
                'resistance_ma_period': ma_period,
                'resistance_level': ma_value,
                'distance_pct': distance_pct,
                'macd_signal': reversal_conditions.get('macd_signal'),
                'stoch_overbought': reversal_conditions.get('stoch_overbought'),
                'volume_confirm': reversal_conditions.get('volume_confirm')
            }
        )
    
    def _find_support_resistance(self, price: float, sr_type: str) -> Optional[Tuple[float, int]]:
        """寻找支撑或阻力位均线"""
        candidates = []
        
        for period in self.params.ma_periods:
            if period in self.moving_averages:
                ma_value = float(self.moving_averages[period][0])
                distance = abs(price - ma_value) / ma_value
                
                if distance <= self.params.deviation_threshold:
                    if sr_type == 'support' and price <= ma_value * 1.005:  # 价格略低于均线
                        candidates.append((ma_value, period, distance))
                    elif sr_type == 'resistance' and price >= ma_value * 0.995:  # 价格略高于均线
                        candidates.append((ma_value, period, distance))
        
        if not candidates:
            return None
        
        # 选择距离最近的均线
        candidates.sort(key=lambda x: x[2])
        return candidates[0][0], candidates[0][1]
    
    def _check_reversal_conditions(self, price: float, ma_value: float, direction: str) -> dict:
        """检查反转确认条件"""
        conditions = {
            'confirmed': False,
            'macd_signal': False,
            'stoch_oversold': False,
            'stoch_overbought': False,
            'volume_confirm': False,
            'price_pattern': False
        }
        
        try:
            # MACD确认
            if hasattr(self.macd, 'macd') and len(self.macd.macd) > 1:
                macd_current = float(self.macd.macd[0])
                macd_signal_current = float(self.macd.signal[0])
                
                if direction == 'buy':
                    # 买入：MACD金叉或MACD线向上
                    conditions['macd_signal'] = macd_current > macd_signal_current
                else:  # sell
                    # 卖出：MACD死叉或MACD线向下
                    conditions['macd_signal'] = macd_current < macd_signal_current
            
            # 随机指标确认
            if hasattr(self.stochastic, 'percK') and len(self.stochastic.percK) > 0:
                stoch_k = float(self.stochastic.percK[0])
                
                if direction == 'buy':
                    conditions['stoch_oversold'] = stoch_k < 20  # 超卖区域
                else:  # sell
                    conditions['stoch_overbought'] = stoch_k > 80  # 超买区域
            
            # 成交量确认
            if self.params.volume_confirm and len(self.volume_history) >= 5:
                recent_avg_vol = sum(self.volume_history[-5:]) / 5
                current_vol = self.volume_history[-1]
                conditions['volume_confirm'] = current_vol > recent_avg_vol * 1.2
            else:
                conditions['volume_confirm'] = True  # 不需要成交量确认
            
            # 价格形态确认
            if len(self.price_history) >= 3:
                prev_price = self.price_history[-2]
                if direction == 'buy':
                    # 买入：价格开始反弹
                    conditions['price_pattern'] = price > prev_price
                else:  # sell
                    # 卖出：价格开始回落
                    conditions['price_pattern'] = price < prev_price
            
            # 综合确认
            required_conditions = 2  # 至少满足2个条件
            met_conditions = sum([
                conditions['macd_signal'],
                conditions['stoch_oversold'] if direction == 'buy' else conditions['stoch_overbought'],
                conditions['volume_confirm'],
                conditions['price_pattern']
            ])
            
            conditions['confirmed'] = met_conditions >= required_conditions
            
        except Exception as e:
            self.logger.error(f"反转条件检查错误: {e}")
            conditions['confirmed'] = False
        
        return conditions
    
    def _calculate_reversal_confidence(self, price: float, ma_value: float, 
                                     volume: float, conditions: dict, direction: str) -> float:
        """计算反转信号置信度"""
        confidence_factors = []
        
        # 距离均线距离（越近越好）
        distance_pct = abs(price - ma_value) / ma_value
        distance_score = 1.0 - (distance_pct / self.params.deviation_threshold)
        confidence_factors.append(distance_score * 0.25)
        
        # 技术指标确认
        indicator_score = 0
        if conditions.get('macd_signal'):
            indicator_score += 0.3
        if conditions.get('stoch_oversold') or conditions.get('stoch_overbought'):
            indicator_score += 0.25
        if conditions.get('volume_confirm'):
            indicator_score += 0.2
        if conditions.get('price_pattern'):
            indicator_score += 0.25
        
        confidence_factors.append(indicator_score * 0.4)
        
        # RSI位置确认
        if hasattr(self.rsi, '__getitem__') and len(self.rsi) > 0:
            rsi_value = float(self.rsi[0])
            if direction == 'buy':
                rsi_score = max(0, (50 - rsi_value) / 50)  # RSI越低越好
            else:  # sell
                rsi_score = max(0, (rsi_value - 50) / 50)  # RSI越高越好
            confidence_factors.append(rsi_score * 0.2)
        
        # 市场环境评分
        market_score = self._assess_market_environment(direction)
        confidence_factors.append(market_score * 0.15)
        
        return sum(confidence_factors)
    
    def _assess_market_environment(self, direction: str) -> float:
        """评估市场环境适合性"""
        if len(self.price_history) < 20:
            return 0.5
        
        # 计算价格波动性
        recent_prices = self.price_history[-20:]
        price_std = (sum((p - sum(recent_prices)/20)**2 for p in recent_prices) / 20) ** 0.5
        volatility = price_std / (sum(recent_prices) / 20)
        
        # 适中的波动性最适合反转策略
        if 0.01 <= volatility <= 0.03:
            return 1.0
        elif 0.005 <= volatility <= 0.05:
            return 0.7
        else:
            return 0.3
    
    def _determine_signal_strength(self, confidence: float, conditions: dict) -> SignalStrength:
        """确定信号强度"""
        met_conditions = sum([
            conditions.get('macd_signal', False),
            conditions.get('stoch_oversold', False) or conditions.get('stoch_overbought', False),
            conditions.get('volume_confirm', False),
            conditions.get('price_pattern', False)
        ])
        
        if confidence > 0.85 and met_conditions >= 3:
            return SignalStrength.VERY_STRONG
        elif confidence > 0.75 and met_conditions >= 2:
            return SignalStrength.STRONG
        elif confidence > 0.65:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _check_exit_conditions(self, price: float) -> Optional[TradingSignal]:
        """检查平仓条件"""
        if not self.position_entry_time:
            return None
        
        # 时间止损
        periods_held = len(self.price_history) - self.position_entry_time
        if periods_held >= self.params.max_hold_periods:
            return TradingSignal(
                signal_type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                confidence=0.7,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=price,
                indicators={
                    'exit_type': 'time_stop',
                    'periods_held': periods_held,
                    'entry_price': self.position_entry_price
                }
            )
        
        # 反向信号止损
        reverse_signal = self._check_reverse_signal(price)
        if reverse_signal:
            return reverse_signal
        
        # 目标位止盈
        if self.target_level > 0:
            if (self.position_entry_price < price <= self.target_level) or \
               (self.position_entry_price > price >= self.target_level):
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    strength=SignalStrength.STRONG,
                    confidence=0.8,
                    strategy_name=self.params.strategy_name,
                    timestamp=datetime.now(),
                    price=price,
                    indicators={
                        'exit_type': 'target_reached',
                        'target_level': self.target_level,
                        'entry_price': self.position_entry_price
                    }
                )
        
        return None
    
    def _check_reverse_signal(self, price: float) -> Optional[TradingSignal]:
        """检查反向信号"""
        # 如果价格远离反转位，考虑平仓
        if self.reversal_level > 0:
            distance_pct = abs(price - self.reversal_level) / self.reversal_level
            
            if distance_pct > self.params.deviation_threshold * 2:
                return TradingSignal(
                    signal_type=SignalType.SELL,
                    strength=SignalStrength.MODERATE,
                    confidence=0.75,
                    strategy_name=self.params.strategy_name,
                    timestamp=datetime.now(),
                    price=price,
                    indicators={
                        'exit_type': 'reverse_signal',
                        'reversal_level': self.reversal_level,
                        'distance_pct': distance_pct
                    }
                )
        
        return None
    
    def _execute_signal(self, signal: TradingSignal):
        """执行交易信号"""
        super()._execute_signal(signal)
        
        # 更新仓位状态
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            self.position_entry_time = len(self.price_history)
            self.position_entry_price = signal.price
            
            # 设置反转基准位和目标位
            indicators = signal.indicators
            if 'support_level' in indicators:
                self.reversal_level = indicators['support_level']
                self.target_level = self.reversal_level * 1.02  # 2%目标收益
            
            self.logger.info(f"反转买入: 价格={signal.price:.2f}, "
                           f"反转位={self.reversal_level:.2f}, "
                           f"目标位={self.target_level:.2f}")
            
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            if self.position_entry_time:
                pnl_pct = (signal.price - self.position_entry_price) / self.position_entry_price * 100
                self.logger.info(f"反转平仓: 入场={self.position_entry_price:.2f}, "
                               f"出场={signal.price:.2f}, PnL={pnl_pct:.2f}%")
                
                # 统计成功信号
                if pnl_pct > 0:
                    self.successful_signals += 1
            
            # 清空仓位状态
            self.position_entry_time = None
            self.position_entry_price = 0.0
            self.reversal_level = 0.0
            self.target_level = 0.0
    
    def get_strategy_status(self) -> dict:
        """获取策略状态"""
        base_status = self.get_strategy_performance()
        
        reversion_status = {
            'in_position': self.position_entry_time is not None,
            'entry_price': self.position_entry_price,
            'reversal_level': self.reversal_level,
            'target_level': self.target_level,
            'periods_held': (len(self.price_history) - self.position_entry_time) 
                           if self.position_entry_time else 0,
            'current_price': float(self.dataclose[0]) if len(self.dataclose) > 0 else 0.0,
            'moving_averages': {
                period: float(ma[0]) if len(ma) > 0 else 0.0 
                for period, ma in self.moving_averages.items()
            },
            'current_rsi': float(self.rsi[0]) if hasattr(self, 'rsi') and len(self.rsi) > 0 else 50.0
        }
        
        base_status.update(reversion_status)
        return base_status


# 使用示例和测试
if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔄 均线反转策略演示")
    print("=" * 50)
    
    print("策略特点:")
    print("- 多条均线构建支撑阻力网络")
    print("- 价格触及均线的反转信号识别")
    print("- MACD指标确认趋势反转")
    print("- 随机指标辅助入场时机")
    print("- 适用于横盘震荡市场")
    
    print("\\n参数设置:")
    print("- 均线周期: 5, 10, 20, 50")
    print("- 偏离阈值: 1.5%") 
    print("- MACD参数: 12, 26, 9")
    print("- 随机指标: K=14, D=3")
    print("- 最大持仓: 20周期")
    
    print("\\n⚠️  注意事项:")
    print("- 适用于震荡行情，避免单边趋势")
    print("- 严格执行时间止损")
    print("- 结合成交量确认反转有效性")
    print("- 控制单次交易风险")