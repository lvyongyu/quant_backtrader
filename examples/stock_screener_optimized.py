#!/usr/bin/env python3
"""
智能股票筛选器 v2.0 - 优化版
Intelligent Stock Screener v2.0 - Optimized for API Rate Limits

解决API频率限制问题的优化版本
"""

import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime, timedelta
import sys
import os
import warnings
import random
from functools import wraps
warnings.filterwarnings('ignore')

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from data.stock_universe import StockUniverse

# 导入分析模块
try:
    from analyzers.fundamental_analyzer import FundamentalAnalyzer
    from analyzers.market_environment import MarketEnvironmentAnalyzer
    ENABLE_FUNDAMENTAL = True
    ENABLE_MARKET_ENV = True
except ImportError as e:
    print(f"⚠️ 分析模块导入失败: {e}")
    print("📊 将使用纯技术分析模式")
    ENABLE_FUNDAMENTAL = False
    ENABLE_MARKET_ENV = False

def rate_limit_retry(max_retries=3, base_delay=2.0):
    """
    API频率限制重试装饰器
    使用指数退避策略处理Too Many Requests错误
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    # 添加随机延迟避免所有线程同时请求
                    if attempt > 0:
                        delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0.5, 2.0)
                        time.sleep(delay)
                    
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'rate limit' in error_msg or 'too many requests' in error_msg:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt) + random.uniform(2.0, 4.0)
                            print(f"⏱️ API限制，等待 {delay:.1f}秒后重试...")
                            time.sleep(delay)
                            continue
                        else:
                            print(f"❌ API频率限制，重试失败: {e}")
                            return None
                    else:
                        # 其他错误直接抛出
                        raise e
            return None
        return wrapper
    return decorator

class StockScreener:
    """优化版股票筛选器 - 解决API频率限制问题"""
    
    def __init__(self, enable_fundamental=True, enable_market_env=True):
        self.results = []
        self.failed_stocks = []
        
        # 初始化股票池管理器
        self.stock_universe = StockUniverse()
        
        # 初始化分析器
        self.enable_fundamental = enable_fundamental and ENABLE_FUNDAMENTAL
        self.enable_market_env = enable_market_env and ENABLE_MARKET_ENV
        
        if self.enable_fundamental:
            self.fundamental_analyzer = FundamentalAnalyzer()
            print("📊 基本面分析器已启用")
            
        if self.enable_market_env:
            self.market_env_analyzer = MarketEnvironmentAnalyzer()
            print("🌍 市场环境分析器已启用")
        
        # 设置权重
        if self.enable_fundamental and self.enable_market_env:
            # 三维度分析模式
            self.weights = {
                'technical_score': 0.50,    # 技术分析 50%
                'fundamental_score': 0.30,  # 基本面分析 30%
                'market_fit_score': 0.20    # 市场环境匹配 20%
            }
            print("🎯 三维度分析模式: 技术分析50% + 基本面30% + 市场环境20%")
        elif self.enable_fundamental:
            # 技术+基本面分析模式
            self.weights = {
                'technical_score': 0.65,    # 技术分析 65%
                'fundamental_score': 0.35   # 基本面分析 35%
            }
            print("🎯 技术+基本面分析模式: 技术分析65% + 基本面35%")
        else:
            # 纯技术分析模式
            self.weights = {
                'technical_score': 1.0      # 技术分析 100%
            }
            print("🎯 纯技术分析模式: 技术分析100%")
        
        print("🎯 智能股票筛选器初始化完成")
        print(f"📊 评分维度: {len(self.weights)}个主要维度")

    @rate_limit_retry(max_retries=3, base_delay=2.0)
    def fetch_stock_data(self, symbol):
        """获取股票数据 - 带重试机制"""
        # 添加随机延迟
        time.sleep(random.uniform(0.2, 0.8))
        
        stock = yf.Ticker(symbol)
        df = stock.history(period="6mo", interval="1d")
        
        if df.empty or len(df) < 50:
            raise Exception(f"数据不足: 只有{len(df)}条记录")
        
        return df

    def calculate_technical_indicators(self, df):
        """计算技术指标"""
        try:
            # 移动平均线
            df['sma_5'] = df['Close'].rolling(window=5).mean()
            df['sma_10'] = df['Close'].rolling(window=10).mean()
            df['sma_20'] = df['Close'].rolling(window=20).mean()
            df['sma_50'] = df['Close'].rolling(window=50).mean()
            
            # 指数移动平均线
            df['ema_12'] = df['Close'].ewm(span=12).mean()
            df['ema_26'] = df['Close'].ewm(span=26).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 布林带
            df['bb_middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # 成交量指标
            df['volume_sma'] = df['Volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['Volume'] / df['volume_sma']
            
            # 波动率
            df['volatility'] = df['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
            
            # 动量指标
            df['momentum_5'] = df['Close'].pct_change(5)
            df['momentum_10'] = df['Close'].pct_change(10)
            df['momentum_20'] = df['Close'].pct_change(20)
            
            return df
            
        except Exception as e:
            print(f"❌ 技术指标计算错误: {e}")
            return df

    def analyze_single_stock(self, symbol):
        """分析单只股票 - 优化版"""
        try:
            # 获取数据
            df = self.fetch_stock_data(symbol)
            
            # 计算技术指标
            df = self.calculate_technical_indicators(df)
            
            # 技术分析评分
            tech_scores = self.calculate_technical_scores(df)
            technical_score = tech_scores['technical_score']
            
            # 获取最新数据
            latest = df.iloc[-1]
            
            # 基本面分析
            fundamental_score = 50  # 默认值
            fundamental_details = {}
            
            if self.enable_fundamental:
                try:
                    print(f"📊 开始分析 {symbol} 的基本面...")
                    fund_result = self.fundamental_analyzer.analyze_fundamentals(symbol)
                    if fund_result:
                        fundamental_score = fund_result.get('total_score', 50)
                        fundamental_details = {
                            'valuation_score': fund_result.get('valuation_score', 0),
                            'health_score': fund_result.get('health_score', 0),
                            'profitability_score': fund_result.get('profitability_score', 0),
                            'growth_score': fund_result.get('growth_score', 0),
                            'dividend_score': fund_result.get('dividend_score', 0),
                            'sector': fund_result.get('sector', 'Unknown')
                        }
                except Exception as e:
                    print(f"⚠️ {symbol} 基本面分析失败: {e}")
            
            # 市场环境分析
            market_fit_score = 75  # 默认值
            market_details = {}
            
            if self.enable_market_env:
                try:
                    print(f"🌍 分析市场环境...")
                    fit_result = self.market_env_analyzer.get_stock_environment_fit(symbol)
                    if fit_result:
                        market_fit_score = fit_result.get('fit_score', 75)
                        market_details = {
                            'fit_reason': fit_result.get('fit_reason', ''),
                            'beta': fit_result.get('beta', 1.0),
                            'market_environment': fit_result.get('market_environment', ''),
                            'stock_momentum_20d': fit_result.get('stock_momentum_20d', 0)
                        }
                except Exception as e:
                    print(f"⚠️ {symbol} 市场环境分析失败: {e}")
            
            # 计算综合得分
            final_score = 0
            score_breakdown = {}
            
            if 'technical_score' in self.weights:
                final_score += technical_score * self.weights['technical_score']
                score_breakdown['technical_score'] = round(technical_score, 1)
            
            if 'fundamental_score' in self.weights:
                final_score += fundamental_score * self.weights['fundamental_score']
                score_breakdown['fundamental_score'] = round(fundamental_score, 1)
            
            if 'market_fit_score' in self.weights:
                final_score += market_fit_score * self.weights['market_fit_score']
                score_breakdown['market_fit_score'] = round(market_fit_score, 1)
            
            # 额外加分项
            bonus_points = self.calculate_bonus_points(df, latest)
            final_score += bonus_points
            final_score = min(final_score, 100)
            
            # 构建结果
            result = {
                'symbol': symbol,
                'total_score': round(final_score, 2),
                'score_breakdown': score_breakdown,
                'technical_details': {
                    'trend_score': round(tech_scores['trend_score'], 1),
                    'momentum_score': round(tech_scores['momentum_score'], 1),
                    'volatility_score': round(tech_scores['volatility_score'], 1),
                    'volume_score': round(tech_scores['volume_score'], 1),
                    'technical_score': round(tech_scores['technical_score'], 1)
                },
                'fundamental_details': fundamental_details,
                'market_details': market_details,
                'current_price': round(latest['Close'], 2),
                'volume_ratio': round(latest['volume_ratio'], 2) if not pd.isna(latest['volume_ratio']) else 0,
                'rsi': round(latest['rsi'], 1) if not pd.isna(latest['rsi']) else 0,
                'momentum_20': round(latest['momentum_20'] * 100, 2) if not pd.isna(latest['momentum_20']) else 0,
                'volatility': round(latest['volatility'] * 100, 2) if not pd.isna(latest['volatility']) else 0,
                'bonus_points': bonus_points
            }
            
            return result
            
        except Exception as e:
            print(f"❌ {symbol} 分析失败: {e}")
            return None

    def calculate_technical_scores(self, df):
        """计算技术分析各项得分"""
        latest = df.iloc[-1]
        scores = {}
        
        # 1. 趋势得分 (25%)
        trend_score = 0
        if latest['Close'] > latest['sma_20']:
            trend_score += 25
        if latest['sma_20'] > latest['sma_50']:
            trend_score += 25
        if latest['Close'] > latest['sma_5']:
            trend_score += 25
        if latest['ema_12'] > latest['ema_26']:
            trend_score += 25
        
        scores['trend_score'] = min(trend_score, 100)
        
        # 2. 动量得分 (25%)
        momentum_score = 0
        if latest['rsi'] > 30 and latest['rsi'] < 70:
            momentum_score += 50
        if latest['macd'] > latest['macd_signal']:
            momentum_score += 50
        
        scores['momentum_score'] = min(momentum_score, 100)
        
        # 3. 波动得分 (20%) - 低波动率更好
        volatility_score = 100
        if latest['volatility'] > 0.4:  # 高波动
            volatility_score = 20
        elif latest['volatility'] > 0.3:
            volatility_score = 60
        elif latest['volatility'] > 0.2:
            volatility_score = 100
        
        scores['volatility_score'] = volatility_score
        
        # 4. 成交量得分 (15%)
        volume_score = 0
        if latest['volume_ratio'] > 1.5:  # 成交量放大
            volume_score = 100
        elif latest['volume_ratio'] > 1.2:
            volume_score = 80
        elif latest['volume_ratio'] > 1.0:
            volume_score = 60
        elif latest['volume_ratio'] > 0.8:
            volume_score = 40
        else:
            volume_score = 20
        
        # 计算标准化成交量得分
        volume_score = min(latest['volume_ratio'] * 30, 100)
        scores['volume_score'] = volume_score
        
        # 5. 技术指标得分 (15%)
        tech_score = 0
        # 布林带位置
        if 0.2 <= latest['bb_position'] <= 0.8:
            tech_score += 30
        # RSI范围
        if 40 <= latest['rsi'] <= 70:
            tech_score += 40
        # MACD信号
        if latest['macd_histogram'] > 0:
            tech_score += 30
        
        scores['technical_score'] = min(tech_score, 100)
        
        # 综合技术得分
        weights = {
            'trend_score': 0.25,
            'momentum_score': 0.25,
            'volatility_score': 0.20,
            'volume_score': 0.15,
            'technical_score': 0.15
        }
        
        technical_total = sum(scores[key] * weights[key] for key in weights)
        scores['technical_score'] = technical_total
        
        return scores

    def calculate_bonus_points(self, df, latest):
        """计算额外加分项"""
        bonus_points = 0
        
        # 近期表现
        if latest['momentum_20'] > 0.1:  # 20日涨幅>10%
            bonus_points += 20
        elif latest['momentum_20'] > 0.05:  # 20日涨幅>5%
            bonus_points += 15
        elif latest['momentum_20'] > 0.02:  # 20日涨幅>2%
            bonus_points += 10
        
        # RSI适中
        if 50 <= latest['rsi'] <= 70:
            bonus_points += 5
        
        return min(bonus_points, 25)

    def screen_stocks(self, symbols=None, max_workers=3):
        """
        批量筛选股票 - 优化版本
        默认使用3个线程以避免API频率限制
        """
        
        if symbols is None:
            symbols = self.get_stock_list()
        
        # 对于大批量股票，进一步降低并发数
        if len(symbols) > 200:
            max_workers = 2
            print(f"📊 大批量处理({len(symbols)}只)，降低并发数到 {max_workers} 以避免API限制")
        elif len(symbols) > 100:
            max_workers = min(max_workers, 3)
            print(f"📊 中等批量处理({len(symbols)}只)，使用 {max_workers} 个线程")
        
        print(f"\n🔍 开始筛选 {len(symbols)} 只股票...")
        print(f"⚡ 使用 {max_workers} 个线程并行处理")
        
        start_time = time.time()
        self.results = []
        self.failed_stocks = []
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_symbol = {
                executor.submit(self.analyze_single_stock, symbol): symbol 
                for symbol in symbols
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_symbol):
                completed += 1
                symbol = future_to_symbol[future]
                
                try:
                    result = future.result()
                    if result:
                        self.results.append(result)
                        print(f"✅ {symbol}: {result['total_score']:.1f}分 "
                              f"({completed}/{len(symbols)})")
                    else:
                        print(f"❌ {symbol}: 分析失败 ({completed}/{len(symbols)})")
                        self.failed_stocks.append(f"{symbol}: 数据获取失败")
                        
                except Exception as e:
                    error_msg = str(e)
                    if 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower():
                        print(f"❌ {symbol}: API限制 ({completed}/{len(symbols)})")
                    else:
                        print(f"❌ {symbol}: 异常 - {e} ({completed}/{len(symbols)})")
                    self.failed_stocks.append(f"{symbol}: {str(e)}")
                
                # 添加小延迟避免过快请求
                if completed % 5 == 0:
                    time.sleep(1.0)
        
        # 按得分排序
        self.results.sort(key=lambda x: x['total_score'], reverse=True)
        
        elapsed_time = time.time() - start_time
        success_rate = len(self.results) / len(symbols) * 100
        
        print(f"\n📊 筛选完成!")
        print(f"⏱️  用时: {elapsed_time:.1f}秒")
        print(f"✅ 成功: {len(self.results)}只股票")
        print(f"❌ 失败: {len(self.failed_stocks)}只股票")
        print(f"📈 成功率: {success_rate:.1f}%")
        
        return self.results

    def get_stock_list(self, source='sp500'):
        """获取股票列表"""
        if source == 'sp500':
            return self.stock_universe.get_sp500_stocks()
        elif source == 'nasdaq100':
            return self.stock_universe.get_nasdaq100_stocks()
        elif source == 'chinese':
            return self.stock_universe.get_chinese_adrs()
        elif source == 'crypto':
            return self.stock_universe.get_crypto_related_stocks()
        elif source == 'etfs':
            return self.stock_universe.get_popular_etfs()
        elif source == 'comprehensive':
            return self.stock_universe.get_custom_universe(max_stocks=200)  # 限制数量
        else:
            return self.stock_universe.get_sp500_stocks()

    def get_top3(self):
        """获取TOP3结果"""
        return self.results[:3] if len(self.results) >= 3 else self.results

    def show_top3_results(self):
        """显示TOP3分析结果"""
        
        if not self.results:
            print("❌ 没有分析结果")
            return
        
        print("\n🏆 TOP3 最值得购买的股票")
        print("=" * 80)
        
        top3 = self.get_top3()
        medals = ["🥇", "🥈", "🥉"]
        
        for i, stock in enumerate(top3):
            medal = medals[i] if i < 3 else f"{i+1:2d}"
            
            print(f"\n{medal} 第{i+1}名: {stock['symbol']}")
            print(f"   💯 综合得分: {stock['total_score']}/100")
            print(f"   💰 当前价格: ${stock['current_price']}")
            
            # 评分构成
            breakdown = stock['score_breakdown']
            print(f"   📊 评分构成:")
            if 'technical_score' in breakdown:
                weight = int(self.weights.get('technical_score', 0) * 100)
                print(f"      🔧 技术分析: {breakdown['technical_score']}/100 (权重{weight}%)")
            if 'fundamental_score' in breakdown:
                weight = int(self.weights.get('fundamental_score', 0) * 100)
                print(f"      📊 基本面: {breakdown['fundamental_score']}/100 (权重{weight}%)")
            if 'market_fit_score' in breakdown:
                weight = int(self.weights.get('market_fit_score', 0) * 100)
                print(f"      🌍 市场匹配: {breakdown['market_fit_score']}/100 (权重{weight}%)")
            
            # 技术分析详情
            tech_details = stock['technical_details']
            print(f"   🔧 技术分析详情:")
            print(f"      📈 趋势得分: {tech_details.get('trend_score', 0):.1f}/100")
            print(f"      ⚡ 动量得分: {tech_details.get('momentum_score', 0):.1f}/100")
            print(f"      📉 波动得分: {tech_details.get('volatility_score', 0):.1f}/100")
            print(f"      📊 成交量得分: {tech_details.get('volume_score', 0):.1f}/100")
            print(f"      🎯 技术指标得分: {tech_details.get('technical_score', 0):.1f}/100")
            
            # 基本面详情
            if self.enable_fundamental and stock['fundamental_details']:
                fund_details = stock['fundamental_details']
                print(f"   📊 基本面详情:")
                print(f"      💎 估值得分: {fund_details.get('valuation_score', 0):.1f}/100")
                print(f"      💪 财务健康: {fund_details.get('health_score', 0):.1f}/100")
                print(f"      💰 盈利能力: {fund_details.get('profitability_score', 0):.1f}/100")
                print(f"      🚀 成长性: {fund_details.get('growth_score', 0):.1f}/100")
                if fund_details.get('sector'):
                    print(f"      🏢 行业: {fund_details.get('sector')}")
            
            # 市场环境详情
            if self.enable_market_env and stock['market_details']:
                market_details = stock['market_details']
                print(f"   🌍 市场环境匹配:")
                if market_details.get('fit_reason'):
                    print(f"      💡 匹配原因: {market_details.get('fit_reason')}")
                if market_details.get('market_environment'):
                    print(f"      📈 市场环境: {market_details.get('market_environment')}")
                if market_details.get('beta'):
                    print(f"      📊 Beta系数: {market_details.get('beta'):.2f}")
            
            # 关键指标
            print(f"   📋 关键指标:")
            print(f"      RSI: {stock['rsi']}")
            print(f"      成交量比: {stock['volume_ratio']:.2f}x")
            print(f"      20日涨幅: {stock['momentum_20']:+.2f}%")
            print(f"      波动率: {stock['volatility']:.1f}%")
            
            if stock['bonus_points'] > 0:
                print(f"      🎁 加分项: +{stock['bonus_points']}分")

def run_stock_screening(source='sp500', max_stocks=None):
    """运行股票筛选的主函数"""
    
    print("🎯 智能股票筛选器")
    print("🔍 从动态数据源筛选最值得购买的TOP3")
    print("=" * 80)
    
    # 创建筛选器
    screener = StockScreener(enable_fundamental=True, enable_market_env=True)
    
    # 获取股票列表
    print(f"🔍 获取股票列表 - 数据源: {source}")
    
    if source == 'sp500':
        symbols_list = screener.stock_universe.get_sp500_stocks()
        data_desc = "标普500成分股 - 美国大盘蓝筹股"
    elif source == 'nasdaq100':
        symbols_list = screener.stock_universe.get_nasdaq100_stocks()
        data_desc = "纳斯达克100 - 科技成长股为主"
    elif source == 'chinese':
        symbols_list = screener.stock_universe.get_chinese_adrs()
        data_desc = "中概股ADR - 在美上市中国公司"
    elif source == 'crypto':
        symbols_list = screener.stock_universe.get_crypto_related_stocks()
        data_desc = "加密货币相关股票 - 区块链概念"
    elif source == 'etfs':
        symbols_list = screener.stock_universe.get_popular_etfs()
        data_desc = "热门ETF - 指数基金和主题基金"
    elif source == 'comprehensive':
        symbols_list = screener.stock_universe.get_custom_universe(max_stocks=200)
        data_desc = "综合股票池 - 多元化投资组合"
    else:
        symbols_list = screener.stock_universe.get_sp500_stocks()
        data_desc = "默认股票池 - 标普500"
    
    if max_stocks and len(symbols_list) > max_stocks:
        symbols_list = symbols_list[:max_stocks]
        print(f"⚠️ 股票池已限制到 {max_stocks} 只")
    
    print(f"\n📋 股票池: {len(symbols_list)}只股票 (数据源: {source})")
    print(f"📊 数据源说明: {data_desc}")
    
    # 执行筛选
    results = screener.screen_stocks(symbols_list, max_workers=2)  # 降低并发数
    
    if results:
        # 显示TOP3结果
        screener.show_top3_results()
        top3 = screener.get_top3()
        return top3
    else:
        print("❌ 没有成功分析的股票")
        return []

if __name__ == "__main__":
    # 示例用法
    top_picks = run_stock_screening('sp500', max_stocks=50)  # 限制数量测试
    
    if top_picks:
        print(f"\n✅ 筛选完成! TOP3结果:")
        for i, stock in enumerate(top_picks, 1):
            print(f"  {i}. {stock['symbol']}: {stock['total_score']:.1f}分")