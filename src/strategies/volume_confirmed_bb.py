"""
Volume Confirmed Bollinger Bands Strategy
量价确认布林带策略 - 下一个重要增强功能
"""

import backtrader as bt
from .base_strategy import BaseStrategy


class VolumeConfirmedBollingerStrategy(BaseStrategy):
    """
    量价确认的增强布林带策略
    
    在现有MACD+布林带基础上，增加成交量确认：
    - OBV (On Balance Volume) 趋势确认
    - 成交量突破验证
    - VWAP位置分析
    """
    
    params = (
        ('bb_period', 20),
        ('bb_devfactor', 2),
        ('volume_period', 20),        # 成交量移动平均周期
        ('volume_multiplier', 1.5),   # 成交量突破倍数
    )
    
    def __init__(self):
        super().__init__()
        
        # 现有指标
        self.bollinger = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_devfactor
        )
        
        self.macd = bt.indicators.MACDHisto(self.data.close)
        
        # 新增：成交量指标
        self.volume_sma = bt.indicators.SimpleMovingAverage(
            self.data.volume,
            period=self.params.volume_period
        )
        
        # OBV - 平衡成交量
        self.obv = bt.indicators.OnBalanceVolume(self.data)
        
        # VWAP - 成交量加权平均价 (简化版)
        self.vwap = self._calculate_vwap()
        
    def _calculate_vwap(self):
        """计算成交量加权平均价格"""
        # 简化版VWAP计算
        typical_price = (self.data.high + self.data.low + self.data.close) / 3
        return bt.indicators.SimpleMovingAverage(
            typical_price * self.data.volume, period=20
        ) / bt.indicators.SimpleMovingAverage(self.data.volume, period=20)
    
    def buy_signal(self) -> bool:
        """增强的买入信号：价格+MACD+成交量三重确认"""
        
        # 1. 布林带信号
        price_signal = self.data.close[0] <= self.bollinger.lines.bot[0] * 1.02
        
        # 2. MACD确认
        macd_bullish = self.macd.macd[0] > self.macd.signal[0]
        
        # 3. 成交量确认 (新增)
        volume_breakout = self.data.volume[0] > self.volume_sma[0] * self.params.volume_multiplier
        obv_rising = len(self) > 5 and self.obv[0] > self.obv[-5]  # OBV上升趋势
        price_above_vwap = self.data.close[0] > self.vwap[0]  # 价格高于VWAP
        
        # 成交量确认：至少满足2个条件
        volume_confirmed = sum([volume_breakout, obv_rising, price_above_vwap]) >= 2
        
        return price_signal and macd_bullish and volume_confirmed
    
    def sell_signal(self) -> bool:
        """增强的卖出信号：价格+MACD+成交量三重确认"""
        
        # 1. 布林带信号
        price_signal = self.data.close[0] >= self.bollinger.lines.top[0] * 0.98
        
        # 2. MACD确认
        macd_bearish = self.macd.macd[0] < self.macd.signal[0]
        
        # 3. 成交量确认 (新增)
        volume_breakout = self.data.volume[0] > self.volume_sma[0] * self.params.volume_multiplier
        obv_falling = len(self) > 5 and self.obv[0] < self.obv[-5]  # OBV下降趋势
        price_below_vwap = self.data.close[0] < self.vwap[0]  # 价格低于VWAP
        
        # 成交量确认：至少满足2个条件
        volume_confirmed = sum([volume_breakout, obv_falling, price_below_vwap]) >= 2
        
        return price_signal and (macd_bearish or volume_confirmed)