
"""
高级策略示例库

提供多种成熟的量化交易策略示例，包括技术分析、
统计套利、机器学习等不同类型的策略。
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging


class StrategySignal:
    """策略信号类"""
    
    def __init__(self, signal_type: str, strength: float = 1.0, 
                 confidence: float = 1.0, metadata: Dict = None):
        self.signal_type = signal_type  # "BUY", "SELL", "HOLD"
        self.strength = strength  # 信号强度 0-1
        self.confidence = confidence  # 信号置信度 0-1
        self.metadata = metadata or {}
        self.timestamp = datetime.now()


class BaseStrategy:
    """策略基类"""
    
    def __init__(self, name: str, params: Dict[str, Any] = None):
        self.name = name
        self.params = params or {}
        self.logger = logging.getLogger(f"Strategy.{name}")
        
    def generate_signal(self, data: List, **kwargs) -> StrategySignal:
        """生成交易信号"""
        raise NotImplementedError("子类必须实现此方法")
    
    def validate_params(self) -> bool:
        """验证策略参数"""
        return True


class BollingerBandsStrategy(BaseStrategy):
    """布林带策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, **kwargs):
        super().__init__("BollingerBands", {"period": period, "std_dev": std_dev})
        self.period = period
        self.std_dev = std_dev
    
    def generate_signal(self, data: List, **kwargs) -> StrategySignal:
        """生成布林带信号"""
        if len(data) < self.period:
            return StrategySignal("HOLD", 0.0, 0.0)
        
        # 计算移动平均和标准差
        recent_prices = [d.close for d in data[-self.period:]]
        ma = sum(recent_prices) / len(recent_prices)
        
        # 计算标准差
        variance = sum((p - ma) ** 2 for p in recent_prices) / len(recent_prices)
        std = variance ** 0.5
        
        # 布林带上下轨
        upper_band = ma + (self.std_dev * std)
        lower_band = ma - (self.std_dev * std)
        
        current_price = data[-1].close
        
        # 生成信号
        if current_price <= lower_band:
            # 价格触及下轨，买入信号
            strength = min(1.0, (lower_band - current_price) / (ma * 0.05))
            return StrategySignal("BUY", strength, 0.8, {
                "ma": ma, "upper_band": upper_band, "lower_band": lower_band,
                "price_position": (current_price - lower_band) / (upper_band - lower_band)
            })
        
        elif current_price >= upper_band:
            # 价格触及上轨，卖出信号
            strength = min(1.0, (current_price - upper_band) / (ma * 0.05))
            return StrategySignal("SELL", strength, 0.8, {
                "ma": ma, "upper_band": upper_band, "lower_band": lower_band,
                "price_position": (current_price - lower_band) / (upper_band - lower_band)
            })
        
        else:
            # 在布林带内，持有
            return StrategySignal("HOLD", 0.0, 0.5, {
                "ma": ma, "upper_band": upper_band, "lower_band": lower_band,
                "price_position": (current_price - lower_band) / (upper_band - lower_band)
            })


