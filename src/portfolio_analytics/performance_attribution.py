"""
绩效归因分析模块

提供投资组合绩效归因分析：
1. Brinson模型归因
2. 基于因子的归因
3. 行业/风格归因
4. 时间序列归因分析
5. 绩效评估指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import warnings

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available, some attribution analysis will be limited")

from . import Portfolio, AssetData, PerformanceAttribution


class AttributionMethod(Enum):
    """归因方法"""
    BRINSON = "brinson"
    FACTOR_BASED = "factor_based"
    SECTOR_BASED = "sector_based"
    STYLE_BASED = "style_based"


class PerformanceMetric(Enum):
    """绩效指标"""
    TOTAL_RETURN = "total_return"
    EXCESS_RETURN = "excess_return"
    SHARPE_RATIO = "sharpe_ratio"
    INFORMATION_RATIO = "information_ratio"
    TRACKING_ERROR = "tracking_error"
    ALPHA = "alpha"
    BETA = "beta"


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def calculate_performance_metrics(self, portfolio: Portfolio,
                                    benchmark_returns: Optional[pd.Series] = None) -> Dict[str, float]:
        """计算绩效指标"""
        portfolio_returns = portfolio.get_portfolio_returns()
        
        if len(portfolio_returns) == 0:
            return {}
        
        metrics = {}
        
        # 基本收益指标
        total_return = (1 + portfolio_returns).prod() - 1
        annualized_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        
        metrics['total_return'] = total_return
        metrics['annualized_return'] = annualized_return
        metrics['volatility'] = portfolio_returns.std() * np.sqrt(252)
        
        # 夏普比率
        excess_returns = portfolio_returns - self.risk_free_rate / 252
        metrics['sharpe_ratio'] = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
        
        # 最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        metrics['max_drawdown'] = drawdown.min()
        
        # 胜率
        win_rate = (portfolio_returns > 0).mean()
        metrics['win_rate'] = win_rate
        
        # 与基准比较的指标
        if benchmark_returns is not None:
            aligned_data = pd.DataFrame({
                'portfolio': portfolio_returns,
                'benchmark': benchmark_returns
            }).dropna()
            
            if len(aligned_data) > 0:
                port_returns = aligned_data['portfolio']
                bench_returns = aligned_data['benchmark']
                
                # 超额收益
                active_returns = port_returns - bench_returns
                metrics['active_return'] = active_returns.mean() * 252
                metrics['tracking_error'] = active_returns.std() * np.sqrt(252)
                
                # 信息比率
                if metrics['tracking_error'] > 0:
                    metrics['information_ratio'] = metrics['active_return'] / metrics['tracking_error']
                else:
                    metrics['information_ratio'] = 0
                
                # Alpha和Beta
                if SKLEARN_AVAILABLE and len(aligned_data) > 10:
                    X = bench_returns.values.reshape(-1, 1)
                    y = port_returns.values
                    
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    metrics['beta'] = model.coef_[0]
                    metrics['alpha'] = model.intercept_ * 252  # 年化alpha
                
                # 基准相对收益
                benchmark_total_return = (1 + bench_returns).prod() - 1
                metrics['benchmark_return'] = benchmark_total_return
                metrics['excess_total_return'] = total_return - benchmark_total_return
        
        return metrics
    
    def brinson_attribution(self, portfolio_weights: Dict[str, float],
                          benchmark_weights: Dict[str, float],
                          portfolio_returns: Dict[str, float],
                          benchmark_returns: Dict[str, float],
                          sectors: Dict[str, str] = None) -> PerformanceAttribution:
        """Brinson归因分析"""
        
        # 确保所有资产都在字典中
        all_assets = set(portfolio_weights.keys()) | set(benchmark_weights.keys())
        
        # 填充缺失的权重和收益率
        port_weights = {asset: portfolio_weights.get(asset, 0.0) for asset in all_assets}
        bench_weights = {asset: benchmark_weights.get(asset, 0.0) for asset in all_assets}
        port_returns = {asset: portfolio_returns.get(asset, 0.0) for asset in all_assets}
        bench_returns = {asset: benchmark_returns.get(asset, 0.0) for asset in all_assets}
        
        # 计算总收益率
        portfolio_total_return = sum(port_weights[asset] * port_returns[asset] for asset in all_assets)
        benchmark_total_return = sum(bench_weights[asset] * bench_returns[asset] for asset in all_assets)
        active_return = portfolio_total_return - benchmark_total_return
        
        # 资产配置效应
        allocation_effect = sum(
            (port_weights[asset] - bench_weights[asset]) * bench_returns[asset]
            for asset in all_assets
        )
        
        # 证券选择效应
        selection_effect = sum(
            bench_weights[asset] * (port_returns[asset] - bench_returns[asset])
            for asset in all_assets
        )
        
        # 交互效应
        interaction_effect = sum(
            (port_weights[asset] - bench_weights[asset]) * (port_returns[asset] - bench_returns[asset])
            for asset in all_assets
        )
        
        # 行业归因（如果提供了行业信息）
        sector_attribution = {}
        if sectors:
            sector_groups = {}
            for asset in all_assets:
                sector = sectors.get(asset, 'Other')
                if sector not in sector_groups:
                    sector_groups[sector] = []
                sector_groups[sector].append(asset)
            
            for sector, assets in sector_groups.items():
                sector_allocation = sum(
                    (port_weights[asset] - bench_weights[asset]) * bench_returns[asset]
                    for asset in assets
                )
                sector_selection = sum(
                    bench_weights[asset] * (port_returns[asset] - bench_returns[asset])
                    for asset in assets
                )
                sector_interaction = sum(
                    (port_weights[asset] - bench_weights[asset]) * (port_returns[asset] - bench_returns[asset])
                    for asset in assets
                )
                
                sector_attribution[sector] = {
                    'allocation': sector_allocation,
                    'selection': sector_selection,
                    'interaction': sector_interaction,
                    'total': sector_allocation + sector_selection + sector_interaction
                }
        
        return PerformanceAttribution(
            total_return=portfolio_total_return,
            benchmark_return=benchmark_total_return,
            active_return=active_return,
            asset_selection=selection_effect,
            allocation_effect=allocation_effect,
            interaction_effect=interaction_effect,
            sector_attribution=sector_attribution
        )
    
    def factor_attribution(self, portfolio_returns: pd.Series,
                         factor_returns: pd.DataFrame,
                         portfolio_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """基于因子的归因分析"""
        if not SKLEARN_AVAILABLE:
            return {}
        
        # 对齐数据
        aligned_data = pd.concat([portfolio_returns, factor_returns], axis=1).dropna()
        
        if len(aligned_data) < 10:
            return {}
        
        y = aligned_data.iloc[:, 0].values  # 投资组合收益率
        X = aligned_data.iloc[:, 1:].values  # 因子收益率
        factor_names = factor_returns.columns.tolist()
        
        # 多元线性回归
        model = LinearRegression()
        model.fit(X, y)
        
        # 因子暴露度
        factor_exposures = dict(zip(factor_names, model.coef_))
        
        # 因子收益贡献
        factor_contributions = {}
        for i, factor_name in enumerate(factor_names):
            factor_return = factor_returns[factor_name].mean()
            contribution = model.coef_[i] * factor_return
            factor_contributions[factor_name] = contribution
        
        # 特异性收益（Alpha）
        predicted_returns = model.predict(X)
        residuals = y - predicted_returns
        idiosyncratic_return = residuals.mean()
        
        result = {
            'alpha': idiosyncratic_return,
            'r_squared': model.score(X, y),
            'factor_exposures': factor_exposures,
            'factor_contributions': factor_contributions
        }
        
        return result
    
    def rolling_attribution(self, portfolio: Portfolio,
                          benchmark_returns: pd.Series,
                          window: int = 252,
                          attribution_method: AttributionMethod = AttributionMethod.BRINSON) -> pd.DataFrame:
        """滚动归因分析"""
        portfolio_returns = portfolio.get_portfolio_returns()
        
        # 对齐数据
        aligned_data = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < window:
            return pd.DataFrame()
        
        results = []
        
        for i in range(window, len(aligned_data) + 1):
            window_data = aligned_data.iloc[i-window:i]
            end_date = window_data.index[-1]
            
            # 计算窗口期内的归因
            if attribution_method == AttributionMethod.BRINSON:
                # 简化的Brinson归因（需要更多数据）
                port_ret = window_data['portfolio'].mean()
                bench_ret = window_data['benchmark'].mean()
                active_ret = port_ret - bench_ret
                
                result = {
                    'date': end_date,
                    'portfolio_return': port_ret,
                    'benchmark_return': bench_ret,
                    'active_return': active_ret,
                    'tracking_error': (window_data['portfolio'] - window_data['benchmark']).std()
                }
            else:
                # 其他归因方法的简化实现
                result = {
                    'date': end_date,
                    'portfolio_return': window_data['portfolio'].mean(),
                    'benchmark_return': window_data['benchmark'].mean()
                }
            
            results.append(result)
        
        return pd.DataFrame(results).set_index('date')
    
    def style_attribution(self, portfolio: Portfolio,
                         style_factors: pd.DataFrame,
                         benchmark_style_exposures: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """风格归因分析"""
        portfolio_returns = portfolio.get_portfolio_returns()
        
        if not SKLEARN_AVAILABLE or len(style_factors) == 0:
            return {}
        
        # 对齐数据
        aligned_data = pd.concat([portfolio_returns, style_factors], axis=1).dropna()
        
        if len(aligned_data) < 10:
            return {}
        
        y = aligned_data.iloc[:, 0].values  # 投资组合收益率
        X = aligned_data.iloc[:, 1:].values  # 风格因子
        factor_names = style_factors.columns.tolist()
        
        # 线性回归获取风格暴露
        model = LinearRegression()
        model.fit(X, y)
        
        portfolio_exposures = dict(zip(factor_names, model.coef_))
        
        # 如果有基准风格暴露，计算相对暴露
        if benchmark_style_exposures:
            relative_exposures = {}
            for factor in factor_names:
                portfolio_exp = portfolio_exposures.get(factor, 0)
                benchmark_exp = benchmark_style_exposures.get(factor, 0)
                relative_exposures[factor] = portfolio_exp - benchmark_exp
        else:
            relative_exposures = portfolio_exposures
        
        # 计算风格因子对收益的贡献
        style_contributions = {}
        for i, factor_name in enumerate(factor_names):
            factor_return = style_factors[factor_name].mean()
            contribution = model.coef_[i] * factor_return
            style_contributions[factor_name] = contribution
        
        return {
            'portfolio_exposures': portfolio_exposures,
            'relative_exposures': relative_exposures,
            'style_contributions': style_contributions,
            'style_alpha': model.intercept_,
            'r_squared': model.score(X, y)
        }
    
    def sector_attribution(self, portfolio: Portfolio,
                         sector_returns: pd.DataFrame,
                         benchmark_sector_weights: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """行业归因分析"""
        
        # 计算投资组合的行业权重
        portfolio_sector_weights = {}
        for symbol, weight in portfolio.weights.items():
            if symbol in portfolio.assets:
                sector = portfolio.assets[symbol].sector
                if sector:
                    portfolio_sector_weights[sector] = portfolio_sector_weights.get(sector, 0) + weight
        
        # 归因计算
        sector_attribution = {}
        
        for sector in set(portfolio_sector_weights.keys()) | set(benchmark_sector_weights.keys()):
            port_weight = portfolio_sector_weights.get(sector, 0)
            bench_weight = benchmark_sector_weights.get(sector, 0)
            
            if sector in sector_returns.columns:
                sector_return = sector_returns[sector].mean()
                
                # 配置效应
                allocation_effect = (port_weight - bench_weight) * sector_return
                
                # 如果有行业内证券选择数据，可以计算选择效应
                # 这里简化处理
                selection_effect = 0.0
                
                sector_attribution[sector] = {
                    'portfolio_weight': port_weight,
                    'benchmark_weight': bench_weight,
                    'allocation_effect': allocation_effect,
                    'selection_effect': selection_effect,
                    'total_effect': allocation_effect + selection_effect
                }
        
        return sector_attribution
    
    def calculate_tracking_error_decomposition(self, portfolio: Portfolio,
                                             benchmark_returns: pd.Series) -> Dict[str, float]:
        """跟踪误差分解"""
        portfolio_returns = portfolio.get_portfolio_returns()
        
        # 对齐数据
        aligned_data = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) == 0:
            return {}
        
        active_returns = aligned_data['portfolio'] - aligned_data['benchmark']
        tracking_error = active_returns.std() * np.sqrt(252)
        
        # 跟踪误差的时间序列分解
        rolling_te = active_returns.rolling(window=60).std() * np.sqrt(252)
        
        return {
            'total_tracking_error': tracking_error,
            'average_rolling_te': rolling_te.mean(),
            'te_volatility': rolling_te.std(),
            'max_te': rolling_te.max(),
            'min_te': rolling_te.min()
        }


class PerformanceBenchmark:
    """绩效基准"""
    
    def __init__(self):
        pass
    
    def create_custom_benchmark(self, assets: Dict[str, AssetData],
                              weights: Dict[str, float]) -> pd.Series:
        """创建自定义基准"""
        returns_data = {}
        for symbol, weight in weights.items():
            if symbol in assets and weight > 0:
                returns_data[symbol] = assets[symbol].returns
        
        if not returns_data:
            return pd.Series()
        
        returns_df = pd.DataFrame(returns_data).dropna()
        weights_series = pd.Series(weights)
        
        # 计算加权收益率
        benchmark_returns = (returns_df * weights_series).sum(axis=1)
        
        return benchmark_returns
    
    def calculate_benchmark_statistics(self, benchmark_returns: pd.Series) -> Dict[str, float]:
        """计算基准统计数据"""
        if len(benchmark_returns) == 0:
            return {}
        
        return {
            'total_return': (1 + benchmark_returns).prod() - 1,
            'annualized_return': benchmark_returns.mean() * 252,
            'volatility': benchmark_returns.std() * np.sqrt(252),
            'sharpe_ratio': benchmark_returns.mean() / benchmark_returns.std() * np.sqrt(252) if benchmark_returns.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(benchmark_returns),
            'skewness': benchmark_returns.skew(),
            'kurtosis': benchmark_returns.kurtosis()
        }
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()


# 导出
__all__ = [
    'AttributionMethod', 'PerformanceMetric', 'PerformanceAnalyzer', 'PerformanceBenchmark'
]