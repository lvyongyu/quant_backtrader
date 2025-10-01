"""
异常检测系统

提供多种异常检测算法和实时监控能力：
1. 统计异常检测
2. 机器学习异常检测
3. 时间序列异常检测
4. 实时异常监控
5. 异常评分和排序
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import warnings

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.svm import OneClassSVM
    from sklearn.preprocessing import StandardScaler
    from sklearn.covariance import EllipticEnvelope
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available, ML-based anomaly detection will be limited")

from . import AnalysisResult, AnalysisType


class AnomalyType(Enum):
    """异常类型"""
    STATISTICAL = "statistical"        # 统计异常
    PATTERN = "pattern"               # 模式异常
    VOLUME = "volume"                 # 成交量异常
    PRICE = "price"                   # 价格异常
    VOLATILITY = "volatility"         # 波动率异常
    TREND = "trend"                   # 趋势异常


class AnomalySeverity(Enum):
    """异常严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyPoint:
    """异常点数据"""
    timestamp: datetime
    value: float
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float  # 异常分数，越高越异常
    context: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'anomaly_type': self.anomaly_type.value,
            'severity': self.severity.value,
            'score': self.score,
            'context': self.context,
            'description': self.description
        }


@dataclass
class AnomalyReport:
    """异常检测报告"""
    symbol: str
    detection_method: str
    anomalies: List[AnomalyPoint]
    analysis_period: Tuple[datetime, datetime]
    summary_stats: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    
    def get_critical_anomalies(self) -> List[AnomalyPoint]:
        """获取严重异常"""
        return [a for a in self.anomalies if a.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]]
    
    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[AnomalyPoint]:
        """按类型获取异常"""
        return [a for a in self.anomalies if a.anomaly_type == anomaly_type]


class StatisticalAnomalyDetector:
    """统计异常检测器"""
    
    @staticmethod
    def zscore_detection(data: pd.Series, threshold: float = 3.0) -> List[AnomalyPoint]:
        """Z-Score异常检测"""
        mean_val = data.mean()
        std_val = data.std()
        z_scores = np.abs((data - mean_val) / std_val)
        
        anomalies = []
        for idx, (timestamp, value) in enumerate(data.items()):
            z_score = z_scores.iloc[idx]
            if z_score > threshold:
                severity = StatisticalAnomalyDetector._determine_severity(z_score, threshold)
                anomalies.append(AnomalyPoint(
                    timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
                    value=value,
                    anomaly_type=AnomalyType.STATISTICAL,
                    severity=severity,
                    score=z_score,
                    context={'z_score': z_score, 'mean': mean_val, 'std': std_val},
                    description=f"Z-score {z_score:.2f} exceeds threshold {threshold}"
                ))
        
        return anomalies
    
    @staticmethod
    def iqr_detection(data: pd.Series, multiplier: float = 1.5) -> List[AnomalyPoint]:
        """四分位距异常检测"""
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        anomalies = []
        for timestamp, value in data.items():
            if value < lower_bound or value > upper_bound:
                # 计算异常分数
                if value < lower_bound:
                    score = (lower_bound - value) / IQR
                else:
                    score = (value - upper_bound) / IQR
                
                severity = StatisticalAnomalyDetector._determine_severity(score, 1.0)
                anomalies.append(AnomalyPoint(
                    timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
                    value=value,
                    anomaly_type=AnomalyType.STATISTICAL,
                    severity=severity,
                    score=score,
                    context={'Q1': Q1, 'Q3': Q3, 'IQR': IQR, 'bounds': (lower_bound, upper_bound)},
                    description=f"Value {value:.2f} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]"
                ))
        
        return anomalies
    
    @staticmethod
    def modified_zscore_detection(data: pd.Series, threshold: float = 3.5) -> List[AnomalyPoint]:
        """改进的Z-Score异常检测（基于中位数绝对偏差）"""
        median_val = data.median()
        mad = np.median(np.abs(data - median_val))
        
        # 避免除零
        if mad == 0:
            mad = np.median(np.abs(data - data.mean()))
        
        modified_z_scores = 0.6745 * (data - median_val) / mad
        
        anomalies = []
        for idx, (timestamp, value) in enumerate(data.items()):
            mod_z_score = abs(modified_z_scores.iloc[idx])
            if mod_z_score > threshold:
                severity = StatisticalAnomalyDetector._determine_severity(mod_z_score, threshold)
                anomalies.append(AnomalyPoint(
                    timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(),
                    value=value,
                    anomaly_type=AnomalyType.STATISTICAL,
                    severity=severity,
                    score=mod_z_score,
                    context={'modified_z_score': mod_z_score, 'median': median_val, 'mad': mad},
                    description=f"Modified Z-score {mod_z_score:.2f} exceeds threshold {threshold}"
                ))
        
        return anomalies
    
    @staticmethod
    def _determine_severity(score: float, threshold: float) -> AnomalySeverity:
        """确定异常严重程度"""
        ratio = score / threshold
        if ratio >= 3.0:
            return AnomalySeverity.CRITICAL
        elif ratio >= 2.0:
            return AnomalySeverity.HIGH
        elif ratio >= 1.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


