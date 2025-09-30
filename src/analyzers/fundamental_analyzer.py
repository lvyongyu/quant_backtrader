#!/usr/bin/env python3
"""
基本面分析模块
Fundamental Analysis Module

集成基本面指标分析：
- 财务健康度分析
- 估值水平评估
- 盈利能力分析
- 成长性分析
- 股息收益率分析
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self):
        self.cache = {}
        print("📊 基本面分析器初始化完成")
    
    def get_fundamental_data(self, symbol: str) -> dict:
        """获取基本面数据"""
        
        if symbol in self.cache:
            return self.cache[symbol]
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键基本面指标
            fundamental_data = {
                # 估值指标
                'pe_ratio': info.get('trailingPE', None),
                'forward_pe': info.get('forwardPE', None),
                'pb_ratio': info.get('priceToBook', None),
                'ps_ratio': info.get('priceToSalesTrailing12Months', None),
                'peg_ratio': info.get('pegRatio', None),
                'enterprise_value': info.get('enterpriseValue', None),
                'ev_revenue': info.get('enterpriseToRevenue', None),
                'ev_ebitda': info.get('enterpriseToEbitda', None),
                
                # 财务健康度
                'debt_to_equity': info.get('debtToEquity', None),
                'current_ratio': info.get('currentRatio', None),
                'quick_ratio': info.get('quickRatio', None),
                'cash_per_share': info.get('totalCashPerShare', None),
                'book_value': info.get('bookValue', None),
                
                # 盈利能力
                'profit_margin': info.get('profitMargins', None),
                'operating_margin': info.get('operatingMargins', None),
                'gross_margin': info.get('grossMargins', None),
                'roe': info.get('returnOnEquity', None),
                'roa': info.get('returnOnAssets', None),
                'roic': info.get('returnOnInvestmentCapital', None),
                
                # 成长性
                'revenue_growth': info.get('revenueGrowth', None),
                'earnings_growth': info.get('earningsGrowth', None),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', None),
                
                # 股息
                'dividend_yield': info.get('dividendYield', None),
                'payout_ratio': info.get('payoutRatio', None),
                'dividend_rate': info.get('dividendRate', None),
                
                # 市场数据
                'market_cap': info.get('marketCap', None),
                'float_shares': info.get('floatShares', None),
                'shares_outstanding': info.get('sharesOutstanding', None),
                'beta': info.get('beta', None),
                
                # 业务指标
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'business_summary': info.get('longBusinessSummary', ''),
                'full_time_employees': info.get('fullTimeEmployees', None),
                
                # 分析师评级
                'recommendation': info.get('recommendationKey', None),
                'target_price': info.get('targetMeanPrice', None),
                'analyst_count': info.get('numberOfAnalystOpinions', None)
            }
            
            self.cache[symbol] = fundamental_data
            return fundamental_data
            
        except Exception as e:
            print(f"❌ 获取 {symbol} 基本面数据失败: {e}")
            return {}
    
    def score_valuation(self, data: dict) -> float:
        """估值评分 (0-100)"""
        
        score = 0
        factors = 0
        
        # P/E ratio评分
        pe = data.get('pe_ratio')
        if pe and pe > 0:
            factors += 1
            if pe < 15:
                score += 100  # 估值便宜
            elif pe < 20:
                score += 80   # 合理估值
            elif pe < 25:
                score += 60   # 稍贵
            elif pe < 35:
                score += 40   # 较贵
            else:
                score += 20   # 很贵
        
        # P/B ratio评分
        pb = data.get('pb_ratio')
        if pb and pb > 0:
            factors += 1
            if pb < 1:
                score += 100  # 破净，可能低估
            elif pb < 2:
                score += 80   # 合理
            elif pb < 3:
                score += 60   # 一般
            elif pb < 5:
                score += 40   # 偏高
            else:
                score += 20   # 很高
        
        # PEG ratio评分
        peg = data.get('peg_ratio')
        if peg and peg > 0:
            factors += 1
            if peg < 1:
                score += 100  # 成长性好于估值
            elif peg < 1.5:
                score += 80   # 合理
            elif peg < 2:
                score += 60   # 一般
            else:
                score += 40   # 高估
        
        return score / factors if factors > 0 else 50
    
    def score_financial_health(self, data: dict) -> float:
        """财务健康度评分 (0-100)"""
        
        score = 0
        factors = 0
        
        # 债务权益比
        debt_equity = data.get('debt_to_equity')
        if debt_equity is not None:
            factors += 1
            if debt_equity < 0.3:
                score += 100  # 低负债
            elif debt_equity < 0.6:
                score += 80   # 适度负债
            elif debt_equity < 1.0:
                score += 60   # 中等负债
            elif debt_equity < 2.0:
                score += 40   # 高负债
            else:
                score += 20   # 很高负债
        
        # 流动比率
        current_ratio = data.get('current_ratio')
        if current_ratio:
            factors += 1
            if current_ratio > 2:
                score += 100  # 流动性很好
            elif current_ratio > 1.5:
                score += 80   # 流动性好
            elif current_ratio > 1.2:
                score += 60   # 流动性一般
            elif current_ratio > 1:
                score += 40   # 流动性紧张
            else:
                score += 20   # 流动性很差
        
        # ROE (净资产收益率)
        roe = data.get('roe')
        if roe:
            factors += 1
            if roe > 0.2:
                score += 100  # 盈利能力很强
            elif roe > 0.15:
                score += 80   # 盈利能力强
            elif roe > 0.1:
                score += 60   # 盈利能力一般
            elif roe > 0.05:
                score += 40   # 盈利能力弱
            else:
                score += 20   # 盈利能力很弱
        
        return score / factors if factors > 0 else 50
    
    def score_profitability(self, data: dict) -> float:
        """盈利能力评分 (0-100)"""
        
        score = 0
        factors = 0
        
        # 净利润率
        profit_margin = data.get('profit_margin')
        if profit_margin:
            factors += 1
            if profit_margin > 0.2:
                score += 100
            elif profit_margin > 0.1:
                score += 80
            elif profit_margin > 0.05:
                score += 60
            elif profit_margin > 0:
                score += 40
            else:
                score += 20
        
        # 毛利率
        gross_margin = data.get('gross_margin')
        if gross_margin:
            factors += 1
            if gross_margin > 0.5:
                score += 100
            elif gross_margin > 0.3:
                score += 80
            elif gross_margin > 0.2:
                score += 60
            elif gross_margin > 0.1:
                score += 40
            else:
                score += 20
        
        # ROA (总资产收益率)
        roa = data.get('roa')
        if roa:
            factors += 1
            if roa > 0.1:
                score += 100
            elif roa > 0.05:
                score += 80
            elif roa > 0.02:
                score += 60
            elif roa > 0:
                score += 40
            else:
                score += 20
        
        return score / factors if factors > 0 else 50
    
    def score_growth(self, data: dict) -> float:
        """成长性评分 (0-100)"""
        
        score = 0
        factors = 0
        
        # 营收增长率
        revenue_growth = data.get('revenue_growth')
        if revenue_growth is not None:
            factors += 1
            if revenue_growth > 0.3:
                score += 100  # 高增长
            elif revenue_growth > 0.2:
                score += 80   # 良好增长
            elif revenue_growth > 0.1:
                score += 60   # 适度增长
            elif revenue_growth > 0:
                score += 40   # 微增长
            else:
                score += 20   # 负增长
        
        # 盈利增长率
        earnings_growth = data.get('earnings_growth')
        if earnings_growth is not None:
            factors += 1
            if earnings_growth > 0.3:
                score += 100
            elif earnings_growth > 0.2:
                score += 80
            elif earnings_growth > 0.1:
                score += 60
            elif earnings_growth > 0:
                score += 40
            else:
                score += 20
        
        # 季度盈利增长
        quarterly_growth = data.get('earnings_quarterly_growth')
        if quarterly_growth is not None:
            factors += 1
            if quarterly_growth > 0.3:
                score += 100
            elif quarterly_growth > 0.2:
                score += 80
            elif quarterly_growth > 0.1:
                score += 60
            elif quarterly_growth > 0:
                score += 40
            else:
                score += 20
        
        return score / factors if factors > 0 else 50
    
    def score_dividend(self, data: dict) -> float:
        """股息评分 (0-100)"""
        
        dividend_yield = data.get('dividend_yield')
        payout_ratio = data.get('payout_ratio')
        
        if not dividend_yield:
            return 0  # 无股息
        
        score = 0
        
        # 股息收益率评分
        if dividend_yield > 0.06:
            score += 100  # 高股息
        elif dividend_yield > 0.04:
            score += 80   # 良好股息
        elif dividend_yield > 0.02:
            score += 60   # 适度股息
        elif dividend_yield > 0.01:
            score += 40   # 低股息
        else:
            score += 20   # 很低股息
        
        # 派息率评分
        if payout_ratio:
            if 0.3 <= payout_ratio <= 0.6:
                score += 50  # 健康派息率
            elif 0.6 < payout_ratio <= 0.8:
                score += 30  # 较高派息率
            elif payout_ratio > 0.8:
                score += 10  # 不可持续
            else:
                score += 40  # 保守派息
        
        return min(score, 100)
    
    def get_sector_industry_info(self, data: dict) -> dict:
        """获取行业板块信息"""
        
        return {
            'sector': data.get('sector', 'Unknown'),
            'industry': data.get('industry', 'Unknown'),
            'beta': data.get('beta', None)
        }
    
    def analyze_fundamentals(self, symbol: str) -> dict:
        """综合基本面分析"""
        
        print(f"📊 开始分析 {symbol} 的基本面...")
        
        # 获取基本面数据
        data = self.get_fundamental_data(symbol)
        
        if not data:
            return {
                'symbol': symbol,
                'error': '无法获取基本面数据',
                'fundamental_score': 0
            }
        
        # 各维度评分
        valuation_score = self.score_valuation(data)
        health_score = self.score_financial_health(data)
        profitability_score = self.score_profitability(data)
        growth_score = self.score_growth(data)
        dividend_score = self.score_dividend(data)
        
        # 综合基本面评分 (加权平均)
        weights = {
            'valuation': 0.25,      # 估值 25%
            'health': 0.25,         # 财务健康 25%
            'profitability': 0.20,  # 盈利能力 20%
            'growth': 0.20,         # 成长性 20%
            'dividend': 0.10        # 股息 10%
        }
        
        fundamental_score = (
            valuation_score * weights['valuation'] +
            health_score * weights['health'] +
            profitability_score * weights['profitability'] +
            growth_score * weights['growth'] +
            dividend_score * weights['dividend']
        )
        
        # 获取行业信息
        sector_info = self.get_sector_industry_info(data)
        
        result = {
            'symbol': symbol,
            'fundamental_score': round(fundamental_score, 1),
            'valuation_score': round(valuation_score, 1),
            'health_score': round(health_score, 1),
            'profitability_score': round(profitability_score, 1),
            'growth_score': round(growth_score, 1),
            'dividend_score': round(dividend_score, 1),
            'sector': sector_info['sector'],
            'industry': sector_info['industry'],
            'beta': sector_info['beta'],
            'key_metrics': {
                'pe_ratio': data.get('pe_ratio'),
                'pb_ratio': data.get('pb_ratio'),
                'roe': data.get('roe'),
                'debt_to_equity': data.get('debt_to_equity'),
                'dividend_yield': data.get('dividend_yield'),
                'revenue_growth': data.get('revenue_growth'),
                'profit_margin': data.get('profit_margin'),
                'market_cap': data.get('market_cap')
            },
            'recommendation': data.get('recommendation'),
            'target_price': data.get('target_price')
        }
        
        return result
    
    def batch_analyze(self, symbols: list) -> list:
        """批量基本面分析"""
        
        print(f"📊 开始批量基本面分析 {len(symbols)} 只股票...")
        
        results = []
        for i, symbol in enumerate(symbols, 1):
            try:
                result = self.analyze_fundamentals(symbol)
                results.append(result)
                print(f"✅ {symbol}: 基本面得分 {result.get('fundamental_score', 0):.1f} ({i}/{len(symbols)})")
            except Exception as e:
                print(f"❌ {symbol}: 分析失败 - {e} ({i}/{len(symbols)})")
                results.append({
                    'symbol': symbol,
                    'error': str(e),
                    'fundamental_score': 0
                })
        
        return results


def test_fundamental_analysis():
    """测试基本面分析"""
    
    print("🧪 测试基本面分析功能")
    print("=" * 50)
    
    analyzer = FundamentalAnalyzer()
    
    # 测试单只股票
    test_symbols = ['AAPL', 'MSFT', 'JNJ', 'JPM', 'TSLA']
    
    for symbol in test_symbols:
        print(f"\n📊 分析 {symbol}:")
        result = analyzer.analyze_fundamentals(symbol)
        
        if 'error' not in result:
            print(f"   综合得分: {result['fundamental_score']:.1f}/100")
            print(f"   估值得分: {result['valuation_score']:.1f}/100")
            print(f"   财务健康: {result['health_score']:.1f}/100")
            print(f"   盈利能力: {result['profitability_score']:.1f}/100")
            print(f"   成长性: {result['growth_score']:.1f}/100")
            print(f"   股息得分: {result['dividend_score']:.1f}/100")
            print(f"   行业: {result['sector']} - {result['industry']}")
            
            metrics = result['key_metrics']
            print(f"   关键指标:")
            print(f"     P/E: {metrics.get('pe_ratio', 'N/A')}")
            print(f"     P/B: {metrics.get('pb_ratio', 'N/A')}")
            print(f"     ROE: {metrics.get('roe', 'N/A')}")
            print(f"     股息率: {metrics.get('dividend_yield', 'N/A')}")
        else:
            print(f"   错误: {result['error']}")


if __name__ == "__main__":
    test_fundamental_analysis()