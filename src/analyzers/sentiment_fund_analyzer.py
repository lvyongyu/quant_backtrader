#!/usr/bin/env python3
"""
情绪/资金面分析器
Sentiment & Fund Flow Analyzer

分析市场情绪和资金流向，为股票评分提供第四维度
"""

try:
    import yfinance as yf
    import pandas as pd
    from datetime import datetime
    from typing import Dict
    import warnings
    warnings.filterwarnings('ignore')
except ImportError as e:
    print(f"警告: 缺少依赖包 {e}, 情绪分析功能可能受限")
    yf = None
    pd = None


class SentimentFundAnalyzer:
    """情绪/资金面分析器"""
    
    def __init__(self):
        self.vix_data = None
        self.market_indices = ['SPY', 'QQQ', 'IWM']  # 大盘、科技、小盘
        
        print("🎭 情绪/资金面分析器初始化完成")
    
    def analyze_sentiment_fund(self, symbol: str) -> Dict:
        """
        分析股票的情绪和资金面
        
        Args:
            symbol: 股票代码
            
        Returns:
            包含情绪和资金面分析结果的字典
        """
        try:
            # 获取股票数据
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo", interval="1d")
            
            if hist.empty or len(hist) < 30:
                return self._get_default_sentiment_fund()
            
            # 1. VIX恐慌指数分析
            vix_sentiment = self._analyze_vix_sentiment()
            
            # 2. 资金流向分析
            fund_flow = self._analyze_fund_flow(hist)
            
            # 3. 买卖盘强度分析
            order_strength = self._analyze_order_strength(hist)
            
            # 4. 相对表现分析
            relative_performance = self._analyze_relative_performance(hist)
            
            # 5. 成交量情绪分析
            volume_sentiment = self._analyze_volume_sentiment(hist)
            
            # 计算综合得分
            sentiment_fund_score = self._calculate_sentiment_fund_score(
                vix_sentiment, fund_flow, order_strength, 
                relative_performance, volume_sentiment
            )
            
            return {
                'sentiment_fund_score': sentiment_fund_score,
                'vix_sentiment': vix_sentiment,
                'fund_flow': fund_flow,
                'order_strength': order_strength,
                'relative_performance': relative_performance,
                'volume_sentiment': volume_sentiment,
                'analysis_date': datetime.now().isoformat()
            }
            
        except (AttributeError, KeyError, ValueError, ConnectionError) as e:
            print(f"⚠️ 情绪/资金面分析失败 {symbol}: {e}")
            return self._get_default_sentiment_fund()
    
    def _analyze_vix_sentiment(self) -> Dict:
        """分析VIX恐慌指数"""
        try:
            if self.vix_data is None:
                vix = yf.Ticker("^VIX")
                self.vix_data = vix.history(period="5d")
            
            if not self.vix_data.empty:
                current_vix = self.vix_data['Close'].iloc[-1]
                
                if current_vix < 15:
                    sentiment = "极度乐观"
                    score = 90
                elif current_vix < 20:
                    sentiment = "乐观"
                    score = 75
                elif current_vix < 25:
                    sentiment = "中性"
                    score = 50
                elif current_vix < 35:
                    sentiment = "谨慎"
                    score = 25
                else:
                    sentiment = "恐慌"
                    score = 10
                
                return {
                    'level': round(current_vix, 2),
                    'sentiment': sentiment,
                    'score': score
                }
            
        except (AttributeError, KeyError, ValueError, ConnectionError) as e:
            print(f"⚠️ VIX分析失败: {e}")
        
        return {'level': 20.0, 'sentiment': '中性', 'score': 50}
    
    def _analyze_fund_flow(self, hist) -> Dict:
        """分析资金流向"""
        try:
            # 使用价格和成交量计算资金流向
            typical_price = (hist['High'] + hist['Low'] + hist['Close']) / 3
            money_flow = typical_price * hist['Volume']
            
            # 计算正负资金流
            positive_flow = money_flow[hist['Close'] > hist['Close'].shift(1)].sum()
            negative_flow = money_flow[hist['Close'] < hist['Close'].shift(1)].sum()
            total_flow = positive_flow + negative_flow
            
            if total_flow > 0:
                mfi = 100 * positive_flow / total_flow
            else:
                mfi = 50
            
            # 资金流向评分
            if mfi > 80:
                flow_strength = "强劲流入"
                score = 90
            elif mfi > 60:
                flow_strength = "流入"
                score = 70
            elif mfi > 40:
                flow_strength = "平衡"
                score = 50
            elif mfi > 20:
                flow_strength = "流出"
                score = 30
            else:
                flow_strength = "大量流出"
                score = 10
            
            return {
                'mfi': round(mfi, 2),
                'flow_strength': flow_strength,
                'score': score,
                'positive_flow': positive_flow,
                'negative_flow': negative_flow
            }
            
        except (AttributeError, KeyError, ValueError, ZeroDivisionError) as e:
            print(f"⚠️ 资金流向分析失败: {e}")
            return {'mfi': 50, 'flow_strength': '平衡', 'score': 50}
    
    def _analyze_order_strength(self, hist) -> Dict:
        """分析买卖盘强度"""
        try:
            # 使用最近20天数据
            recent_data = hist.tail(20)
            
            # 计算收盘价相对于当日最高最低价的位置
            close_position = (recent_data['Close'] - recent_data['Low']) / (recent_data['High'] - recent_data['Low'])
            close_position = close_position.fillna(0.5)
            
            avg_close_position = close_position.mean()
            
            # 计算涨跌日数比例
            up_days = (recent_data['Close'] > recent_data['Close'].shift(1)).sum()
            total_days = len(recent_data) - 1
            up_ratio = up_days / total_days if total_days > 0 else 0.5
            
            # 综合买卖盘强度评分
            strength_score = (avg_close_position * 0.6 + up_ratio * 0.4) * 100
            
            if strength_score > 70:
                strength = "买盘强劲"
                score = 85
            elif strength_score > 55:
                strength = "买盘占优"
                score = 70
            elif strength_score > 45:
                strength = "买卖平衡"
                score = 50
            elif strength_score > 30:
                strength = "卖盘占优"
                score = 30
            else:
                strength = "卖盘强劲"
                score = 15
            
            return {
                'close_position': round(avg_close_position, 3),
                'up_ratio': round(up_ratio, 3),
                'strength': strength,
                'score': score
            }
            
        except (AttributeError, KeyError, ValueError, ZeroDivisionError) as e:
            print(f"⚠️ 买卖盘强度分析失败: {e}")
            return {'strength': '买卖平衡', 'score': 50}
    
    def _analyze_relative_performance(self, hist) -> Dict:
        """分析相对市场表现"""
        try:
            # 获取最近20天的收益率
            stock_returns = hist['Close'].pct_change().tail(20)
            stock_performance = (1 + stock_returns).prod() - 1
            
            # 获取SPY作为基准
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="1mo")
            spy_returns = spy_hist['Close'].pct_change().tail(20)
            spy_performance = (1 + spy_returns).prod() - 1
            
            # 计算相对表现
            relative_perf = stock_performance - spy_performance
            
            if relative_perf > 0.05:  # 超越大盘5%以上
                performance = "强于大盘"
                score = 80
            elif relative_perf > 0.02:  # 超越大盘2-5%
                performance = "略强于大盘"
                score = 65
            elif relative_perf > -0.02:  # 与大盘持平
                performance = "跟随大盘"
                score = 50
            elif relative_perf > -0.05:  # 落后大盘2-5%
                performance = "略弱于大盘"
                score = 35
            else:  # 落后大盘5%以上
                performance = "弱于大盘"
                score = 20
            
            return {
                'stock_performance': round(stock_performance * 100, 2),
                'spy_performance': round(spy_performance * 100, 2),
                'relative_performance': round(relative_perf * 100, 2),
                'performance': performance,
                'score': score
            }
            
        except (AttributeError, KeyError, ValueError, ConnectionError) as e:
            print(f"⚠️ 相对表现分析失败: {e}")
            return {'performance': '跟随大盘', 'score': 50}
    
    def _analyze_volume_sentiment(self, hist) -> Dict:
        """分析成交量情绪"""
        try:
            # 计算成交量移动平均
            volume_ma_20 = hist['Volume'].rolling(20).mean()
            recent_volume = hist['Volume'].tail(5).mean()
            
            # 成交量比率
            volume_ratio = recent_volume / volume_ma_20.iloc[-1] if volume_ma_20.iloc[-1] > 0 else 1
            
            # 价量配合分析
            price_change = hist['Close'].pct_change().tail(10)
            volume_change = hist['Volume'].pct_change().tail(10)
            
            # 计算价量相关性
            correlation = price_change.corr(volume_change)
            if pd.isna(correlation):
                correlation = 0
            
            # 综合评分
            if volume_ratio > 1.5 and correlation > 0.3:
                sentiment = "放量上涨"
                score = 85
            elif volume_ratio > 1.2 and correlation > 0.1:
                sentiment = "温和放量"
                score = 70
            elif volume_ratio > 0.8:
                sentiment = "成交正常"
                score = 50
            elif volume_ratio > 0.5:
                sentiment = "成交萎缩"
                score = 30
            else:
                sentiment = "成交低迷"
                score = 15
            
            return {
                'volume_ratio': round(volume_ratio, 2),
                'price_volume_correlation': round(correlation, 3),
                'sentiment': sentiment,
                'score': score
            }
            
        except (AttributeError, KeyError, ValueError, ZeroDivisionError) as e:
            print(f"⚠️ 成交量情绪分析失败: {e}")
            return {'sentiment': '成交正常', 'score': 50}
    
    def _calculate_sentiment_fund_score(self, vix_sentiment: Dict, fund_flow: Dict, 
                                      order_strength: Dict, relative_performance: Dict,
                                      volume_sentiment: Dict) -> float:
        """计算情绪/资金面综合得分"""
        
        # 权重分配
        weights = {
            'vix': 0.25,           # VIX恐慌指数 25%
            'fund_flow': 0.30,     # 资金流向 30%
            'order_strength': 0.20, # 买卖盘强度 20%
            'relative_perf': 0.15,  # 相对表现 15%
            'volume': 0.10         # 成交量情绪 10%
        }
        
        total_score = (
            vix_sentiment.get('score', 50) * weights['vix'] +
            fund_flow.get('score', 50) * weights['fund_flow'] +
            order_strength.get('score', 50) * weights['order_strength'] +
            relative_performance.get('score', 50) * weights['relative_perf'] +
            volume_sentiment.get('score', 50) * weights['volume']
        )
        
        return round(total_score, 2)
    
    def _get_default_sentiment_fund(self) -> Dict:
        """获取默认的情绪/资金面分析结果"""
        return {
            'sentiment_fund_score': 50.0,
            'vix_sentiment': {'level': 20.0, 'sentiment': '中性', 'score': 50},
            'fund_flow': {'mfi': 50, 'flow_strength': '平衡', 'score': 50},
            'order_strength': {'strength': '买卖平衡', 'score': 50},
            'relative_performance': {'performance': '跟随大盘', 'score': 50},
            'volume_sentiment': {'sentiment': '成交正常', 'score': 50},
            'analysis_date': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # 测试情绪/资金面分析器
    analyzer = SentimentFundAnalyzer()
    
    test_symbols = ['AAPL', 'TSLA', 'NVDA']
    
    for symbol in test_symbols:
        print(f"\n📊 分析 {symbol} 的情绪/资金面...")
        result = analyzer.analyze_sentiment_fund(symbol)
        print(f"💯 综合得分: {result['sentiment_fund_score']}")
        print(f"🎭 VIX情绪: {result['vix_sentiment']['sentiment']} ({result['vix_sentiment']['score']}分)")
        print(f"💰 资金流向: {result['fund_flow']['flow_strength']} ({result['fund_flow']['score']}分)")
        print(f"⚖️ 买卖盘: {result['order_strength']['strength']} ({result['order_strength']['score']}分)")