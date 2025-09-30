"""
回测框架增强工具模块

提供额外的工具函数和实用程序，包括数据处理、
指标计算、风险管理等功能。
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union


class TechnicalIndicators:
    """技术指标计算工具"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> float:
        """简单移动平均"""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0.0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def ema(prices: List[float], period: int, alpha: float = None) -> float:
        """指数移动平均"""
        if not prices:
            return 0.0
        
        if alpha is None:
            alpha = 2 / (period + 1)
        
        ema_val = prices[0]
        for price in prices[1:]:
            ema_val = alpha * price + (1 - alpha) * ema_val
        
        return ema_val
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """相对强弱指标"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(0, change))
            losses.append(abs(min(0, change)))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """布林带指标"""
        if len(prices) < period:
            ma = sum(prices) / len(prices) if prices else 0
            return {"middle": ma, "upper": ma, "lower": ma}
        
        recent_prices = prices[-period:]
        ma = sum(recent_prices) / len(recent_prices)
        
        variance = sum((p - ma) ** 2 for p in recent_prices) / len(recent_prices)
        std = variance ** 0.5
        
        return {
            "middle": ma,
            "upper": ma + (std_dev * std),
            "lower": ma - (std_dev * std)
        }
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """MACD指标"""
        if len(prices) < slow:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        fast_ema = TechnicalIndicators.ema(prices, fast)
        slow_ema = TechnicalIndicators.ema(prices, slow)
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line * 0.8  # 简化的信号线
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }


class RiskManager:
    """风险管理工具"""
    
    def __init__(self, max_position_size: float = 0.1, max_daily_loss: float = 0.02):
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.daily_pnl = 0.0
        self.positions = {}
    
    def check_position_size(self, symbol: str, position_value: float, total_equity: float) -> bool:
        """检查仓位大小限制"""
        position_ratio = position_value / total_equity if total_equity > 0 else 0
        return position_ratio <= self.max_position_size
    
    def check_daily_loss(self, current_pnl: float, total_equity: float) -> bool:
        """检查日损失限制"""
        loss_ratio = abs(current_pnl) / total_equity if total_equity > 0 else 0
        return loss_ratio <= self.max_daily_loss
    
    def calculate_position_size(self, signal_strength: float, equity: float, price: float, 
                              risk_per_trade: float = 0.01) -> int:
        """计算建议仓位大小"""
        # 基于信号强度和风险管理的仓位计算
        risk_amount = equity * risk_per_trade * signal_strength
        shares = int(risk_amount / price) if price > 0 else 0
        
        # 确保不超过最大仓位限制
        max_shares = int((equity * self.max_position_size) / price) if price > 0 else 0
        
        return min(shares, max_shares)


class DataValidator:
    """数据验证工具"""
    
    @staticmethod
    def validate_price_data(data_point) -> bool:
        """验证价格数据"""
        try:
            # 检查基本属性
            if not hasattr(data_point, 'open') or not hasattr(data_point, 'close'):
                return False
            
            # 检查价格合理性
            prices = [data_point.open, data_point.high, data_point.low, data_point.close]
            if any(p <= 0 for p in prices):
                return False
            
            # 检查高低价关系
            if data_point.high < max(data_point.open, data_point.close):
                return False
            if data_point.low > min(data_point.open, data_point.close):
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def detect_outliers(prices: List[float], threshold: float = 3.0) -> List[int]:
        """检测价格异常值"""
        if len(prices) < 3:
            return []
        
        outliers = []
        mean_price = sum(prices) / len(prices)
        
        # 计算标准差
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        
        # 检测异常值
        for i, price in enumerate(prices):
            z_score = abs(price - mean_price) / std_dev if std_dev > 0 else 0
            if z_score > threshold:
                outliers.append(i)
        
        return outliers
    
    @staticmethod
    def fill_missing_data(data: List, method: str = "forward") -> List:
        """填充缺失数据"""
        if not data:
            return data
        
        filled_data = list(data)
        
        if method == "forward":
            # 前向填充
            for i in range(1, len(filled_data)):
                if filled_data[i] is None:
                    filled_data[i] = filled_data[i-1]
        
        elif method == "backward":
            # 后向填充
            for i in range(len(filled_data) - 2, -1, -1):
                if filled_data[i] is None:
                    filled_data[i] = filled_data[i+1]
        
        elif method == "interpolate":
            # 线性插值
            for i in range(1, len(filled_data) - 1):
                if filled_data[i] is None:
                    # 找到前后非空值
                    prev_val = filled_data[i-1]
                    next_idx = i + 1
                    while next_idx < len(filled_data) and filled_data[next_idx] is None:
                        next_idx += 1
                    
                    if next_idx < len(filled_data):
                        next_val = filled_data[next_idx]
                        # 线性插值
                        steps = next_idx - i + 1
                        step_size = (next_val - prev_val) / steps
                        filled_data[i] = prev_val + step_size
        
        return filled_data


class PerformanceTracker:
    """性能跟踪工具"""
    
    def __init__(self):
        self.trades = []
        self.daily_returns = []
        self.equity_curve = []
    
    def add_trade(self, entry_time: datetime, exit_time: datetime, 
                  pnl: float, symbol: str = ""):
        """添加交易记录"""
        self.trades.append({
            "entry_time": entry_time,
            "exit_time": exit_time,
            "pnl": pnl,
            "symbol": symbol,
            "duration": (exit_time - entry_time).total_seconds() / 86400  # 天数
        })
    
    def add_daily_return(self, date: datetime, return_pct: float):
        """添加日收益率"""
        self.daily_returns.append({
            "date": date,
            "return": return_pct
        })
    
    def add_equity_point(self, date: datetime, equity: float):
        """添加权益点"""
        self.equity_curve.append({
            "date": date,
            "equity": equity
        })
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        if not self.trades:
            return {}
        
        # 交易统计
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t["pnl"] > 0]
        losing_trades = [t for t in self.trades if t["pnl"] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss < 0 else 0
        
        # 收益统计
        total_pnl = sum(t["pnl"] for t in self.trades)
        
        # 时间统计
        avg_trade_duration = sum(t["duration"] for t in self.trades) / len(self.trades)
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "total_pnl": total_pnl,
            "avg_trade_duration": avg_trade_duration
        }


class ConfigManager:
    """配置管理工具"""
    
    def __init__(self, config_file: str = "backtest_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"加载配置文件失败: {e}")
        
        # 默认配置
        return {
            "data": {
                "provider": "mock",
                "cache_enabled": True,
                "cache_duration": 3600
            },
            "backtest": {
                "initial_capital": 100000,
                "commission": 0.001,
                "slippage": 0.0005
            },
            "risk": {
                "max_position_size": 0.1,
                "max_daily_loss": 0.02,
                "stop_loss": 0.05
            },
            "optimization": {
                "default_algorithm": "grid",
                "max_iterations": 100,
                "population_size": 50
            }
        }
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def get(self, key_path: str, default=None):
        """获取配置值"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """设置配置值"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value


