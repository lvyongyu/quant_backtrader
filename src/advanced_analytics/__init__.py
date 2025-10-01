"""
高级数据分析和可视化模块

提供企业级的数据分析和可视化能力：
1. 高级技术指标库
2. 统计分析工具
3. 相关性和回归分析
4. 异常检测系统
5. 交互式图表引擎
6. 市场洞察报告生成器
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class IndicatorType(Enum):
    """技术指标类型"""
    TREND = "trend"                    # 趋势指标
    MOMENTUM = "momentum"              # 动量指标
    VOLATILITY = "volatility"          # 波动率指标
    VOLUME = "volume"                  # 成交量指标
    SUPPORT_RESISTANCE = "support_resistance"  # 支撑阻力


class AnalysisType(Enum):
    """分析类型"""
    TECHNICAL = "technical"            # 技术分析
    STATISTICAL = "statistical"       # 统计分析
    CORRELATION = "correlation"        # 相关性分析
    REGRESSION = "regression"          # 回归分析
    ANOMALY = "anomaly"               # 异常检测


@dataclass
class IndicatorResult:
    """技术指标结果"""
    name: str
    type: IndicatorType
    values: Union[pd.Series, Dict[str, pd.Series]]
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            'name': self.name,
            'type': self.type.value,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat()
        }
        
        if isinstance(self.values, pd.Series):
            result['values'] = self.values.to_dict()
        else:
            result['values'] = {k: v.to_dict() for k, v in self.values.items()}
        
        return result


@dataclass
class AnalysisResult:
    """分析结果"""
    analysis_type: AnalysisType
    symbol: str
    result_data: Dict[str, Any]
    confidence_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'analysis_type': self.analysis_type.value,
            'symbol': self.symbol,
            'result_data': self.result_data,
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class MarketInsight:
    """市场洞察"""
    title: str
    description: str
    insight_type: str
    importance_score: float  # 0-1
    affected_symbols: List[str]
    supporting_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'title': self.title,
            'description': self.description,
            'insight_type': self.insight_type,
            'importance_score': self.importance_score,
            'affected_symbols': self.affected_symbols,
            'supporting_data': self.supporting_data,
            'timestamp': self.timestamp.isoformat()
        }


# 导出主要接口
__all__ = [
    'IndicatorType', 'AnalysisType',
    'IndicatorResult', 'AnalysisResult', 'MarketInsight'
]