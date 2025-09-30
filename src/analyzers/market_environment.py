#!/usr/bin/env python3
"""
市场环境分析模块
Market Environment Analysis Module

分析市场宏观环境：
- 大盘指数趋势分析
- 市场情绪指标
- 行业板块轮动
- 波动率环境
- 流动性环境
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class MarketEnvironmentAnalyzer:
    """市场环境分析器"""
    
    def __init__(self):
        self.market_data = {}
        print("🌍 市场环境分析器初始化完成")
    
    def get_market_indices(self) -> dict:
        """获取主要市场指数数据"""
        
        indices = {
            'SPX': '^GSPC',    # S&P 500
            'NDX': '^IXIC',    # NASDAQ
            'DJI': '^DJI',     # 道琼斯
            'RUT': '^RUT',     # Russell 2000 (小盘股)
            'VIX': '^VIX',     # 恐慌指数
            'TNX': '^TNX',     # 10年期国债收益率
            'DXY': 'DX-Y.NYB'  # 美元指数
        }
        
        market_data = {}
        
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="3mo", interval="1d")
                
                if not hist.empty:
                    # 计算技术指标
                    hist['SMA_20'] = hist['Close'].rolling(20).mean()
                    hist['SMA_50'] = hist['Close'].rolling(50).mean()
                    hist['volatility'] = hist['Close'].pct_change().rolling(20).std() * np.sqrt(252)
                    
                    current_price = hist['Close'].iloc[-1]
                    sma_20 = hist['SMA_20'].iloc[-1]
                    sma_50 = hist['SMA_50'].iloc[-1]
                    volatility = hist['volatility'].iloc[-1]
                    
                    # 计算动量
                    momentum_5d = (current_price / hist['Close'].iloc[-6] - 1) * 100
                    momentum_20d = (current_price / hist['Close'].iloc[-21] - 1) * 100
                    momentum_60d = (current_price / hist['Close'].iloc[-61] - 1) * 100
                    
                    market_data[name] = {
                        'current_price': current_price,
                        'sma_20': sma_20,
                        'sma_50': sma_50,
                        'volatility': volatility,
                        'momentum_5d': momentum_5d,
                        'momentum_20d': momentum_20d,
                        'momentum_60d': momentum_60d,
                        'trend_strength': self._calculate_trend_strength(hist),
                        'data': hist
                    }
                    
            except Exception as e:
                print(f"❌ 获取 {name} 数据失败: {e}")
                continue
        
        self.market_data = market_data
        return market_data
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """计算趋势强度"""
        
        if len(data) < 20:
            return 0
        
        # 计算价格相对于移动平均线的位置
        current_price = data['Close'].iloc[-1]
        sma_20 = data['Close'].rolling(20).mean().iloc[-1]
        
        # 计算趋势一致性
        above_sma_count = sum(data['Close'].tail(20) > data['Close'].rolling(20).mean().tail(20))
        trend_consistency = above_sma_count / 20
        
        # 计算价格动量
        price_momentum = (current_price / sma_20 - 1) * 100
        
        # 综合趋势强度
        trend_strength = (trend_consistency * 50) + min(abs(price_momentum) * 2, 50)
        
        return min(trend_strength, 100)
    
    def analyze_market_trend(self) -> dict:
        """分析市场趋势"""
        
        if not self.market_data:
            self.get_market_indices()
        
        trend_analysis = {}
        
        for index, data in self.market_data.items():
            current = data['current_price']
            sma_20 = data['sma_20']
            sma_50 = data['sma_50']
            
            # 判断趋势方向
            if current > sma_20 > sma_50:
                trend = "强烈上涨"
                trend_score = 100
            elif current > sma_20 and sma_20 < sma_50:
                trend = "震荡上涨"
                trend_score = 75
            elif current < sma_20 > sma_50:
                trend = "震荡下跌"
                trend_score = 25
            elif current < sma_20 < sma_50:
                trend = "强烈下跌"
                trend_score = 0
            else:
                trend = "横盘整理"
                trend_score = 50
            
            trend_analysis[index] = {
                'trend': trend,
                'trend_score': trend_score,
                'trend_strength': data['trend_strength'],
                'momentum_5d': data['momentum_5d'],
                'momentum_20d': data['momentum_20d']
            }
        
        return trend_analysis
    
    def analyze_market_sentiment(self) -> dict:
        """分析市场情绪"""
        
        sentiment = {}
        
        if 'VIX' in self.market_data:
            vix_level = self.market_data['VIX']['current_price']
            
            if vix_level < 15:
                vix_sentiment = "极度乐观"
                vix_score = 90
            elif vix_level < 20:
                vix_sentiment = "乐观"
                vix_score = 70
            elif vix_level < 25:
                vix_sentiment = "中性"
                vix_score = 50
            elif vix_level < 35:
                vix_sentiment = "谨慎"
                vix_score = 30
            else:
                vix_sentiment = "恐慌"
                vix_score = 10
            
            sentiment['vix'] = {
                'level': vix_level,
                'sentiment': vix_sentiment,
                'score': vix_score
            }
        
        # 分析大盘相对强弱
        if 'SPX' in self.market_data and 'RUT' in self.market_data:
            spx_momentum = self.market_data['SPX']['momentum_20d']
            rut_momentum = self.market_data['RUT']['momentum_20d']
            
            if spx_momentum > rut_momentum + 2:
                size_preference = "偏好大盘股"
            elif rut_momentum > spx_momentum + 2:
                size_preference = "偏好小盘股"
            else:
                size_preference = "大小盘均衡"
            
            sentiment['size_preference'] = size_preference
        
        return sentiment
    
    def analyze_sector_rotation(self) -> dict:
        """分析行业板块轮动"""
        
        sectors = {
            'XLK': '科技',
            'XLF': '金融', 
            'XLV': '医疗',
            'XLE': '能源',
            'XLI': '工业',
            'XLP': '消费必需品',
            'XLY': '消费可选',
            'XLU': '公用事业',
            'XLRE': '房地产',
            'XLB': '材料',
            'XLC': '通讯'
        }
        
        sector_performance = {}
        
        for etf, sector_name in sectors.items():
            try:
                ticker = yf.Ticker(etf)
                hist = ticker.history(period="3mo", interval="1d")
                
                if not hist.empty:
                    # 计算相对表现
                    momentum_20d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-21] - 1) * 100
                    momentum_60d = (hist['Close'].iloc[-1] / hist['Close'].iloc[-61] - 1) * 100
                    
                    sector_performance[sector_name] = {
                        'etf': etf,
                        'momentum_20d': momentum_20d,
                        'momentum_60d': momentum_60d
                    }
                    
            except Exception as e:
                continue
        
        # 排序找出表现最好的板块
        if sector_performance:
            top_sectors = sorted(
                sector_performance.items(), 
                key=lambda x: x[1]['momentum_20d'], 
                reverse=True
            )[:3]
            
            bottom_sectors = sorted(
                sector_performance.items(), 
                key=lambda x: x[1]['momentum_20d']
            )[:3]
            
            return {
                'top_performers': top_sectors,
                'bottom_performers': bottom_sectors,
                'all_sectors': sector_performance
            }
        
        return {}
    
    def get_market_environment_score(self) -> dict:
        """获取市场环境综合评分"""
        
        print("🌍 分析市场环境...")
        
        # 获取各项分析
        trend_analysis = self.analyze_market_trend()
        sentiment_analysis = self.analyze_market_sentiment()
        sector_analysis = self.analyze_sector_rotation()
        
        # 计算综合市场得分
        market_scores = []
        
        # 主要指数趋势得分
        if 'SPX' in trend_analysis:
            market_scores.append(trend_analysis['SPX']['trend_score'])
        if 'NDX' in trend_analysis:
            market_scores.append(trend_analysis['NDX']['trend_score'])
        
        # VIX情绪得分
        if 'vix' in sentiment_analysis:
            market_scores.append(sentiment_analysis['vix']['score'])
        
        overall_score = np.mean(market_scores) if market_scores else 50
        
        # 判断市场环境
        if overall_score >= 80:
            environment = "极度乐观"
            recommendation = "积极配置成长股和周期股"
        elif overall_score >= 60:
            environment = "乐观"
            recommendation = "适度配置股票，关注优质成长股"
        elif overall_score >= 40:
            environment = "中性"
            recommendation = "均衡配置，关注防御性股票"
        elif overall_score >= 20:
            environment = "谨慎"
            recommendation = "降低风险敞口，增加防御性资产"
        else:
            environment = "悲观"
            recommendation = "保守配置，重点关注安全资产"
        
        return {
            'overall_score': round(overall_score, 1),
            'environment': environment,
            'recommendation': recommendation,
            'trend_analysis': trend_analysis,
            'sentiment_analysis': sentiment_analysis,
            'sector_analysis': sector_analysis,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_stock_environment_fit(self, symbol: str, sector: str = None) -> dict:
        """分析个股与市场环境的匹配度"""
        
        market_env = self.get_market_environment_score()
        
        # 获取个股数据
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo", interval="1d")
            info = ticker.info
            
            if hist.empty:
                return {'error': f'无法获取{symbol}数据'}
            
            # 计算个股相对市场表现
            stock_momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-21] - 1) * 100
            
            # 获取beta值
            beta = info.get('beta', 1.0)
            stock_sector = sector or info.get('sector', 'Unknown')
            
            # 分析匹配度
            market_score = market_env['overall_score']
            
            # 根据市场环境判断个股适合度
            if market_score >= 70:  # 牛市环境
                if beta > 1.2:
                    fit_score = 90  # 高beta股票在牛市表现好
                    fit_reason = "高beta股票适合牛市环境"
                elif beta > 0.8:
                    fit_score = 75
                    fit_reason = "适度风险股票在牛市有良好表现"
                else:
                    fit_score = 60
                    fit_reason = "低风险股票在牛市表现一般"
            elif market_score <= 30:  # 熊市环境
                if beta < 0.8:
                    fit_score = 90  # 低beta股票在熊市抗跌
                    fit_reason = "低风险股票在熊市具有防御性"
                elif beta < 1.2:
                    fit_score = 70
                    fit_reason = "适度风险股票在熊市需要谨慎"
                else:
                    fit_score = 40
                    fit_reason = "高风险股票在熊市表现较差"
            else:  # 震荡市
                fit_score = 60 + (stock_momentum / 10)  # 基于个股表现调整
                fit_reason = "震荡市中个股表现分化"
            
            # 行业轮动影响
            sector_analysis = market_env.get('sector_analysis', {})
            if sector_analysis and 'top_performers' in sector_analysis:
                top_sectors = [s[0] for s in sector_analysis['top_performers']]
                if stock_sector in top_sectors:
                    fit_score = min(fit_score + 15, 100)
                    fit_reason += f"，{stock_sector}板块表现强势"
            
            return {
                'symbol': symbol,
                'fit_score': round(max(0, min(fit_score, 100)), 1),
                'fit_reason': fit_reason,
                'beta': beta,
                'sector': stock_sector,
                'stock_momentum_20d': round(stock_momentum, 2),
                'market_environment': market_env['environment'],
                'market_score': market_env['overall_score']
            }
            
        except Exception as e:
            return {'error': f'分析{symbol}环境匹配度失败: {str(e)}'}


def test_market_environment():
    """测试市场环境分析"""
    
    print("🧪 测试市场环境分析")
    print("=" * 50)
    
    analyzer = MarketEnvironmentAnalyzer()
    
    # 获取市场环境分析
    market_env = analyzer.get_market_environment_score()
    
    print(f"📊 市场环境分析结果:")
    print(f"   综合得分: {market_env['overall_score']}/100")
    print(f"   市场环境: {market_env['environment']}")
    print(f"   投资建议: {market_env['recommendation']}")
    
    # 显示趋势分析
    if 'trend_analysis' in market_env:
        print(f"\n📈 主要指数趋势:")
        for index, data in market_env['trend_analysis'].items():
            print(f"   {index}: {data['trend']} (得分: {data['trend_score']})")
    
    # 显示情绪分析
    if 'sentiment_analysis' in market_env:
        print(f"\n😊 市场情绪:")
        sentiment = market_env['sentiment_analysis']
        if 'vix' in sentiment:
            vix_info = sentiment['vix']
            print(f"   VIX: {vix_info['level']:.1f} ({vix_info['sentiment']})")
    
    # 显示板块轮动
    if 'sector_analysis' in market_env and market_env['sector_analysis']:
        sector_info = market_env['sector_analysis']
        if 'top_performers' in sector_info:
            print(f"\n🔥 表现最佳板块:")
            for sector, data in sector_info['top_performers']:
                print(f"   {sector}: +{data['momentum_20d']:.1f}%")
    
    # 测试个股环境匹配度
    test_stocks = ['AAPL', 'TSLA', 'JNJ']
    print(f"\n🎯 个股环境匹配度分析:")
    
    for symbol in test_stocks:
        fit_analysis = analyzer.get_stock_environment_fit(symbol)
        if 'error' not in fit_analysis:
            print(f"   {symbol}: {fit_analysis['fit_score']}/100 - {fit_analysis['fit_reason']}")


if __name__ == "__main__":
    test_market_environment()