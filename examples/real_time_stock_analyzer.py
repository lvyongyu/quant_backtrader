#!/usr/bin/env python3
"""
基于真实数据的股票分析工具
使用requests直接调用Yahoo Finance API避免复杂依赖
"""

import sys
import json
import datetime
from typing import Dict, List, Tuple
import time

def get_stock_price_simple(symbol: str) -> Dict:
    """
    使用简单HTTP请求获取股票价格，避免复杂依赖
    """
    try:
        import requests
        
        # Yahoo Finance API端点
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['chart']['result'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('previousClose', current_price)
                
                # 获取历史价格（最近20个交易日）
                timestamps = result['timestamp'][-20:] if 'timestamp' in result else []
                prices_data = result['indicators']['quote'][0]
                closes = prices_data['close'][-20:] if 'close' in prices_data else [current_price] * 20
                
                # 清理None值
                clean_closes = [p for p in closes if p is not None]
                if len(clean_closes) < 10:
                    clean_closes = [current_price] * 20
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'prev_close': prev_close,
                    'prices': clean_closes,
                    'success': True,
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
        return {'success': False, 'error': 'No data found'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def calculate_technical_indicators(prices: List[float]) -> Dict:
    """计算技术指标"""
    
    if len(prices) < 10:
        return {}
    
    current_price = prices[-1]
    
    # 移动平均线
    sma_10 = sum(prices[-10:]) / 10
    sma_20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else sma_10
    
    # RSI计算
    def calculate_rsi(prices, period=14):
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    rsi = calculate_rsi(prices)
    
    # 布林带
    period = min(20, len(prices))
    recent_prices = prices[-period:]
    bb_middle = sum(recent_prices) / len(recent_prices)
    
    # 标准差计算
    variance = sum((p - bb_middle) ** 2 for p in recent_prices) / len(recent_prices)
    std_dev = variance ** 0.5
    
    bb_upper = bb_middle + (2 * std_dev)
    bb_lower = bb_middle - (2 * std_dev)
    
    return {
        'current_price': current_price,
        'sma_10': sma_10,
        'sma_20': sma_20,
        'rsi': rsi,
        'bb_upper': bb_upper,
        'bb_middle': bb_middle,
        'bb_lower': bb_lower
    }

def generate_trading_signals(indicators: Dict) -> Dict:
    """生成交易信号"""
    
    if not indicators:
        return {}
    
    current_price = indicators['current_price']
    sma_10 = indicators['sma_10']
    sma_20 = indicators['sma_20']
    rsi = indicators['rsi']
    bb_upper = indicators['bb_upper']
    bb_lower = indicators['bb_lower']
    
    signals = {
        'sma_signal': 'NEUTRAL',
        'rsi_signal': 'NEUTRAL',
        'bb_signal': 'NEUTRAL',
        'overall': 'NEUTRAL'
    }
    
    # SMA信号
    if sma_10 > sma_20 * 1.02:
        signals['sma_signal'] = 'BUY'
    elif sma_10 < sma_20 * 0.98:
        signals['sma_signal'] = 'SELL'
    
    # RSI信号
    if rsi < 30:
        signals['rsi_signal'] = 'BUY'
    elif rsi > 70:
        signals['rsi_signal'] = 'SELL'
    
    # 布林带信号
    if current_price < bb_lower * 1.01:
        signals['bb_signal'] = 'BUY'
    elif current_price > bb_upper * 0.99:
        signals['bb_signal'] = 'SELL'
    
    # 综合信号
    buy_count = sum(1 for s in signals.values() if s == 'BUY')
    sell_count = sum(1 for s in signals.values() if s == 'SELL')
    
    if buy_count >= 2:
        signals['overall'] = 'BUY'
    elif sell_count >= 2:
        signals['overall'] = 'SELL'
    
    return signals

def calculate_score_and_recommendation(indicators: Dict, signals: Dict) -> Tuple[int, str]:
    """计算综合评分和投资建议"""
    
    if not indicators or not signals:
        return 5, "数据不足"
    
    score = 5
    buy_signals = sum(1 for s in signals.values() if s == 'BUY')
    sell_signals = sum(1 for s in signals.values() if s == 'SELL')
    
    score += buy_signals - sell_signals
    score = max(1, min(9, score))
    
    if buy_signals >= 2:
        recommendation = "买入"
    elif buy_signals > sell_signals:
        recommendation = "弱势买入"
    elif sell_signals >= 2:
        recommendation = "卖出"
    elif sell_signals > buy_signals:
        recommendation = "弱势卖出"
    else:
        recommendation = "持有"
    
    return score, recommendation

def print_analysis_report(symbol: str, stock_data: Dict, indicators: Dict, signals: Dict, score: int, recommendation: str):
    """打印分析报告"""
    
    print(f"📈 实时股票分析 - {symbol}")
    print("=" * 60)
    
    if not stock_data.get('success'):
        print(f"❌ 获取{symbol}数据失败: {stock_data.get('error', '未知错误')}")
        return
    
    current_price = indicators['current_price']
    prev_close = stock_data['prev_close']
    price_change = current_price - prev_close
    price_change_pct = (price_change / prev_close) * 100
    
    print(f"🏷️  股票代码: {symbol}")
    print(f"💰 当前价格: ${current_price:.2f}")
    print(f"📊 价格变化: ${price_change:+.2f} ({price_change_pct:+.1f}%)")
    print(f"📅 更新时间: {stock_data['timestamp']}")
    
    print(f"\n📊 技术指标:")
    print(f"   10日均线: ${indicators['sma_10']:.2f}")
    print(f"   20日均线: ${indicators['sma_20']:.2f}")
    print(f"   RSI(14): {indicators['rsi']:.1f}")
    print(f"   布林带上轨: ${indicators['bb_upper']:.2f}")
    print(f"   布林带中轨: ${indicators['bb_middle']:.2f}")
    print(f"   布林带下轨: ${indicators['bb_lower']:.2f}")
    
    print(f"\n🚦 交易信号:")
    signal_emojis = {'BUY': '🟢', 'SELL': '🔴', 'NEUTRAL': '🟡'}
    for signal_name, signal_value in signals.items():
        if signal_name != 'overall':
            emoji = signal_emojis[signal_value]
            display_name = signal_name.replace('_signal', '').upper()
            print(f"   {emoji} {display_name}: {signal_value}")
    
    print(f"\n🎯 综合评估:")
    print(f"   评分: {score}/9 分")
    print(f"   投资建议: {recommendation}")
    print(f"   综合信号: {signal_emojis[signals['overall']]} {signals['overall']}")
    
    # 风险建议
    print(f"\n💡 投资建议:")
    if score >= 7:
        print(f"   ✅ 技术面偏多，建议适量配置")
        print(f"   📈 止损参考: ${current_price * 0.95:.2f} (-5%)")
    elif score >= 5:
        print(f"   🔄 技术面中性，建议观望或小仓位")
        print(f"   ⚖️ 关注突破确认信号")
    else:
        print(f"   ⚠️  技术面偏弱，建议谨慎")
        print(f"   📉 反弹阻力: ${current_price * 1.05:.2f} (+5%)")

def main():
    """主函数"""
    
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'AAPL'
    
    print("🔍 正在获取实时数据...")
    
    # 获取股票数据
    stock_data = get_stock_price_simple(symbol)
    
    if not stock_data.get('success'):
        print(f"❌ 无法获取{symbol}数据: {stock_data.get('error')}")
        print("💡 请检查网络连接或股票代码是否正确")
        return
    
    # 计算技术指标
    indicators = calculate_technical_indicators(stock_data['prices'])
    
    if not indicators:
        print("❌ 数据不足，无法计算技术指标")
        return
    
    # 生成交易信号
    signals = generate_trading_signals(indicators)
    
    # 计算评分和建议
    score, recommendation = calculate_score_and_recommendation(indicators, signals)
    
    # 打印报告
    print_analysis_report(symbol, stock_data, indicators, signals, score, recommendation)
    
    print(f"\n🎉 {symbol} 实时分析完成!")
    print("📊 数据来源: Yahoo Finance")
    print("⚠️  仅供参考，投资有风险")

if __name__ == "__main__":
    main()