"""
统一数据源架构测试

验证整合后的数据源功能和性能。
"""

import asyncio
import time
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入统一数据源
from .unified_manager import UnifiedDataManager
from .adapters import create_unified_data_sources
from .backtrader_integration import UnifiedBacktraderFeed, create_unified_feed
from . import DataType, DataFrequency


class UnifiedDataTestSuite:
    """统一数据源测试套件"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.test_config = {
            'yahoo_finance': {},
            'coingecko': {},
            'fred': {
                'api_key': None  # 使用demo模式
            },
            'websocket': {
                'enabled': False  # 暂时禁用WebSocket测试
            }
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 统一数据源架构测试")
        print("=" * 60)
        
        test_results = {}
        
        # 测试1: 数据源适配器
        print("\n1️⃣ 测试数据源适配器...")
        test_results['adapters'] = await self.test_data_source_adapters()
        
        # 测试2: 统一数据管理器
        print("\n2️⃣ 测试统一数据管理器...")
        test_results['manager'] = await self.test_unified_manager()
        
        # 测试3: Backtrader集成
        print("\n3️⃣ 测试Backtrader集成...")
        test_results['backtrader'] = await self.test_backtrader_integration()
        
        # 测试4: 性能测试
        print("\n4️⃣ 性能测试...")
        test_results['performance'] = await self.test_performance()
        
        # 汇总结果
        self.print_test_summary(test_results)
        
        return test_results
    
    async def test_data_source_adapters(self) -> Dict[str, bool]:
        """测试数据源适配器"""
        results = {}
        
        try:
            # 创建适配器
            data_sources = create_unified_data_sources(self.test_config)
            print(f"✅ 创建了 {len(data_sources)} 个数据源适配器")
            
            # 测试每个适配器
            for name, source in data_sources.items():
                try:
                    # 测试获取支持的符号
                    symbols = source.get_supported_symbols()
                    print(f"   {name}: 支持 {len(symbols)} 个符号")
                    
                    # 测试实时数据（使用安全的符号）
                    test_symbol = self._get_test_symbol(name)
                    if test_symbol:
                        real_time_data = source.get_real_time_price(test_symbol)
                        if real_time_data:
                            print(f"   {name}: 实时数据获取成功 - {test_symbol}")
                        else:
                            print(f"   {name}: 实时数据为空 - {test_symbol}")
                    
                    results[name] = True
                    
                except Exception as e:
                    print(f"   ❌ {name} 测试失败: {e}")
                    results[name] = False
                
                # 避免频率限制
                await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ 适配器测试失败: {e}")
            results['overall'] = False
        
        return results
    
    async def test_unified_manager(self) -> Dict[str, bool]:
        """测试统一数据管理器"""
        results = {}
        
        try:
            # 创建管理器
            manager = UnifiedDataManager(self.test_config)
            
            # 注册数据源
            data_sources = create_unified_data_sources(self.test_config)
            for name, source in data_sources.items():
                manager.register_data_source(name, source)
            
            print(f"✅ 统一管理器注册了 {len(data_sources)} 个数据源")
            
            # 测试健康检查
            health = manager.health_check()
            print(f"✅ 健康检查: {health['overall_status']}")
            
            for source_name, status in health['data_sources'].items():
                print(f"   {source_name}: {status['status']}")
            
            # 测试实时数据获取
            try:
                apple_data = await manager.get_real_time_data("AAPL", DataType.STOCK_PRICE)
                if apple_data:
                    print(f"✅ 获取AAPL实时数据: ${apple_data.price:.2f}")
                    results['real_time'] = True
                else:
                    print("⚠️ AAPL实时数据为空")
                    results['real_time'] = False
            except Exception as e:
                print(f"❌ 实时数据获取失败: {e}")
                results['real_time'] = False
            
            # 测试历史数据获取
            try:
                start_date = datetime.now() - timedelta(days=7)
                historical_data = await manager.get_historical_data(
                    "AAPL", DataType.STOCK_PRICE, DataFrequency.DAY_1, start_date
                )
                print(f"✅ 获取AAPL历史数据: {len(historical_data)} 条记录")
                results['historical'] = len(historical_data) > 0
            except Exception as e:
                print(f"❌ 历史数据获取失败: {e}")
                results['historical'] = False
            
            # 测试缓存功能
            cache_stats = manager.cache.get_stats()
            print(f"✅ 缓存统计: {cache_stats}")
            results['cache'] = True
            
            # 测试性能报告
            performance = manager.get_performance_report()
            print(f"✅ 性能报告生成成功")
            results['performance'] = True
            
        except Exception as e:
            print(f"❌ 统一管理器测试失败: {e}")
            results['overall'] = False
        
        return results
    
    async def test_backtrader_integration(self) -> Dict[str, bool]:
        """测试Backtrader集成"""
        results = {}
        
        try:
            # 创建统一数据源
            feed = create_unified_feed(
                symbol='AAPL',
                data_type='stock',
                frequency='1d',
                config=self.test_config
            )
            print("✅ 创建统一Backtrader数据源")
            results['creation'] = True
            
            # 测试启动和停止
            try:
                print("🚀 启动数据源...")
                feed.start()
                
                # 等待一些数据
                await asyncio.sleep(3)
                
                # 获取性能指标
                metrics = feed.get_performance_metrics()
                print(f"✅ 数据源性能: {metrics['data_count']} 个数据点")
                
                # 停止数据源
                feed.stop()
                print("⏹️ 数据源已停止")
                
                results['operation'] = True
                
            except Exception as e:
                print(f"❌ 数据源操作失败: {e}")
                results['operation'] = False
                
                # 确保清理
                try:
                    feed.stop()
                except:
                    pass
            
        except Exception as e:
            print(f"❌ Backtrader集成测试失败: {e}")
            results['overall'] = False
        
        return results
    
    async def test_performance(self) -> Dict[str, Any]:
        """性能测试"""
        results = {}
        
        try:
            print("⚡ 开始性能测试...")
            
            # 创建管理器
            manager = UnifiedDataManager(self.test_config)
            data_sources = create_unified_data_sources(self.test_config)
            
            for name, source in data_sources.items():
                manager.register_data_source(name, source)
            
            # 测试并发请求性能
            symbols = ['AAPL', 'MSFT', 'GOOGL']
            start_time = time.time()
            
            tasks = []
            for symbol in symbols:
                task = manager.get_real_time_data(symbol, DataType.STOCK_PRICE)
                tasks.append(task)
            
            results_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = time.time() - start_time
            successful = sum(1 for r in results_data if not isinstance(r, Exception))
            
            print(f"✅ 并发性能测试:")
            print(f"   请求数量: {len(symbols)}")
            print(f"   成功数量: {successful}")
            print(f"   总耗时: {elapsed:.2f}秒")
            print(f"   平均延迟: {elapsed/len(symbols)*1000:.1f}ms")
            
            results['concurrent_requests'] = successful
            results['average_latency_ms'] = elapsed / len(symbols) * 1000
            results['success_rate'] = successful / len(symbols)
            
            # 获取性能报告
            performance_report = manager.get_performance_report()
            results['performance_report'] = performance_report
            
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            results['error'] = str(e)
        
        return results
    
    def _get_test_symbol(self, source_name: str) -> str:
        """获取测试用符号"""
        symbol_map = {
            'yahoo': 'AAPL',
            'coingecko': 'bitcoin',
            'fred': 'FEDFUNDS'
        }
        return symbol_map.get(source_name, 'AAPL')
    
    def print_test_summary(self, test_results: Dict[str, Any]):
        """打印测试汇总"""
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in test_results.items():
            print(f"\n📂 {category.upper()}:")
            
            if isinstance(results, dict):
                for test_name, result in results.items():
                    total_tests += 1
                    if result is True:
                        passed_tests += 1
                        print(f"  ✅ {test_name}: PASSED")
                    elif result is False:
                        print(f"  ❌ {test_name}: FAILED")
                    else:
                        print(f"  ℹ️ {test_name}: {result}")
            else:
                total_tests += 1
                if results:
                    passed_tests += 1
                    print(f"  ✅ {category}: PASSED")
                else:
                    print(f"  ❌ {category}: FAILED")
        
        # 总体统计
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 总体结果:")
        print(f"  测试总数: {total_tests}")
        print(f"  通过数量: {passed_tests}")
        print(f"  成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("  🎉 整合成功！")
        elif success_rate >= 60:
            print("  ⚠️ 部分成功，需要优化")
        else:
            print("  ❌ 整合失败，需要修复")


# 单独测试函数
async def test_data_compatibility():
    """测试数据兼容性"""
    print("🔄 测试新旧数据源兼容性...")
    
    try:
        # 测试新架构
        from .unified_manager import UnifiedDataManager
        from .adapters import create_unified_data_sources
        
        manager = UnifiedDataManager()
        sources = create_unified_data_sources()
        
        for name, source in sources.items():
            manager.register_data_source(name, source)
        
        # 获取数据
        data = await manager.get_real_time_data("AAPL", DataType.STOCK_PRICE)
        
        if data:
            print(f"✅ 新架构数据获取成功: {data.symbol} ${data.price}")
            return True
        else:
            print("❌ 新架构数据获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        return False


async def quick_validation():
    """快速验证"""
    print("⚡ 快速验证统一数据源...")
    
    try:
        # 创建简单的测试
        from .backtrader_integration import create_unified_feed
        
        feed = create_unified_feed(symbol='AAPL', data_type='stock')
        print("✅ 统一数据源创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 快速验证失败: {e}")
        return False


# 主测试入口
async def main():
    """主测试函数"""
    print("🚀 开始统一数据源架构测试")
    
    # 快速验证
    if not await quick_validation():
        print("❌ 快速验证失败，退出测试")
        return
    
    # 兼容性测试
    if not await test_data_compatibility():
        print("⚠️ 兼容性测试失败，但继续完整测试")
    
    # 完整测试套件
    test_suite = UnifiedDataTestSuite()
    results = await test_suite.run_all_tests()
    
    return results


if __name__ == "__main__":
    # 运行测试
    try:
        results = asyncio.run(main())
        print("\n🏁 测试完成")
        
        # 设置退出码
        if results:
            # 计算成功率
            total_success = 0
            total_tests = 0
            
            for category_results in results.values():
                if isinstance(category_results, dict):
                    for result in category_results.values():
                        if isinstance(result, bool):
                            total_tests += 1
                            if result:
                                total_success += 1
            
            success_rate = (total_success / total_tests) if total_tests > 0 else 0
            
            if success_rate >= 0.8:
                sys.exit(0)  # 成功
            else:
                sys.exit(1)  # 失败
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        sys.exit(1)