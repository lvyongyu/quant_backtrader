#!/usr/bin/env python3
"""
统一数据源架构验证测试
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def comprehensive_test():
    try:
        print('🧪 统一数据源架构验证测试')
        print('=' * 50)
        
        # 1. 测试数据结构
        print('\n1️⃣ 测试数据结构...')
        from src.unified_data import MarketData, StockData, CryptoData, EconomicData
        from src.unified_data import DataType, DataFrequency, SourceType
        
        # 创建测试数据
        from datetime import datetime
        stock_data = StockData(
            symbol='AAPL',
            timestamp=datetime.now(),
            data_type=DataType.STOCK_PRICE,
            frequency=DataFrequency.DAY_1,
            price=150.0,
            volume=1000000
        )
        print(f'✅ 股票数据: {stock_data.symbol} ${stock_data.price}')
        
        crypto_data = CryptoData(
            symbol='BTC',
            timestamp=datetime.now(),
            data_type=DataType.CRYPTO_PRICE,
            frequency=DataFrequency.DAY_1,
            price=50000.0,
            market_cap=1000000000
        )
        print(f'✅ 加密货币数据: {crypto_data.symbol} ${crypto_data.price:,.0f}')
        
        # 2. 测试适配器
        print('\n2️⃣ 测试数据源适配器...')
        from src.unified_data.adapters import create_unified_data_sources
        
        config = {
            'yahoo_finance': {},
            'coingecko': {},
            'fred': {'api_key': None}
        }
        
        sources = create_unified_data_sources(config)
        print(f'✅ 创建了 {len(sources)} 个数据源适配器')
        
        for name, source in sources.items():
            print(f'   {name}: {type(source).__name__}')
        
        # 3. 测试统一管理器
        print('\n3️⃣ 测试统一数据管理器...')
        from src.unified_data.unified_manager import UnifiedDataManager
        
        manager = UnifiedDataManager(config)
        
        # 注册数据源
        for name, source in sources.items():
            manager.register_data_source(name, source)
        
        print(f'✅ 注册了 {len(sources)} 个数据源')
        
        # 健康检查
        health = manager.health_check()
        print(f'✅ 系统健康状态: {health["overall_status"]}')
        
        for source_name, status in health['data_sources'].items():
            print(f'   {source_name}: {status["status"]}')
        
        # 4. 测试Backtrader集成
        print('\n4️⃣ 测试Backtrader集成...')
        from src.unified_data.backtrader_integration import create_unified_feed
        
        feed = create_unified_feed(
            symbol='AAPL',
            data_type='stock',
            frequency='1d',
            config=config
        )
        print(f'✅ Backtrader数据源: {feed.p.symbol}')
        
        # 5. 测试性能
        print('\n5️⃣ 测试缓存性能...')
        cache_stats = manager.cache.get_stats()
        print(f'✅ 缓存统计: {cache_stats}')
        
        performance_report = manager.get_performance_report()
        print(f'✅ 性能报告生成成功')
        
        print('\n🎉 所有测试通过！统一数据源架构工作正常')
        return True
        
    except Exception as e:
        print(f'\n❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(comprehensive_test())
    print(f'\n📊 测试结果: {"PASSED" if result else "FAILED"}')
    sys.exit(0 if result else 1)