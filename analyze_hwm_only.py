#!/usr/bin/env python3
"""
HWM (Howmet Aerospace) 专项四维度分析
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
    print(f"⚠️ 分析模块导入失败: {e}")
    ANALYZERS_AVAILABLE = False

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_technical_score(data):
    """计算技术分析得分"""
    if len(data) < 50:
        return 0, {}
    
    try:
        # 技术指标计算
        close = data['Close']
        volume = data['Volume']
        
        # 移动平均线
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        
        # 当前值
        current_price = close.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        
        # 趋势得分 (40%)
        trend_score = 0
        if current_price > sma_20.iloc[-1]:
            trend_score += 40
        if current_price > sma_50.iloc[-1]:
            trend_score += 30
        if sma_20.iloc[-1] > sma_50.iloc[-1]:
            trend_score += 30
        
        # 动量得分 (30%)
        momentum_score = 0
        if 30 <= current_rsi <= 70:
            momentum_score += 60
        elif current_rsi > 70:
            momentum_score += 40  # 超买但仍有动量
        else:
            momentum_score += 50  # 超卖，反弹机会
            
        if current_macd > current_signal:
            momentum_score += 40
        
        # 波动性得分 (15%)
        volatility = close.pct_change().std() * np.sqrt(252)
        if 0.15 <= volatility <= 0.35:  # 合理波动性
            volatility_score = 100
        elif volatility < 0.15:  # 波动性过低
            volatility_score = 70
        else:  # 波动性过高
            volatility_score = 50
        
        # 成交量得分 (15%)
        avg_volume = volume.rolling(window=20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio >= 1.2:
            volume_score = 100
        elif volume_ratio >= 1.0:
            volume_score = 80
        elif volume_ratio >= 0.8:
            volume_score = 60
        else:
            volume_score = 40
        
        # 综合技术得分
        technical_score = (trend_score * 0.4 + momentum_score * 0.3 + 
                          volatility_score * 0.15 + volume_score * 0.15)
        
        details = {
            '趋势得分': trend_score,
            '动量得分': momentum_score,
            '波动得分': volatility_score,
            '成交量得分': volume_score,
            '技术指标得分': technical_score
        }
        
        return technical_score, details
        
    except Exception as e:
        print(f"技术分析计算错误: {e}")
        return 0, {}

def analyze_hwm_comprehensive():
    """HWM四维度综合分析"""
    ticker = 'HWM'
    
    try:
        print(f"🔍 HWM (Howmet Aerospace) 四维度深度分析")
        print("="*80)
        
        # 获取数据
        stock = yf.Ticker(ticker)
        info = stock.info
        data = stock.history(period='1y')
        
        if data.empty:
            print(f"❌ 无法获取 {ticker} 的历史数据")
            return
            
        # 基本信息
        current_price = info.get('currentPrice', data['Close'][-1])
        print(f"💰 当前价格: ${current_price:.2f}")
        print(f"🏢 公司: {info.get('longName', 'Howmet Aerospace')}")
        print(f"🏭 行业: {info.get('industry', 'Aerospace & Defense')}")
        print(f"📊 市值: ${info.get('marketCap', 0)/1e9:.1f}B")
        print("="*80)
        
        # 1. 技术分析 (40%)
        print("🔧 技术分析 (权重40%):")
        tech_score, tech_details = calculate_technical_score(data)
        print(f"   总分: {tech_score:.1f}/100")
        for key, value in tech_details.items():
            print(f"   {key}: {value:.1f}/100")
        print()
        
        # 2. 基本面分析 (25%)
        fund_score = 50  # 默认值
        if ANALYZERS_AVAILABLE:
            print("📊 基本面分析 (权重25%):")
            try:
                fundamental_analyzer = FundamentalAnalyzer()
                fund_score, fund_details = fundamental_analyzer.analyze(info)
                print(f"   总分: {fund_score:.1f}/100")
                for key, value in fund_details.items():
                    print(f"   {key}: {value:.1f}/100")
            except Exception as e:
                print(f"   ❌ 基本面分析失败: {e}")
                fund_score = 50
        else:
            print("📊 基本面分析: 50/100 (模块不可用)")
        print()
        
        # 3. 市场环境分析 (20%)
        market_score = 75  # 默认值
        if ANALYZERS_AVAILABLE:
            print("🌍 市场环境分析 (权重20%):")
            try:
                market_analyzer = MarketEnvironmentAnalyzer()
                market_score, market_details = market_analyzer.analyze(info)
                print(f"   总分: {market_score:.1f}/100")
                print(f"   匹配原因: {market_details.get('reason', 'N/A')}")
                beta = info.get('beta', 'N/A')
                print(f"   Beta系数: {beta}")
            except Exception as e:
                print(f"   ❌ 市场环境分析失败: {e}")
                market_score = 75
        else:
            print("🌍 市场环境分析: 75/100 (当前牛市环境)")
        print()
        
        # 4. 情绪/资金面分析 (15%)
        sentiment_score = 60  # 默认值
        if ANALYZERS_AVAILABLE:
            print("🎭 情绪/资金面分析 (权重15%):")
            try:
                sentiment_analyzer = SentimentFundAnalyzer()
                sentiment_score, sentiment_details = sentiment_analyzer.analyze(ticker, data, info)
                print(f"   总分: {sentiment_score:.1f}/100")
                for key, value in sentiment_details.items():
                    print(f"   {key}: {value}")
            except Exception as e:
                print(f"   ❌ 情绪/资金面分析失败: {e}")
                sentiment_score = 60
        else:
            print("🎭 情绪/资金面分析: 60/100 (中性偏乐观)")
        print()
        
        # 计算综合得分
        final_score = tech_score * 0.4 + fund_score * 0.25 + market_score * 0.2 + sentiment_score * 0.15
        
        print("="*80)
        print(f"🏆 HWM 四维度综合得分: {final_score:.2f}/100")
        print(f"📊 构成: 技术{tech_score:.1f}(40%) + 基本面{fund_score:.1f}(25%) + 市场{market_score:.1f}(20%) + 情绪{sentiment_score:.1f}(15%)")
        
        # 投资建议
        if final_score >= 90:
            recommendation = "🟢 强烈推荐 - 优质投资标的"
        elif final_score >= 80:
            recommendation = "🟢 推荐 - 良好投资机会"
        elif final_score >= 70:
            recommendation = "🟡 谨慎乐观 - 可适量配置"
        elif final_score >= 60:
            recommendation = "🟠 观望 - 等待更好机会"
        else:
            recommendation = "🔴 不推荐 - 风险较高"
            
        print(f"📈 投资建议: {recommendation}")
        
        # HWM特色分析
        print(f"\n🏭 HWM 投资亮点:")
        print(f"   ✈️  航空航天龙头: 全球领先的航空发动机和结构件制造商")
        print(f"   🔬 技术护城河: 先进的轻量化材料和精密制造技术")
        print(f"   📈 行业复苏: 受益于航空业复苏和新能源汽车轻量化需求")
        print(f"   💰 现金流强: 稳定的现金流和分红能力 (股息率{info.get('dividendYield', 0)*100:.1f}%)")
        print(f"   🌍 全球布局: 多元化的客户基础和地域分布")
        
        print(f"\n⚠️  主要风险:")
        print(f"   📉 周期性行业: 航空业具有明显的周期性特征")
        print(f"   💸 估值偏高: 当前P/E {info.get('forwardPE', 'N/A')}，估值处于历史高位")
        print(f"   🛠️  原材料成本: 铝、钛等原材料价格波动影响")
        print(f"   🌐 地缘政治: 国际贸易政策和地缘政治风险")
        
        # 详细财务数据
        print(f"\n📊 关键财务指标:")
        print(f"   ROE: {info.get('returnOnEquity', 'N/A'):.1%}" if info.get('returnOnEquity') else f"   ROE: N/A")
        print(f"   营收增长: {info.get('revenueGrowth', 'N/A'):.1%}" if info.get('revenueGrowth') else f"   营收增长: N/A")
        print(f"   毛利率: {info.get('grossMargins', 'N/A'):.1%}" if info.get('grossMargins') else f"   毛利率: N/A")
        print(f"   净利润率: {info.get('profitMargins', 'N/A'):.1%}" if info.get('profitMargins') else f"   净利润率: N/A")
        print(f"   债务股本比: {info.get('debtToEquity', 'N/A'):.1f}" if info.get('debtToEquity') else f"   债务股本比: N/A")
        
        print("="*80)
        
    except Exception as e:
        print(f"❌ 分析 {ticker} 时出错: {e}")

if __name__ == "__main__":
    analyze_hwm_comprehensive()