class MLAnomalyDetector:
    """机器学习异常检测器"""
    
    def __init__(self):
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.models = {}
    
    def isolation_forest_detection(self, data: Union[pd.Series, pd.DataFrame],
                                 contamination: float = 0.1) -> List[AnomalyPoint]:
        """孤立森林异常检测"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for Isolation Forest")
        
        # 数据预处理
        if isinstance(data, pd.Series):
            X = data.values.reshape(-1, 1)
            timestamps = data.index
        else:
            X = data.values
            timestamps = data.index
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练模型
        model = IsolationForest(contamination=contamination, random_state=42)
        predictions = model.fit_predict(X_scaled)
        scores = model.decision_function(X_scaled)
        
        # 提取异常点
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # 异常点
                timestamp = timestamps[i] if hasattr(timestamps[i], 'to_pydatetime') else datetime.now()
                if hasattr(timestamps[i], 'to_pydatetime'):
                    timestamp = timestamps[i].to_pydatetime()
                elif isinstance(timestamps[i], datetime):
                    timestamp = timestamps[i]
                else:
                    timestamp = datetime.now()
                
                value = data.iloc[i] if isinstance(data, pd.Series) else data.iloc[i, 0]
                severity = self._score_to_severity(-score)  # 负分数表示异常
                
                anomalies.append(AnomalyPoint(
                    timestamp=timestamp,
                    value=value,
                    anomaly_type=AnomalyType.PATTERN,
                    severity=severity,
                    score=-score,
                    context={'isolation_score': score, 'contamination': contamination},
                    description=f"Isolation Forest detected anomaly with score {score:.3f}"
                ))
        
        return anomalies
    
    def one_class_svm_detection(self, data: Union[pd.Series, pd.DataFrame],
                              nu: float = 0.1) -> List[AnomalyPoint]:
        """一类支持向量机异常检测"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for One-Class SVM")
        
        # 数据预处理
        if isinstance(data, pd.Series):
            X = data.values.reshape(-1, 1)
            timestamps = data.index
        else:
            X = data.values
            timestamps = data.index
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练模型
        model = OneClassSVM(nu=nu)
        predictions = model.fit_predict(X_scaled)
        scores = model.decision_function(X_scaled)
        
        # 提取异常点
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, scores)):
            if pred == -1:  # 异常点
                timestamp = timestamps[i] if hasattr(timestamps[i], 'to_pydatetime') else datetime.now()
                if hasattr(timestamps[i], 'to_pydatetime'):
                    timestamp = timestamps[i].to_pydatetime()
                elif isinstance(timestamps[i], datetime):
                    timestamp = timestamps[i]
                else:
                    timestamp = datetime.now()
                
                value = data.iloc[i] if isinstance(data, pd.Series) else data.iloc[i, 0]
                severity = self._score_to_severity(-score)
                
                anomalies.append(AnomalyPoint(
                    timestamp=timestamp,
                    value=value,
                    anomaly_type=AnomalyType.PATTERN,
                    severity=severity,
                    score=-score,
                    context={'svm_score': score, 'nu': nu},
                    description=f"One-Class SVM detected anomaly with score {score:.3f}"
                ))
        
        return anomalies
    
    def _score_to_severity(self, score: float) -> AnomalySeverity:
        """将异常分数转换为严重程度"""
        if score >= 0.5:
            return AnomalySeverity.CRITICAL
        elif score >= 0.3:
            return AnomalySeverity.HIGH
        elif score >= 0.15:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


