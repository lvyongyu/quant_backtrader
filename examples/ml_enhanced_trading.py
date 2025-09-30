#!/usr/bin/env python3
"""
机器学习增强交易系统
Machine Learning Enhanced Trading System

集成机器学习模型用于市场预测和策略优化
"""

import backtrader as bt
import numpy as np
import pandas as pd
import random
import datetime
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class FeatureEngineer:
    """特征工程类"""
    
    def __init__(self):
        self.features = []
        self.scaler = StandardScaler()
        
    def create_technical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """创建技术指标特征"""
        
        df = data.copy()
        
        # 基础价格特征
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close']/df['close'].shift(1))
        df['price_change'] = df['close'] - df['open']
        df['price_range'] = df['high'] - df['low']
        
        # 移动平均特征
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
            df[f'sma_slope_{period}'] = df[f'sma_{period}'].diff(5)
        
        # 波动率特征
        for period in [5, 10, 20]:
            df[f'volatility_{period}'] = df['returns'].rolling(period).std()
        
        # 波动率比率（基于20日波动率）
        if 'volatility_20' in df.columns:
            for period in [5, 10]:
                df[f'volatility_ratio_{period}'] = df[f'volatility_{period}'] / df['volatility_20']
        
        # RSI特征
        for period in [14, 21]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD特征
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # 布林带特征
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 成交量特征
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['price_volume'] = df['close'] * df['volume']
        
        # 价格位置特征
        for period in [10, 20, 50]:
            df[f'high_low_ratio_{period}'] = df['high'].rolling(period).max() / df['low'].rolling(period).min()
            df[f'close_position_{period}'] = (df['close'] - df['low'].rolling(period).min()) / (df['high'].rolling(period).max() - df['low'].rolling(period).min())
        
        # 动量特征
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            df[f'momentum_smoothed_{period}'] = df[f'momentum_{period}'].rolling(3).mean()
        
        return df
    
    def create_market_regime_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """创建市场环境特征"""
        
        df = data.copy()
        
        # 趋势强度
        df['trend_strength'] = abs(df['close'].rolling(20).mean().diff(10))
        
        # 市场波动状态
        short_vol = df['returns'].rolling(5).std()
        long_vol = df['returns'].rolling(20).std()
        df['volatility_regime'] = short_vol / long_vol
        
        # 成交量趋势
        df['volume_trend'] = df['volume'].rolling(10).mean() / df['volume'].rolling(30).mean()
        
        # 价格效率（随机游走度量）
        df['price_efficiency'] = abs(df['close'] - df['close'].shift(10)) / df['price_range'].rolling(10).sum()
        
        return df
    
    def prepare_features(self, data: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """准备最终特征矩阵"""
        
        # 创建所有特征
        df = self.create_technical_features(data)
        df = self.create_market_regime_features(df)
        
        # 选择特征列
        feature_columns = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']]
        
        # 移除包含NaN的行
        df_clean = df[feature_columns].dropna()
        
        if len(df_clean) == 0:
            return np.array([]), []
        
        self.feature_names = feature_columns
        
        return df_clean.values, feature_columns

class MarketPredictor:
    """市场预测模型"""
    
    def __init__(self):
        self.direction_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        self.return_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        self.feature_engineer = FeatureEngineer()
        self.is_trained = False
        self.feature_importance = {}
        
    def prepare_training_data(self, data: pd.DataFrame, forecast_period: int = 5) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """准备训练数据"""
        
        # 创建特征
        features, feature_names = self.feature_engineer.prepare_features(data)
        
        if len(features) == 0:
            return np.array([]), np.array([]), np.array([])
        
        # 创建目标变量
        returns = data['close'].pct_change(forecast_period).shift(-forecast_period)
        directions = (returns > 0).astype(int)
        
        # 对齐数据
        min_length = min(len(features), len(returns))
        features = features[:min_length]
        returns = returns.iloc[:min_length].values
        directions = directions.iloc[:min_length].values
        
        # 移除NaN
        valid_idx = ~(np.isnan(returns) | np.isnan(directions))
        features = features[valid_idx]
        returns = returns[valid_idx]
        directions = directions[valid_idx]
        
        return features, returns, directions
    
    def train(self, data: pd.DataFrame, test_size: float = 0.2) -> Dict:
        """训练模型"""
        
        print("🤖 开始训练机器学习模型...")
        
        # 准备数据
        X, y_returns, y_directions = self.prepare_training_data(data)
        
        if len(X) == 0:
            print("❌ 没有足够的训练数据")
            return {}
        
        print(f"📊 训练数据: {len(X)} 样本, {X.shape[1]} 特征")
        
        # 分割数据
        X_train, X_test, y_ret_train, y_ret_test, y_dir_train, y_dir_test = train_test_split(
            X, y_returns, y_directions, test_size=test_size, random_state=42
        )
        
        # 训练方向预测模型
        self.direction_model.fit(X_train, y_dir_train)
        dir_pred = self.direction_model.predict(X_test)
        dir_accuracy = accuracy_score(y_dir_test, dir_pred)
        
        # 训练收益预测模型
        self.return_model.fit(X_train, y_ret_train)
        ret_pred = self.return_model.predict(X_test)
        ret_mse = mean_squared_error(y_ret_test, ret_pred)
        
        # 特征重要性
        self.feature_importance = {
            'direction': dict(zip(self.feature_engineer.feature_names, self.direction_model.feature_importances_)),
            'returns': dict(zip(self.feature_engineer.feature_names, self.return_model.feature_importances_))
        }
        
        self.is_trained = True
        
        results = {
            'direction_accuracy': dir_accuracy,
            'return_mse': ret_mse,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'features_count': X.shape[1]
        }
        
        print(f"✅ 模型训练完成:")
        print(f"   方向预测准确率: {dir_accuracy:.3f}")
        print(f"   收益预测MSE: {ret_mse:.6f}")
        print(f"   训练样本: {len(X_train)}, 测试样本: {len(X_test)}")
        
        return results
    
    def predict(self, data: pd.DataFrame) -> Dict:
        """进行预测"""
        
        if not self.is_trained:
            return {'direction_prob': 0.5, 'expected_return': 0.0, 'confidence': 0.0}
        
        try:
            # 准备特征
            features, _ = self.feature_engineer.prepare_features(data)
            
            if len(features) == 0:
                return {'direction_prob': 0.5, 'expected_return': 0.0, 'confidence': 0.0}
            
            # 使用最新数据进行预测
            latest_features = features[-1:] if len(features) > 0 else features
            
            # 预测方向
            direction_proba = self.direction_model.predict_proba(latest_features)
            direction_prob = direction_proba[0][1] if len(direction_proba[0]) > 1 else 0.5
            
            # 预测收益
            expected_return = self.return_model.predict(latest_features)[0]
            
            # 计算置信度
            confidence = abs(direction_prob - 0.5) * 2
            
            return {
                'direction_prob': float(direction_prob),
                'expected_return': float(expected_return),
                'confidence': float(confidence)
            }
            
        except Exception as e:
            print(f"❌ 预测失败: {e}")
            return {'direction_prob': 0.5, 'expected_return': 0.0, 'confidence': 0.0}
    
    def get_top_features(self, model_type: str = 'direction', top_n: int = 10) -> List[Tuple[str, float]]:
        """获取重要特征"""
        
        if not self.is_trained or model_type not in self.feature_importance:
            return []
        
        importance_dict = self.feature_importance[model_type]
        sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_features[:top_n]

class MLEnhancedStrategy(bt.Strategy):
    """机器学习增强策略"""
    
    params = (
        ('ml_confidence_threshold', 0.6),  # ML预测置信度阈值
        ('ml_direction_threshold', 0.6),   # 方向预测阈值
        ('position_size', 0.8),            # 仓位大小
        ('stop_loss', 0.04),               # 止损
        ('take_profit', 0.08),             # 止盈
        ('retraining_period', 50),         # 重新训练周期
    )
    
    def __init__(self):
        # 技术指标
        self.sma_short = bt.indicators.SMA(period=10)
        self.sma_long = bt.indicators.SMA(period=20)
        self.rsi = bt.indicators.RSI(period=14)
        self.macd = bt.indicators.MACD()
        
        # ML模型
        self.predictor = MarketPredictor()
        
        # 交易状态
        self.order = None
        self.buy_price = None
        self.trade_count = 0
        
        # 数据收集
        self.historical_data = []
        self.last_training = 0
        
        # ML统计
        self.ml_signals = 0
        self.ml_correct_predictions = 0
        self.ml_predictions = []
        
        print(f"🤖 ML增强策略初始化:")
        print(f"   置信度阈值: {self.p.ml_confidence_threshold}")
        print(f"   方向阈值: {self.p.ml_direction_threshold}")
        print(f"   重训练周期: {self.p.retraining_period} 天")
    
    def log(self, txt, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def collect_data(self):
        """收集历史数据"""
        
        current_data = {
            'date': self.datas[0].datetime.date(0),
            'open': self.data.open[0],
            'high': self.data.high[0],
            'low': self.data.low[0],
            'close': self.data.close[0],
            'volume': self.data.volume[0]
        }
        
        self.historical_data.append(current_data)
        
        # 限制历史数据长度
        if len(self.historical_data) > 500:
            self.historical_data = self.historical_data[-400:]
    
    def should_retrain(self):
        """判断是否需要重新训练"""
        return (len(self) - self.last_training) >= self.p.retraining_period
    
    def retrain_model(self):
        """重新训练模型"""
        
        if len(self.historical_data) < 100:
            return False
        
        self.log("🔄 重新训练ML模型...")
        
        # 转换为DataFrame
        df = pd.DataFrame(self.historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 训练模型
        results = self.predictor.train(df)
        
        if results:
            self.last_training = len(self)
            self.log(f"✅ 模型训练完成, 准确率: {results.get('direction_accuracy', 0):.3f}")
            return True
        
        return False
    
    def get_ml_signal(self):
        """获取ML信号"""
        
        if not self.predictor.is_trained or len(self.historical_data) < 50:
            return None
        
        # 转换数据
        df = pd.DataFrame(self.historical_data[-100:])  # 使用最近100个数据点
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 获取预测
        prediction = self.predictor.predict(df)
        
        # 记录预测
        self.ml_predictions.append({
            'date': self.datas[0].datetime.date(0),
            'prediction': prediction,
            'actual_price': self.data.close[0]
        })
        
        return prediction
    
    def evaluate_ml_performance(self):
        """评估ML性能"""
        
        if len(self.ml_predictions) < 10:
            return
        
        # 检查最近的预测准确性
        recent_predictions = self.ml_predictions[-10:]
        correct = 0
        
        for i, pred_data in enumerate(recent_predictions[:-5]):  # 排除最近5个还未确认的
            actual_direction = 1 if recent_predictions[i+5]['actual_price'] > pred_data['actual_price'] else 0
            predicted_direction = 1 if pred_data['prediction']['direction_prob'] > 0.5 else 0
            
            if actual_direction == predicted_direction:
                correct += 1
        
        if len(recent_predictions) > 5:
            recent_accuracy = correct / (len(recent_predictions) - 5)
            if len(self.ml_predictions) % 20 == 0:  # 每20次预测报告一次
                self.log(f"📊 ML最近准确率: {recent_accuracy:.3f}")
    
    def notify_order(self, order):
        """订单状态通知"""
        
        if order.status == order.Completed:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'💰 买入: ${order.executed.price:.2f}')
            else:
                if self.buy_price:
                    pnl = (order.executed.price - self.buy_price) / self.buy_price * 100
                    self.log(f'💰 卖出: ${order.executed.price:.2f}, 收益: {pnl:+.2f}%')
                    self.trade_count += 1
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'❌ 订单失败: {order.getstatusname()}')
        
        self.order = None
    
    def next(self):
        """策略主逻辑"""
        
        # 收集数据
        self.collect_data()
        
        # 等待足够的历史数据
        if len(self) < 50:
            return
        
        if self.order:
            return
        
        # 重新训练模型
        if self.should_retrain():
            self.retrain_model()
        
        current_price = self.data.close[0]
        
        # 持仓管理
        if self.position:
            # 止损止盈
            if current_price <= self.buy_price * (1 - self.p.stop_loss):
                self.log('🛑 触发止损')
                self.order = self.sell()
                return
            elif current_price >= self.buy_price * (1 + self.p.take_profit):
                self.log('🎯 触发止盈')
                self.order = self.sell()
                return
        
        else:
            # 获取技术信号
            tech_signals = [
                self.data.close[0] > self.sma_short[0],   # 价格在短期均线上方
                self.sma_short[0] > self.sma_long[0],     # 短期均线在长期均线上方
                self.rsi[0] > 30 and self.rsi[0] < 70,    # RSI在合理范围
                self.macd.macd[0] > self.macd.signal[0],  # MACD金叉
            ]
            
            tech_score = sum(tech_signals) / len(tech_signals)
            
            # 获取ML信号
            ml_prediction = self.get_ml_signal()
            
            if ml_prediction:
                ml_confidence = ml_prediction['confidence']
                ml_direction_prob = ml_prediction['direction_prob']
                
                # 评估ML性能
                self.evaluate_ml_performance()
                
                # 综合信号决策
                if (ml_confidence >= self.p.ml_confidence_threshold and 
                    ml_direction_prob >= self.p.ml_direction_threshold and 
                    tech_score >= 0.5):  # 至少一半技术指标支持
                    
                    # 根据ML置信度调整仓位
                    confidence_multiplier = min(ml_confidence * 1.5, 1.0)
                    position_size_adj = self.p.position_size * confidence_multiplier
                    
                    cash = self.broker.get_cash()
                    position_value = cash * position_size_adj
                    size = int(position_value / current_price)
                    
                    if size > 0:
                        self.order = self.buy(size=size)
                        self.ml_signals += 1
                        
                        self.log(f'🚀 ML增强开仓:')
                        self.log(f'   ML置信度: {ml_confidence:.3f}')
                        self.log(f'   方向概率: {ml_direction_prob:.3f}')
                        self.log(f'   技术评分: {tech_score:.3f}')
                        self.log(f'   预期收益: {ml_prediction["expected_return"]:+.4f}')
    
    def stop(self):
        """策略结束统计"""
        
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        print('\n' + '='*60)
        print('🤖 ML增强策略结果:')
        print(f'💰 初始资金: $10,000')
        print(f'💰 最终价值: ${final_value:.2f}')
        print(f'📈 总收益率: {total_return:+.2f}%')
        print(f'🔄 完成交易: {self.trade_count} 笔')
        print(f'🤖 ML信号数: {self.ml_signals}')
        
        if self.predictor.is_trained:
            print(f'\n📊 ML模型特征重要性 (TOP 5):')
            top_features = self.predictor.get_top_features('direction', 5)
            for i, (feature, importance) in enumerate(top_features, 1):
                print(f'   {i}. {feature}: {importance:.4f}')
        
        print('='*60)

def generate_sample_data(symbol='ML_TEST', days=200):
    """生成样本数据用于ML训练"""
    
    data = []
    base_price = 100.0
    trend = 0.0
    
    start_date = datetime.datetime(2022, 1, 1)
    
    for i in range(days):
        date = start_date + datetime.timedelta(days=i)
        
        # 跳过周末
        if date.weekday() >= 5:
            continue
        
        # 创建有趋势的价格数据
        trend_change = random.gauss(0, 0.001)
        trend += trend_change
        trend = max(-0.02, min(0.02, trend))  # 限制趋势
        
        daily_return = trend + random.gauss(0, 0.02)
        base_price *= (1 + daily_return)
        base_price = max(50, base_price)
        
        # 生成OHLCV
        open_price = base_price * random.uniform(0.995, 1.005)
        high_price = base_price * random.uniform(1.01, 1.04)
        low_price = base_price * random.uniform(0.96, 0.99)
        close_price = base_price
        volume = random.randint(80000, 300000)
        
        data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    return pd.DataFrame(data)

def run_ml_enhanced_demo():
    """运行ML增强演示"""
    
    print("🤖 机器学习增强交易系统演示")
    print("="*50)
    
    # 1. 生成训练数据并训练模型
    print("📊 准备训练数据...")
    
    training_data = generate_sample_data('TRAIN', 300)
    
    predictor = MarketPredictor()
    training_results = predictor.train(training_data)
    
    if training_results:
        print(f"✅ 预训练完成:")
        print(f"   方向准确率: {training_results['direction_accuracy']:.3f}")
        print(f"   特征数量: {training_results['features_count']}")
        
        # 显示重要特征
        print(f"\n🔍 最重要的特征 (TOP 5):")
        top_features = predictor.get_top_features('direction', 5)
        for i, (feature, importance) in enumerate(top_features, 1):
            print(f"   {i}. {feature}: {importance:.4f}")
    
    # 2. 运行回测
    print(f"\n" + "="*50)
    print("🔄 运行ML增强回测...")
    
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(MLEnhancedStrategy)
    
    # 创建数据源
    test_data = generate_sample_data('TEST', 150)
    
    # 转换为Backtrader数据格式
    import tempfile
    import csv
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    writer = csv.writer(temp_file)
    writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
    
    for _, row in test_data.iterrows():
        writer.writerow([
            row['date'].strftime('%Y-%m-%d'),
            row['open'], row['high'], row['low'], row['close'], row['volume']
        ])
    
    temp_file.close()
    
    # 添加数据
    data = bt.feeds.GenericCSVData(
        dataname=temp_file.name,
        dtformat='%Y-%m-%d',
        datetime=0,
        open=1, high=2, low=3, close=4, volume=5
    )
    cerebro.adddata(data)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    # 设置资金
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)
    
    print(f"💰 初始资金: ${cerebro.broker.getvalue():.2f}")
    
    # 运行
    results = cerebro.run()
    
    # 清理临时文件
    import os
    os.unlink(temp_file.name)
    
    if results:
        strat = results[0]
        
        # 分析结果
        try:
            trade_analysis = strat.analyzers.trades.get_analysis()
            
            total = trade_analysis.get('total', {}).get('total', 0)
            won = trade_analysis.get('won', {}).get('total', 0)
            
            if total > 0:
                print(f"\n📈 交易分析:")
                print(f"   胜率: {won/total*100:.1f}% ({won}/{total})")
                
                avg_win = trade_analysis.get('won', {}).get('pnl', {}).get('average', 0)
                avg_loss = trade_analysis.get('lost', {}).get('pnl', {}).get('average', 0)
                
                if avg_win and avg_loss:
                    print(f"   平均盈利: ${avg_win:.2f}")
                    print(f"   平均亏损: ${avg_loss:.2f}")
                    print(f"   盈亏比: {abs(avg_win/avg_loss):.2f}")
        except Exception as e:
            print(f"❌ 分析失败: {e}")
    
    print(f"\n💰 最终资金: ${cerebro.broker.getvalue():.2f}")
    
    return cerebro

