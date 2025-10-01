"""
统计分析工具

提供高级统计分析功能，包括：
1. 相关性分析
2. 回归分析  
3. 时间序列分析
4. 分布分析
5. 假设检验
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings

try:
    from scipy import stats
    from scipy.stats import normaltest, jarque_bera, shapiro
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.metrics import r2_score, mean_squared_error
    from sklearn.preprocessing import StandardScaler
    SCIPY_AVAILABLE = True
    SKLEARN_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    SKLEARN_AVAILABLE = False
    warnings.warn("SciPy or scikit-learn not available, some features will be limited")

from . import AnalysisResult, AnalysisType


@dataclass
class CorrelationResult:
    """相关性分析结果"""
    correlation_matrix: pd.DataFrame
    significance_matrix: pd.DataFrame
    strong_correlations: List[Dict[str, Any]]
    analysis_date: datetime = datetime.now()
    
    def get_strongest_pairs(self, threshold: float = 0.7) -> List[Tuple[str, str, float]]:
        """获取最强相关性配对"""
        strong_pairs = []
        
        for i in range(len(self.correlation_matrix)):
            for j in range(i + 1, len(self.correlation_matrix)):
                corr_value = abs(self.correlation_matrix.iloc[i, j])
                if corr_value >= threshold:
                    strong_pairs.append((
                        self.correlation_matrix.index[i],
                        self.correlation_matrix.columns[j],
                        self.correlation_matrix.iloc[i, j]
                    ))
        
        return sorted(strong_pairs, key=lambda x: abs(x[2]), reverse=True)


@dataclass
class RegressionResult:
    """回归分析结果"""
    model_type: str
    coefficients: Dict[str, float]
    r_squared: float
    adjusted_r_squared: float
    p_values: Dict[str, float]
    residuals: pd.Series
    predictions: pd.Series
    confidence_intervals: Dict[str, Tuple[float, float]]
    
    def get_significant_features(self, alpha: float = 0.05) -> List[str]:
        """获取统计显著的特征"""
        return [feature for feature, p_val in self.p_values.items() if p_val < alpha]


class StatisticalAnalyzer:
    """统计分析器"""
    
    def __init__(self):
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
    
    def correlation_analysis(self, data: pd.DataFrame, method: str = 'pearson',
                           significance_level: float = 0.05) -> CorrelationResult:
        """相关性分析
        
        Args:
            data: 数据框
            method: 相关性方法 ('pearson', 'spearman', 'kendall')
            significance_level: 显著性水平
        """
        # 计算相关性矩阵
        if method == 'pearson':
            corr_matrix = data.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = data.corr(method='spearman')
        elif method == 'kendall':
            corr_matrix = data.corr(method='kendall')
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        # 计算显著性
        n = len(data)
        significance_matrix = pd.DataFrame(
            index=corr_matrix.index,
            columns=corr_matrix.columns
        )
        
        if SCIPY_AVAILABLE:
            for i in range(len(corr_matrix)):
                for j in range(len(corr_matrix)):
                    if i != j:
                        r = corr_matrix.iloc[i, j]
                        # 计算t统计量
                        t_stat = r * np.sqrt((n - 2) / (1 - r**2))
                        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
                        significance_matrix.iloc[i, j] = p_value
                    else:
                        significance_matrix.iloc[i, j] = 0.0
        else:
            # 简化的显著性计算
            significance_matrix = significance_matrix.fillna(0.5)
        
        # 找出强相关性
        strong_correlations = []
        for i in range(len(corr_matrix)):
            for j in range(i + 1, len(corr_matrix)):
                corr_val = corr_matrix.iloc[i, j]
                p_val = significance_matrix.iloc[i, j]
                
                if abs(corr_val) > 0.5 and p_val < significance_level:
                    strong_correlations.append({
                        'pair': (corr_matrix.index[i], corr_matrix.columns[j]),
                        'correlation': corr_val,
                        'p_value': p_val,
                        'strength': 'strong' if abs(corr_val) > 0.7 else 'moderate'
                    })
        
        return CorrelationResult(
            correlation_matrix=corr_matrix,
            significance_matrix=significance_matrix,
            strong_correlations=strong_correlations
        )
    
    def regression_analysis(self, X: pd.DataFrame, y: pd.Series,
                          model_type: str = 'linear',
                          alpha: float = 1.0) -> RegressionResult:
        """回归分析
        
        Args:
            X: 特征变量
            y: 目标变量
            model_type: 模型类型 ('linear', 'ridge', 'lasso')
            alpha: 正则化参数
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for regression analysis")
        
        # 数据预处理
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        
        # 选择模型
        if model_type == 'linear':
            model = LinearRegression()
        elif model_type == 'ridge':
            model = Ridge(alpha=alpha)
        elif model_type == 'lasso':
            model = Lasso(alpha=alpha)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # 训练模型
        model.fit(X_scaled, y)
        
        # 预测
        predictions = pd.Series(model.predict(X_scaled), index=y.index)
        residuals = y - predictions
        
        # 计算统计指标
        r_squared = r2_score(y, predictions)
        n, p = X.shape
        adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1)
        
        # 系数
        coefficients = dict(zip(X.columns, model.coef_))
        if hasattr(model, 'intercept_'):
            coefficients['intercept'] = model.intercept_
        
        # 计算p值（简化版本）
        if SCIPY_AVAILABLE:
            mse = mean_squared_error(y, predictions)
            var_residual = mse * (n - p - 1) / n
            
            p_values = {}
            for i, feature in enumerate(X.columns):
                # 简化的t检验
                se = np.sqrt(var_residual / np.var(X_scaled.iloc[:, i]))
                t_stat = model.coef_[i] / se
                p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - p - 1))
                p_values[feature] = p_val
        else:
            p_values = {col: 0.05 for col in X.columns}  # 默认值
        
        # 置信区间（简化版本）
        confidence_intervals = {}
        for feature in X.columns:
            coef = coefficients[feature]
            # 简化的95%置信区间
            margin = 1.96 * abs(coef) * 0.1  # 估计
            confidence_intervals[feature] = (coef - margin, coef + margin)
        
        return RegressionResult(
            model_type=model_type,
            coefficients=coefficients,
            r_squared=r_squared,
            adjusted_r_squared=adjusted_r_squared,
            p_values=p_values,
            residuals=residuals,
            predictions=predictions,
            confidence_intervals=confidence_intervals
        )
    
    def distribution_analysis(self, data: pd.Series) -> Dict[str, Any]:
        """分布分析
        
        Args:
            data: 数据序列
        """
        analysis = {
            'descriptive_stats': {
                'mean': data.mean(),
                'median': data.median(),
                'std': data.std(),
                'var': data.var(),
                'skewness': data.skew(),
                'kurtosis': data.kurtosis(),
                'min': data.min(),
                'max': data.max(),
                'q25': data.quantile(0.25),
                'q75': data.quantile(0.75),
                'iqr': data.quantile(0.75) - data.quantile(0.25)
            },
            'normality_tests': {},
            'outliers': self._detect_outliers(data)
        }
        
        # 正态性检验
        if SCIPY_AVAILABLE:
            try:
                # Shapiro-Wilk test (适用于小样本)
                if len(data) <= 5000:
                    shapiro_stat, shapiro_p = shapiro(data.dropna())
                    analysis['normality_tests']['shapiro'] = {
                        'statistic': shapiro_stat,
                        'p_value': shapiro_p,
                        'is_normal': shapiro_p > 0.05
                    }
                
                # Jarque-Bera test
                jb_stat, jb_p = jarque_bera(data.dropna())
                analysis['normality_tests']['jarque_bera'] = {
                    'statistic': jb_stat,
                    'p_value': jb_p,
                    'is_normal': jb_p > 0.05
                }
                
                # D'Agostino's normality test
                da_stat, da_p = normaltest(data.dropna())
                analysis['normality_tests']['dagostino'] = {
                    'statistic': da_stat,
                    'p_value': da_p,
                    'is_normal': da_p > 0.05
                }
                
            except Exception as e:
                analysis['normality_tests']['error'] = str(e)
        
        return analysis
    
    def _detect_outliers(self, data: pd.Series, method: str = 'iqr') -> Dict[str, Any]:
        """检测异常值
        
        Args:
            data: 数据序列
            method: 检测方法 ('iqr', 'zscore', 'modified_zscore')
        """
        outliers_info = {
            'method': method,
            'outliers': [],
            'outlier_count': 0,
            'outlier_percentage': 0.0
        }
        
        if method == 'iqr':
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(data.dropna())) if SCIPY_AVAILABLE else np.abs((data - data.mean()) / data.std())
            outliers = data[z_scores > 3]
            
        elif method == 'modified_zscore':
            median = data.median()
            mad = np.median(np.abs(data - median))
            modified_z_scores = 0.6745 * (data - median) / mad
            outliers = data[np.abs(modified_z_scores) > 3.5]
            
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
        
        outliers_info['outliers'] = outliers.tolist()
        outliers_info['outlier_count'] = len(outliers)
        outliers_info['outlier_percentage'] = len(outliers) / len(data) * 100
        
        return outliers_info
    
    def time_series_analysis(self, data: pd.Series, frequency: str = 'D') -> Dict[str, Any]:
        """时间序列分析
        
        Args:
            data: 时间序列数据
            frequency: 数据频率
        """
        analysis = {
            'trend_analysis': self._analyze_trend(data),
            'seasonality_analysis': self._analyze_seasonality(data, frequency),
            'stationarity_test': self._test_stationarity(data),
            'autocorrelation': self._calculate_autocorrelation(data)
        }
        
        return analysis
    
    def _analyze_trend(self, data: pd.Series) -> Dict[str, Any]:
        """趋势分析"""
        # 简单线性趋势
        x = np.arange(len(data))
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(x.reshape(-1, 1), data.values)
            trend_slope = model.coef_[0]
            trend_r2 = model.score(x.reshape(-1, 1), data.values)
        else:
            # 简单的趋势估计
            trend_slope = (data.iloc[-1] - data.iloc[0]) / len(data)
            trend_r2 = 0.5  # 估计值
        
        return {
            'slope': trend_slope,
            'r_squared': trend_r2,
            'direction': 'upward' if trend_slope > 0 else 'downward' if trend_slope < 0 else 'flat',
            'strength': 'strong' if abs(trend_r2) > 0.7 else 'moderate' if abs(trend_r2) > 0.3 else 'weak'
        }
    
    def _analyze_seasonality(self, data: pd.Series, frequency: str) -> Dict[str, Any]:
        """季节性分析"""
        # 简化的季节性检测
        if frequency == 'D':
            period = 365  # 年度季节性
        elif frequency == 'W':
            period = 52   # 年度季节性
        elif frequency == 'M':
            period = 12   # 年度季节性
        else:
            period = 30   # 默认周期
        
        if len(data) < period * 2:
            return {'detected': False, 'reason': 'Insufficient data'}
        
        # 简单的周期性检测
        autocorr_seasonal = data.autocorr(lag=period) if hasattr(data, 'autocorr') else 0.0
        
        return {
            'detected': abs(autocorr_seasonal) > 0.3,
            'period': period,
            'strength': abs(autocorr_seasonal),
            'seasonal_autocorr': autocorr_seasonal
        }
    
    def _test_stationarity(self, data: pd.Series) -> Dict[str, Any]:
        """平稳性检验"""
        # 简化的平稳性测试
        # 计算滚动统计
        window = min(30, len(data) // 4)
        rolling_mean = data.rolling(window=window).mean()
        rolling_std = data.rolling(window=window).std()
        
        # 检查统计量的变化
        mean_variation = rolling_mean.std() / data.mean() if data.mean() != 0 else 0
        std_variation = rolling_std.std() / data.std() if data.std() != 0 else 0
        
        is_stationary = mean_variation < 0.1 and std_variation < 0.1
        
        return {
            'is_stationary': is_stationary,
            'mean_variation': mean_variation,
            'std_variation': std_variation,
            'method': 'rolling_statistics'
        }
    
    def _calculate_autocorrelation(self, data: pd.Series, max_lags: int = 20) -> Dict[str, Any]:
        """计算自相关"""
        autocorrelations = {}
        
        for lag in range(1, min(max_lags + 1, len(data) // 4)):
            if hasattr(data, 'autocorr'):
                autocorr = data.autocorr(lag=lag)
            else:
                # 手动计算自相关
                shifted = data.shift(lag)
                autocorr = data.corr(shifted)
            
            autocorrelations[f'lag_{lag}'] = autocorr
        
        # 找出显著的自相关
        significant_lags = {
            lag: corr for lag, corr in autocorrelations.items()
            if abs(corr) > 0.3
        }
        
        return {
            'autocorrelations': autocorrelations,
            'significant_lags': significant_lags,
            'has_autocorrelation': len(significant_lags) > 0
        }


class StatisticalEngine:
    """统计分析引擎"""
    
    def __init__(self):
        self.analyzer = StatisticalAnalyzer()
    
    def comprehensive_analysis(self, data: pd.DataFrame, 
                             target_column: Optional[str] = None) -> Dict[str, AnalysisResult]:
        """综合统计分析
        
        Args:
            data: 数据框
            target_column: 目标列（用于回归分析）
        """
        results = {}
        
        # 相关性分析
        try:
            corr_result = self.analyzer.correlation_analysis(data)
            results['correlation'] = AnalysisResult(
                analysis_type=AnalysisType.CORRELATION,
                symbol='portfolio',
                result_data={
                    'correlation_matrix': corr_result.correlation_matrix.to_dict(),
                    'strong_correlations': corr_result.strong_correlations,
                    'strongest_pairs': corr_result.get_strongest_pairs()
                },
                confidence_score=0.85
            )
        except Exception as e:
            results['correlation'] = AnalysisResult(
                analysis_type=AnalysisType.CORRELATION,
                symbol='portfolio',
                result_data={'error': str(e)},
                confidence_score=0.0
            )
        
        # 分布分析
        for column in data.select_dtypes(include=[np.number]).columns:
            try:
                dist_analysis = self.analyzer.distribution_analysis(data[column])
                results[f'distribution_{column}'] = AnalysisResult(
                    analysis_type=AnalysisType.STATISTICAL,
                    symbol=column,
                    result_data=dist_analysis,
                    confidence_score=0.9
                )
            except Exception as e:
                results[f'distribution_{column}'] = AnalysisResult(
                    analysis_type=AnalysisType.STATISTICAL,
                    symbol=column,
                    result_data={'error': str(e)},
                    confidence_score=0.0
                )
        
        # 回归分析（如果指定了目标列）
        if target_column and target_column in data.columns:
            try:
                feature_columns = [col for col in data.select_dtypes(include=[np.number]).columns 
                                 if col != target_column]
                
                if feature_columns:
                    X = data[feature_columns].dropna()
                    y = data[target_column].dropna()
                    
                    # 确保索引匹配
                    common_index = X.index.intersection(y.index)
                    X = X.loc[common_index]
                    y = y.loc[common_index]
                    
                    if len(X) > 0:
                        reg_result = self.analyzer.regression_analysis(X, y)
                        results['regression'] = AnalysisResult(
                            analysis_type=AnalysisType.REGRESSION,
                            symbol=target_column,
                            result_data={
                                'model_type': reg_result.model_type,
                                'coefficients': reg_result.coefficients,
                                'r_squared': reg_result.r_squared,
                                'significant_features': reg_result.get_significant_features()
                            },
                            confidence_score=reg_result.r_squared
                        )
            except Exception as e:
                results['regression'] = AnalysisResult(
                    analysis_type=AnalysisType.REGRESSION,
                    symbol=target_column,
                    result_data={'error': str(e)},
                    confidence_score=0.0
                )
        
        return results


# 导出
__all__ = [
    'CorrelationResult', 'RegressionResult', 'StatisticalAnalyzer', 'StatisticalEngine'
]