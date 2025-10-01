"""
价格预测模型

提供多种机器学习模型用于股票价格预测：
1. 线性回归模型
2. 随机森林模型
3. LSTM时间序列模型
4. XGBoost模型
5. 支持向量机模型
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import warnings

try:
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.svm import SVR, SVC
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available, ML models will be limited")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    warnings.warn("XGBoost not available, XGBoost models will be disabled")

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    warnings.warn("TensorFlow not available, LSTM models will be disabled")

from . import MLModel, ModelConfig, ModelMetrics, ModelPrediction, PredictionType


class FeatureEngineer:
    """特征工程"""
    
    @staticmethod
    def create_technical_features(df: pd.DataFrame) -> pd.DataFrame:
        """创建技术分析特征"""
        features = df.copy()
        
        # 价格特征
        features['returns'] = features['close'].pct_change()
        features['log_returns'] = np.log(features['close'] / features['close'].shift(1))
        features['price_momentum'] = features['close'] / features['close'].shift(5) - 1
        
        # 移动平均特征
        for window in [5, 10, 20, 50]:
            features[f'ma_{window}'] = features['close'].rolling(window).mean()
            features[f'ma_ratio_{window}'] = features['close'] / features[f'ma_{window}']
        
        # 波动率特征
        for window in [5, 10, 20]:
            features[f'volatility_{window}'] = features['returns'].rolling(window).std()
            features[f'volatility_ratio_{window}'] = (features[f'volatility_{window}'] / 
                                                    features[f'volatility_{window}'].rolling(50).mean())
        
        # 量价特征
        features['volume_ma'] = features['volume'].rolling(20).mean()
        features['volume_ratio'] = features['volume'] / features['volume_ma']
        features['price_volume'] = features['close'] * features['volume']
        
        # RSI
        delta = features['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = features['close'].ewm(span=12).mean()
        exp2 = features['close'].ewm(span=26).mean()
        features['macd'] = exp1 - exp2
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_histogram'] = features['macd'] - features['macd_signal']
        
        # 布林带
        ma20 = features['close'].rolling(20).mean()
        std20 = features['close'].rolling(20).std()
        features['bb_upper'] = ma20 + (std20 * 2)
        features['bb_lower'] = ma20 - (std20 * 2)
        features['bb_position'] = (features['close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
        
        # 时间特征
        features['day_of_week'] = pd.to_datetime(features.index).dayofweek
        features['month'] = pd.to_datetime(features.index).month
        features['quarter'] = pd.to_datetime(features.index).quarter
        
        return features.dropna()
    
    @staticmethod
    def create_lag_features(df: pd.DataFrame, columns: List[str], lags: List[int]) -> pd.DataFrame:
        """创建滞后特征"""
        features = df.copy()
        
        for col in columns:
            for lag in lags:
                features[f'{col}_lag_{lag}'] = features[col].shift(lag)
        
        return features.dropna()
    
    @staticmethod
    def create_target_variables(df: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
        """创建目标变量"""
        targets = pd.DataFrame(index=df.index)
        
        # 价格预测目标
        targets['future_price'] = df['close'].shift(-horizon)
        targets['future_return'] = (df['close'].shift(-horizon) / df['close'] - 1)
        
        # 方向预测目标
        targets['price_direction'] = (targets['future_return'] > 0).astype(int)
        
        # 分类目标（上涨、下跌、持平）
        targets['price_change_category'] = pd.cut(
            targets['future_return'],
            bins=[-np.inf, -0.02, 0.02, np.inf],
            labels=['down', 'flat', 'up']
        )
        
        return targets.dropna()


class LinearRegressionModel(MLModel):
    """线性回归模型"""
    
    def __init__(self, name: str, config: ModelConfig):
        super().__init__(name, config)
        if SKLEARN_AVAILABLE:
            self.model = LinearRegression(**config.parameters)
            self.scaler = StandardScaler()
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """训练模型"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for LinearRegression")
        
        # 数据预处理
        X_scaled = self.scaler.fit_transform(X)
        
        # 训练模型
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # 计算特征重要性（系数）
        self.feature_importance = pd.Series(
            np.abs(self.model.coef_),
            index=X.columns
        ).sort_values(ascending=False)
        
        # 评估模型
        self.metrics = self.evaluate(X, y)
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """评估模型"""
        predictions = self.predict(X)
        
        metrics = ModelMetrics()
        metrics.mse = mean_squared_error(y, predictions)
        metrics.rmse = np.sqrt(metrics.mse)
        metrics.mae = mean_absolute_error(y, predictions)
        metrics.r2_score = r2_score(y, predictions)
        
        return metrics