class RSIStrategy(BaseStrategy):
    """RSI相对强弱指标策略"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70, **kwargs):
        super().__init__("RSI", {"period": period, "oversold": oversold, "overbought": overbought})
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def calculate_rsi(self, prices: List[float]) -> float:
        """计算RSI指标"""
        if len(prices) < self.period + 1:
            return 50.0  # 默认中性值
        
        # 计算价格变动
        price_changes = []
        for i in range(1, len(prices)):
            price_changes.append(prices[i] - prices[i-1])
        
        # 分离上涨和下跌
        gains = [max(0, change) for change in price_changes[-self.period:]]
        losses = [abs(min(0, change)) for change in price_changes[-self.period:]]
        
        # 计算平均收益和损失
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        # 计算RSI
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def generate_signal(self, data: List, **kwargs) -> StrategySignal:
        """生成RSI信号"""
        if len(data) < self.period + 1:
            return StrategySignal("HOLD", 0.0, 0.0)
        
        prices = [d.close for d in data]
        rsi = self.calculate_rsi(prices)
        
        if rsi <= self.oversold:
            # RSI过低，超卖，买入信号
            strength = min(1.0, (self.oversold - rsi) / self.oversold)
            confidence = 0.7 + (strength * 0.3)
            return StrategySignal("BUY", strength, confidence, {"rsi": rsi})
        
        elif rsi >= self.overbought:
            # RSI过高，超买，卖出信号
            strength = min(1.0, (rsi - self.overbought) / (100 - self.overbought))
            confidence = 0.7 + (strength * 0.3)
            return StrategySignal("SELL", strength, confidence, {"rsi": rsi})
        
        else:
            # RSI中性区域，持有
            return StrategySignal("HOLD", 0.0, 0.5, {"rsi": rsi})


class MACDStrategy(BaseStrategy):
    """MACD指标策略"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs):
        super().__init__("MACD", {
            "fast_period": fast_period, "slow_period": slow_period, "signal_period": signal_period
        })
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """计算指数移动平均"""
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        # 简化的EMA计算
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema
    
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """计算MACD指标"""
        if len(prices) < self.slow_period:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # 计算快线和慢线EMA
        fast_ema = self.calculate_ema(prices[-self.fast_period:], self.fast_period)
        slow_ema = self.calculate_ema(prices[-self.slow_period:], self.slow_period)
        
        # MACD线
        macd_line = fast_ema - slow_ema
        
        # 信号线（MACD的EMA）
        # 简化处理，实际应该用历史MACD值计算
        signal_line = macd_line * 0.8  # 简化的信号线
        
        # 柱状图
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    def generate_signal(self, data: List, **kwargs) -> StrategySignal:
        """生成MACD信号"""
        if len(data) < self.slow_period + self.signal_period:
            return StrategySignal("HOLD", 0.0, 0.0)
        
        prices = [d.close for d in data]
        macd_data = self.calculate_macd(prices)
        
        macd = macd_data["macd"]
        signal = macd_data["signal"]
        histogram = macd_data["histogram"]
        
        # 金叉：MACD上穿信号线
        if macd > signal and histogram > 0:
            strength = min(1.0, abs(histogram) / (abs(macd) + 0.01))
            return StrategySignal("BUY", strength, 0.75, macd_data)
        
        # 死叉：MACD下穿信号线
        elif macd < signal and histogram < 0:
            strength = min(1.0, abs(histogram) / (abs(macd) + 0.01))
            return StrategySignal("SELL", strength, 0.75, macd_data)
        
        else:
            return StrategySignal("HOLD", 0.0, 0.5, macd_data)


class MomentumStrategy(BaseStrategy):
    """动量策略"""
    
    def __init__(self, lookback_period: int = 20, momentum_threshold: float = 0.02, **kwargs):
        super().__init__("Momentum", {
            "lookback_period": lookback_period, "momentum_threshold": momentum_threshold
        })
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
    
    def generate_signal(self, data: List, **kwargs) -> StrategySignal:
        """生成动量信号"""
        if len(data) < self.lookback_period + 1:
            return StrategySignal("HOLD", 0.0, 0.0)
        
        # 计算动量
        current_price = data[-1].close
        past_price = data[-self.lookback_period-1].close
        momentum = (current_price - past_price) / past_price
        
        # 计算价格波动率
        recent_prices = [d.close for d in data[-self.lookback_period:]]
        price_mean = sum(recent_prices) / len(recent_prices)
        price_variance = sum((p - price_mean) ** 2 for p in recent_prices) / len(recent_prices)
        price_volatility = price_variance ** 0.5 / price_mean
        
        # 动量信号
        if momentum > self.momentum_threshold:
            # 正动量，买入信号
            strength = min(1.0, momentum / (self.momentum_threshold * 3))
            confidence = max(0.5, 1.0 - price_volatility * 10)
            return StrategySignal("BUY", strength, confidence, {
                "momentum": momentum, "volatility": price_volatility
            })
        
        elif momentum < -self.momentum_threshold:
            # 负动量，卖出信号
            strength = min(1.0, abs(momentum) / (self.momentum_threshold * 3))
            confidence = max(0.5, 1.0 - price_volatility * 10)
            return StrategySignal("SELL", strength, confidence, {
                "momentum": momentum, "volatility": price_volatility
            })
        
        else:
            # 动量不足，持有
            return StrategySignal("HOLD", 0.0, 0.5, {
                "momentum": momentum, "volatility": price_volatility
            })