class TimeSeriesAnomalyDetector:
    """时间序列异常检测器"""
    
    @staticmethod
    def sudden_change_detection(data: pd.Series, threshold: float = 2.0) -> List[AnomalyPoint]:
        """突变检测"""
        # 计算一阶差分
        diff = data.diff().abs()
        mean_diff = diff.mean()
        std_diff = diff.std()
        
        anomalies = []
        for i in range(1, len(data)):
            change = diff.iloc[i]
            if change > mean_diff + threshold * std_diff:
                severity = StatisticalAnomalyDetector._determine_severity(
                    change / (mean_diff + std_diff), threshold
                )
                
                timestamp = data.index[i] if hasattr(data.index[i], 'to_pydatetime') else datetime.now()
                if hasattr(data.index[i], 'to_pydatetime'):
                    timestamp = data.index[i].to_pydatetime()
                elif isinstance(data.index[i], datetime):
                    timestamp = data.index[i]
                else:
                    timestamp = datetime.now()
                
                anomalies.append(AnomalyPoint(
                    timestamp=timestamp,
                    value=data.iloc[i],
                    anomaly_type=AnomalyType.TREND,
                    severity=severity,
                    score=change / (mean_diff + std_diff),
                    context={
                        'change': change,
                        'mean_change': mean_diff,
                        'std_change': std_diff,
                        'previous_value': data.iloc[i-1]
                    },
                    description=f"Sudden change detected: {change:.2f} (threshold: {threshold})"
                ))
        
        return anomalies
    
    @staticmethod
    def volatility_anomaly_detection(data: pd.Series, window: int = 20,
                                   threshold: float = 2.0) -> List[AnomalyPoint]:
        """波动率异常检测"""
        # 计算滚动波动率
        rolling_std = data.rolling(window=window).std()
        mean_vol = rolling_std.mean()
        std_vol = rolling_std.std()
        
        anomalies = []
        for i in range(window, len(data)):
            current_vol = rolling_std.iloc[i]
            if current_vol > mean_vol + threshold * std_vol:
                severity = StatisticalAnomalyDetector._determine_severity(
                    current_vol / (mean_vol + std_vol), threshold
                )
                
                timestamp = data.index[i] if hasattr(data.index[i], 'to_pydatetime') else datetime.now()
                if hasattr(data.index[i], 'to_pydatetime'):
                    timestamp = data.index[i].to_pydatetime()
                elif isinstance(data.index[i], datetime):
                    timestamp = data.index[i]
                else:
                    timestamp = datetime.now()
                
                anomalies.append(AnomalyPoint(
                    timestamp=timestamp,
                    value=data.iloc[i],
                    anomaly_type=AnomalyType.VOLATILITY,
                    severity=severity,
                    score=current_vol / (mean_vol + std_vol),
                    context={
                        'volatility': current_vol,
                        'mean_volatility': mean_vol,
                        'window': window
                    },
                    description=f"High volatility detected: {current_vol:.4f} (threshold: {threshold})"
                ))
        
        return anomalies


