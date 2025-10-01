"""
投资组合优化器

实现多种投资组合优化算法：
1. 均值-方差优化
2. 风险平价
3. 最小方差优化
4. 最大夏普比率优化
5. Black-Litterman模型
6. 分层风险平价
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import warnings
from scipy import optimize
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

try:
    from scipy.optimize import minimize
    from scipy.linalg import inv, pinv
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    warnings.warn("scipy not available, some optimization methods will be limited")

try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False
    warnings.warn("CVXPY not available, some optimization methods will be limited")

from . import (
    OptimizationMethod, OptimizationConstraints, OptimizationResult,
    AssetData, Portfolio, RiskMetrics
)


class PortfolioOptimizer:
    """投资组合优化器"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def optimize_portfolio(self, assets: Dict[str, AssetData],
                         method: OptimizationMethod,
                         constraints: OptimizationConstraints = None) -> OptimizationResult:
        """优化投资组合"""
        if constraints is None:
            constraints = OptimizationConstraints()
        
        # 准备数据
        returns_df = self._prepare_returns_data(assets)
        
        if len(returns_df) == 0:
            return self._create_failed_result(method, constraints, "No valid returns data")
        
        # 选择优化方法
        if method == OptimizationMethod.MEAN_VARIANCE:
            return self._mean_variance_optimization(returns_df, constraints)
        elif method == OptimizationMethod.MINIMUM_VARIANCE:
            return self._minimum_variance_optimization(returns_df, constraints)
        elif method == OptimizationMethod.MAXIMUM_SHARPE:
            return self._maximum_sharpe_optimization(returns_df, constraints)
        elif method == OptimizationMethod.RISK_PARITY:
            return self._risk_parity_optimization(returns_df, constraints)
        elif method == OptimizationMethod.BLACK_LITTERMAN:
            return self._black_litterman_optimization(returns_df, assets, constraints)
        elif method == OptimizationMethod.HIERARCHICAL_RISK_PARITY:
            return self._hierarchical_risk_parity_optimization(returns_df, constraints)
        else:
            return self._create_failed_result(method, constraints, f"Unknown method: {method}")
    
    def _prepare_returns_data(self, assets: Dict[str, AssetData]) -> pd.DataFrame:
        """准备收益率数据"""
        returns_data = {}
        
        for symbol, asset in assets.items():
            if len(asset.returns) > 0:
                returns_data[symbol] = asset.returns
        
        if returns_data:
            returns_df = pd.DataFrame(returns_data)
            return returns_df.dropna()
        else:
            return pd.DataFrame()
    
    def _mean_variance_optimization(self, returns_df: pd.DataFrame,
                                  constraints: OptimizationConstraints) -> OptimizationResult:
        """均值-方差优化"""
        if not SCIPY_AVAILABLE:
            return self._create_failed_result(
                OptimizationMethod.MEAN_VARIANCE, 
                constraints, 
                "scipy not available"
            )
        
        n_assets = len(returns_df.columns)
        mean_returns = returns_df.mean().values
        cov_matrix = returns_df.cov().values
        
        # 目标函数：最小化组合方差，同时考虑期望收益
        def objective(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            
            # 如果有收益目标，转换为约束优化
            if constraints.return_target:
                # 最小化方差
                return portfolio_variance
            else:
                # 最大化效用 = 期望收益 - 0.5 * 风险厌恶系数 * 方差
                risk_aversion = 2.0  # 默认风险厌恶系数
                return -(portfolio_return - 0.5 * risk_aversion * portfolio_variance)
        
        # 约束条件
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # 权重和为1
        ]
        
        # 收益目标约束
        if constraints.return_target:
            constraints_list.append({
                'type': 'eq',
                'fun': lambda x: np.dot(x, mean_returns) - constraints.return_target
            })
        
        # 权重边界
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        
        # 初始权重（等权重）
        x0 = np.array([1.0 / n_assets] * n_assets)
        
        # 优化
        try:
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            if result.success:
                optimal_weights = dict(zip(returns_df.columns, result.x))
                
                # 计算组合指标
                portfolio_return = np.dot(result.x, mean_returns)
                portfolio_risk = np.sqrt(np.dot(result.x, np.dot(cov_matrix, result.x)))
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk
                
                return OptimizationResult(
                    optimal_weights=optimal_weights,
                    expected_return=portfolio_return,
                    expected_risk=portfolio_risk,
                    sharpe_ratio=sharpe_ratio,
                    method=OptimizationMethod.MEAN_VARIANCE,
                    constraints=constraints,
                    optimization_status="success"
                )
            else:
                return self._create_failed_result(
                    OptimizationMethod.MEAN_VARIANCE,
                    constraints,
                    f"Optimization failed: {result.message}"
                )
        
        except Exception as e:
            return self._create_failed_result(
                OptimizationMethod.MEAN_VARIANCE,
                constraints,
                f"Optimization error: {str(e)}"
            )
    
    def _minimum_variance_optimization(self, returns_df: pd.DataFrame,
                                     constraints: OptimizationConstraints) -> OptimizationResult:
        """最小方差优化"""
        if not SCIPY_AVAILABLE:
            return self._create_failed_result(
                OptimizationMethod.MINIMUM_VARIANCE,
                constraints,
                "scipy not available"
            )
        
        n_assets = len(returns_df.columns)
        cov_matrix = returns_df.cov().values
        
        # 目标函数：最小化组合方差
        def objective(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))
        
        # 约束条件
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        # 权重边界
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        
        # 初始权重
        x0 = np.array([1.0 / n_assets] * n_assets)
        
        # 优化
        try:
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            if result.success:
                optimal_weights = dict(zip(returns_df.columns, result.x))
                
                # 计算组合指标
                mean_returns = returns_df.mean().values
                portfolio_return = np.dot(result.x, mean_returns)
                portfolio_risk = np.sqrt(objective(result.x))
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk
                
                return OptimizationResult(
                    optimal_weights=optimal_weights,
                    expected_return=portfolio_return,
                    expected_risk=portfolio_risk,
                    sharpe_ratio=sharpe_ratio,
                    method=OptimizationMethod.MINIMUM_VARIANCE,
                    constraints=constraints,
                    optimization_status="success"
                )
            else:
                return self._create_failed_result(
                    OptimizationMethod.MINIMUM_VARIANCE,
                    constraints,
                    f"Optimization failed: {result.message}"
                )
        
        except Exception as e:
            return self._create_failed_result(
                OptimizationMethod.MINIMUM_VARIANCE,
                constraints,
                f"Optimization error: {str(e)}"
            )
    
    def _maximum_sharpe_optimization(self, returns_df: pd.DataFrame,
                                   constraints: OptimizationConstraints) -> OptimizationResult:
        """最大夏普比率优化"""
        if not SCIPY_AVAILABLE:
            return self._create_failed_result(
                OptimizationMethod.MAXIMUM_SHARPE,
                constraints,
                "scipy not available"
            )
        
        n_assets = len(returns_df.columns)
        mean_returns = returns_df.mean().values
        cov_matrix = returns_df.cov().values
        
        # 目标函数：最大化夏普比率（最小化负夏普比率）
        def objective(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance)
            
            if portfolio_std == 0:
                return -np.inf
            
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std
            return -sharpe_ratio  # 最小化负夏普比率
        
        # 约束条件
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        # 权重边界
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        
        # 初始权重
        x0 = np.array([1.0 / n_assets] * n_assets)
        
        # 优化
        try:
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            if result.success:
                optimal_weights = dict(zip(returns_df.columns, result.x))
                
                # 计算组合指标
                portfolio_return = np.dot(result.x, mean_returns)
                portfolio_risk = np.sqrt(np.dot(result.x, np.dot(cov_matrix, result.x)))
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk
                
                return OptimizationResult(
                    optimal_weights=optimal_weights,
                    expected_return=portfolio_return,
                    expected_risk=portfolio_risk,
                    sharpe_ratio=sharpe_ratio,
                    method=OptimizationMethod.MAXIMUM_SHARPE,
                    constraints=constraints,
                    optimization_status="success"
                )
            else:
                return self._create_failed_result(
                    OptimizationMethod.MAXIMUM_SHARPE,
                    constraints,
                    f"Optimization failed: {result.message}"
                )
        
        except Exception as e:
            return self._create_failed_result(
                OptimizationMethod.MAXIMUM_SHARPE,
                constraints,
                f"Optimization error: {str(e)}"
            )
    
    def _risk_parity_optimization(self, returns_df: pd.DataFrame,
                                constraints: OptimizationConstraints) -> OptimizationResult:
        """风险平价优化"""
        if not SCIPY_AVAILABLE:
            return self._create_failed_result(
                OptimizationMethod.RISK_PARITY,
                constraints,
                "scipy not available"
            )
        
        n_assets = len(returns_df.columns)
        cov_matrix = returns_df.cov().values
        
        # 目标函数：最小化风险贡献的平方和差异
        def objective(weights):
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            
            # 计算边际风险贡献
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / portfolio_variance
            
            # 目标风险贡献（等权重）
            target_contrib = 1.0 / n_assets
            
            # 最小化偏差的平方和
            return np.sum((risk_contrib - target_contrib) ** 2)
        
        # 约束条件
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        # 权重边界
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]
        
        # 初始权重
        x0 = np.array([1.0 / n_assets] * n_assets)
        
        # 优化
        try:
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            if result.success:
                optimal_weights = dict(zip(returns_df.columns, result.x))
                
                # 计算组合指标
                mean_returns = returns_df.mean().values
                portfolio_return = np.dot(result.x, mean_returns)
                portfolio_risk = np.sqrt(np.dot(result.x, np.dot(cov_matrix, result.x)))
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk
                
                return OptimizationResult(
                    optimal_weights=optimal_weights,
                    expected_return=portfolio_return,
                    expected_risk=portfolio_risk,
                    sharpe_ratio=sharpe_ratio,
                    method=OptimizationMethod.RISK_PARITY,
                    constraints=constraints,
                    optimization_status="success"
                )
            else:
                return self._create_failed_result(
                    OptimizationMethod.RISK_PARITY,
                    constraints,
                    f"Optimization failed: {result.message}"
                )
        
        except Exception as e:
            return self._create_failed_result(
                OptimizationMethod.RISK_PARITY,
                constraints,
                f"Optimization error: {str(e)}"
            )
    
    def _black_litterman_optimization(self, returns_df: pd.DataFrame,
                                    assets: Dict[str, AssetData],
                                    constraints: OptimizationConstraints) -> OptimizationResult:
        """Black-Litterman优化"""
        if not SCIPY_AVAILABLE:
            return self._create_failed_result(
                OptimizationMethod.BLACK_LITTERMAN,
                constraints,
                "scipy not available"
            )
        
        # 简化的Black-Litterman实现
        # 在实际应用中，需要市场均衡收益、投资者观点等额外信息
        
        cov_matrix = returns_df.cov().values
        mean_returns = returns_df.mean().values
        
        # 使用市值权重作为先验（简化）
        market_caps = []
        for symbol in returns_df.columns:
            if symbol in assets and assets[symbol].market_cap:
                market_caps.append(assets[symbol].market_cap)
            else:
                market_caps.append(1.0)  # 默认权重
        
        market_caps = np.array(market_caps)
        prior_weights = market_caps / np.sum(market_caps)
        
        # 隐含均衡收益
        risk_aversion = 2.0
        implied_returns = risk_aversion * np.dot(cov_matrix, prior_weights)
        
        # 在没有投资者观点的情况下，使用隐含收益进行优化
        # 这里简化为均值-方差优化
        def objective(weights):
            portfolio_return = np.dot(weights, implied_returns)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            return -(portfolio_return - 0.5 * risk_aversion * portfolio_variance)
        
        # 约束条件
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        ]
        
        # 权重边界
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(len(returns_df.columns))]
        
        # 优化
        try:
            result = minimize(objective, prior_weights, method='SLSQP', bounds=bounds, constraints=constraints_list)
            
            if result.success:
                optimal_weights = dict(zip(returns_df.columns, result.x))
                
                # 计算组合指标
                portfolio_return = np.dot(result.x, mean_returns)
                portfolio_risk = np.sqrt(np.dot(result.x, np.dot(cov_matrix, result.x)))
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk
                
                return OptimizationResult(
                    optimal_weights=optimal_weights,
                    expected_return=portfolio_return,
                    expected_risk=portfolio_risk,
                    sharpe_ratio=sharpe_ratio,
                    method=OptimizationMethod.BLACK_LITTERMAN,
                    constraints=constraints,
                    optimization_status="success"
                )
            else:
                return self._create_failed_result(
                    OptimizationMethod.BLACK_LITTERMAN,
                    constraints,
                    f"Optimization failed: {result.message}"
                )
        
        except Exception as e:
            return self._create_failed_result(
                OptimizationMethod.BLACK_LITTERMAN,
                constraints,
                f"Optimization error: {str(e)}"
            )
    
    def _hierarchical_risk_parity_optimization(self, returns_df: pd.DataFrame,
                                             constraints: OptimizationConstraints) -> OptimizationResult:
        """分层风险平价优化"""
        try:
            # 计算相关矩阵
            corr_matrix = returns_df.corr().values
            
            # 转换为距离矩阵
            distance_matrix = np.sqrt((1 - corr_matrix) / 2)
            
            # 层次聚类
            condensed_distances = squareform(distance_matrix, checks=False)
            linkage_matrix = linkage(condensed_distances, method='ward')
            
            # 获取聚类结果并计算权重
            weights = self._calculate_hrp_weights(returns_df, linkage_matrix)
            optimal_weights = dict(zip(returns_df.columns, weights))
            
            # 计算组合指标
            mean_returns = returns_df.mean().values
            cov_matrix = returns_df.cov().values
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_risk
            
            return OptimizationResult(
                optimal_weights=optimal_weights,
                expected_return=portfolio_return,
                expected_risk=portfolio_risk,
                sharpe_ratio=sharpe_ratio,
                method=OptimizationMethod.HIERARCHICAL_RISK_PARITY,
                constraints=constraints,
                optimization_status="success"
            )
        
        except Exception as e:
            return self._create_failed_result(
                OptimizationMethod.HIERARCHICAL_RISK_PARITY,
                constraints,
                f"HRP optimization error: {str(e)}"
            )
    
    def _calculate_hrp_weights(self, returns_df: pd.DataFrame, linkage_matrix: np.ndarray) -> np.ndarray:
        """计算HRP权重"""
        n_assets = len(returns_df.columns)
        
        # 递归分配权重
        def _recursive_bisection(items):
            if len(items) == 1:
                return {items[0]: 1.0}
            
            # 找到分割点
            mid = len(items) // 2
            left_items = items[:mid]
            right_items = items[mid:]
            
            # 计算左右两组的协方差
            left_cov = returns_df.iloc[:, left_items].cov().values
            right_cov = returns_df.iloc[:, right_items].cov().values
            
            # 计算逆方差权重
            left_ivp = 1.0 / np.diag(left_cov)
            right_ivp = 1.0 / np.diag(right_cov)
            
            left_weight = np.sum(left_ivp)
            right_weight = np.sum(right_ivp)
            
            # 分配权重
            total_weight = left_weight + right_weight
            left_allocation = left_weight / total_weight
            right_allocation = right_weight / total_weight
            
            # 递归计算子组权重
            left_weights = _recursive_bisection(left_items)
            right_weights = _recursive_bisection(right_items)
            
            # 合并权重
            weights = {}
            for item, weight in left_weights.items():
                weights[item] = weight * left_allocation
            for item, weight in right_weights.items():
                weights[item] = weight * right_allocation
            
            return weights
        
        # 从聚类结果获取排序
        items = list(range(n_assets))
        weights_dict = _recursive_bisection(items)
        
        # 转换为数组
        weights = np.zeros(n_assets)
        for i, weight in weights_dict.items():
            weights[i] = weight
        
        return weights
    
    def _create_failed_result(self, method: OptimizationMethod,
                            constraints: OptimizationConstraints,
                            error_message: str) -> OptimizationResult:
        """创建失败的优化结果"""
        return OptimizationResult(
            optimal_weights={},
            expected_return=0.0,
            expected_risk=0.0,
            sharpe_ratio=0.0,
            method=method,
            constraints=constraints,
            optimization_status=f"failed: {error_message}"
        )


