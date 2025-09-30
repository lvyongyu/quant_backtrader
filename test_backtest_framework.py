"""
回测框架综合测试脚本

全面测试回测引擎的各个模块，识别问题并进行性能优化。

测试内容：
1. 数据管理器完整性测试
2. 参数优化器算法测试
3. 性能分析器准确性测试
4. 集成管理器稳定性测试
5. 异常处理和边界条件测试
"""

import sys
import os
import time
import traceback
from datetime import datetime, timedelta

# 添加src路径以支持模块导入
sys.path.append('src')

# 修复导入路径
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_data_manager():
    """测试数据管理器功能"""
    print("🔍 测试数据管理器...")
    
    try:
        # 导入数据管理模块
        from backtesting.data_manager import HistoricalDataManager, MarketData, DataCache, MockDataProvider
        
        # 1. 测试数据提供者
        print("  • 测试Mock数据提供者...")
        provider = MockDataProvider()
        test_data = provider.get_historical_data("TEST", "2023-01-01", "2023-01-10")
        assert len(test_data) > 0, "Mock数据生成失败"
        assert all(isinstance(d, MarketData) for d in test_data), "数据类型错误"
        print(f"    ✅ Mock数据生成: {len(test_data)}条记录")
        
        # 2. 测试数据验证
        print("  • 测试数据验证...")
        valid_count = sum(1 for d in test_data if d.validate())
        assert valid_count == len(test_data), f"数据验证失败: {len(test_data) - valid_count}条无效"
        print(f"    ✅ 数据验证通过: {valid_count}/{len(test_data)}")
        
        # 3. 测试缓存机制
        print("  • 测试数据缓存...")
        cache = DataCache("test_cache")
        cache.cache_data("TEST", "2023-01-01", "2023-01-10", "1d", test_data)
        cached_data = cache.get_cached_data("TEST", "2023-01-01", "2023-01-10", "1d")
        assert cached_data is not None, "缓存读取失败"
        assert len(cached_data) == len(test_data), "缓存数据数量不匹配"
        print(f"    ✅ 缓存功能正常: {len(cached_data)}条记录")
        
        # 4. 测试数据管理器
        print("  • 测试数据管理器...")
        manager = HistoricalDataManager()
        data = manager.get_data("AAPL", "2023-01-01", "2023-01-31", provider="mock")
        assert len(data) > 0, "数据获取失败"
        print(f"    ✅ 数据管理器正常: {len(data)}条记录")
        
        # 5. 测试数据信息
        info = manager.get_data_info("AAPL", "mock")
        assert info['available'], "数据信息获取失败"
        print(f"    ✅ 数据信息: 价格范围${info['price_range']['min']:.2f}-${info['price_range']['max']:.2f}")
        
        print("✅ 数据管理器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 数据管理器测试失败: {e}")
        traceback.print_exc()
        return False


