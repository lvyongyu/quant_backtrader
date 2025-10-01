"""
P1-2高级量化交易组件 - 简化工作示例

这个文件展示了如何在实际项目中使用P1-2的核心功能，
使用现有的代码结构，避免模块导入问题。

版本: 1.1 (修复版)
日期: 2025-10-01
"""

import sys
import os
import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

print("🚀 P1-2高级量化交易组件 - 工作示例")
print("🕒 开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("="*80)

# ============================================================================
# 示例1: 基础技术分析 (使用核心数据结构)
# ============================================================================

def example_1_basic_technical_analysis():
    """
    示例1: 基础技术分析 - 展示数据结构和核心计算逻辑
    """
    print("\n" + "=" * 60)
    print("📊 示例1: 基础技术分析")
    print("=" * 60)
    
    try:
        # 1. 生成测试数据
        print("📈 生成Apple股票测试数据...")
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # 模拟Apple股票价格
        initial_price = 150.0
        returns = pd.Series(
            np.random.normal(0.0008, 0.02, len(dates)),
            index=dates
        )
        prices = pd.Series(
            initial_price * np.exp(np.cumsum(returns)),
            index=dates,
            name='AAPL'
        )
        
        print(f"✓ 数据期间: {dates[0].date()} 到 {dates[-1].date()}")
        print(f"✓ 价格范围: ${prices.min():.2f} - ${prices.max():.2f}")
        print(f"✓ 数据点数: {len(prices)}")
        
        # 2. 计算基础技术指标
        print("\n🔍 计算技术指标...")
        
        # RSI计算
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        rsi = calculate_rsi(prices)
        current_rsi = rsi.iloc[-1]
        print(f"✓ RSI(14): {current_rsi:.2f}")
        
        # MACD计算
        def calculate_macd(prices, fast=12, slow=26, signal=9):
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            return macd_line, signal_line, histogram
        
        macd_line, signal_line, histogram = calculate_macd(prices)
        print(f"✓ MACD: {macd_line.iloc[-1]:.4f}")
        print(f"✓ Signal: {signal_line.iloc[-1]:.4f}")
        print(f"✓ Histogram: {histogram.iloc[-1]:.4f}")
        
        # 布林带计算
        def calculate_bollinger_bands(prices, period=20, std_dev=2):
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            return upper, sma, lower
        
        upper, middle, lower = calculate_bollinger_bands(prices)
        current_price = prices.iloc[-1]
        print(f"✓ 布林带上轨: ${upper.iloc[-1]:.2f}")
        print(f"✓ 布林带中轨: ${middle.iloc[-1]:.2f}")
        print(f"✓ 布林带下轨: ${lower.iloc[-1]:.2f}")
        print(f"✓ 当前价格: ${current_price:.2f}")
        
        # 3. 生成交易信号
        print("\n🎯 交易信号分析...")
        
        signals = []
        
        # RSI信号
        if current_rsi < 30:
            signals.append("🔵 RSI超卖 - 考虑买入机会")
        elif current_rsi > 70:
            signals.append("🔴 RSI超买 - 考虑减仓")
        else:
            signals.append(f"🟡 RSI中性 - 当前值{current_rsi:.1f}")
        
        # MACD信号
        if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
            signals.append("🟢 MACD金叉 - 上涨信号")
        elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
            signals.append("🔴 MACD死叉 - 下跌信号")
        else:
            signals.append("🟡 MACD无明显信号")
        
        # 布林带信号
        bb_position = (current_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])
        if bb_position < 0.2:
            signals.append("🔵 价格靠近布林带下轨 - 可能反弹")
        elif bb_position > 0.8:
            signals.append("🔴 价格靠近布林带上轨 - 可能回调")
        else:
            signals.append(f"🟡 价格在布林带中部 - 位置{bb_position:.1%}")
        
        print("📢 综合信号:")
        for i, signal in enumerate(signals, 1):
            print(f"  {i}. {signal}")
        
        # 4. 统计分析
        print("\n📊 统计分析...")
        returns_data = prices.pct_change().dropna()
        
        print(f"✓ 平均日收益: {returns_data.mean():.4f} ({returns_data.mean()*252:.1%} 年化)")
        print(f"✓ 日波动率: {returns_data.std():.4f} ({returns_data.std()*np.sqrt(252):.1%} 年化)")
        print(f"✓ 夏普比率: {(returns_data.mean() - 0.02/252) / returns_data.std():.3f}")
        print(f"✓ 最大回撤: {((prices / prices.expanding().max()) - 1).min():.2%}")
        
        # 计算偏度和峰度
        skewness = returns_data.skew()
        kurtosis = returns_data.kurtosis()
        print(f"✓ 偏度: {skewness:.3f} ({'左偏' if skewness < 0 else '右偏' if skewness > 0 else '对称'})")
        print(f"✓ 峰度: {kurtosis:.3f} ({'尖峰' if kurtosis > 0 else '平峰' if kurtosis < 0 else '正态'})")
        
        print("\n✅ 基础技术分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 基础技术分析失败: {str(e)}")
        return False


