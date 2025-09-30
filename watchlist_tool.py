#!/usr/bin/env python3
"""
自选股池管理工具
Watchlist Management Tool

快速管理和分析自选股池的独立工具
"""

import os
import sys

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.stock_screener import StockScreener, run_stock_screening


def main():
    """自选股池管理主程序"""
    
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    screener = StockScreener()
    
    if command == 'show' or command == 'list':
        # 显示自选股池
        screener.show_watchlist()
        
    elif command == 'add':
        # 手动添加股票到自选股池
        if len(sys.argv) < 3:
            print("❌ 请指定要添加的股票代码")
            print("💡 用法: python watchlist_tool.py add AAPL")
            return
        
        symbol = sys.argv[2].upper()
        print(f"📊 分析 {symbol} 并添加到自选股池...")
        
        # 分析单只股票
        results, _ = run_stock_screening('sp500', max_stocks=500)
        target_stock = None
        
        for stock in screener.results:
            if stock['symbol'] == symbol:
                target_stock = stock
                break
        
        if target_stock:
            screener.add_to_watchlist(
                symbol, 
                target_stock['total_score'], 
                target_stock.get('price')
            )
            print(f"✅ {symbol} 已添加到自选股池 (得分: {target_stock['total_score']:.1f})")
        else:
            print(f"❌ 未找到股票 {symbol} 或分析失败")
            
    elif command == 'remove' or command == 'rm':
        # 移除股票
        if len(sys.argv) < 3:
            print("❌ 请指定要移除的股票代码")
            print("💡 用法: python watchlist_tool.py remove AAPL")
            return
        
        symbol = sys.argv[2].upper()
        screener.remove_from_watchlist(symbol)
        
    elif command == 'clear':
        # 清空自选股池
        watchlist = screener.load_watchlist()
        watchlist["stocks"] = {}
        screener.save_watchlist(watchlist)
        print("🗑️ 自选股池已清空")
        
    elif command == 'analyze':
        # 分析自选股池
        watchlist_symbols = screener.get_watchlist_symbols()
        if not watchlist_symbols:
            print("📝 自选股池为空，请先添加一些股票")
            return
        
        print("🔍 分析自选股池中的股票...")
        results, _ = run_stock_screening('watchlist')
        
        if results:
            print(f"\n✅ 自选股分析完成!")
            print(f"📊 TOP股票排名:")
            for i, stock in enumerate(results, 1):
                print(f"  {i}. {stock['symbol']}: {stock['total_score']:.1f}分")
        
    elif command == 'stats':
        # 显示自选股池统计信息
        show_stats(screener)
        
    else:
        print(f"❌ 未知命令: {command}")
        print_help()


def show_stats(screener):
    """显示自选股池统计信息"""
    watchlist = screener.load_watchlist()
    stocks = watchlist.get("stocks", {})
    
    if not stocks:
        print("📝 自选股池为空")
        return
    
    print(f"\n📊 自选股池统计")
    print("=" * 40)
    
    scores = [data.get("last_score", 0) for data in stocks.values()]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    
    print(f"📈 股票总数: {len(stocks)}只")
    print(f"📊 平均得分: {avg_score:.1f}")
    print(f"🏆 最高得分: {max_score:.1f}")
    print(f"📉 最低得分: {min_score:.1f}")
    
    # 按行业分类统计
    industries = {}
    for data in stocks.values():
        # 这里可以扩展获取行业信息
        pass
    
    created_at = watchlist.get("created_at", "未知")[:10]
    last_updated = watchlist.get("last_updated", "未知")[:10]
    
    print(f"📅 创建时间: {created_at}")
    print(f"🔄 更新时间: {last_updated}")


def print_help():
    """显示帮助信息"""
    print("📝 自选股池管理工具")
    print("=" * 40)
    print("📊 查看操作:")
    print("  python watchlist_tool.py show     - 显示自选股池")
    print("  python watchlist_tool.py list     - 显示自选股池")
    print("  python watchlist_tool.py stats    - 显示统计信息")
    print("")
    print("✏️ 管理操作:")
    print("  python watchlist_tool.py add AAPL    - 添加股票")
    print("  python watchlist_tool.py remove AAPL - 移除股票")
    print("  python watchlist_tool.py rm AAPL     - 移除股票")
    print("  python watchlist_tool.py clear       - 清空股票池")
    print("")
    print("🔍 分析操作:")
    print("  python watchlist_tool.py analyze  - 分析自选股池")
    print("")
    print("💡 提示: 也可以通过主筛选器添加股票:")
    print("  python examples/stock_screener.py sp500 10")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已中断")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        print("💡 请检查股票代码是否正确")
