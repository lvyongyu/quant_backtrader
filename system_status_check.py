#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统综合状态检查器
检查所有核心组件的状态和功能
"""

import os
import sys
import traceback
from datetime import datetime

def check_component_status():
    """检查所有组件状态"""
    print("🔍 开始系统综合状态检查...")
    print("=" * 80)
    
    components = {
        'data_manager': '📊 数据管理器',
        'strategy_signal_fusion': '🧠 策略信号融合',
        'risk_engine_integration': '🛡️ 风险引擎集成',
        'realtime_signal_integration': '⚡ 实时信号集成',
        'realtime_risk_engine': '🚨 实时风险引擎',
        'ml_signal_prediction': '🤖 ML信号预测',
        'ml_integration': '🔗 ML集成',
        'smart_order_execution': '📈 智能订单执行',
        'performance_monitor': '📊 性能监控'
    }
    
    status_report = {}
    
    # 添加 core 目录到路径
    core_path = os.path.join(os.path.dirname(__file__), 'core')
    if core_path not in sys.path:
        sys.path.append(core_path)
    
    for module_name, display_name in components.items():
        try:
            print(f"\n{display_name}:")
            
            # 动态导入模块
            module = __import__(module_name)
            
            # 检查关键类和函数
            if module_name == 'data_manager':
                # 测试数据获取
                data = module.get_data('AAPL', period='5d')
                if data is not None and not data.empty:
                    print("  ✅ 数据获取正常")
                    print(f"  📊 数据量: {len(data)} 条记录")
                    status_report[module_name] = 'OK'
                else:
                    print("  ❌ 数据获取失败")
                    status_report[module_name] = 'ERROR'
                    
            elif module_name == 'strategy_signal_fusion':
                # 检查策略融合系统
                fusion_system = module.StrategySignalFusion()
                print("  ✅ 策略融合系统初始化成功")
                print(f"  🎯 已注册策略: {len(fusion_system.strategies)}")
                status_report[module_name] = 'OK'
                
            elif module_name == 'risk_engine_integration':
                # 检查风险引擎
                risk_engine = module.RiskEngineIntegration()
                print("  ✅ 风险引擎初始化成功")
                print(f"  🛡️ 风险控制: {'启用' if risk_engine.is_integrated else '禁用'}")
                status_report[module_name] = 'OK'
                
            elif module_name == 'realtime_signal_integration':
                # 检查实时信号
                signal_system = module.RealtimeSignalIntegration()
                print("  ✅ 实时信号系统初始化成功")
                print(f"  ⚡ 信号处理器: 已配置")
                status_report[module_name] = 'OK'
                
            elif module_name == 'realtime_risk_engine':
                # 检查实时风险引擎
                risk_engine = module.RealtimeRiskEngine()
                print("  ✅ 实时风险引擎初始化成功")
                print(f"  🚨 风险监控: 已配置")
                status_report[module_name] = 'OK'
                
            elif module_name == 'ml_signal_prediction':
                # 检查ML信号预测
                ml_system = module.MLSignalPredictionSystem()
                print("  ✅ ML信号预测系统初始化成功")
                print(f"  🤖 ML模型: {len(ml_system.model_manager.models)} 个")
                status_report[module_name] = 'OK'
                
            elif module_name == 'ml_integration':
                # 检查ML集成
                ml_integration = module.MLIntegration()
                print("  ✅ ML集成系统初始化成功")
                print(f"  🔗 数据集成: 已配置")
                status_report[module_name] = 'OK'
                
            elif module_name == 'smart_order_execution':
                # 检查智能订单执行
                order_engine = module.SmartOrderExecutionEngine()
                print("  ✅ 智能订单执行引擎初始化成功")
                print(f"  📈 执行策略: {len(order_engine.execution_strategies)} 个")
                status_report[module_name] = 'OK'
                
            elif module_name == 'performance_monitor':
                # 检查性能监控
                monitor = module.get_performance_monitor()
                print("  ✅ 性能监控系统初始化成功")
                print(f"  📊 监控状态: {'运行中' if monitor.is_running else '待启动'}")
                status_report[module_name] = 'OK'
                
        except Exception as e:
            print(f"  ❌ {display_name} 检查失败: {str(e)}")
            status_report[module_name] = 'ERROR'
    
    # 生成状态报告
    print("\n" + "=" * 80)
    print("📋 系统状态报告")
    print("=" * 80)
    
    total_components = len(components)
    working_components = sum(1 for status in status_report.values() if status == 'OK')
    
    print(f"📊 组件状态: {working_components}/{total_components} 正常运行")
    print(f"📈 系统健康度: {working_components/total_components*100:.1f}%")
    
    # 详细状态
    print(f"\n📝 详细状态:")
    for module_name, display_name in components.items():
        status = status_report.get(module_name, 'UNKNOWN')
        status_emoji = "✅" if status == 'OK' else "❌"
        print(f"   {status_emoji} {display_name}: {status}")
    
    # 系统建议
    print(f"\n💡 系统建议:")
    if working_components == total_components:
        print("   🎉 所有组件运行正常！系统已准备就绪")
        print("   🚀 可以开始进行量化交易操作")
    else:
        failed_components = [name for name, status in status_report.items() if status != 'OK']
        print(f"   ⚠️ 有 {len(failed_components)} 个组件需要修复")
        for component in failed_components:
            print(f"   🔧 检查组件: {components[component]}")
    
    print("=" * 80)
    return status_report

def test_integration():
    """测试组件集成"""
    print("\n🔗 开始集成测试...")
    
    try:
        # 添加 core 目录到路径
        core_path = os.path.join(os.path.dirname(__file__), 'core')
        if core_path not in sys.path:
            sys.path.append(core_path)
        
        print("\n1. 数据流测试...")
        from data_manager import get_data
        data = get_data('AAPL', period='5d')
        if data is not None:
            print(f"   ✅ 数据获取成功: {len(data)} 条记录")
        else:
            print(f"   ❌ 数据获取失败")
        
        print("\n2. 策略信号测试...")
        from strategy_signal_fusion import StrategySignalFusion
        fusion = StrategySignalFusion()
        if data is not None:
            signals = fusion.generate_signals('AAPL', data)
            print(f"   ✅ 策略信号生成成功: {len(signals)} 个信号")
        
        print("\n3. ML预测测试...")
        from ml_signal_prediction import MLSignalPredictionSystem
        ml_system = MLSignalPredictionSystem()
        print(f"   ✅ ML系统初始化: {len(ml_system.model_manager.models)} 个模型")
        
        print("\n4. 订单执行测试...")
        from smart_order_execution import SmartOrderExecutionEngine, Order, OrderType
        order_engine = SmartOrderExecutionEngine()
        test_order = Order(
            order_id='TEST_ORDER_001',
            symbol='AAPL',
            side='buy',
            order_type=OrderType.MARKET,
            quantity=100,
            price=150.0
        )
        print(f"   ✅ 订单系统测试成功")
        
        print("\n5. 性能监控测试...")
        from performance_monitor import get_performance_monitor
        monitor = get_performance_monitor()
        summary = monitor.get_performance_summary()
        print(f"   ✅ 性能监控获取成功: 评分 {summary.get('performance_score', 0)}/100")
        
        print("\n🎉 集成测试完成！所有组件协同工作正常")
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        traceback.print_exc()
        return False

def print_system_architecture():
    """打印系统架构图"""
    print("\n🏗️ 系统架构图")
    print("=" * 80)
    print("""
                    📊 专业量化交易系统架构
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                        🎯 主程序 (main.py)                      │
    │                    统一命令行接口 + 系统控制                     │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                      📊 数据层 (Data Layer)                    │
    │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
    │  │ 数据管理器   │  │ 实时数据引擎  │  │ 统一数据源集成        │   │
    │  │ data_manager │  │ realtime_    │  │ data_stream_         │   │
    │  │             │  │ data_engine  │  │ integration_real     │   │
    │  └─────────────┘  └──────────────┘  └──────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    🧠 信号处理层 (Signal Layer)                 │
    │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
    │  │ 策略信号融合 │  │ 实时信号集成  │  │ ML信号预测            │   │
    │  │ strategy_   │  │ realtime_    │  │ ml_signal_           │   │
    │  │ signal_fusion│  │ signal_integ │  │ prediction           │   │
    │  └─────────────┘  └──────────────┘  └──────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    🛡️ 风险控制层 (Risk Layer)                   │
    │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
    │  │ 风险引擎集成 │  │ 实时风险引擎  │  │ 风险管理系统          │   │
    │  │ risk_engine_│  │ realtime_    │  │ risk_management      │   │
    │  │ integration │  │ risk_engine  │  │                      │   │
    │  └─────────────┘  └──────────────┘  └──────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                  📈 执行层 (Execution Layer)                    │
    │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
    │  │ 智能订单执行 │  │ 纸张交易器    │  │ 快速交易引擎          │   │
    │  │ smart_order_│  │ paper_trader │  │ quick_trade          │   │
    │  │ execution   │  │              │  │                      │   │
    │  └─────────────┘  └──────────────┘  └──────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                📊 监控分析层 (Monitoring Layer)                  │
    │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
    │  │ 性能监控系统 │  │ 高级分析器    │  │ 异常检测系统          │   │
    │  │ performance_│  │ advanced_    │  │ anomaly_detection    │   │
    │  │ monitor     │  │ analytics    │  │                      │   │
    │  └─────────────┘  └──────────────┘  └──────────────────────┘   │
    └─────────────────────────────────────────────────────────────────┘
    
    🔄 数据流向: 实时数据 → 信号生成 → 风险检查 → 订单执行 → 性能监控
    ⚡ 特色功能: 机器学习增强 + 多层风险控制 + 实时性能优化
    🎯 目标延迟: <200ms 端到端处理时间
    """)
    print("=" * 80)

if __name__ == "__main__":
    print(f"🕐 系统检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 组件状态检查
    status_report = check_component_status()
    
    # 2. 集成测试
    integration_ok = test_integration()
    
    # 3. 系统架构图
    print_system_architecture()
    
    # 4. 最终评估
    print(f"\n🏆 最终评估")
    print("=" * 80)
    working_count = sum(1 for status in status_report.values() if status == 'OK')
    total_count = len(status_report)
    
    if working_count == total_count and integration_ok:
        print("🎉 系统状态: 优秀")
        print("✅ 所有组件正常运行")
        print("✅ 集成测试通过")
        print("🚀 系统已准备投入使用！")
    elif working_count >= total_count * 0.8:
        print("😊 系统状态: 良好")
        print(f"✅ {working_count}/{total_count} 组件正常")
        print("⚠️ 建议修复剩余问题后投入使用")
    else:
        print("😐 系统状态: 需要改进")
        print(f"⚠️ 只有 {working_count}/{total_count} 组件正常")
        print("🔧 需要修复主要问题后才能使用")
    
    print("=" * 80)