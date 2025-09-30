"""
动量突破策略 - 简化版本

基于价格动量和突破信号的日内交易策略。
适用于趋势明显、波动性适中的股票。
"""

import random
from datetime import datetime
from typing import Optional

from . import BaseStrategy, TradingSignal, SignalType, SignalStrength


class MomentumBreakoutStrategy(BaseStrategy):
    """
    动量突破策略
    
    核心特征：
    - 识别价格突破
    - 成交量确认  
    - RSI过滤
    - 动态止损
    """
    
    def __init__(self):
        super().__init__()
        self.params.strategy_name = 'MomentumBreakout'
        self.params.min_confidence = 0.65
        
    def _init_indicators(self):
        """初始化技术指标"""
        self.price_history = []
        self.volume_history = []
        self.logger.info("动量突破策略指标初始化完成")
    
    def _generate_signal(self) -> Optional[TradingSignal]:
        """生成动量突破信号"""
        # 模拟价格数据
        mock_price = 150.0 + random.uniform(-5, 5)
        mock_volume = 50000 + random.randint(-20000, 20000)
        mock_rsi = random.uniform(20, 80)
        
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
    
    def get_strategy_status(self) -> dict:
        """获取策略状态"""
        base_status = self.get_strategy_performance()
        
        momentum_status = {
            'price_history_length': len(self.price_history),
            'volume_history_length': len(self.volume_history),
            'current_price': self.price_history[-1] if self.price_history else 0,
            'recent_volume_avg': sum(self.volume_history[-5:]) / 5 if len(self.volume_history) >= 5 else 0,
            'strategy_type': 'momentum_breakout'
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
    
    print("📈 动量突破策略演示")
    print("=" * 50)
    
    print("策略特点:")
    print("- 识别价格突破关键位置")
    print("- 成交量确认突破有效性") 
    print("- RSI指标过滤超买超卖")
    print("- 动态止损止盈管理")
    
    print("\\n参数设置:")
    print("- 突破阈值: 1%")
    print("- 成交量倍数: 1.2x")
    print("- RSI范围: 30-70")
    
    print("\\n⚠️  注意事项:")
    print("- 适用于趋势明确的市场")
    print("- 避免震荡行情使用")
    print("- 严格执行止损规则")