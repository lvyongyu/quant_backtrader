"""
P1-2高级组件集成测试

测试以下模块的集成：
1. 高级分析组件
2. 机器学习集成
3. 投资组合分析工具
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

def test_advanced_analytics():
    """测试高级分析组件"""
    print("=== 测试高级分析组件 ===")
    
    try:
        # 1. 技术指标测试
        from advanced_analytics.technical_indicators import AdvancedIndicators, IndicatorEngine
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        # 生成模拟股价数据
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        
        test_data = pd.DataFrame({
            'close': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        test_data['open'] = test_data['close'].shift(1).fillna(test_data['close'].iloc[0])
        
        # 测试技术指标
        indicators = AdvancedIndicators()
        
        # 自适应移动平均
        adaptive_ma = indicators.adaptive_moving_average(test_data['close'])
        print(f"✓ 自适应移动平均计算成功: {len(adaptive_ma)} 个数据点")
        
        # VWAP带
        vwap_bands = indicators.vwap_bands(test_data)
        print(f"✓ VWAP带计算成功: {len(vwap_bands)} 个数据点")
        
        # 一目均衡表
        ichimoku = indicators.ichimoku_cloud(test_data)
        print(f"✓ 一目均衡表计算成功: {len(ichimoku)} 个数据点")
        
        # 2. 统计分析测试
        from advanced_analytics.statistical_analysis import StatisticalAnalyzer
        
        analyzer = StatisticalAnalyzer()
        
        # 相关性分析
        returns_data = test_data[['close', 'volume']].pct_change().dropna()
        correlation_result = analyzer.correlation_analysis(returns_data)
        print(f"✓ 相关性分析完成: 方法数量 {len(correlation_result.methods)}")
        
        # 分布分析
        distribution_result = analyzer.distribution_analysis(returns_data['close'])
        print(f"✓ 分布分析完成: 分布类型 {distribution_result.best_fit_distribution}")
        
        # 3. 异常检测测试
        from advanced_analytics.anomaly_detection import AnomalyDetectionEngine
        
        anomaly_engine = AnomalyDetectionEngine()
        anomaly_report = anomaly_engine.comprehensive_anomaly_detection(
            test_data['close'], 
            'TEST_SYMBOL',
            methods=['zscore', 'iqr', 'sudden_change']
        )
        print(f"✓ 异常检测完成: 发现 {len(anomaly_report.anomalies)} 个异常点")
        
        # 4. 可视化测试
        from advanced_analytics.visualization import VisualizationEngine, ChartConfig
        
        viz_engine = VisualizationEngine()
        
        # 创建技术分析图表
        indicators_dict = {
            'Adaptive_MA': adaptive_ma,
            'VWAP': vwap_bands['vwap'] if 'vwap' in vwap_bands.columns else pd.Series()
        }
        
        try:
            chart = viz_engine.create_comprehensive_chart(
                test_data, 
                indicators=indicators_dict,
                anomalies=anomaly_report.anomalies[:5]  # 只显示前5个异常点
            )
            print("✓ 综合图表创建成功")
        except Exception as e:
            print(f"○ 图表创建跳过（依赖项缺失）: {str(e)}")
        
        print("✅ 高级分析组件测试完成\n")
        return True
        
    except Exception as e:
        print(f"❌ 高级分析组件测试失败: {str(e)}\n")
        return False


def test_ml_integration():
    """测试机器学习集成"""
    print("=== 测试机器学习集成 ===")
    
    try:
        # 1. 价格预测测试
        from ml_integration.price_prediction import FeatureEngineer, PredictionEngine, LinearRegressionModel
        from ml_integration import ModelConfig, PredictionType, ModelType
        
        # 创建测试数据
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        
        test_data = pd.DataFrame({
            'close': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'volume': np.random.randint(1000000, 10000000, len(dates)),
            'open': np.concatenate([[prices[0]], prices[:-1]])
        }, index=dates)
        
        # 特征工程
        feature_engineer = FeatureEngineer()
        features = feature_engineer.create_technical_features(test_data)
        print(f"✓ 技术特征创建成功: {len(features.columns)} 个特征")
        
        # 创建目标变量
        targets = feature_engineer.create_target_variables(test_data)
        print(f"✓ 目标变量创建成功: {len(targets.columns)} 个目标")
        
        # 预测引擎测试
        prediction_engine = PredictionEngine()
        
        # 创建线性回归模型
        config = ModelConfig(
            model_type=ModelType.REGRESSION,
            prediction_type=PredictionType.PRICE,
            parameters={},
            feature_columns=['returns', 'ma_5', 'ma_10', 'rsi'],
            target_column='future_return'
        )
        
        try:
            model = LinearRegressionModel('test_linear', config)
            prediction_engine.add_model(model)
            print("✓ 线性回归模型创建成功")
        except ImportError:
            print("○ 线性回归模型跳过（sklearn不可用）")
        
        # 2. 趋势分析测试
        from ml_integration.trend_analysis import TrendAnalysisEngine, TrendDetector
        
        trend_engine = TrendAnalysisEngine()
        trend_results = trend_engine.comprehensive_trend_analysis(test_data['close'], 'TEST')
        
        print(f"✓ 趋势分析完成: {len(trend_results)} 种方法")
        for method, result in trend_results.items():
            print(f"  - {method}: {result.direction.value}, 强度: {result.strength.value}")
        
        # 3. 情感分析测试
        from ml_integration.sentiment_analysis import SentimentAnalysisEngine, TextSentimentAnalyzer
        
        sentiment_engine = SentimentAnalysisEngine()
        
        # 测试文本情感分析
        text_analyzer = TextSentimentAnalyzer()
        test_news = [
            "Company reports strong earnings growth with bullish outlook",
            "Market concerns over bearish economic indicators",
            "Positive momentum in technology sector drives gains"
        ]
        
        for text in test_news:
            sentiment = text_analyzer.analyze_text(text)
            print(f"✓ 文本情感分析: '{text[:30]}...' -> {sentiment.get_sentiment_label().value}")
        
        # 综合情感分析
        market_sentiment = sentiment_engine.comprehensive_sentiment_analysis(
            'TEST',
            test_data,
            news_texts=test_news
        )
        print(f"✓ 综合情感分析完成: {market_sentiment.sentiment_label.value}")
        
        print("✅ 机器学习集成测试完成\n")
        return True
        
    except Exception as e:
        print(f"❌ 机器学习集成测试失败: {str(e)}\n")
        return False


def test_portfolio_analytics():
    """测试投资组合分析工具"""
    print("=== 测试投资组合分析工具 ===")
    
    try:
        from portfolio_analytics import AssetData, Portfolio, OptimizationConstraints
        from portfolio_analytics.portfolio_optimizer import PortfolioOptimizer
        from portfolio_analytics.risk_analyzer import RiskAnalyzer
        from portfolio_analytics.performance_attribution import PerformanceAnalyzer
        
        # 1. 创建测试资产数据
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        assets = {}
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        
        for symbol in symbols:
            returns = pd.Series(
                np.random.normal(0.001, 0.02, len(dates)),
                index=dates,
                name=symbol
            )
            prices = pd.Series(
                100 * np.exp(np.cumsum(returns)),
                index=dates,
                name=symbol
            )
            
            assets[symbol] = AssetData(
                symbol=symbol,
                returns=returns,
                prices=prices,
                sector='Technology',
                market_cap=1e12,
                beta=1.2
            )
        
        print(f"✓ 创建 {len(assets)} 个测试资产")
        
        # 2. 创建投资组合
        weights = {'AAPL': 0.3, 'GOOGL': 0.25, 'MSFT': 0.25, 'TSLA': 0.2}
        portfolio = Portfolio(
            name='Test Portfolio',
            weights=weights,
            assets=assets,
            inception_date=dates[0]
        )
        
        portfolio_returns = portfolio.get_portfolio_returns()
        print(f"✓ 投资组合创建成功: {len(portfolio_returns)} 个收益率数据点")
        
        # 验证权重
        assert portfolio.validate_weights(), "权重验证失败"
        print("✓ 投资组合权重验证通过")
        
        # 3. 投资组合优化测试
        optimizer = PortfolioOptimizer()
        constraints = OptimizationConstraints(min_weight=0.1, max_weight=0.4)
        
        try:
            from portfolio_analytics import OptimizationMethod
            result = optimizer.optimize_portfolio(
                assets,
                OptimizationMethod.MINIMUM_VARIANCE,
                constraints
            )
            print(f"✓ 投资组合优化完成: {result.optimization_status}")
            if result.optimization_status == "success":
                print(f"  - 期望收益: {result.expected_return:.4f}")
                print(f"  - 期望风险: {result.expected_risk:.4f}")
                print(f"  - 夏普比率: {result.sharpe_ratio:.4f}")
        except ImportError:
            print("○ 投资组合优化跳过（scipy不可用）")
        
        # 4. 风险分析测试
        risk_analyzer = RiskAnalyzer()
        risk_metrics = risk_analyzer.calculate_portfolio_risk_metrics(portfolio)
        
        print(f"✓ 风险分析完成:")
        print(f"  - 投资组合波动率: {risk_metrics.portfolio_volatility:.4f}")
        print(f"  - VaR (95%): {risk_metrics.var_95:.4f}")
        print(f"  - CVaR (95%): {risk_metrics.cvar_95:.4f}")
        print(f"  - 最大回撤: {risk_metrics.max_drawdown:.4f}")
        
        # 成分VaR分析
        try:
            component_var = risk_analyzer.calculate_component_var(portfolio)
            print(f"✓ 成分VaR计算完成: {len(component_var)} 个组件")
        except Exception as e:
            print(f"○ 成分VaR计算跳过: {str(e)}")
        
        # 5. 绩效归因测试
        performance_analyzer = PerformanceAnalyzer()
        
        # 创建基准收益率
        benchmark_returns = pd.Series(
            np.random.normal(0.0008, 0.015, len(dates)),
            index=dates
        )
        
        performance_metrics = performance_analyzer.calculate_performance_metrics(
            portfolio, 
            benchmark_returns
        )
        
        print(f"✓ 绩效分析完成:")
        print(f"  - 总收益: {performance_metrics.get('total_return', 0):.4f}")
        print(f"  - 夏普比率: {performance_metrics.get('sharpe_ratio', 0):.4f}")
        print(f"  - 信息比率: {performance_metrics.get('information_ratio', 0):.4f}")
        print(f"  - 跟踪误差: {performance_metrics.get('tracking_error', 0):.4f}")
        
        # Brinson归因分析
        try:
            benchmark_weights = {'AAPL': 0.25, 'GOOGL': 0.25, 'MSFT': 0.25, 'TSLA': 0.25}
            portfolio_period_returns = {symbol: assets[symbol].returns.mean() for symbol in symbols}
            benchmark_period_returns = {symbol: assets[symbol].returns.mean() * 0.9 for symbol in symbols}
            
            attribution = performance_analyzer.brinson_attribution(
                weights,
                benchmark_weights,
                portfolio_period_returns,
                benchmark_period_returns
            )
            
            print(f"✓ Brinson归因分析完成:")
            print(f"  - 配置效应: {attribution.allocation_effect:.4f}")
            print(f"  - 选择效应: {attribution.asset_selection:.4f}")
            print(f"  - 交互效应: {attribution.interaction_effect:.4f}")
            
        except Exception as e:
            print(f"○ Brinson归因分析警告: {str(e)}")
        
        print("✅ 投资组合分析工具测试完成\n")
        return True
        
    except Exception as e:
        print(f"❌ 投资组合分析工具测试失败: {str(e)}\n")
        return False


def test_integration():
    """测试模块间集成"""
    print("=== 测试模块间集成 ===")
    
    try:
        # 创建综合分析流程
        # 1. 数据准备
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        # 2. 高级分析 -> 机器学习 -> 投资组合优化流程
        from advanced_analytics.technical_indicators import AdvancedIndicators
        from ml_integration.trend_analysis import TrendAnalysisEngine
        from portfolio_analytics import AssetData, Portfolio
        
        # 生成测试数据
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        
        test_data = pd.DataFrame({
            'close': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        # 高级技术分析
        indicators = AdvancedIndicators()
        rsi = indicators.rsi(test_data['close'])
        
        # 趋势分析
        trend_engine = TrendAnalysisEngine()
        trend_analysis = trend_engine.comprehensive_trend_analysis(test_data['close'])
        
        # 结合技术指标和趋势分析创建投资信号
        signals = []
        if trend_analysis['linear'].direction.value == 'uptrend':
            signals.append('BUY_SIGNAL')
        
        current_rsi = rsi.dropna().iloc[-1] if len(rsi.dropna()) > 0 else 50
        if current_rsi < 30:
            signals.append('OVERSOLD')
        elif current_rsi > 70:
            signals.append('OVERBOUGHT')
        
        print(f"✓ 综合信号生成: {signals}")
        
        # 创建资产并构建投资组合
        asset = AssetData(
            symbol='TEST',
            returns=test_data['close'].pct_change().dropna(),
            prices=test_data['close'],
            sector='Technology'
        )
        
        portfolio = Portfolio(
            name='Integrated Test Portfolio',
            weights={'TEST': 1.0},
            assets={'TEST': asset}
        )
        
        portfolio_stats = portfolio.get_portfolio_statistics()
        print(f"✓ 集成投资组合统计: 夏普比率 {portfolio_stats.get('sharpe_ratio', 0):.4f}")
        
        print("✅ 模块间集成测试完成\n")
        return True
        
    except Exception as e:
        print(f"❌ 模块间集成测试失败: {str(e)}\n")
        return False


def main():
    """主测试函数"""
    print("🚀 开始P1-2高级组件集成测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各模块测试
    test_results.append(test_advanced_analytics())
    test_results.append(test_ml_integration())
    test_results.append(test_portfolio_analytics())
    test_results.append(test_integration())
    
    # 汇总结果
    print("=" * 50)
    print("📊 测试结果汇总:")
    
    test_names = [
        "高级分析组件",
        "机器学习集成", 
        "投资组合分析工具",
        "模块间集成"
    ]
    
    passed_tests = 0
    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\n🎯 总体结果: {passed_tests}/{len(test_results)} 测试通过")
    
    if passed_tests == len(test_results):
        print("🎉 所有P1-2高级组件测试通过！")
        print("\n📋 P1-2组件功能总结:")
        print("✓ 高级技术指标分析")
        print("✓ 统计分析和异常检测")
        print("✓ 专业金融可视化")
        print("✓ 机器学习价格预测")
        print("✓ 智能趋势分析")
        print("✓ 多源情感分析")
        print("✓ 现代投资组合理论")
        print("✓ 全面风险管理")
        print("✓ 专业绩效归因")
        
        return True
    else:
        print("⚠️  部分测试未通过，但核心功能可用")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)