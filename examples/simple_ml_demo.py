#!/usr/bin/env python3
"""
简化机器学习交易演示
Simplified ML Trading Demo

展示机器学习在量化交易中的应用
"""

import backtrader as bt
import numpy as np
import pandas as pd
import random
import datetime
import tempfile
import csv
import os

# 检查依赖
try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn不可用，将使用简化的ML模拟")

class SimpleMLPredictor:
    """简化的ML预测器"""
    
    def __init__(self):
        self.is_trained = False
        self.feature_weights = {}
        self.accuracy = 0.0
        
    def create_features(self, prices, volumes):
        """创建技术特征"""
        
        if len(prices) < 20:
            return []
        
        features = []
        
        # 价格特征
        current_price = prices[-1]
        sma_5 = np.mean(prices[-5:])
        sma_10 = np.mean(prices[-10:])
        sma_20 = np.mean(prices[-20:])
        
        # 相对位置特征
        price_to_sma5 = current_price / sma_5 if sma_5 > 0 else 1.0
        price_to_sma10 = current_price / sma_10 if sma_10 > 0 else 1.0
        price_to_sma20 = current_price / sma_20 if sma_20 > 0 else 1.0
        
        # 动量特征
        momentum_5 = (prices[-1] / prices[-6] - 1) if len(prices) >= 6 else 0.0
        momentum_10 = (prices[-1] / prices[-11] - 1) if len(prices) >= 11 else 0.0
        
        # 波动率特征
        returns_5 = [prices[i]/prices[i-1]-1 for i in range(-5, 0) if i > -len(prices)]
        volatility = np.std(returns_5) if len(returns_5) > 1 else 0.0
        
        # RSI-like指标
        gains = [max(0, r) for r in returns_5]
        losses = [max(0, -r) for r in returns_5]
        avg_gain = np.mean(gains) if gains else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        rsi_like = 50.0  # 默认中性
        if avg_loss > 0:
            rs = avg_gain / avg_loss
            rsi_like = 100 - (100 / (1 + rs))
        
        # 成交量特征
        current_volume = volumes[-1] if volumes else 100000
        avg_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else current_volume
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        features = [
            price_to_sma5, price_to_sma10, price_to_sma20,
            momentum_5, momentum_10, volatility,
            rsi_like / 100.0,  # 归一化到0-1
            volume_ratio,
            min(max(sma_5 / sma_20 - 1, -0.1), 0.1) if sma_20 > 0 else 0.0  # 趋势强度
        ]
        
        return features
    
    def train(self, price_history, volume_history, future_returns):
        """训练模型"""
        
        if len(price_history) < 30:
            return False
        
        print("🤖 训练简化ML模型...")
        
        training_data = []
        labels = []
        
        # 准备训练数据
        for i in range(20, len(price_history) - 5):
            features = self.create_features(
                price_history[:i+1], 
                volume_history[:i+1]
            )
            
            if len(features) == 9:  # 确保特征完整
                # 未来收益（5天后）
                future_return = (price_history[i+5] / price_history[i] - 1) if i+5 < len(price_history) else 0
                direction = 1 if future_return > 0 else 0
                
                training_data.append(features)
                labels.append(direction)
        
        if len(training_data) < 10:
            return False
        
        # 使用scikit-learn训练
        if SKLEARN_AVAILABLE:
            try:
                X = np.array(training_data)
                y = np.array(labels)
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.3, random_state=42
                )
                
                self.model = RandomForestClassifier(
                    n_estimators=50, 
                    max_depth=6, 
                    random_state=42
                )
                self.model.fit(X_train, y_train)
                
                # 评估模型
                y_pred = self.model.predict(X_test)
                self.accuracy = accuracy_score(y_test, y_pred)
                
                # 特征重要性
                feature_names = [
                    'price_to_sma5', 'price_to_sma10', 'price_to_sma20',
                    'momentum_5', 'momentum_10', 'volatility',
                    'rsi_like', 'volume_ratio', 'trend_strength'
                ]
                
                self.feature_weights = dict(zip(
                    feature_names, 
                    self.model.feature_importances_
                ))
                
                self.is_trained = True
                
                print(f"✅ 模型训练完成:")
                print(f"   训练样本: {len(X_train)}")
                print(f"   测试准确率: {self.accuracy:.3f}")
                
                return True
                
            except Exception as e:
                print(f"❌ sklearn训练失败: {e}")
        
        # 简化训练（如果sklearn不可用）
        print("🔧 使用简化算法训练...")
        
        # 简单的基于统计的预测
        up_count = sum(labels)
        total_count = len(labels)
        self.base_probability = up_count / total_count if total_count > 0 else 0.5
        
        # 计算特征相关性（简化版）
        self.feature_correlations = []
        for i in range(9):  # 9个特征
            feature_values = [data[i] for data in training_data]
            correlation = np.corrcoef(feature_values, labels)[0, 1] if len(feature_values) > 1 else 0
            self.feature_correlations.append(correlation if not np.isnan(correlation) else 0)
        
        self.accuracy = 0.55  # 模拟准确率
        self.is_trained = True
        
        print(f"✅ 简化模型训练完成:")
        print(f"   基础概率: {self.base_probability:.3f}")
        print(f"   模拟准确率: {self.accuracy:.3f}")
        
        return True
    
    def predict(self, prices, volumes):
        """预测方向"""
        
        if not self.is_trained:
            return {'direction_prob': 0.5, 'confidence': 0.0}
        
        features = self.create_features(prices, volumes)
        
        if len(features) != 9:
            return {'direction_prob': 0.5, 'confidence': 0.0}
        
        if SKLEARN_AVAILABLE and hasattr(self, 'model'):
            try:
                X = np.array([features])
                prob = self.model.predict_proba(X)[0]
                direction_prob = prob[1] if len(prob) > 1 else 0.5
                confidence = abs(direction_prob - 0.5) * 2
                
                return {
                    'direction_prob': float(direction_prob),
                    'confidence': float(confidence)
                }
            except:
                pass
        
        # 简化预测
        signal = 0
        for i, feature in enumerate(features):
            if i < len(self.feature_correlations):
                signal += feature * self.feature_correlations[i]
        
        # 归一化到概率
        direction_prob = max(0.1, min(0.9, self.base_probability + signal * 0.1))
        confidence = abs(direction_prob - 0.5) * 2
        
        return {
            'direction_prob': direction_prob,
            'confidence': confidence
        }

