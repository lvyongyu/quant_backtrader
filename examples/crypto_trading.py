#!/usr/bin/env python3
"""
加密货币交易系统
Cryptocurrency Trading System

支持Binance数据源的加密货币交易策略
"""

import backtrader as bt
import requests
import json
import datetime
from typing import Dict, List, Optional
import time

class SimpleBinanceAPI:
    """简化的Binance API客户端"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BacktraderBot/1.0)'
        })
    
    def get_klines(self, symbol: str, interval: str = '1d', limit: int = 100) -> List[List]:
        """获取K线数据"""
        url = f"{self.BASE_URL}/klines"
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API请求失败: {e}")
            return []
    
    def get_24hr_ticker(self, symbol: str) -> Dict:
        """获取24小时价格变动统计"""
        url = f"{self.BASE_URL}/ticker/24hr"
        params = {'symbol': symbol.upper()}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ 获取行情失败: {e}")
            return {}
    
    def get_top_volume_pairs(self, quote_asset: str = 'USDT', limit: int = 10) -> List[Dict]:
        """获取交易量最大的交易对"""
        url = f"{self.BASE_URL}/ticker/24hr"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            tickers = response.json()
            
            # 筛选指定计价货币的交易对
            filtered = [
                ticker for ticker in tickers 
                if ticker['symbol'].endswith(quote_asset.upper()) and float(ticker['quoteVolume']) > 0
            ]
            
            # 按交易量排序
            filtered.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            
            return filtered[:limit]
            
        except Exception as e:
            print(f"❌ 获取热门交易对失败: {e}")
            return []

class CryptoDataFeed(bt.feeds.GenericCSVData):
    """加密货币数据源"""
    
    params = (
        ('symbol', 'BTCUSDT'),
        ('interval', '1d'),
        ('limit', 100),
    )
    
    def __init__(self):
        self.api = SimpleBinanceAPI()
        
        # 创建临时CSV文件
        import tempfile
        import csv
        import os
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        
        try:
            print(f"📊 获取 {self.p.symbol} 数据...")
            
            # 获取K线数据
            klines = self.api.get_klines(self.p.symbol, self.p.interval, self.p.limit)
            
            if not klines:
                raise ValueError("No data received from Binance")
            
            # 写入CSV
            writer = csv.writer(self.temp_file)
            writer.writerow(['date', 'open', 'high', 'low', 'close', 'volume'])
            
            for kline in klines:
                timestamp = datetime.datetime.fromtimestamp(kline[0] / 1000)
                date_str = timestamp.strftime('%Y-%m-%d')
                
                writer.writerow([
                    date_str,
                    float(kline[1]),  # open
                    float(kline[2]),  # high
                    float(kline[3]),  # low
                    float(kline[4]),  # close
                    float(kline[5])   # volume
                ])
            
            self.temp_file.close()
            
            print(f"✅ 获取到 {len(klines)} 条 {self.p.symbol} 数据")
            
            # 初始化父类
            super(CryptoDataFeed, self).__init__(
                dataname=self.temp_file.name,
                dtformat='%Y-%m-%d',
                datetime=0,
                open=1, high=2, low=3, close=4, volume=5
            )
            
        except Exception as e:
            print(f"❌ {self.p.symbol} 数据获取失败: {e}")
            self.temp_file.close()
            # 创建空文件
            with open(self.temp_file.name, 'w') as f:
                f.write('date,open,high,low,close,volume\n')
            
            super(CryptoDataFeed, self).__init__(
                dataname=self.temp_file.name,
                dtformat='%Y-%m-%d',
                datetime=0,
                open=1, high=2, low=3, close=4, volume=5
            )
    
    def __del__(self):
        """清理临时文件"""
        try:
            import os
            if hasattr(self, 'temp_file') and self.temp_file:
                os.unlink(self.temp_file.name)
        except:
            pass

class CryptoStrategy(bt.Strategy):
    """加密货币交易策略"""
    
    params = (
        ('sma_fast', 7),
        ('sma_slow', 21),
        ('rsi_period', 14),
        ('position_pct', 0.1),  # 10%仓位
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
    )
    
    def __init__(self):
        # 技术指标
        self.sma_fast = bt.indicators.SMA(period=self.p.sma_fast)
        self.sma_slow = bt.indicators.SMA(period=self.p.sma_slow)
        self.rsi = bt.indicators.RSI(period=self.p.rsi_period)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        self.macd = bt.indicators.MACD()
        
        # 状态变量
        self.order = None
        self.trades = 0
        self.wins = 0
        self.buy_price = None
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt}: {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'买入: ${order.executed.price:.4f}, 数量: {order.executed.size}')
            else:
                self.trades += 1
                if self.buy_price:
                    pnl = order.executed.price - self.buy_price
                    if pnl > 0:
                        self.wins += 1
                    pnl_pct = (pnl / self.buy_price) * 100
                    self.log(f'卖出: ${order.executed.price:.4f}, 盈亏: {pnl_pct:+.2f}%')
                else:
                    self.log(f'卖出: ${order.executed.price:.4f}')
                    
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败: {order.getstatusname()}')
        
        self.order = None
    
    def next(self):
        # 等待足够的历史数据
        if len(self) < self.p.sma_slow:
            return
            
        if self.order:
            return
        
        current_price = self.data.close[0]
        
        if not self.position:
            # 买入条件：金叉 + RSI不超买 + MACD向上
            buy_conditions = [
                self.crossover[0] > 0,  # 金叉
                self.rsi[0] < self.p.rsi_overbought,  # RSI不超买
                self.macd.macd[0] > self.macd.signal[0],  # MACD向上
                current_price > self.sma_slow[0]  # 价格在慢线上方
            ]
            
            if sum(buy_conditions) >= 3:  # 至少满足3个条件
                cash = self.broker.get_cash()
                size = int((cash * self.p.position_pct) / current_price)
                
                if size > 0:
                    self.order = self.buy(size=size)
                    self.log(f'金叉买入信号 RSI={self.rsi[0]:.1f} 条件={sum(buy_conditions)}/4')
        else:
            # 卖出条件：死叉 或 RSI超买 或 价格跌破慢线
            sell_conditions = [
                self.crossover[0] < 0,  # 死叉
                self.rsi[0] > self.p.rsi_overbought + 10,  # RSI严重超买
                current_price < self.sma_slow[0] * 0.95  # 跌破慢线5%
            ]
            
            if any(sell_conditions):
                self.order = self.sell()
                reasons = []
                if sell_conditions[0]: reasons.append("死叉")
                if sell_conditions[1]: reasons.append("RSI超买")
                if sell_conditions[2]: reasons.append("跌破支撑")
                self.log(f'卖出信号: {"/".join(reasons)} RSI={self.rsi[0]:.1f}')
    
    def stop(self):
        final_value = self.broker.getvalue()
        return_pct = (final_value - 10000) / 10000 * 100
        win_rate = (self.wins / self.trades * 100) if self.trades > 0 else 0
        
        self.log('=' * 50)
        self.log(f'加密货币策略结果:')
        self.log(f'最终价值: ${final_value:.2f}')
        self.log(f'收益率: {return_pct:+.2f}%')
        self.log(f'交易次数: {self.trades}')
        if self.trades > 0:
            self.log(f'胜率: {win_rate:.1f}%')
        self.log('=' * 50)

def run_crypto_backtest(symbol='BTCUSDT'):
    """运行加密货币回测"""
    
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(CryptoStrategy)
    
    # 添加数据源
    data = CryptoDataFeed(symbol=symbol, interval='1d', limit=90)  # 90天数据
    cerebro.adddata(data)
    
    # 设置参数
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1%手续费
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    print(f'🚀 {symbol} 加密货币策略回测')
    print(f'💰 初始资金: ${cerebro.broker.getvalue():.2f}')
    print('-' * 50)
    
    # 运行
    results = cerebro.run()
    
    if results:
        strat = results[0]
        
        try:
            trades = strat.analyzers.trades.get_analysis()
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            
            print(f'\n📊 策略分析:')
            
            total = trades.get('total', {}).get('total', 0)
            won = trades.get('won', {}).get('total', 0)
            
            if total > 0:
                win_rate = (won / total) * 100
                print(f'总交易: {total}, 胜率: {win_rate:.1f}%')
                
                avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
                avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
                
                if avg_win and avg_loss:
                    print(f'平均盈利: ${avg_win:.2f}')
                    print(f'平均亏损: ${avg_loss:.2f}')
                    print(f'盈亏比: {abs(avg_win/avg_loss):.2f}')
            
            sharpe_ratio = sharpe.get('sharperatio')
            if sharpe_ratio and not (sharpe_ratio != sharpe_ratio):  # 检查NaN
                print(f'夏普比率: {sharpe_ratio:.3f}')
            
            max_drawdown = drawdown.get('max', {}).get('drawdown', 0)
            if max_drawdown:
                print(f'最大回撤: {max_drawdown:.2f}%')
                
        except Exception as e:
            print(f'分析器获取失败: {e}')
    
    print(f'💰 最终资金: ${cerebro.broker.getvalue():.2f}')
    
    return cerebro

def get_crypto_market_overview():
    """获取加密货币市场概览"""
    
    api = SimpleBinanceAPI()
    
    print("🌟 加密货币市场快照")
    print("=" * 60)
    
    # 获取热门交易对
    top_pairs = api.get_top_volume_pairs('USDT', 8)
    
    if top_pairs:
        print(f"{'排名':<4} {'交易对':<12} {'价格':<15} {'24H涨跌%':<10} {'成交额(M)':<12}")
        print("-" * 65)
        
        for i, pair in enumerate(top_pairs, 1):
            symbol = pair['symbol']
            price = float(pair['lastPrice'])
            change_pct = float(pair['priceChangePercent'])
            volume_m = float(pair['quoteVolume']) / 1_000_000  # 转换为百万
            
            change_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
            
            print(f"{i:<4} {symbol:<12} ${price:<14.4f} {change_emoji}{change_pct:+6.2f}% ${volume_m:>10.1f}M")
    else:
        # 备用方案：手动列出主要货币
        major_cryptos = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        
        print(f"{'交易对':<12} {'价格':<15} {'24H涨跌%':<12} {'成交额':<15}")
        print("-" * 60)
        
        for symbol in major_cryptos:
            ticker = api.get_24hr_ticker(symbol)
            
            if ticker:
                price = float(ticker['lastPrice'])
                change_pct = float(ticker['priceChangePercent'])
                volume = float(ticker['quoteVolume'])
                
                change_emoji = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
                
                print(f"{symbol:<12} ${price:<14.4f} {change_emoji}{change_pct:+6.2f}% ${volume:>13,.0f}")
            else:
                print(f"{symbol:<12} 数据获取失败")

def create_futures_demo():
    """创建期货交易演示"""
    
    print("\n🔮 期货交易系统框架")
    print("=" * 50)
    
    print("📋 期货交易特点:")
    print("  ✅ 杠杆交易 (10x-100x)")
    print("  ✅ 多空双向交易")
    print("  ✅ 保证金制度")
    print("  ✅ 强制平仓机制")
    print("  ✅ 资金费率")
    
    print("\n🛠️ 期货策略框架:")
    
    futures_strategy_code = """
