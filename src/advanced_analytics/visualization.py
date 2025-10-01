"""
高级可视化系统

提供专业的金融数据可视化功能：
1. 技术分析图表
2. 统计分析可视化
3. 异常检测可视化
4. 交互式图表
5. 报告生成
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import warnings

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn("matplotlib not available, visualization will be limited")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    warnings.warn("plotly not available, interactive charts will be limited")

from . import IndicatorResult, AnalysisResult
from .anomaly_detection import AnomalyReport, AnomalyPoint, AnomalySeverity


class ChartType(Enum):
    """图表类型"""
    CANDLESTICK = "candlestick"
    LINE = "line"
    BAR = "bar"
    VOLUME = "volume"
    INDICATOR = "indicator"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    DISTRIBUTION = "distribution"


class ChartStyle(Enum):
    """图表样式"""
    CLASSIC = "classic"
    MODERN = "modern"
    DARK = "dark"
    MINIMAL = "minimal"


@dataclass
class ChartConfig:
    """图表配置"""
    title: str = ""
    width: int = 1200
    height: int = 600
    style: ChartStyle = ChartStyle.MODERN
    show_legend: bool = True
    show_grid: bool = True
    interactive: bool = True
    color_scheme: Optional[List[str]] = None
    
    def get_colors(self) -> List[str]:
        """获取颜色方案"""
        if self.color_scheme:
            return self.color_scheme
        
        if self.style == ChartStyle.DARK:
            return ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        elif self.style == ChartStyle.MINIMAL:
            return ['#2E8B57', '#4682B4', '#DC143C', '#FF8C00', '#9932CC', '#8B4513']
        else:
            return ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']


class TechnicalChartBuilder:
    """技术分析图表构建器"""
    
    def __init__(self, config: ChartConfig = None):
        self.config = config or ChartConfig()
    
    def create_candlestick_chart(self, df: pd.DataFrame, 
                               indicators: Optional[Dict[str, pd.Series]] = None,
                               volume: bool = True) -> Any:
        """创建K线图"""
        if not PLOTLY_AVAILABLE:
            return self._create_matplotlib_candlestick(df, indicators, volume)
        
        # 创建子图
        rows = 2 if volume else 1
        row_heights = [0.7, 0.3] if volume else [1.0]
        
        fig = make_subplots(
            rows=rows, cols=1,
            row_heights=row_heights,
            shared_xaxes=True,
            vertical_spacing=0.02,
            subplot_titles=['Price Chart', 'Volume'] if volume else ['Price Chart']
        )
        
        # K线图
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'] if 'open' in df.columns else df['Open'],
                high=df['high'] if 'high' in df.columns else df['High'],
                low=df['low'] if 'low' in df.columns else df['Low'],
                close=df['close'] if 'close' in df.columns else df['Close'],
                name='Price',
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )
        
        # 添加技术指标
        if indicators:
            colors = self.config.get_colors()
            for i, (name, data) in enumerate(indicators.items()):
                color = colors[i % len(colors)]
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data.values,
                        mode='lines',
                        name=name,
                        line=dict(color=color, width=2)
                    ),
                    row=1, col=1
                )
        
        # 成交量图
        if volume and 'volume' in df.columns:
            volume_data = df['volume']
        elif volume and 'Volume' in df.columns:
            volume_data = df['Volume']
        else:
            volume_data = None
            
        if volume and volume_data is not None:
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=volume_data,
                    name='Volume',
                    marker_color='lightblue',
                    opacity=0.7
                ),
                row=2, col=1
            )
        
        # 更新布局
        fig.update_layout(
            title=self.config.title,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            xaxis_rangeslider_visible=False,
            template='plotly_dark' if self.config.style == ChartStyle.DARK else 'plotly_white'
        )
        
        if self.config.show_grid:
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        return fig
    
    def create_indicator_chart(self, indicators: Dict[str, pd.Series],
                             chart_type: ChartType = ChartType.LINE) -> Any:
        """创建指标图表"""
        if not PLOTLY_AVAILABLE:
            return self._create_matplotlib_indicators(indicators)
        
        fig = go.Figure()
        colors = self.config.get_colors()
        
        for i, (name, data) in enumerate(indicators.items()):
            color = colors[i % len(colors)]
            
            if chart_type == ChartType.LINE:
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=data.values,
                        mode='lines',
                        name=name,
                        line=dict(color=color, width=2)
                    )
                )
            elif chart_type == ChartType.BAR:
                fig.add_trace(
                    go.Bar(
                        x=data.index,
                        y=data.values,
                        name=name,
                        marker_color=color,
                        opacity=0.7
                    )
                )
        
        fig.update_layout(
            title=self.config.title,
            width=self.config.width,
            height=self.config.height,
            showlegend=self.config.show_legend,
            template='plotly_dark' if self.config.style == ChartStyle.DARK else 'plotly_white'
        )
        
        return fig
    
    def _create_matplotlib_candlestick(self, df: pd.DataFrame,
                                     indicators: Optional[Dict[str, pd.Series]] = None,
                                     volume: bool = True) -> plt.Figure:
        """使用matplotlib创建K线图"""
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for chart creation")
        
        fig, axes = plt.subplots(2 if volume else 1, 1, 
                               figsize=(self.config.width/100, self.config.height/100),
                               sharex=True)
        
        if volume:
            ax_price, ax_volume = axes
        else:
            ax_price = axes
        
        # 简化的K线图（使用线图代替）
        close_col = 'close' if 'close' in df.columns else 'Close'
        ax_price.plot(df.index, df[close_col], label='Close Price', linewidth=2)
        
        # 添加技术指标
        if indicators:
            colors = self.config.get_colors()
            for i, (name, data) in enumerate(indicators.items()):
                color = colors[i % len(colors)]
                ax_price.plot(data.index, data.values, label=name, color=color, linewidth=1.5)
        
        ax_price.set_title(self.config.title)
        ax_price.legend()
        ax_price.grid(self.config.show_grid)
        
        # 成交量图
        if volume:
            volume_col = 'volume' if 'volume' in df.columns else 'Volume'
            if volume_col in df.columns:
                ax_volume.bar(df.index, df[volume_col], alpha=0.7, color='lightblue')
                ax_volume.set_ylabel('Volume')
                ax_volume.grid(self.config.show_grid)
        
        plt.tight_layout()
        return fig


class StatisticalChartBuilder:
    """统计分析图表构建器"""
    
    def __init__(self, config: ChartConfig = None):
        self.config = config or ChartConfig()
    
    def create_correlation_heatmap(self, correlation_matrix: pd.DataFrame) -> Any:
        """创建相关性热力图"""
        if PLOTLY_AVAILABLE and self.config.interactive:
            fig = go.Figure(data=go.Heatmap(
                z=correlation_matrix.values,
                x=correlation_matrix.columns,
                y=correlation_matrix.index,
                colorscale='RdBu',
                zmid=0,
                text=correlation_matrix.round(3).values,
                texttemplate='%{text}',
                textfont={'size': 10}
            ))
            
            fig.update_layout(
                title=self.config.title or 'Correlation Heatmap',
                width=self.config.width,
                height=self.config.height
            )
            
            return fig
        
        elif MATPLOTLIB_AVAILABLE:
            fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100))
            
            if 'seaborn' in globals():
                sns.heatmap(correlation_matrix, annot=True, cmap='RdBu', center=0,
                           square=True, ax=ax, fmt='.3f')
            else:
                im = ax.imshow(correlation_matrix.values, cmap='RdBu', aspect='auto')
                ax.set_xticks(range(len(correlation_matrix.columns)))
                ax.set_yticks(range(len(correlation_matrix.index)))
                ax.set_xticklabels(correlation_matrix.columns, rotation=45)
                ax.set_yticklabels(correlation_matrix.index)
                plt.colorbar(im, ax=ax)
            
            ax.set_title(self.config.title or 'Correlation Heatmap')
            plt.tight_layout()
            return fig
        
        else:
            raise ImportError("Either plotly or matplotlib is required for visualization")
    
    def create_distribution_plot(self, data: pd.Series, bins: int = 50) -> Any:
        """创建分布图"""
        if PLOTLY_AVAILABLE and self.config.interactive:
            fig = go.Figure()
            
            # 直方图
            fig.add_trace(go.Histogram(
                x=data.values,
                nbinsx=bins,
                name='Distribution',
                opacity=0.7,
                marker_color=self.config.get_colors()[0]
            ))
            
            # 正态分布拟合
            mean_val = data.mean()
            std_val = data.std()
            x_norm = np.linspace(data.min(), data.max(), 100)
            y_norm = (1/(std_val * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean_val) / std_val) ** 2)
            
            # 标准化y轴到直方图比例
            hist_max = len(data) / bins * (data.max() - data.min())
            y_norm = y_norm * hist_max / y_norm.max()
            
            fig.add_trace(go.Scatter(
                x=x_norm,
                y=y_norm,
                mode='lines',
                name='Normal Fit',
                line=dict(color='red', width=2)
            ))
            
            fig.update_layout(
                title=self.config.title or f'Distribution of {data.name}',
                xaxis_title='Value',
                yaxis_title='Frequency',
                width=self.config.width,
                height=self.config.height,
                showlegend=self.config.show_legend
            )
            
            return fig
        
        elif MATPLOTLIB_AVAILABLE:
            fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100))
            
            # 直方图
            ax.hist(data.values, bins=bins, alpha=0.7, density=True, 
                   color=self.config.get_colors()[0], label='Data')
            
            # 正态分布拟合
            mean_val = data.mean()
            std_val = data.std()
            x_norm = np.linspace(data.min(), data.max(), 100)
            y_norm = (1/(std_val * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean_val) / std_val) ** 2)
            ax.plot(x_norm, y_norm, 'r-', linewidth=2, label='Normal Fit')
            
            ax.set_title(self.config.title or f'Distribution of {data.name}')
            ax.set_xlabel('Value')
            ax.set_ylabel('Density')
            ax.legend()
            ax.grid(self.config.show_grid)
            
            plt.tight_layout()
            return fig
        
        else:
            raise ImportError("Either plotly or matplotlib is required for visualization")
    
    def create_scatter_plot(self, x_data: pd.Series, y_data: pd.Series,
                          trend_line: bool = True) -> Any:
        """创建散点图"""
        if PLOTLY_AVAILABLE and self.config.interactive:
            fig = go.Figure()
            
            # 散点图
            fig.add_trace(go.Scatter(
                x=x_data.values,
                y=y_data.values,
                mode='markers',
                name='Data Points',
                marker=dict(
                    color=self.config.get_colors()[0],
                    size=6,
                    opacity=0.7
                )
            ))
            
            # 趋势线
            if trend_line:
                z = np.polyfit(x_data.values, y_data.values, 1)
                p = np.poly1d(z)
                fig.add_trace(go.Scatter(
                    x=x_data.values,
                    y=p(x_data.values),
                    mode='lines',
                    name='Trend Line',
                    line=dict(color='red', width=2)
                ))
            
            fig.update_layout(
                title=self.config.title or f'{y_data.name} vs {x_data.name}',
                xaxis_title=x_data.name,
                yaxis_title=y_data.name,
                width=self.config.width,
                height=self.config.height,
                showlegend=self.config.show_legend
            )
            
            return fig
        
        elif MATPLOTLIB_AVAILABLE:
            fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100))
            
            # 散点图
            ax.scatter(x_data.values, y_data.values, 
                      color=self.config.get_colors()[0], alpha=0.7, s=50)
            
            # 趋势线
            if trend_line:
                z = np.polyfit(x_data.values, y_data.values, 1)
                p = np.poly1d(z)
                ax.plot(x_data.values, p(x_data.values), 'r-', linewidth=2, label='Trend Line')
                ax.legend()
            
            ax.set_title(self.config.title or f'{y_data.name} vs {x_data.name}')
            ax.set_xlabel(x_data.name)
            ax.set_ylabel(y_data.name)
            ax.grid(self.config.show_grid)
            
            plt.tight_layout()
            return fig
        
        else:
            raise ImportError("Either plotly or matplotlib is required for visualization")


class AnomalyVisualization:
    """异常检测可视化"""
    
    def __init__(self, config: ChartConfig = None):
        self.config = config or ChartConfig()
    
    def plot_anomalies_on_timeseries(self, data: pd.Series,
                                   anomalies: List[AnomalyPoint]) -> Any:
        """在时间序列上标注异常点"""
        if PLOTLY_AVAILABLE and self.config.interactive:
            fig = go.Figure()
            
            # 原始数据
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data.values,
                mode='lines',
                name='Data',
                line=dict(color='blue', width=2)
            ))
            
            # 异常点
            if anomalies:
                anomaly_times = [a.timestamp for a in anomalies]
                anomaly_values = [a.value for a in anomalies]
                anomaly_colors = [self._severity_to_color(a.severity) for a in anomalies]
                anomaly_text = [f"Score: {a.score:.2f}<br>{a.description}" for a in anomalies]
                
                fig.add_trace(go.Scatter(
                    x=anomaly_times,
                    y=anomaly_values,
                    mode='markers',
                    name='Anomalies',
                    marker=dict(
                        color=anomaly_colors,
                        size=10,
                        symbol='x',
                        line=dict(width=2)
                    ),
                    text=anomaly_text,
                    hovertemplate='%{text}<extra></extra>'
                ))
            
            fig.update_layout(
                title=self.config.title or 'Anomaly Detection Results',
                xaxis_title='Time',
                yaxis_title='Value',
                width=self.config.width,
                height=self.config.height,
                showlegend=self.config.show_legend
            )
            
            return fig
        
        elif MATPLOTLIB_AVAILABLE:
            fig, ax = plt.subplots(figsize=(self.config.width/100, self.config.height/100))
            
            # 原始数据
            ax.plot(data.index, data.values, 'b-', linewidth=2, label='Data')
            
            # 异常点
            if anomalies:
                for anomaly in anomalies:
                    color = self._severity_to_color(anomaly.severity)
                    ax.scatter(anomaly.timestamp, anomaly.value, 
                             color=color, s=100, marker='x', linewidth=3,
                             label=f'{anomaly.severity.value} anomaly' if anomaly == anomalies[0] else "")
            
            ax.set_title(self.config.title or 'Anomaly Detection Results')
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.legend()
            ax.grid(self.config.show_grid)
            
            plt.tight_layout()
            return fig
        
        else:
            raise ImportError("Either plotly or matplotlib is required for visualization")
    
    def create_anomaly_summary_chart(self, report: AnomalyReport) -> Any:
        """创建异常检测摘要图表"""
        if not report.anomalies:
            return None
        
        if PLOTLY_AVAILABLE and self.config.interactive:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=['Severity Distribution', 'Type Distribution', 
                              'Anomaly Timeline', 'Score Distribution'],
                specs=[[{"type": "pie"}, {"type": "pie"}],
                       [{"type": "scatter"}, {"type": "histogram"}]]
            )
            
            # 严重程度分布
            severity_counts = {}
            for anomaly in report.anomalies:
                severity_counts[anomaly.severity.value] = severity_counts.get(anomaly.severity.value, 0) + 1
            
            fig.add_trace(go.Pie(
                labels=list(severity_counts.keys()),
                values=list(severity_counts.values()),
                name="Severity"
            ), row=1, col=1)
            
            # 类型分布
            type_counts = {}
            for anomaly in report.anomalies:
                type_counts[anomaly.anomaly_type.value] = type_counts.get(anomaly.anomaly_type.value, 0) + 1
            
            fig.add_trace(go.Pie(
                labels=list(type_counts.keys()),
                values=list(type_counts.values()),
                name="Type"
            ), row=1, col=2)
            
            # 异常时间线
            fig.add_trace(go.Scatter(
                x=[a.timestamp for a in report.anomalies],
                y=[a.score for a in report.anomalies],
                mode='markers',
                marker=dict(
                    color=[self._severity_to_color(a.severity) for a in report.anomalies],
                    size=8
                ),
                name="Timeline"
            ), row=2, col=1)
            
            # 分数分布
            fig.add_trace(go.Histogram(
                x=[a.score for a in report.anomalies],
                name="Scores"
            ), row=2, col=2)
            
            fig.update_layout(
                title=f'Anomaly Analysis Summary - {report.symbol}',
                width=self.config.width,
                height=self.config.height
            )
            
            return fig
        
        return None
    
    def _severity_to_color(self, severity: AnomalySeverity) -> str:
        """将严重程度转换为颜色"""
        color_map = {
            AnomalySeverity.LOW: 'green',
            AnomalySeverity.MEDIUM: 'orange',
            AnomalySeverity.HIGH: 'red',
            AnomalySeverity.CRITICAL: 'darkred'
        }
        return color_map.get(severity, 'gray')


class VisualizationEngine:
    """可视化引擎"""
    
    def __init__(self, default_config: ChartConfig = None):
        self.default_config = default_config or ChartConfig()
        self.technical_builder = TechnicalChartBuilder(self.default_config)
        self.statistical_builder = StatisticalChartBuilder(self.default_config)
        self.anomaly_viz = AnomalyVisualization(self.default_config)
    
    def create_comprehensive_chart(self, data: pd.DataFrame,
                                 indicators: Optional[Dict[str, pd.Series]] = None,
                                 anomalies: Optional[List[AnomalyPoint]] = None,
                                 config: Optional[ChartConfig] = None) -> Any:
        """创建综合图表"""
        chart_config = config or self.default_config
        
        if not PLOTLY_AVAILABLE:
            # 回退到matplotlib
            return self.technical_builder.create_candlestick_chart(data, indicators, True)
        
        # 创建多子图布局
        rows = 3
        row_heights = [0.5, 0.2, 0.3]
        
        fig = make_subplots(
            rows=rows, cols=1,
            row_heights=row_heights,
            shared_xaxes=True,
            vertical_spacing=0.02,
            subplot_titles=['Price & Indicators', 'Volume', 'Analysis']
        )
        
        # 价格图
        close_col = 'close' if 'close' in data.columns else 'Close'
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data.get('open', data.get('Open')),
                high=data.get('high', data.get('High')),
                low=data.get('low', data.get('Low')),
                close=data[close_col],
                name='Price'
            ),
            row=1, col=1
        )
        
        # 技术指标
        if indicators:
            colors = chart_config.get_colors()
            for i, (name, data_series) in enumerate(indicators.items()):
                color = colors[i % len(colors)]
                fig.add_trace(
                    go.Scatter(
                        x=data_series.index,
                        y=data_series.values,
                        mode='lines',
                        name=name,
                        line=dict(color=color, width=2)
                    ),
                    row=1, col=1
                )
        
        # 异常点
        if anomalies:
            anomaly_times = [a.timestamp for a in anomalies]
            anomaly_values = [a.value for a in anomalies]
            anomaly_colors = [self.anomaly_viz._severity_to_color(a.severity) for a in anomalies]
            
            fig.add_trace(
                go.Scatter(
                    x=anomaly_times,
                    y=anomaly_values,
                    mode='markers',
                    name='Anomalies',
                    marker=dict(
                        color=anomaly_colors,
                        size=10,
                        symbol='x'
                    )
                ),
                row=1, col=1
            )
        
        # 成交量
        volume_col = 'volume' if 'volume' in data.columns else 'Volume'
        if volume_col in data.columns:
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data[volume_col],
                    name='Volume',
                    marker_color='lightblue',
                    opacity=0.7
                ),
                row=2, col=1
            )
        
        # 分析面板（可以添加其他分析结果）
        if indicators:
            # 选择一个主要指标显示在分析面板
            main_indicator = list(indicators.values())[0]
            fig.add_trace(
                go.Scatter(
                    x=main_indicator.index,
                    y=main_indicator.values,
                    mode='lines',
                    name='Analysis',
                    line=dict(color='purple', width=2)
                ),
                row=3, col=1
            )
        
        # 更新布局
        fig.update_layout(
            title=chart_config.title or 'Comprehensive Market Analysis',
            width=chart_config.width,
            height=chart_config.height,
            showlegend=chart_config.show_legend,
            xaxis_rangeslider_visible=False,
            template='plotly_dark' if chart_config.style == ChartStyle.DARK else 'plotly_white'
        )
        
        return fig
    
    def save_chart(self, fig: Any, filename: str, format: str = 'html') -> str:
        """保存图表"""
        if PLOTLY_AVAILABLE and hasattr(fig, 'write_html'):
            if format.lower() == 'html':
                fig.write_html(filename)
            elif format.lower() in ['png', 'jpg', 'jpeg', 'svg', 'pdf']:
                fig.write_image(filename)
            return filename
        elif MATPLOTLIB_AVAILABLE and hasattr(fig, 'savefig'):
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            return filename
        else:
            raise ValueError("Unsupported chart format or missing dependencies")


# 导出
__all__ = [
    'ChartType', 'ChartStyle', 'ChartConfig',
    'TechnicalChartBuilder', 'StatisticalChartBuilder', 'AnomalyVisualization',
    'VisualizationEngine'
]