# P1-2 高级量化交易组件 API 参考文档

## 📋 目录

1. [高级分析组件 API](#高级分析组件-api)
2. [机器学习集成 API](#机器学习集成-api)
3. [投资组合分析 API](#投资组合分析-api)
4. [数据结构参考](#数据结构参考)
5. [配置选项](#配置选项)

---

## 🔬 高级分析组件 API

### AdvancedIndicators 类

**功能**: 提供50+高级技术指标计算

#### 初始化
```python
from advanced_analytics.technical_indicators import AdvancedIndicators

indicators = AdvancedIndicators(
    use_cache=True,           # 是否启用计算缓存
    cache_size=1000,          # 缓存大小
    validate_inputs=True      # 是否验证输入数据
)
```

#### 核心方法

##### calculate_rsi()
```python
def calculate_rsi(
    self,
    prices: pd.Series,
    period: int = 14,
    overbought: float = 70,
    oversold: float = 30
) -> IndicatorResult
```

**参数**:
- `prices` (pd.Series): 价格序列
- `period` (int): RSI计算周期，默认14
- `overbought` (float): 超买阈值，默认70
- `oversold` (float): 超卖阈值，默认30

**返回**: `IndicatorResult` 对象

**示例**:
```python
rsi_result = indicators.calculate_rsi(
    prices=stock_prices,
    period=14,
    overbought=75,
    oversold=25
)

print(f"当前RSI: {rsi_result.values.iloc[-1]:.2f}")
print(f"信号解读: {rsi_result.interpretation}")
```

##### calculate_macd()
```python
def calculate_macd(
    self,
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> IndicatorResult
```

**参数**:
- `prices` (pd.Series): 价格序列
- `fast_period` (int): 快线EMA周期，默认12
- `slow_period` (int): 慢线EMA周期，默认26
- `signal_period` (int): 信号线EMA周期，默认9

**返回**: `IndicatorResult` 对象，包含MACD线、信号线和柱状图

**示例**:
```python
macd_result = indicators.calculate_macd(prices=stock_prices)

# 获取MACD组件
macd_line = macd_result.values['macd']
signal_line = macd_result.values['signal']
histogram = macd_result.values['histogram']

# 检查金叉死叉
if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
    print("MACD金叉信号！")
```

##### calculate_bollinger_bands()
```python
def calculate_bollinger_bands(
    self,
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
    ma_type: str = 'sma'
) -> IndicatorResult
```

**参数**:
- `prices` (pd.Series): 价格序列
- `period` (int): 移动平均周期，默认20
- `std_dev` (float): 标准差倍数，默认2.0
- `ma_type` (str): 移动平均类型，'sma'或'ema'

**返回**: `IndicatorResult` 对象，包含上轨、中轨、下轨

##### calculate_multiple_indicators()
```python
def calculate_multiple_indicators(
    self,
    price_data: pd.Series,
    indicator_list: List[str],
    **kwargs
) -> Dict[str, IndicatorResult]
```

**参数**:
- `price_data` (pd.Series): 价格数据
- `indicator_list` (List[str]): 指标名称列表
- `**kwargs`: 各指标的参数

**可用指标**:
- `'rsi'`: 相对强弱指数
- `'macd'`: MACD指标
- `'bollinger_bands'`: 布林带
- `'stochastic'`: 随机指标
- `'williams_r'`: 威廉指标
- `'cci'`: 顺势指标
- `'atr'`: 平均真实波幅
- `'adx'`: 平均趋向指标

**示例**:
```python
multi_results = indicators.calculate_multiple_indicators(
    stock_prices,
    ['rsi', 'macd', 'bollinger_bands'],
    rsi_period=14,
    macd_fast_period=12,
    bollinger_period=20
)

for indicator_name, result in multi_results.items():
    print(f"{indicator_name}: {result.interpretation}")
```

### StatisticalAnalyzer 类

**功能**: 统计分析和数据挖掘

#### 初始化
```python
from advanced_analytics.statistical_analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(
    confidence_level=0.95,    # 置信水平
    random_state=42          # 随机种子
)
```

#### 核心方法

##### calculate_correlation_analysis()
```python
def calculate_correlation_analysis(
    self,
    data1: pd.Series,
    data2: pd.Series,
    method: str = 'pearson',
    test_significance: bool = True
) -> AnalysisResult
```

**参数**:
- `data1, data2` (pd.Series): 待分析的数据序列
- `method` (str): 相关性方法，'pearson'、'spearman'、'kendall'
- `test_significance` (bool): 是否进行显著性检验

**示例**:
```python
correlation_result = analyzer.calculate_correlation_analysis(
    stock1_returns, stock2_returns, method='pearson'
)

print(f"相关系数: {correlation_result.results['correlation']:.3f}")
print(f"P值: {correlation_result.results['p_value']:.4f}")
print(f"显著性: {'显著' if correlation_result.results['p_value'] < 0.05 else '不显著'}")
```

##### perform_regression_analysis()
```python
def perform_regression_analysis(
    self,
    dependent_var: pd.Series,
    independent_vars: pd.DataFrame,
    method: str = 'ols',
    include_diagnostics: bool = True
) -> AnalysisResult
```

**参数**:
- `dependent_var` (pd.Series): 因变量
- `independent_vars` (pd.DataFrame): 自变量
- `method` (str): 回归方法，'ols'、'ridge'、'lasso'
- `include_diagnostics` (bool): 是否包含诊断信息

##### analyze_distribution()
```python
def analyze_distribution(
    self,
    data: pd.Series,
    test_normality: bool = True,
    calculate_moments: bool = True,
    fit_distributions: List[str] = None
) -> AnalysisResult
```

**参数**:
- `data` (pd.Series): 待分析数据
- `test_normality` (bool): 是否进行正态性检验
- `calculate_moments` (bool): 是否计算矩统计量
- `fit_distributions` (List[str]): 待拟合的分布类型

### AnomalyDetectionEngine 类

**功能**: 多算法异常检测

#### 核心方法

##### detect_anomalies_isolation_forest()
```python
def detect_anomalies_isolation_forest(
    self,
    data: pd.DataFrame,
    contamination: float = 0.1,
    features: List[str] = None,
    random_state: int = 42
) -> AnomalyResult
```

**参数**:
- `data` (pd.DataFrame): 输入数据
- `contamination` (float): 异常值比例估计
- `features` (List[str]): 用于检测的特征列
- `random_state` (int): 随机种子

##### detect_statistical_anomalies()
```python
def detect_statistical_anomalies(
    self,
    data: pd.Series,
    method: str = 'z_score',
    threshold: float = 3.0,
    window_size: int = None
) -> AnomalyResult
```

**参数**:
- `data` (pd.Series): 输入数据
- `method` (str): 检测方法，'z_score'、'iqr'、'modified_z_score'
- `threshold` (float): 异常阈值
- `window_size` (int): 滚动窗口大小（用于滚动检测）

---

## 🤖 机器学习集成 API

### PredictionEngine 类

**功能**: 多算法价格预测引擎

#### 初始化
```python
from ml_integration.price_prediction import PredictionEngine

prediction_engine = PredictionEngine(
    random_state=42,          # 随机种子
    validation_split=0.2,     # 验证集比例
    early_stopping=True       # 是否启用早停
)
```

#### 核心方法

##### train_model()
```python
def train_model(
    self,
    features: pd.DataFrame,
    config: ModelConfig,
    save_model: bool = True,
    model_name: str = None
) -> MLModel
```

**参数**:
- `features` (pd.DataFrame): 特征数据
- `config` (ModelConfig): 模型配置
- `save_model` (bool): 是否保存模型
- `model_name` (str): 模型名称

**示例**:
```python
from ml_integration import ModelConfig, ModelType, PredictionType

config = ModelConfig(
    model_type=ModelType.RANDOM_FOREST,
    prediction_type=PredictionType.PRICE,
    parameters={
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5
    },
    feature_columns=['rsi', 'macd', 'volume_ratio'],
    target_column='future_return_5d'
)

model = prediction_engine.train_model(features, config)
print(f"模型训练完成，R²得分: {model.performance_metrics.r2_score:.3f}")
```

##### predict()
```python
def predict(
    self,
    model: MLModel,
    input_data: pd.DataFrame,
    prediction_horizon: int = 1,
    return_probabilities: bool = False
) -> ModelPrediction
```

##### predict_ensemble()
```python
def predict_ensemble(
    self,
    features: pd.DataFrame,
    models: List[MLModel],
    ensemble_method: str = 'voting',
    weights: List[float] = None
) -> ModelPrediction
```

**参数**:
- `features` (pd.DataFrame): 输入特征
- `models` (List[MLModel]): 模型列表
- `ensemble_method` (str): 集成方法，'voting'、'averaging'、'stacking'
- `weights` (List[float]): 模型权重

##### backtest_model()
```python
def backtest_model(
    self,
    model: MLModel,
    test_data: pd.DataFrame,
    start_date: str = None,
    end_date: str = None,
    transaction_cost: float = 0.001
) -> BacktestResult
```

### FeatureEngineer 类

**功能**: 特征工程和数据预处理

#### 核心方法

##### add_technical_features()
```python
def add_technical_features(
    self,
    price_data: pd.DataFrame,
    indicators: List[str] = None,
    periods: Dict[str, List[int]] = None
) -> pd.DataFrame
```

**参数**:
- `price_data` (pd.DataFrame): 价格数据(OHLCV)
- `indicators` (List[str]): 技术指标列表
- `periods` (Dict): 各指标的计算周期

**可用指标**:
```python
default_indicators = [
    'rsi', 'macd', 'bollinger_bands', 'stochastic',
    'williams_r', 'cci', 'atr', 'adx', 'obv', 'mfi'
]
```

##### add_market_features()
```python
def add_market_features(
    self,
    features: pd.DataFrame,
    market_data: pd.DataFrame,
    economic_indicators: pd.DataFrame = None
) -> pd.DataFrame
```

##### create_lag_features()
```python
def create_lag_features(
    self,
    data: pd.DataFrame,
    columns: List[str],
    lags: List[int],
    include_rolling_stats: bool = True
) -> pd.DataFrame
```

### TrendAnalysisEngine 类

**功能**: 趋势分析和变化点检测

#### 核心方法

##### analyze_trend_multi_algorithm()
```python
def analyze_trend_multi_algorithm(
    self,
    price_data: pd.Series,
    algorithms: List[str] = None,
    confidence_threshold: float = 0.7
) -> TrendAnalysisResult
```

**可用算法**:
- `'linear_regression'`: 线性回归趋势
- `'polynomial'`: 多项式拟合
- `'moving_average'`: 移动平均趋势
- `'exponential_smoothing'`: 指数平滑
- `'hodrick_prescott'`: HP滤波

##### detect_trend_changes()
```python
def detect_trend_changes(
    self,
    data: pd.Series,
    method: str = 'pelt',
    sensitivity: float = 0.1,
    min_segment_length: int = 10
) -> ChangePointResult
```

**变化点检测方法**:
- `'pelt'`: PELT算法
- `'binary_segmentation'`: 二分法
- `'window_based'`: 滑窗法
- `'cusum'`: CUSUM控制图

---

## 📊 投资组合分析 API

### PortfolioOptimizer 类

**功能**: 现代投资组合理论优化

#### 初始化
```python
from portfolio_analytics.portfolio_optimizer import PortfolioOptimizer

optimizer = PortfolioOptimizer(
    risk_free_rate=0.02,      # 无风险利率
    max_iterations=1000,      # 最大迭代次数
    tolerance=1e-8,           # 收敛容忍度
    solver='SLSQP'           # 优化求解器
)
```

#### 核心方法

##### optimize_portfolio()
```python
def optimize_portfolio(
    self,
    assets: Dict[str, AssetData],
    method: OptimizationMethod,
    constraints: OptimizationConstraints = None,
    objective_params: Dict = None
) -> OptimizationResult
```

**参数**:
- `assets` (Dict[str, AssetData]): 资产数据字典
- `method` (OptimizationMethod): 优化方法
- `constraints` (OptimizationConstraints): 约束条件
- `objective_params` (Dict): 目标函数参数

**优化方法**:
```python
from portfolio_analytics import OptimizationMethod

# 可用的优化方法
OptimizationMethod.MINIMUM_VARIANCE      # 最小方差
OptimizationMethod.MAXIMUM_SHARPE        # 最大夏普比率
OptimizationMethod.MAXIMUM_RETURN        # 最大收益
OptimizationMethod.RISK_PARITY          # 风险平价
OptimizationMethod.MAXIMUM_DIVERSIFICATION  # 最大分散化
OptimizationMethod.MINIMUM_CVaR          # 最小条件风险价值
```

**示例**:
```python
from portfolio_analytics import OptimizationConstraints

# 设置约束条件
constraints = OptimizationConstraints(
    min_weight=0.05,          # 最小权重5%
    max_weight=0.40,          # 最大权重40%
    max_assets=10,            # 最多10个资产
    sector_constraints={      # 行业约束
        'Technology': 0.50,   # 科技股最多50%
        'Healthcare': 0.30    # 医疗股最多30%
    },
    turnover_constraint=0.20  # 换手率约束20%
)

# 执行优化
result = optimizer.optimize_portfolio(
    assets=asset_universe,
    method=OptimizationMethod.MAXIMUM_SHARPE,
    constraints=constraints
)

# 查看结果
if result.optimization_status == "success":
    print(f"最优夏普比率: {result.sharpe_ratio:.3f}")
    print("最优权重分配:")
    for asset, weight in result.optimal_weights.items():
        print(f"  {asset}: {weight:.1%}")
else:
    print(f"优化失败: {result.optimization_status}")
```

##### calculate_efficient_frontier()
```python
def calculate_efficient_frontier(
    self,
    assets: Dict[str, AssetData],
    n_portfolios: int = 100,
    constraints: OptimizationConstraints = None,
    return_range: Tuple[float, float] = None
) -> List[OptimizationResult]
```

**参数**:
- `n_portfolios` (int): 有效前沿组合数量
- `return_range` (Tuple): 收益率范围(min_return, max_return)

### RiskAnalyzer 类

**功能**: 全面的风险分析和管理

#### 初始化
```python
from portfolio_analytics.risk_analyzer import RiskAnalyzer

risk_analyzer = RiskAnalyzer(
    confidence_levels=[0.95, 0.99],  # VaR置信水平
    time_horizon=1,                  # 风险时间范围(天)
    bootstrap_samples=1000           # Bootstrap样本数
)
```

#### 核心方法

##### calculate_portfolio_risk_metrics()
```python
def calculate_portfolio_risk_metrics(
    self,
    portfolio: Portfolio,
    benchmark: pd.Series = None
) -> RiskMetrics
```

**返回的风险指标**:
- `portfolio_volatility`: 年化波动率
- `var_95`, `var_99`: 风险价值(95%、99%置信水平)
- `cvar_95`, `cvar_99`: 条件风险价值
- `max_drawdown`: 最大回撤
- `sortino_ratio`: Sortino比率
- `calmar_ratio`: Calmar比率
- `beta`: 贝塔系数(相对基准)
- `tracking_error`: 跟踪误差

**示例**:
```python
risk_metrics = risk_analyzer.calculate_portfolio_risk_metrics(portfolio)

print(f"投资组合风险分析:")
print(f"  年化波动率: {risk_metrics.portfolio_volatility:.2%}")
print(f"  VaR (95%): {risk_metrics.var_95:.2%}")
print(f"  最大回撤: {risk_metrics.max_drawdown:.2%}")
print(f"  Sortino比率: {risk_metrics.sortino_ratio:.3f}")

# 风险评估
if risk_metrics.portfolio_volatility > 0.20:
    print("⚠️ 警告: 投资组合波动率较高")
if risk_metrics.max_drawdown < -0.15:
    print("⚠️ 警告: 最大回撤超过15%")
```

##### calculate_var()
```python
def calculate_var(
    self,
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: VaRMethod = VaRMethod.HISTORICAL
) -> float
```

**VaR计算方法**:
```python
from portfolio_analytics.risk_analyzer import VaRMethod

VaRMethod.HISTORICAL        # 历史模拟法
VaRMethod.PARAMETRIC       # 参数法(正态分布假设)
VaRMethod.MONTE_CARLO      # 蒙特卡洛模拟
VaRMethod.CORNISH_FISHER   # Cornish-Fisher展开
```

##### calculate_component_var()
```python
def calculate_component_var(
    self,
    portfolio: Portfolio,
    confidence_level: float = 0.95
) -> Dict[str, float]
```

**返回**: 各资产对投资组合VaR的贡献度

##### stress_test()
```python
def stress_test(
    self,
    portfolio: Portfolio,
    stress_type: StressTestType,
    stress_parameters: Dict
) -> Dict[str, float]
```

**压力测试类型**:
```python
from portfolio_analytics.risk_analyzer import StressTestType

StressTestType.FACTOR_SHOCK     # 因子冲击
StressTestType.HISTORICAL       # 历史情景
StressTestType.MONTE_CARLO      # 蒙特卡洛压力测试
StressTestType.TAIL_RISK        # 尾部风险情景
```

**示例**:
```python
# 市场下跌压力测试
stress_params = {
    'market_shock': -0.30,      # 市场下跌30%
    'volatility_shock': 2.0,    # 波动率上升2倍
    'correlation_shock': 0.1    # 相关性增加0.1
}

stress_result = risk_analyzer.stress_test(
    portfolio, 
    StressTestType.FACTOR_SHOCK, 
    stress_params
)

print(f"压力测试结果:")
print(f"  投资组合损失: {stress_result['portfolio_loss_pct']:.1%}")
print(f"  风险调整收益: {stress_result['risk_adjusted_return']:.3f}")
```

### PerformanceAnalyzer 类

**功能**: 绩效分析和归因

#### 核心方法

##### calculate_performance_metrics()
```python
def calculate_performance_metrics(
    self,
    portfolio: Portfolio,
    benchmark: pd.Series,
    risk_free_rate: float = None
) -> Dict[str, float]
```

**返回的绩效指标**:
- `total_return`: 总收益率
- `annualized_return`: 年化收益率
- `volatility`: 年化波动率
- `sharpe_ratio`: 夏普比率
- `information_ratio`: 信息比率
- `alpha`: Alpha系数
- `beta`: Beta系数
- `max_drawdown`: 最大回撤
- `calmar_ratio`: Calmar比率

##### brinson_attribution()
```python
def brinson_attribution(
    self,
    portfolio_weights: Dict[str, float],
    benchmark_weights: Dict[str, float],
    portfolio_returns: Dict[str, float],
    benchmark_returns: Dict[str, float],
    sector_mapping: Dict[str, str] = None
) -> BrinsonAttribution
```

**Brinson归因分析**:
- `allocation_effect`: 资产配置效应
- `asset_selection`: 证券选择效应  
- `interaction_effect`: 交互效应
- `active_return`: 主动收益
- `sector_attribution`: 行业归因(如提供sector_mapping)

**示例**:
```python
attribution = performance_analyzer.brinson_attribution(
    portfolio_weights=current_weights,
    benchmark_weights=benchmark_weights,
    portfolio_returns=period_returns,
    benchmark_returns=benchmark_period_returns,
    sector_mapping={'AAPL': 'Technology', 'JPM': 'Financial'}
)

print(f"Brinson归因分析:")
print(f"  资产配置效应: {attribution.allocation_effect:.4f}")
print(f"  证券选择效应: {attribution.asset_selection:.4f}")
print(f"  交互效应: {attribution.interaction_effect:.4f}")
print(f"  主动收益: {attribution.active_return:.4f}")

# 行业级归因
if attribution.sector_attribution:
    print(f"\n行业归因:")
    for sector, attr in attribution.sector_attribution.items():
        print(f"  {sector}: {attr['total']:.4f}")
```

---

## 📋 数据结构参考

### AssetData
```python
@dataclass
class AssetData:
    symbol: str                    # 股票代码
    returns: pd.Series            # 收益率序列
    prices: pd.Series             # 价格序列
    sector: str = None            # 所属行业
    market_cap: float = None      # 市值
    beta: float = None            # 贝塔系数
    
    def get_statistics(self) -> Dict[str, float]:
        """获取基础统计信息"""
        pass
        
    def calculate_rolling_metrics(self, window: int) -> pd.DataFrame:
        """计算滚动指标"""
        pass
```

### Portfolio
```python
@dataclass
class Portfolio:
    name: str                           # 投资组合名称
    weights: Dict[str, float]          # 权重分配
    assets: Dict[str, AssetData]       # 资产数据
    inception_date: datetime           # 成立日期
    rebalance_frequency: str = 'monthly'  # 再平衡频率
    
    def get_portfolio_returns(self) -> pd.Series:
        """获取投资组合收益率"""
        pass
        
    def get_portfolio_statistics(self) -> Dict[str, float]:
        """获取投资组合统计信息"""
        pass
        
    def validate_weights(self) -> bool:
        """验证权重有效性"""
        pass
```

### OptimizationResult
```python
@dataclass
class OptimizationResult:
    optimal_weights: Dict[str, float]    # 最优权重
    expected_return: float               # 期望收益
    expected_risk: float                # 期望风险
    sharpe_ratio: float                 # 夏普比率
    optimization_status: str            # 优化状态
    objective_value: float              # 目标函数值
    optimization_time: float           # 优化耗时
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        pass
        
    def save_to_file(self, filepath: str):
        """保存到文件"""
        pass
```

### ModelConfig
```python
@dataclass
class ModelConfig:
    model_type: ModelType              # 模型类型
    prediction_type: PredictionType    # 预测类型
    parameters: Dict                   # 模型参数
    feature_columns: List[str]         # 特征列
    target_column: str                # 目标列
    validation_method: str = 'time_series'  # 验证方法
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        pass
        
    @classmethod
    def from_dict(cls, config_dict: Dict):
        """从字典创建"""
        pass
```

---

## ⚙️ 配置选项

### 全局配置
```python
# config.py
import os

class Config:
    # 数据配置
    DATA_CACHE_DIR = os.path.expanduser("~/.quant_cache")
    CACHE_EXPIRY_HOURS = 24
    
    # 计算配置
    PARALLEL_JOBS = -1              # 并行任务数(-1为所有CPU)
    CHUNK_SIZE = 1000              # 数据块大小
    
    # 优化配置
    OPTIMIZATION_TIMEOUT = 300      # 优化超时(秒)
    MAX_ITERATIONS = 1000          # 最大迭代次数
    TOLERANCE = 1e-8               # 收敛容忍度
    
    # 风险配置
    DEFAULT_CONFIDENCE_LEVELS = [0.95, 0.99]
    VAR_BOOTSTRAP_SAMPLES = 1000
    STRESS_TEST_SCENARIOS = 1000
    
    # ML配置
    VALIDATION_SPLIT = 0.2
    EARLY_STOPPING_PATIENCE = 10
    CROSS_VALIDATION_FOLDS = 5
    
    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 环境变量
```bash
# .env 文件
QUANT_DATA_SOURCE=yahoo           # 数据源
QUANT_CACHE_DIR=/path/to/cache   # 缓存目录
QUANT_LOG_LEVEL=INFO             # 日志级别
QUANT_PARALLEL_JOBS=4            # 并行任务数
QUANT_RISK_FREE_RATE=0.02        # 无风险利率
```

### 使用配置
```python
from config import Config
import os

# 更新配置
Config.PARALLEL_JOBS = int(os.getenv('QUANT_PARALLEL_JOBS', -1))
Config.DATA_CACHE_DIR = os.getenv('QUANT_CACHE_DIR', Config.DATA_CACHE_DIR)

# 在组件中使用
optimizer = PortfolioOptimizer(
    max_iterations=Config.MAX_ITERATIONS,
    tolerance=Config.TOLERANCE
)
```

---

## 📞 技术支持

### 错误处理示例
```python
try:
    result = optimizer.optimize_portfolio(assets, method, constraints)
    if result.optimization_status != "success":
        logger.warning(f"优化警告: {result.optimization_status}")
        # 实施回退策略
        
except OptimizationError as e:
    logger.error(f"优化失败: {e}")
    # 错误处理逻辑
    
except InsufficientDataError as e:
    logger.error(f"数据不足: {e}")
    # 数据处理逻辑
```

### 性能监控
```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        if execution_time > 60:  # 超过1分钟
            logger.warning(f"{func.__name__} 执行时间较长: {execution_time:.2f}秒")
            
        return result
    return wrapper

# 使用装饰器
@monitor_performance
def expensive_calculation():
    pass
```

---

*API文档版本: v1.0 | 最后更新: 2025年10月1日*