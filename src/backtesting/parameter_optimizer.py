"""
策略回测参数优化器

提供多种优化算法来寻找策略的最优参数组合，
包括网格搜索、遗传算法、贝叶斯优化等。

核心功能：
1. 网格搜索优化
2. 随机搜索优化
3. 遗传算法优化
4. 参数空间定义
5. 优化结果分析
"""

import itertools
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class ParameterRange:
    """参数范围定义"""
    name: str                           # 参数名称
    param_type: str = "float"          # 参数类型: float, int, choice
    min_value: Optional[float] = None   # 最小值
    max_value: Optional[float] = None   # 最大值
    step: Optional[float] = None        # 步长
    choices: Optional[List[Any]] = None # 选择列表
    
    def validate(self) -> bool:
        """验证参数范围定义"""
        if self.param_type in ["float", "int"]:
            return (self.min_value is not None and 
                   self.max_value is not None and
                   self.min_value < self.max_value)
        elif self.param_type == "choice":
            return self.choices is not None and len(self.choices) > 0
        return False
    
    def generate_values(self, num_samples: int = None) -> List[Any]:
        """生成参数值列表"""
        if self.param_type == "choice":
            return self.choices
        
        elif self.param_type == "int":
            if self.step is None:
                self.step = 1
            values = []
            current = self.min_value
            while current <= self.max_value:
                values.append(int(current))
                current += self.step
            return values
        
        elif self.param_type == "float":
            if num_samples is None:
                if self.step is None:
                    num_samples = 10
                else:
                    num_samples = int((self.max_value - self.min_value) / self.step) + 1
            
            if self.step is not None:
                values = []
                current = self.min_value
                while current <= self.max_value:
                    values.append(round(current, 6))
                    current += self.step
                return values
            else:
                # 均匀分布
                step = (self.max_value - self.min_value) / (num_samples - 1)
                return [round(self.min_value + i * step, 6) for i in range(num_samples)]
        
        return []


@dataclass
class OptimizationResult:
    """优化结果"""
    parameters: Dict[str, Any]          # 参数组合
    fitness: float                      # 适应度得分
    metrics: Dict[str, float] = field(default_factory=dict)  # 详细指标
    backtest_results: Any = None        # 回测结果对象
    optimization_time: float = 0.0      # 优化耗时
    
    def __lt__(self, other):
        """用于排序比较"""
        return self.fitness < other.fitness