class RandomForestModel(MLModel):
    """随机森林模型"""
    
    def __init__(self, name: str, config: ModelConfig):
        super().__init__(name, config)
        if SKLEARN_AVAILABLE:
            if config.prediction_type in [PredictionType.PRICE, PredictionType.VOLATILITY]:
                self.model = RandomForestRegressor(**config.parameters)
            else:
                self.model = RandomForestClassifier(**config.parameters)
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """训练模型"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for RandomForest")
        
        # 训练模型
        self.model.fit(X, y)
        self.is_trained = True
        
        # 特征重要性
        self.feature_importance = pd.Series(
            self.model.feature_importances_,
            index=X.columns
        ).sort_values(ascending=False)
        
        # 评估模型
        self.metrics = self.evaluate(X, y)
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        return self.model.predict(X)
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """评估模型"""
        predictions = self.predict(X)
        metrics = ModelMetrics()
        
        if self.config.prediction_type in [PredictionType.PRICE, PredictionType.VOLATILITY]:
            # 回归指标
            metrics.mse = mean_squared_error(y, predictions)
            metrics.rmse = np.sqrt(metrics.mse)
            metrics.mae = mean_absolute_error(y, predictions)
            metrics.r2_score = r2_score(y, predictions)
        else:
            # 分类指标
            metrics.accuracy = accuracy_score(y, predictions)
            metrics.precision = precision_score(y, predictions, average='weighted')
            metrics.recall = recall_score(y, predictions, average='weighted')
            metrics.f1_score = f1_score(y, predictions, average='weighted')
        
        return metrics


class XGBoostModel(MLModel):
    """XGBoost模型"""
    
    def __init__(self, name: str, config: ModelConfig):
        super().__init__(name, config)
        if XGBOOST_AVAILABLE:
            if config.prediction_type in [PredictionType.PRICE, PredictionType.VOLATILITY]:
                self.model = xgb.XGBRegressor(**config.parameters)
            else:
                self.model = xgb.XGBClassifier(**config.parameters)
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """训练模型"""
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is required for XGBoostModel")
        
        # 训练模型
        self.model.fit(X, y)
        self.is_trained = True
        
        # 特征重要性
        self.feature_importance = pd.Series(
            self.model.feature_importances_,
            index=X.columns
        ).sort_values(ascending=False)
        
        # 评估模型
        self.metrics = self.evaluate(X, y)
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        return self.model.predict(X)
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """评估模型"""
        predictions = self.predict(X)
        metrics = ModelMetrics()
        
        if self.config.prediction_type in [PredictionType.PRICE, PredictionType.VOLATILITY]:
            # 回归指标
            metrics.mse = mean_squared_error(y, predictions)
            metrics.rmse = np.sqrt(metrics.mse)
            metrics.mae = mean_absolute_error(y, predictions)
            metrics.r2_score = r2_score(y, predictions)
        else:
            # 分类指标
            metrics.accuracy = accuracy_score(y, predictions)
            metrics.precision = precision_score(y, predictions, average='weighted')
            metrics.recall = recall_score(y, predictions, average='weighted')
            metrics.f1_score = f1_score(y, predictions, average='weighted')
        
        return metrics


class LSTMModel(MLModel):
    """LSTM时间序列模型"""
    
    def __init__(self, name: str, config: ModelConfig):
        super().__init__(name, config)
        self.sequence_length = config.parameters.get('sequence_length', 60)
        self.scaler = MinMaxScaler() if SKLEARN_AVAILABLE else None
        
        if TENSORFLOW_AVAILABLE:
            self._build_model(config.parameters)
    
    def _build_model(self, params: Dict[str, Any]):
        """构建LSTM模型"""
        self.model = Sequential([
            LSTM(params.get('lstm_units', 50), 
                 return_sequences=True, 
                 input_shape=(self.sequence_length, params.get('n_features', 1))),
            Dropout(params.get('dropout', 0.2)),
            LSTM(params.get('lstm_units', 50), return_sequences=False),
            Dropout(params.get('dropout', 0.2)),
            Dense(params.get('dense_units', 25)),
            Dense(1)
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=params.get('learning_rate', 0.001)),
            loss='mean_squared_error'
        )
    
    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """创建时间序列序列"""
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i])
        return np.array(X), np.array(y)
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """训练模型"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM")
        
        # 数据预处理
        if self.scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X.values
        
        # 创建序列
        X_seq, y_seq = self._create_sequences(
            np.column_stack([X_scaled, y.values])
        )
        
        X_train = X_seq[:, :, :-1]  # 排除目标变量
        y_train = X_seq[:, -1, -1]  # 最后一个时间步的目标变量
        
        # 训练模型
        history = self.model.fit(
            X_train, y_train,
            epochs=self.config.parameters.get('epochs', 100),
            batch_size=self.config.parameters.get('batch_size', 32),
            validation_split=0.2,
            verbose=0
        )
        
        self.is_trained = True
        self.training_history = history.history
        
        # 评估模型
        self.metrics = self.evaluate(X, y)
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """预测"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        if self.scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X.values
        
        # 只取最后sequence_length个时间步
        if len(X_scaled) >= self.sequence_length:
            X_seq = X_scaled[-self.sequence_length:].reshape(1, self.sequence_length, -1)
            prediction = self.model.predict(X_seq, verbose=0)
            return prediction.flatten()
        else:
            raise ValueError(f"Need at least {self.sequence_length} time steps for prediction")
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> ModelMetrics:
        """评估模型"""
        # 由于LSTM需要序列数据，这里简化评估
        metrics = ModelMetrics()
        if self.training_history:
            final_loss = self.training_history['loss'][-1]
            metrics.mse = final_loss
            metrics.rmse = np.sqrt(final_loss)
        
        return metrics


class PredictionEngine:
    """预测引擎"""
    
    def __init__(self):
        self.models = {}
        self.feature_engineer = FeatureEngineer()
    
    def add_model(self, model: MLModel):
        """添加模型"""
        self.models[model.name] = model
    
    def train_model(self, model_name: str, data: pd.DataFrame, 
                   target_column: str) -> ModelMetrics:
        """训练指定模型"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        # 特征工程
        features = self.feature_engineer.create_technical_features(data)
        features = features[model.config.feature_columns]
        
        # 创建目标变量
        targets = self.feature_engineer.create_target_variables(data)
        target = targets[target_column]
        
        # 对齐数据
        aligned_data = pd.concat([features, target], axis=1).dropna()
        X = aligned_data[model.config.feature_columns]
        y = aligned_data[target_column]
        
        # 训练模型
        return model.train(X, y)
    
    def predict(self, model_name: str, data: pd.DataFrame) -> ModelPrediction:
        """使用指定模型进行预测"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        if not model.is_trained:
            raise ValueError(f"Model {model_name} must be trained before prediction")
        
        # 特征工程
        features = self.feature_engineer.create_technical_features(data)
        X = features[model.config.feature_columns].tail(1)  # 取最新数据
        
        # 预测
        prediction = model.predict(X)[0]
        
        # 计算置信度（简化版本）
        confidence = 0.5  # 可以基于模型性能或预测不确定性计算
        
        return ModelPrediction(
            symbol=data.get('symbol', 'UNKNOWN'),
            prediction_type=model.config.prediction_type,
            predicted_value=prediction,
            confidence=confidence,
            timestamp=datetime.now(),
            features_used=model.config.feature_columns,
            model_name=model_name
        )
    
    def ensemble_predict(self, model_names: List[str], data: pd.DataFrame,
                        weights: Optional[List[float]] = None) -> ModelPrediction:
        """集成预测"""
        if weights is None:
            weights = [1.0] * len(model_names)
        
        if len(weights) != len(model_names):
            raise ValueError("Weights length must match model names length")
        
        predictions = []
        confidences = []
        
        for model_name in model_names:
            pred = self.predict(model_name, data)
            predictions.append(pred.predicted_value)
            confidences.append(pred.confidence)
        
        # 加权平均
        ensemble_prediction = np.average(predictions, weights=weights)
        ensemble_confidence = np.average(confidences, weights=weights)
        
        return ModelPrediction(
            symbol=data.get('symbol', 'UNKNOWN'),
            prediction_type=self.models[model_names[0]].config.prediction_type,
            predicted_value=ensemble_prediction,
            confidence=ensemble_confidence,
            timestamp=datetime.now(),
            features_used=self.models[model_names[0]].config.feature_columns,
            model_name=f"Ensemble({', '.join(model_names)})"
        )


# 导出
__all__ = [
    'FeatureEngineer', 'LinearRegressionModel', 'RandomForestModel',
    'XGBoostModel', 'LSTMModel', 'PredictionEngine'
]