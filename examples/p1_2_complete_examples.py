"""
P1-2高级量化交易组件 - 完整使用示例

这个文件展示了如何在实际项目中使用P1-2的三大核心组件：
1. 高级分析组件 - 技术指标和统计分析
2. 机器学习集成 - 价格预测和趋势分析  
3. 投资组合分析 - 现代投资组合理论和风险管理

作者: P1-2开发团队
版本: 1.0
日期: 2025-10-01
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# ============================================================================
# 示例1: 单只股票技术分析 - Apple (AAPL)
# ============================================================================

def example_1_technical_analysis():
    """
    示例1: 使用高级分析组件对Apple股票进行技术分析
    """
    print("=" * 60)
    print("📊 示例1: Apple股票技术分析")
    print("=" * 60)
    
    try:
        # 1. 准备测试数据
        print("📈 准备Apple股票价格数据...")
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # 模拟Apple股票价格走势
        initial_price = 150.0
        returns = pd.Series(
            np.random.normal(0.0008, 0.02, len(dates)),  # 年化8%收益，20%波动
            index=dates
        )
        prices = pd.Series(
            initial_price * np.exp(np.cumsum(returns)),
            index=dates,
            name='AAPL'
        )
        
        print(f"✓ 数据时间范围: {prices.index[0].date()} 到 {prices.index[-1].date()}")
        print(f"✓ 价格范围: ${prices.min():.2f} - ${prices.max():.2f}")
        
        # 2. 计算技术指标
        from advanced_analytics.technical_indicators import AdvancedIndicators
        
        indicators = AdvancedIndicators()
        print("\n🔍 计算技术指标...")
        
        # RSI指标
        rsi_result = indicators.calculate_rsi(prices, period=14)
        current_rsi = rsi_result.values.iloc[-1]
        print(f"✓ RSI(14): {current_rsi:.2f} - {rsi_result.interpretation}")
        
        # MACD指标
        macd_result = indicators.calculate_macd(prices)
        macd_line = macd_result.values['macd'].iloc[-1]
        signal_line = macd_result.values['signal'].iloc[-1]
        print(f"✓ MACD: {macd_line:.4f}, Signal: {signal_line:.4f}")
        
        # 布林带
        bollinger_result = indicators.calculate_bollinger_bands(prices, period=20)
        current_price = prices.iloc[-1]
        upper_band = bollinger_result.values['upper'].iloc[-1]
        lower_band = bollinger_result.values['lower'].iloc[-1]
        print(f"✓ 布林带: 上轨${upper_band:.2f}, 下轨${lower_band:.2f}, 当前${current_price:.2f}")
        
        # 多指标分析
        multi_results = indicators.calculate_multiple_indicators(
            prices, 
            ['rsi', 'stochastic', 'williams_r']
        )
        
        print("\n📋 多指标分析结果:")
        for indicator_name, result in multi_results.items():
            if hasattr(result, 'values') and not result.values.empty:
                current_value = result.values.iloc[-1] if isinstance(result.values, pd.Series) else result.values['main'].iloc[-1]
                print(f"  {indicator_name}: {current_value:.2f}")
        
        # 3. 统计分析
        from advanced_analytics.statistical_analysis import StatisticalAnalyzer
        
        print("\n📊 统计分析...")
        analyzer = StatisticalAnalyzer()
        
        # 收益率分布分析
        returns_data = prices.pct_change().dropna()
        distribution_result = analyzer.analyze_distribution(
            returns_data,
            test_normality=True,
            calculate_moments=True
        )
        
        print(f"✓ 收益率统计:")
        print(f"  平均收益: {returns_data.mean():.4f}")
        print(f"  波动率: {returns_data.std():.4f}")
        print(f"  偏度: {distribution_result.results.get('skewness', 0):.3f}")
        print(f"  峰度: {distribution_result.results.get('kurtosis', 0):.3f}")
        
        # 4. 交易信号生成
        print("\n🎯 生成交易信号...")
        
        # 综合信号判断
        signals = []
        
        # RSI信号
        if current_rsi < 30:
            signals.append("RSI超卖，考虑买入")
        elif current_rsi > 70:
            signals.append("RSI超买，考虑卖出")
        
        # MACD信号
        if macd_line > signal_line:
            signals.append("MACD金叉，趋势向上")
        else:
            signals.append("MACD死叉，趋势向下")
        
        # 布林带信号
        if current_price < lower_band:
            signals.append("价格接近布林带下轨，可能反弹")
        elif current_price > upper_band:
            signals.append("价格接近布林带上轨，可能回调")
        
        print("📢 交易信号:")
        for signal in signals:
            print(f"  • {signal}")
        
        if not signals:
            print("  • 当前无明确交易信号，持有观望")
        
        print("\n✅ Apple技术分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 技术分析失败: {str(e)}")
        return False


# ============================================================================
# 示例2: 机器学习价格预测 - 多股票预测
# ============================================================================

def example_2_ml_prediction():
    """
    示例2: 使用机器学习组件预测多只股票的价格走势
    """
    print("\n" + "=" * 60)
    print("🤖 示例2: 机器学习价格预测")
    print("=" * 60)
    
    try:
        # 1. 准备多股票数据
        print("📊 准备多股票数据...")
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        stock_data = {}
        for i, symbol in enumerate(symbols):
            # 为不同股票生成不同特征的价格数据
            returns = pd.Series(
                np.random.normal(0.001 + i*0.0002, 0.018 + i*0.003, len(dates)),
                index=dates
            )
            prices = pd.Series(
                (100 + i*20) * np.exp(np.cumsum(returns)),
                index=dates,
                name=symbol
            )
            stock_data[symbol] = prices
            
        print(f"✓ 准备了 {len(symbols)} 只股票的数据")
        
        # 2. 特征工程
        from ml_integration.price_prediction import FeatureEngineer
        
        print("\n🔧 执行特征工程...")
        feature_engineer = FeatureEngineer()
        
        # 为每只股票创建特征
        all_features = {}
        for symbol, prices in stock_data.items():
            print(f"  处理 {symbol}...")
            
            # 创建价格数据框
            price_df = pd.DataFrame({
                'open': prices,
                'high': prices * (1 + np.random.uniform(0, 0.02, len(prices))),
                'low': prices * (1 - np.random.uniform(0, 0.02, len(prices))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(prices))
            })
            
            # 添加技术指标特征
            features = feature_engineer.add_technical_features(
                price_df,
                indicators=['rsi', 'macd', 'bollinger_bands'],
                periods={'rsi': [14], 'macd': [12, 26, 9]}
            )
            
            # 创建滞后特征
            features = feature_engineer.create_lag_features(
                features,
                columns=['close', 'volume'],
                lags=[1, 2, 3, 5],
                include_rolling_stats=True
            )
            
            # 创建目标变量（未来5日收益率）
            features['future_return_5d'] = prices.pct_change(5).shift(-5)
            
            all_features[symbol] = features.dropna()
            
        print(f"✓ 特征工程完成，每只股票约有 {len(all_features[symbols[0]].columns)} 个特征")
        
        # 3. 模型训练和预测
        from ml_integration.price_prediction import PredictionEngine
        from ml_integration import ModelConfig, ModelType, PredictionType
        
        print("\n🎯 训练预测模型...")
        prediction_engine = PredictionEngine()
        
        predictions_summary = {}
        
        for symbol in symbols:
            print(f"\n  训练 {symbol} 预测模型...")
            features = all_features[symbol]
            
            # 准备训练数据
            feature_columns = [col for col in features.columns if col != 'future_return_5d']
            X = features[feature_columns].fillna(0)
            y = features['future_return_5d'].fillna(0)
            
            # 分割训练和测试数据
            split_point = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
            y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]
            
            # 模型配置
            config = ModelConfig(
                model_type=ModelType.RANDOM_FOREST,
                prediction_type=PredictionType.RETURN,
                parameters={
                    'n_estimators': 50,
                    'max_depth': 8,
                    'min_samples_split': 10,
                    'random_state': 42
                },
                feature_columns=feature_columns[:10],  # 使用前10个特征
                target_column='future_return_5d'
            )
            
            # 训练模型
            model = prediction_engine.train_model(
                pd.concat([X_train[config.feature_columns], y_train], axis=1),
                config
            )
            
            # 生成预测
            if len(X_test) > 0:
                predictions = prediction_engine.predict(
                    model,
                    X_test[config.feature_columns].tail(1),
                    prediction_horizon=5
                )
                
                predictions_summary[symbol] = {
                    'predicted_return': predictions.predicted_value,
                    'confidence': predictions.confidence,
                    'current_price': stock_data[symbol].iloc[-1],
                    'predicted_price': stock_data[symbol].iloc[-1] * (1 + predictions.predicted_value)
                }
                
                print(f"    ✓ 预测5日收益率: {predictions.predicted_value:.2%}")
                print(f"    ✓ 预测置信度: {predictions.confidence:.1%}")
        
        # 4. 趋势分析
        from ml_integration.trend_analysis import TrendAnalysisEngine
        
        print("\n📈 趋势分析...")
        trend_analyzer = TrendAnalysisEngine()
        
        trend_summary = {}
        for symbol in symbols:
            prices = stock_data[symbol]
            
            # 多算法趋势分析
            trend_result = trend_analyzer.analyze_trend_multi_algorithm(
                prices,
                algorithms=['linear_regression', 'moving_average'],
                confidence_threshold=0.6
            )
            
            trend_summary[symbol] = {
                'trend_direction': trend_result.trend_direction,
                'trend_strength': trend_result.trend_strength,
                'confidence': trend_result.confidence
            }
            
            print(f"  {symbol}: {trend_result.trend_direction} "
                  f"(强度: {trend_result.trend_strength:.2f}, "
                  f"置信度: {trend_result.confidence:.1%})")
        
        # 5. 综合分析报告
        print("\n" + "="*50)
        print("📋 综合预测报告")
        print("="*50)
        
        for symbol in symbols:
            print(f"\n🔸 {symbol}:")
            
            if symbol in predictions_summary:
                pred = predictions_summary[symbol]
                print(f"  当前价格: ${pred['current_price']:.2f}")
                print(f"  预测价格: ${pred['predicted_price']:.2f}")
                print(f"  预期收益: {pred['predicted_return']:.2%}")
                print(f"  预测置信度: {pred['confidence']:.1%}")
            
            if symbol in trend_summary:
                trend = trend_summary[symbol]
                print(f"  趋势方向: {trend['trend_direction']}")
                print(f"  趋势强度: {trend['trend_strength']:.2f}")
            
            # 投资建议
            if symbol in predictions_summary and symbol in trend_summary:
                pred_return = predictions_summary[symbol]['predicted_return']
                trend_dir = trend_summary[symbol]['trend_direction']
                
                if pred_return > 0.02 and trend_dir == 'upward':
                    recommendation = "🟢 强烈买入"
                elif pred_return > 0.01:
                    recommendation = "🔵 买入"
                elif pred_return < -0.02 and trend_dir == 'downward':
                    recommendation = "🔴 卖出"
                elif pred_return < -0.01:
                    recommendation = "🟡 减持"
                else:
                    recommendation = "⚪ 持有"
                
                print(f"  投资建议: {recommendation}")
        
        print("\n✅ 机器学习预测分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 机器学习预测失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 示例3: 投资组合优化和风险管理
# ============================================================================

def example_3_portfolio_optimization():
    """
    示例3: 使用投资组合分析组件进行现代投资组合理论优化
    """
    print("\n" + "=" * 60)
    print("📊 示例3: 投资组合优化与风险管理")
    print("=" * 60)
    
    try:
        # 1. 构建投资组合资产池
        print("🏗️ 构建投资组合资产池...")
        
        from portfolio_analytics import AssetData, Portfolio
        
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
        sectors = ['Technology', 'Technology', 'Technology', 'Automotive', 
                  'Consumer', 'Technology', 'Technology', 'Entertainment']
        
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        assets = {}
        print(f"📈 生成 {len(symbols)} 只股票的历史数据...")
        
        for i, (symbol, sector) in enumerate(zip(symbols, sectors)):
            # 生成具有不同特征的股票数据
            base_return = 0.0008 + i * 0.0001  # 不同的基础收益率
            volatility = 0.015 + i * 0.002      # 不同的波动率
            
            returns = pd.Series(
                np.random.normal(base_return, volatility, len(dates)),
                index=dates,
                name=symbol
            )
            
            prices = pd.Series(
                (100 + i * 50) * np.exp(np.cumsum(returns)),
                index=dates,
                name=symbol
            )
            
            assets[symbol] = AssetData(
                symbol=symbol,
                returns=returns,
                prices=prices,
                sector=sector,
                market_cap=(500 + i * 200) * 1e9,  # 不同市值
                beta=0.7 + i * 0.2                 # 不同贝塔系数
            )
            
            # 显示资产统计信息
            stats = assets[symbol].get_statistics()
            print(f"  {symbol} ({sector}): "
                  f"年化收益 {stats['annualized_return']:.1%}, "
                  f"波动率 {stats['volatility']:.1%}, "
                  f"夏普比率 {stats['sharpe_ratio']:.2f}")
        
        # 2. 投资组合优化
        from portfolio_analytics.portfolio_optimizer import PortfolioOptimizer
        from portfolio_analytics import OptimizationMethod, OptimizationConstraints
        
        print(f"\n🎯 执行投资组合优化...")
        
        optimizer = PortfolioOptimizer(risk_free_rate=0.02)
        
        # 设置约束条件
        constraints = OptimizationConstraints(
            min_weight=0.05,        # 最小权重5%
            max_weight=0.25,        # 最大权重25%
            max_assets=6,           # 最多6只股票
            sector_constraints={    # 行业约束
                'Technology': 0.60,  # 科技股最多60%
                'Automotive': 0.15,  # 汽车股最多15%
                'Consumer': 0.15     # 消费股最多15%
            }
        )
        
        # 执行多种优化策略
        optimization_methods = [
            (OptimizationMethod.MAXIMUM_SHARPE, "最大夏普比率"),
            (OptimizationMethod.MINIMUM_VARIANCE, "最小方差"),
            (OptimizationMethod.RISK_PARITY, "风险平价"),
            (OptimizationMethod.MAXIMUM_DIVERSIFICATION, "最大分散化")
        ]
        
        optimization_results = {}
        
        for method, method_name in optimization_methods:
            print(f"\n  执行{method_name}优化...")
            
            result = optimizer.optimize_portfolio(assets, method, constraints)
            
            if result.optimization_status == "success":
                optimization_results[method_name] = result
                print(f"    ✓ 优化成功!")
                print(f"    ✓ 期望收益: {result.expected_return:.2%}")
                print(f"    ✓ 期望风险: {result.expected_risk:.2%}")
                print(f"    ✓ 夏普比率: {result.sharpe_ratio:.3f}")
                
                # 显示前5大持仓
                sorted_weights = sorted(result.optimal_weights.items(), 
                                      key=lambda x: x[1], reverse=True)
                print(f"    ✓ 前5大持仓:")
                for symbol, weight in sorted_weights[:5]:
                    print(f"      {symbol}: {weight:.1%}")
            else:
                print(f"    ❌ 优化失败: {result.optimization_status}")
        
        # 3. 有效前沿计算
        from portfolio_analytics.portfolio_optimizer import EfficientFrontier
        
        print(f"\n📈 计算有效前沿...")
        efficient_frontier = EfficientFrontier(optimizer)
        
        frontier_portfolios = efficient_frontier.calculate_efficient_frontier(
            assets, n_portfolios=20, constraints=constraints
        )
        
        print(f"✓ 计算出 {len(frontier_portfolios)} 个有效组合")
        
        # 选择最优组合用于后续分析
        best_portfolio_result = optimization_results.get("最大夏普比率")
        if not best_portfolio_result:
            print("⚠️ 未找到有效的最优组合，使用等权重组合")
            equal_weights = {symbol: 1.0/len(assets) for symbol in assets.keys()}
            best_portfolio_result = type('Result', (), {
                'optimal_weights': equal_weights,
                'expected_return': 0.08,
                'expected_risk': 0.15,
                'sharpe_ratio': 0.4
            })()
        
        # 创建投资组合对象
        portfolio = Portfolio(
            name="优化投资组合",
            weights=best_portfolio_result.optimal_weights,
            assets=assets,
            inception_date=dates[0],
            rebalance_frequency='monthly'
        )
        
        # 4. 风险分析
        from portfolio_analytics.risk_analyzer import RiskAnalyzer, VaRMethod, StressTestType
        
        print(f"\n⚠️ 投资组合风险分析...")
        risk_analyzer = RiskAnalyzer()
        
        # 计算风险指标
        risk_metrics = risk_analyzer.calculate_portfolio_risk_metrics(portfolio)
        
        print(f"📊 风险指标:")
        print(f"  年化波动率: {risk_metrics.portfolio_volatility:.2%}")
        print(f"  VaR (95%): {risk_metrics.var_95:.2%}")
        print(f"  CVaR (95%): {risk_metrics.cvar_95:.2%}")
        print(f"  最大回撤: {risk_metrics.max_drawdown:.2%}")
        print(f"  Sortino比率: {risk_metrics.sortino_ratio:.3f}")
        print(f"  Calmar比率: {risk_metrics.calmar_ratio:.3f}")
        
        # VaR计算（不同方法）
        portfolio_returns = portfolio.get_portfolio_returns()
        print(f"\n📐 VaR计算 (95%置信水平):")
        
        var_methods = [
            (VaRMethod.HISTORICAL, "历史模拟法"),
            (VaRMethod.PARAMETRIC, "参数法"),
            (VaRMethod.MONTE_CARLO, "蒙特卡洛法")
        ]
        
        for method, method_name in var_methods:
            try:
                var_value = risk_analyzer.calculate_var(portfolio_returns, 0.95, method)
                print(f"  {method_name}: {var_value:.2%}")
            except Exception as e:
                print(f"  {method_name}: 计算失败 ({str(e)})")
        
        # 成分VaR分析
        component_var = risk_analyzer.calculate_component_var(portfolio)
        print(f"\n🔍 成分VaR分析:")
        sorted_component_var = sorted(component_var.items(), key=lambda x: abs(x[1]), reverse=True)
        for symbol, var_contribution in sorted_component_var[:5]:
            print(f"  {symbol}: {var_contribution:.4f}")
        
        # 风险预算分析
        risk_budget = risk_analyzer.calculate_risk_budget(portfolio)
        print(f"\n💰 风险预算分析:")
        sorted_risk_budget = sorted(risk_budget.items(), key=lambda x: x[1], reverse=True)
        for symbol, risk_contrib in sorted_risk_budget[:5]:
            print(f"  {symbol}: {risk_contrib:.1%}")
        
        # 压力测试
        print(f"\n🔥 压力测试...")
        stress_scenarios = [
            ({'market_shock': -0.20}, "市场下跌20%"),
            ({'market_shock': -0.30, 'volatility_shock': 2.0}, "市场崩盘情景"),
            ({'sector_shock': {'Technology': -0.25}}, "科技股暴跌25%")
        ]
        
        for stress_params, scenario_name in stress_scenarios:
            try:
                stress_result = risk_analyzer.stress_test(
                    portfolio, StressTestType.FACTOR_SHOCK, stress_params
                )
                loss_pct = stress_result.get('portfolio_loss_pct', 0)
                print(f"  {scenario_name}: 损失 {loss_pct:.1%}")
            except Exception as e:
                print(f"  {scenario_name}: 测试失败 ({str(e)})")
        
        # 5. 绩效归因分析
        from portfolio_analytics.performance_attribution import PerformanceAnalyzer
        
        print(f"\n📈 绩效归因分析...")
        performance_analyzer = PerformanceAnalyzer(risk_free_rate=0.02)
        
        # 创建基准（等权重组合）
        benchmark_weights = {symbol: 1.0/len(assets) for symbol in assets.keys()}
        benchmark_returns = pd.Series(0.0, index=dates)
        for symbol, weight in benchmark_weights.items():
            benchmark_returns += weight * assets[symbol].returns
        
        # 计算绩效指标
        performance_metrics = performance_analyzer.calculate_performance_metrics(
            portfolio, benchmark_returns
        )
        
        print(f"📊 绩效指标:")
        print(f"  总收益率: {performance_metrics.get('total_return', 0):.2%}")
        print(f"  年化收益率: {performance_metrics.get('annualized_return', 0):.2%}")
        print(f"  信息比率: {performance_metrics.get('information_ratio', 0):.3f}")
        print(f"  Alpha: {performance_metrics.get('alpha', 0):.4f}")
        print(f"  Beta: {performance_metrics.get('beta', 0):.3f}")
        
        # Brinson归因分析
        portfolio_period_returns = {symbol: assets[symbol].returns.mean() for symbol in assets.keys()}
        benchmark_period_returns = {symbol: assets[symbol].returns.mean() * 0.98 for symbol in assets.keys()}
        
        brinson_attribution = performance_analyzer.brinson_attribution(
            portfolio_weights=best_portfolio_result.optimal_weights,
            benchmark_weights=benchmark_weights,
            portfolio_returns=portfolio_period_returns,
            benchmark_returns=benchmark_period_returns,
            sector_mapping={symbol: assets[symbol].sector for symbol in assets.keys()}
        )
        
        print(f"\n🎯 Brinson归因分析:")
        print(f"  资产配置效应: {brinson_attribution.allocation_effect:.6f}")
        print(f"  证券选择效应: {brinson_attribution.asset_selection:.6f}")
        print(f"  交互效应: {brinson_attribution.interaction_effect:.6f}")
        print(f"  主动收益: {brinson_attribution.active_return:.6f}")
        
        # 行业归因
        if brinson_attribution.sector_attribution:
            print(f"\n🏭 行业归因分析:")
            for sector, attribution in brinson_attribution.sector_attribution.items():
                print(f"  {sector}: 总效应 {attribution['total']:.6f}")
        
        # 6. 投资建议总结
        print(f"\n" + "="*60)
        print("🎯 投资组合分析总结")
        print("="*60)
        
        print(f"📊 最优投资组合配置:")
        sorted_weights = sorted(best_portfolio_result.optimal_weights.items(), 
                              key=lambda x: x[1], reverse=True)
        total_weight = 0
        for symbol, weight in sorted_weights:
            sector = assets[symbol].sector
            print(f"  {symbol} ({sector}): {weight:.1%}")
            total_weight += weight
        print(f"  总权重: {total_weight:.1%}")
        
        print(f"\n📈 预期表现:")
        print(f"  年化收益率: {best_portfolio_result.expected_return:.2%}")
        print(f"  年化波动率: {best_portfolio_result.expected_risk:.2%}")
        print(f"  夏普比率: {best_portfolio_result.sharpe_ratio:.3f}")
        
        print(f"\n⚠️ 风险评估:")
        if risk_metrics.portfolio_volatility > 0.20:
            print("  🔴 高风险：投资组合波动率较高，适合风险承受能力强的投资者")
        elif risk_metrics.portfolio_volatility > 0.15:
            print("  🟡 中等风险：投资组合风险适中，适合大多数投资者")
        else:
            print("  🟢 低风险：投资组合相对稳健，适合保守型投资者")
        
        print(f"\n💡 投资建议:")
        if best_portfolio_result.sharpe_ratio > 1.0:
            print("  🟢 强烈推荐：风险调整后收益表现优异")
        elif best_portfolio_result.sharpe_ratio > 0.5:
            print("  🔵 推荐：风险调整后收益表现良好")
        else:
            print("  🟡 谨慎：收益风险比一般，建议进一步优化")
        
        diversification_level = len([w for w in best_portfolio_result.optimal_weights.values() if w > 0.05])
        print(f"  📊 分散化程度：{diversification_level}只核心持仓，分散化{'良好' if diversification_level >= 5 else '一般'}")
        
        print(f"\n✅ 投资组合优化与风险管理分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 投资组合分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 示例4: 端到端量化交易策略
# ============================================================================

def example_4_complete_strategy():
    """
    示例4: 完整的端到端量化交易策略
    整合技术分析、机器学习预测和投资组合优化
    """
    print("\n" + "=" * 60)
    print("🚀 示例4: 端到端量化交易策略")
    print("=" * 60)
    
    try:
        print("🎯 策略概述:")
        print("  1. 技术分析筛选股票")
        print("  2. 机器学习预测未来收益")
        print("  3. 投资组合优化分配权重")
        print("  4. 风险管理和绩效监控")
        
        # 数据准备
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX', 'CRM', 'ADBE']
        print(f"\n📊 股票池: {', '.join(symbols)}")
        
        # 这里可以整合前面三个示例的逻辑
        # 为了简化演示，我们展示策略框架
        
        print("\n🔍 第一步: 技术分析筛选")
        print("  • 使用RSI、MACD、布林带等指标")
        print("  • 筛选出技术面向好的股票")
        print("  • 剔除技术面恶化的股票")
        
        # 模拟筛选结果
        selected_symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN']
        print(f"  ✓ 筛选结果: {', '.join(selected_symbols)}")
        
        print("\n🤖 第二步: 机器学习预测")
        print("  • 对筛选后的股票进行收益预测")
        print("  • 使用随机森林等集成学习算法")
        print("  • 生成未来5-10日的收益预测")
        
        # 模拟预测结果
        predictions = {
            'AAPL': 0.025,   # 预测2.5%收益
            'MSFT': 0.018,   # 预测1.8%收益
            'NVDA': 0.035,   # 预测3.5%收益
            'GOOGL': 0.012,  # 预测1.2%收益
            'AMZN': 0.008    # 预测0.8%收益
        }
        
        print("  ✓ 预测结果:")
        for symbol, pred_return in predictions.items():
            print(f"    {symbol}: {pred_return:.1%}")
        
        print("\n📊 第三步: 投资组合优化")
        print("  • 基于预测收益优化权重分配")
        print("  • 考虑风险约束和行业分散")
        print("  • 最大化风险调整后收益")
        
        # 模拟优化结果（基于预测收益的权重调整）
        total_pred = sum(predictions.values())
        optimized_weights = {
            symbol: max(0.1, min(0.3, pred / total_pred)) 
            for symbol, pred in predictions.items()
        }
        
        # 归一化权重
        total_weight = sum(optimized_weights.values())
        optimized_weights = {k: v/total_weight for k, v in optimized_weights.items()}
        
        print("  ✓ 优化权重:")
        for symbol, weight in optimized_weights.items():
            print(f"    {symbol}: {weight:.1%}")
        
        print("\n⚠️ 第四步: 风险管理")
        print("  • 设置止损位: -5%")
        print("  • 设置止盈位: +15%")
        print("  • 最大单只股票权重: 30%")
        print("  • 投资组合最大回撤: 10%")
        
        # 模拟风险检查
        max_weight = max(optimized_weights.values())
        if max_weight > 0.30:
            print("  ⚠️ 警告: 单只股票权重过高")
        else:
            print("  ✓ 权重分散度检查通过")
        
        print("\n📈 第五步: 执行和监控")
        print("  • 生成交易订单")
        print("  • 实时监控持仓")
        print("  • 动态调整权重")
        print("  • 定期再平衡")
        
        # 模拟组合表现
        portfolio_expected_return = sum(predictions[s] * optimized_weights[s] for s in selected_symbols)
        portfolio_risk = 0.12  # 假设的组合风险
        sharpe_ratio = (portfolio_expected_return - 0.02) / portfolio_risk
        
        print(f"\n🎯 策略预期表现:")
        print(f"  预期收益: {portfolio_expected_return:.2%}")
        print(f"  预期风险: {portfolio_risk:.1%}")
        print(f"  夏普比率: {sharpe_ratio:.2f}")
        
        if sharpe_ratio > 1.0:
            print("  🟢 策略表现优秀，建议执行")
        elif sharpe_ratio > 0.5:
            print("  🔵 策略表现良好，可以考虑执行")
        else:
            print("  🟡 策略表现一般，建议优化后再执行")
        
        print("\n📋 下一步行动计划:")
        print("  1. 设置自动化交易系统")
        print("  2. 实施实时监控和报警")
        print("  3. 定期回测和策略优化")
        print("  4. 建立绩效归因分析框架")
        
        print("\n✅ 端到端量化交易策略设计完成！")
        return True
        
    except Exception as e:
        print(f"❌ 策略设计失败: {str(e)}")
        return False


# ============================================================================
# 主函数 - 运行所有示例
# ============================================================================

def main():
    """
    主函数：运行所有P1-2组件使用示例
    """
    print("🚀 P1-2高级量化交易组件 - 完整使用示例")
    print("🕒 开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*80)
    
    # 运行各个示例
    examples = [
        ("技术分析示例", example_1_technical_analysis),
        ("机器学习预测示例", example_2_ml_prediction),
        ("投资组合优化示例", example_3_portfolio_optimization),
        ("端到端策略示例", example_4_complete_strategy)
    ]
    
    results = []
    
    for example_name, example_func in examples:
        print(f"\n🎯 运行: {example_name}")
        try:
            success = example_func()
            results.append((example_name, success))
        except Exception as e:
            print(f"❌ {example_name}执行失败: {str(e)}")
            results.append((example_name, False))
    
    # 汇总结果
    print("\n" + "="*80)
    print("📊 示例执行结果汇总")
    print("="*80)
    
    successful_count = 0
    for example_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{example_name}: {status}")
        if success:
            successful_count += 1
    
    print(f"\n🎯 总体结果: {successful_count}/{len(examples)} 个示例执行成功")
    
    if successful_count == len(examples):
        print("🎉 恭喜！所有P1-2组件示例都运行成功！")
        print("\n📚 后续学习建议:")
        print("• 详细阅读 docs/P1-2_USER_MANUAL.md")
        print("• 参考 docs/API_REFERENCE.md 深入了解API")
        print("• 在实际项目中集成P1-2组件")
        print("• 根据需求定制和扩展功能")
        
    else:
        print("⚠️ 部分示例执行失败，请检查环境配置和依赖安装")
        print("\n🔧 故障排除建议:")
        print("• 确保所有依赖库已正确安装")
        print("• 检查Python路径配置")
        print("• 参考文档中的故障排除部分")
    
    print(f"\n🕒 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return successful_count == len(examples)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)