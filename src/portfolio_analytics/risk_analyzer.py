"""
风险分析模块

提供全面的投资组合风险分析功能：
1. VaR和CVaR计算
2. 风险分解
3. 压力测试
4. 风险预算
5. 相关性分析
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import warnings

try:
    from scipy import stats
    from scipy.linalg import cholesky
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy not available, some risk analysis features will be limited")

from . import Portfolio, AssetData, RiskMetrics


class VaRMethod(Enum):
    """VaR计算方法"""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    CORNISH_FISHER = "cornish_fisher"


class StressTestType(Enum):
    """压力测试类型"""
    HISTORICAL_SCENARIO = "historical_scenario"
    HYPOTHETICAL_SCENARIO = "hypothetical_scenario"
    FACTOR_SHOCK = "factor_shock"
    CORRELATION_BREAKDOWN = "correlation_breakdown"


class RiskAnalyzer:
    """风险分析器"""
    
    def __init__(self):
        pass
    
    def calculate_portfolio_risk_metrics(self, portfolio: Portfolio,
                                       confidence_levels: List[float] = None) -> RiskMetrics:
        """计算投资组合风险指标"""
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]
        
        returns = portfolio.get_portfolio_returns()
        
        if len(returns) == 0:
            return RiskMetrics(
                portfolio_var=0.0,
                portfolio_volatility=0.0,
                var_95=0.0,
                cvar_95=0.0,
                max_drawdown=0.0
            )
        
        # 基本风险指标
        portfolio_volatility = returns.std()
        portfolio_var = returns.var()
        max_drawdown = self._calculate_max_drawdown(returns)
        
        # VaR计算
        var_95 = self.calculate_var(returns, confidence_level=0.95, method=VaRMethod.HISTORICAL)
        var_99 = self.calculate_var(returns, confidence_level=0.99, method=VaRMethod.HISTORICAL)
        
        # CVaR计算
        cvar_95 = self.calculate_cvar(returns, confidence_level=0.95)
        cvar_99 = self.calculate_cvar(returns, confidence_level=0.99)
        
        # 下行风险
        downside_deviation = self._calculate_downside_deviation(returns)
        sortino_ratio = self._calculate_sortino_ratio(returns)
        
        return RiskMetrics(
            portfolio_var=portfolio_var,
            portfolio_volatility=portfolio_volatility,
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            downside_deviation=downside_deviation,
            sortino_ratio=sortino_ratio
        )
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95,
                     method: VaRMethod = VaRMethod.HISTORICAL) -> float:
        """计算在险价值(VaR)"""
        if len(returns) == 0:
            return 0.0
        
        alpha = 1 - confidence_level
        
        if method == VaRMethod.HISTORICAL:
            return self._historical_var(returns, alpha)
        elif method == VaRMethod.PARAMETRIC:
            return self._parametric_var(returns, alpha)
        elif method == VaRMethod.MONTE_CARLO:
            return self._monte_carlo_var(returns, alpha)
        elif method == VaRMethod.CORNISH_FISHER:
            return self._cornish_fisher_var(returns, alpha)
        else:
            return self._historical_var(returns, alpha)
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """计算条件在险价值(CVaR)"""
        if len(returns) == 0:
            return 0.0
        
        var = self.calculate_var(returns, confidence_level, VaRMethod.HISTORICAL)
        
        # CVaR是超过VaR的损失的期望值
        tail_losses = returns[returns <= var]
        
        if len(tail_losses) > 0:
            return tail_losses.mean()
        else:
            return var
    
    def _historical_var(self, returns: pd.Series, alpha: float) -> float:
        """历史VaR"""
        return returns.quantile(alpha)
    
    def _parametric_var(self, returns: pd.Series, alpha: float) -> float:
        """参数VaR（假设正态分布）"""
        if SCIPY_AVAILABLE:
            mean = returns.mean()
            std = returns.std()
            z_score = stats.norm.ppf(alpha)
            return mean + z_score * std
        else:
            # 简化实现
            mean = returns.mean()
            std = returns.std()
            # 使用近似值代替正态分布分位数
            if alpha <= 0.01:
                z_score = -2.58  # 99% 置信水平
            elif alpha <= 0.05:
                z_score = -1.96  # 95% 置信水平
            elif alpha <= 0.10:
                z_score = -1.64  # 90% 置信水平
            else:
                z_score = -1.0
            
            return mean + z_score * std
    
    def _monte_carlo_var(self, returns: pd.Series, alpha: float,
                        n_simulations: int = 10000) -> float:
        """蒙特卡洛VaR"""
        if SCIPY_AVAILABLE:
            # 拟合分布参数
            mean = returns.mean()
            std = returns.std()
            
            # 蒙特卡洛模拟
            simulated_returns = np.random.normal(mean, std, n_simulations)
            return np.percentile(simulated_returns, alpha * 100)
        else:
            # 回退到历史VaR
            return self._historical_var(returns, alpha)
    
    def _cornish_fisher_var(self, returns: pd.Series, alpha: float) -> float:
        """Cornish-Fisher VaR（考虑偏度和峰度）"""
        if SCIPY_AVAILABLE:
            mean = returns.mean()
            std = returns.std()
            skewness = returns.skew()
            kurtosis = returns.kurtosis()
            
            # 正态分布分位数
            z = stats.norm.ppf(alpha)
            
            # Cornish-Fisher调整
            z_cf = (z + 
                   (z**2 - 1) * skewness / 6 +
                   (z**3 - 3*z) * kurtosis / 24 -
                   (2*z**3 - 5*z) * skewness**2 / 36)
            
            return mean + z_cf * std
        else:
            # 回退到参数VaR
            return self._parametric_var(returns, alpha)
    
    def calculate_component_var(self, portfolio: Portfolio,
                              confidence_level: float = 0.95) -> Dict[str, float]:
        """计算成分VaR"""
        if not portfolio.assets or not portfolio.weights:
            return {}
        
        # 获取资产收益率矩阵
        returns_data = {}
        for symbol in portfolio.weights.keys():
            if symbol in portfolio.assets:
                returns_data[symbol] = portfolio.assets[symbol].returns
        
        if not returns_data:
            return {}
        
        returns_df = pd.DataFrame(returns_data).dropna()
        weights = pd.Series(portfolio.weights)
        
        # 计算协方差矩阵
        cov_matrix = returns_df.cov()
        
        # 投资组合方差
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # 边际VaR
        marginal_var = np.dot(cov_matrix, weights) / portfolio_volatility
        
        # 成分VaR
        component_var = weights * marginal_var
        
        # 转换为VaR（假设正态分布）
        alpha = 1 - confidence_level
        if SCIPY_AVAILABLE:
            z_score = stats.norm.ppf(alpha)
        else:
            z_score = -1.96 if alpha == 0.05 else -2.58
        
        portfolio_mean = (returns_df * weights).sum(axis=1).mean()
        var_multiplier = z_score
        
        component_var_dict = {}
        for symbol in component_var.index:
            component_var_dict[symbol] = portfolio_mean + component_var[symbol] * var_multiplier
        
        return component_var_dict
    
    def stress_test(self, portfolio: Portfolio, scenario_type: StressTestType,
                   scenario_params: Dict[str, Any]) -> Dict[str, float]:
        """压力测试"""
        if scenario_type == StressTestType.FACTOR_SHOCK:
            return self._factor_shock_test(portfolio, scenario_params)
        elif scenario_type == StressTestType.HISTORICAL_SCENARIO:
            return self._historical_scenario_test(portfolio, scenario_params)
        elif scenario_type == StressTestType.CORRELATION_BREAKDOWN:
            return self._correlation_breakdown_test(portfolio, scenario_params)
        else:
            return {}
    
    def _factor_shock_test(self, portfolio: Portfolio,
                          params: Dict[str, Any]) -> Dict[str, float]:
        """因子冲击测试"""
        results = {}
        
        # 市场冲击
        market_shock = params.get('market_shock', 0.0)  # 市场整体下跌幅度
        
        total_loss = 0.0
        for symbol, weight in portfolio.weights.items():
            if symbol in portfolio.assets:
                asset = portfolio.assets[symbol]
                
                # 计算资产对市场冲击的敏感性
                beta = asset.beta if asset.beta else 1.0
                asset_shock = market_shock * beta
                
                # 计算损失
                asset_value = weight  # 假设总价值为1
                asset_loss = asset_value * asset_shock
                total_loss += asset_loss
                
                results[f'{symbol}_loss'] = asset_loss
        
        results['total_loss'] = total_loss
        results['portfolio_loss_pct'] = total_loss * 100
        
        return results
    
    def _historical_scenario_test(self, portfolio: Portfolio,
                                params: Dict[str, Any]) -> Dict[str, float]:
        """历史情景测试"""
        scenario_date = params.get('scenario_date')
        
        if not scenario_date:
            return {}
        
        results = {}
        total_loss = 0.0
        
        for symbol, weight in portfolio.weights.items():
            if symbol in portfolio.assets:
                asset = portfolio.assets[symbol]
                returns = asset.returns
                
                # 找到指定日期的收益率
                if scenario_date in returns.index:
                    scenario_return = returns[scenario_date]
                    asset_loss = weight * scenario_return
                    total_loss += asset_loss
                    
                    results[f'{symbol}_return'] = scenario_return
                    results[f'{symbol}_loss'] = asset_loss
        
        results['total_loss'] = total_loss
        results['portfolio_return'] = total_loss
        
        return results
    
    def _correlation_breakdown_test(self, portfolio: Portfolio,
                                  params: Dict[str, Any]) -> Dict[str, float]:
        """相关性崩溃测试"""
        # 假设所有资产相关性变为指定值
        new_correlation = params.get('correlation', 0.9)
        
        # 获取资产收益率
        returns_data = {}
        for symbol in portfolio.weights.keys():
            if symbol in portfolio.assets:
                returns_data[symbol] = portfolio.assets[symbol].returns
        
        if len(returns_data) < 2:
            return {}
        
        returns_df = pd.DataFrame(returns_data).dropna()
        weights = pd.Series(portfolio.weights)
        
        # 原始协方差矩阵
        original_cov = returns_df.cov()
        original_vol = np.sqrt(np.dot(weights, np.dot(original_cov, weights)))
        
        # 构建新的相关矩阵
        std_devs = returns_df.std()
        new_corr_matrix = np.full((len(std_devs), len(std_devs)), new_correlation)
        np.fill_diagonal(new_corr_matrix, 1.0)
        
        # 转换为协方差矩阵
        new_cov = pd.DataFrame(
            new_corr_matrix * np.outer(std_devs, std_devs),
            index=std_devs.index,
            columns=std_devs.index
        )
        
        # 新的投资组合波动率
        new_vol = np.sqrt(np.dot(weights, np.dot(new_cov, weights)))
        
        return {
            'original_volatility': original_vol,
            'new_volatility': new_vol,
            'volatility_change': new_vol - original_vol,
            'volatility_change_pct': (new_vol / original_vol - 1) * 100
        }
    
    def calculate_risk_budget(self, portfolio: Portfolio) -> Dict[str, float]:
        """计算风险预算"""
        if not portfolio.assets or not portfolio.weights:
            return {}
        
        # 获取资产收益率矩阵
        returns_data = {}
        for symbol in portfolio.weights.keys():
            if symbol in portfolio.assets:
                returns_data[symbol] = portfolio.assets[symbol].returns
        
        if not returns_data:
            return {}
        
        returns_df = pd.DataFrame(returns_data).dropna()
        weights = pd.Series(portfolio.weights)
        
        # 计算协方差矩阵
        cov_matrix = returns_df.cov()
        
        # 投资组合方差
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        
        # 边际风险贡献
        marginal_contrib = np.dot(cov_matrix, weights)
        
        # 风险贡献
        risk_contrib = weights * marginal_contrib / portfolio_variance
        
        # 转换为百分比
        risk_budget = (risk_contrib * 100).to_dict()
        
        return risk_budget
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """计算最大回撤"""
        if len(returns) == 0:
            return 0.0
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _calculate_downside_deviation(self, returns: pd.Series,
                                    target_return: float = 0.0) -> float:
        """计算下行偏差"""
        if len(returns) == 0:
            return 0.0
        
        downside_returns = returns[returns < target_return] - target_return
        return np.sqrt(np.mean(downside_returns ** 2)) if len(downside_returns) > 0 else 0.0
    
    def _calculate_sortino_ratio(self, returns: pd.Series,
                               target_return: float = 0.0) -> float:
        """计算Sortino比率"""
        if len(returns) == 0:
            return 0.0
        
        excess_return = returns.mean() - target_return
        downside_deviation = self._calculate_downside_deviation(returns, target_return)
        
        return excess_return / downside_deviation if downside_deviation > 0 else 0.0


class CorrelationAnalyzer:
    """相关性分析器"""
    
    def __init__(self):
        pass
    
    def calculate_correlation_matrix(self, assets: Dict[str, AssetData]) -> pd.DataFrame:
        """计算相关矩阵"""
        returns_data = {}
        for symbol, asset in assets.items():
            if len(asset.returns) > 0:
                returns_data[symbol] = asset.returns
        
        if not returns_data:
            return pd.DataFrame()
        
        returns_df = pd.DataFrame(returns_data).dropna()
        return returns_df.corr()
    
    def calculate_rolling_correlation(self, asset1: AssetData, asset2: AssetData,
                                    window: int = 252) -> pd.Series:
        """计算滚动相关系数"""
        # 对齐数据
        aligned_data = pd.DataFrame({
            'asset1': asset1.returns,
            'asset2': asset2.returns
        }).dropna()
        
        if len(aligned_data) < window:
            return pd.Series()
        
        return aligned_data['asset1'].rolling(window).corr(aligned_data['asset2'])
    
    def detect_correlation_regime_changes(self, correlation_series: pd.Series,
                                        threshold: float = 0.3) -> List[datetime]:
        """检测相关性制度变化"""
        if len(correlation_series) < 2:
            return []
        
        changes = []
        prev_value = correlation_series.iloc[0]
        
        for i in range(1, len(correlation_series)):
            current_value = correlation_series.iloc[i]
            
            if abs(current_value - prev_value) > threshold:
                changes.append(correlation_series.index[i])
            
            prev_value = current_value
        
        return changes
    
    def calculate_diversification_ratio(self, portfolio: Portfolio) -> float:
        """计算分散化比率"""
        if not portfolio.assets or not portfolio.weights:
            return 0.0
        
        # 获取资产收益率和权重
        returns_data = {}
        weights_list = []
        
        for symbol, weight in portfolio.weights.items():
            if symbol in portfolio.assets:
                returns_data[symbol] = portfolio.assets[symbol].returns
                weights_list.append(weight)
        
        if not returns_data:
            return 0.0
        
        returns_df = pd.DataFrame(returns_data).dropna()
        weights = np.array(weights_list)
        
        # 个别资产加权平均波动率
        individual_volatilities = returns_df.std().values
        weighted_avg_volatility = np.dot(weights, individual_volatilities)
        
        # 投资组合波动率
        cov_matrix = returns_df.cov().values
        portfolio_volatility = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        
        # 分散化比率
        if portfolio_volatility > 0:
            return weighted_avg_volatility / portfolio_volatility
        else:
            return 0.0


# 导出
__all__ = [
    'VaRMethod', 'StressTestType', 'RiskAnalyzer', 'CorrelationAnalyzer'
]