#!/usr/bin/env python3
"""
简化版股票筛选器 - 中国投资者版
Simplified Stock Screener for Chinese Investors

专门筛选中国投资者常关注的美股、港股和中概股
"""

import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_popular_chinese_stocks():
    """获取中国投资者常关注的股票列表"""
    
    stocks = {
        "🇺🇸 热门美股": [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META',
            'JPM', 'BAC', 'V', 'MA', 'WMT', 'HD', 'PG', 'JNJ', 'KO'
        ],
        "🏢 中概股": [
            'BABA', 'JD', 'PDD', 'BIDU', 'NIO', 'XPEV', 'LI', 
            'BILI', 'TME', 'NTES', 'VIPS', 'IQ', 'DIDI'
        ],
        "🎮 科技成长股": [
            'RBLX', 'COIN', 'PLTR', 'SNOW', 'ZM', 'SQ', 'ROKU',
            'PTON', 'DDOG', 'CRM', 'OKTA', 'TWLO'
        ],
        "💰 金融股": [
            'GS', 'MS', 'WFC', 'C', 'USB', 'PNC', 'TFC', 'COF'
        ],
        "🛒 消费股": [
            'NKE', 'SBUX', 'MCD', 'TGT', 'COST', 'LOW', 'DIS', 'NFLX'
        ]
    }
    
    all_stocks = []
    for category, symbols in stocks.items():
        all_stocks.extend(symbols)
    
    print("📊 股票分类:")
    for category, symbols in stocks.items():
        print(f"   {category}: {len(symbols)}只")
    print(f"📈 总计: {len(all_stocks)}只股票")
    
    return all_stocks

def calculate_stock_score(symbol):
    """计算单只股票的综合得分"""
    
    try:
        # 获取数据
        stock = yf.Ticker(symbol)
        df = stock.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 20:
            return None
        
        # 基础数据
        current_price = df['Close'].iloc[-1]
        volumes = df['Volume']
        prices = df['Close']
        
        # 1. 趋势分析 (30分)
        sma_5 = prices.rolling(5).mean().iloc[-1]
        sma_20 = prices.rolling(20).mean().iloc[-1]
        trend_score = 0
        
        if current_price > sma_5:
            trend_score += 10
        if current_price > sma_20:
            trend_score += 10
        if sma_5 > sma_20:
            trend_score += 10
        
        # 2. 动量分析 (25分)
        returns_1w = (current_price / prices.iloc[-6] - 1) * 100 if len(prices) >= 6 else 0
        returns_1m = (current_price / prices.iloc[-21] - 1) * 100 if len(prices) >= 21 else 0
        
        momentum_score = 0
        if returns_1w > 0:
            momentum_score += 12
        if returns_1m > 0:
            momentum_score += 13
        
        # 3. 成交量分析 (20分)
        avg_volume = volumes.tail(20).mean()
        current_volume = volumes.iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        volume_score = 0
        if volume_ratio > 1.2:
            volume_score += 15
        elif volume_ratio > 1.0:
            volume_score += 10
        else:
            volume_score += 5
        
        if volumes.tail(5).mean() > volumes.tail(20).mean():
            volume_score += 5
        
        # 4. 波动率分析 (15分)
        daily_returns = prices.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        volatility_score = 0
        if volatility < 20:
            volatility_score += 15  # 低波动
        elif volatility < 35:
            volatility_score += 12  # 中波动
        elif volatility < 50:
            volatility_score += 8   # 高波动
        else:
            volatility_score += 3   # 极高波动
        
        # 5. 技术指标分析 (10分)
        # 简化RSI
        delta = daily_returns
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        technical_score = 0
        if 30 <= rsi <= 70:
            technical_score += 10
        elif rsi < 30:
            technical_score += 7  # 超卖
        else:
            technical_score += 5  # 超买
        
        # 总分计算
        total_score = trend_score + momentum_score + volume_score + volatility_score + technical_score
        
        # 加分项
        bonus = 0
        if current_price == prices.tail(10).max():  # 近期新高
            bonus += 5
        if volume_ratio > 2.0:  # 成交量爆发
            bonus += 3
        
        total_score += bonus
        total_score = min(total_score, 100)
        
        return {
            'symbol': symbol,
            'score': round(total_score, 1),
            'price': round(current_price, 2),
            'trend_score': trend_score,
            'momentum_score': momentum_score,
            'volume_score': round(volume_score, 1),
            'volatility_score': volatility_score,
            'technical_score': technical_score,
            'returns_1w': round(returns_1w, 2),
            'returns_1m': round(returns_1m, 2),
            'volume_ratio': round(volume_ratio, 2),
            'volatility': round(volatility, 1),
            'rsi': round(rsi, 1) if not pd.isna(rsi) else 50,
            'bonus': bonus
        }
        
    except Exception as e:
        print(f"❌ {symbol}: {e}")
        return None