if __name__ == '__main__':
    """运行ML增强演示"""
    
    print("🎯 机器学习增强交易系统")
    print("="*60)
    
    try:
        # 检查依赖
        try:
            from sklearn.ensemble import RandomForestRegressor
            print("✅ scikit-learn 可用")
        except ImportError:
            print("❌ 需要安装 scikit-learn: pip install scikit-learn")
            exit(1)
        
        # 运行演示
        run_ml_enhanced_demo()
        
        print(f"\n" + "="*60)
        print("🎉 ML增强系统演示完成!")
        
        print(f"\n🤖 系统特色:")
        print("  ✅ 智能特征工程 - 自动创建50+技术特征")
        print("  ✅ 双模型预测 - 方向+收益率预测")
        print("  ✅ 动态重训练 - 定期更新模型")
        print("  ✅ 置信度评估 - 基于预测置信度调整仓位")
        print("  ✅ 技术指标融合 - ML信号与技术分析结合")
        print("  ✅ 性能监控 - 实时跟踪预测准确率")
        
        print(f"\n💡 关键创新:")
        print("  🔸 市场环境特征 - 识别不同市场状态")
        print("  🔸 自适应学习 - 根据市场变化重新训练")
        print("  🔸 多维度信号 - 技术+ML双重确认")
        print("  🔸 风险感知 - 基于预测置信度管理风险")
        print("  🔸 特征重要性 - 识别最有价值的预测因子")
        
        print(f"\n⚠️ 注意事项:")
        print("  • ML模型需要充足的历史数据")
        print("  • 过拟合风险需要谨慎管理")
        print("  • 模型需要定期重新训练")
        print("  • 不应完全依赖ML预测")
        print("  • 建议结合传统技术分析")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()