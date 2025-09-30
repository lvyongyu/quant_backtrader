#!/usr/bin/env python3
"""
MSTR股票四维度分析脚本 - 基于现有股票筛选器
"""
import yfinance as yf
import json
import os

def analyze_mstr_simple():
    """使用yfinance简单分析MSTR"""
    ticker = 'MSTR'
    
    try:
        print(f"🔍 正在分析 {ticker} (MicroStrategy)")
        print("="*80)
        
        # 获取股票信息
        stock = yf.Ticker(ticker)
        info = stock.info
        data = stock.history(period='6mo')
        
        if data.empty:
            print(f"❌ 无法获取 {ticker} 的数据")
            return
            
        # 基本信息
        current_price = info.get('currentPrice', data['Close'][-1])
        print(f"� 当前价格: ${current_price:.2f}")
        print(f"🏢 公司名称: {info.get('longName', 'MicroStrategy')}")
        print(f"🏭 行业: {info.get('industry', 'N/A')}")
        print(f"� 板块: {info.get('sector', 'N/A')}")
        
        market_cap = info.get('marketCap', 0)
        if market_cap:
            print(f"📊 市值: ${market_cap/1e9:.1f}B")
        
        print("\n📋 关键财务指标:")
        print(f"   P/E比率: {info.get('forwardPE', info.get('trailingPE', 'N/A'))}")
        print(f"   P/B比率: {info.get('priceToBook', 'N/A')}")
        print(f"   Beta系数: {info.get('beta', 'N/A')}")
        print(f"   ROE: {info.get('returnOnEquity', 'N/A')}")
        print(f"   债务股本比: {info.get('debtToEquity', 'N/A')}")
        print(f"   营收增长: {info.get('revenueGrowth', 'N/A')}")
        
        # 价格区间
        print(f"\n📈 价格区间:")
        print(f"   52周高点: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
        print(f"   52周低点: ${info.get('fiftyTwoWeekLow', 'N/A')}")
        print(f"   200日均线: ${info.get('twoHundredDayAverage', 'N/A')}")
        print(f"   50日均线: ${info.get('fiftyDayAverage', 'N/A')}")
        
        # 简单技术指标
        if len(data) >= 20:
            sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(window=50).mean().iloc[-1] if len(data) >= 50 else None
            
            print(f"\n🔧 技术指标:")
            print(f"   20日均线: ${sma_20:.2f}")
            if sma_50:
                print(f"   50日均线: ${sma_50:.2f}")
            
            # RSI计算
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            print(f"   RSI(14): {current_rsi:.1f}")
            
            # 价格动能
            price_change_20d = ((current_price - data['Close'].iloc[-20]) / data['Close'].iloc[-20]) * 100
            print(f"   20日涨跌幅: {price_change_20d:.1f}%")
        
        # 成交量分析
        avg_volume = data['Volume'].rolling(window=20).mean().iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume
        
        print(f"\n📊 成交量分析:")
        print(f"   平均成交量(20日): {avg_volume:,.0f}")
        print(f"   最新成交量: {current_volume:,.0f}")
        print(f"   成交量比率: {volume_ratio:.2f}x")
        
        # MSTR特殊性分析 - 比特币相关性
        print(f"\n🟠 MicroStrategy特殊分析:")
        print(f"   💎 比特币持有公司: MSTR是全球最大的企业比特币持有者之一")
        print(f"   📈 比特币敏感性: 股价与比特币价格高度相关")
        print(f"   ⚡ 波动性: 由于比特币敞口，波动性通常高于传统软件股")
        print(f"   🎯 投资逻辑: 可作为比特币的间接投资工具")
        
        # 分析当前状态下的建议
        print(f"\n� 投资分析:")
        
        # 技术面判断
        if len(data) >= 20:
            if current_price > sma_20:
                tech_signal = "🟢 技术面偏多"
            else:
                tech_signal = "🔴 技术面偏空"
        else:
            tech_signal = "⚪ 数据不足"
            
        print(f"   {tech_signal}")
        
        # 估值判断
        pe = info.get('forwardPE', info.get('trailingPE'))
        if pe and isinstance(pe, (int, float)) and pe > 0:
            if pe < 15:
                valuation = "🟢 估值偏低"
            elif pe < 25:
                valuation = "🟡 估值合理"
            else:
                valuation = "🔴 估值偏高"
        else:
            valuation = "⚪ 估值数据不足"
            
        print(f"   {valuation}")
        
        # 风险提示
        print(f"\n⚠️ 风险提示:")
        print(f"   � 高波动性: 受比特币价格波动影响较大")
        print(f"   📊 宏观敏感: 对利率政策和加密货币监管政策敏感")
        print(f"   � 资金密集: 大量债务用于购买比特币，存在财务杠杆风险")
        
        print("="*80)
        
        # 添加到自选股
        add_to_watchlist(ticker, current_price, f"手动分析-{ticker}")
        
    except Exception as e:
        print(f"❌ 分析 {ticker} 时出错: {e}")

def add_to_watchlist(symbol, price, note=""):
    """添加到自选股"""
    try:
        watchlist_file = os.path.join(os.path.dirname(__file__), 'data', 'watchlist.json')
        
        # 读取现有数据
        if os.path.exists(watchlist_file):
            with open(watchlist_file, 'r', encoding='utf-8') as f:
                watchlist = json.load(f)
        else:
            watchlist = {"stocks": []}
        
        # 检查是否已存在
        existing = next((item for item in watchlist["stocks"] if item["symbol"] == symbol), None)
        
        if existing:
            existing["current_price"] = price
            existing["updated_at"] = str(datetime.now())
            if note:
                existing["note"] = note
            print(f"📝 更新自选股: {symbol} (价格: ${price:.2f})")
        else:
            from datetime import datetime
            new_stock = {
                "symbol": symbol,
                "current_price": price,
                "added_at": str(datetime.now()),
                "updated_at": str(datetime.now()),
                "note": note
            }
            watchlist["stocks"].append(new_stock)
            print(f"➕ 添加到自选股: {symbol} (价格: ${price:.2f})")
        
        # 保存
        os.makedirs(os.path.dirname(watchlist_file), exist_ok=True)
        with open(watchlist_file, 'w', encoding='utf-8') as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"❌ 自选股操作失败: {e}")

if __name__ == "__main__":
    analyze_mstr_simple()