#!/usr/bin/env python3
"""
实时数据源演示脚本

演示P0阶段开发的实时数据源功能，包括数据获取、质量监控和性能测试。
"""

import time
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_realtime_feed():
    """演示实时数据源"""
    print("🚀 实时数据源演示")
    print("=" * 50)
    
    try:
        from src.data.realtime_feed import RealTimeDataFeed, MarketData
        
        def data_handler(data: MarketData):
            """数据处理回调"""
            print(f"[{data.timestamp.strftime('%H:%M:%S')}] "
                  f"{data.symbol}: ${data.price:.2f} "
                  f"vol:{data.volume} (延迟: {data.latency_ms:.1f}ms)")
        
        # 创建实时数据源
        feed = RealTimeDataFeed(
            symbols=['AAPL'],
            data_callback=data_handler,
            update_interval_ms=1000  # 1秒更新
        )
        
        print("📊 启动实时数据流...")
        feed.start()
        
        # 运行30秒
        for i in range(30):
            time.sleep(1)
            if i % 10 == 9:
                # 每10秒显示质量报告
                report = feed.get_quality_report()
                print(f"\\n📈 质量报告: "
                      f"延迟={report.get('avg_latency_ms', 0):.1f}ms, "
                      f"频率={report.get('data_rate_hz', 0):.1f}Hz, "
                      f"评分={report.get('quality_score', 0):.1f}%\\n")
        
        print("\\n🛑 停止数据流...")
        feed.stop()
        
        # 最终报告
        final_report = feed.get_quality_report()
        print(f"\\n📋 最终质量报告:")
        print(f"  - 平均延迟: {final_report.get('avg_latency_ms', 0):.1f}ms")
        print(f"  - 数据频率: {final_report.get('data_rate_hz', 0):.1f}Hz")
        print(f"  - 质量评分: {final_report.get('quality_score', 0):.1f}%")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("💡 这是正常的，因为某些依赖包可能未安装")
        return False

def demo_backtrader_integration():
    """演示Backtrader集成"""
    print("\\n🔗 Backtrader集成演示")
    print("=" * 50)
    
    try:
        from src.data.bt_realtime_feed import BacktraderRealTimeFeed
        
        # 创建Backtrader实时数据源
        feed = BacktraderRealTimeFeed()
        feed.p.symbol = 'AAPL'
        feed.p.update_interval_ms = 500  # 500ms更新
        
        print(f"📊 监控股票: {feed.p.symbol}")
        print("💡 启动数据源...")
        
        feed.start()
        
        # 运行20秒
        print("⏱️ 运行20秒数据收集...")
        time.sleep(20)
        
        feed.stop()
        
        # 显示性能指标
        metrics = feed.get_performance_metrics()
        print(f"\\n📈 性能指标:")
        print(f"  - 数据点数: {metrics.get('data_count', 0)}")
        print(f"  - 数据频率: {metrics.get('data_rate_per_second', 0):.1f} 点/秒")
        print(f"  - 质量警告: {metrics.get('quality_warnings', 0)} 次")
        print(f"  - 平均延迟: {metrics.get('avg_latency_ms', 0):.1f}ms")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def demo_performance_test():
    """演示性能测试"""
    print("\\n🧪 性能测试演示")
    print("=" * 50)
    
    try:
        from src.data.performance_tester import PerformanceTester
        from src.data.bt_realtime_feed import BacktraderRealTimeFeed
        
        tester = PerformanceTester()
        feed = BacktraderRealTimeFeed()
        feed.p.symbol = 'AAPL'
        
        print("⏱️ 运行快速延迟测试 (30秒)...")
        latency_result = tester.run_latency_test(feed, 30)
        
        print(f"\\n📊 延迟测试结果:")
        if 'avg_latency_ms' in latency_result:
            print(f"  - 平均延迟: {latency_result['avg_latency_ms']:.1f}ms")
            print(f"  - 最大延迟: {latency_result['max_latency_ms']:.1f}ms")
            print(f"  - P95延迟: {latency_result['p95_latency_ms']:.1f}ms")
            print(f"  - 目标达成: {'✅' if latency_result['target_met'] else '❌'}")
        else:
            print(f"  - 错误: {latency_result.get('error', 'Unknown error')}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def demo_data_source_manager():
    """演示数据源管理"""
    print("\\n⚙️ 数据源管理演示")
    print("=" * 50)
    
    try:
        from src.data.data_source_manager import DataSourceManager
        
        manager = DataSourceManager("demo_data_sources.json")
        
        print("📋 可用数据源:")
        sources = manager.get_available_sources()
        for i, source in enumerate(sources, 1):
            status = "🟢 活跃" if source.name == manager.active_source else "⚪ 备用"
            print(f"  {i}. {source.name} ({source.type}) {status}")
            print(f"     URL: {source.url}")
            print(f"     更新间隔: {source.update_interval_ms}ms")
        
        # 显示性能总结
        summary = manager.get_performance_summary(hours=24)
        print(f"\\n📈 性能总结: {summary}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def main():
    """主演示函数"""
    print("🎯 P0阶段实时数据源功能演示")
    print("=" * 60)
    print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 演示计数
    success_count = 0
    total_demos = 4
    
    try:
        # 1. 实时数据源演示
        if demo_realtime_feed():
            success_count += 1
        
        # 2. Backtrader集成演示
        if demo_backtrader_integration():
            success_count += 1
        
        # 3. 性能测试演示
        if demo_performance_test():
            success_count += 1
        
        # 4. 数据源管理演示
        if demo_data_source_manager():
            success_count += 1
        
    except KeyboardInterrupt:
        print("\\n\\n❌ 用户中断演示")
    
    # 总结
    print(f"\\n🏁 演示完成")
    print("=" * 60)
    print(f"✅ 成功演示: {success_count}/{total_demos}")
    
    if success_count == total_demos:
        print("🎉 所有功能演示成功!")
        print("📋 P0-1任务完成度: 90%")
        print("🔧 下一步: 安装完整依赖、优化性能参数")
    elif success_count >= 2:
        print("👍 大部分功能正常!")
        print("📋 P0-1任务完成度: 70%")
        print("🔧 下一步: 解决导入问题、完善功能")
    else:
        print("⚠️ 需要解决一些问题")
        print("📋 P0-1任务完成度: 40%")
        print("🔧 下一步: 检查环境、安装依赖")
    
    print("\\n📚 P0开发路线图:")
    print("  ✅ P0-1: 实时数据源升级 (进行中)")
    print("  ⏳ P0-2: 基础策略引擎开发")
    print("  ⏳ P0-3: 核心风险框架搭建")

if __name__ == "__main__":
    main()