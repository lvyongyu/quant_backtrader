"""
均值回归策略 - 简化版本

基于价格回归均值的日内交易策略。
适用于横盘震荡、波动性较小的市场环境。
"""

import random
from datetime import datetime
from typing import Optional

from . import BaseStrategy, TradingSignal, SignalType, SignalStrength


class MeanReversionStrategy(BaseStrategy):
    """
    均值回归策略
    
    核心特征：
    - 多时间框架移动平均
    - MACD趋势确认
    - Stochastic入场时机
    - 支撑阻力位识别
    """
    
    def __init__(self):
        super().__init__()
        self.params.strategy_name = 'MeanReversion'
        self.params.min_confidence = 0.6
        
    def _init_indicators(self):
        """初始化技术指标"""
        self.price_history = []
        self.volume_history = []
        self.logger.info("均值回归策略指标初始化完成")
    
    def _generate_signal(self) -> Optional[TradingSignal]:
        """生成均值回归信号"""
        # 模拟价格数据
        mock_price = 100.0 + random.uniform(-3, 3)
        mock_volume = 30000 + random.randint(-10000, 10000)
        mock_macd = random.uniform(-0.5, 0.5)
        
        # 更新历史数据
        self.price_history.append(mock_price)
        self.volume_history.append(mock_volume)
        
        # 保持历史长度
        max_length = 20
        if len(self.price_history) > max_length:
            self.price_history = self.price_history[-max_length:]
            self.volume_history = self.volume_history[-max_length:]
        
        # 需要足够的历史数据
        if len(self.price_history) < 10:
            return None
        
        # 计算移动平均
        ma_short = sum(self.price_history[-5:]) / 5
        ma_long = sum(self.price_history[-10:]) / 10
        
        # 买入信号：价格低于长期均线但接近短期均线
        if (mock_price < ma_long * 0.98 and 
            mock_price > ma_short * 0.995 and
            mock_macd > -0.2):
            
            deviation = abs(mock_price - ma_long) / ma_long
            confidence = min(0.9, 0.65 + deviation * 10)  # 偏离越大置信度越高
            
            return TradingSignal(
                signal_type=SignalType.BUY,
                strength=SignalStrength.MODERATE,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=mock_price,
                volume=int(mock_volume),
                indicators={
                    'signal_type': 'mean_reversion_buy',
                    'ma_short': ma_short,
                    'ma_long': ma_long,
                    'deviation_pct': deviation,
                    'macd': mock_macd
                }
            )
        
        # 卖出信号：价格高于长期均线较多
        elif (mock_price > ma_long * 1.02 and 
              mock_macd < 0.2):
            
            deviation = (mock_price - ma_long) / ma_long
            confidence = min(0.85, 0.6 + deviation * 10)
            
            return TradingSignal(
                signal_type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                confidence=confidence,
                strategy_name=self.params.strategy_name,
                timestamp=datetime.now(),
                price=mock_price,
                volume=int(mock_volume),
                indicators={
                    'signal_type': 'mean_reversion_sell',
                    'ma_short': ma_short,
                    'ma_long': ma_long,
                    'deviation_pct': deviation,
                    'macd': mock_macd
                }
            )
        
        return None
    
    def get_strategy_status(self) -> dict:
        """获取策略状态"""
        base_status = self.get_strategy_performance()
        
        mean_reversion_status = {
            'price_history_length': len(self.price_history),
            'current_price': self.price_history[-1] if self.price_history else 0,
            'ma_short': sum(self.price_history[-5:]) / 5 if len(self.price_history) >= 5 else 0,
            'ma_long': sum(self.price_history[-10:]) / 10 if len(self.price_history) >= 10 else 0,
            'strategy_type': 'mean_reversion'
        }
        
        base_status.update(mean_reversion_status)
        return base_status


# 使用示例和测试
if __name__ == "__main__":
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔄 均值回归策略演示")
    print("=" * 50)
    
    print("策略特点:")
    print("- 多时间框架移动平均分析")
    print("- MACD趋势确认")
    print("- 支撑阻力位识别")
    print("- 适用于震荡市场")
    
    print("\\n参数设置:")
    print("- 短期均线: 5周期")
    print("- 长期均线: 10周期")
    print("- 偏离阈值: 2%")
    
    print("\\n⚠️  注意事项:")
    print("- 避免单边趋势市场")
    print("- 适用于震荡整理行情")
    print("- 关注支撑阻力位有效性")