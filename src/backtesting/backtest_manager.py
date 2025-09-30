"""
策略回测集成模块

整合回测引擎、数据管理、参数优化、性能分析等模块，
提供统一的接口进行策略回测和优化。

核心功能：
1. 完整的回测流程管理
2. 策略参数优化
3. 多策略批量回测
4. 结果分析和报告
5. 回测任务调度
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
import json

# 导入回测模块
from .data_manager import HistoricalDataManager, MarketData
from .parameter_optimizer import OptimizationManager, ParameterRange, OptimizationResult
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetrics

# 导入核心回测引擎（简化版本）
class SimpleBacktestEngine:
    """简化的回测引擎用于集成测试"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.logger = logging.getLogger("SimpleBacktestEngine")
    
    def run_backtest(self, strategy_func: Callable, data: List[MarketData], 
                    **strategy_params) -> 'SimpleBacktestResults':
        """运行简化回测"""
        try:
            # 模拟回测过程
            trades = []
            equity_curve = [self.initial_capital]
            daily_returns = []
            
            current_equity = self.initial_capital
            position = None
            
            for i, market_data in enumerate(data):
                # 生成交易信号
                signal = strategy_func(data[:i+1], **strategy_params)
                
                # 简单的交易逻辑
                if signal == "BUY" and position is None:
                    # 开仓
                    position = {
                        'entry_price': market_data.close,
                        'entry_date': market_data.date,
                        'shares': int(current_equity * 0.95 / market_data.close)  # 95%仓位
                    }
                
                elif signal == "SELL" and position is not None:
                    # 平仓
                    exit_value = position['shares'] * market_data.close
                    pnl = exit_value - (position['shares'] * position['entry_price'])
                    
                    # 创建交易记录
                    trade = type('Trade', (), {
                        'entry_time': position['entry_date'],
                        'exit_time': market_data.date,
                        'pnl': pnl,
                        'entry_price': position['entry_price'],
                        'exit_price': market_data.close
                    })()
                    trades.append(trade)
                    
                    current_equity += pnl
                    position = None
                
                # 更新权益曲线
                if position:
                    current_value = current_equity - (position['shares'] * position['entry_price']) + (position['shares'] * market_data.close)
                else:
                    current_value = current_equity
                
                equity_curve.append(current_value)
                
                # 计算日收益率
                if len(equity_curve) > 1:
                    daily_return = (equity_curve[-1] - equity_curve[-2]) / equity_curve[-2]
                    daily_returns.append(daily_return)
            
            # 如果最后还有持仓，强制平仓
            if position and data:
                final_value = position['shares'] * data[-1].close
                final_pnl = final_value - (position['shares'] * position['entry_price'])
                
                trade = type('Trade', (), {
                    'entry_time': position['entry_date'],
                    'exit_time': data[-1].date,
                    'pnl': final_pnl,
                    'entry_price': position['entry_price'],
                    'exit_price': data[-1].close
                })()
                trades.append(trade)
            
            # 创建回测结果
            return SimpleBacktestResults(
                trades=trades,
                equity_curve=equity_curve,
                daily_returns=daily_returns,
                final_equity=equity_curve[-1] if equity_curve else self.initial_capital
            )
        
        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            return SimpleBacktestResults()


