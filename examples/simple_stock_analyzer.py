#!/usr/bin/env python3
"""
简化版股票分析工具 - 避免numpy版本冲突
基于基础计算提供技术分析和投资建议
"""

import sys
import datetime
from typing import Dict, Tuple, List

print(f"📈 股票分析工具 - {sys.argv[1] if len(sys.argv) > 1 else 'AAPL'}")
print("=" * 60)

def simple_moving_average(prices: List[float], period: int) -> float:
    """计算简单移动平均"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    return sum(prices[-period:]) / period

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """计算RSI指标"""
    if len(prices) < period + 1:
        return 50  # 默认中性值
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-change)
    
    # 计算平均收益和损失
    if len(gains) < period:
        return 50
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_stock_simple(symbol: str) -> Dict:
    """简化版股票分析"""
    
    # 模拟历史价格数据（在实际应用中会从yfinance获取）
    mock_data = {
        'AAPL': [150, 152, 148, 151, 155, 153, 157, 154, 158, 156, 160, 159, 162, 158, 161, 165, 163, 167, 164, 168],
        'NVDA': [420, 425, 418, 428, 435, 432, 440, 438, 445, 443, 450, 448, 455, 452, 460, 458, 465, 462, 468, 470],
        'TSLA': [240, 245, 238, 248, 252, 250, 255, 253, 258, 256, 260, 258, 263, 260, 265, 268, 266, 270, 268, 272],
        'MSFT': [340, 342, 338, 345, 348, 346, 350, 352, 348, 355, 358, 356, 360, 358, 365, 363, 368, 366, 370, 372],
        'MSTR': [180, 195, 185, 210, 225, 220, 245, 240, 265, 250, 280, 275, 295, 285, 310, 305, 325, 315, 340, 335]
    }
    
    prices = mock_data.get(symbol, mock_data['AAPL'])
    current_price = prices[-1]
    
    # 技术指标计算
    sma_10 = simple_moving_average(prices, 10)
    sma_20 = simple_moving_average(prices, 20)
    rsi = calculate_rsi(prices, 14)
    
    # 布林带简化计算
    bb_middle = sma_20
    # 简化的标准差计算
    squared_diffs = [(p - bb_middle) ** 2 for p in prices[-20:]]
    variance = sum(squared_diffs) / len(squared_diffs)
    std_dev = variance ** 0.5
    bb_upper = bb_middle + (2 * std_dev)
    bb_lower = bb_middle - (2 * std_dev)
    
    # 价格趋势
    price_change_1d = prices[-1] - prices[-2] if len(prices) > 1 else 0
    price_change_5d = prices[-1] - prices[-6] if len(prices) > 5 else 0
    price_change_10d = prices[-1] - prices[-11] if len(prices) > 10 else 0
    
    return {
        'symbol': symbol,
        'current_price': current_price,
        'sma_10': sma_10,
        'sma_20': sma_20,
        'rsi': rsi,
        'bb_upper': bb_upper,
        'bb_middle': bb_middle,
        'bb_lower': bb_lower,
        'price_change_1d': price_change_1d,
        'price_change_5d': price_change_5d,
        'price_change_10d': price_change_10d,
        'prices': prices
    }

def generate_signals(analysis: Dict) -> Dict:
    """生成交易信号"""
    
    signals = {
        'sma_signal': 'NEUTRAL',
        'rsi_signal': 'NEUTRAL', 
        'bb_signal': 'NEUTRAL',
        'trend_signal': 'NEUTRAL'
    }
    
    current_price = analysis['current_price']
    sma_10 = analysis['sma_10']
    sma_20 = analysis['sma_20']
    rsi = analysis['rsi']
    bb_upper = analysis['bb_upper']
    bb_lower = analysis['bb_lower']
    
    # SMA信号
    if sma_10 > sma_20 * 1.02:  # 10日线明显高于20日线
        signals['sma_signal'] = 'BUY'
    elif sma_10 < sma_20 * 0.98:  # 10日线明显低于20日线
        signals['sma_signal'] = 'SELL'
    
    # RSI信号
    if rsi < 30:
        signals['rsi_signal'] = 'BUY'  # 超卖
    elif rsi > 70:
        signals['rsi_signal'] = 'SELL'  # 超买
    
    # 布林带信号
    if current_price < bb_lower:
        signals['bb_signal'] = 'BUY'  # 价格接近下轨
    elif current_price > bb_upper:
        signals['bb_signal'] = 'SELL'  # 价格接近上轨
    
    # 趋势信号
    if analysis['price_change_5d'] > 0 and analysis['price_change_10d'] > 0:
        signals['trend_signal'] = 'BUY'  # 上升趋势
    elif analysis['price_change_5d'] < 0 and analysis['price_change_10d'] < 0:
        signals['trend_signal'] = 'SELL'  # 下降趋势
    
    return signals

def calculate_score_and_recommendation(analysis: Dict, signals: Dict) -> Tuple[int, str]:
    """计算综合评分和投资建议"""
    
    score = 5  # 基础中性分
    buy_signals = 0
    sell_signals = 0
    
    for signal in signals.values():
        if signal == 'BUY':
            buy_signals += 1
            score += 1
        elif signal == 'SELL':
            sell_signals += 1
            score -= 1
    
    # 确保分数在1-9范围内
    score = max(1, min(9, score))
    
    # 生成投资建议
    if buy_signals >= 3:
        recommendation = "强烈买入"
    elif buy_signals >= 2:
        recommendation = "买入"
    elif buy_signals > sell_signals:
        recommendation = "弱势买入"
    elif sell_signals >= 3:
        recommendation = "强烈卖出"
    elif sell_signals >= 2:
        recommendation = "卖出"
    elif sell_signals > buy_signals:
        recommendation = "弱势卖出"
    else:
        recommendation = "持有"
    
    return score, recommendation

def print_analysis_report(analysis: Dict, signals: Dict, score: int, recommendation: str):
    """打印分析报告"""
    
    symbol = analysis['symbol']
    current_price = analysis['current_price']
    
    print(f"🏷️  股票代码: {symbol}")
    print(f"💰 当前价格: ${current_price:.2f}")
    print(f"📅 分析时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    print(f"\n📊 技术指标:")
    print(f"   10日均线: ${analysis['sma_10']:.2f}")
    print(f"   20日均线: ${analysis['sma_20']:.2f}")
    print(f"   RSI(14): {analysis['rsi']:.1f}")
    print(f"   布林带上轨: ${analysis['bb_upper']:.2f}")
    print(f"   布林带中轨: ${analysis['bb_middle']:.2f}")
    print(f"   布林带下轨: ${analysis['bb_lower']:.2f}")
    
    print(f"\n📈 价格变化:")
    print(f"   1日变化: ${analysis['price_change_1d']:+.2f}")
    print(f"   5日变化: ${analysis['price_change_5d']:+.2f}")
    print(f"   10日变化: ${analysis['price_change_10d']:+.2f}")
    
    print(f"\n🚦 交易信号:")
    signal_emojis = {'BUY': '🟢', 'SELL': '🔴', 'NEUTRAL': '🟡'}
    for signal_name, signal_value in signals.items():
        emoji = signal_emojis[signal_value]
        signal_chinese = signal_name.replace('_signal', '').upper()
        print(f"   {emoji} {signal_chinese}: {signal_value}")
    
    print(f"\n🎯 综合评估:")
    print(f"   评分: {score}/9 分")
    print(f"   投资建议: {recommendation}")
    
    # 风险提示
    print(f"\n⚠️  风险提示:")
    risk_level = "低" if 3 <= score <= 7 else "中" if 2 <= score <= 8 else "高"
    print(f"   风险等级: {risk_level}")
    print(f"   建议仓位: {'20-30%' if score >= 7 else '10-20%' if score >= 5 else '5-10%'}")
    
    print(f"\n💡 策略建议:")
    if score >= 7:
        print(f"   ✅ 多个指标显示买入信号，建议积极配置")
        print(f"   📈 设置止损位: ${current_price * 0.95:.2f} (-5%)")
    elif score >= 5:
        print(f"   🔄 指标混合，建议谨慎观察或小仓位试探")
        print(f"   ⚖️ 密切关注突破信号")
    else:
        print(f"   ⛔ 多个指标显示卖出信号，建议减仓或观望")
        print(f"   📉 反弹止损位: ${current_price * 1.05:.2f} (+5%)")

def test_strategy_performance(symbol: str, analysis: Dict):
    """测试策略历史表现（模拟）"""
    
    print(f"\n📊 {symbol} 策略回测表现 (模拟数据):")
    print("-" * 40)
    
    # 模拟回测数据
    backtest_data = {
        'AAPL': {'return': 7.30, 'trades': 3, 'win_rate': 66.7, 'max_drawdown': 0.84},
        'NVDA': {'return': 8.84, 'trades': 5, 'win_rate': 80.0, 'max_drawdown': 3.27},
        'TSLA': {'return': 3.23, 'trades': 1, 'win_rate': 100, 'max_drawdown': 6.77},
        'MSFT': {'return': 5.45, 'trades': 4, 'win_rate': 75.0, 'max_drawdown': 2.15},
        'MSTR': {'return': 85.6, 'trades': 6, 'win_rate': 83.3, 'max_drawdown': 15.2}
    }
    
    perf = backtest_data.get(symbol, {'return': 6.0, 'trades': 3, 'win_rate': 70.0, 'max_drawdown': 4.0})
    
    print(f"   总收益率: {perf['return']:+.2f}%")
    print(f"   交易次数: {perf['trades']}")
    print(f"   胜率: {perf['win_rate']:.1f}%")
    print(f"   最大回撤: {perf['max_drawdown']:.2f}%")
    
    # 性能评级
    if perf['return'] > 8:
        performance_grade = "优秀 ⭐⭐⭐"
    elif perf['return'] > 5:
        performance_grade = "良好 ⭐⭐"
    elif perf['return'] > 2:
        performance_grade = "一般 ⭐"
    else:
        performance_grade = "较差"
    
    print(f"   策略评级: {performance_grade}")

def main():
    """主函数"""
    
    # 获取股票代码
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'AAPL'
    
    try:
        # 分析股票
        analysis = analyze_stock_simple(symbol)
        
        # 生成信号
        signals = generate_signals(analysis)
        
        # 计算评分和建议
        score, recommendation = calculate_score_and_recommendation(analysis, signals)
        
        # 打印报告
        print_analysis_report(analysis, signals, score, recommendation)
        
        # 测试策略表现
        test_strategy_performance(symbol, analysis)
        
        print(f"\n🎉 {symbol} 分析完成!")
        print(f"💻 提示: 这是基于简化算法的演示版本")
        print(f"🔗 Web监控界面: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {e}")
        print("💡 支持的股票代码: AAPL, NVDA, TSLA, MSFT, MSTR")

if __name__ == "__main__":
    main()