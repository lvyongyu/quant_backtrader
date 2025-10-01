"""
情感分析模块

提供市场情感分析功能：
1. 新闻情感分析
2. 社交媒体情感分析
3. 技术指标情感分析
4. 市场恐慌指数
5. 综合情感评分
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import warnings
import re

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    warnings.warn("TextBlob not available, text sentiment analysis will be limited")

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    warnings.warn("requests and BeautifulSoup not available, web scraping will be limited")

from . import ModelPrediction, PredictionType


class SentimentScore(Enum):
    """情感评分"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class SentimentSource(Enum):
    """情感来源"""
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    TECHNICAL = "technical"
    MARKET_DATA = "market_data"
    ANALYST_REPORTS = "analyst_reports"


@dataclass
class SentimentPoint:
    """情感数据点"""
    timestamp: datetime
    source: SentimentSource
    score: float  # -1 to 1
    confidence: float  # 0 to 1
    text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_sentiment_label(self) -> SentimentScore:
        """获取情感标签"""
        if self.score <= -0.6:
            return SentimentScore.VERY_NEGATIVE
        elif self.score <= -0.2:
            return SentimentScore.NEGATIVE
        elif self.score <= 0.2:
            return SentimentScore.NEUTRAL
        elif self.score <= 0.6:
            return SentimentScore.POSITIVE
        else:
            return SentimentScore.VERY_POSITIVE
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value,
            'score': self.score,
            'confidence': self.confidence,
            'sentiment_label': self.get_sentiment_label().value,
            'text': self.text,
            'metadata': self.metadata
        }


@dataclass
class MarketSentiment:
    """市场情感分析结果"""
    symbol: str
    overall_score: float
    confidence: float
    sentiment_label: SentimentScore
    analysis_period: Tuple[datetime, datetime]
    source_scores: Dict[SentimentSource, float]
    sentiment_points: List[SentimentPoint] = field(default_factory=list)
    fear_greed_index: Optional[float] = None
    volatility_sentiment: Optional[float] = None
    momentum_sentiment: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'overall_score': self.overall_score,
            'confidence': self.confidence,
            'sentiment_label': self.sentiment_label.value,
            'analysis_period': [self.analysis_period[0].isoformat(), self.analysis_period[1].isoformat()],
            'source_scores': {source.value: score for source, score in self.source_scores.items()},
            'sentiment_points': [sp.to_dict() for sp in self.sentiment_points],
            'fear_greed_index': self.fear_greed_index,
            'volatility_sentiment': self.volatility_sentiment,
            'momentum_sentiment': self.momentum_sentiment
        }


