#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习信号预测集成系统
将ML模型集成到实时交易流程中，提供价格预测、信号强度评估和趋势判断
"""

import asyncio
import logging
import time
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from collections import deque
import json
import pickle
import os

# 机器学习库
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("⚠️ Scikit-learn不可用，ML功能将受限")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================= 数据模型 =================================

@dataclass
class MLPrediction:
    """ML预测结果"""
    timestamp: float
    symbol: str
    current_price: float
    
    # 价格预测
    predicted_price_1m: float    # 1分钟后价格预测
    predicted_price_5m: float    # 5分钟后价格预测
    predicted_price_15m: float   # 15分钟后价格预测
    
    # 信号强度
    signal_strength: float       # 信号强度 (0-1)
    signal_direction: str        # 信号方向 ('BUY', 'SELL', 'HOLD')
    confidence: float           # 预测置信度 (0-1)
    
    # 趋势分析
    trend_short: str            # 短期趋势 ('UP', 'DOWN', 'SIDEWAYS')
    trend_medium: str           # 中期趋势
    trend_strength: float       # 趋势强度 (0-1)
    
    # 风险评估
    volatility_prediction: float # 预测波动率
    risk_score: float           # 风险评分 (0-1)
    
    # 模型信息
    model_accuracy: float       # 模型准确率
    prediction_latency_ms: float # 预测延迟

@dataclass
class FeatureSet:
    """特征集合"""
    timestamp: float
    symbol: str
    
    # 价格特征
    price: float
    price_change_1m: float
    price_change_5m: float
    price_change_15m: float
    
    # 技术指标特征
    rsi: float
    macd: float
    macd_signal: float
    bb_upper: float
    bb_lower: float
    bb_position: float
    
    # 成交量特征
    volume: float
    volume_sma: float
    volume_ratio: float
    
    # 市场特征
    market_volatility: float
    market_trend: float

# ================================= ML模型管理器 =================================

class MLModelManager:
    """机器学习模型管理器"""
    
    def __init__(self, model_dir: str = "models"):
        """初始化模型管理器"""
        self.model_dir = model_dir
        self.models: Dict[str, Dict] = {}  # 模型缓存
        self.scalers: Dict[str, StandardScaler] = {}  # 特征缩放器
        self.feature_columns = []
        
        # 确保模型目录存在
        os.makedirs(model_dir, exist_ok=True)
        
        # 模型性能指标
        self.model_metrics: Dict[str, Dict] = {}
        
        if ML_AVAILABLE:
            self._initialize_models()
        else:
            logger.warning("⚠️ ML库不可用，使用简化预测模型")
        
        logger.info("✅ ML模型管理器初始化完成")
    
    def _initialize_models(self):
        """初始化ML模型"""
        # 价格预测模型
        self.models['price_1m'] = {
            'model': RandomForestRegressor(n_estimators=100, random_state=42),
            'trained': False,
            'last_train_time': 0.0
        }
        
        self.models['price_5m'] = {
            'model': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'trained': False,
            'last_train_time': 0.0
        }
        
        self.models['price_15m'] = {
            'model': RandomForestRegressor(n_estimators=150, random_state=42),
            'trained': False,
            'last_train_time': 0.0
        }
        
        # 信号强度预测模型
        self.models['signal_strength'] = {
            'model': GradientBoostingRegressor(n_estimators=80, random_state=42),
            'trained': False,
            'last_train_time': 0.0
        }
        
        # 趋势预测模型
        self.models['trend_prediction'] = {
            'model': RandomForestRegressor(n_estimators=120, random_state=42),
            'trained': False,
            'last_train_time': 0.0
        }
        
        # 波动率预测模型
        self.models['volatility'] = {
            'model': LinearRegression(),
            'trained': False,
            'last_train_time': 0.0
        }
        
        # 定义特征列
        self.feature_columns = [
            'price_change_1m', 'price_change_5m', 'price_change_15m',
            'rsi', 'macd', 'macd_signal', 'bb_position',
            'volume_ratio', 'market_volatility', 'market_trend'
        ]
        
        logger.info(f"✅ 初始化 {len(self.models)} 个ML模型")
    
    def extract_features(self, price_history: List[float], 
                        volume_history: List[float], 
                        technical_indicators: Dict) -> Optional[FeatureSet]:
        """从历史数据提取特征"""
        if len(price_history) < 20:  # 需要足够的历史数据
            return None
        
        try:
            current_time = time.time()
            current_price = price_history[-1]
            
            # 价格变化特征
            price_change_1m = (price_history[-1] - price_history[-2]) / price_history[-2] if len(price_history) > 1 else 0.0
            price_change_5m = (price_history[-1] - price_history[-5]) / price_history[-5] if len(price_history) > 5 else 0.0
            price_change_15m = (price_history[-1] - price_history[-15]) / price_history[-15] if len(price_history) > 15 else 0.0
            
            # 技术指标特征
            rsi = technical_indicators.get('rsi', 50.0)
            macd = technical_indicators.get('macd', 0.0)
            macd_signal = technical_indicators.get('macd_signal', 0.0)
            bb_upper = technical_indicators.get('bb_upper', current_price * 1.02)
            bb_lower = technical_indicators.get('bb_lower', current_price * 0.98)
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            
            # 成交量特征
            current_volume = volume_history[-1] if volume_history else 0.0
            volume_sma = np.mean(volume_history[-10:]) if len(volume_history) >= 10 else current_volume
            volume_ratio = current_volume / volume_sma if volume_sma > 0 else 1.0
            
            # 市场特征
            prices = np.array(price_history[-20:])
            returns = np.diff(prices) / prices[:-1]
            market_volatility = np.std(returns) if len(returns) > 0 else 0.01
            market_trend = (prices[-1] - prices[0]) / prices[0] if len(prices) > 1 else 0.0
            
            return FeatureSet(
                timestamp=current_time,
                symbol="",  # 将在调用时设置
                price=current_price,
                price_change_1m=price_change_1m,
                price_change_5m=price_change_5m,
                price_change_15m=price_change_15m,
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                bb_upper=bb_upper,
                bb_lower=bb_lower,
                bb_position=bb_position,
                volume=current_volume,
                volume_sma=volume_sma,
                volume_ratio=volume_ratio,
                market_volatility=market_volatility,
                market_trend=market_trend
            )
            
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return None
    
    def train_models(self, training_data: List[FeatureSet], 
                    target_data: Dict[str, List[float]]) -> Dict[str, float]:
        """训练ML模型"""
        if not ML_AVAILABLE or not training_data:
            return {}
        
        try:
            # 准备特征矩阵
            X = []
            for features in training_data:
                feature_vector = [
                    features.price_change_1m, features.price_change_5m, features.price_change_15m,
                    features.rsi, features.macd, features.macd_signal, features.bb_position,
                    features.volume_ratio, features.market_volatility, features.market_trend
                ]
                X.append(feature_vector)
            
            X = np.array(X)
            
            # 特征缩放
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers['features'] = scaler
            
            training_results = {}
            
            # 训练各个模型
            for model_name, target_values in target_data.items():
                if model_name in self.models and len(target_values) == len(X):
                    try:
                        y = np.array(target_values)
                        model = self.models[model_name]['model']
                        
                        # 训练模型
                        model.fit(X_scaled, y)
                        
                        # 评估性能
                        y_pred = model.predict(X_scaled)
                        mse = mean_squared_error(y, y_pred)
                        mae = mean_absolute_error(y, y_pred)
                        
                        # 更新模型状态
                        self.models[model_name]['trained'] = True
                        self.models[model_name]['last_train_time'] = time.time()
                        
                        # 保存性能指标
                        self.model_metrics[model_name] = {
                            'mse': mse,
                            'mae': mae,
                            'samples': len(y),
                            'last_updated': time.time()
                        }
                        
                        training_results[model_name] = 1.0 - (mse / np.var(y)) if np.var(y) > 0 else 0.0
                        
                        logger.info(f"✅ 模型 {model_name} 训练完成，R² = {training_results[model_name]:.3f}")
                        
                    except Exception as e:
                        logger.error(f"模型 {model_name} 训练失败: {e}")
            
            logger.info(f"✅ 完成 {len(training_results)} 个模型训练")
            return training_results
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            return {}
    
    def predict(self, features: FeatureSet) -> Optional[MLPrediction]:
        """使用ML模型进行预测"""
        if not ML_AVAILABLE:
            return self._simple_prediction(features)
        
        start_time = time.perf_counter()
        
        try:
            # 准备特征向量
            feature_vector = np.array([[
                features.price_change_1m, features.price_change_5m, features.price_change_15m,
                features.rsi, features.macd, features.macd_signal, features.bb_position,
                features.volume_ratio, features.market_volatility, features.market_trend
            ]])
            
            # 特征缩放
            if 'features' in self.scalers:
                feature_vector = self.scalers['features'].transform(feature_vector)
            
            predictions = {}
            
            # 价格预测
            for time_horizon in ['1m', '5m', '15m']:
                model_name = f'price_{time_horizon}'
                if model_name in self.models and self.models[model_name]['trained']:
                    try:
                        pred = self.models[model_name]['model'].predict(feature_vector)[0]
                        predictions[f'predicted_price_{time_horizon}'] = max(0.1, pred)  # 确保价格为正
                    except:
                        predictions[f'predicted_price_{time_horizon}'] = features.price
            
            # 信号强度预测
            if 'signal_strength' in self.models and self.models['signal_strength']['trained']:
                try:
                    signal_strength = self.models['signal_strength']['model'].predict(feature_vector)[0]
                    predictions['signal_strength'] = np.clip(signal_strength, 0.0, 1.0)
                except:
                    predictions['signal_strength'] = 0.5
            else:
                predictions['signal_strength'] = self._calculate_signal_strength(features)
            
            # 趋势预测
            if 'trend_prediction' in self.models and self.models['trend_prediction']['trained']:
                try:
                    trend_score = self.models['trend_prediction']['model'].predict(feature_vector)[0]
                    predictions['trend_strength'] = np.clip(abs(trend_score), 0.0, 1.0)
                    predictions['trend_short'] = 'UP' if trend_score > 0.1 else 'DOWN' if trend_score < -0.1 else 'SIDEWAYS'
                except:
                    predictions['trend_strength'] = 0.5
                    predictions['trend_short'] = 'SIDEWAYS'
            else:
                trend_info = self._calculate_trend(features)
                predictions.update(trend_info)
            
            # 波动率预测
            if 'volatility' in self.models and self.models['volatility']['trained']:
                try:
                    volatility = self.models['volatility']['model'].predict(feature_vector)[0]
                    predictions['volatility_prediction'] = max(0.001, volatility)
                except:
                    predictions['volatility_prediction'] = features.market_volatility
            else:
                predictions['volatility_prediction'] = features.market_volatility
            
            # 计算信号方向
            price_change_pred = predictions.get('predicted_price_1m', features.price) - features.price
            if price_change_pred > features.price * 0.001:  # 0.1%阈值
                signal_direction = 'BUY'
            elif price_change_pred < -features.price * 0.001:
                signal_direction = 'SELL'
            else:
                signal_direction = 'HOLD'
            
            # 计算置信度和风险评分
            confidence = min(0.95, predictions.get('signal_strength', 0.5) * 0.8 + 0.2)
            risk_score = min(1.0, predictions.get('volatility_prediction', 0.01) * 10 + 
                           (1.0 - predictions.get('signal_strength', 0.5)) * 0.5)
            
            # 计算预测延迟
            prediction_latency = (time.perf_counter() - start_time) * 1000
            
            # 计算模型准确率（简化版本）
            model_accuracy = np.mean([self.model_metrics.get(name, {}).get('mae', 0.1) 
                                    for name in self.models.keys() if self.models[name]['trained']])
            model_accuracy = max(0.1, 1.0 - model_accuracy) if model_accuracy > 0 else 0.7
            
            return MLPrediction(
                timestamp=features.timestamp,
                symbol=features.symbol,
                current_price=features.price,
                predicted_price_1m=predictions.get('predicted_price_1m', features.price),
                predicted_price_5m=predictions.get('predicted_price_5m', features.price),
                predicted_price_15m=predictions.get('predicted_price_15m', features.price),
                signal_strength=predictions.get('signal_strength', 0.5),
                signal_direction=signal_direction,
                confidence=confidence,
                trend_short=predictions.get('trend_short', 'SIDEWAYS'),
                trend_medium='SIDEWAYS',  # 简化版本
                trend_strength=predictions.get('trend_strength', 0.5),
                volatility_prediction=predictions.get('volatility_prediction', 0.01),
                risk_score=risk_score,
                model_accuracy=model_accuracy,
                prediction_latency_ms=prediction_latency
            )
            
        except Exception as e:
            logger.error(f"ML预测失败: {e}")
            return self._simple_prediction(features)
    
    def _simple_prediction(self, features: FeatureSet) -> MLPrediction:
        """简化预测模型（无ML库时使用）"""
        try:
            # 基于技术指标的简单预测
            signal_strength = self._calculate_signal_strength(features)
            trend_info = self._calculate_trend(features)
            
            # 简单价格预测（基于趋势）
            trend_factor = 0.001 if trend_info['trend_short'] == 'UP' else -0.001 if trend_info['trend_short'] == 'DOWN' else 0.0
            
            predicted_price_1m = features.price * (1 + trend_factor)
            predicted_price_5m = features.price * (1 + trend_factor * 2)
            predicted_price_15m = features.price * (1 + trend_factor * 3)
            
            signal_direction = 'BUY' if signal_strength > 0.6 else 'SELL' if signal_strength < 0.4 else 'HOLD'
            
            return MLPrediction(
                timestamp=features.timestamp,
                symbol=features.symbol,
                current_price=features.price,
                predicted_price_1m=predicted_price_1m,
                predicted_price_5m=predicted_price_5m,
                predicted_price_15m=predicted_price_15m,
                signal_strength=signal_strength,
                signal_direction=signal_direction,
                confidence=0.6,  # 简化模型置信度较低
                trend_short=trend_info['trend_short'],
                trend_medium='SIDEWAYS',
                trend_strength=trend_info['trend_strength'],
                volatility_prediction=features.market_volatility,
                risk_score=min(1.0, features.market_volatility * 5),
                model_accuracy=0.6,  # 简化模型准确率
                prediction_latency_ms=1.0
            )
            
        except Exception as e:
            logger.error(f"简化预测失败: {e}")
            # 返回中性预测
            return MLPrediction(
                timestamp=features.timestamp,
                symbol=features.symbol,
                current_price=features.price,
                predicted_price_1m=features.price,
                predicted_price_5m=features.price,
                predicted_price_15m=features.price,
                signal_strength=0.5,
                signal_direction='HOLD',
                confidence=0.5,
                trend_short='SIDEWAYS',
                trend_medium='SIDEWAYS',
                trend_strength=0.5,
                volatility_prediction=0.01,
                risk_score=0.5,
                model_accuracy=0.5,
                prediction_latency_ms=1.0
            )
    
    def _calculate_signal_strength(self, features: FeatureSet) -> float:
        """计算信号强度"""
        try:
            # RSI因子
            rsi_factor = 0.0
            if features.rsi < 30:
                rsi_factor = 0.3  # 超卖
            elif features.rsi > 70:
                rsi_factor = 0.3  # 超买
            
            # MACD因子
            macd_factor = 0.2 if features.macd > features.macd_signal else -0.2
            
            # 布林带因子
            bb_factor = 0.0
            if features.bb_position < 0.2:
                bb_factor = 0.2  # 接近下轨
            elif features.bb_position > 0.8:
                bb_factor = 0.2  # 接近上轨
            
            # 价格动量因子
            momentum_factor = features.price_change_5m * 2
            
            # 成交量因子
            volume_factor = min(0.2, (features.volume_ratio - 1.0) * 0.1)
            
            signal_strength = 0.5 + rsi_factor + macd_factor + bb_factor + momentum_factor + volume_factor
            return np.clip(signal_strength, 0.0, 1.0)
            
        except:
            return 0.5
    
    def _calculate_trend(self, features: FeatureSet) -> Dict:
        """计算趋势信息"""
        try:
            # 综合趋势评分
            trend_score = 0.0
            
            # 价格趋势
            if features.price_change_15m > 0.01:  # 1%
                trend_score += 0.3
            elif features.price_change_15m < -0.01:
                trend_score -= 0.3
            
            # MACD趋势
            if features.macd > features.macd_signal:
                trend_score += 0.2
            else:
                trend_score -= 0.2
            
            # RSI趋势
            if 40 < features.rsi < 60:  # 中性区域
                trend_score += 0.1
            elif features.rsi > 70 or features.rsi < 30:
                trend_score -= 0.1
            
            # 确定趋势方向
            if trend_score > 0.2:
                trend_short = 'UP'
            elif trend_score < -0.2:
                trend_short = 'DOWN'
            else:
                trend_short = 'SIDEWAYS'
            
            trend_strength = np.clip(abs(trend_score), 0.0, 1.0)
            
            return {
                'trend_short': trend_short,
                'trend_strength': trend_strength
            }
            
        except:
            return {
                'trend_short': 'SIDEWAYS',
                'trend_strength': 0.5
            }

# ================================= ML信号预测集成系统 =================================

class MLSignalPredictionSystem:
    """ML信号预测集成系统"""
    
    def __init__(self, model_dir: str = "models"):
        """初始化ML信号预测系统"""
        self.model_manager = MLModelManager(model_dir)
        self.is_running = False
        
        # 历史数据缓存
        self.price_history: Dict[str, deque] = {}
        self.volume_history: Dict[str, deque] = {}
        self.prediction_history: deque = deque(maxlen=1000)
        
        # 性能统计
        self.total_predictions = 0
        self.total_prediction_time = 0.0
        self.prediction_accuracy = 0.0
        
        logger.info("✅ ML信号预测系统初始化完成")
    
    async def start(self):
        """启动ML信号预测系统"""
        if self.is_running:
            logger.warning("⚠️ ML信号预测系统已在运行")
            return
        
        self.is_running = True
        logger.info("🚀 ML信号预测系统启动成功")
    
    async def stop(self):
        """停止ML信号预测系统"""
        self.is_running = False
        logger.info("🛑 ML信号预测系统已停止")
    
    async def update_market_data(self, symbol: str, price: float, volume: float = 0.0, 
                               technical_indicators: Dict = None):
        """更新市场数据"""
        if not self.is_running:
            return
        
        # 更新历史数据
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=100)
            self.volume_history[symbol] = deque(maxlen=100)
        
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)
    
    async def get_ml_prediction(self, symbol: str, 
                              technical_indicators: Dict = None) -> Optional[MLPrediction]:
        """获取ML预测"""
        if not self.is_running or symbol not in self.price_history:
            return None
        
        try:
            # 提取特征
            features = self.model_manager.extract_features(
                list(self.price_history[symbol]),
                list(self.volume_history[symbol]),
                technical_indicators or {}
            )
            
            if not features:
                return None
            
            features.symbol = symbol
            
            # 进行预测
            prediction = self.model_manager.predict(features)
            
            if prediction:
                # 更新性能统计
                self.total_predictions += 1
                self.total_prediction_time += prediction.prediction_latency_ms
                
                # 保存预测历史
                self.prediction_history.append(prediction)
                
                # 检查预测延迟
                if prediction.prediction_latency_ms > 100:  # 100ms阈值
                    logger.warning(f"⚠️ ML预测延迟过高: {prediction.prediction_latency_ms:.2f}ms")
            
            return prediction
            
        except Exception as e:
            logger.error(f"ML预测失败: {e}")
            return None
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        avg_prediction_time = (self.total_prediction_time / self.total_predictions 
                             if self.total_predictions > 0 else 0.0)
        
        recent_predictions = list(self.prediction_history)[-10:] if self.prediction_history else []
        
        return {
            'is_running': self.is_running,
            'ml_available': ML_AVAILABLE,
            'total_predictions': self.total_predictions,
            'avg_prediction_latency_ms': avg_prediction_time,
            'cached_symbols': len(self.price_history),
            'model_status': {name: info['trained'] for name, info in self.model_manager.models.items()},
            'recent_predictions': [asdict(p) for p in recent_predictions]
        }

# ================================= 测试代码 =================================

async def test_ml_system():
    """测试ML信号预测系统"""
    print("🧪 开始测试ML信号预测系统...")
    
    # 创建系统
    ml_system = MLSignalPredictionSystem()
    await ml_system.start()
    
    # 模拟市场数据
    symbol = "AAPL"
    base_price = 150.0
    
    print("\n1. 更新市场数据...")
    for i in range(50):
        price = base_price + np.random.normal(0, 2)  # 随机价格波动
        volume = 1000000 + np.random.randint(-100000, 100000)
        
        await ml_system.update_market_data(symbol, price, volume)
        
        if i % 10 == 0:
            print(f"   数据点 {i+1}: ${price:.2f}")
    
    print("\n2. 进行ML预测...")
    
    # 模拟技术指标
    technical_indicators = {
        'rsi': 45.0,
        'macd': 0.5,
        'macd_signal': 0.3,
        'bb_upper': 155.0,
        'bb_lower': 145.0
    }
    
    prediction = await ml_system.get_ml_prediction(symbol, technical_indicators)
    
    if prediction:
        print(f"✅ 预测成功:")
        print(f"   当前价格: ${prediction.current_price:.2f}")
        print(f"   1分钟预测: ${prediction.predicted_price_1m:.2f}")
        print(f"   5分钟预测: ${prediction.predicted_price_5m:.2f}")
        print(f"   15分钟预测: ${prediction.predicted_price_15m:.2f}")
        print(f"   信号强度: {prediction.signal_strength:.2f}")
        print(f"   信号方向: {prediction.signal_direction}")
        print(f"   置信度: {prediction.confidence:.2f}")
        print(f"   趋势: {prediction.trend_short} (强度: {prediction.trend_strength:.2f})")
        print(f"   预测延迟: {prediction.prediction_latency_ms:.2f}ms")
        print(f"   模型准确率: {prediction.model_accuracy:.2f}")
    else:
        print("❌ 预测失败")
    
    print("\n3. 系统状态:")
    status = ml_system.get_system_status()
    print(f"   ML可用: {status['ml_available']}")
    print(f"   预测总数: {status['total_predictions']}")
    print(f"   平均延迟: {status['avg_prediction_latency_ms']:.2f}ms")
    print(f"   缓存股票数: {status['cached_symbols']}")
    
    await ml_system.stop()
    print("\n✅ ML信号预测系统测试完成")

if __name__ == "__main__":
    asyncio.run(test_ml_system())