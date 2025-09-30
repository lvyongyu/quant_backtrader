"""
框架最终验证测试

综合验证P1-1智能策略优化引擎的所有功能，
确保框架完全准备就绪。
"""

import sys
import os
from datetime import datetime, timedelta

# 添加src路径
sys.path.append('src')

def test_complete_workflow():
    """测试完整工作流程"""
    print("🔄 完整工作流程测试")
    print("=" * 50)
    
    try:
        # 1. 导入所有模块
        print("📦 导入模块...")
        from backtesting import BacktestEngine, HistoricalDataManager, ParameterOptimizer
        from backtesting import PerformanceAnalyzer, StrategyBacktestManager
        from strategies.advanced_strategies import create_strategy, create_multi_factor_strategy
        from utils.enhanced_utils import TechnicalIndicators, RiskManager, ConfigManager
        
        print("    ✅ 所有模块导入成功")
        
        # 2. 初始化组件
        print("⚙️ 初始化组件...")
        data_manager = HistoricalDataManager()
        backtest_engine = BacktestEngine()
        optimizer = ParameterOptimizer()
        analyzer = PerformanceAnalyzer()
        
        # 增强工具
        risk_manager = RiskManager()
        config_manager = ConfigManager()
        
        print("    ✅ 核心组件初始化成功")
        
        # 3. 创建策略
        print("🎯 创建高级策略...")
        bollinger_strategy = create_strategy("bollinger", period=20, std_dev=2.0)
        rsi_strategy = create_strategy("rsi", period=14)
        
        multi_strategy = create_multi_factor_strategy(
            {"type": "bollinger", "period": 20, "std_dev": 2.0, "weight": 0.6},
            {"type": "rsi", "period": 14, "weight": 0.4}
        )
        
        print(f"    ✅ 策略创建成功: {bollinger_strategy.name}, {rsi_strategy.name}, {multi_strategy.name}")
        
        # 4. 获取数据
        print("📊 获取测试数据...")
        test_data = data_manager.get_data("TEST", 
                                         datetime.now() - timedelta(days=30),
                                         datetime.now())
        print(f"    ✅ 数据获取成功: {len(test_data)}条记录")
        
        # 5. 技术指标计算
        print("📈 计算技术指标...")
        prices = [d.close for d in test_data]
        
        sma = TechnicalIndicators.sma(prices, 10)
        rsi = TechnicalIndicators.rsi(prices, 14)
        bb = TechnicalIndicators.bollinger_bands(prices, 20)
        
        print(f"    ✅ 技术指标: SMA={sma:.2f}, RSI={rsi:.2f}")
        print(f"    ✅ 布林带: 上轨={bb['upper']:.2f}, 下轨={bb['lower']:.2f}")
        
        # 6. 风险管理
        print("⚠️ 风险管理测试...")
        position_size = risk_manager.calculate_position_size(0.8, 100000, 100)
        is_valid_position = risk_manager.check_position_size("TEST", 10000, 100000)
        
        print(f"    ✅ 建议仓位: {position_size}股")
        print(f"    ✅ 仓位检查: {'通过' if is_valid_position else '未通过'}")
        
        # 7. 策略回测
        print("🔬 运行策略回测...")
        from strategies.mean_reversion_simple import SimpleMeanReversionStrategy
        
        # 使用内置策略进行回测
        strategy = SimpleMeanReversionStrategy()
        results = backtest_engine.run_backtest(
            strategy=strategy,
            data=test_data,
            initial_capital=100000
        )
        
        print(f"    ✅ 回测完成: 收益率{results.total_return:.2%}")
        print(f"    ✅ 夏普比率: {results.sharpe_ratio:.2f}")
        print(f"    ✅ 最大回撤: {results.max_drawdown:.2%}")
        
        # 8. 性能分析
        print("📊 性能分析...")
        metrics = analyzer.calculate_metrics(results)
        
        print(f"    ✅ 总交易次数: {metrics.total_trades}")
        print(f"    ✅ 胜率: {metrics.win_rate:.2%}")
        print(f"    ✅ 盈亏比: {metrics.avg_win/abs(metrics.avg_loss) if metrics.avg_loss < 0 else 0:.2f}")
        
        # 9. 参数优化
        print("⚡ 参数优化...")
        from backtesting.parameter_optimizer import ParameterRange
        
        param_ranges = [
            ParameterRange("period", "int", 10, 30, 5),
            ParameterRange("threshold", "float", 0.01, 0.05, 0.01)
        ]
        
        optimization_results = optimizer.optimize(
            strategy_class=SimpleMeanReversionStrategy,
            data=test_data,
            parameter_ranges=param_ranges,
            algorithm="grid",
            max_combinations=5
        )
        
        print(f"    ✅ 优化完成: {len(optimization_results.results)}个结果")
        print(f"    ✅ 最优参数: {optimization_results.best_result.parameters}")
        
        # 10. 配置管理
        print("⚙️ 配置管理...")
        initial_capital = config_manager.get("backtest.initial_capital", 100000)
        commission = config_manager.get("backtest.commission", 0.001)
        
        print(f"    ✅ 初始资金: ${initial_capital:,}")
        print(f"    ✅ 手续费率: {commission:.3%}")
        
        print("\n" + "=" * 50)
        print("🎉 完整工作流程测试成功！")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_advanced_strategies():
    """测试高级策略"""
    print("\n🎯 高级策略功能测试")
    print("=" * 50)
    
    try:
        from strategies.advanced_strategies import create_strategy, create_multi_factor_strategy
        from backtesting.data_manager import MockDataProvider
        
        # 生成测试数据
        mock_provider = MockDataProvider()
        test_data = mock_provider.get_data("TEST", datetime.now() - timedelta(days=30), datetime.now())
        
        strategies_to_test = [
            ("Bollinger", create_strategy("bollinger", period=20, std_dev=2.0)),
            ("RSI", create_strategy("rsi", period=14, oversold=30, overbought=70)),
            ("MACD", create_strategy("macd", fast_period=12, slow_period=26)),
            ("Momentum", create_strategy("momentum", lookback_period=20, momentum_threshold=0.02))
        ]
        
        signal_results = []
        
        for name, strategy in strategies_to_test:
            signal = strategy.generate_signal(test_data)
            signal_results.append((name, signal))
            
            print(f"  📊 {name}策略:")
            print(f"      信号: {signal.signal_type}")
            print(f"      强度: {signal.strength:.2f}")
            print(f"      置信度: {signal.confidence:.2f}")
        
        # 测试多因子策略
        print("\n  🔧 多因子策略测试:")
        multi_strategy = create_multi_factor_strategy(
            {"type": "bollinger", "period": 20, "weight": 0.3},
            {"type": "rsi", "period": 14, "weight": 0.3},
            {"type": "momentum", "lookback_period": 20, "weight": 0.4}
        )
        
        multi_signal = multi_strategy.generate_signal(test_data)
        print(f"      综合信号: {multi_signal.signal_type}")
        print(f"      综合强度: {multi_signal.strength:.2f}")
        print(f"      综合置信度: {multi_signal.confidence:.2f}")
        
        print("\n✅ 高级策略测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 高级策略测试失败: {e}")
        return False