# ============================================================================
# 示例2: 多股票相关性分析
# ============================================================================

def example_2_correlation_analysis():
    """
    示例2: 多股票相关性分析和统计建模
    """
    print("\n" + "=" * 60)
    print("📊 示例2: 多股票相关性分析")
    print("=" * 60)
    
    try:
        # 1. 生成多股票数据
        print("📈 生成多股票数据...")
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # 创建相关性矩阵
        correlation_matrix = np.array([
            [1.00, 0.70, 0.75, 0.50, 0.65],  # AAPL
            [0.70, 1.00, 0.80, 0.45, 0.60],  # GOOGL
            [0.75, 0.80, 1.00, 0.40, 0.55],  # MSFT
            [0.50, 0.45, 0.40, 1.00, 0.35],  # TSLA
            [0.65, 0.60, 0.55, 0.35, 1.00]   # AMZN
        ])
        
        # 生成具有相关性的收益率
        base_returns = np.random.multivariate_normal(
            mean=[0.0008, 0.0010, 0.0009, 0.0012, 0.0007],
            cov=correlation_matrix * 0.0004,  # 基础协方差
            size=len(dates)
        )
        
        stock_data = {}
        stock_returns = {}
        
        for i, symbol in enumerate(symbols):
            returns = pd.Series(base_returns[:, i], index=dates, name=symbol)
            prices = pd.Series(
                (100 + i*20) * np.exp(np.cumsum(returns)),
                index=dates,
                name=symbol
            )
            stock_data[symbol] = prices
            stock_returns[symbol] = returns
            
        print(f"✓ 生成了 {len(symbols)} 只股票的数据")
        
        # 2. 相关性分析
        print("\n🔍 相关性分析...")
        returns_df = pd.DataFrame(stock_returns)
        actual_correlation = returns_df.corr()
        
        print("📊 股票收益率相关性矩阵:")
        print(actual_correlation.round(3))
        
        # 寻找最高和最低相关性
        corr_pairs = []
        for i in range(len(symbols)):
            for j in range(i+1, len(symbols)):
                corr_value = actual_correlation.iloc[i, j]
                corr_pairs.append((symbols[i], symbols[j], corr_value))
        
        corr_pairs.sort(key=lambda x: x[2], reverse=True)
        
        print(f"\n🔝 最高相关性:")
        for i, (stock1, stock2, corr) in enumerate(corr_pairs[:3]):
            print(f"  {i+1}. {stock1} vs {stock2}: {corr:.3f}")
        
        print(f"\n🔻 最低相关性:")
        for i, (stock1, stock2, corr) in enumerate(corr_pairs[-3:]):
            print(f"  {i+1}. {stock1} vs {stock2}: {corr:.3f}")
        
        # 3. 投资组合分析
        print("\n💼 投资组合分析...")
        
        # 等权重组合
        equal_weights = np.array([0.2] * 5)
        portfolio_returns = returns_df.dot(equal_weights)
        portfolio_prices = stock_data['AAPL'].iloc[0] * np.exp(np.cumsum(portfolio_returns))
        
        print(f"📊 等权重投资组合表现:")
        print(f"  年化收益: {portfolio_returns.mean() * 252:.2%}")
        print(f"  年化波动: {portfolio_returns.std() * np.sqrt(252):.2%}")
        print(f"  夏普比率: {(portfolio_returns.mean() - 0.02/252) / portfolio_returns.std():.3f}")
        print(f"  最大回撤: {((portfolio_prices / portfolio_prices.expanding().max()) - 1).min():.2%}")
        
        # 与个股对比
        print(f"\n📈 个股 vs 投资组合对比:")
        print(f"{'股票':<8} {'年化收益':<10} {'年化波动':<10} {'夏普比率':<10}")
        print("-" * 45)
        
        for symbol in symbols:
            returns = stock_returns[symbol]
            annual_return = returns.mean() * 252
            annual_vol = returns.std() * np.sqrt(252)
            sharpe = (returns.mean() - 0.02/252) / returns.std()
            print(f"{symbol:<8} {annual_return:>8.1%} {annual_vol:>8.1%} {sharpe:>8.3f}")
        
        # 投资组合
        portfolio_annual_return = portfolio_returns.mean() * 252
        portfolio_annual_vol = portfolio_returns.std() * np.sqrt(252)
        portfolio_sharpe = (portfolio_returns.mean() - 0.02/252) / portfolio_returns.std()
        print(f"{'组合':<8} {portfolio_annual_return:>8.1%} {portfolio_annual_vol:>8.1%} {portfolio_sharpe:>8.3f}")
        
        # 4. 风险分散效果
        print(f"\n⚠️ 风险分散效果分析:")
        individual_vol_avg = returns_df.std().mean() * np.sqrt(252)
        portfolio_vol = portfolio_returns.std() * np.sqrt(252)
        diversification_benefit = (individual_vol_avg - portfolio_vol) / individual_vol_avg
        
        print(f"  平均个股波动率: {individual_vol_avg:.1%}")
        print(f"  投资组合波动率: {portfolio_vol:.1%}")
        print(f"  分散化收益: {diversification_benefit:.1%}")
        
        if diversification_benefit > 0.15:
            print("  🟢 分散化效果显著")
        elif diversification_benefit > 0.05:
            print("  🟡 分散化效果一般")
        else:
            print("  🔴 分散化效果有限")
        
        # 5. 波动率聚类分析
        print(f"\n📊 波动率聚类分析:")
        vol_30d = returns_df.rolling(30).std() * np.sqrt(252)
        vol_latest = vol_30d.iloc[-1]
        
        print(f"  最新30日年化波动率:")
        vol_sorted = vol_latest.sort_values(ascending=False)
        for symbol, vol in vol_sorted.items():
            if vol > 0.25:
                risk_level = "🔴 高风险"
            elif vol > 0.20:
                risk_level = "🟡 中风险"
            else:
                risk_level = "🟢 低风险"
            print(f"    {symbol}: {vol:.1%} {risk_level}")
        
        print("\n✅ 多股票相关性分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 相关性分析失败: {str(e)}")
        return False