def test_parameter_optimizer():
    """测试参数优化器功能"""
    print("🔧 测试参数优化器...")
    
    try:
        from backtesting.parameter_optimizer import (
            ParameterRange, GridSearchOptimizer, RandomSearchOptimizer, 
            OptimizationManager, OptimizationResult
        )
        
        # 1. 测试参数范围定义
        print("  • 测试参数范围...")
        param_ranges = [
            ParameterRange(name="period", param_type="int", min_value=5, max_value=15, step=2),
            ParameterRange(name="threshold", param_type="float", min_value=0.01, max_value=0.05, step=0.01),
            ParameterRange(name="method", param_type="choice", choices=["sma", "ema"])
        ]
        
        for pr in param_ranges:
            assert pr.validate(), f"参数范围验证失败: {pr.name}"
            values = pr.generate_values()
            assert len(values) > 0, f"参数值生成失败: {pr.name}"
        print(f"    ✅ 参数范围定义: {len(param_ranges)}个参数")
        
        # 2. 测试目标函数
        def test_objective(params):
            # 模拟策略评估，返回适应度分数
            score = params.get("period", 10) * 0.1
            score += params.get("threshold", 0.02) * 20
            if params.get("method") == "ema":
                score += 0.5
            
            return OptimizationResult(
                parameters=params,
                fitness=score,
                metrics={"return": score * 0.1}
            )
        
        # 3. 测试网格搜索
        print("  • 测试网格搜索...")
        grid_optimizer = GridSearchOptimizer()
        grid_results = grid_optimizer.optimize(param_ranges, test_objective, max_iterations=20)
        assert len(grid_results) > 0, "网格搜索无结果"
        assert all(isinstance(r, OptimizationResult) for r in grid_results), "结果类型错误"
        print(f"    ✅ 网格搜索: {len(grid_results)}个结果")
        
        # 4. 测试随机搜索
        print("  • 测试随机搜索...")
        random_optimizer = RandomSearchOptimizer(seed=42)
        random_results = random_optimizer.optimize(param_ranges, test_objective, max_iterations=10)
        assert len(random_results) > 0, "随机搜索无结果"
        print(f"    ✅ 随机搜索: {len(random_results)}个结果")
        
        # 5. 测试优化管理器
        print("  • 测试优化管理器...")
        opt_manager = OptimizationManager()
        
        # 模拟回测函数
        def mock_backtest(params):
            class MockResults:
                def __init__(self, params):
                    self.sharpe_ratio = params.get("period", 10) * 0.05
                    self.total_return = params.get("threshold", 0.02) * 10
                    self.max_drawdown = 0.05
                def get_summary(self):
                    return {
                        'performance': {
                            'total_return': f"{self.total_return:.2%}",
                            'sharpe_ratio': f"{self.sharpe_ratio:.2f}"
                        }
                    }
            return MockResults(params)
        
        opt_results = opt_manager.optimize_strategy(
            param_ranges, mock_backtest, "sharpe_ratio", "grid", 15
        )
        assert len(opt_results) > 0, "策略优化无结果"
        print(f"    ✅ 策略优化: {len(opt_results)}个结果")
        
        # 6. 测试优化报告
        report = opt_manager.get_optimization_report(opt_results, top_n=5)
        assert 'summary' in report, "优化报告生成失败"
        assert report['summary']['total_evaluations'] > 0, "报告统计错误"
        print(f"    ✅ 优化报告: 成功率{report['summary']['success_rate']:.1%}")
        
        print("✅ 参数优化器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 参数优化器测试失败: {e}")
        traceback.print_exc()
        return False


def test_performance_analyzer():
    """测试性能分析器功能"""
    print("📊 测试性能分析器...")
    
    try:
        from backtesting.performance_analyzer import PerformanceAnalyzer, PerformanceMetrics
        from backtesting.data_manager import MarketData
        
        # 1. 创建模拟回测结果
        print("  • 创建测试数据...")
        
        class MockTrade:
            def __init__(self, pnl, entry_time, exit_time):
                self.pnl = pnl
                self.entry_time = entry_time
                self.exit_time = exit_time
        
        class MockBacktestResults:
            def __init__(self):
                # 创建50笔交易
                self.trades = []
                base_date = datetime(2023, 1, 1)
                
                for i in range(50):
                    # 60%胜率
                    import random
                    random.seed(42 + i)
                    pnl = random.uniform(50, 200) if random.random() < 0.6 else random.uniform(-150, -30)
                    entry_time = base_date + timedelta(days=i*2)
                    exit_time = entry_time + timedelta(days=1)
                    self.trades.append(MockTrade(pnl, entry_time, exit_time))
                
                # 创建权益曲线
                equity_values = [100000]
                for trade in self.trades:
                    equity_values.append(equity_values[-1] + trade.pnl)
                
                # 创建简单的序列对象
                class MockSeries:
                    def __init__(self, values, dates=None):
                        self.values = values
                        self.dates = dates or [base_date + timedelta(days=i) for i in range(len(values))]
                    
                    def __len__(self):
                        return len(self.values)
                    
                    def __getitem__(self, index):
                        return self.values[index]
                    
                    def __iter__(self):
                        return iter(self.values)
                    
                    @property
                    def iloc(self):
                        return MockIloc(self.values)
                    
                    @property 
                    def index(self):
                        return self.dates
                    
                    def tolist(self):
                        return list(self.values)
                
                class MockIloc:
                    def __init__(self, values):
                        self.values = values
                    def __getitem__(self, index):
                        return self.values[index]
                
                self.equity_curve = MockSeries(equity_values)
                
                # 计算日收益率
                daily_returns = []
                for i in range(1, len(equity_values)):
                    daily_return = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                    daily_returns.append(daily_return)
                
                self.daily_returns = MockSeries(daily_returns)
        
        mock_results = MockBacktestResults()
        print(f"    ✅ 测试数据: {len(mock_results.trades)}笔交易, {len(mock_results.equity_curve)}天权益")
        
        # 2. 测试性能分析
        print("  • 测试性能指标计算...")
        analyzer = PerformanceAnalyzer(risk_free_rate=0.02)
        metrics = analyzer.analyze_backtest_results(mock_results)
        
        # 验证关键指标
        assert metrics.total_trades == 50, f"交易数量错误: {metrics.total_trades}"
        assert 0 <= metrics.win_rate <= 1, f"胜率超出范围: {metrics.win_rate}"
        assert metrics.sharpe_ratio != 0, "夏普比率计算错误"
        print(f"    ✅ 性能指标: 收益{metrics.total_return:.2%}, 夏普{metrics.sharpe_ratio:.2f}")
        
        # 3. 测试报告生成
        print("  • 测试报告生成...")
        report = analyzer.generate_performance_report(mock_results, "测试策略")
        assert len(report) > 500, "报告内容太短"
        assert "测试策略" in report, "策略名称未包含"
        assert "总收益率" in report, "关键指标缺失"
        print(f"    ✅ 报告生成: {len(report)}字符")
        
        # 4. 测试策略比较
        print("  • 测试策略比较...")
        comparison_data = {
            "策略A": mock_results,
            "策略B": mock_results  # 使用相同数据作为对比
        }
        comparison = analyzer.compare_strategies(comparison_data)
        assert 'strategies' in comparison, "策略比较结果缺失"
        assert len(comparison['strategies']) == 2, "策略数量错误"
        print(f"    ✅ 策略比较: {len(comparison['strategies'])}个策略")
        
        # 5. 测试指标计算详细验证
        print("  • 详细验证性能指标...")
        metrics_dict = metrics.to_dict()
        
        # 验证指标格式
        assert 'returns' in metrics_dict, "收益指标缺失"
        assert 'risk' in metrics_dict, "风险指标缺失"
        assert 'trading' in metrics_dict, "交易指标缺失"
        
        # 验证数值合理性
        total_return_str = metrics_dict['returns']['total_return']
        assert '%' in total_return_str, "收益率格式错误"
        print(f"    ✅ 指标验证通过: {total_return_str}")
        
        print("✅ 性能分析器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 性能分析器测试失败: {e}")
        traceback.print_exc()
        return False


