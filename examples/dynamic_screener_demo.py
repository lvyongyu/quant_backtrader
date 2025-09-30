#!/usr/bin/env python3
"""
动态股票筛选器演示
Dynamic Stock Screener Demo

展示如何使用不同的数据源进行股票筛选：
- 标普500成分股
- 纳斯达克100成分股
- 中概股ADR
- 加密货币相关股票
- 综合股票池
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from examples.stock_screener import StockScreener, run_stock_screening, quick_screen
import time


def demo_different_sources():
    """演示不同数据源的股票筛选"""
    
    print("🎯 动态股票筛选器演示")
    print("🌟 支持多种外部数据源，不再使用硬编码股票列表")
    print("=" * 100)
    
    # 可用的数据源
    data_sources = {
        'sp500': {'name': 'S&P 500成分股', 'max_stocks': 500, 'description': '美国大盘蓝筹股'},
        'nasdaq100': {'name': 'NASDAQ 100', 'max_stocks': 100, 'description': '科技成长股为主'},
        'chinese': {'name': '中概股ADR', 'max_stocks': 50, 'description': '在美上市中国股票'},
        'crypto': {'name': '加密货币相关', 'max_stocks': 30, 'description': '比特币矿企和区块链'},
        'etfs': {'name': '热门ETF', 'max_stocks': 50, 'description': '指数基金和行业ETF'},
        'comprehensive': {'name': '综合股票池', 'max_stocks': 300, 'description': '包含多种资产类别'}
    }
    
    print("📋 可用数据源:")
    for source, info in data_sources.items():
        print(f"   • {source}: {info['name']} - {info['description']}")
    
    print("\n" + "="*100)
    
    # 演示每个数据源
    results = {}
    
    for source, info in data_sources.items():
        print(f"\n🔍 正在演示: {info['name']} ({source})")
        print(f"📊 描述: {info['description']}")
        print("-" * 80)
        
        try:
            start_time = time.time()
            
            # 运行筛选
            top3 = run_stock_screening(
                source=source, 
                max_stocks=info['max_stocks']
            )
            
            elapsed_time = time.time() - start_time
            results[source] = {
                'top3': top3,
                'time': elapsed_time,
                'success': True
            }
            
            print(f"⏱️ 用时: {elapsed_time:.1f}秒")
            
            if top3 and len(top3) >= 3:
                print(f"🏆 TOP3结果:")
                for i, stock in enumerate(top3, 1):
                    print(f"   {i}. {stock['symbol']}: {stock['total_score']:.1f}分")
            
        except Exception as e:
            print(f"❌ 筛选失败: {e}")
            results[source] = {
                'top3': [],
                'time': 0,
                'success': False,
                'error': str(e)
            }
        
        print("\n" + "="*100)
        time.sleep(2)  # 暂停2秒，避免请求过于频繁
    
    # 总结报告
    print("\n📊 演示总结报告")
    print("=" * 100)
    
    successful_sources = [s for s, r in results.items() if r['success']]
    failed_sources = [s for s, r in results.items() if not r['success']]
    
    print(f"✅ 成功的数据源: {len(successful_sources)}/{len(data_sources)}")
    print(f"❌ 失败的数据源: {len(failed_sources)}/{len(data_sources)}")
    
    if successful_sources:
        print(f"\n🎯 各数据源TOP1股票对比:")
        for source in successful_sources:
            result = results[source]
            if result['top3']:
                top1 = result['top3'][0]
                source_name = data_sources[source]['name']
                print(f"   • {source_name}: {top1['symbol']} ({top1['total_score']:.1f}分)")
    
    if failed_sources:
        print(f"\n⚠️ 失败的数据源:")
        for source in failed_sources:
            source_name = data_sources[source]['name']
            error = results[source].get('error', '未知错误')
            print(f"   • {source_name}: {error}")
    
    print(f"\n🎉 演示完成! 动态股票池功能已成功替代硬编码列表")
    return results


def demo_custom_screening():
    """演示自定义股票筛选"""
    
    print("\n" + "🌟"*50)
    print("🎯 自定义股票筛选演示")
    print("🔍 筛选用户指定的股票列表")
    print("=" * 100)
    
    # 自定义股票列表示例
    custom_lists = {
        'faang': {
            'name': 'FAANG+科技巨头',
            'symbols': ['AAPL', 'AMZN', 'NFLX', 'GOOGL', 'META', 'MSFT', 'TSLA', 'NVDA'],
            'description': '美国科技巨头股票'
        },
        'chinese_giants': {
            'name': '中国互联网巨头',
            'symbols': ['BABA', 'JD', 'PDD', 'BIDU', 'NTES', 'TME'],
            'description': '主要中概股公司'
        },
        'ev_stocks': {
            'name': '电动车股票',
            'symbols': ['TSLA', 'NIO', 'XPEV', 'LI', 'RIVN', 'LCID', 'F', 'GM'],
            'description': '电动车产业链股票'
        },
        'crypto_miners': {
            'name': '比特币矿企',
            'symbols': ['MARA', 'RIOT', 'COIN', 'MSTR', 'BTBT', 'SOS'],
            'description': '加密货币挖矿和交易股票'
        }
    }
    
    custom_results = {}
    
    for category, info in custom_lists.items():
        print(f"\n🔍 筛选类别: {info['name']}")
        print(f"📊 描述: {info['description']}")
        print(f"📋 股票列表: {', '.join(info['symbols'])}")
        print("-" * 80)
        
        try:
            start_time = time.time()
            
            # 使用quick_screen函数进行快速筛选
            top3 = quick_screen(info['symbols'])
            
            elapsed_time = time.time() - start_time
            custom_results[category] = {
                'top3': top3,
                'time': elapsed_time,
                'success': True
            }
            
            print(f"⏱️ 用时: {elapsed_time:.1f}秒")
            
            if top3:
                print(f"🏆 TOP{min(3, len(top3))}结果:")
                for i, stock in enumerate(top3[:3], 1):
                    print(f"   {i}. {stock['symbol']}: {stock['total_score']:.1f}分 "
                          f"(价格: ${stock['current_price']})")
        
        except Exception as e:
            print(f"❌ 筛选失败: {e}")
            custom_results[category] = {
                'success': False,
                'error': str(e)
            }
        
        time.sleep(1)  # 短暂暂停
    
    print(f"\n📊 自定义筛选总结:")
    for category, result in custom_results.items():
        category_name = custom_lists[category]['name']
        if result['success'] and result['top3']:
            winner = result['top3'][0]
            print(f"   • {category_name}: 🥇{winner['symbol']} ({winner['total_score']:.1f}分)")
        else:
            print(f"   • {category_name}: ❌ 筛选失败")


def main():
    """主演示程序"""
    
    print("🚀 启动动态股票筛选器演示程序")
    print("🎯 展示从硬编码列表到动态数据源的升级")
    print("\n")
    
    try:
        # 演示1: 不同数据源
        demo_results = demo_different_sources()
        
        # 演示2: 自定义筛选
        demo_custom_screening()
        
        print("\n" + "🎉"*50)
        print("✅ 所有演示完成!")
        print("\n💡 主要改进:")
        print("   1. ❌ 不再使用硬编码的95只股票列表")
        print("   2. ✅ 支持动态获取S&P 500、NASDAQ 100等指数成分股")  
        print("   3. ✅ 支持多种数据源：美股、中概股、ETF、加密货币相关")
        print("   4. ✅ 实现本地缓存，提高性能和稳定性")
        print("   5. ✅ 可扩展到数千只股票的大规模筛选")
        
        print("\n🌟 数据源优势:")
        print("   • 实时更新: 指数成分股变化时自动更新")
        print("   • 覆盖面广: 从100只扩展到1000+只股票")
        print("   • 分类明确: 可按行业、地区、资产类别筛选")
        print("   • 性能优化: 缓存机制减少网络请求")
        
    except KeyboardInterrupt:
        print("\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()