# 使用示例
if __name__ == "__main__":
    print("🛠️ 回测框架增强工具")
    print("=" * 50)
    
    # 测试技术指标
    test_prices = [100, 102, 98, 105, 103, 107, 104, 108, 106, 110]
    
    sma = TechnicalIndicators.sma(test_prices, 5)
    rsi = TechnicalIndicators.rsi(test_prices, 5)
    bb = TechnicalIndicators.bollinger_bands(test_prices, 5)
    
    print(f"技术指标测试:")
    print(f"  SMA(5): {sma:.2f}")
    print(f"  RSI(5): {rsi:.2f}")
    print(f"  布林带: 上轨{bb['upper']:.2f}, 中轨{bb['middle']:.2f}, 下轨{bb['lower']:.2f}")
    
    # 测试风险管理
    risk_mgr = RiskManager(max_position_size=0.1, max_daily_loss=0.02)
    position_size = risk_mgr.calculate_position_size(0.8, 100000, 100, 0.01)
    print(f"风险管理测试:")
    print(f"  建议仓位: {position_size}股")
    
    # 测试配置管理
    config_mgr = ConfigManager()
    initial_capital = config_mgr.get("backtest.initial_capital", 100000)
    print(f"配置管理测试:")
    print(f"  初始资金: ${initial_capital:,}")
    
    print("\n✅ 增强工具模块测试完成")