class AnomalyDetectionEngine:
    """异常检测引擎"""
    
    def __init__(self):
        self.statistical_detector = StatisticalAnomalyDetector()
        self.ml_detector = MLAnomalyDetector()
        self.ts_detector = TimeSeriesAnomalyDetector()
    
    def comprehensive_anomaly_detection(self, data: pd.Series, symbol: str,
                                      methods: List[str] = None) -> AnomalyReport:
        """综合异常检测
        
        Args:
            data: 时间序列数据
            symbol: 符号标识
            methods: 检测方法列表
        """
        if methods is None:
            methods = ['zscore', 'iqr', 'modified_zscore', 'sudden_change', 'volatility']
        
        all_anomalies = []
        analysis_start = data.index[0] if len(data) > 0 else datetime.now()
        analysis_end = data.index[-1] if len(data) > 0 else datetime.now()
        
        # 统计方法
        if 'zscore' in methods:
            all_anomalies.extend(self.statistical_detector.zscore_detection(data))
        
        if 'iqr' in methods:
            all_anomalies.extend(self.statistical_detector.iqr_detection(data))
        
        if 'modified_zscore' in methods:
            all_anomalies.extend(self.statistical_detector.modified_zscore_detection(data))
        
        # 时间序列方法
        if 'sudden_change' in methods:
            all_anomalies.extend(self.ts_detector.sudden_change_detection(data))
        
        if 'volatility' in methods:
            all_anomalies.extend(self.ts_detector.volatility_anomaly_detection(data))
        
        # 机器学习方法
        if SKLEARN_AVAILABLE:
            if 'isolation_forest' in methods:
                try:
                    all_anomalies.extend(self.ml_detector.isolation_forest_detection(data))
                except Exception as e:
                    pass  # 忽略ML方法的错误
            
            if 'one_class_svm' in methods:
                try:
                    all_anomalies.extend(self.ml_detector.one_class_svm_detection(data))
                except Exception as e:
                    pass  # 忽略ML方法的错误
        
        # 去重和排序
        unique_anomalies = self._deduplicate_anomalies(all_anomalies)
        unique_anomalies.sort(key=lambda x: x.score, reverse=True)
        
        # 生成摘要统计
        summary_stats = {
            'total_anomalies': len(unique_anomalies),
            'critical_count': len([a for a in unique_anomalies if a.severity == AnomalySeverity.CRITICAL]),
            'high_count': len([a for a in unique_anomalies if a.severity == AnomalySeverity.HIGH]),
            'medium_count': len([a for a in unique_anomalies if a.severity == AnomalySeverity.MEDIUM]),
            'low_count': len([a for a in unique_anomalies if a.severity == AnomalySeverity.LOW]),
            'anomaly_rate': len(unique_anomalies) / len(data) * 100 if len(data) > 0 else 0,
            'methods_used': methods
        }
        
        # 生成建议
        recommendations = self._generate_recommendations(unique_anomalies, summary_stats)
        
        return AnomalyReport(
            symbol=symbol,
            detection_method=', '.join(methods),
            anomalies=unique_anomalies,
            analysis_period=(analysis_start, analysis_end),
            summary_stats=summary_stats,
            recommendations=recommendations
        )
    
    def _deduplicate_anomalies(self, anomalies: List[AnomalyPoint],
                             time_tolerance: timedelta = timedelta(minutes=5)) -> List[AnomalyPoint]:
        """去重异常点"""
        if not anomalies:
            return []
        
        # 按时间排序
        sorted_anomalies = sorted(anomalies, key=lambda x: x.timestamp)
        unique_anomalies = [sorted_anomalies[0]]
        
        for anomaly in sorted_anomalies[1:]:
            # 检查是否与已有异常太接近
            is_duplicate = False
            for existing in unique_anomalies:
                if (abs((anomaly.timestamp - existing.timestamp).total_seconds()) <= 
                    time_tolerance.total_seconds()):
                    # 如果时间接近，保留分数更高的
                    if anomaly.score > existing.score:
                        unique_anomalies.remove(existing)
                        unique_anomalies.append(anomaly)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_anomalies.append(anomaly)
        
        return unique_anomalies
    
    def _generate_recommendations(self, anomalies: List[AnomalyPoint],
                                stats: Dict[str, Any]) -> List[str]:
        """生成异常处理建议"""
        recommendations = []
        
        # 基于异常数量的建议
        anomaly_rate = stats['anomaly_rate']
        if anomaly_rate > 10:
            recommendations.append("异常率过高(>10%)，建议检查数据质量和检测参数")
        elif anomaly_rate > 5:
            recommendations.append("异常率较高(>5%)，建议关注市场异常情况")
        
        # 基于严重程度的建议
        if stats['critical_count'] > 0:
            recommendations.append(f"发现{stats['critical_count']}个严重异常，需要立即关注")
        
        if stats['high_count'] > 3:
            recommendations.append(f"发现{stats['high_count']}个高级异常，建议深入分析")
        
        # 基于异常类型的建议
        type_counts = {}
        for anomaly in anomalies:
            type_counts[anomaly.anomaly_type] = type_counts.get(anomaly.anomaly_type, 0) + 1
        
        if AnomalyType.VOLATILITY in type_counts and type_counts[AnomalyType.VOLATILITY] > 2:
            recommendations.append("检测到多个波动率异常，建议调整风险管理策略")
        
        if AnomalyType.TREND in type_counts and type_counts[AnomalyType.TREND] > 2:
            recommendations.append("检测到多个趋势异常，可能存在市场结构性变化")
        
        return recommendations


# 导出
__all__ = [
    'AnomalyType', 'AnomalySeverity', 'AnomalyPoint', 'AnomalyReport',
    'StatisticalAnomalyDetector', 'MLAnomalyDetector', 'TimeSeriesAnomalyDetector',
    'AnomalyDetectionEngine'
]