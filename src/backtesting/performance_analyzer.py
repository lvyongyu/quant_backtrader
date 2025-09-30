"""
回测性能分析器

提供全面的回测结果分析功能，包括风险指标计算、
图表生成、报告输出等。

核心功能：
1. 风险收益指标计算
2. 交易统计分析
3. 时序分析
4. 绩效归因分析
5. 对比分析
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import json


@dataclass
class PerformanceMetrics:
    """性能指标集合"""
    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    monthly_return: float = 0.0
    daily_return_mean: float = 0.0
    
    # 风险指标
    volatility: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    var_95: float = 0.0  # 95% VaR
    cvar_95: float = 0.0  # 95% CVaR
    
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    
    # 交易指标
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # 时间指标
    trading_days: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'returns': {
                'total_return': f"{self.total_return:.2%}",
                'annual_return': f"{self.annual_return:.2%}",
                'monthly_return': f"{self.monthly_return:.2%}",
                'daily_return_mean': f"{self.daily_return_mean:.4%}"
            },
            'risk': {
                'volatility': f"{self.volatility:.2%}",
                'max_drawdown': f"{self.max_drawdown:.2%}",
                'max_drawdown_duration': f"{self.max_drawdown_duration} days",
                'var_95': f"{self.var_95:.2%}",
                'cvar_95': f"{self.cvar_95:.2%}"
            },
            'risk_adjusted': {
                'sharpe_ratio': f"{self.sharpe_ratio:.2f}",
                'sortino_ratio': f"{self.sortino_ratio:.2f}",
                'calmar_ratio': f"{self.calmar_ratio:.2f}",
                'information_ratio': f"{self.information_ratio:.2f}"
            },
            'trading': {
                'total_trades': self.total_trades,
                'win_rate': f"{self.win_rate:.2%}",
                'profit_factor': f"{self.profit_factor:.2f}",
                'avg_win': f"${self.avg_win:.2f}",
                'avg_loss': f"${self.avg_loss:.2f}",
                'max_consecutive_wins': self.max_consecutive_wins,
                'max_consecutive_losses': self.max_consecutive_losses
            },
            'period': {
                'trading_days': self.trading_days,
                'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else '',
                'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else ''
            }
        }


@dataclass 
class DrawdownPeriod:
    """回撤期间"""
    start_date: datetime
    end_date: datetime
    peak_date: datetime
    trough_date: datetime
    duration: int
    drawdown: float
    recovery_time: Optional[int] = None


class PerformanceAnalyzer:
    """
    性能分析器
    
    计算各种性能指标，生成分析报告。
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate  # 无风险利率
        self.logger = logging.getLogger("PerformanceAnalyzer")
    
    def analyze_backtest_results(self, backtest_results) -> PerformanceMetrics:
        """
        分析回测结果
        
        Args:
            backtest_results: 回测结果对象
        
        Returns:
            性能指标
        """
        metrics = PerformanceMetrics()
        
        # 基础信息
        if hasattr(backtest_results, 'trades') and backtest_results.trades:
            metrics.total_trades = len(backtest_results.trades)
            metrics.start_date = backtest_results.trades[0].entry_time
            metrics.end_date = backtest_results.trades[-1].exit_time or backtest_results.trades[-1].entry_time
        
        if hasattr(backtest_results, 'equity_curve') and len(backtest_results.equity_curve) > 0:
            equity_curve = backtest_results.equity_curve
            daily_returns = backtest_results.daily_returns if hasattr(backtest_results, 'daily_returns') else None
            
            # 时间指标
            metrics.trading_days = len(equity_curve)
            if not metrics.start_date:
                metrics.start_date = equity_curve.index[0]
            if not metrics.end_date:
                metrics.end_date = equity_curve.index[-1]
            
            # 收益指标
            metrics = self._calculate_return_metrics(metrics, equity_curve, daily_returns)
            
            # 风险指标
            metrics = self._calculate_risk_metrics(metrics, equity_curve, daily_returns)
            
            # 风险调整收益
            metrics = self._calculate_risk_adjusted_metrics(metrics, daily_returns)
        
        # 交易指标
        if hasattr(backtest_results, 'trades') and backtest_results.trades:
            metrics = self._calculate_trading_metrics(metrics, backtest_results.trades)
        
        return metrics
    
    def _calculate_return_metrics(self, metrics: PerformanceMetrics, 
                                 equity_curve, daily_returns) -> PerformanceMetrics:
        """计算收益指标"""
        if len(equity_curve) == 0:
            return metrics
        
        # 总收益
        initial_value = equity_curve.iloc[0] if hasattr(equity_curve, 'iloc') else equity_curve[0]
        final_value = equity_curve.iloc[-1] if hasattr(equity_curve, 'iloc') else equity_curve[-1]
        
        metrics.total_return = (final_value / initial_value) - 1 if initial_value > 0 else 0
        
        # 年化收益
        if metrics.trading_days > 0:
            years = metrics.trading_days / 252  # 假设252个交易日
            if years > 0:
                metrics.annual_return = (1 + metrics.total_return) ** (1/years) - 1
                metrics.monthly_return = (1 + metrics.annual_return) ** (1/12) - 1
        
        # 日均收益
        if daily_returns is not None and len(daily_returns) > 0:
            returns_list = daily_returns.tolist() if hasattr(daily_returns, 'tolist') else list(daily_returns)
            metrics.daily_return_mean = sum(returns_list) / len(returns_list)
        
        return metrics
    
    def _calculate_risk_metrics(self, metrics: PerformanceMetrics, 
                               equity_curve, daily_returns) -> PerformanceMetrics:
        """计算风险指标"""
        if daily_returns is not None and len(daily_returns) > 0:
            returns_list = daily_returns.tolist() if hasattr(daily_returns, 'tolist') else list(daily_returns)
            
            # 波动率
            if len(returns_list) > 1:
                mean_return = sum(returns_list) / len(returns_list)
                variance = sum((r - mean_return) ** 2 for r in returns_list) / (len(returns_list) - 1)
                metrics.volatility = (variance ** 0.5) * (252 ** 0.5)  # 年化波动率
            
            # VaR和CVaR (95%)
            sorted_returns = sorted(returns_list)
            var_index = int(len(sorted_returns) * 0.05)
            if var_index < len(sorted_returns):
                metrics.var_95 = abs(sorted_returns[var_index])
                # CVaR是超过VaR的损失的平均值
                tail_losses = [abs(r) for r in sorted_returns[:var_index+1] if r < 0]
                if tail_losses:
                    metrics.cvar_95 = sum(tail_losses) / len(tail_losses)
        
        # 最大回撤
        if len(equity_curve) > 0:
            drawdown_info = self._calculate_drawdown(equity_curve)
            metrics.max_drawdown = drawdown_info['max_drawdown']
            metrics.max_drawdown_duration = drawdown_info['max_duration']
        
        return metrics
    
    def _calculate_risk_adjusted_metrics(self, metrics: PerformanceMetrics, 
                                       daily_returns) -> PerformanceMetrics:
        """计算风险调整收益指标"""
        # Sharpe比率
        if metrics.volatility > 0:
            excess_return = metrics.annual_return - self.risk_free_rate
            metrics.sharpe_ratio = excess_return / metrics.volatility
        
        # Sortino比率（只考虑下行波动）
        if daily_returns is not None and len(daily_returns) > 0:
            returns_list = daily_returns.tolist() if hasattr(daily_returns, 'tolist') else list(daily_returns)
            negative_returns = [r for r in returns_list if r < 0]
            
            if negative_returns:
                downside_variance = sum(r ** 2 for r in negative_returns) / len(negative_returns)
                downside_volatility = (downside_variance ** 0.5) * (252 ** 0.5)
                
                if downside_volatility > 0:
                    excess_return = metrics.annual_return - self.risk_free_rate
                    metrics.sortino_ratio = excess_return / downside_volatility
        
        # Calmar比率
        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown
        
        return metrics
    
    def _calculate_trading_metrics(self, metrics: PerformanceMetrics, trades: List) -> PerformanceMetrics:
        """计算交易指标"""
        if not trades:
            return metrics
        
        # 基础统计
        total_trades = len(trades)
        winning_trades = [t for t in trades if getattr(t, 'pnl', 0) > 0]
        losing_trades = [t for t in trades if getattr(t, 'pnl', 0) < 0]
        
        metrics.total_trades = total_trades
        metrics.win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # 平均盈亏
        if winning_trades:
            metrics.avg_win = sum(getattr(t, 'pnl', 0) for t in winning_trades) / len(winning_trades)
        if losing_trades:
            metrics.avg_loss = sum(getattr(t, 'pnl', 0) for t in losing_trades) / len(losing_trades)
        
        # 盈亏比
        if metrics.avg_loss < 0:
            metrics.profit_factor = abs(metrics.avg_win / metrics.avg_loss)
        
        # 连续盈亏
        consecutive_wins = 0
        consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            pnl = getattr(trade, 'pnl', 0)
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                consecutive_wins = max(consecutive_wins, current_wins)
            elif pnl < 0:
                current_losses += 1
                current_wins = 0
                consecutive_losses = max(consecutive_losses, current_losses)
        
        metrics.max_consecutive_wins = consecutive_wins
        metrics.max_consecutive_losses = consecutive_losses
        
        return metrics
    
    def _calculate_drawdown(self, equity_curve) -> Dict[str, Any]:
        """计算回撤相关指标"""
        try:
            # 转换为列表以便处理
            if hasattr(equity_curve, 'values'):
                if hasattr(equity_curve.values, 'tolist'):
                    values = equity_curve.values.tolist()
                else:
                    values = list(equity_curve.values)
                if hasattr(equity_curve, 'index'):
                    dates = list(equity_curve.index)
                else:
                    dates = list(range(len(values)))
            else:
                values = list(equity_curve)
                dates = list(range(len(values)))
            
            if len(values) == 0:
                return {'max_drawdown': 0.0, 'max_duration': 0, 'drawdown_periods': []}
            
            # 计算累计最高点
            peak = values[0]
            max_drawdown = 0.0
            max_duration = 0
            current_duration = 0
            drawdown_periods = []
            
            current_drawdown_start = None
            
            for i, value in enumerate(values):
                if value > peak:
                    # 创新高，结束当前回撤期
                    if current_drawdown_start is not None:
                        # 记录回撤期
                        drawdown_periods.append({
                            'start_index': current_drawdown_start,
                            'end_index': i - 1,
                            'duration': current_duration,
                            'drawdown': (peak - values[current_drawdown_start]) / peak if peak > 0 else 0
                        })
                        current_drawdown_start = None
                    
                    peak = value
                    current_duration = 0
                else:
                    # 在回撤中
                    if current_drawdown_start is None:
                        current_drawdown_start = i
                    
                    current_duration += 1
                    drawdown = (peak - value) / peak if peak > 0 else 0
                    max_drawdown = max(max_drawdown, drawdown)
                    max_duration = max(max_duration, current_duration)
            
            # 处理最后一个回撤期（如果存在）
            if current_drawdown_start is not None:
                drawdown_periods.append({
                    'start_index': current_drawdown_start,
                    'end_index': len(values) - 1,
                    'duration': current_duration,
                    'drawdown': (peak - values[-1]) / peak if peak > 0 else 0
                })
            
            return {
                'max_drawdown': max_drawdown,
                'max_duration': max_duration,
                'drawdown_periods': drawdown_periods
            }
        
        except Exception as e:
            self.logger.error(f"计算回撤失败: {e}")
            return {'max_drawdown': 0.0, 'max_duration': 0, 'drawdown_periods': []}
    
    def compare_strategies(self, results_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        比较多个策略的性能
        
        Args:
            results_dict: 策略名称到回测结果的映射
        
        Returns:
            比较报告
        """
        if not results_dict:
            return {"error": "没有提供策略结果"}
        
        comparison = {
            'strategies': {},
            'ranking': {},
            'summary': {}
        }
        
        # 分析每个策略
        strategy_metrics = {}
        for strategy_name, results in results_dict.items():
            try:
                metrics = self.analyze_backtest_results(results)
                strategy_metrics[strategy_name] = metrics
                comparison['strategies'][strategy_name] = metrics.to_dict()
            except Exception as e:
                self.logger.error(f"分析策略{strategy_name}失败: {e}")
                continue
        
        if not strategy_metrics:
            return {"error": "没有有效的策略分析结果"}
        
        # 生成排名
        ranking_criteria = {
            'total_return': lambda m: m.total_return,
            'sharpe_ratio': lambda m: m.sharpe_ratio,
            'calmar_ratio': lambda m: m.calmar_ratio,
            'max_drawdown': lambda m: -m.max_drawdown,  # 负值，因为回撤越小越好
            'win_rate': lambda m: m.win_rate,
            'profit_factor': lambda m: m.profit_factor
        }
        
        for criterion, key_func in ranking_criteria.items():
            try:
                sorted_strategies = sorted(
                    strategy_metrics.items(),
                    key=lambda x: key_func(x[1]),
                    reverse=True
                )
                comparison['ranking'][criterion] = [
                    {'strategy': name, 'value': key_func(metrics)}
                    for name, metrics in sorted_strategies
                ]
            except Exception as e:
                self.logger.error(f"排名计算失败 {criterion}: {e}")
        
        # 生成汇总统计
        if strategy_metrics:
            all_returns = [m.total_return for m in strategy_metrics.values()]
            all_sharpe = [m.sharpe_ratio for m in strategy_metrics.values()]
            all_drawdown = [m.max_drawdown for m in strategy_metrics.values()]
            
            comparison['summary'] = {
                'strategy_count': len(strategy_metrics),
                'return_stats': {
                    'best': max(all_returns),
                    'worst': min(all_returns),
                    'average': sum(all_returns) / len(all_returns)
                },
                'sharpe_stats': {
                    'best': max(all_sharpe),
                    'worst': min(all_sharpe),
                    'average': sum(all_sharpe) / len(all_sharpe)
                },
                'drawdown_stats': {
                    'best': min(all_drawdown),
                    'worst': max(all_drawdown),
                    'average': sum(all_drawdown) / len(all_drawdown)
                }
            }
        
        return comparison
    
    def generate_performance_report(self, backtest_results, 
                                  strategy_name: str = "Strategy") -> str:
        """
        生成性能报告
        
        Args:
            backtest_results: 回测结果
            strategy_name: 策略名称
        
        Returns:
            Markdown格式的报告
        """
        metrics = self.analyze_backtest_results(backtest_results)
        
        report = f"""# {strategy_name} 回测性能报告

## 执行概要
- **策略名称**: {strategy_name}
- **回测期间**: {metrics.start_date.strftime('%Y-%m-%d') if metrics.start_date else 'N/A'} 至 {metrics.end_date.strftime('%Y-%m-%d') if metrics.end_date else 'N/A'}
- **交易日数**: {metrics.trading_days}
- **总交易数**: {metrics.total_trades}

## 收益指标
| 指标 | 数值 |
|------|------|
| 总收益率 | {metrics.total_return:.2%} |
| 年化收益率 | {metrics.annual_return:.2%} |
| 月平均收益率 | {metrics.monthly_return:.2%} |
| 日平均收益率 | {metrics.daily_return_mean:.4%} |

## 风险指标
| 指标 | 数值 |
|------|------|
| 年化波动率 | {metrics.volatility:.2%} |
| 最大回撤 | {metrics.max_drawdown:.2%} |
| 最大回撤持续时间 | {metrics.max_drawdown_duration} 天 |
| 95% VaR | {metrics.var_95:.2%} |
| 95% CVaR | {metrics.cvar_95:.2%} |

## 风险调整收益
| 指标 | 数值 | 评价 |
|------|------|------|
| 夏普比率 | {metrics.sharpe_ratio:.2f} | {'优秀' if metrics.sharpe_ratio > 1.5 else '良好' if metrics.sharpe_ratio > 1.0 else '一般' if metrics.sharpe_ratio > 0.5 else '较差'} |
| 索提诺比率 | {metrics.sortino_ratio:.2f} | {'优秀' if metrics.sortino_ratio > 2.0 else '良好' if metrics.sortino_ratio > 1.5 else '一般' if metrics.sortino_ratio > 1.0 else '较差'} |
| 卡玛比率 | {metrics.calmar_ratio:.2f} | {'优秀' if metrics.calmar_ratio > 1.0 else '良好' if metrics.calmar_ratio > 0.5 else '一般' if metrics.calmar_ratio > 0.2 else '较差'} |

## 交易统计
| 指标 | 数值 |
|------|------|
| 胜率 | {metrics.win_rate:.2%} |
| 盈亏比 | {metrics.profit_factor:.2f} |
| 平均盈利 | ${metrics.avg_win:.2f} |
| 平均亏损 | ${metrics.avg_loss:.2f} |
| 最大连续盈利 | {metrics.max_consecutive_wins} |
| 最大连续亏损 | {metrics.max_consecutive_losses} |

## 总体评价
"""
        
        # 添加总体评价
        score = 0
        evaluations = []
        
        # 收益评价
        if metrics.annual_return > 0.15:
            score += 3
            evaluations.append("✅ 年化收益率优秀")
        elif metrics.annual_return > 0.08:
            score += 2
            evaluations.append("🟡 年化收益率良好")
        elif metrics.annual_return > 0.03:
            score += 1
            evaluations.append("🟡 年化收益率一般")
        else:
            evaluations.append("❌ 年化收益率较低")
        
        # 风险评价
        if metrics.max_drawdown < 0.05:
            score += 3
            evaluations.append("✅ 回撤控制优秀")
        elif metrics.max_drawdown < 0.15:
            score += 2
            evaluations.append("🟡 回撤控制良好")
        elif metrics.max_drawdown < 0.25:
            score += 1
            evaluations.append("🟡 回撤控制一般")
        else:
            evaluations.append("❌ 回撤较大")
        
        # 夏普比率评价
        if metrics.sharpe_ratio > 1.5:
            score += 3
            evaluations.append("✅ 风险调整收益优秀")
        elif metrics.sharpe_ratio > 1.0:
            score += 2
            evaluations.append("🟡 风险调整收益良好")
        elif metrics.sharpe_ratio > 0.5:
            score += 1
            evaluations.append("🟡 风险调整收益一般")
        else:
            evaluations.append("❌ 风险调整收益较差")
        
        # 交易评价
        if metrics.win_rate > 0.6 and metrics.profit_factor > 1.5:
            score += 2
            evaluations.append("✅ 交易表现优秀")
        elif metrics.win_rate > 0.45 and metrics.profit_factor > 1.2:
            score += 1
            evaluations.append("🟡 交易表现良好")
        else:
            evaluations.append("❌ 交易表现需要改进")
        
        # 总体评分
        total_score = score / 11 * 100  # 最高11分
        
        if total_score >= 80:
            overall = "🏆 优秀策略"
        elif total_score >= 60:
            overall = "👍 良好策略"
        elif total_score >= 40:
            overall = "⚠️ 一般策略"
        else:
            overall = "❌ 需要改进"
        
        report += f"""
**策略评分**: {total_score:.0f}/100 - {overall}

**详细评价**:
{chr(10).join(f"- {eval}" for eval in evaluations)}

## 建议
"""
        
        # 添加改进建议
        suggestions = []
        
        if metrics.annual_return < 0.08:
            suggestions.append("- 考虑优化入市时机和信号质量")
        
        if metrics.max_drawdown > 0.15:
            suggestions.append("- 加强风险管理，设置更严格的止损")
        
        if metrics.sharpe_ratio < 1.0:
            suggestions.append("- 改善风险调整收益，考虑降低仓位或改进选股")
        
        if metrics.win_rate < 0.4:
            suggestions.append("- 提高胜率，优化交易信号准确性")
        
        if metrics.profit_factor < 1.2:
            suggestions.append("- 改善盈亏比，及时止盈止损")
        
        if not suggestions:
            suggestions.append("- 策略表现良好，可考虑适当增加仓位或拓展到更多标的")
        
        report += chr(10).join(suggestions)
        
        report += f"""

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report


# 使用示例和测试
if __name__ == "__main__":
    print("📊 回测性能分析器")
    print("=" * 50)
    
    # 创建性能分析器
    analyzer = PerformanceAnalyzer(risk_free_rate=0.02)
    print("✅ 性能分析器创建成功")
    
    # 模拟回测结果数据
    class MockBacktestResults:
        def __init__(self):
            # 模拟交易记录
            self.trades = []
            for i in range(50):
                import random
                random.seed(42 + i)
                
                class MockTrade:
                    def __init__(self, pnl):
                        self.pnl = pnl
                        self.entry_time = datetime(2023, 1, 1) + timedelta(days=i*2)
                        self.exit_time = self.entry_time + timedelta(days=1)
                
                # 60%胜率
                pnl = random.uniform(50, 200) if random.random() < 0.6 else random.uniform(-150, -30)
                self.trades.append(MockTrade(pnl))
            
            # 模拟权益曲线
            equity_values = [100000]
            for trade in self.trades:
                equity_values.append(equity_values[-1] + trade.pnl)
            
            # 简单的时间序列模拟
            class MockSeries:
                def __init__(self, values, start_date):
                    self.values = values
                    self.dates = [start_date + timedelta(days=i) for i in range(len(values))]
                    
                def __len__(self):
                    return len(self.values)
                
                def __getitem__(self, index):
                    return self.values[index]
                
                def __iter__(self):
                    return iter(self.values)
                
                @property 
                def iloc(self):
                    class IlocWrapper:
                        def __init__(self, values):
                            self.values = values
                        def __getitem__(self, index):
                            return self.values[index]
                    return IlocWrapper(self.values)
                
                @property
                def index(self):
                    return self.dates
            
            self.equity_curve = MockSeries(equity_values, datetime(2023, 1, 1))
            
            # 生成日收益率
            daily_returns = []
            for i in range(1, len(equity_values)):
                daily_return = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                daily_returns.append(daily_return)
            
            self.daily_returns = MockSeries(daily_returns, datetime(2023, 1, 2))
    
    # 测试性能分析
    print("\\n🔍 测试性能分析...")
    mock_results = MockBacktestResults()
    metrics = analyzer.analyze_backtest_results(mock_results)
    
    print(f"✅ 性能分析完成:")
    print(f"  总收益率: {metrics.total_return:.2%}")
    print(f"  年化收益率: {metrics.annual_return:.2%}")
    print(f"  最大回撤: {metrics.max_drawdown:.2%}")
    print(f"  夏普比率: {metrics.sharpe_ratio:.2f}")
    print(f"  胜率: {metrics.win_rate:.2%}")
    print(f"  总交易数: {metrics.total_trades}")
    
    # 测试报告生成
    print("\\n📝 测试报告生成...")
    report = analyzer.generate_performance_report(mock_results, "测试策略")
    print("✅ 报告生成完成")
    print(f"  报告长度: {len(report)}字符")
    
    # 保存报告到文件
    try:
        with open("performance_report_test.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("✅ 报告已保存到 performance_report_test.md")
    except Exception as e:
        print(f"⚠️ 报告保存失败: {e}")
    
    # 测试策略比较
    print("\\n🔄 测试策略比较...")
    comparison_results = {
        "策略A": mock_results,
        "策略B": mock_results  # 使用相同数据作为示例
    }
    
    comparison = analyzer.compare_strategies(comparison_results)
    print(f"✅ 策略比较完成:")
    print(f"  策略数量: {comparison['summary']['strategy_count']}")
    print(f"  平均收益: {comparison['summary']['return_stats']['average']:.2%}")
    
    print("\\n🎯 性能分析器核心功能:")
    print("  - 全面性能指标计算 ✅")
    print("  - 风险指标分析 ✅")
    print("  - 交易统计分析 ✅")
    print("  - 策略比较功能 ✅")
    print("  - 自动报告生成 ✅")
    
    print("\\n🔧 下一步集成:")
    print("  1. 图表可视化功能")
    print("  2. 基准比较分析")
    print("  3. 滚动窗口分析")
    print("  4. 归因分析功能")
    
    print("\\n" + "=" * 50)