class ParameterOptimizer(ABC):
    """参数优化器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"Optimizer.{name}")
    
    @abstractmethod
    def optimize(self, parameter_ranges: List[ParameterRange],
                objective_function: Callable,
                max_iterations: int = 100) -> List[OptimizationResult]:
        """执行参数优化"""
        pass


class GridSearchOptimizer(ParameterOptimizer):
    """网格搜索优化器"""
    
    def __init__(self):
        super().__init__("GridSearch")
    
    def optimize(self, parameter_ranges: List[ParameterRange],
                objective_function: Callable,
                max_iterations: int = 100) -> List[OptimizationResult]:
        """
        网格搜索优化
        
        Args:
            parameter_ranges: 参数范围列表
            objective_function: 目标函数，接受参数字典，返回OptimizationResult
            max_iterations: 最大迭代次数
        
        Returns:
            优化结果列表，按适应度排序
        """
        self.logger.info("开始网格搜索优化")
        
        # 验证参数范围
        for param_range in parameter_ranges:
            if not param_range.validate():
                raise ValueError(f"无效的参数范围: {param_range.name}")
        
        # 生成所有参数组合
        param_combinations = self._generate_grid_combinations(parameter_ranges)
        
        # 限制组合数量
        if len(param_combinations) > max_iterations:
            self.logger.warning(f"参数组合过多({len(param_combinations)})，限制为{max_iterations}")
            # 使用采样减少组合数量
            import random
            random.seed(42)
            param_combinations = random.sample(param_combinations, max_iterations)
        
        results = []
        total_combinations = len(param_combinations)
        
        self.logger.info(f"总参数组合数: {total_combinations}")
        
        # 执行回测
        for i, params in enumerate(param_combinations):
            try:
                start_time = datetime.now()
                
                # 调用目标函数
                result = objective_function(params)
                
                if isinstance(result, OptimizationResult):
                    result.optimization_time = (datetime.now() - start_time).total_seconds()
                    results.append(result)
                else:
                    # 兼容返回单个数值的情况
                    opt_result = OptimizationResult(
                        parameters=params,
                        fitness=float(result),
                        optimization_time=(datetime.now() - start_time).total_seconds()
                    )
                    results.append(opt_result)
                
                # 进度日志
                if (i + 1) % max(1, total_combinations // 10) == 0:
                    progress = (i + 1) / total_combinations * 100
                    self.logger.info(f"优化进度: {progress:.1f}% ({i+1}/{total_combinations})")
            
            except Exception as e:
                self.logger.error(f"参数组合{i+1}优化失败: {params}, {e}")
                continue
        
        # 按适应度排序（降序）
        results.sort(key=lambda x: x.fitness, reverse=True)
        
        self.logger.info(f"网格搜索完成: {len(results)}个有效结果")
        if results:
            best = results[0]
            self.logger.info(f"最优结果: 适应度={best.fitness:.4f}, 参数={best.parameters}")
        
        return results
    
    def _generate_grid_combinations(self, parameter_ranges: List[ParameterRange]) -> List[Dict[str, Any]]:
        """生成网格参数组合"""
        param_values = {}
        
        for param_range in parameter_ranges:
            param_values[param_range.name] = param_range.generate_values()
        
        # 生成笛卡尔积
        param_names = list(param_values.keys())
        value_combinations = itertools.product(*[param_values[name] for name in param_names])
        
        combinations = []
        for values in value_combinations:
            combination = dict(zip(param_names, values))
            combinations.append(combination)
        
        return combinations


class RandomSearchOptimizer(ParameterOptimizer):
    """随机搜索优化器"""
    
    def __init__(self, seed: int = 42):
        super().__init__("RandomSearch")
        import random
        self.random = random
        self.random.seed(seed)
    
    def optimize(self, parameter_ranges: List[ParameterRange],
                objective_function: Callable,
                max_iterations: int = 100) -> List[OptimizationResult]:
        """
        随机搜索优化
        
        在参数空间中随机采样，适合高维参数空间。
        """
        self.logger.info("开始随机搜索优化")
        
        # 验证参数范围
        for param_range in parameter_ranges:
            if not param_range.validate():
                raise ValueError(f"无效的参数范围: {param_range.name}")
        
        results = []
        
        for i in range(max_iterations):
            try:
                # 随机生成参数组合
                params = self._generate_random_parameters(parameter_ranges)
                
                start_time = datetime.now()
                
                # 调用目标函数
                result = objective_function(params)
                
                if isinstance(result, OptimizationResult):
                    result.optimization_time = (datetime.now() - start_time).total_seconds()
                    results.append(result)
                else:
                    opt_result = OptimizationResult(
                        parameters=params,
                        fitness=float(result),
                        optimization_time=(datetime.now() - start_time).total_seconds()
                    )
                    results.append(opt_result)
                
                # 进度日志
                if (i + 1) % max(1, max_iterations // 10) == 0:
                    progress = (i + 1) / max_iterations * 100
                    self.logger.info(f"优化进度: {progress:.1f}% ({i+1}/{max_iterations})")
            
            except Exception as e:
                self.logger.error(f"随机搜索第{i+1}次失败: {e}")
                continue
        
        # 排序结果
        results.sort(key=lambda x: x.fitness, reverse=True)
        
        self.logger.info(f"随机搜索完成: {len(results)}个有效结果")
        if results:
            best = results[0]
            self.logger.info(f"最优结果: 适应度={best.fitness:.4f}, 参数={best.parameters}")
        
        return results
    
    def _generate_random_parameters(self, parameter_ranges: List[ParameterRange]) -> Dict[str, Any]:
        """生成随机参数组合"""
        params = {}
        
        for param_range in parameter_ranges:
            if param_range.param_type == "choice":
                params[param_range.name] = self.random.choice(param_range.choices)
            
            elif param_range.param_type == "int":
                params[param_range.name] = self.random.randint(
                    int(param_range.min_value), 
                    int(param_range.max_value)
                )
            
            elif param_range.param_type == "float":
                params[param_range.name] = round(
                    self.random.uniform(param_range.min_value, param_range.max_value), 
                    6
                )
        
        return params


class GeneticOptimizer(ParameterOptimizer):
    """遗传算法优化器"""
    
    def __init__(self, population_size: int = 50, mutation_rate: float = 0.1, 
                 crossover_rate: float = 0.8, seed: int = 42):
        super().__init__("Genetic")
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        import random
        self.random = random
        self.random.seed(seed)
    
    def optimize(self, parameter_ranges: List[ParameterRange],
                objective_function: Callable,
                max_iterations: int = 100) -> List[OptimizationResult]:
        """
        遗传算法优化
        
        使用选择、交叉、变异操作进化参数组合。
        """
        self.logger.info(f"开始遗传算法优化: 种群大小={self.population_size}, 代数={max_iterations}")
        
        # 验证参数范围
        for param_range in parameter_ranges:
            if not param_range.validate():
                raise ValueError(f"无效的参数范围: {param_range.name}")
        
        self.parameter_ranges = parameter_ranges
        
        # 初始化种群
        population = self._initialize_population()
        all_results = []
        
        for generation in range(max_iterations):
            self.logger.info(f"第{generation+1}代进化")
            
            # 评估种群
            generation_results = []
            for individual in population:
                try:
                    start_time = datetime.now()
                    result = objective_function(individual)
                    
                    if isinstance(result, OptimizationResult):
                        result.optimization_time = (datetime.now() - start_time).total_seconds()
                        generation_results.append(result)
                    else:
                        opt_result = OptimizationResult(
                            parameters=individual,
                            fitness=float(result),
                            optimization_time=(datetime.now() - start_time).total_seconds()
                        )
                        generation_results.append(opt_result)
                
                except Exception as e:
                    self.logger.error(f"个体评估失败: {individual}, {e}")
                    # 给失败的个体一个很低的适应度
                    opt_result = OptimizationResult(
                        parameters=individual,
                        fitness=-float('inf')
                    )
                    generation_results.append(opt_result)
            
            all_results.extend(generation_results)
            
            # 排序（按适应度降序）
            generation_results.sort(key=lambda x: x.fitness, reverse=True)
            
            # 记录最优个体
            if generation_results:
                best = generation_results[0]
                avg_fitness = sum(r.fitness for r in generation_results if r.fitness != -float('inf')) / len(generation_results)
                self.logger.info(f"第{generation+1}代: 最优适应度={best.fitness:.4f}, 平均适应度={avg_fitness:.4f}")
            
            # 选择、交叉、变异
            if generation < max_iterations - 1:  # 不是最后一代
                population = self._evolve_population(generation_results)
        
        # 返回所有结果，按适应度排序
        all_results.sort(key=lambda x: x.fitness, reverse=True)
        
        self.logger.info(f"遗传算法完成: {len(all_results)}个评估结果")
        if all_results:
            best = all_results[0]
            self.logger.info(f"全局最优: 适应度={best.fitness:.4f}, 参数={best.parameters}")
        
        return all_results
    
    def _initialize_population(self) -> List[Dict[str, Any]]:
        """初始化种群"""
        population = []
        
        for _ in range(self.population_size):
            individual = {}
            for param_range in self.parameter_ranges:
                if param_range.param_type == "choice":
                    individual[param_range.name] = self.random.choice(param_range.choices)
                elif param_range.param_type == "int":
                    individual[param_range.name] = self.random.randint(
                        int(param_range.min_value), 
                        int(param_range.max_value)
                    )
                elif param_range.param_type == "float":
                    individual[param_range.name] = round(
                        self.random.uniform(param_range.min_value, param_range.max_value), 
                        6
                    )
            population.append(individual)
        
        return population
    
    def _evolve_population(self, evaluated_population: List[OptimizationResult]) -> List[Dict[str, Any]]:
        """进化种群"""
        # 选择（轮盘赌选择）
        selected = self._selection(evaluated_population)
        
        # 交叉和变异
        new_population = []
        
        for i in range(0, len(selected), 2):
            parent1 = selected[i].parameters
            parent2 = selected[i + 1] if i + 1 < len(selected) else selected[0].parameters
            
            # 交叉
            if self.random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # 变异
            if self.random.random() < self.mutation_rate:
                child1 = self._mutate(child1)
            if self.random.random() < self.mutation_rate:
                child2 = self._mutate(child2)
            
            new_population.extend([child1, child2])
        
        # 确保种群大小
        return new_population[:self.population_size]
    
    def _selection(self, evaluated_population: List[OptimizationResult]) -> List[OptimizationResult]:
        """轮盘赌选择"""
        # 处理负适应度
        min_fitness = min(r.fitness for r in evaluated_population if r.fitness != -float('inf'))
        if min_fitness < 0:
            offset = abs(min_fitness) + 1
        else:
            offset = 0
        
        # 计算选择概率
        total_fitness = sum(max(0, r.fitness + offset) for r in evaluated_population)
        
        if total_fitness == 0:
            # 如果所有适应度都相同，随机选择
            return self.random.choices(evaluated_population, k=self.population_size)
        
        # 轮盘赌选择
        selected = []
        for _ in range(self.population_size):
            pick = self.random.uniform(0, total_fitness)
            current = 0
            for individual in evaluated_population:
                current += max(0, individual.fitness + offset)
                if current >= pick:
                    selected.append(individual)
                    break
        
        return selected
    
    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """单点交叉"""
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # 随机选择交叉点
        param_names = list(parent1.keys())
        if len(param_names) > 1:
            crossover_point = self.random.randint(1, len(param_names) - 1)
            
            for i, param_name in enumerate(param_names):
                if i >= crossover_point:
                    child1[param_name] = parent2[param_name]
                    child2[param_name] = parent1[param_name]
        
        return child1, child2
    
    def _mutate(self, individual: Dict[str, Any]) -> Dict[str, Any]:
        """变异操作"""
        mutated = individual.copy()
        
        # 随机选择一个参数进行变异
        param_name = self.random.choice(list(mutated.keys()))
        
        # 找到对应的参数范围
        param_range = None
        for pr in self.parameter_ranges:
            if pr.name == param_name:
                param_range = pr
                break
        
        if param_range:
            if param_range.param_type == "choice":
                mutated[param_name] = self.random.choice(param_range.choices)
            elif param_range.param_type == "int":
                mutated[param_name] = self.random.randint(
                    int(param_range.min_value), 
                    int(param_range.max_value)
                )
            elif param_range.param_type == "float":
                mutated[param_name] = round(
                    self.random.uniform(param_range.min_value, param_range.max_value), 
                    6
                )
        
        return mutated


class OptimizationManager:
    """
    参数优化管理器
    
    统一管理多种优化算法，提供简化的接口
    进行策略参数优化。
    """
    
    def __init__(self):
        self.optimizers = {
            "grid": GridSearchOptimizer(),
            "random": RandomSearchOptimizer(),
            "genetic": GeneticOptimizer()
        }
        self.logger = logging.getLogger("OptimizationManager")
    
    def register_optimizer(self, name: str, optimizer: ParameterOptimizer):
        """注册新的优化器"""
        self.optimizers[name] = optimizer
        self.logger.info(f"注册优化器: {name}")
    
    def optimize_strategy(self, 
                         parameter_ranges: List[ParameterRange],
                         backtest_function: Callable,
                         objective_metric: str = "sharpe_ratio",
                         optimizer_type: str = "grid",
                         max_iterations: int = 100) -> List[OptimizationResult]:
        """
        策略参数优化
        
        Args:
            parameter_ranges: 参数范围列表
            backtest_function: 回测函数，接受参数字典，返回回测结果
            objective_metric: 优化目标指标
            optimizer_type: 优化器类型
            max_iterations: 最大迭代次数
        
        Returns:
            优化结果列表
        """
        if optimizer_type not in self.optimizers:
            raise ValueError(f"未知的优化器类型: {optimizer_type}")
        
        optimizer = self.optimizers[optimizer_type]
        
        def objective_function(params: Dict[str, Any]) -> OptimizationResult:
            """目标函数"""
            try:
                # 执行回测
                backtest_result = backtest_function(params)
                
                # 提取目标指标
                if hasattr(backtest_result, objective_metric):
                    fitness = getattr(backtest_result, objective_metric)
                elif hasattr(backtest_result, 'metrics') and objective_metric in backtest_result.metrics:
                    fitness = backtest_result.metrics[objective_metric]
                else:
                    # 默认使用总收益
                    fitness = getattr(backtest_result, 'total_return', 0.0)
                
                # 创建优化结果
                metrics = {}
                if hasattr(backtest_result, 'get_summary'):
                    summary = backtest_result.get_summary()
                    if 'performance' in summary:
                        for key, value in summary['performance'].items():
                            try:
                                # 尝试转换为数值
                                if isinstance(value, str) and '%' in value:
                                    metrics[key] = float(value.replace('%', '')) / 100
                                else:
                                    metrics[key] = float(value)
                            except:
                                pass
                
                return OptimizationResult(
                    parameters=params,
                    fitness=float(fitness) if fitness is not None else 0.0,
                    metrics=metrics,
                    backtest_results=backtest_result
                )
            
            except Exception as e:
                self.logger.error(f"回测失败: {params}, {e}")
                return OptimizationResult(
                    parameters=params,
                    fitness=-float('inf')
                )
        
        # 执行优化
        self.logger.info(f"开始参数优化: 算法={optimizer_type}, 目标={objective_metric}")
        results = optimizer.optimize(parameter_ranges, objective_function, max_iterations)
        
        self.logger.info(f"参数优化完成: {len(results)}个结果")
        
        return results
    
    def get_optimization_report(self, results: List[OptimizationResult], 
                               top_n: int = 10) -> Dict[str, Any]:
        """生成优化报告"""
        if not results:
            return {"error": "没有优化结果"}
        
        # 过滤有效结果
        valid_results = [r for r in results if r.fitness != -float('inf')]
        
        if not valid_results:
            return {"error": "没有有效的优化结果"}
        
        # 基础统计
        fitness_values = [r.fitness for r in valid_results]
        
        report = {
            "summary": {
                "total_evaluations": len(results),
                "valid_evaluations": len(valid_results),
                "success_rate": len(valid_results) / len(results),
                "best_fitness": max(fitness_values),
                "worst_fitness": min(fitness_values),
                "average_fitness": sum(fitness_values) / len(fitness_values),
                "fitness_std": self._calculate_std(fitness_values)
            },
            "top_results": [
                {
                    "rank": i + 1,
                    "parameters": result.parameters,
                    "fitness": result.fitness,
                    "metrics": result.metrics
                }
                for i, result in enumerate(valid_results[:top_n])
            ],
            "parameter_analysis": self._analyze_parameters(valid_results)
        }
        
        return report
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _analyze_parameters(self, results: List[OptimizationResult]) -> Dict[str, Any]:
        """分析参数分布"""
        if not results:
            return {}
        
        param_analysis = {}
        
        # 获取所有参数名
        param_names = set()
        for result in results:
            param_names.update(result.parameters.keys())
        
        for param_name in param_names:
            values = []
            for result in results:
                if param_name in result.parameters:
                    values.append(result.parameters[param_name])
            
            if values:
                if isinstance(values[0], (int, float)):
                    param_analysis[param_name] = {
                        "type": "numeric",
                        "min": min(values),
                        "max": max(values),
                        "mean": sum(values) / len(values),
                        "best_value": results[0].parameters.get(param_name)
                    }
                else:
                    # 分类参数
                    value_counts = {}
                    for value in values:
                        value_counts[value] = value_counts.get(value, 0) + 1
                    
                    param_analysis[param_name] = {
                        "type": "categorical",
                        "value_counts": value_counts,
                        "best_value": results[0].parameters.get(param_name)
                    }
        
        return param_analysis


# 使用示例和测试
if __name__ == "__main__":
    print("🔧 策略回测参数优化器")
    print("=" * 50)
    
    # 创建优化管理器
    optimization_manager = OptimizationManager()
    print("✅ 优化管理器创建成功")
    
    # 定义示例参数范围
    parameter_ranges = [
        ParameterRange(name="period", param_type="int", min_value=5, max_value=30, step=5),
        ParameterRange(name="threshold", param_type="float", min_value=0.01, max_value=0.1, step=0.01),
        ParameterRange(name="method", param_type="choice", choices=["sma", "ema", "wma"])
    ]
    
    print("\\n📊 参数范围定义:")
    for pr in parameter_ranges:
        print(f"  {pr.name}: {pr.param_type}, 范围={pr.min_value}-{pr.max_value}")
        if pr.choices:
            print(f"    选择: {pr.choices}")
    
    # 测试网格搜索
    print("\\n🔍 测试网格搜索...")
    grid_optimizer = GridSearchOptimizer()
    
    # 模拟目标函数
    def mock_objective(params):
        # 模拟计算适应度
        fitness = params.get("period", 10) * 0.1 + params.get("threshold", 0.05) * 10
        if params.get("method") == "ema":
            fitness += 0.5
        
        return OptimizationResult(
            parameters=params,
            fitness=fitness,
            metrics={"return": fitness * 0.1, "sharpe": fitness * 0.2}
        )
    
    grid_results = grid_optimizer.optimize(parameter_ranges, mock_objective, max_iterations=50)
    print(f"✅ 网格搜索完成: {len(grid_results)}个结果")
    if grid_results:
        best = grid_results[0]
        print(f"  最优参数: {best.parameters}")
        print(f"  最优适应度: {best.fitness:.4f}")
    
    # 测试随机搜索
    print("\\n🎲 测试随机搜索...")
    random_optimizer = RandomSearchOptimizer()
    random_results = random_optimizer.optimize(parameter_ranges, mock_objective, max_iterations=30)
    print(f"✅ 随机搜索完成: {len(random_results)}个结果")
    if random_results:
        best = random_results[0]
        print(f"  最优参数: {best.parameters}")
        print(f"  最优适应度: {best.fitness:.4f}")
    
    # 测试遗传算法
    print("\\n🧬 测试遗传算法...")
    genetic_optimizer = GeneticOptimizer(population_size=20, mutation_rate=0.2)
    genetic_results = genetic_optimizer.optimize(parameter_ranges, mock_objective, max_iterations=10)
    print(f"✅ 遗传算法完成: {len(genetic_results)}个结果")
    if genetic_results:
        best = genetic_results[0]
        print(f"  最优参数: {best.parameters}")
        print(f"  最优适应度: {best.fitness:.4f}")
    
    # 生成优化报告
    print("\\n📈 优化报告...")
    if grid_results:
        report = optimization_manager.get_optimization_report(grid_results, top_n=5)
        print(f"✅ 报告生成完成:")
        print(f"  总评估次数: {report['summary']['total_evaluations']}")
        print(f"  成功率: {report['summary']['success_rate']:.1%}")
        print(f"  最优适应度: {report['summary']['best_fitness']:.4f}")
        print(f"  参数分析: {len(report['parameter_analysis'])}个参数")
    
    print("\\n🎯 参数优化器核心功能:")
    print("  - 网格搜索算法 ✅")
    print("  - 随机搜索算法 ✅")
    print("  - 遗传算法优化 ✅")
    print("  - 参数范围管理 ✅")
    print("  - 优化结果分析 ✅")
    
    print("\\n🔧 下一步集成:")
    print("  1. 贝叶斯优化算法")
    print("  2. 多目标优化支持")
    print("  3. 并行优化执行")
    print("  4. 优化过程可视化")
    
    print("\\n" + "=" * 50)