class MLEnhancedStrategy(bt.Strategy):
    """ML增强策略"""
    
    params = (
        ('confidence_threshold', 0.3),  # 置信度阈值
        ('direction_threshold', 0.6),   # 方向阈值
        ('position_size', 0.8),         # 仓位大小
        ('retrain_period', 30),         # 重训练周期
    )
    
    def __init__(self):
        # 技术指标
        self.sma_short = bt.indicators.SMA(period=10)
        self.sma_long = bt.indicators.SMA(period=20)
        self.rsi = bt.indicators.RSI(period=14)
        
        # ML模型
        self.predictor = SimpleMLPredictor()
        
        # 数据存储
        self.price_history = []
        self.volume_history = []
        
        # 交易状态
        self.order = None
        self.buy_price = None
        self.trade_count = 0
        self.ml_signals = 0
        self.last_retrain = 0
        
        print(f"🤖 ML增强策略初始化:")
        print(f"   置信度阈值: {self.p.confidence_threshold}")
        print(f"   方向阈值: {self.p.direction_threshold}")
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def next(self):
        # 收集数据
        self.price_history.append(self.data.close[0])
        self.volume_history.append(self.data.volume[0])
        
        # 限制历史长度
        if len(self.price_history) > 200:
            self.price_history = self.price_history[-150:]
            self.volume_history = self.volume_history[-150:]
        
        # 等待足够数据
        if len(self.price_history) < 30:
            return
        
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        # 重新训练模型
        if (len(self) - self.last_retrain) >= self.p.retrain_period and len(self.price_history) >= 50:
            self.retrain_model()
        
        # 持仓管理
        if self.position:
            # 简单止损止盈
            if (current_price <= self.buy_price * 0.96 or 
                current_price >= self.buy_price * 1.08):
                self.order = self.sell()
                return
        
        else:
            # 技术信号
            tech_signals = [
                self.data.close[0] > self.sma_short[0],
                self.sma_short[0] > self.sma_long[0],
                30 < self.rsi[0] < 70,
            ]
            tech_score = sum(tech_signals) / len(tech_signals)
            
            # ML预测
            if self.predictor.is_trained:
                prediction = self.predictor.predict(
                    self.price_history, 
                    self.volume_history
                )
                
                ml_confidence = prediction['confidence']
                ml_direction = prediction['direction_prob']
                
                # 综合决策
                if (ml_confidence >= self.p.confidence_threshold and
                    ml_direction >= self.p.direction_threshold and
                    tech_score >= 0.5):
                    
                    cash = self.broker.get_cash()
                    size = int((cash * self.p.position_size) / current_price)
                    
                    if size > 0:
                        self.order = self.buy(size=size)
                        self.buy_price = current_price
                        self.ml_signals += 1
                        
                        self.log(f'🚀 ML信号开仓:')
                        self.log(f'   ML置信度: {ml_confidence:.3f}')
                        self.log(f'   方向概率: {ml_direction:.3f}')
                        self.log(f'   技术评分: {tech_score:.3f}')
    
    def retrain_model(self):
        """重新训练模型"""
        
        self.log("🔄 重新训练ML模型...")
        
        # 准备未来收益数据
        future_returns = []
        for i in range(len(self.price_history) - 5):
            future_return = (self.price_history[i+5] / self.price_history[i] - 1)
            future_returns.append(future_return)
        
        success = self.predictor.train(
            self.price_history[:-5], 
            self.volume_history[:-5], 
            future_returns
        )
        
        if success:
            self.last_retrain = len(self)
            self.log(f"✅ 模型重训练完成, 准确率: {self.predictor.accuracy:.3f}")
    
    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'💰 买入: ${order.executed.price:.2f}')
            else:
                pnl = (order.executed.price - self.buy_price) / self.buy_price * 100
                self.log(f'💰 卖出: ${order.executed.price:.2f}, 收益: {pnl:+.2f}%')
                self.trade_count += 1
        
        self.order = None
    
    def stop(self):
        final_value = self.broker.getvalue()
        total_return = (final_value - 10000) / 10000 * 100
        
        print('\n' + '='*50)
        print('🤖 ML增强策略结果:')
        print(f'💰 初始: $10,000 → 最终: ${final_value:.2f}')
        print(f'📈 总收益率: {total_return:+.2f}%')
        print(f'🔄 完成交易: {self.trade_count} 笔')
        print(f'🤖 ML信号: {self.ml_signals} 次')
        
        if self.predictor.is_trained:
            print(f'🎯 模型准确率: {self.predictor.accuracy:.3f}')
            
            if hasattr(self.predictor, 'feature_weights') and self.predictor.feature_weights:
                print(f'📊 重要特征 (TOP 3):')
                sorted_features = sorted(
                    self.predictor.feature_weights.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                for i, (feature, weight) in enumerate(sorted_features[:3], 1):
                    print(f'   {i}. {feature}: {weight:.4f}')
        
        print('='*50)

def generate_test_data(days=100):
    """生成测试数据"""
    
    data = []
    base_price = 100.0
    trend = 0.0
    
    start_date = datetime.datetime(2023, 1, 1)
    
    for i in range(days):
        date = start_date + datetime.timedelta(days=i)
        
        if date.weekday() >= 5:  # 跳过周末
            continue
        
        # 添加趋势和随机性
        trend_change = random.gauss(0, 0.002)
        trend += trend_change
        trend = max(-0.03, min(0.03, trend))
        
        daily_return = trend + random.gauss(0, 0.025)
        base_price *= (1 + daily_return)
        base_price = max(50, base_price)
        
        # OHLCV
        open_price = base_price * random.uniform(0.99, 1.01)
        high_price = base_price * random.uniform(1.01, 1.05)
        low_price = base_price * random.uniform(0.95, 0.99)
        close_price = base_price
        volume = random.randint(80000, 200000)
        
        data.append([
            date.strftime('%Y-%m-%d'),
            round(open_price, 2),
            round(high_price, 2),
            round(low_price, 2),
            round(close_price, 2),
            volume
        ])
    
    return data

def run_ml_demo():
    """运行ML演示"""
    
    print("🤖 机器学习交易系统演示")
    print("="*40)
    
    # 检查依赖
    if SKLEARN_AVAILABLE:
        print("✅ scikit-learn 可用")
    else:
        print("⚠️  使用简化ML算法")
    
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(MLEnhancedStrategy)
    
    # 生成并添加数据
    print("📊 生成测试数据...")
    test_data = generate_test_data(120)
    
    # 创建临时CSV文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    writer = csv.writer(temp_file)
    writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
    writer.writerows(test_data)
    temp_file.close()
    
    # 添加数据到Backtrader
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
    
    # 设置资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)
    
    print(f"💰 初始资金: ${cerebro.broker.getvalue():.2f}")
    print("-" * 40)
    
    # 运行回测
    results = cerebro.run()
    
    # 清理临时文件
    os.unlink(temp_file.name)
    
    if results:
        strat = results[0]
        
        # 分析结果
        try:
            trade_analysis = strat.analyzers.trades.get_analysis()
            
            total_trades = trade_analysis.get('total', {}).get('total', 0)
            won_trades = trade_analysis.get('won', {}).get('total', 0)
            
            if total_trades > 0:
                win_rate = won_trades / total_trades * 100
                print(f"\n📈 交易分析:")
                print(f"   胜率: {win_rate:.1f}% ({won_trades}/{total_trades})")
                
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
    """运行演示"""
    
    print("🎯 机器学习增强交易演示")
    print("="*50)
    
    try:
        run_ml_demo()
        
        print(f"\n" + "="*50)
        print("🎉 ML演示完成!")
        
        print(f"\n🤖 系统特点:")
        print("  ✅ 自适应特征工程")
        print("  ✅ 动态模型训练")
        print("  ✅ 置信度评估")
        print("  ✅ 技术指标融合")
        print("  ✅ 实时预测")
        
        print(f"\n💡 核心优势:")
        print("  🔸 学习市场模式")
        print("  🔸 适应市场变化")
        print("  🔸 量化预测置信度")
        print("  🔸 多信号确认")
        print("  🔸 风险控制")
        
        print(f"\n⚠️  注意事项:")
        print("  • ML需要充足历史数据")
        print("  • 避免过度拟合")
        print("  • 定期重新训练")
        print("  • 结合传统分析")
        print("  • 谨慎使用预测结果")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()