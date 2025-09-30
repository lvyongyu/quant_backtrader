#!/usr/bin/env python3
"""
通用单股分析模板
Universal Single Stock Analysis Template

支持分析任意股票的四维度综合评分
"""
import sys
import os
import warnings
warnings.filterwarnings('ignore')

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.append(src_path)

try:
    from analyzers.fundamental_analyzer import FundamentalAnalyzer
    from analyzers.market_environment import MarketEnvironmentAnalyzer  
    from analyzers.sentiment_fund_analyzer import SentimentFundAnalyzer
    ANALYZERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 分析器导入失败: {e}")
    ANALYZERS_AVAILABLE = False

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_stock_info(ticker):
    """获取股票基本信息"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'current_price': info.get('currentPrice', 0)
        }
    except:
        return {
            'name': ticker,
            'sector': 'Unknown',
            'industry': 'Unknown', 
            'market_cap': 0,
            'current_price': 0
        }

def calculate_technical_score(ticker):
    """计算技术分析得分"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return 50.0, "数据不足"
        
        current_price = hist['Close'].iloc[-1]
        
        # 计算移动平均线
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['MA50'] = hist['Close'].rolling(window=50).mean()
        
        # 趋势得分
        trend_score = 0
        if current_price > hist['MA5'].iloc[-1]:
            trend_score += 25
        if current_price > hist['MA20'].iloc[-1]:
            trend_score += 35
        if current_price > hist['MA50'].iloc[-1]:
            trend_score += 40
            
        # RSI计算
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # 动量得分 (RSI)
        if 40 <= current_rsi <= 70:
            momentum_score = 100
        elif 30 <= current_rsi <= 80:
            momentum_score = 80
        elif 20 <= current_rsi <= 85:
            momentum_score = 60
        else:
            momentum_score = 30
            
        # 波动率得分
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        if volatility < 20:
            volatility_score = 100
        elif volatility < 30:
            volatility_score = 80
        elif volatility < 40:
            volatility_score = 60
        else:
            volatility_score = 30
            
        # 成交量得分  
        avg_volume = hist['Volume'].rolling(window=20).mean().iloc[-1]
        recent_volume = hist['Volume'].iloc[-5:].mean()
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        if volume_ratio > 1.5:
            volume_score = 100
        elif volume_ratio > 1.2:
            volume_score = 80
        elif volume_ratio > 0.8:
            volume_score = 60
        else:
            volume_score = 40
            
        # 综合技术得分
        technical_score = (trend_score * 0.4 + momentum_score * 0.3 + 
                          volatility_score * 0.2 + volume_score * 0.1)
        
        details = f"趋势:{trend_score:.0f} 动量:{momentum_score:.0f} 波动:{volatility_score:.0f} 成交量:{volume_score:.0f} RSI:{current_rsi:.1f}"
        
        return technical_score, details
        
    except Exception as e:
        return 50.0, f"计算失败: {str(e)}"

def analyze_single_stock(ticker, stock_name=None):
    """分析单只股票"""
    print(f"\n🔍 {ticker} 股票四维度深度分析")
    print("=" * 60)
    
    # 获取股票基本信息
    stock_info = get_stock_info(ticker)
    if stock_name:
        stock_info['name'] = stock_name
    
    print(f"📊 股票信息:")
    print(f"   代码: {ticker}")
    print(f"   名称: {stock_info['name']}")
    print(f"   行业: {stock_info['sector']} - {stock_info['industry']}")
    print(f"   当前价格: ${stock_info['current_price']:.2f}")
    if stock_info['market_cap'] > 0:
        market_cap_b = stock_info['market_cap'] / 1e9
        print(f"   市值: ${market_cap_b:.1f}B")
    
    print(f"\n📈 四维度分析结果:")
    print("-" * 60)
    
    # 1. 技术分析 (40% 权重)
    tech_score, tech_details = calculate_technical_score(ticker)
    print(f"🔧 技术分析 (权重40%): {tech_score:.1f}/100")
    print(f"   详情: {tech_details}")
    
    # 2. 基本面分析 (25% 权重) 
    fundamental_score = 50.0
    fundamental_details = "需要分析器支持"
    if ANALYZERS_AVAILABLE:
        try:
            analyzer = FundamentalAnalyzer()
            fundamental_result = analyzer.analyze(ticker)
            if fundamental_result and 'score' in fundamental_result:
                fundamental_score = fundamental_result['score']
                fundamental_details = f"PE:{fundamental_result.get('pe', 'N/A')} PB:{fundamental_result.get('pb', 'N/A')} ROE:{fundamental_result.get('roe', 'N/A')}"
        except:
            pass
    
    print(f"📊 基本面分析 (权重25%): {fundamental_score:.1f}/100")
    print(f"   详情: {fundamental_details}")
    
    # 3. 市场环境分析 (20% 权重)
    market_score = 75.0
    market_details = "市场环境良好"
    if ANALYZERS_AVAILABLE:
        try:
            analyzer = MarketEnvironmentAnalyzer()
            market_result = analyzer.analyze()
            if market_result and 'score' in market_result:
                market_score = market_result['score'] 
                market_details = market_result.get('description', '市场环境分析')
        except:
            pass
    
    print(f"🌍 市场环境分析 (权重20%): {market_score:.1f}/100")
    print(f"   详情: {market_details}")
    
    # 4. 情绪资金面分析 (15% 权重)
    sentiment_score = 60.0
    sentiment_details = "情绪资金面中性"
    if ANALYZERS_AVAILABLE:
        try:
            analyzer = SentimentFundAnalyzer()
            sentiment_result = analyzer.analyze(ticker)
            if sentiment_result and 'score' in sentiment_result:
                sentiment_score = sentiment_result['score']
                sentiment_details = sentiment_result.get('description', '情绪资金面分析')
        except:
            pass
    
    print(f"🎭 情绪资金面分析 (权重15%): {sentiment_score:.1f}/100")
    print(f"   详情: {sentiment_details}")
    
    # 计算综合得分
    total_score = (tech_score * 0.4 + fundamental_score * 0.25 + 
                   market_score * 0.2 + sentiment_score * 0.15)
    
    print(f"\n🏆 {ticker} 四维度综合得分: {total_score:.1f}/100")
    print(f"📊 构成: 技术{tech_score:.1f}(40%) + 基本面{fundamental_score:.1f}(25%) + 市场{market_score:.1f}(20%) + 情绪{sentiment_score:.1f}(15%)")
    
    # 投资建议
    if total_score >= 85:
        recommendation = "🟢 强烈推荐 - 优质投资标的"
    elif total_score >= 75:
        recommendation = "🟡 推荐 - 可适量配置"
    elif total_score >= 65:
        recommendation = "🔸 谨慎 - 需密切关注"
    elif total_score >= 50:
        recommendation = "🔶 观望 - 等待更好时机"
    else:
        recommendation = "🔴 避免 - 风险较高"
    
    print(f"📈 投资建议: {recommendation}")
    print("=" * 60)
    
    return {
        'symbol': ticker,
        'name': stock_info['name'],
        'total_score': total_score,
        'technical_score': tech_score,
        'fundamental_score': fundamental_score,
        'market_score': market_score,
        'sentiment_score': sentiment_score,
        'recommendation': recommendation,
        'current_price': stock_info['current_price']
    }

def main():
    """主函数"""
    # 支持命令行参数
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
        stock_name = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # 默认分析HWM
        ticker = 'HWM'
        stock_name = 'Howmet Aerospace'
    
    try:
        result = analyze_single_stock(ticker, stock_name)
        return result
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

if __name__ == "__main__":
    main()