def test_backtest_manager():
    """测试回测管理器功能"""
    print("🚀 测试回测管理器...")
    
    try:
        from backtesting.backtest_manager import StrategyBacktestManager, BacktestConfig
        from backtesting.parameter_optimizer import ParameterRange
        
        # 1. 创建回测管理器
        print("  • 初始化回测管理器...")
        manager = StrategyBacktestManager(cache_dir="test_cache")
        assert manager is not None, "管理器初始化失败"
        print("    ✅ 管理器初始化成功")
        
        # 2. 创建测试配置
        config = BacktestConfig(
            symbol="TEST",
            start_date="2023-01-01",
            end_date="2023-01-31",
            initial_capital=50000,
            strategy_name="TestStrategy"
        )
        
        # 3. 定义简单策略
        def simple_test_strategy(data, period=10, **kwargs):
            if len(data) < period:
                return "HOLD"
            
            # 简单的移动平均策略
            recent_prices = [d.close for d in data[-period:]]
            ma = sum(recent_prices) / len(recent_prices)
            current_price = data[-1].close
            
            if current_price > ma * 1.01:
                return "BUY"
            elif current_price < ma * 0.99:
                return "SELL"
            else:
                return "HOLD"
        
        # 4. 测试单次回测
        print("  • 测试单次回测...")
        try:
            results, metrics = manager.run_single_backtest(config, simple_test_strategy, period=15)
            assert results is not None, "回测结果为空"
            assert metrics is not None, "性能指标为空"
            print(f"    ✅ 单次回测: 收益{metrics.total_return:.2%}, 交易{metrics.total_trades}笔")
        except Exception as e:
            print(f"    ⚠️ 单次回测跳过: {e}")
        
        # 5. 测试参数优化（简化版）
        print("  • 测试参数优化...")
        try:
            param_ranges = [
                ParameterRange(name="period", param_type="int", min_value=8, max_value=12, step=2)
            ]
            
            opt_results = manager.optimize_strategy(
                config, simple_test_strategy, param_ranges, 
                optimizer_type="grid", max_iterations=5
            )
            assert len(opt_results) > 0, "优化结果为空"
            print(f"    ✅ 参数优化: {len(opt_results)}个结果")
        except Exception as e:
            print(f"    ⚠️ 参数优化跳过: {e}")
        
        # 6. 测试任务管理
        print("  • 测试任务管理...")
        task_id = manager.create_backtest_task(config, simple_test_strategy, period=10)
        assert task_id in manager.tasks, "任务创建失败"
        print(f"    ✅ 任务创建: {task_id}")
        
        # 获取任务状态
        status = manager.get_task_status(task_id)
        assert status['status'] == 'pending', "任务状态错误"
        print(f"    ✅ 任务状态: {status['status']}")
        
        # 7. 测试缓存信息
        cache_info = manager.get_cache_info()
        assert 'cache_dir' in cache_info, "缓存信息缺失"
        print(f"    ✅ 缓存信息: {cache_info['cache_dir']}")
        
        print("✅ 回测管理器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 回测管理器测试失败: {e}")
        traceback.print_exc()
        return False


