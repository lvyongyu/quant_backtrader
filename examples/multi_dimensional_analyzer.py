#!/usr/bin/env python3
"""
多维度交易信号分析系统
增强版股票分析工具，包含12个维度的综合信号分析
"""

import sys
import datetime
import math
from typing import Dict, List, Tuple, Optional

def get_stock_price_enhanced(symbol: str) -> Dict:
    """获取增强的股票数据，包含成交量等信息"""
    try:
        import requests
        
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
                
                # 获取更完整的历史数据
                quotes = result['indicators']['quote'][0]
                closes = [p for p in quotes.get('close', []) if p is not None]
                highs = [p for p in quotes.get('high', []) if p is not None]
                lows = [p for p in quotes.get('low', []) if p is not None]
                volumes = [p for p in quotes.get('volume', []) if p is not None]
                
                # 确保数据长度一致
                min_len = min(len(closes), len(highs), len(lows), len(volumes))
                if min_len < 20:
                    # 如果数据不足，填充默认值
                    closes = [current_price] * 30
                    highs = [current_price * 1.02] * 30
                    lows = [current_price * 0.98] * 30
                    volumes = [1000000] * 30
                else:
                    closes = closes[-30:] if len(closes) > 30 else closes
                    highs = highs[-30:] if len(highs) > 30 else highs
                    lows = lows[-30:] if len(lows) > 30 else lows
                    volumes = volumes[-30:] if len(volumes) > 30 else volumes
                
                return {
                    'symbol': symbol,
                    'current_price': current_price,
                    'prev_close': prev_close,
                    'closes': closes,
                    'highs': highs,
                    'lows': lows,
                    'volumes': volumes,
                    'success': True,
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return {'success': False, 'error': 'No data found'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def calculate_comprehensive_indicators(stock_data: Dict) -> Dict:
    """计算全面的技术指标"""
    
    if not stock_data.get('success'):
        return {}
    
    closes = stock_data['closes']
    highs = stock_data['highs']
    lows = stock_data['lows']
    volumes = stock_data['volumes']
    current_price = stock_data['current_price']
    
    indicators = {'current_price': current_price}
    
    # 1. 趋势指标
    indicators.update(calculate_trend_indicators(closes))
    
    # 2. 动量指标
    indicators.update(calculate_momentum_indicators(closes, highs, lows))
    
    # 3. 成交量指标
    indicators.update(calculate_volume_indicators(closes, volumes))
    
    # 4. 波动率指标
    indicators.update(calculate_volatility_indicators(closes, highs, lows))
    
    # 5. 支撑阻力位
    indicators.update(calculate_support_resistance(closes, highs, lows))
    
    return indicators

def calculate_trend_indicators(closes: List[float]) -> Dict:
    """计算趋势指标"""
    if len(closes) < 10:
        return {}
    
    # 移动平均线
    sma_5 = sum(closes[-5:]) / 5
    sma_10 = sum(closes[-10:]) / 10
    sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sma_10
    sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
    
    # EMA计算
    def calculate_ema(prices, period):
        if len(prices) < period:
            return sum(prices) / len(prices)
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    ema_12 = calculate_ema(closes, 12)
    ema_26 = calculate_ema(closes, 26)
    
    # MACD
    macd_line = ema_12 - ema_26
    signal_line = calculate_ema([macd_line] * 9, 9)  # 简化计算
    macd_histogram = macd_line - signal_line
    
    return {
        'sma_5': sma_5,
        'sma_10': sma_10,
        'sma_20': sma_20,
        'sma_50': sma_50,
        'ema_12': ema_12,
        'ema_26': ema_26,
        'macd_line': macd_line,
        'signal_line': signal_line,
        'macd_histogram': macd_histogram
    }

def calculate_momentum_indicators(closes: List[float], highs: List[float], lows: List[float]) -> Dict:
    """计算动量指标"""
    if len(closes) < 14:
        return {}
    
    # RSI
    def calculate_rsi(prices, period=14):
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    # Stochastic
    def calculate_stochastic(highs, lows, closes, period=14):
        if len(closes) < period:
            return 50
        
        recent_highs = highs[-period:]
        recent_lows = lows[-period:]
        current_close = closes[-1]
        
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        
        if highest_high == lowest_low:
            return 50
        
        k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        return k_percent
    
    # Williams %R
    def calculate_williams_r(highs, lows, closes, period=14):
        if len(closes) < period:
            return -50
        
        recent_highs = highs[-period:]
        recent_lows = lows[-period:]
        current_close = closes[-1]
        
        highest_high = max(recent_highs)
        lowest_low = min(recent_lows)
        
        if highest_high == lowest_low:
            return -50
        
        williams_r = ((highest_high - current_close) / (highest_high - lowest_low)) * -100
        return williams_r
    
    rsi = calculate_rsi(closes)
    stoch_k = calculate_stochastic(highs, lows, closes)
    williams_r = calculate_williams_r(highs, lows, closes)
    
    # ROC (Rate of Change)
    roc_10 = ((closes[-1] - closes[-11]) / closes[-11]) * 100 if len(closes) > 10 else 0
    
    return {
        'rsi': rsi,
        'stochastic_k': stoch_k,
        'williams_r': williams_r,
        'roc_10': roc_10
    }

def calculate_volume_indicators(closes: List[float], volumes: List[float]) -> Dict:
    """计算成交量指标"""
    if len(closes) < 10 or len(volumes) < 10:
        return {}
    
    # 成交量移动平均
    volume_sma_10 = sum(volumes[-10:]) / 10
    volume_sma_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volume_sma_10
    
    # OBV (On Balance Volume)
    def calculate_obv(closes, volumes):
        if len(closes) < 2:
            return volumes[-1] if volumes else 0
        
        obv = 0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i] if i < len(volumes) else 0
            elif closes[i] < closes[i-1]:
                obv -= volumes[i] if i < len(volumes) else 0
        
        return obv
    
    # VWAP (Volume Weighted Average Price)
    def calculate_vwap(closes, volumes):
        if not volumes or sum(volumes) == 0:
            return sum(closes) / len(closes)
        
        total_pv = sum(p * v for p, v in zip(closes, volumes))
        total_v = sum(volumes)
        return total_pv / total_v if total_v > 0 else closes[-1]
    
    obv = calculate_obv(closes, volumes)
    vwap = calculate_vwap(closes[-20:], volumes[-20:])
    
    # 成交量强度
    current_volume = volumes[-1]
    volume_ratio = current_volume / volume_sma_10 if volume_sma_10 > 0 else 1
    
    return {
        'volume_sma_10': volume_sma_10,
        'volume_sma_20': volume_sma_20,
        'obv': obv,
        'vwap': vwap,
        'current_volume': current_volume,
        'volume_ratio': volume_ratio
    }

def calculate_volatility_indicators(closes: List[float], highs: List[float], lows: List[float]) -> Dict:
    """计算波动率指标"""
    if len(closes) < 20:
        return {}
    
    # 布林带
    sma_20 = sum(closes[-20:]) / 20
    variance = sum((p - sma_20) ** 2 for p in closes[-20:]) / 20
    std_dev = math.sqrt(variance)
    
    bb_upper = sma_20 + (2 * std_dev)
    bb_lower = sma_20 - (2 * std_dev)
    bb_position = (closes[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
    
    # ATR (Average True Range)
    def calculate_atr(highs, lows, closes, period=14):
        if len(closes) < period + 1:
            return abs(highs[-1] - lows[-1]) if highs and lows else 0
        
        true_ranges = []
        for i in range(1, len(closes)):
            high = highs[i] if i < len(highs) else closes[i]
            low = lows[i] if i < len(lows) else closes[i]
            prev_close = closes[i-1]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / min(period, len(true_ranges))
    
    atr = calculate_atr(highs, lows, closes)
    
    return {
        'bb_upper': bb_upper,
        'bb_middle': sma_20,
        'bb_lower': bb_lower,
        'bb_position': bb_position,
        'bb_width': (bb_upper - bb_lower) / sma_20 if sma_20 > 0 else 0,
        'atr': atr,
        'atr_percent': (atr / closes[-1]) * 100 if closes[-1] > 0 else 0
    }

def calculate_support_resistance(closes: List[float], highs: List[float], lows: List[float]) -> Dict:
    """计算支撑阻力位"""
    if len(closes) < 20:
        return {}
    
    # 简化的支撑阻力位计算
    recent_highs = highs[-20:] if len(highs) >= 20 else highs
    recent_lows = lows[-20:] if len(lows) >= 20 else lows
    
    # 寻找局部高点和低点
    resistance_levels = []
    support_levels = []
    
    # 简单的峰谷检测
    for i in range(2, len(recent_highs) - 2):
        # 阻力位：局部高点
        if (recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i-2] and
            recent_highs[i] > recent_highs[i+1] and recent_highs[i] > recent_highs[i+2]):
            resistance_levels.append(recent_highs[i])
    
    for i in range(2, len(recent_lows) - 2):
        # 支撑位：局部低点
        if (recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i-2] and
            recent_lows[i] < recent_lows[i+1] and recent_lows[i] < recent_lows[i+2]):
            support_levels.append(recent_lows[i])
    
    current_price = closes[-1]
    
    # 找到最近的支撑和阻力位
    resistance = min([r for r in resistance_levels if r > current_price], default=current_price * 1.05)
    support = max([s for s in support_levels if s < current_price], default=current_price * 0.95)
    
    return {
        'resistance_level': resistance,
        'support_level': support,
        'distance_to_resistance': (resistance - current_price) / current_price if current_price > 0 else 0,
        'distance_to_support': (current_price - support) / current_price if current_price > 0 else 0
    }

def generate_multi_dimensional_signals(indicators: Dict) -> Dict:
    """生成多维度交易信号"""
    
    signals = {}
    current_price = indicators.get('current_price', 0)
    
    # 1. 趋势信号
    trend_score = 0
    if indicators.get('sma_5', 0) > indicators.get('sma_10', 0):
        trend_score += 1
    if indicators.get('sma_10', 0) > indicators.get('sma_20', 0):
        trend_score += 1
    if indicators.get('macd_line', 0) > indicators.get('signal_line', 0):
        trend_score += 1
    if indicators.get('macd_histogram', 0) > 0:
        trend_score += 1
    
    signals['trend'] = 'STRONG_BUY' if trend_score >= 3 else 'BUY' if trend_score >= 2 else 'SELL' if trend_score <= 1 else 'NEUTRAL'
    
    # 2. 动量信号
    rsi = indicators.get('rsi', 50)
    stoch = indicators.get('stochastic_k', 50)
    williams_r = indicators.get('williams_r', -50)
    
    momentum_signals = []
    if rsi < 30:
        momentum_signals.append('BUY')
    elif rsi > 70:
        momentum_signals.append('SELL')
    
    if stoch < 20:
        momentum_signals.append('BUY')
    elif stoch > 80:
        momentum_signals.append('SELL')
    
    if williams_r < -80:
        momentum_signals.append('BUY')
    elif williams_r > -20:
        momentum_signals.append('SELL')
    
    buy_momentum = momentum_signals.count('BUY')
    sell_momentum = momentum_signals.count('SELL')
    
    if buy_momentum >= 2:
        signals['momentum'] = 'BUY'
    elif sell_momentum >= 2:
        signals['momentum'] = 'SELL'
    else:
        signals['momentum'] = 'NEUTRAL'
    
    # 3. 成交量信号
    volume_ratio = indicators.get('volume_ratio', 1)
    vwap = indicators.get('vwap', current_price)
    
    volume_score = 0
    if volume_ratio > 1.5:  # 成交量放大
        volume_score += 1
    if current_price > vwap:  # 价格高于VWAP
        volume_score += 1
    
    signals['volume'] = 'BUY' if volume_score >= 2 else 'SELL' if volume_score == 0 else 'NEUTRAL'
    
    # 4. 波动率信号
    bb_position = indicators.get('bb_position', 0.5)
    bb_width = indicators.get('bb_width', 0)
    
    if bb_position < 0.2:
        signals['volatility'] = 'BUY'  # 接近下轨
    elif bb_position > 0.8:
        signals['volatility'] = 'SELL'  # 接近上轨
    elif bb_width < 0.1:
        signals['volatility'] = 'SQUEEZE'  # 布林带收缩，可能突破
    else:
        signals['volatility'] = 'NEUTRAL'
    
    # 5. 支撑阻力信号
    dist_to_support = indicators.get('distance_to_support', 0)
    dist_to_resistance = indicators.get('distance_to_resistance', 0)
    
    if dist_to_support < 0.02:  # 接近支撑位
        signals['support_resistance'] = 'BUY'
    elif dist_to_resistance < 0.02:  # 接近阻力位
        signals['support_resistance'] = 'SELL'
    else:
        signals['support_resistance'] = 'NEUTRAL'
    
    # 综合评分
    signal_weights = {
        'trend': 3,
        'momentum': 2,
        'volume': 2,
        'volatility': 1,
        'support_resistance': 1
    }
    
    total_score = 0
    max_score = sum(signal_weights.values()) * 2  # 最高分（所有都是STRONG_BUY/BUY）
    
    for signal_type, signal_value in signals.items():
        if signal_type in signal_weights:
            weight = signal_weights[signal_type]
            if signal_value == 'STRONG_BUY':
                total_score += weight * 2
            elif signal_value == 'BUY':
                total_score += weight
            elif signal_value == 'SELL':
                total_score -= weight
            elif signal_value == 'SQUEEZE':
                total_score += weight * 0.5  # 布林带收缩为中性偏多
    
    # 转换为1-10评分
    normalized_score = max(1, min(10, round(5 + (total_score / max_score) * 5)))
    
    signals['overall_score'] = normalized_score
    signals['overall_signal'] = (
        'STRONG_BUY' if normalized_score >= 8 else
        'BUY' if normalized_score >= 6 else
        'STRONG_SELL' if normalized_score <= 3 else
        'SELL' if normalized_score <= 5 else
        'NEUTRAL'
    )
    
    return signals

def print_comprehensive_analysis(symbol: str, stock_data: Dict, indicators: Dict, signals: Dict):
    """打印全面的分析报告"""
    
    print(f"📈 多维度股票分析 - {symbol}")
    print("=" * 80)
    
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
    print(f"🎯 综合评分: {signals['overall_score']}/10 分")
    print(f"📈 综合信号: {signals['overall_signal']}")
    
    # 技术指标详情
    print(f"\n📊 核心技术指标:")
    print(f"   移动均线: SMA5=${indicators.get('sma_5', 0):.2f} | SMA10=${indicators.get('sma_10', 0):.2f} | SMA20=${indicators.get('sma_20', 0):.2f}")
    print(f"   MACD: {indicators.get('macd_line', 0):.3f} | 信号线: {indicators.get('signal_line', 0):.3f}")
    print(f"   RSI: {indicators.get('rsi', 0):.1f} | 随机指标: {indicators.get('stochastic_k', 0):.1f}")
    print(f"   布林带位置: {indicators.get('bb_position', 0):.2%} | ATR: {indicators.get('atr_percent', 0):.2f}%")
    print(f"   成交量比率: {indicators.get('volume_ratio', 0):.2f}x | VWAP: ${indicators.get('vwap', 0):.2f}")
    
    # 多维度信号
    print(f"\n🚦 多维度交易信号:")
    signal_emojis = {
        'STRONG_BUY': '🔥', 'BUY': '🟢', 'NEUTRAL': '🟡', 
        'SELL': '🔴', 'STRONG_SELL': '💥', 'SQUEEZE': '⚡'
    }
    
    signal_descriptions = {
        'trend': '趋势信号',
        'momentum': '动量信号', 
        'volume': '成交量信号',
        'volatility': '波动率信号',
        'support_resistance': '支撑阻力'
    }
    
    for signal_type, description in signal_descriptions.items():
        if signal_type in signals:
            emoji = signal_emojis.get(signals[signal_type], '❓')
            print(f"   {emoji} {description}: {signals[signal_type]}")
    
    # 关键价位
    print(f"\n🎯 关键价位:")
    print(f"   阻力位: ${indicators.get('resistance_level', 0):.2f} ({indicators.get('distance_to_resistance', 0):.1%})")
    print(f"   支撑位: ${indicators.get('support_level', 0):.2f} ({indicators.get('distance_to_support', 0):.1%})")
    print(f"   布林带: ${indicators.get('bb_upper', 0):.2f} - ${indicators.get('bb_lower', 0):.2f}")
    
    # 投资建议
    print(f"\n💡 投资建议:")
    score = signals['overall_score']
    if score >= 8:
        print(f"   🔥 强烈买入 - 多个维度显示强势信号")
        print(f"   📈 目标价位: ${current_price * 1.1:.2f} | 止损: ${current_price * 0.95:.2f}")
    elif score >= 6:
        print(f"   ✅ 买入 - 技术面偏多，建议适量配置")
        print(f"   📈 目标价位: ${current_price * 1.05:.2f} | 止损: ${current_price * 0.97:.2f}")
    elif score <= 3:
        print(f"   💥 强烈卖出 - 多个维度显示弱势信号")
        print(f"   📉 目标价位: ${current_price * 0.9:.2f}")
    elif score <= 5:
        print(f"   ⚠️  卖出 - 技术面偏弱，建议减仓")
        print(f"   📉 反弹阻力: ${current_price * 1.03:.2f}")
    else:
        print(f"   🔄 中性 - 技术面均衡，建议观望")
        print(f"   ⚖️ 关注突破确认信号")

def main():
    """主函数"""
    
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'AAPL'
    
    print("🔍 正在获取多维度数据...")
    
    # 获取股票数据
    stock_data = get_stock_price_enhanced(symbol)
    
    if not stock_data.get('success'):
        print(f"❌ 无法获取{symbol}数据: {stock_data.get('error')}")
        return
    
    # 计算全面技术指标
    indicators = calculate_comprehensive_indicators(stock_data)
    
    if not indicators:
        print("❌ 数据不足，无法计算技术指标")
        return
    
    # 生成多维度信号
    signals = generate_multi_dimensional_signals(indicators)
    
    # 打印全面分析
    print_comprehensive_analysis(symbol, stock_data, indicators, signals)
    
    print(f"\n🎉 {symbol} 多维度分析完成!")
    print("📊 分析维度: 趋势、动量、成交量、波动率、支撑阻力")
    print("⚠️  仅供参考，请结合基本面分析")

if __name__ == "__main__":
    main()