#!/usr/bin/env python3
"""
快速股票筛选脚本
Quick Stock Screening Script

一行命令搞定所有筛选！
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# 导入函数
from examples.stock_screener import run_stock_screening

# 快捷函数
def sp500(max_stocks=500):
    """S&P 500筛选"""
    return run_stock_screening('sp500', max_stocks)

def nasdaq(max_stocks=100):
    """NASDAQ 100筛选"""
    return run_stock_screening('nasdaq100', max_stocks)

def chinese(max_stocks=50):
    """中概股筛选"""
    return run_stock_screening('chinese', max_stocks)

def crypto(max_stocks=30):
    """加密货币相关筛选"""
    return run_stock_screening('crypto', max_stocks)

def etf(max_stocks=50):
    """ETF筛选"""
    return run_stock_screening('etfs', max_stocks)

def all_stocks(max_stocks=300):
    """综合筛选"""
    return run_stock_screening('comprehensive', max_stocks)

def quick_screen(symbols, mode='comprehensive'):
    """
    快速筛选指定股票
    
    Args:
        symbols: 股票代码列表
        mode: 分析模式 ('technical', 'fundamental', 'comprehensive')
    
    Returns:
        筛选结果
    """
    from examples.stock_screener import StockScreener
    
    # 根据模式配置分析器
    enable_fundamental = mode in ['fundamental', 'comprehensive']
    enable_market_env = mode in ['comprehensive']
    
    screener = StockScreener(
        enable_fundamental=enable_fundamental,
        enable_market_env=enable_market_env
    )
    
    results = screener.screen_stocks(symbols)
    if results:
        top3 = screener.get_top3()
        return top3
    else:
        return []

# 如果直接运行，显示示例
if __name__ == "__main__":
    print("🎯 快速股票筛选脚本")
    print("=" * 40)
    print("在Python中直接调用:")
    print()
    print("  from quick_screen import *")
    print()
    print("  # 然后使用:")
    print("  sp500()          # S&P 500筛选")
    print("  nasdaq()         # NASDAQ筛选")
    print("  chinese()        # 中概股筛选")
    print("  crypto()         # 加密货币筛选")
    print("  etf()            # ETF筛选")
    print("  all_stocks()     # 综合筛选")
    print()
    print("  # 指定数量:")
    print("  sp500(200)       # 筛选200只S&P 500")
    print("  nasdaq(50)       # 筛选50只NASDAQ")