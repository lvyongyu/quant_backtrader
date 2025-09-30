"""
动量突破策略

基于价格动量和突破信号的日内交易策略。
适用于趋势明显、波动性适中的股票。

策略逻辑：
1. 监测价格突破关键阻力/支撑位
2. 结合成交量确认突破有效性
3. RSI指标避免超买超卖区域
4. 动态止损和止盈设置
"""

import backtrader as bt
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from . import (BaseStrategy, TradingSignal, SignalType, SignalStrength,
               calculate_rsi, calculate_moving_average, calculate_bollinger_bands)


class MomentumBreakoutStrategy(BaseStrategy):
    """
    动量突破策略
    
    核心特征：
    - 识别价格突破
    - 成交量确认
    - RSI过滤
    - 动态止损
    """
    
    params = (
        ('strategy_name', 'MomentumBreakout'),
        ('min_confidence', 0.65),
        ('lookback_period', 20),
        ('breakout_threshold', 0.02),  # 突破阈值 2%
        ('volume_multiplier', 1.5),    # 成交量倍数
        ('rsi_oversold', 30),          # RSI超卖线
        ('rsi_overbought', 70),        # RSI超买线
        ('stop_loss_pct', 0.015),      # 止损比例 1.5%
        ('take_profit_pct', 0.03),     # 止盈比例 3%
        ('min_volume', 10000),         # 最小成交量
    )
    
    def _init_indicators(self):
        """初始化技术指标"""
        # 为了避免元类冲突，我们使用模拟数据结构
        # 在实际应用中，这些数据会从实时数据源填充
        
        # 基础数据存储
        self.price_history = []  # 价格历史
        self.volume_history = [] # 成交量历史
        self.high_history = []   # 最高价历史
        self.low_history = []    # 最低价历史
        
        # 技术指标值存储
        self.rsi_values = []
        self.moving_avg_values = []
        self.bollinger_values = []
        
        # 突破检测数据
        self.resistance_levels = []
        self.support_levels = []
        
        # 策略状态
        self.position_entry_bar = None
        self.entry_price = None
        self.stop_loss_price = None
        self.take_profit_price = None
        
        self.logger.info("动量突破策略指标初始化完成")
    
    def _generate_signal(self) -> Optional[TradingSignal]:
        """生成动量突破信号"""
        # 在实际使用中，这里会接收实时市场数据
        # 目前返回模拟信号用于测试集成
        
        import random
        
        # 模拟价格数据
        mock_price = 150.0 + random.uniform(-5, 5)
        mock_volume = 50000 + random.randint(-20000, 20000)
        mock_rsi = random.uniform(20, 80)
        
        # 更新历史数据
        self.price_history.append(mock_price)
        self.volume_history.append(mock_volume)
        
        # 保持历史长度
        max_length = self.params.lookback_period
        if len(self.price_history) > max_length:
            self.price_history = self.price_history[-max_length:]
            self.volume_history = self.volume_history[-max_length:]
        
        # 需要足够的历史数据
        if len(self.price_history) < 10:
            return None
        
        # 简单的突破逻辑模拟
        recent_high = max(self.price_history[-10:])
        recent_low = min(self.price_history[-10:])
        
        # 买入信号：价格突破近期高点且成交量放大
        if (mock_price > recent_high * 1.01 and 
            mock_volume > sum(self.volume_history[-5:]) / 5 * 1.2 and
            mock_rsi < 70):
            
            confidence = min(0.95, 0.6 + (mock_volume / 100000) * 0.2 + (80 - mock_rsi) / 100)
            
            return TradingSignal(
                signal_type=SignalType.BUY,
                strength=SignalStrength.STRONG if confidence > 0.8 else SignalStrength.MODERATE,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=mock_price,
                volume=int(mock_volume),
                indicators={
                    'signal_type': 'momentum_breakout',
                    'rsi': mock_rsi,
                    'resistance_break': (mock_price - recent_high) / recent_high,
                    'volume_ratio': mock_volume / (sum(self.volume_history[-5:]) / 5)
                }
            )
        
        # 卖出信号：价格跌破近期低点
        elif (mock_price < recent_low * 0.99 and
              mock_rsi > 30):
            
            confidence = min(0.9, 0.6 + (recent_low - mock_price) / recent_low)
            
            return TradingSignal(
                signal_type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=mock_price,
                volume=int(mock_volume),
                indicators={
                    'signal_type': 'support_breakdown',
                    'rsi': mock_rsi,
                    'support_break': (recent_low - mock_price) / recent_low
                }
            )
        
        return None
    
    def _check_buy_conditions(self, price: float, volume: float, rsi: float) -> Optional[TradingSignal]:
        """检查买入条件"""
        if self.in_position:
            return None
        
        # 条件1: 价格突破阻力位
        resistance_level = max(self.price_history[-10:])  # 10期内最高价
        breakout_price = resistance_level * (1 + self.params.breakout_threshold)
        
        if price <= breakout_price:
            return None
        
        # 条件2: 成交量放大确认
        avg_volume = sum(self.volume_history[-10:]) / 10
        if volume < avg_volume * self.params.volume_multiplier:
            return None
        
        # 条件3: RSI不在超买区域
        if rsi > self.params.rsi_overbought:
            return None
        
        # 条件4: 短期均线向上
        if len(self.price_history) >= 5:
            sma5_current = sum(self.price_history[-5:]) / 5
            sma5_previous = sum(self.price_history[-6:-1]) / 5
            if sma5_current <= sma5_previous:
                return None
        
        # 条件5: 布林带位置
        if hasattr(self.bollinger, 'top') and hasattr(self.bollinger, 'bot'):
            bb_top = float(self.bollinger.top[0])
            bb_bot = float(self.bollinger.bot[0])
            bb_position = (price - bb_bot) / (bb_top - bb_bot) if bb_top > bb_bot else 0.5
            
            # 避免在布林带极端位置交易
            if bb_position > 0.9:
                return None
        
        # 计算信号置信度
        confidence = self._calculate_buy_confidence(price, volume, rsi, resistance_level)
        
        if confidence < self.params.min_confidence:
            return None
        
        # 确定信号强度
        strength = SignalStrength.STRONG if confidence > 0.8 else SignalStrength.MODERATE
        signal_type = SignalType.STRONG_BUY if confidence > 0.85 else SignalType.BUY
        
        return TradingSignal(
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            strategy_name=self.params.strategy_name,
            timestamp=datetime.now(),
            price=price,
            volume=int(volume),
            indicators={
                'resistance_level': resistance_level,
                'breakout_ratio': price / resistance_level,
                'volume_ratio': volume / avg_volume,
                'rsi': rsi,
                'bb_position': bb_position if 'bb_position' in locals() else 0.5
            }
        )
    
    def _check_sell_conditions(self, price: float, volume: float, rsi: float) -> Optional[TradingSignal]:
        """检查卖出条件"""
        if not self.in_position:
            return None
        
        # 条件1: 价格跌破支撑位
        support_level = min(self.price_history[-10:])  # 10期内最低价
        breakdown_price = support_level * (1 - self.params.breakout_threshold)
        
        if price >= breakdown_price:
            return None
        
        # 条件2: 成交量放大确认
        avg_volume = sum(self.volume_history[-10:]) / 10
        if volume < avg_volume * self.params.volume_multiplier:
            return None
        
        # 条件3: RSI不在超卖区域
        if rsi < self.params.rsi_oversold:
            return None
        
        # 计算信号置信度
        confidence = self._calculate_sell_confidence(price, volume, rsi, support_level)
        
        if confidence < self.params.min_confidence:
            return None
        
        # 确定信号强度
        strength = SignalStrength.STRONG if confidence > 0.8 else SignalStrength.MODERATE
        signal_type = SignalType.STRONG_SELL if confidence > 0.85 else SignalType.SELL
        
        return TradingSignal(
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            strategy_name=self.params.strategy_name,
            timestamp=datetime.now(),
            price=price,
            volume=int(volume),
            indicators={
                'support_level': support_level,
                'breakdown_ratio': price / support_level,
                'volume_ratio': volume / avg_volume,
                'rsi': rsi
            }
        )
    
    def _check_exit_conditions(self, price: float) -> Optional[TradingSignal]:
        """检查止损止盈条件"""
        if not self.in_position:
            return None
        
        # 止损检查
        if price <= self.stop_loss_price:
            confidence = 0.9  # 止损信号置信度很高
            return TradingSignal(
                signal_type=SignalType.SELL,
                strength=SignalStrength.VERY_STRONG,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=price,
                indicators={
                    'exit_type': 'stop_loss',
                    'entry_price': self.entry_price,
                    'loss_pct': (price - self.entry_price) / self.entry_price
                }
            )
        
        # 止盈检查
        if price >= self.take_profit_price:
            confidence = 0.85  # 止盈信号置信度高
            return TradingSignal(
                signal_type=SignalType.SELL,
                strength=SignalStrength.STRONG,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=price,
                indicators={
                    'exit_type': 'take_profit',
                    'entry_price': self.entry_price,
                    'profit_pct': (price - self.entry_price) / self.entry_price
                }
            )
        
        return None
    
    def _calculate_buy_confidence(self, price: float, volume: float, rsi: float, resistance: float) -> float:
        """计算买入信号置信度"""
        confidence_factors = []
        
        # 突破幅度
        breakout_ratio = price / resistance
        breakout_score = min(1.0, (breakout_ratio - 1) / self.params.breakout_threshold)
        confidence_factors.append(breakout_score * 0.3)
        
        # 成交量放大
        avg_volume = sum(self.volume_history[-10:]) / 10 if len(self.volume_history) >= 10 else volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        volume_score = min(1.0, (volume_ratio - 1) / (self.params.volume_multiplier - 1))
        confidence_factors.append(volume_score * 0.25)
        
        # RSI位置
        rsi_score = 1.0 - max(0, rsi - 50) / 50  # RSI越低越好
        confidence_factors.append(rsi_score * 0.2)
        
        # 趋势强度
        if len(self.price_history) >= 5:
            trend_slope = (self.price_history[-1] - self.price_history[-5]) / 5
            trend_score = min(1.0, max(0, trend_slope / (price * 0.01)))
            confidence_factors.append(trend_score * 0.25)
        
        return sum(confidence_factors)
    
    def _calculate_sell_confidence(self, price: float, volume: float, rsi: float, support: float) -> float:
        """计算卖出信号置信度"""
        confidence_factors = []
        
        # 跌破幅度
        breakdown_ratio = price / support
        breakdown_score = min(1.0, (1 - breakdown_ratio) / self.params.breakout_threshold)
        confidence_factors.append(breakdown_score * 0.3)
        
        # 成交量放大
        avg_volume = sum(self.volume_history[-10:]) / 10 if len(self.volume_history) >= 10 else volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        volume_score = min(1.0, (volume_ratio - 1) / (self.params.volume_multiplier - 1))
        confidence_factors.append(volume_score * 0.25)
        
        # RSI位置
        rsi_score = max(0, rsi - 50) / 50  # RSI越高越好
        confidence_factors.append(rsi_score * 0.2)
        
        # 趋势强度
        if len(self.price_history) >= 5:
            trend_slope = (self.price_history[-1] - self.price_history[-5]) / 5
            trend_score = min(1.0, max(0, -trend_slope / (price * 0.01)))
            confidence_factors.append(trend_score * 0.25)
        
        return sum(confidence_factors)
    
    def _execute_signal(self, signal: TradingSignal):
        """执行交易信号"""
        super()._execute_signal(signal)
        
        # 更新仓位状态
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            self.in_position = True
            self.entry_price = signal.price
            
            # 设置止损止盈
            self.stop_loss_price = self.entry_price * (1 - self.params.stop_loss_pct)
            self.take_profit_price = self.entry_price * (1 + self.params.take_profit_pct)
            
            self.logger.info(f"开仓: 价格={self.entry_price:.2f}, "
                           f"止损={self.stop_loss_price:.2f}, "
                           f"止盈={self.take_profit_price:.2f}")
            
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            if self.in_position:
                pnl_pct = (signal.price - self.entry_price) / self.entry_price * 100
                self.logger.info(f"平仓: 入场={self.entry_price:.2f}, "
                               f"出场={signal.price:.2f}, PnL={pnl_pct:.2f}%")
                
                # 统计成功信号
                if pnl_pct > 0:
                    self.successful_signals += 1
            
            self.in_position = False
            self.entry_price = 0.0
            self.stop_loss_price = 0.0
            self.take_profit_price = 0.0
    
    def get_strategy_status(self) -> dict:
        """获取策略状态"""
        base_status = self.get_strategy_performance()
        
        momentum_status = {
            'in_position': self.in_position,
            'entry_price': self.entry_price,
            'stop_loss_price': self.stop_loss_price,
            'take_profit_price': self.take_profit_price,
            'current_price': float(self.dataclose[0]) if len(self.dataclose) > 0 else 0.0,
            'current_rsi': float(self.rsi[0]) if hasattr(self, 'rsi') and len(self.rsi) > 0 else 50.0,
            'price_history_length': len(self.price_history),
            'last_volume': self.volume_history[-1] if self.volume_history else 0
        }
        
        base_status.update(momentum_status)
        return base_status


# 使用示例和测试
if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 动量突破策略演示")
    print("=" * 50)
    
    # 这里可以添加策略回测示例
    print("策略特点:")
    print("- 识别价格突破关键阻力位")
    print("- 成交量放大确认突破有效性") 
    print("- RSI避免超买超卖区域")
    print("- 动态止损止盈管理")
    print("- 适用于趋势性股票日内交易")
    
    print("\\n参数设置:")
    print("- 突破阈值: 2%")
    print("- 成交量倍数: 1.5倍")
    print("- RSI范围: 30-70")
    print("- 止损: 1.5%")
    print("- 止盈: 3%")
    
    print("\\n⚠️  注意事项:")
    print("- 适用于波动性适中的股票")
    print("- 避免在重要消息发布时交易")
    print("- 需要结合其他策略信号")
    print("- 严格执行止损纪律")