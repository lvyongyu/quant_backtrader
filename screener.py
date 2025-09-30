#!/usr/bin/env python3
"""
简化股票筛选命令工具
Simplified Stock Screening Commands

使用方法:
python3 screener.py sp500          # S&P 500筛选
python3 screener.py nasdaq         # NASDAQ 100筛选  
python3 screener.py chinese        # 中概股筛选
python3 screener.py crypto         # 加密货币相关筛选
python3 screener.py etf            # ETF筛选
python3 screener.py all            # 综合筛选
python3 screener.py custom         # 自定义筛选
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

# 导入函数
from examples.stock_screener import run_stock_screening


def show_help():
    """显示帮助信息"""
    print("🎯 简化股票筛选命令")
    print("=" * 50)
    print("使用方法:")
    print("  python3 screener.py <数据源> [股票数量]")
    print()
    print("可用数据源:")
    print("  sp500     - S&P 500成分股 (~500只)")
    print("  nasdaq    - NASDAQ 100成分股 (~100只)")
    print("  chinese   - 中概股ADR (~40只)")
    print("  crypto    - 加密货币相关股票 (~20只)")
    print("  etf       - 热门ETF (~50只)")
    print("  all       - 综合股票池 (1000+只)")
    print("  custom    - 自定义股票池")
    print()
    print("示例:")
    print("  python3 screener.py sp500        # 筛选S&P 500")
    print("  python3 screener.py nasdaq 50    # 筛选NASDAQ前50只")
    print("  python3 screener.py chinese      # 筛选中概股")
    print("  python3 screener.py all 300      # 综合筛选300只")


def main():
    """主函数"""
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    # 显示帮助
    if command in ['help', '-h', '--help']:
        show_help()
        return
    
    # 获取股票数量限制
    max_stocks = None
    if len(sys.argv) >= 3:
        try:
            max_stocks = int(sys.argv[2])
        except ValueError:
            print(f"❌ 无效的股票数量: {sys.argv[2]}")
            return
    
    # 命令映射
    source_map = {
        'sp500': 'sp500',
        's&p': 'sp500',
        'spx': 'sp500',
        
        'nasdaq': 'nasdaq100',
        'nasdaq100': 'nasdaq100',
        'ndx': 'nasdaq100',
        'tech': 'nasdaq100',
        
        'chinese': 'chinese',
        'china': 'chinese',
        'adr': 'chinese',
        'cn': 'chinese',
        
        'crypto': 'crypto',
        'bitcoin': 'crypto',
        'btc': 'crypto',
        
        'etf': 'etfs',
        'etfs': 'etfs',
        'fund': 'etfs',
        
        'all': 'comprehensive',
        'comprehensive': 'comprehensive',
        'total': 'comprehensive',
        
        'custom': 'custom'
    }
    
    # 默认股票数量设置
    default_limits = {
        'sp500': 500,
        'nasdaq100': 100,
        'chinese': 50,
        'crypto': 30,
        'etfs': 50,
        'comprehensive': 300,
        'custom': 200
    }
    
    if command not in source_map:
        print(f"❌ 未知命令: {command}")
        print("💡 使用 'python3 screener.py help' 查看帮助")
        return
    
    source = source_map[command]
    
    # 如果没有指定数量，使用默认值
    if max_stocks is None:
        max_stocks = default_limits.get(source, 100)
    
    print(f"🚀 启动筛选: {source} (最多{max_stocks}只股票)")
    print("=" * 60)
    
    try:
        # 运行筛选
        top3 = run_stock_screening(source=source, max_stocks=max_stocks)
        
        if top3:
            print(f"\n✅ 筛选完成! TOP3结果:")
            for i, stock in enumerate(top3, 1):
                print(f"  {i}. {stock['symbol']}: {stock['total_score']:.1f}分")
        else:
            print("❌ 筛选失败，未获得有效结果")
            
    except KeyboardInterrupt:
        print("\n⏹️ 筛选被用户中断")
    except Exception as e:
        print(f"❌ 筛选出错: {e}")


if __name__ == "__main__":
    main()