"""
成交量确认策略 - 简化版本

基于成交量分析的交易策略，通过识别成交量异常和价量配合来发现交易机会。
适用于捕获主力资金进出动作和市场情绪变化。
"""

import random
from datetime import datetime
from typing import Optional

from . import BaseStrategy, TradingSignal, SignalType, SignalStrength


class VolumeConfirmationStrategy(BaseStrategy):
    """
    成交量确认策略
    
    核心特征：
    - 成交量异常识别
    - 价量配合分析
    - 量价背离检测
    - OBV趋势确认
    """
    
    def __init__(self):
        super().__init__()
        self.params.strategy_name = 'VolumeConfirmation'
        self.params.min_confidence = 0.65
        
    def _init_indicators(self):
        """初始化技术指标"""
        self.price_history = []
        self.volume_history = []
        self.obv_values = []
        self.logger.info("成交量确认策略指标初始化完成")
    
    def _generate_signal(self) -> Optional[TradingSignal]:
        """生成成交量确认信号"""
        # 模拟价格和成交量数据
        mock_price = 120.0 + random.uniform(-4, 4)
        mock_volume = 40000 + random.randint(-15000, 25000)
        
        # 更新历史数据
        self.price_history.append(mock_price)
        self.volume_history.append(mock_volume)
        
        # 计算OBV
        if self.obv_values:
            prev_price = self.price_history[-2] if len(self.price_history) > 1 else mock_price
            prev_obv = self.obv_values[-1]
            
            if mock_price > prev_price:
                new_obv = prev_obv + mock_volume
            elif mock_price < prev_price:
                new_obv = prev_obv - mock_volume
            else:
                new_obv = prev_obv
            
            self.obv_values.append(new_obv)
        else:
            self.obv_values.append(mock_volume)
        
        # 保持历史长度
        max_length = 20
        if len(self.price_history) > max_length:
            self.price_history = self.price_history[-max_length:]
            self.volume_history = self.volume_history[-max_length:]
            self.obv_values = self.obv_values[-max_length:]
        
        # 需要足够的历史数据
        if len(self.volume_history) < 10:
            return None
        
        # 分析成交量异常
        avg_volume = sum(self.volume_history[-10:]) / 10
        volume_ratio = mock_volume / avg_volume
        
        # 价格变化
        price_change = 0
        if len(self.price_history) > 1:
            price_change = (mock_price - self.price_history[-2]) / self.price_history[-2]
        
        # OBV趋势
        obv_trend = 0
        if len(self.obv_values) > 5:
            obv_trend = (self.obv_values[-1] - self.obv_values[-6]) / abs(self.obv_values[-6])
        
        # 买入信号：放量上涨
        if (volume_ratio > 1.5 and 
            price_change > 0.005 and
            obv_trend > 0):
            
            confidence = min(0.9, 0.6 + (volume_ratio - 1) * 0.2 + price_change * 10)
            
            return TradingSignal(
                signal_type=SignalType.BUY,
                strength=SignalStrength.STRONG if volume_ratio > 2.0 else SignalStrength.MODERATE,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=mock_price,
                volume=int(mock_volume),
                indicators={
                    'signal_type': 'volume_surge_buy',
                    'volume_ratio': volume_ratio,
                    'price_change': price_change,
                    'obv_trend': obv_trend
                }
            )
        
        # 卖出信号：放量下跌或缩量上涨
        elif ((volume_ratio > 1.3 and price_change < -0.005) or 
              (volume_ratio < 0.7 and price_change > 0.01)):
            
            confidence = min(0.85, 0.65 + abs(price_change) * 15)
            
            return TradingSignal(
                signal_type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=mock_price,
                volume=int(mock_volume),
                indicators={
                    'signal_type': 'volume_divergence_sell',
                    'volume_ratio': volume_ratio,
                    'price_change': price_change,
                    'obv_trend': obv_trend
                }
            )
        
        return None
    
    def get_strategy_status(self) -> dict:
        """获取策略状态"""
        base_status = self.get_strategy_performance()
        
        volume_status = {
            'volume_history_length': len(self.volume_history),
            'current_volume': self.volume_history[-1] if self.volume_history else 0,
            'avg_volume': sum(self.volume_history[-10:]) / 10 if len(self.volume_history) >= 10 else 0,
            'current_obv': self.obv_values[-1] if self.obv_values else 0,
            'strategy_type': 'volume_confirmation'
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
    
    print("\\n参数设置:")
    print("- 放量倍数: 1.5倍")
    print("- 缩量倍数: 0.7倍")
    print("- 价格变化阈值: 0.5%")
    
    print("\\n⚠️  注意事项:")
    print("- 成交量数据质量要求高")
    print("- 避免在特殊时段交易")
    print("- 结合基本面消息验证")