#!/usr/bin/env python3
"""
智能股票分析系统统一入口
Stock Analysis System Unified Entry Point

提供选股筛选、自选股管理、单股分析和投资组合管理功能
"""

import os
import sys
import argparse
from datetime import datetime

def print_banner():
    """打印系统横幅"""
    print("============================================================")
    print("🚀 智能股票分析系统 v3.0")
    print("============================================================")
    print("📊 核心功能:")
    print("   1. 🔍 选股筛选 - 四维度智能筛选优质股票")
    print("   2. 📋 自选股池 - 管理和分析个人股票池")
    print("   3. 📈 单股分析 - 深度分析指定股票")
    print("   4. 💼 投资组合 - 智能自动交易管理")
    print("============================================================")

def print_help():
    """打印帮助信息"""
    print("\\n🎯 智能股票分析系统 - 使用指南")
    print("=" * 60)
    
    print("\\n🔍 选股筛选:")
    print("   python3 main.py screen sp500 [数量]     # 筛选标普500")
    print("   python3 main.py screen nasdaq100 [数量] # 筛选纳斯达克100")
    print("   python3 main.py screen chinese [数量]   # 筛选中概股")
    
    print("\\n📋 自选股池管理:")
    print("   python3 main.py watchlist show          # 显示自选股池")
    print("   python3 main.py watchlist analyze       # 分析自选股池")
    print("   python3 main.py watchlist add AAPL      # 添加股票")
    print("   python3 main.py watchlist remove AAPL   # 移除股票")
    print("   python3 main.py watchlist clear         # 清空股池")
    
    print("\\n📈 单股分析:")
    print("   python3 main.py analyze AAPL            # 分析苹果股票")
    print("   python3 main.py analyze TSLA            # 分析特斯拉股票")
    
    print("\\n💼 投资组合管理:")
    print("   python3 main.py portfolio status        # 查看投资组合")
    print("   python3 main.py portfolio simulate      # 模拟自动交易")
    print("   python3 main.py portfolio trade         # 执行实际交易")
    print("   python3 main.py portfolio history       # 交易历史")
    
    print("\\n💡 使用示例:")
    print("   python3 main.py screen sp500 10         # 筛选SP500前10只股票")
    print("   python3 main.py analyze HWM             # 分析HWM股票")
    print("   python3 main.py watchlist analyze       # 分析我的自选股")
    print("   python3 main.py portfolio simulate      # 模拟自动交易")
    print("=" * 60)

def run_stock_screener(market, count=5):
    """运行股票筛选器"""
    print(f"🔍 正在筛选 {market.upper()} 股票 (TOP {count})...")
    
    # 导入并运行股票筛选器
    script_path = os.path.join(os.path.dirname(__file__), 'examples', 'stock_screener.py')
    cmd = f"python3 {script_path} {market} {count}"
    os.system(cmd)

def run_watchlist_manager(action, symbol=None):
    """运行自选股池管理"""
    script_path = os.path.join(os.path.dirname(__file__), 'watchlist_tool.py')
    
    if action == 'show':
        print("📋 显示自选股池...")
        cmd = f"python3 {script_path} show"
    elif action == 'analyze':
        print("📊 分析自选股池...")
        cmd = f"python3 {script_path} analyze"
    elif action == 'add' and symbol:
        print(f"➕ 添加 {symbol} 到自选股池...")
        cmd = f"python3 {script_path} add {symbol}"
    elif action == 'remove' and symbol:
        print(f"➖ 从自选股池移除 {symbol}...")
        cmd = f"python3 {script_path} remove {symbol}"
    elif action == 'clear':
        print("🗑️ 清空自选股池...")
        cmd = f"python3 {script_path} clear"
    else:
        print("❌ 自选股操作参数错误")
        return
    
    os.system(cmd)

def run_portfolio_manager(action, dry_run=False):
    """运行投资组合管理"""
    script_path = os.path.join(os.path.dirname(__file__), 'portfolio_manager.py')
    
    if action == 'status':
        print("💼 查看投资组合状态...")
        cmd = f"python3 {script_path} status"
    elif action == 'simulate':
        print("🔍 模拟自动交易...")
        cmd = f"python3 {script_path} simulate"
    elif action == 'trade':
        if dry_run:
            print("🔍 模拟执行交易...")
            cmd = f"python3 {script_path} trade --dry-run"
        else:
            print("⚡ 执行实际交易...")
            cmd = f"python3 {script_path} trade"
    elif action == 'history':
        print("📈 查看交易历史...")
        cmd = f"python3 {script_path} history"
    elif action == 'reset':
        print("🗑️ 重置投资组合...")
        cmd = f"python3 {script_path} reset"
    else:
        print("❌ 投资组合操作参数错误")
        return
    
    os.system(cmd)

def run_single_stock_analysis(symbol):
    """运行单只股票分析"""
    print(f"📈 正在分析 {symbol.upper()} 股票...")
    
    # 使用通用股票分析器
    script_path = os.path.join(os.path.dirname(__file__), 'stock_analyzer.py')
    cmd = f"python3 {script_path} {symbol.upper()}"
    os.system(cmd)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能股票分析系统')
    subparsers = parser.add_subparsers(dest='command', help='功能命令')
    
    # 选股筛选命令
    screen_parser = subparsers.add_parser('screen', help='股票筛选')
    screen_parser.add_argument('market', choices=['sp500', 'nasdaq100', 'chinese'], 
                              help='市场类型')
    screen_parser.add_argument('count', type=int, nargs='?', default=5, 
                              help='筛选数量 (默认5)')
    
    # 自选股管理命令
    watchlist_parser = subparsers.add_parser('watchlist', help='自选股池管理')
    watchlist_parser.add_argument('action', 
                                 choices=['show', 'analyze', 'add', 'remove', 'clear'],
                                 help='操作类型')
    watchlist_parser.add_argument('symbol', nargs='?', help='股票代码 (add/remove时需要)')
    
    # 单股分析命令
    analyze_parser = subparsers.add_parser('analyze', help='单只股票分析')
    analyze_parser.add_argument('symbol', help='股票代码')
    
    # 投资组合管理命令
    portfolio_parser = subparsers.add_parser('portfolio', help='投资组合管理')
    portfolio_parser.add_argument('action', 
                                 choices=['status', 'simulate', 'trade', 'history', 'reset'],
                                 help='操作类型')
    portfolio_parser.add_argument('--dry-run', '-d', action='store_true',
                                 help='模拟执行（仅适用于trade）')
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        print_help()
        return
    
    print_banner()
    print(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        if args.command == 'screen':
            run_stock_screener(args.market, args.count)
        elif args.command == 'watchlist':
            if args.action in ['add', 'remove'] and not args.symbol:
                print(f"❌ {args.action} 操作需要提供股票代码")
                return
            run_watchlist_manager(args.action, args.symbol)
        elif args.command == 'analyze':
            run_single_stock_analysis(args.symbol)
        elif args.command == 'portfolio':
            dry_run = getattr(args, 'dry_run', False)
            run_portfolio_manager(args.action, dry_run)
    except KeyboardInterrupt:
        print("\\n\\n❌ 用户中断操作")
    except Exception as e:
        print(f"\\n❌ 执行出错: {e}")

if __name__ == "__main__":
    main()