"""
投资组合分析模块

提供现代投资组合理论和高级分析功能：
1. 投资组合优化
2. 风险分析
3. 绩效归因
4. 投资组合构建
5. 资产配置
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
import pandas as pd


class OptimizationMethod(Enum):
    """优化方法"""
    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MINIMUM_VARIANCE = "minimum_variance"
    MAXIMUM_SHARPE = "maximum_sharpe"
    BLACK_LITTERMAN = "black_litterman"
    HIERARCHICAL_RISK_PARITY = "hierarchical_risk_parity"


class RiskMeasure(Enum):
    """风险度量"""
    VARIANCE = "variance"
    VOLATILITY = "volatility"
    VAR = "value_at_risk"
    CVAR = "conditional_var"
    MAX_DRAWDOWN = "max_drawdown"
    SEMI_VARIANCE = "semi_variance"


class AllocationConstraint(Enum):
    """配置约束"""
    LONG_ONLY = "long_only"
    LONG_SHORT = "long_short"
    SECTOR_LIMITS = "sector_limits"
    TURNOVER_LIMITS = "turnover_limits"


@dataclass
class AssetData:
    """资产数据"""
    symbol: str
    returns: pd.Series
    prices: pd.Series
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    beta: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_statistics(self) -> Dict[str, float]:
        """获取统计数据"""
        return {
            'mean_return': self.returns.mean(),
            'volatility': self.returns.std(),
            'sharpe_ratio': self.returns.mean() / self.returns.std() if self.returns.std() > 0 else 0,
            'max_drawdown': self.calculate_max_drawdown(),
            'skewness': self.returns.skew(),
            'kurtosis': self.returns.kurtosis()
        }
    
    def calculate_max_drawdown(self) -> float:
        """计算最大回撤"""
        cumulative = (1 + self.returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()


@dataclass
class Portfolio:
    """投资组合"""
    name: str
    weights: Dict[str, float]
    assets: Dict[str, AssetData]
    benchmark: Optional[str] = None
    inception_date: Optional[datetime] = None
    rebalance_frequency: str = "monthly"
    
    def get_portfolio_returns(self) -> pd.Series:
        """计算投资组合收益率"""
        if not self.assets or not self.weights:
            return pd.Series()
        
        # 获取所有资产的收益率
        returns_df = pd.DataFrame({
            symbol: asset.returns for symbol, asset in self.assets.items()
            if symbol in self.weights
        })
        
        # 计算加权收益率
        weights_series = pd.Series(self.weights)
        portfolio_returns = (returns_df * weights_series).sum(axis=1)
        
        return portfolio_returns.dropna()
    
    def get_portfolio_value(self, initial_value: float = 100000) -> pd.Series:
        """计算投资组合价值"""
        returns = self.get_portfolio_returns()
        return initial_value * (1 + returns).cumprod()
    
    def validate_weights(self) -> bool:
        """验证权重"""
        total_weight = sum(self.weights.values())
        return abs(total_weight - 1.0) < 1e-6
    
    def get_portfolio_statistics(self) -> Dict[str, float]:
        """获取投资组合统计数据"""
        returns = self.get_portfolio_returns()
        
        if len(returns) == 0:
            return {}
        
        return {
            'mean_return': returns.mean(),
            'volatility': returns.std(),
            'sharpe_ratio': returns.mean() / returns.std() if returns.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(returns),
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis(),
            'var_95': returns.quantile(0.05),
            'cvar_95': returns[returns <= returns.quantile(0.05)].mean()
        }
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()


@dataclass
class OptimizationConstraints:
    """优化约束条件"""
    min_weight: float = 0.0
    max_weight: float = 1.0
    sector_limits: Optional[Dict[str, Tuple[float, float]]] = None
    turnover_limit: Optional[float] = None
    max_assets: Optional[int] = None
    risk_target: Optional[float] = None
    return_target: Optional[float] = None
    
    def validate_constraints(self, weights: Dict[str, float],
                           assets: Dict[str, AssetData]) -> bool:
        """验证约束条件"""
        # 权重约束
        for weight in weights.values():
            if weight < self.min_weight or weight > self.max_weight:
                return False
        
        # 资产数量约束
        if self.max_assets and len([w for w in weights.values() if w > 1e-6]) > self.max_assets:
            return False
        
        # 行业约束
        if self.sector_limits:
            sector_weights = {}
            for symbol, weight in weights.items():
                if symbol in assets:
                    sector = assets[symbol].sector
                    if sector:
                        sector_weights[sector] = sector_weights.get(sector, 0) + weight
            
            for sector, (min_limit, max_limit) in self.sector_limits.items():
                sector_weight = sector_weights.get(sector, 0)
                if sector_weight < min_limit or sector_weight > max_limit:
                    return False
        
        return True


@dataclass
class RiskMetrics:
    """风险指标"""
    portfolio_var: float
    portfolio_volatility: float
    var_95: float
    cvar_95: float
    max_drawdown: float
    beta: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    downside_deviation: Optional[float] = None
    sortino_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'portfolio_var': self.portfolio_var,
            'portfolio_volatility': self.portfolio_volatility,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'max_drawdown': self.max_drawdown,
            'beta': self.beta,
            'tracking_error': self.tracking_error,
            'information_ratio': self.information_ratio,
            'downside_deviation': self.downside_deviation,
            'sortino_ratio': self.sortino_ratio
        }


@dataclass
class PerformanceAttribution:
    """绩效归因"""
    total_return: float
    benchmark_return: float
    active_return: float
    asset_selection: float
    allocation_effect: float
    interaction_effect: float
    sector_attribution: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_return': self.total_return,
            'benchmark_return': self.benchmark_return,
            'active_return': self.active_return,
            'asset_selection': self.asset_selection,
            'allocation_effect': self.allocation_effect,
            'interaction_effect': self.interaction_effect,
            'sector_attribution': self.sector_attribution
        }


@dataclass
class OptimizationResult:
    """优化结果"""
    optimal_weights: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    method: OptimizationMethod
    constraints: OptimizationConstraints
    optimization_status: str
    risk_metrics: Optional[RiskMetrics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'optimal_weights': self.optimal_weights,
            'expected_return': self.expected_return,
            'expected_risk': self.expected_risk,
            'sharpe_ratio': self.sharpe_ratio,
            'method': self.method.value,
            'optimization_status': self.optimization_status,
            'risk_metrics': self.risk_metrics.to_dict() if self.risk_metrics else None
        }


# 导出
__all__ = [
    'OptimizationMethod', 'RiskMeasure', 'AllocationConstraint',
    'AssetData', 'Portfolio', 'OptimizationConstraints', 'RiskMetrics',
    'PerformanceAttribution', 'OptimizationResult'
]