class EfficientFrontier:
    """有效前沿"""
    
    def __init__(self, optimizer: PortfolioOptimizer):
        self.optimizer = optimizer
    
    def calculate_efficient_frontier(self, assets: Dict[str, AssetData],
                                   n_portfolios: int = 100,
                                   constraints: OptimizationConstraints = None) -> List[OptimizationResult]:
        """计算有效前沿"""
        if constraints is None:
            constraints = OptimizationConstraints()
        
        results = []
        
        # 获取收益率范围
        returns_df = self.optimizer._prepare_returns_data(assets)
        if len(returns_df) == 0:
            return results
        
        mean_returns = returns_df.mean()
        min_return = mean_returns.min()
        max_return = mean_returns.max()
        
        # 在收益率范围内生成目标收益率
        target_returns = np.linspace(min_return, max_return, n_portfolios)
        
        for target_return in target_returns:
            # 设置收益目标约束
            target_constraints = OptimizationConstraints(
                min_weight=constraints.min_weight,
                max_weight=constraints.max_weight,
                sector_limits=constraints.sector_limits,
                turnover_limit=constraints.turnover_limit,
                max_assets=constraints.max_assets,
                risk_target=constraints.risk_target,
                return_target=target_return
            )
            
            # 优化
            result = self.optimizer.optimize_portfolio(
                assets, 
                OptimizationMethod.MEAN_VARIANCE,
                target_constraints
            )
            
            if result.optimization_status == "success":
                results.append(result)
        
        return results


# 导出
__all__ = [
    'PortfolioOptimizer', 'EfficientFrontier'
]