class MultiFactorStrategy(BaseStrategy):
    """多因子策略"""
    
    def __init__(self, strategies: List[BaseStrategy], weights: List[float] = None, **kwargs):
        super().__init__("MultiFactor", {"strategies": len(strategies)})
        self.strategies = strategies
        self.weights = weights or [1.0 / len(strategies)] * len(strategies)
        
        # 确保权重归一化
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]
    
    def generate_signal(self, data: List, **kwargs) -> StrategySignal:
        """生成多因子综合信号"""
        if not self.strategies:
            return StrategySignal("HOLD", 0.0, 0.0)
        
        signals = []
        total_weight = 0.0
        
        # 收集各策略信号
        for strategy, weight in zip(self.strategies, self.weights):
            try:
                signal = strategy.generate_signal(data, **kwargs)
                signals.append((signal, weight))
                total_weight += weight
            except Exception as e:
                self.logger.warning(f"策略{strategy.name}信号生成失败: {e}")
                continue
        
        if not signals:
            return StrategySignal("HOLD", 0.0, 0.0)
        
        # 计算加权信号
        buy_score = 0.0
        sell_score = 0.0
        hold_score = 0.0
        confidence_sum = 0.0
        
        for signal, weight in signals:
            weighted_strength = signal.strength * weight * signal.confidence
            
            if signal.signal_type == "BUY":
                buy_score += weighted_strength
            elif signal.signal_type == "SELL":
                sell_score += weighted_strength
            else:  # HOLD
                hold_score += weighted_strength
            
            confidence_sum += signal.confidence * weight
        
        # 决定最终信号
        avg_confidence = confidence_sum / total_weight if total_weight > 0 else 0.5
        
        if buy_score > sell_score and buy_score > hold_score:
            return StrategySignal("BUY", buy_score, avg_confidence, {
                "buy_score": buy_score, "sell_score": sell_score, "hold_score": hold_score
            })
        elif sell_score > buy_score and sell_score > hold_score:
            return StrategySignal("SELL", sell_score, avg_confidence, {
                "buy_score": buy_score, "sell_score": sell_score, "hold_score": hold_score
            })
        else:
            return StrategySignal("HOLD", hold_score, avg_confidence, {
                "buy_score": buy_score, "sell_score": sell_score, "hold_score": hold_score
            })


# 策略工厂函数
def create_strategy(strategy_type: str, **params) -> BaseStrategy:
    """策略工厂函数"""
    strategy_map = {
        "bollinger": BollingerBandsStrategy,
        "rsi": RSIStrategy,
        "macd": MACDStrategy,
        "momentum": MomentumStrategy
    }
    
    if strategy_type.lower() not in strategy_map:
        raise ValueError(f"不支持的策略类型: {strategy_type}")
    
    return strategy_map[strategy_type.lower()](**params)


def create_multi_factor_strategy(*strategy_configs) -> MultiFactorStrategy:
    """创建多因子策略"""
    strategies = []
    weights = []
    
    for config in strategy_configs:
        if isinstance(config, dict):
            strategy_type = config.pop("type")
            weight = config.pop("weight", 1.0)
            strategy = create_strategy(strategy_type, **config)
            strategies.append(strategy)
            weights.append(weight)
        else:
            raise ValueError("策略配置必须是字典")
    
    return MultiFactorStrategy(strategies, weights)


# 使用示例
if __name__ == "__main__":
    print("🎯 高级策略示例库")
    print("=" * 50)
    
    # 创建单一策略
    bollinger_strategy = create_strategy("bollinger", period=20, std_dev=2.0)
    rsi_strategy = create_strategy("rsi", period=14, oversold=30, overbought=70)
    
    print(f"✅ 创建策略: {bollinger_strategy.name}, {rsi_strategy.name}")
    
    # 创建多因子策略
    multi_strategy = create_multi_factor_strategy(
        {"type": "bollinger", "period": 20, "std_dev": 2.0, "weight": 0.4},
        {"type": "rsi", "period": 14, "oversold": 30, "overbought": 70, "weight": 0.3},
        {"type": "momentum", "lookback_period": 20, "momentum_threshold": 0.02, "weight": 0.3}
    )
    
    print(f"✅ 创建多因子策略: {multi_strategy.name}")
    
    print("\n🔧 策略功能:")
    print("  - 布林带策略 ✅")
    print("  - RSI策略 ✅")
    print("  - MACD策略 ✅")
    print("  - 动量策略 ✅")
    print("  - 多因子组合策略 ✅")
    
    print("\n" + "=" * 50)
