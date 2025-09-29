"""
Stock Analysis Tool - 股票分析工具

使用多种技术指标和策略来分析单只股票的买入信号和投资价值。
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import backtrader as bt
    from src.strategies.sma_crossover import SMACrossoverStrategy
    from src.strategies.rsi_strategy import RSIStrategy
    from src.strategies.bollinger_bands import BollingerBandsStrategy
    from src.strategies.mean_reversion import MeanReversionStrategy
    from src.data.yahoo_feed import YahooDataFeed
    from src.brokers.paper_broker import PaperBroker
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required dependencies with: pip install -r requirements.txt")
    sys.exit(1)


class StockAnalyzer:
    """股票分析器 - 综合多种指标分析股票买入价值"""
    
    def __init__(self, symbol: str):
        """
        初始化股票分析器
        
        Args:
            symbol: 股票代码 (如: 'AAPL', 'TSLA', 'MSFT')
        """
        self.symbol = symbol.upper()
        self.current_signals = {}
        self.historical_performance = {}
        
    def analyze_current_signals(self, period: str = '6mo') -> dict:
        """
        分析当前的买入卖出信号
        
        Args:
            period: 分析周期 ('1mo', '3mo', '6mo', '1y', '2y')
            
        Returns:
            包含各种信号的字典
        """
        print(f"🔍 分析 {self.symbol} 的当前信号...")
        print(f"📊 数据周期: {period}")
        print("-" * 60)
        
        # 获取数据
        try:
            data_feed = YahooDataFeed.create_data_feed(
                symbol=self.symbol,
                period=period,
                interval='1d'
            )
            
            # 获取最新价格信息
            ticker_info = YahooDataFeed.get_ticker_info(self.symbol)
            print(f"📈 股票信息:")
            print(f"   名称: {ticker_info.get('name', 'N/A')}")
            print(f"   行业: {ticker_info.get('sector', 'N/A')} - {ticker_info.get('industry', 'N/A')}")
            print(f"   当前价格: ${ticker_info.get('price', 'N/A')}")
            print(f"   市值: {ticker_info.get('market_cap', 'N/A')}")
            print()
            
        except Exception as e:
            print(f"❌ 获取数据失败: {e}")
            return {}
        
        signals = {}
        
        # 1. SMA交叉信号分析
        signals['sma_crossover'] = self._analyze_sma_signals(data_feed)
        
        # 2. RSI信号分析  
        signals['rsi'] = self._analyze_rsi_signals(data_feed)
        
        # 3. 布林带信号分析
        signals['bollinger'] = self._analyze_bollinger_signals(data_feed)
        
        # 4. 综合评分
        signals['overall_score'] = self._calculate_overall_score(signals)
        
        self._print_signal_summary(signals)
        return signals
    
    def _analyze_sma_signals(self, data_feed) -> dict:
        """分析SMA交叉信号"""
        cerebro = bt.Cerebro()
        cerebro.adddata(data_feed)
        cerebro.addstrategy(SMACrossoverStrategy, fast_period=10, slow_period=30)
        
        # 运行策略获取最新信号
        results = cerebro.run()
        strategy = results[0]
        
        # 获取最后的指标值
        fast_sma = strategy.fast_sma[0]
        slow_sma = strategy.slow_sma[0]
        current_price = strategy.data.close[0]
        crossover = strategy.crossover[0]
        
        # 判断信号强度
        if crossover > 0:
            signal = "强烈买入"
            strength = "🟢 强烈"
        elif crossover < 0:
            signal = "卖出"
            strength = "🔴 强烈"
        elif fast_sma > slow_sma:
            signal = "持有/轻微买入"
            strength = "🟡 中等"
        else:
            signal = "观望"
            strength = "⚪ 弱"
        
        return {
            'signal': signal,
            'strength': strength,
            'fast_sma': round(fast_sma, 2),
            'slow_sma': round(slow_sma, 2),
            'current_price': round(current_price, 2),
            'crossover': round(crossover, 2)
        }
    
    def _analyze_rsi_signals(self, data_feed) -> dict:
        """分析RSI信号"""
        cerebro = bt.Cerebro()
        cerebro.adddata(data_feed)
        cerebro.addstrategy(RSIStrategy, rsi_period=14, rsi_overbought=70, rsi_oversold=30)
        
        results = cerebro.run()
        strategy = results[0]
        
        rsi_value = strategy.rsi[0]
        
        # RSI信号判断
        if rsi_value < 30:
            signal = "超卖 - 买入机会"
            strength = "🟢 强烈"
        elif rsi_value < 40:
            signal = "轻微超卖 - 考虑买入"  
            strength = "🟡 中等"
        elif rsi_value > 70:
            signal = "超买 - 避免买入"
            strength = "🔴 强烈"
        elif rsi_value > 60:
            signal = "轻微超买 - 谨慎"
            strength = "🟡 中等"
        else:
            signal = "中性"
            strength = "⚪ 弱"
        
        return {
            'signal': signal,
            'strength': strength,
            'rsi_value': round(rsi_value, 2)
        }
    
    def _analyze_bollinger_signals(self, data_feed) -> dict:
        """分析布林带信号"""
        cerebro = bt.Cerebro()
        cerebro.adddata(data_feed)
        cerebro.addstrategy(BollingerBandsStrategy, bb_period=20, bb_devfactor=2)
        
        results = cerebro.run()
        strategy = results[0]
        
        current_price = strategy.data.close[0]
        bb_top = strategy.bb_top[0]
        bb_mid = strategy.bb_mid[0] 
        bb_bot = strategy.bb_bot[0]
        
        # 布林带信号判断
        if current_price <= bb_bot:
            signal = "触及下轨 - 买入机会"
            strength = "🟢 强烈"
        elif current_price >= bb_top:
            signal = "触及上轨 - 避免买入"
            strength = "🔴 强烈"
        elif current_price < bb_mid:
            signal = "低于中线 - 考虑买入"
            strength = "🟡 中等"
        else:
            signal = "高于中线 - 谨慎"
            strength = "🟡 中等"
        
        return {
            'signal': signal,
            'strength': strength,
            'current_price': round(current_price, 2),
            'bb_top': round(bb_top, 2),
            'bb_mid': round(bb_mid, 2),  
            'bb_bot': round(bb_bot, 2),
            'position_in_band': round((current_price - bb_bot) / (bb_top - bb_bot) * 100, 1)
        }
    
    def _calculate_overall_score(self, signals: dict) -> dict:
        """计算综合评分"""
        score = 0
        max_score = 0
        
        # SMA信号评分
        sma_signal = signals['sma_crossover']['signal']
        if "强烈买入" in sma_signal:
            score += 3
        elif "买入" in sma_signal or "持有" in sma_signal:
            score += 1
        elif "卖出" in sma_signal:
            score -= 2
        max_score += 3
        
        # RSI信号评分
        rsi_signal = signals['rsi']['signal']
        if "超卖" in rsi_signal and "买入" in rsi_signal:
            score += 3
        elif "考虑买入" in rsi_signal:
            score += 1
        elif "超买" in rsi_signal:
            score -= 2
        max_score += 3
        
        # 布林带信号评分
        bb_signal = signals['bollinger']['signal']
        if "买入机会" in bb_signal:
            score += 3
        elif "考虑买入" in bb_signal:
            score += 1
        elif "避免买入" in bb_signal:
            score -= 2
        max_score += 3
        
        # 计算百分比评分
        percentage_score = (score / max_score) * 100 if max_score > 0 else 0
        
        # 评级判断
        if percentage_score >= 80:
            rating = "🟢 强烈推荐买入"
        elif percentage_score >= 60:
            rating = "🟡 推荐买入"
        elif percentage_score >= 40:
            rating = "⚪ 中性观望"
        elif percentage_score >= 20:
            rating = "🟠 不建议买入"
        else:
            rating = "🔴 强烈不推荐"
        
        return {
            'score': score,
            'max_score': max_score,
            'percentage': round(percentage_score, 1),
            'rating': rating
        }
    
    def _print_signal_summary(self, signals: dict):
        """打印信号摘要"""
        print("📊 技术指标分析结果:")
        print("-" * 60)
        
        print(f"1️⃣  SMA交叉策略:")
        sma = signals['sma_crossover']
        print(f"   信号: {sma['signal']} {sma['strength']}")
        print(f"   快线SMA(10): {sma['fast_sma']} | 慢线SMA(30): {sma['slow_sma']}")
        print(f"   当前价格: {sma['current_price']}")
        print()
        
        print(f"2️⃣  RSI指标:")
        rsi = signals['rsi']
        print(f"   信号: {rsi['signal']} {rsi['strength']}")
        print(f"   RSI值: {rsi['rsi_value']} (< 30超卖, > 70超买)")
        print()
        
        print(f"3️⃣  布林带策略:")
        bb = signals['bollinger']
        print(f"   信号: {bb['signal']} {bb['strength']}")
        print(f"   当前价格: {bb['current_price']}")
        print(f"   布林带: 上轨{bb['bb_top']} | 中线{bb['bb_mid']} | 下轨{bb['bb_bot']}")
        print(f"   位置: {bb['position_in_band']}% (0%=下轨, 100%=上轨)")
        print()
        
        print("🎯 综合评估:")
        overall = signals['overall_score']
        print(f"   评分: {overall['score']}/{overall['max_score']} ({overall['percentage']}%)")
        print(f"   建议: {overall['rating']}")
        print("-" * 60)
    
    def backtest_performance(self, period: str = '1y') -> dict:
        """回测历史表现"""
        print(f"📈 回测 {self.symbol} 在过去{period}的策略表现...")
        print("-" * 60)
        
        strategies = [
            ('SMA交叉', SMACrossoverStrategy),
            ('RSI策略', RSIStrategy),
            ('布林带', BollingerBandsStrategy)
        ]
        
        results = {}
        
        for name, strategy_class in strategies:
            try:
                cerebro = bt.Cerebro()
                
                # 添加数据
                data_feed = YahooDataFeed.create_data_feed(
                    symbol=self.symbol,
                    period=period,
                    interval='1d'
                )
                cerebro.adddata(data_feed)
                
                # 添加策略
                cerebro.addstrategy(strategy_class)
                
                # 设置经纪商
                broker = PaperBroker.create_realistic_broker(cash=10000)
                broker.setup_broker(cerebro)
                
                # 添加分析器
                cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
                cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
                
                # 运行回测
                starting_value = cerebro.broker.getvalue()
                strategy_results = cerebro.run()
                final_value = cerebro.broker.getvalue()
                
                # 计算结果
                total_return = ((final_value - starting_value) / starting_value) * 100
                
                trades_analysis = strategy_results[0].analyzers.trades.get_analysis()
                drawdown_analysis = strategy_results[0].analyzers.drawdown.get_analysis()
                
                total_trades = trades_analysis.get('total', {}).get('total', 0)
                won_trades = trades_analysis.get('won', {}).get('total', 0)
                win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
                max_drawdown = drawdown_analysis.get('max', {}).get('drawdown', 0)
                
                results[name] = {
                    'return': round(total_return, 2),
                    'trades': total_trades,
                    'win_rate': round(win_rate, 1),
                    'max_drawdown': round(max_drawdown, 2)
                }
                
                print(f"{name}:")
                print(f"   收益率: {total_return:.2f}%")
                print(f"   交易次数: {total_trades}")
                print(f"   胜率: {win_rate:.1f}%")
                print(f"   最大回撤: {max_drawdown:.2f}%")
                print()
                
            except Exception as e:
                print(f"{name}: 回测失败 - {e}")
                results[name] = None
        
        return results


def analyze_stock(symbol: str, period: str = '6mo'):
    """
    分析单只股票的买入价值
    
    Args:
        symbol: 股票代码
        period: 分析周期
    """
    print(f"🎯 股票分析报告: {symbol.upper()}")
    print("=" * 70)
    
    analyzer = StockAnalyzer(symbol)
    
    # 1. 当前信号分析
    current_signals = analyzer.analyze_current_signals(period)
    
    print("\n")
    
    # 2. 历史回测表现
    historical_performance = analyzer.backtest_performance('1y')
    
    # 3. 综合建议
    print("💡 投资建议:")
    print("-" * 60)
    
    overall_rating = current_signals.get('overall_score', {}).get('rating', '未知')
    print(f"技术面评级: {overall_rating}")
    
    # 基于回测结果给出建议
    if historical_performance:
        avg_return = sum([r['return'] for r in historical_performance.values() if r]) / len([r for r in historical_performance.values() if r])
        avg_win_rate = sum([r['win_rate'] for r in historical_performance.values() if r]) / len([r for r in historical_performance.values() if r])
        
        print(f"策略平均收益: {avg_return:.2f}%")
        print(f"策略平均胜率: {avg_win_rate:.1f}%")
        
        if avg_return > 10 and avg_win_rate > 50:
            print("📈 历史表现优秀，策略有效性较高")
        elif avg_return > 5:
            print("📊 历史表现一般，需要谨慎评估")  
        else:
            print("📉 历史表现较差，建议进一步分析")
    
    print("\n⚠️  风险提示:")
    print("   - 技术分析仅供参考，不构成投资建议")
    print("   - 过往表现不代表未来收益")
    print("   - 请结合基本面分析和市场环境做决策")
    print("=" * 70)


if __name__ == '__main__':
    # 示例分析
    import sys
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        symbol = input("请输入要分析的股票代码 (如 AAPL): ").strip() or 'AAPL'
    
    analyze_stock(symbol)