class SimpleBacktestResults:
    """简化的回测结果"""
    
    def __init__(self, trades=None, equity_curve=None, daily_returns=None, final_equity=100000):
        self.trades = trades or []
        self.equity_curve = self._create_series(equity_curve or [100000])
        self.daily_returns = self._create_series(daily_returns or [])
        self.final_equity = final_equity
        
        # 计算基础指标
        self.total_return = (final_equity / 100000) - 1 if final_equity > 0 else 0
        self.total_trades = len(self.trades)
        
        if self.trades:
            winning_trades = [t for t in self.trades if t.pnl > 0]
            self.win_rate = len(winning_trades) / len(self.trades)
            self.avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            self.avg_loss = sum(t.pnl for t in self.trades if t.pnl < 0) / max(1, len(self.trades) - len(winning_trades))
            self.profit_factor = abs(self.avg_win / self.avg_loss) if self.avg_loss < 0 else 0
        else:
            self.win_rate = 0
            self.avg_win = 0
            self.avg_loss = 0
            self.profit_factor = 0
        
        # 计算夏普比率
        if daily_returns and len(daily_returns) > 1:
            mean_return = sum(daily_returns) / len(daily_returns)
            std_return = self._calculate_std(daily_returns)
            self.sharpe_ratio = (mean_return * 252) / (std_return * (252 ** 0.5)) if std_return > 0 else 0
        else:
            self.sharpe_ratio = 0
        
        # 计算最大回撤
        if equity_curve and len(equity_curve) > 1:
            peak = equity_curve[0]
            max_dd = 0
            for value in equity_curve:
                if value > peak:
                    peak = value
                else:
                    drawdown = (peak - value) / peak
                    max_dd = max(max_dd, drawdown)
            self.max_drawdown = max_dd
        else:
            self.max_drawdown = 0
    
    def _create_series(self, data):
        """创建简单的序列对象"""
        class SimpleSeries:
            def __init__(self, data):
                self.data = data
                self.index = list(range(len(data)))
            
            def __len__(self):
                return len(self.data)
            
            def __getitem__(self, index):
                return self.data[index]
            
            def __iter__(self):
                return iter(self.data)
            
            @property
            def iloc(self):
                class IlocWrapper:
                    def __init__(self, data):
                        self.data = data
                    def __getitem__(self, index):
                        return self.data[index]
                return IlocWrapper(self.data)
            
            def tolist(self):
                return list(self.data)
        
        return SimpleSeries(data)
    
    def _calculate_std(self, values):
        """计算标准差"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5


@dataclass
class BacktestConfig:
    """回测配置"""
    symbol: str = "AAPL"
    start_date: str = "2023-01-01"
    end_date: str = "2023-12-31"
    initial_capital: float = 100000
    data_provider: str = "mock"
    strategy_name: str = "SimpleStrategy"
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'data_provider': self.data_provider,
            'strategy_name': self.strategy_name
        }


@dataclass
class BacktestTask:
    """回测任务"""
    task_id: str
    config: BacktestConfig
    strategy_func: Callable
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: Optional[Any] = None
    error: Optional[str] = None


class StrategyBacktestManager:
    """
    策略回测管理器
    
    提供完整的策略回测解决方案，集成数据管理、
    回测执行、参数优化、性能分析等功能。
    """
    
    def __init__(self, cache_dir: str = "data/backtest_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 初始化各模块
        self.data_manager = HistoricalDataManager()
        self.optimization_manager = OptimizationManager()
        self.performance_analyzer = PerformanceAnalyzer()
        self.backtest_engine = SimpleBacktestEngine()
        
        # 任务管理
        self.tasks = {}
        self.task_counter = 0
        
        self.logger = logging.getLogger("StrategyBacktestManager")
        self.logger.info("策略回测管理器初始化完成")
    
    def run_single_backtest(self, config: BacktestConfig, strategy_func: Callable,
                           **strategy_params) -> Tuple[SimpleBacktestResults, PerformanceMetrics]:
        """
        运行单次策略回测
        
        Args:
            config: 回测配置
            strategy_func: 策略函数
            **strategy_params: 策略参数
        
        Returns:
            (回测结果, 性能指标)
        """
        self.logger.info(f"开始单次回测: {config.strategy_name}")
        
        try:
            # 获取历史数据
            data = self.data_manager.get_data(
                symbol=config.symbol,
                start_date=config.start_date,
                end_date=config.end_date,
                provider=config.data_provider
            )
            
            if not data:
                raise ValueError(f"无法获取数据: {config.symbol}")
            
            self.logger.info(f"数据获取成功: {len(data)}条记录")
            
            # 执行回测
            self.backtest_engine.initial_capital = config.initial_capital
            results = self.backtest_engine.run_backtest(strategy_func, data, **strategy_params)
            
            # 性能分析
            metrics = self.performance_analyzer.analyze_backtest_results(results)
            
            self.logger.info(f"回测完成: 收益率{metrics.total_return:.2%}, 夏普{metrics.sharpe_ratio:.2f}")
            
            return results, metrics
        
        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            raise
    
    def optimize_strategy(self, config: BacktestConfig, strategy_func: Callable,
                         parameter_ranges: List[ParameterRange],
                         optimizer_type: str = "grid",
                         max_iterations: int = 50) -> List[OptimizationResult]:
        """
        策略参数优化
        
        Args:
            config: 回测配置
            strategy_func: 策略函数
            parameter_ranges: 参数范围列表
            optimizer_type: 优化算法类型
            max_iterations: 最大迭代次数
        
        Returns:
            优化结果列表
        """
        self.logger.info(f"开始参数优化: {config.strategy_name}, 算法={optimizer_type}")
        
        # 获取数据
        data = self.data_manager.get_data(
            symbol=config.symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            provider=config.data_provider
        )
        
        if not data:
            raise ValueError(f"无法获取数据: {config.symbol}")
        
        # 定义回测函数
        def backtest_function(params: Dict[str, Any]):
            """用于优化的回测函数"""
            self.backtest_engine.initial_capital = config.initial_capital
            return self.backtest_engine.run_backtest(strategy_func, data, **params)
        
        # 执行优化
        results = self.optimization_manager.optimize_strategy(
            parameter_ranges=parameter_ranges,
            backtest_function=backtest_function,
            objective_metric="sharpe_ratio",
            optimizer_type=optimizer_type,
            max_iterations=max_iterations
        )
        
        self.logger.info(f"参数优化完成: {len(results)}个结果")
        
        # 缓存优化结果
        self._cache_optimization_results(config, results)
        
        return results
    
    def batch_backtest(self, configs: List[BacktestConfig], 
                      strategy_funcs: Dict[str, Callable]) -> Dict[str, Any]:
        """
        批量回测多个策略
        
        Args:
            configs: 回测配置列表
            strategy_funcs: 策略函数字典 {策略名: 函数}
        
        Returns:
            批量回测结果
        """
        self.logger.info(f"开始批量回测: {len(configs)}个配置")
        
        batch_results = {
            'individual_results': {},
            'comparison': {},
            'summary': {}
        }
        
        strategy_results = {}
        
        for config in configs:
            try:
                strategy_func = strategy_funcs.get(config.strategy_name)
                if not strategy_func:
                    self.logger.error(f"未找到策略函数: {config.strategy_name}")
                    continue
                
                # 执行回测
                results, metrics = self.run_single_backtest(config, strategy_func)
                
                # 存储结果
                result_key = f"{config.strategy_name}_{config.symbol}"
                batch_results['individual_results'][result_key] = {
                    'config': config.to_dict(),
                    'metrics': metrics.to_dict(),
                    'performance': {
                        'total_return': metrics.total_return,
                        'sharpe_ratio': metrics.sharpe_ratio,
                        'max_drawdown': metrics.max_drawdown,
                        'win_rate': metrics.win_rate
                    }
                }
                
                strategy_results[result_key] = results
            
            except Exception as e:
                self.logger.error(f"批量回测失败: {config.strategy_name}, {e}")
                continue
        
        # 策略比较分析
        if strategy_results:
            batch_results['comparison'] = self.performance_analyzer.compare_strategies(strategy_results)
        
        # 生成汇总
        batch_results['summary'] = self._generate_batch_summary(batch_results['individual_results'])
        
        self.logger.info(f"批量回测完成: {len(batch_results['individual_results'])}个成功")
        
        return batch_results
    
    def create_backtest_task(self, config: BacktestConfig, strategy_func: Callable,
                            **strategy_params) -> str:
        """
        创建异步回测任务
        
        Args:
            config: 回测配置
            strategy_func: 策略函数
            **strategy_params: 策略参数
        
        Returns:
            任务ID
        """
        self.task_counter += 1
        task_id = f"backtest_{self.task_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task = BacktestTask(
            task_id=task_id,
            config=config,
            strategy_func=strategy_func,
            strategy_params=strategy_params
        )
        
        self.tasks[task_id] = task
        self.logger.info(f"创建回测任务: {task_id}")
        
        return task_id
    
    def run_task(self, task_id: str) -> bool:
        """
        执行回测任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否执行成功
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        task.status = "running"
        task.start_time = datetime.now()
        
        try:
            # 执行回测
            results, metrics = self.run_single_backtest(
                task.config, 
                task.strategy_func,
                **task.strategy_params
            )
            
            task.results = {
                'backtest_results': results,
                'performance_metrics': metrics,
                'report': self.performance_analyzer.generate_performance_report(
                    results, task.config.strategy_name
                )
            }
            task.status = "completed"
            task.end_time = datetime.now()
            
            self.logger.info(f"任务执行成功: {task_id}")
            return True
        
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            task.end_time = datetime.now()
            
            self.logger.error(f"任务执行失败: {task_id}, {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return {"error": "任务不存在"}
        
        task = self.tasks[task_id]
        
        status_info = {
            'task_id': task.task_id,
            'status': task.status,
            'config': task.config.to_dict(),
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'duration': (task.end_time - task.start_time).total_seconds() if task.start_time and task.end_time else None
        }
        
        if task.status == "completed" and task.results:
            status_info['results_summary'] = {
                'total_return': task.results['performance_metrics'].total_return,
                'sharpe_ratio': task.results['performance_metrics'].sharpe_ratio,
                'max_drawdown': task.results['performance_metrics'].max_drawdown,
                'total_trades': task.results['performance_metrics'].total_trades
            }
        
        if task.error:
            status_info['error'] = task.error
        
        return status_info
    
    def _cache_optimization_results(self, config: BacktestConfig, results: List[OptimizationResult]):
        """缓存优化结果"""
        cache_file = os.path.join(
            self.cache_dir, 
            f"optimization_{config.strategy_name}_{config.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            cache_data = {
                'config': config.to_dict(),
                'optimization_time': datetime.now().isoformat(),
                'results_count': len(results),
                'top_results': [
                    {
                        'parameters': result.parameters,
                        'fitness': result.fitness,
                        'metrics': result.metrics
                    }
                    for result in results[:10]  # 保存前10个结果
                ]
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"优化结果已缓存: {cache_file}")
        
        except Exception as e:
            self.logger.error(f"缓存优化结果失败: {e}")
    
    def _generate_batch_summary(self, individual_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成批量回测汇总"""
        if not individual_results:
            return {}
        
        # 收集所有性能指标
        all_returns = []
        all_sharpe = []
        all_drawdowns = []
        all_win_rates = []
        
        for result in individual_results.values():
            perf = result['performance']
            all_returns.append(perf['total_return'])
            all_sharpe.append(perf['sharpe_ratio'])
            all_drawdowns.append(perf['max_drawdown'])
            all_win_rates.append(perf['win_rate'])
        
        summary = {
            'total_strategies': len(individual_results),
            'return_stats': {
                'best': max(all_returns),
                'worst': min(all_returns),
                'average': sum(all_returns) / len(all_returns),
                'positive_count': len([r for r in all_returns if r > 0])
            },
            'sharpe_stats': {
                'best': max(all_sharpe),
                'worst': min(all_sharpe),
                'average': sum(all_sharpe) / len(all_sharpe),
                'above_1_count': len([s for s in all_sharpe if s > 1.0])
            },
            'drawdown_stats': {
                'best': min(all_drawdowns),
                'worst': max(all_drawdowns),
                'average': sum(all_drawdowns) / len(all_drawdowns),
                'low_risk_count': len([d for d in all_drawdowns if d < 0.1])
            },
            'win_rate_stats': {
                'best': max(all_win_rates),
                'worst': min(all_win_rates),
                'average': sum(all_win_rates) / len(all_win_rates),
                'high_win_count': len([w for w in all_win_rates if w > 0.6])
            }
        }
        
        return summary
    
    def get_available_strategies(self) -> List[str]:
        """获取可用策略列表"""
        # 这里可以扫描策略目录或注册表
        return ["SimpleMovingAverage", "MeanReversion", "MomentumBreakout"]
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        cache_info = {
            'cache_dir': self.cache_dir,
            'cached_optimizations': 0,
            'total_cache_size': 0
        }
        
        try:
            if os.path.exists(self.cache_dir):
                files = os.listdir(self.cache_dir)
                cache_info['cached_optimizations'] = len([f for f in files if f.startswith('optimization_')])
                
                total_size = 0
                for f in files:
                    file_path = os.path.join(self.cache_dir, f)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                
                cache_info['total_cache_size'] = total_size
        
        except Exception as e:
            self.logger.error(f"获取缓存信息失败: {e}")
        
        return cache_info


# 示例策略函数
def simple_moving_average_strategy(data: List[MarketData], period: int = 20, **kwargs) -> str:
    """简单移动平均策略"""
    if len(data) < period:
        return "HOLD"
    
    # 计算移动平均
    recent_prices = [d.close for d in data[-period:]]
    ma = sum(recent_prices) / len(recent_prices)
    
    current_price = data[-1].close
    
    if current_price > ma * 1.02:  # 价格超过MA 2%
        return "BUY"
    elif current_price < ma * 0.98:  # 价格低于MA 2%
        return "SELL"
    else:
        return "HOLD"


def mean_reversion_strategy(data: List[MarketData], period: int = 14, threshold: float = 2.0, **kwargs) -> str:
    """均值回归策略"""
    if len(data) < period:
        return "HOLD"
    
    # 计算价格的标准差
    recent_prices = [d.close for d in data[-period:]]
    mean_price = sum(recent_prices) / len(recent_prices)
    
    variance = sum((p - mean_price) ** 2 for p in recent_prices) / len(recent_prices)
    std_dev = variance ** 0.5
    
    current_price = data[-1].close
    z_score = (current_price - mean_price) / std_dev if std_dev > 0 else 0
    
    if z_score > threshold:  # 价格过高，卖出
        return "SELL"
    elif z_score < -threshold:  # 价格过低，买入
        return "BUY"
    else:
        return "HOLD"


# 使用示例和测试
if __name__ == "__main__":
    print("🚀 策略回测集成模块")
    print("=" * 50)
    
    # 创建回测管理器
    manager = StrategyBacktestManager()
    print("✅ 回测管理器创建成功")
    
    # 创建回测配置
    config = BacktestConfig(
        symbol="AAPL",
        start_date="2023-01-01",
        end_date="2023-06-30",
        initial_capital=100000,
        strategy_name="SimpleMA"
    )
    
    print(f"\\n📊 回测配置:")
    print(f"  股票: {config.symbol}")
    print(f"  期间: {config.start_date} - {config.end_date}")
    print(f"  资金: ${config.initial_capital:,}")
    
    # 测试单次回测
    print("\\n🔍 测试单次回测...")
    try:
        results, metrics = manager.run_single_backtest(
            config, 
            simple_moving_average_strategy,
            period=20
        )
        print(f"✅ 单次回测完成:")
        print(f"  总收益率: {metrics.total_return:.2%}")
        print(f"  夏普比率: {metrics.sharpe_ratio:.2f}")
        print(f"  最大回撤: {metrics.max_drawdown:.2%}")
        print(f"  交易次数: {metrics.total_trades}")
    except Exception as e:
        print(f"❌ 单次回测失败: {e}")
    
    # 测试参数优化
    print("\\n🔧 测试参数优化...")
    try:
        parameter_ranges = [
            ParameterRange(name="period", param_type="int", min_value=10, max_value=30, step=5)
        ]
        
        optimization_results = manager.optimize_strategy(
            config,
            simple_moving_average_strategy,
            parameter_ranges,
            optimizer_type="grid",
            max_iterations=10
        )
        
        print(f"✅ 参数优化完成: {len(optimization_results)}个结果")
        if optimization_results:
            best = optimization_results[0]
            print(f"  最优参数: {best.parameters}")
            print(f"  最优适应度: {best.fitness:.4f}")
    except Exception as e:
        print(f"❌ 参数优化失败: {e}")
    
    # 测试批量回测
    print("\\n📈 测试批量回测...")
    try:
        configs = [
            BacktestConfig(symbol="AAPL", strategy_name="SimpleMA"),
            BacktestConfig(symbol="AAPL", strategy_name="MeanReversion")
        ]
        
        strategy_funcs = {
            "SimpleMA": simple_moving_average_strategy,
            "MeanReversion": mean_reversion_strategy
        }
        
        batch_results = manager.batch_backtest(configs, strategy_funcs)
        print(f"✅ 批量回测完成:")
        print(f"  策略数量: {batch_results['summary']['total_strategies']}")
        print(f"  平均收益: {batch_results['summary']['return_stats']['average']:.2%}")
        print(f"  盈利策略: {batch_results['summary']['return_stats']['positive_count']}")
    except Exception as e:
        print(f"❌ 批量回测失败: {e}")
    
    # 测试任务管理
    print("\\n⚙️ 测试任务管理...")
    try:
        # 创建任务
        task_id = manager.create_backtest_task(config, simple_moving_average_strategy, period=15)
        print(f"✅ 任务创建: {task_id}")
        
        # 执行任务
        success = manager.run_task(task_id)
        print(f"✅ 任务执行: {'成功' if success else '失败'}")
        
        # 查看状态
        status = manager.get_task_status(task_id)
        print(f"✅ 任务状态: {status['status']}")
        if 'results_summary' in status:
            print(f"  任务结果: 收益{status['results_summary']['total_return']:.2%}")
    except Exception as e:
        print(f"❌ 任务管理失败: {e}")
    
    # 查看缓存信息
    print("\\n💾 缓存信息:")
    cache_info = manager.get_cache_info()
    print(f"  缓存目录: {cache_info['cache_dir']}")
    print(f"  缓存优化结果: {cache_info['cached_optimizations']}个")
    print(f"  缓存大小: {cache_info['total_cache_size']} bytes")
    
    print("\\n🎯 集成模块核心功能:")
    print("  - 完整回测流程管理 ✅")
    print("  - 策略参数优化集成 ✅")
    print("  - 多策略批量回测 ✅")
    print("  - 异步任务管理 ✅")
    print("  - 结果缓存机制 ✅")
    
    print("\\n🔧 下一步完善:")
    print("  1. 实际策略类集成")
    print("  2. 并行处理支持")
    print("  3. Web界面开发")
    print("  4. 实时监控功能")
    
    print("\\n" + "=" * 50)