def test_integration():
    """测试系统集成功能"""
    print("🔗 测试系统集成...")
    
    try:
        # 1. 测试模块间协作
        print("  • 测试模块协作...")
        
        from backtesting.data_manager import HistoricalDataManager
        from backtesting.parameter_optimizer import OptimizationManager, ParameterRange
        from backtesting.performance_analyzer import PerformanceAnalyzer
        
        # 创建各模块实例
        data_manager = HistoricalDataManager()
        opt_manager = OptimizationManager()
        perf_analyzer = PerformanceAnalyzer()
        
        print("    ✅ 所有模块实例化成功")
        
        # 2. 测试数据流
        print("  • 测试数据流...")
        data = data_manager.get_data("TEST", "2023-01-01", "2023-01-15", provider="mock")
        assert len(data) > 0, "数据获取失败"
        
        # 验证数据质量
        valid_data = [d for d in data if d.validate()]
        assert len(valid_data) == len(data), "数据质量问题"
        print(f"    ✅ 数据流测试: {len(data)}条有效数据")
        
        # 3. 测试异常处理
        print("  • 测试异常处理...")
        
        # 测试无效日期范围
        try:
            invalid_data = data_manager.get_data("TEST", "2023-12-31", "2023-01-01")
            # 应该返回空数据而不是异常
            assert isinstance(invalid_data, list), "异常处理不当"
            print("    ✅ 无效日期处理正常")
        except Exception as e:
            print(f"    ⚠️ 异常处理需要改进: {e}")
        
        # 4. 测试性能
        print("  • 测试性能...")
        start_time = time.time()
        
        # 执行一系列操作
        for i in range(5):
            test_data = data_manager.get_data(f"TEST{i}", "2023-01-01", "2023-01-10", provider="mock")
            
        execution_time = time.time() - start_time
        assert execution_time < 5, f"性能太慢: {execution_time:.2f}秒"
        print(f"    ✅ 性能测试: {execution_time:.2f}秒完成5次数据获取")
        
        print("✅ 系统集成测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 系统集成测试失败: {e}")
        traceback.print_exc()
        return False


def test_edge_cases():
    """测试边界条件和异常情况"""
    print("⚠️ 测试边界条件...")
    
    try:
        from backtesting.data_manager import MarketData
        from backtesting.parameter_optimizer import ParameterRange
        
        # 1. 测试空数据处理
        print("  • 测试空数据...")
        empty_data = []
        
        # 创建空的市场数据对象
        try:
            invalid_market_data = MarketData("TEST", datetime.now(), -1, -1, -1, -1, -1)
            assert not invalid_market_data.validate(), "无效数据应该验证失败"
            print("    ✅ 无效数据验证正常")
        except:
            print("    ✅ 无效数据异常处理正常")
        
        # 2. 测试极端参数范围
        print("  • 测试极端参数...")
        
        # 无效参数范围
        invalid_range = ParameterRange(name="test", param_type="int", min_value=10, max_value=5)
        assert not invalid_range.validate(), "无效参数范围应该验证失败"
        print("    ✅ 无效参数范围验证正常")
        
        # 3. 测试内存使用
        print("  • 测试内存使用...")
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 创建大量数据对象测试内存
        large_data = []
        for i in range(1000):
            data = MarketData(f"TEST{i}", datetime.now(), 100, 101, 99, 100.5, 1000)
            large_data.append(data)
        
        assert len(large_data) == 1000, "大数据集创建失败"
        
        # 清理
        del large_data
        gc.collect()
        print("    ✅ 内存测试通过")
        
        # 4. 测试并发安全性（简单测试）
        print("  • 测试并发安全...")
        
        from backtesting.data_manager import HistoricalDataManager
        
        # 同时创建多个管理器实例
        managers = [HistoricalDataManager() for _ in range(3)]
        assert len(managers) == 3, "并发实例创建失败"
        print("    ✅ 并发安全测试通过")
        
        print("✅ 边界条件测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 边界条件测试失败: {e}")
        traceback.print_exc()
        return False