class FuturesStrategy(bt.Strategy):
    params = (
        ('leverage', 10),      # 杠杆倍数
        ('margin_ratio', 0.1), # 保证金比例
        ('stop_loss', 0.05),   # 止损比例
    )
    
    def __init__(self):
        self.sma = bt.indicators.SMA(period=20)
        self.rsi = bt.indicators.RSI()
        self.position_value = 0
        self.margin_used = 0
    
    def next(self):
        # 期货交易逻辑
        if not self.position:
            if self.rsi[0] < 30:  # 超卖做多
                size = self.calculate_futures_size()
                self.buy(size=size)
        else:
            if self.rsi[0] > 70:  # 超买平仓
                self.close()
    
    def calculate_futures_size(self):
        # 计算期货合约数量
        available_cash = self.broker.get_cash()
        margin_per_contract = self.data.close[0] * self.p.margin_ratio
        max_contracts = available_cash / margin_per_contract
        return int(max_contracts * 0.5)  # 使用50%资金
"""
    
    print(futures_strategy_code)
    
    print("⚠️ 期货交易风险提示:")
    print("  • 高杠杆带来高风险")
    print("  • 可能损失超过本金")
    print("  • 需要严格的风险管理")
    print("  • 建议模拟交易验证策略")

if __name__ == '__main__':
    """运行演示"""
    
    print("🎯 加密货币 & 期货交易系统")
    print("=" * 60)
    
    try:
        # 1. 市场概览
        get_crypto_market_overview()
        
        # 2. 策略回测
        print(f"\n" + "=" * 60)
        
        # 测试主要加密货币
        test_symbols = ['BTCUSDT', 'ETHUSDT']
        
        for symbol in test_symbols:
            print(f"\n🔍 测试 {symbol}:")
            try:
                cerebro = run_crypto_backtest(symbol)
                print(f"✅ {symbol} 回测完成")
            except Exception as e:
                print(f"❌ {symbol} 回测失败: {e}")
        
        # 3. 期货交易演示
        create_futures_demo()
        
        print(f"\n" + "=" * 60)
        print("🎉 加密货币 & 期货系统演示完成!")
        print("\n📚 系统功能:")
        print("  ✅ 实时Binance数据获取")
        print("  ✅ 多加密货币支持")
        print("  ✅ 技术指标策略")
        print("  ✅ 风险控制机制")
        print("  ✅ 期货交易框架")
        print("  ✅ 市场分析工具")
        
        print(f"\n💡 使用建议:")
        print(f"  • 先在模拟环境测试")
        print(f"  • 控制仓位大小")
        print(f"  • 设置止损止盈")
        print(f"  • 关注市场风险")
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n🔧 故障排除:")
        print(f"  • 检查网络连接")
        print(f"  • 安装依赖: pip install requests")
        print(f"  • 确认Binance API可访问")
        print(f"  • 检查防火墙设置")