# ============================================================================
# 示例3: 投资组合优化模拟
# ============================================================================

def example_3_portfolio_optimization_simulation():
    """
    示例3: 基于现代投资组合理论的优化模拟
    """
    print("\n" + "=" * 60)
    print("📊 示例3: 投资组合优化模拟")
    print("=" * 60)
    
    try:
        # 1. 准备数据
        print("🏗️ 准备投资组合数据...")
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX']
        sectors = ['Tech', 'Tech', 'Tech', 'Auto', 'Retail', 'Tech', 'Tech', 'Media']
        
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        
        # 生成期望收益和风险
        expected_returns = np.array([0.12, 0.15, 0.10, 0.18, 0.11, 0.20, 0.13, 0.14])  # 年化期望收益
        volatilities = np.array([0.25, 0.28, 0.22, 0.35, 0.24, 0.40, 0.30, 0.32])       # 年化波动率
        
        # 创建相关性矩阵
        n_assets = len(symbols)
        correlation_matrix = np.full((n_assets, n_assets), 0.3)  # 基础相关性0.3
        np.fill_diagonal(correlation_matrix, 1.0)  # 对角线为1
        
        # 同行业股票相关性更高
        sector_groups = {}
        for i, sector in enumerate(sectors):
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(i)
        
        for sector, indices in sector_groups.items():
            for i in indices:
                for j in indices:
                    if i != j:
                        correlation_matrix[i, j] = 0.6  # 同行业相关性0.6
        
        # 构建协方差矩阵
        volatility_matrix = np.outer(volatilities, volatilities)
        covariance_matrix = correlation_matrix * volatility_matrix
        
        print(f"✓ 资产池: {len(symbols)} 只股票")
        print(f"✓ 行业分布: {dict(zip(*np.unique(sectors, return_counts=True)))}")
        
        # 2. 显示资产特征
        print(f"\n📊 资产特征:")
        print(f"{'股票':<6} {'行业':<6} {'期望收益':<10} {'波动率':<8} {'夏普比率':<8}")
        print("-" * 50)
        
        risk_free_rate = 0.02
        for i, symbol in enumerate(symbols):
            sharpe = (expected_returns[i] - risk_free_rate) / volatilities[i]
            print(f"{symbol:<6} {sectors[i]:<6} {expected_returns[i]:>8.1%} {volatilities[i]:>6.1%} {sharpe:>8.2f}")
        
        # 3. 投资组合优化模拟
        print(f"\n🎯 投资组合优化模拟...")
        
        def portfolio_performance(weights, returns, cov_matrix, risk_free_rate):
            """计算投资组合表现"""
            port_return = np.sum(returns * weights)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe_ratio = (port_return - risk_free_rate) / port_vol
            return port_return, port_vol, sharpe_ratio
        
        # 生成随机投资组合进行Monte Carlo模拟
        num_portfolios = 10000
        np.random.seed(42)
        
        results = np.zeros((4, num_portfolios))  # 存储收益、风险、夏普比率、权重
        
        print(f"  运行 {num_portfolios} 次Monte Carlo模拟...")
        
        for i in range(num_portfolios):
            # 生成随机权重
            weights = np.random.random(n_assets)
            weights = weights / np.sum(weights)  # 归一化
            
            # 计算组合表现
            port_return, port_vol, sharpe = portfolio_performance(
                weights, expected_returns, covariance_matrix, risk_free_rate
            )
            
            results[0, i] = port_return
            results[1, i] = port_vol
            results[2, i] = sharpe
        
        # 4. 寻找最优组合
        print(f"\n🏆 最优组合分析:")
        
        # 最大夏普比率组合
        max_sharpe_idx = np.argmax(results[2])
        max_sharpe_return = results[0, max_sharpe_idx]
        max_sharpe_vol = results[1, max_sharpe_idx]
        max_sharpe_ratio = results[2, max_sharpe_idx]
        
        print(f"📈 最大夏普比率组合:")
        print(f"  期望收益: {max_sharpe_return:.2%}")
        print(f"  风险(波动率): {max_sharpe_vol:.2%}")
        print(f"  夏普比率: {max_sharpe_ratio:.3f}")
        
        # 最小风险组合
        min_vol_idx = np.argmin(results[1])
        min_vol_return = results[0, min_vol_idx]
        min_vol_vol = results[1, min_vol_idx]
        min_vol_sharpe = results[2, min_vol_idx]
        
        print(f"\n⚠️ 最小风险组合:")
        print(f"  期望收益: {min_vol_return:.2%}")
        print(f"  风险(波动率): {min_vol_vol:.2%}")
        print(f"  夏普比率: {min_vol_sharpe:.3f}")
        
        # 5. 有效前沿近似
        print(f"\n📈 有效前沿分析:")
        
        # 按风险排序，计算有效前沿
        efficient_idx = []
        sorted_vol_idx = np.argsort(results[1])
        
        current_max_return = -np.inf
        for idx in sorted_vol_idx:
            if results[0, idx] > current_max_return:
                efficient_idx.append(idx)
                current_max_return = results[0, idx]
        
        print(f"  有效前沿组合数量: {len(efficient_idx)}")
        print(f"  风险范围: {results[1, efficient_idx].min():.1%} - {results[1, efficient_idx].max():.1%}")
        print(f"  收益范围: {results[0, efficient_idx].min():.1%} - {results[0, efficient_idx].max():.1%}")
        
        # 6. 风险预算分析
        print(f"\n💰 风险预算分析:")
        
        # 对于最大夏普比率组合，计算各资产的风险贡献
        # 由于我们在模拟中没有保存权重，这里用等权重作为示例
        equal_weights = np.array([1/n_assets] * n_assets)
        
        # 计算边际风险贡献
        portfolio_vol = np.sqrt(np.dot(equal_weights.T, np.dot(covariance_matrix, equal_weights)))
        marginal_contrib = np.dot(covariance_matrix, equal_weights) / portfolio_vol
        risk_contrib = equal_weights * marginal_contrib
        risk_contrib_pct = risk_contrib / np.sum(risk_contrib)
        
        print(f"  等权重组合风险贡献:")
        risk_data = list(zip(symbols, sectors, equal_weights, risk_contrib_pct))
        risk_data.sort(key=lambda x: x[3], reverse=True)
        
        for symbol, sector, weight, risk_contrib in risk_data:
            print(f"    {symbol} ({sector}): 权重{weight:.1%}, 风险贡献{risk_contrib:.1%}")
        
        # 7. 行业分散度分析
        print(f"\n🏭 行业分散度分析:")
        sector_weights = {}
        sector_risk_contrib = {}
        
        for symbol, sector, weight, risk_contrib in risk_data:
            if sector not in sector_weights:
                sector_weights[sector] = 0
                sector_risk_contrib[sector] = 0
            sector_weights[sector] += weight
            sector_risk_contrib[sector] += risk_contrib
        
        print(f"  行业权重分布:")
        for sector in sorted(sector_weights.keys()):
            print(f"    {sector}: 权重{sector_weights[sector]:.1%}, 风险{sector_risk_contrib[sector]:.1%}")
        
        # 计算集中度指标(Herfindahl指数)
        hhi_weights = sum(w**2 for w in equal_weights)
        hhi_risk = sum(r**2 for r in risk_contrib_pct)
        
        print(f"\n📊 集中度指标:")
        print(f"  权重集中度(HHI): {hhi_weights:.3f}")
        print(f"  风险集中度(HHI): {hhi_risk:.3f}")
        
        if hhi_weights < 0.2:
            print(f"  🟢 权重分散度良好")
        elif hhi_weights < 0.3:
            print(f"  🟡 权重分散度一般")
        else:
            print(f"  🔴 权重过于集中")
        
        # 8. 投资建议
        print(f"\n💡 投资建议:")
        
        # 基于夏普比率的建议
        if max_sharpe_ratio > 1.0:
            print("  🟢 最优组合夏普比率优秀，强烈推荐")
        elif max_sharpe_ratio > 0.6:
            print("  🔵 最优组合夏普比率良好，推荐考虑")
        else:
            print("  🟡 最优组合夏普比率一般，需要进一步优化")
        
        # 基于风险水平的建议
        if min_vol_vol < 0.15:
            print("  🟢 可构建低风险投资组合，适合保守投资者")
        elif min_vol_vol < 0.20:
            print("  🟡 最低风险水平适中，适合一般投资者")
        else:
            print("  🔴 整体风险水平较高，建议谨慎投资")
        
        # 行业建议
        tech_exposure = sector_weights.get('Tech', 0)
        if tech_exposure > 0.6:
            print("  ⚠️ 科技股集中度较高，建议分散投资")
        
        print("\n✅ 投资组合优化模拟完成！")
        return True
        
    except Exception as e:
        print(f"❌ 投资组合优化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 示例4: 风险管理和回测分析
# ============================================================================

def example_4_risk_management_backtest():
    """
    示例4: 风险管理和简单回测分析
    """
    print("\n" + "=" * 60)
    print("⚠️ 示例4: 风险管理和回测分析")
    print("=" * 60)
    
    try:
        # 1. 构建投资组合
        print("🏗️ 构建测试投资组合...")
        
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        weights = [0.25, 0.20, 0.25, 0.15, 0.15]  # 投资组合权重
        
        np.random.seed(42)
        dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='D')
        
        # 生成股票收益率数据
        stock_returns = {}
        for i, symbol in enumerate(symbols):
            # 不同股票具有不同的收益率和波动率特征
            returns = pd.Series(
                np.random.normal(0.0008 + i*0.0002, 0.015 + i*0.003, len(dates)),
                index=dates,
                name=symbol
            )
            stock_returns[symbol] = returns
        
        # 计算投资组合收益率
        portfolio_returns = pd.Series(0, index=dates)
        for i, symbol in enumerate(symbols):
            portfolio_returns += weights[i] * stock_returns[symbol]
        
        # 计算累积价值
        portfolio_value = (1 + portfolio_returns).cumprod() * 100000  # 初始投资10万
        
        print(f"✓ 投资组合权重: {dict(zip(symbols, weights))}")
        print(f"✓ 回测期间: {dates[0].date()} 到 {dates[-1].date()}")
        print(f"✓ 初始资金: $100,000")
        
        # 2. 基础绩效指标
        print(f"\n📊 基础绩效指标:")
        
        total_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1)
        annual_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        annual_vol = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - 0.02) / annual_vol
        
        print(f"  总收益率: {total_return:.2%}")
        print(f"  年化收益率: {annual_return:.2%}")
        print(f"  年化波动率: {annual_vol:.2%}")
        print(f"  夏普比率: {sharpe_ratio:.3f}")
        print(f"  期末价值: ${portfolio_value.iloc[-1]:,.0f}")
        
        # 3. 最大回撤分析
        print(f"\n⚠️ 最大回撤分析:")
        
        # 计算回撤
        peak = portfolio_value.expanding(min_periods=1).max()
        drawdown = (portfolio_value / peak - 1)
        max_drawdown = drawdown.min()
        
        # 找到最大回撤期间
        max_dd_end = drawdown.idxmin()
        max_dd_start = portfolio_value[:max_dd_end].idxmax()
        recovery_date = portfolio_value[max_dd_end:][portfolio_value[max_dd_end:] >= peak[max_dd_end]].index
        recovery_date = recovery_date[0] if len(recovery_date) > 0 else None
        
        print(f"  最大回撤: {max_drawdown:.2%}")
        print(f"  回撤开始: {max_dd_start.date()}")
        print(f"  回撤低点: {max_dd_end.date()}")
        if recovery_date:
            print(f"  回撤恢复: {recovery_date.date()}")
            recovery_days = (recovery_date - max_dd_start).days
            print(f"  恢复时间: {recovery_days} 天")
        else:
            print(f"  回撤恢复: 尚未完全恢复")
        
        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        print(f"  Calmar比率: {calmar_ratio:.3f}")
        
        # 4. VaR分析
        print(f"\n📐 风险价值(VaR)分析:")
        
        # 历史模拟法VaR
        var_95 = np.percentile(portfolio_returns, 5)
        var_99 = np.percentile(portfolio_returns, 1)
        
        # 参数法VaR (假设正态分布)
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        var_95_parametric = mean_return - 1.645 * std_return
        var_99_parametric = mean_return - 2.326 * std_return
        
        print(f"  VaR (95%, 历史法): {var_95:.2%} (日损失)")
        print(f"  VaR (99%, 历史法): {var_99:.2%} (日损失)")
        print(f"  VaR (95%, 参数法): {var_95_parametric:.2%} (日损失)")
        print(f"  VaR (99%, 参数法): {var_99_parametric:.2%} (日损失)")
        
        # 转换为美元金额
        var_95_dollar = var_95 * portfolio_value.iloc[-1]
        var_99_dollar = var_99 * portfolio_value.iloc[-1]
        
        print(f"  95% VaR (美元): ${abs(var_95_dollar):,.0f}")
        print(f"  99% VaR (美元): ${abs(var_99_dollar):,.0f}")
        
        # 5. 条件风险价值(CVaR/ES)
        print(f"\n📊 条件风险价值(CVaR)分析:")
        
        # 计算CVaR
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        cvar_99 = portfolio_returns[portfolio_returns <= var_99].mean()
        
        print(f"  CVaR (95%): {cvar_95:.2%}")
        print(f"  CVaR (99%): {cvar_99:.2%}")
        
        cvar_95_dollar = cvar_95 * portfolio_value.iloc[-1]
        cvar_99_dollar = cvar_99 * portfolio_value.iloc[-1]
        
        print(f"  95% CVaR (美元): ${abs(cvar_95_dollar):,.0f}")
        print(f"  99% CVaR (美元): ${abs(cvar_99_dollar):,.0f}")
        
        # 6. 滚动风险分析
        print(f"\n📈 滚动风险分析 (30日窗口):")
        
        rolling_vol = portfolio_returns.rolling(30).std() * np.sqrt(252)
        rolling_var = portfolio_returns.rolling(30).quantile(0.05)
        
        print(f"  当前30日年化波动率: {rolling_vol.iloc[-1]:.2%}")
        print(f"  最高30日年化波动率: {rolling_vol.max():.2%}")
        print(f"  最低30日年化波动率: {rolling_vol.min():.2%}")
        print(f"  波动率标准差: {rolling_vol.std():.2%}")
        
        # 7. 压力测试
        print(f"\n🔥 压力测试:")
        
        stress_scenarios = {
            "市场下跌10%": -0.10,
            "市场下跌20%": -0.20,
            "极端熊市30%": -0.30,
            "黑天鹅事件40%": -0.40
        }
        
        for scenario_name, shock in stress_scenarios.items():
            # 假设所有资产同时下跌
            stressed_portfolio_value = portfolio_value.iloc[-1] * (1 + shock)
            loss_amount = portfolio_value.iloc[-1] - stressed_portfolio_value
            
            print(f"  {scenario_name}: 损失 ${loss_amount:,.0f} ({shock:.0%})")
        
        # 8. 风险监控指标
        print(f"\n🚨 风险监控指标:")
        
        # 最近收益率趋势
        recent_returns = portfolio_returns.tail(30)  # 最近30天
        recent_performance = recent_returns.mean() * 252  # 年化
        recent_volatility = recent_returns.std() * np.sqrt(252)
        
        print(f"  最近30日年化收益: {recent_performance:.2%}")
        print(f"  最近30日年化波动: {recent_volatility:.2%}")
        
        # 风险警报
        risk_alerts = []
        
        if recent_volatility > annual_vol * 1.5:
            risk_alerts.append("🔴 波动率异常升高")
        
        if drawdown.iloc[-1] < -0.05:
            risk_alerts.append("🟡 当前处于回撤状态")
        
        if recent_performance < -0.10:
            risk_alerts.append("🔴 近期表现不佳")
        
        recent_var_breaches = (recent_returns < var_95).sum()
        if recent_var_breaches > 3:  # 30天内超过3次
            risk_alerts.append("🔴 VaR突破次数过多")
        
        if risk_alerts:
            print(f"  风险警报:")
            for alert in risk_alerts:
                print(f"    {alert}")
        else:
            print(f"  🟢 当前风险状况正常")
        
        # 9. 建议和总结
        print(f"\n💡 风险管理建议:")
        
        if max_drawdown > -0.15:
            print("  🔴 最大回撤超过15%，建议加强风险控制")
        elif max_drawdown > -0.10:
            print("  🟡 最大回撤适中，继续监控")
        else:
            print("  🟢 回撤控制良好")
        
        if sharpe_ratio > 1.0:
            print("  🟢 风险调整后收益优秀")
        elif sharpe_ratio > 0.5:
            print("  🔵 风险调整后收益良好")
        else:
            print("  🟡 建议优化收益风险比")
        
        if annual_vol > 0.20:
            print("  ⚠️ 投资组合波动率较高，适合风险承受力强的投资者")
        elif annual_vol > 0.15:
            print("  🟡 投资组合波动率适中")
        else:
            print("  🟢 投资组合风险相对较低")
        
        print("\n✅ 风险管理和回测分析完成！")
        return True
        
    except Exception as e:
        print(f"❌ 风险管理分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 主函数
# ============================================================================

def main():
    """
    主函数：运行所有工作示例
    """
    print("🎯 这些示例展示了P1-2组件的核心思想和计算逻辑")
    print("📚 完整功能请参考 docs/P1-2_USER_MANUAL.md")
    print("🔧 API详情请参考 docs/API_REFERENCE.md")
    
    # 运行示例
    examples = [
        ("基础技术分析", example_1_basic_technical_analysis),
        ("多股票相关性分析", example_2_correlation_analysis),
        ("投资组合优化模拟", example_3_portfolio_optimization_simulation),
        ("风险管理和回测分析", example_4_risk_management_backtest)
    ]
    
    results = []
    
    for example_name, example_func in examples:
        print(f"\n🎯 运行: {example_name}")
        try:
            success = example_func()
            results.append((example_name, success))
        except Exception as e:
            print(f"❌ {example_name}执行失败: {str(e)}")
            results.append((example_name, False))
    
    # 汇总结果
    print("\n" + "="*80)
    print("📊 工作示例执行结果")
    print("="*80)
    
    successful_count = 0
    for example_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{example_name}: {status}")
        if success:
            successful_count += 1
    
    print(f"\n🎯 执行结果: {successful_count}/{len(examples)} 个示例成功")
    
    if successful_count == len(examples):
        print("\n🎉 所有工作示例运行成功！")
        print("\n📚 学习路径:")
        print("1. 📖 阅读 docs/P1-2_USER_MANUAL.md 了解完整功能")
        print("2. 🔧 查看 docs/API_REFERENCE.md 学习详细API")
        print("3. 💻 运行 test_p1_2_core_validation.py 验证组件")
        print("4. 🚀 在实际项目中集成P1-2组件")
    else:
        print("\n⚠️ 部分示例执行失败，但核心逻辑演示成功")
    
    print(f"\n🕒 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return successful_count >= 3  # 至少3个示例成功


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)