class TextSentimentAnalyzer:
    """文本情感分析器"""
    
    def __init__(self):
        # 金融领域特定的词典
        self.positive_words = {
            'bullish', 'buy', 'strong', 'growth', 'profit', 'gain', 'rise', 'surge',
            'rally', 'outperform', 'upgrade', 'positive', 'optimistic', 'confident',
            'beat', 'exceed', 'momentum', 'breakthrough', 'opportunity'
        }
        
        self.negative_words = {
            'bearish', 'sell', 'weak', 'decline', 'loss', 'fall', 'drop', 'crash',
            'plunge', 'underperform', 'downgrade', 'negative', 'pessimistic', 'worried',
            'miss', 'disappoint', 'risk', 'concern', 'uncertainty', 'volatility'
        }
        
        self.financial_keywords = {
            'earnings', 'revenue', 'eps', 'guidance', 'forecast', 'outlook',
            'dividend', 'buyback', 'merger', 'acquisition', 'ipo', 'sec'
        }
    
    def analyze_text(self, text: str) -> SentimentPoint:
        """分析文本情感"""
        if not text:
            return SentimentPoint(
                timestamp=datetime.now(),
                source=SentimentSource.NEWS,
                score=0.0,
                confidence=0.0
            )
        
        # 文本预处理
        text_clean = self._preprocess_text(text)
        
        # 使用TextBlob进行基础情感分析
        if TEXTBLOB_AVAILABLE:
            blob = TextBlob(text_clean)
            base_sentiment = blob.sentiment.polarity
            base_confidence = abs(blob.sentiment.polarity)
        else:
            base_sentiment = 0.0
            base_confidence = 0.0
        
        # 金融词典增强
        financial_sentiment = self._financial_sentiment_score(text_clean)
        financial_confidence = self._calculate_financial_confidence(text_clean)
        
        # 组合情感分数
        if financial_confidence > 0.1:  # 如果包含金融关键词
            combined_sentiment = (base_sentiment * 0.6 + financial_sentiment * 0.4)
            combined_confidence = max(base_confidence, financial_confidence)
        else:
            combined_sentiment = base_sentiment
            combined_confidence = base_confidence
        
        # 确保分数在合理范围内
        combined_sentiment = max(-1.0, min(1.0, combined_sentiment))
        combined_confidence = max(0.0, min(1.0, combined_confidence))
        
        return SentimentPoint(
            timestamp=datetime.now(),
            source=SentimentSource.NEWS,
            score=combined_sentiment,
            confidence=combined_confidence,
            text=text[:200],  # 保存前200字符
            metadata={
                'text_length': len(text),
                'base_sentiment': base_sentiment,
                'financial_sentiment': financial_sentiment,
                'has_financial_keywords': financial_confidence > 0.1
            }
        )
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 转换为小写
        text = text.lower()
        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        # 移除多余空格
        text = ' '.join(text.split())
        return text
    
    def _financial_sentiment_score(self, text: str) -> float:
        """基于金融词典的情感评分"""
        words = text.split()
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        sentiment_score = (positive_count - negative_count) / total_sentiment_words
        return sentiment_score
    
    def _calculate_financial_confidence(self, text: str) -> float:
        """计算金融关键词置信度"""
        words = text.split()
        financial_word_count = sum(1 for word in words if word in self.financial_keywords)
        sentiment_word_count = sum(1 for word in words if word in self.positive_words or word in self.negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        # 基于金融关键词和情感词的密度
        financial_density = financial_word_count / total_words
        sentiment_density = sentiment_word_count / total_words
        
        confidence = min(1.0, (financial_density + sentiment_density) * 2)
        return confidence


class TechnicalSentimentAnalyzer:
    """技术指标情感分析器"""
    
    def analyze_technical_sentiment(self, data: pd.DataFrame) -> SentimentPoint:
        """基于技术指标分析市场情感"""
        if len(data) < 20:
            return SentimentPoint(
                timestamp=datetime.now(),
                source=SentimentSource.TECHNICAL,
                score=0.0,
                confidence=0.0
            )
        
        sentiment_scores = []
        
        # RSI情感
        rsi_sentiment = self._rsi_sentiment(data)
        sentiment_scores.append(rsi_sentiment)
        
        # 移动平均情感
        ma_sentiment = self._moving_average_sentiment(data)
        sentiment_scores.append(ma_sentiment)
        
        # 波动率情感
        volatility_sentiment = self._volatility_sentiment(data)
        sentiment_scores.append(volatility_sentiment)
        
        # 成交量情感
        volume_sentiment = self._volume_sentiment(data)
        sentiment_scores.append(volume_sentiment)
        
        # MACD情感
        macd_sentiment = self._macd_sentiment(data)
        sentiment_scores.append(macd_sentiment)
        
        # 综合评分
        overall_sentiment = np.mean(sentiment_scores)
        confidence = 1.0 - np.std(sentiment_scores)  # 一致性越高，置信度越高
        
        return SentimentPoint(
            timestamp=datetime.now(),
            source=SentimentSource.TECHNICAL,
            score=overall_sentiment,
            confidence=max(0.0, confidence),
            metadata={
                'rsi_sentiment': rsi_sentiment,
                'ma_sentiment': ma_sentiment,
                'volatility_sentiment': volatility_sentiment,
                'volume_sentiment': volume_sentiment,
                'macd_sentiment': macd_sentiment
            }
        )
    
    def _rsi_sentiment(self, data: pd.DataFrame) -> float:
        """RSI情感分析"""
        close = data['close'] if 'close' in data.columns else data['Close']
        
        # 计算RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # RSI情感映射
        if current_rsi >= 70:
            return -0.5  # 超买，负面情感
        elif current_rsi <= 30:
            return 0.5   # 超卖，正面情感
        else:
            # 50附近为中性，越远离50情感越强
            return (50 - current_rsi) / 50 * 0.3
    
    def _moving_average_sentiment(self, data: pd.DataFrame) -> float:
        """移动平均情感分析"""
        close = data['close'] if 'close' in data.columns else data['Close']
        
        ma_short = close.rolling(5).mean()
        ma_long = close.rolling(20).mean()
        current_price = close.iloc[-1]
        
        # 价格相对于均线的位置
        short_ratio = (current_price - ma_short.iloc[-1]) / ma_short.iloc[-1]
        long_ratio = (current_price - ma_long.iloc[-1]) / ma_long.iloc[-1]
        
        # 均线趋势
        ma_trend = (ma_short.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1]
        
        # 综合情感
        sentiment = (short_ratio + long_ratio + ma_trend) / 3
        return max(-1.0, min(1.0, sentiment * 10))  # 放大并限制范围
    
    def _volatility_sentiment(self, data: pd.DataFrame) -> float:
        """波动率情感分析"""
        close = data['close'] if 'close' in data.columns else data['Close']
        
        # 计算历史波动率
        returns = close.pct_change()
        current_vol = returns.rolling(10).std().iloc[-1]
        historical_vol = returns.rolling(50).std().mean()
        
        # 波动率比较
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
        
        # 高波动率通常表示恐慌或不确定性
        if vol_ratio > 1.5:
            return -0.3  # 负面情感
        elif vol_ratio < 0.7:
            return 0.2   # 正面情感（低波动率，稳定）
        else:
            return 0.0   # 中性
    
    def _volume_sentiment(self, data: pd.DataFrame) -> float:
        """成交量情感分析"""
        volume = data['volume'] if 'volume' in data.columns else data.get('Volume')
        close = data['close'] if 'close' in data.columns else data['Close']
        
        if volume is None:
            return 0.0
        
        # 成交量变化
        volume_ma = volume.rolling(20).mean()
        current_volume = volume.iloc[-1]
        volume_ratio = current_volume / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1.0
        
        # 价格变化
        price_change = close.pct_change().iloc[-1]
        
        # 量价关系分析
        if volume_ratio > 1.5:  # 高成交量
            if price_change > 0:
                return 0.3  # 放量上涨，正面
            else:
                return -0.3  # 放量下跌，负面
        else:
            return 0.0  # 正常成交量，中性
    
    def _macd_sentiment(self, data: pd.DataFrame) -> float:
        """MACD情感分析"""
        close = data['close'] if 'close' in data.columns else data['Close']
        
        # 计算MACD
        exp1 = close.ewm(span=12).mean()
        exp2 = close.ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        # MACD信号
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        # 情感评分
        macd_score = 0.0
        
        # MACD线相对于信号线
        if current_macd > current_signal:
            macd_score += 0.2
        else:
            macd_score -= 0.2
        
        # 柱状图趋势
        if len(histogram) > 1:
            if current_histogram > histogram.iloc[-2]:
                macd_score += 0.1
            else:
                macd_score -= 0.1
        
        return max(-1.0, min(1.0, macd_score))


class MarketDataSentimentAnalyzer:
    """市场数据情感分析器"""
    
    def calculate_fear_greed_index(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """计算恐慌贪婪指数"""
        components = []
        
        # 1. 价格动量（25%权重）
        momentum_score = self._calculate_momentum_sentiment(market_data)
        components.append(('momentum', momentum_score, 0.25))
        
        # 2. 市场波动率（25%权重）
        volatility_score = self._calculate_volatility_sentiment(market_data)
        components.append(('volatility', volatility_score, 0.25))
        
        # 3. 市场广度（25%权重）
        breadth_score = self._calculate_market_breadth(market_data)
        components.append(('breadth', breadth_score, 0.25))
        
        # 4. 成交量（25%权重）
        volume_score = self._calculate_volume_sentiment(market_data)
        components.append(('volume', volume_score, 0.25))
        
        # 加权平均
        fear_greed_score = sum(score * weight for _, score, weight in components)
        
        # 转换到0-100范围（0=极度恐慌，100=极度贪婪）
        fear_greed_index = (fear_greed_score + 1) * 50
        
        return max(0, min(100, fear_greed_index))
    
    def _calculate_momentum_sentiment(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """计算动量情感"""
        momentum_scores = []
        
        for symbol, data in market_data.items():
            if len(data) >= 20:
                close = data['close'] if 'close' in data.columns else data['Close']
                
                # 短期动量
                momentum_5d = (close.iloc[-1] - close.iloc[-6]) / close.iloc[-6]
                momentum_20d = (close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]
                
                # 综合动量
                avg_momentum = (momentum_5d + momentum_20d) / 2
                momentum_scores.append(avg_momentum)
        
        if momentum_scores:
            overall_momentum = np.mean(momentum_scores)
            # 标准化到-1到1范围
            return max(-1, min(1, overall_momentum * 5))
        else:
            return 0.0
    
    def _calculate_volatility_sentiment(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """计算波动率情感"""
        volatility_scores = []
        
        for symbol, data in market_data.items():
            if len(data) >= 50:
                close = data['close'] if 'close' in data.columns else data['Close']
                returns = close.pct_change()
                
                # 当前波动率vs历史波动率
                current_vol = returns.rolling(10).std().iloc[-1]
                historical_vol = returns.rolling(50).std().mean()
                
                vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
                
                # 高波动率 = 恐慌
                vol_sentiment = -(vol_ratio - 1)  # 1为中性，>1为负面，<1为正面
                volatility_scores.append(vol_sentiment)
        
        if volatility_scores:
            overall_volatility = np.mean(volatility_scores)
            return max(-1, min(1, overall_volatility))
        else:
            return 0.0
    
    def _calculate_market_breadth(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """计算市场广度"""
        if len(market_data) < 2:
            return 0.0
        
        advancing_stocks = 0
        declining_stocks = 0
        
        for symbol, data in market_data.items():
            if len(data) >= 2:
                close = data['close'] if 'close' in data.columns else data['Close']
                change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
                
                if change > 0:
                    advancing_stocks += 1
                elif change < 0:
                    declining_stocks += 1
        
        total_stocks = advancing_stocks + declining_stocks
        if total_stocks > 0:
            advance_decline_ratio = (advancing_stocks - declining_stocks) / total_stocks
            return advance_decline_ratio
        else:
            return 0.0
    
    def _calculate_volume_sentiment(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """计算成交量情感"""
        volume_scores = []
        
        for symbol, data in market_data.items():
            volume_col = 'volume' if 'volume' in data.columns else data.get('Volume')
            if volume_col is not None and len(data) >= 20:
                volume = data[volume_col]
                close = data['close'] if 'close' in data.columns else data['Close']
                
                # 成交量相对于平均值
                volume_ma = volume.rolling(20).mean()
                volume_ratio = volume.iloc[-1] / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1.0
                
                # 价格变化
                price_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]
                
                # 量价配合分析
                if volume_ratio > 1.2:  # 放量
                    if price_change > 0:
                        volume_scores.append(0.3)  # 放量上涨，正面
                    else:
                        volume_scores.append(-0.3)  # 放量下跌，负面
                else:
                    volume_scores.append(0.0)  # 正常量，中性
        
        if volume_scores:
            return np.mean(volume_scores)
        else:
            return 0.0


class SentimentAnalysisEngine:
    """情感分析引擎"""
    
    def __init__(self):
        self.text_analyzer = TextSentimentAnalyzer()
        self.technical_analyzer = TechnicalSentimentAnalyzer()
        self.market_analyzer = MarketDataSentimentAnalyzer()
    
    def comprehensive_sentiment_analysis(self, symbol: str,
                                       price_data: pd.DataFrame,
                                       news_texts: List[str] = None,
                                       market_data: Dict[str, pd.DataFrame] = None) -> MarketSentiment:
        """综合情感分析"""
        sentiment_points = []
        source_scores = {}
        
        # 技术指标情感
        technical_sentiment = self.technical_analyzer.analyze_technical_sentiment(price_data)
        sentiment_points.append(technical_sentiment)
        source_scores[SentimentSource.TECHNICAL] = technical_sentiment.score
        
        # 新闻情感分析
        if news_texts:
            news_sentiments = []
            for text in news_texts:
                news_sentiment = self.text_analyzer.analyze_text(text)
                sentiment_points.append(news_sentiment)
                news_sentiments.append(news_sentiment.score)
            
            if news_sentiments:
                source_scores[SentimentSource.NEWS] = np.mean(news_sentiments)
        
        # 市场数据情感
        if market_data:
            fear_greed_index = self.market_analyzer.calculate_fear_greed_index(market_data)
            # 转换为-1到1的范围
            market_sentiment_score = (fear_greed_index - 50) / 50
            
            market_sentiment_point = SentimentPoint(
                timestamp=datetime.now(),
                source=SentimentSource.MARKET_DATA,
                score=market_sentiment_score,
                confidence=0.8,
                metadata={'fear_greed_index': fear_greed_index}
            )
            sentiment_points.append(market_sentiment_point)
            source_scores[SentimentSource.MARKET_DATA] = market_sentiment_score
        else:
            fear_greed_index = None
        
        # 计算综合情感分数
        if sentiment_points:
            weights = {
                SentimentSource.TECHNICAL: 0.4,
                SentimentSource.NEWS: 0.3,
                SentimentSource.MARKET_DATA: 0.3
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for source, score in source_scores.items():
                weight = weights.get(source, 0.2)
                weighted_score += score * weight
                total_weight += weight
            
            overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
            
            # 计算综合置信度
            confidences = [sp.confidence for sp in sentiment_points]
            overall_confidence = np.mean(confidences) if confidences else 0.0
        else:
            overall_score = 0.0
            overall_confidence = 0.0
        
        # 确定情感标签
        if overall_score <= -0.6:
            sentiment_label = SentimentScore.VERY_NEGATIVE
        elif overall_score <= -0.2:
            sentiment_label = SentimentScore.NEGATIVE
        elif overall_score <= 0.2:
            sentiment_label = SentimentScore.NEUTRAL
        elif overall_score <= 0.6:
            sentiment_label = SentimentScore.POSITIVE
        else:
            sentiment_label = SentimentScore.VERY_POSITIVE
        
        # 分析时间段
        analysis_start = price_data.index[0] if len(price_data) > 0 else datetime.now()
        analysis_end = price_data.index[-1] if len(price_data) > 0 else datetime.now()
        
        # 转换时间戳
        if hasattr(analysis_start, 'to_pydatetime'):
            analysis_start = analysis_start.to_pydatetime()
        elif not isinstance(analysis_start, datetime):
            analysis_start = datetime.now()
        
        if hasattr(analysis_end, 'to_pydatetime'):
            analysis_end = analysis_end.to_pydatetime()
        elif not isinstance(analysis_end, datetime):
            analysis_end = datetime.now()
        
        return MarketSentiment(
            symbol=symbol,
            overall_score=overall_score,
            confidence=overall_confidence,
            sentiment_label=sentiment_label,
            analysis_period=(analysis_start, analysis_end),
            source_scores=source_scores,
            sentiment_points=sentiment_points,
            fear_greed_index=fear_greed_index,
            volatility_sentiment=source_scores.get(SentimentSource.TECHNICAL),
            momentum_sentiment=source_scores.get(SentimentSource.MARKET_DATA)
        )
    
    def generate_sentiment_signals(self, sentiment: MarketSentiment) -> List[str]:
        """生成情感交易信号"""
        signals = []
        
        # 基于整体情感的信号
        if sentiment.sentiment_label == SentimentScore.VERY_POSITIVE:
            signals.append("STRONG_BULLISH_SENTIMENT")
        elif sentiment.sentiment_label == SentimentScore.POSITIVE:
            signals.append("BULLISH_SENTIMENT")
        elif sentiment.sentiment_label == SentimentScore.VERY_NEGATIVE:
            signals.append("STRONG_BEARISH_SENTIMENT")
        elif sentiment.sentiment_label == SentimentScore.NEGATIVE:
            signals.append("BEARISH_SENTIMENT")
        else:
            signals.append("NEUTRAL_SENTIMENT")
        
        # 基于恐慌贪婪指数的信号
        if sentiment.fear_greed_index is not None:
            if sentiment.fear_greed_index <= 20:
                signals.append("EXTREME_FEAR")  # 极度恐慌，可能是买入机会
            elif sentiment.fear_greed_index <= 40:
                signals.append("FEAR")
            elif sentiment.fear_greed_index >= 80:
                signals.append("EXTREME_GREED")  # 极度贪婪，可能是卖出机会
            elif sentiment.fear_greed_index >= 60:
                signals.append("GREED")
        
        # 基于置信度的信号
        if sentiment.confidence >= 0.8:
            signals.append("HIGH_CONFIDENCE_SENTIMENT")
        elif sentiment.confidence <= 0.3:
            signals.append("LOW_CONFIDENCE_SENTIMENT")
        
        return signals


# 导出
__all__ = [
    'SentimentScore', 'SentimentSource', 'SentimentPoint', 'MarketSentiment',
    'TextSentimentAnalyzer', 'TechnicalSentimentAnalyzer', 'MarketDataSentimentAnalyzer',
    'SentimentAnalysisEngine'
]