def test_enhanced_utils():
    """测试增强工具"""
    print("\n🛠️ 增强工具功能测试")
    print("=" * 50)
    
    try:
        from utils.enhanced_utils import TechnicalIndicators, RiskManager, DataValidator, ConfigManager
        
        # 技术指标测试
        test_prices = [100 + i + (i%3)*2 for i in range(20)]
        
        print("  📈 技术指标测试:")
        sma = TechnicalIndicators.sma(test_prices, 10)
        ema = TechnicalIndicators.ema(test_prices, 10)
        rsi = TechnicalIndicators.rsi(test_prices, 14)
        bb = TechnicalIndicators.bollinger_bands(test_prices, 10)
        macd = TechnicalIndicators.macd(test_prices, 12, 26)
        
        print(f"      SMA(10): {sma:.2f}")
        print(f"      EMA(10): {ema:.2f}")
        print(f"      RSI(14): {rsi:.2f}")
        print(f"      布林带范围: {bb['lower']:.2f} - {bb['upper']:.2f}")
        print(f"      MACD: {macd['macd']:.2f}")
        
        # 风险管理测试
        print("\n  ⚠️ 风险管理测试:")
        risk_mgr = RiskManager(max_position_size=0.1, max_daily_loss=0.02)
        
        position_size = risk_mgr.calculate_position_size(0.8, 100000, 100, 0.01)
        is_valid_size = risk_mgr.check_position_size("TEST", 8000, 100000)
        is_valid_loss = risk_mgr.check_daily_loss(-1500, 100000)
        
        print(f"      建议仓位: {position_size}股")
        print(f"      仓位检查: {'✅' if is_valid_size else '❌'}")
        print(f"      损失检查: {'✅' if is_valid_loss else '❌'}")
        
        # 数据验证测试
        print("\n  🔍 数据验证测试:")
        from collections import namedtuple
        PriceData = namedtuple('PriceData', ['open', 'high', 'low', 'close'])
        
        valid_data = PriceData(100, 105, 98, 103)
        invalid_data = PriceData(100, 95, 98, 103)  # high < close
        
        valid_check = DataValidator.validate_price_data(valid_data)
        invalid_check = DataValidator.validate_price_data(invalid_data)
        
        print(f"      有效数据验证: {'✅' if valid_check else '❌'}")
        print(f"      无效数据验证: {'✅' if not invalid_check else '❌'}")
        
        # 异常值检测
        outlier_prices = test_prices + [1000]  # 添加异常值
        outliers = DataValidator.detect_outliers(outlier_prices, threshold=2.0)
        print(f"      异常值检测: 发现{len(outliers)}个异常值")
        
        # 配置管理测试
        print("\n  ⚙️ 配置管理测试:")
        config_mgr = ConfigManager("test_config.json")
        
        # 设置和获取配置
        config_mgr.set("test.value", 12345)
        test_value = config_mgr.get("test.value", 0)
        default_capital = config_mgr.get("backtest.initial_capital", 100000)
        
        print(f"      配置设置: {test_value}")
        print(f"      默认资金: ${default_capital:,}")
        
        # 清理测试文件
        try:
            os.remove("test_config.json")
        except:
            pass
        
        print("\n✅ 增强工具测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 增强工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🔬 P1-1框架最终验证测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 执行所有测试
    tests = [
        ("完整工作流程", test_complete_workflow),
        ("高级策略功能", test_advanced_strategies),
        ("增强工具功能", test_enhanced_utils)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🏃‍♂️ 执行测试: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 通过" if result else "❌ 失败"
            print(f"测试结果: {status}")
        except Exception as e:
            print(f"测试异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 最终验证结果")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 框架验证完全成功！")
        print("🚀 P1-1智能策略优化引擎已完全准备就绪")
        print("📈 可以开始P1-2高级数据分析平台开发")
    else:
        print("\n⚠️ 部分测试未通过，需要进一步检查")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()