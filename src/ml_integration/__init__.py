"""
机器学习集成模块

为量化交易系统提供机器学习能力：
1. 价格预测模型
2. 趋势分析
3. 情感分析
4. 策略优化
5. 模型管理
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from enum import Enum
import numpy as np
import pandas as pd


class ModelType(Enum):
    """模型类型"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    TIME_SERIES = "time_series"
    CLUSTERING = "clustering"
    REINFORCEMENT = "reinforcement"


class PredictionType(Enum):
    """预测类型"""
    PRICE = "price"
    DIRECTION = "direction"
    VOLATILITY = "volatility"
    TREND = "trend"
    SENTIMENT = "sentiment"


@dataclass
class ModelMetrics:
    """模型评估指标"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    mse: float = 0.0
    rmse: float = 0.0
    mae: float = 0.0
    r2_score: float = 0.0
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'mse': self.mse,
            'rmse': self.rmse,
            'mae': self.mae,
            'r2_score': self.r2_score,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown
        }


@dataclass
class ModelPrediction:
    """模型预测结果"""
    symbol: str
    prediction_type: PredictionType
    predicted_value: Union[float, int, str]
    confidence: float
    timestamp: datetime
    features_used: List[str]
    model_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'prediction_type': self.prediction_type.value,
            'predicted_value': self.predicted_value,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'features_used': self.features_used,
            'model_name': self.model_name,
            'metadata': self.metadata
        }


@dataclass
class FeatureSet:
    """特征集合"""
    technical_features: pd.DataFrame
    fundamental_features: Optional[pd.DataFrame] = None
    sentiment_features: Optional[pd.DataFrame] = None
    market_features: Optional[pd.DataFrame] = None
    macro_features: Optional[pd.DataFrame] = None
    
    def get_combined_features(self) -> pd.DataFrame:
        """获取合并的特征"""
        features = [self.technical_features]
        
        if self.fundamental_features is not None:
            features.append(self.fundamental_features)
        if self.sentiment_features is not None:
            features.append(self.sentiment_features)
        if self.market_features is not None:
            features.append(self.market_features)
        if self.macro_features is not None:
            features.append(self.macro_features)
        
        return pd.concat(features, axis=1)


@dataclass
class ModelConfig:
    """模型配置"""
    model_type: ModelType
    prediction_type: PredictionType
    parameters: Dict[str, Any]
    feature_columns: List[str]
    target_column: str
    validation_split: float = 0.2
    test_split: float = 0.1
    cross_validation_folds: int = 5
    random_state: int = 42
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'model_type': self.model_type.value,
            'prediction_type': self.prediction_type.value,
            'parameters': self.parameters,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'validation_split': self.validation_split,
            'test_split': self.test_split,
            'cross_validation_folds': self.cross_validation_folds,
            'random_state': self.random_state
        }


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades_count: int
    avg_trade_return: float
    best_trade: float
    worst_trade: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'trades_count': self.trades_count,
            'avg_trade_return': self.avg_trade_return,
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade
        }


class MLModel:
    """基础ML模型类"""
    
    def __init__(self, name: str, config: ModelConfig):
        self.name = name
        self.config = config
        self.model = None
        self.is_trained = False
        self.metrics = ModelMetrics()
        self.feature_importance = None
        self.training_history = []
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """训练模型"""
        raise NotImplementedError("Subclasses must implement train method")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        raise NotImplementedError("Subclasses must implement predict method")
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """预测概率"""
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            raise NotImplementedError("Model does not support probability prediction")
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """评估模型"""
        raise NotImplementedError("Subclasses must implement evaluate method")
    
    def get_feature_importance(self) -> pd.Series:
        """获取特征重要性"""
        if self.feature_importance is not None:
            return self.feature_importance
        else:
            raise ValueError("Feature importance not available")
    
    def save_model(self, filepath: str):
        """保存模型"""
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'config': self.config,
                'metrics': self.metrics,
                'feature_importance': self.feature_importance,
                'is_trained': self.is_trained
            }, f)
    
    def load_model(self, filepath: str):
        """加载模型"""
        import pickle
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.config = data['config']
            self.metrics = data['metrics']
            self.feature_importance = data['feature_importance']
            self.is_trained = data['is_trained']


# 导出
__all__ = [
    'ModelType', 'PredictionType', 'ModelMetrics', 'ModelPrediction',
    'FeatureSet', 'ModelConfig', 'BacktestResult', 'MLModel'
]