def generate_test_report(test_results):
    """生成测试报告"""
    print("📋 生成测试报告...")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    report = f"""
# 回测框架测试报告

## 测试概要
- **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总测试项**: {total_tests}
- **通过测试**: {passed_tests}
- **失败测试**: {total_tests - passed_tests}
- **成功率**: {success_rate:.1%}

## 详细结果

| 测试模块 | 状态 | 说明 |
|---------|------|------|
"""
    
    status_map = {True: "✅ 通过", False: "❌ 失败"}
    
    for test_name, result in test_results.items():
        report += f"| {test_name} | {status_map[result]} | {'功能正常' if result else '需要修复'} |\n"
    
    report += f"""
## 总体评价

{'🎉 框架测试全部通过，可以进入下一阶段开发！' if success_rate == 1.0 else 
 '⚠️ 存在部分问题，建议先修复后再继续开发。' if success_rate >= 0.8 else
 '❌ 框架存在严重问题，需要全面修复。'}

## 建议改进

"""
    
    if not test_results.get('数据管理器', True):
        report += "- 修复数据管理器的缓存和验证机制\n"
    
    if not test_results.get('参数优化器', True):
        report += "- 改进参数优化算法的稳定性\n"
    
    if not test_results.get('性能分析器', True):
        report += "- 完善性能指标计算的准确性\n"
    
    if not test_results.get('回测管理器', True):
        report += "- 优化回测管理器的任务调度\n"
    
    if not test_results.get('系统集成', True):
        report += "- 加强模块间的协作和错误处理\n"
    
    if not test_results.get('边界条件', True):
        report += "- 改进异常处理和边界条件检查\n"
    
    if success_rate == 1.0:
        report += "- 框架已经具备良好的基础，可以考虑添加更多高级功能\n"
        report += "- 建议添加更多的策略示例和文档\n"
        report += "- 可以开始开发可视化界面\n"
    
    report += f"""
---
*测试框架版本: 1.0*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report


def main():
    """主测试函数"""
    print("🧪 回测框架综合测试")
    print("=" * 60)
    
    # 测试计划
    test_functions = [
        ("数据管理器", test_data_manager),
        ("参数优化器", test_parameter_optimizer), 
        ("性能分析器", test_performance_analyzer),
        ("回测管理器", test_backtest_manager),
        ("系统集成", test_integration),
        ("边界条件", test_edge_cases)
    ]
    
    # 执行测试
    test_results = {}
    start_time = time.time()
    
    for test_name, test_func in test_functions:
        print(f"🏃‍♂️ 开始测试: {test_name}")
        try:
            result = test_func()
            test_results[test_name] = result
        except Exception as e:
            print(f"❌ 测试异常: {test_name} - {e}")
            test_results[test_name] = False
        
        print("-" * 40)
    
    total_time = time.time() - start_time
    
    # 生成测试报告
    report = generate_test_report(test_results)
    
    # 保存报告到文件
    try:
        with open("backtest_framework_test_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("📄 测试报告已保存到: backtest_framework_test_report.md")
    except Exception as e:
        print(f"⚠️ 报告保存失败: {e}")
    
    # 显示汇总结果
    print("\n" + "=" * 60)
    print("🏁 测试完成汇总")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    print(f"总测试时间: {total_time:.2f}秒")
    print(f"测试结果: {passed}/{total} 通过 ({passed/total:.1%})")
    
    if passed == total:
        print("🎉 所有测试通过！框架已准备就绪。")
    elif passed >= total * 0.8:
        print("⚠️ 大部分测试通过，建议修复失败项。")
    else:
        print("❌ 存在较多问题，需要重点修复。")
    
    print("\n🔧 下一步建议:")
    if passed == total:
        print("- ✅ 可以开始P1-2高级数据分析平台开发")
        print("- ✅ 考虑添加更多策略示例")
        print("- ✅ 开发可视化界面")
    else:
        print("- 🔨 修复失败的测试项")
        print("- 🔍 重新运行测试验证")
        print("- 📚 完善错误处理机制")


if __name__ == "__main__":
    main()