def screen_stocks_fast():
    """快速筛选股票"""
    
    print("🎯 简化版股票筛选器")
    print("🇨🇳 专为中国投资者定制")
    print("=" * 60)
    
    # 获取股票列表
    symbols = get_popular_chinese_stocks()
    
    print(f"\n🔍 开始筛选...")
    start_time = time.time()
    
    results = []
    failed = []
    
    # 并行处理
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_symbol = {
            executor.submit(calculate_stock_score, symbol): symbol 
            for symbol in symbols
        }
        
        for i, future in enumerate(as_completed(future_to_symbol), 1):
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    print(f"✅ {symbol}: {result['score']}分 ({i}/{len(symbols)})")
                else:
                    failed.append(symbol)
                    print(f"❌ {symbol}: 失败 ({i}/{len(symbols)})")
            except Exception as e:
                failed.append(symbol)
                print(f"❌ {symbol}: {e} ({i}/{len(symbols)})")
    
    # 排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  筛选完成，用时: {elapsed:.1f}秒")
    print(f"✅ 成功: {len(results)}只")
    print(f"❌ 失败: {len(failed)}只")
    
    return results

def display_top3(results):
    """显示TOP3结果"""
    
    if len(results) < 3:
        print(f"⚠️ 结果不足3只股票")
        return results[:len(results)]
    
    top3 = results[:3]
    
    print(f"\n🏆 TOP3 最值得买入的股票")
    print("=" * 60)
    
    for i, stock in enumerate(top3, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        
        print(f"\n{emoji} 第{i}名: {stock['symbol']}")
        print(f"   💯 综合得分: {stock['score']}/100")
        print(f"   💰 当前价格: ${stock['price']}")
        print(f"   📊 涨跌幅: 周 {stock['returns_1w']:+.1f}% | 月 {stock['returns_1m']:+.1f}%")
        print(f"   📈 技术指标: RSI {stock['rsi']:.0f} | 波动率 {stock['volatility']:.1f}%")
        print(f"   📊 成交量比: {stock['volume_ratio']:.1f}x")
        
        # 分析点评
        if stock['score'] >= 80:
            rating = "🔥 强烈推荐"
        elif stock['score'] >= 70:
            rating = "👍 推荐买入"
        elif stock['score'] >= 60:
            rating = "✨ 谨慎买入"
        else:
            rating = "⚠️ 观望等待"
        
        print(f"   🎯 投资建议: {rating}")
        
        if stock['bonus'] > 0:
            print(f"   🎁 特殊加分: +{stock['bonus']}分")
    
    return top3

def display_detailed_results(results, top_n=15):
    """显示详细结果"""
    
    print(f"\n📊 详细排名 (TOP{min(top_n, len(results))})")
    print("=" * 100)
    
    print(f"{'排名':>4} {'股票':>8} {'总分':>6} {'价格':>8} {'周涨幅':>8} "
          f"{'月涨幅':>8} {'成交比':>7} {'RSI':>5} {'波动率':>7} {'评级':>8}")
    print("-" * 100)
    
    for i, stock in enumerate(results[:top_n], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        
        if stock['score'] >= 80:
            rating = "🔥强推"
        elif stock['score'] >= 70:
            rating = "👍推荐"
        elif stock['score'] >= 60:
            rating = "✨谨慎"
        else:
            rating = "⚠️观望"
        
        print(f"{medal}{i:>2} {stock['symbol']:>8} {stock['score']:>6.1f} "
              f"${stock['price']:>7.2f} {stock['returns_1w']:>+7.1f}% "
              f"{stock['returns_1m']:>+7.1f}% {stock['volume_ratio']:>7.1f} "
              f"{stock['rsi']:>5.0f} {stock['volatility']:>6.1f}% {rating:>8}")

def save_results(results):
    """保存结果"""
    
    if not results:
        return
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"简化股票筛选结果_{timestamp}.csv"
        
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 结果已保存: {filename}")
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")

def main():
    """主程序"""
    
    try:
        # 筛选股票
        results = screen_stocks_fast()
        
        if not results:
            print("❌ 没有获得有效结果")
            return
        
        # 显示TOP3
        top3 = display_top3(results)
        
        # 显示详细结果
        display_detailed_results(results)
        
        # 保存结果
        save_results(results)
        
        # 投资建议
        print(f"\n" + "=" * 60)
        print("💡 投资建议总结")
        print("=" * 60)
        
        if len(top3) >= 3:
            print(f"🚀 最值得买入的TOP3股票:")
            for i, stock in enumerate(top3, 1):
                print(f"   {i}. {stock['symbol']} - {stock['score']:.1f}分")
            
            print(f"\n📊 选股逻辑:")
            print("• 趋势分析: 股价位于均线之上")
            print("• 动量分析: 近期涨跌幅表现")
            print("• 成交量: 资金关注度和活跃度")
            print("• 波动率: 风险收益比评估")
            print("• 技术面: RSI等技术指标健康度")
            
            print(f"\n⚠️ 风险提示:")
            print("• 本分析基于技术面，仅供参考")
            print("• 投资需结合基本面和市场环境")
            print("• 注意仓位管理和止损设置")
            print("• 分散投资，不要ALL-IN单一股票")
        
        print(f"\n🎉 筛选完成! 祝您投资顺利! 📈")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断")
    except Exception as e:
        print(f"❌ 程序异常: {e}")

if __name__ == '__main__':
    main()