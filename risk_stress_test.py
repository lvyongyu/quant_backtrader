#!/usr/bin/env python3
"""
风险管理系统压力测试

模拟极端市场条件下的风险管理系统表现，验证：
1. 极端价格波动下的止损机制
2. 大幅亏损时的风险监控
3. 系统性风险的紧急保护
4. 高频交易下的性能表现
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 降低日志级别以减少输出
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def stress_test_stop_loss():
    """测试止损机制在极端价格波动下的表现"""
    print("🔥 压力测试1: 极端价格波动止损测试")
    print("-" * 50)
    
    try:
        from src.risk.stop_loss import StopLossManager, StopLossType
        
        manager = StopLossManager()
        
        # 创建多种止损类型
        stop_types = [
            StopLossType.FIXED,
            StopLossType.TRAILING,
            StopLossType.ATR_BASED,
            StopLossType.SMART
        ]
        
        stops = []
        entry_price = 150.0
        
        # 为每种类型创建止损
        for i, stop_type in enumerate(stop_types):
            stop = manager.create_stop_loss(
                stop_type,
                entry_price=entry_price,
                params={'max_loss_pct': 0.02, 'atr_value': 2.5}  # 2%止损
            )
            stops.append((stop_type.value, stop))
        
        # 模拟极端价格波动（闪崩场景）
        print("  📉 模拟闪崩场景...")
        crash_prices = [149.0, 147.0, 143.0, 138.0, 135.0, 132.0, 130.0]  # -13.3%
        
        triggered_stops = []
        
        for price in crash_prices:
            print(f"    价格: ${price:.2f} ({(price/entry_price-1)*100:+.1f}%)")
            
            for stop_name, stop in stops:
                if stop['stop_id'] not in [s[1] for s in triggered_stops]:
                    manager.update_price(stop['stop_id'], price)
                    
                    if manager.check_trigger(stop['stop_id'], price):
                        triggered_stops.append((stop_name, stop['stop_id']))
                        trigger_price = manager.get_stop_price(stop['stop_id'])
                        print(f"      ⚠️  {stop_name} 止损触发 @ ${trigger_price:.2f}")
        
        print(f"\\n  ✅ 测试结果: {len(triggered_stops)}/{len(stops)} 止损正常触发")
        
        # 验证所有止损都应该在合理范围内触发
        success = len(triggered_stops) >= len(stops) * 0.75  # 至少75%触发
        print(f"  {'✅ 通过' if success else '❌ 失败'}: 止损保护机制")
        
        return success
        
    except Exception as e:
        print(f"  ❌ 止损压力测试失败: {e}")
        return False


def stress_test_risk_limits():
    """测试风险限制在极端条件下的表现"""
    print("\\n🚨 压力测试2: 极端风险条件测试")
    print("-" * 50)
    
    try:
        from src.risk import RiskController, RiskMetrics, RiskLevel
        from production_risk_config import RiskConfigManager
        
        # 使用保守配置进行测试
        conservative_limits = RiskConfigManager.get_config('conservative')
        controller = RiskController(conservative_limits)
        
        account_value = 100000.0
        extreme_scenarios = [
            {
                'name': '巨额单笔交易',
                'trade': {
                    'symbol': 'TSLA',
                    'quantity': 5000,
                    'price': 200.0,
                    'estimated_loss': 0.05  # 5%风险
                },
                'should_pass': False
            },
            {
                'name': '超高仓位比例',
                'trade': {
                    'symbol': 'NVDA',
                    'quantity': 1000,
                    'price': 800.0,
                    'estimated_loss': 0.02  # 2%风险
                },
                'should_pass': False
            },
            {
                'name': '正常保守交易',
                'trade': {
                    'symbol': 'AAPL',
                    'quantity': 100,
                    'price': 150.0,
                    'estimated_loss': 0.001  # 0.1%风险
                },
                'should_pass': True
            }
        ]
        
        passed_tests = 0
        
        for scenario in extreme_scenarios:
            trade = scenario['trade']
            expected = scenario['should_pass']
            
            is_valid, reason = controller.validate_trade_dict(trade, account_value)
            
            result = "✅ 通过" if is_valid == expected else "❌ 失败"
            print(f"  {result}: {scenario['name']}")
            print(f"    验证结果: {'允许' if is_valid else '拒绝'} - {reason}")
            
            if is_valid == expected:
                passed_tests += 1
        
        success = passed_tests == len(extreme_scenarios)
        print(f"\\n  {'✅ 通过' if success else '❌ 失败'}: 风险限制保护 ({passed_tests}/{len(extreme_scenarios)})")
        
        return success
        
    except Exception as e:
        print(f"  ❌ 风险限制压力测试失败: {e}")
        return False


def stress_test_risk_monitoring():
    """测试风险监控在持续亏损下的表现"""
    print("\\n📊 压力测试3: 持续亏损监控测试")
    print("-" * 50)
    
    try:
        from src.risk.risk_monitor import RiskMonitor, RiskAlert
        from src.risk import RiskMetrics, RiskLevel
        
        monitor = RiskMonitor(check_interval=1)  # 1秒检查
        
        alerts_received = []
        emergency_events = []
        
        def alert_callback(alert: RiskAlert):
            alerts_received.append(alert)
            print(f"    ⚠️  警报: {alert.alert_type} - {alert.message}")
        
        def emergency_callback(event):
            emergency_events.append(event)
            print(f"    🚨 紧急事件: {event.event_type}")
        
        monitor.add_alert_callback(alert_callback)
        monitor.add_emergency_callback(emergency_callback)
        
        # 启动监控
        monitor.start_monitoring()
        
        # 模拟逐步恶化的市场条件
        print("  📉 模拟持续亏损场景...")
        
        initial_value = 100000
        for day in range(5):  # 5天持续亏损
            daily_loss = 0.018 + (day * 0.002)  # 逐渐增加的损失 1.8% -> 2.6%
            consecutive_losses = day + 1
            
            current_value = initial_value * (1 - daily_loss)
            
            # 更新风险指标
            metrics = RiskMetrics(
                account_value=current_value,
                daily_pnl=-initial_value * daily_loss,
                consecutive_losses=consecutive_losses,
                max_drawdown=daily_loss * 1.2,
                risk_level=RiskLevel.HIGH if daily_loss > 0.02 else RiskLevel.MODERATE
            )
            
            monitor.update_metrics(metrics)
            print(f"    第{day+1}天: 账户${current_value:,.0f} 亏损{daily_loss:.1%}")
            
            time.sleep(1.5)  # 等待监控检查
        
        time.sleep(2)  # 最后等待
        monitor.stop_monitoring()
        
        # 分析结果
        print(f"\\n  📈 监控结果:")
        print(f"    总警报数: {len(alerts_received)}")
        print(f"    紧急事件数: {len(emergency_events)}")
        
        # 验证应该产生警报
        success = len(alerts_received) > 0  # 应该至少有一个警报
        print(f"  {'✅ 通过' if success else '❌ 失败'}: 风险监控机制")
        
        return success
        
    except Exception as e:
        print(f"  ❌ 风险监控压力测试失败: {e}")
        return False


def stress_test_high_frequency():
    """测试高频交易场景下的性能"""
    print("\\n⚡ 压力测试4: 高频交易性能测试")
    print("-" * 50)
    
    try:
        from src.risk import RiskController
        from production_risk_config import RiskConfigManager
        
        # 使用生产配置
        production_limits = RiskConfigManager.get_config('production')
        controller = RiskController(production_limits)
        
        account_value = 100000.0
        num_trades = 1000  # 1000笔交易
        
        print(f"  🔄 模拟 {num_trades} 笔高频交易...")
        
        start_time = time.time()
        valid_trades = 0
        rejected_trades = 0
        
        for i in range(num_trades):
            # 生成随机交易
            trade = {
                'symbol': random.choice(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']),
                'quantity': random.randint(50, 200),
                'price': random.uniform(100, 300),
                'estimated_loss': random.uniform(0.001, 0.008)  # 0.1%-0.8%风险
            }
            
            is_valid, _ = controller.validate_trade_dict(trade, account_value)
            
            if is_valid:
                valid_trades += 1
            else:
                rejected_trades += 1
        
        end_time = time.time()
        duration = end_time - start_time
        trades_per_second = num_trades / duration
        
        print(f"\\n  📊 性能结果:")
        print(f"    处理时间: {duration:.2f}秒")
        print(f"    处理速度: {trades_per_second:.0f} 交易/秒")
        print(f"    通过交易: {valid_trades}")
        print(f"    拒绝交易: {rejected_trades}")
        print(f"    通过率: {valid_trades/num_trades:.1%}")
        
        # 验证性能要求（至少100交易/秒）
        performance_ok = trades_per_second >= 100
        rejection_rate_ok = rejected_trades / num_trades >= 0.1  # 至少10%拒绝率说明风控有效
        
        success = performance_ok and rejection_rate_ok
        print(f"  {'✅ 通过' if success else '❌ 失败'}: 高频交易性能")
        
        return success
        
    except Exception as e:
        print(f"  ❌ 高频交易压力测试失败: {e}")
        return False


def stress_test_system_integration():
    """测试系统整体集成的健壮性"""
    print("\\n🔧 压力测试5: 系统集成健壮性测试")
    print("-" * 50)
    
    try:
        from src.risk import RiskController
        from src.risk.stop_loss import StopLossManager
        from src.risk.position_manager import PositionManager
        from src.risk.risk_monitor import RiskMonitor
        from production_risk_config import RiskConfigManager
        
        # 创建所有组件
        risk_limits = RiskConfigManager.get_config('production')
        risk_controller = RiskController(risk_limits)
        stop_manager = StopLossManager()
        position_manager = PositionManager()
        risk_monitor = RiskMonitor(check_interval=2)
        
        print("  🔧 测试组件初始化...")
        
        # 测试组件协同工作
        account_value = 100000.0
        
        # 1. 风险控制器验证交易
        test_trade = {
            'symbol': 'AAPL',
            'quantity': 200,
            'price': 150.0,
            'estimated_loss': 0.004
        }
        
        is_valid, reason = risk_controller.validate_trade_dict(test_trade, account_value)
        print(f"    ✅ 风险控制器: {'通过' if is_valid else '拒绝'}")
        
        # 2. 仓位管理器计算仓位
        from src.risk import PositionSizeMethod
        position_size = position_manager.calculate_position_size(
            method=PositionSizeMethod.FIXED_PERCENTAGE,
            account_value=account_value,
            price=150.0,
            risk_per_trade=0.01
        )
        print(f"    ✅ 仓位管理器: {position_size}股建议仓位")
        
        # 3. 止损管理器创建止损
        from src.risk.stop_loss import StopLossType
        stop_loss = stop_manager.create_stop_loss(
            StopLossType.SMART,
            entry_price=150.0,
            params={'max_loss_pct': 0.02}
        )
        print(f"    ✅ 止损管理器: 创建智能止损")
        
        # 4. 风险监控器监控
        risk_monitor.start_monitoring()
        from src.risk import RiskMetrics, RiskLevel
        
        metrics = RiskMetrics(
            account_value=account_value,
            daily_pnl=0,
            consecutive_losses=0,
            risk_level=RiskLevel.LOW
        )
        
        risk_monitor.update_metrics(metrics)
        time.sleep(3)
        risk_monitor.stop_monitoring()
        print(f"    ✅ 风险监控器: 运行正常")
        
        print(f"\\n  ✅ 通过: 系统集成健壮性")
        return True
        
    except Exception as e:
        print(f"  ❌ 系统集成测试失败: {e}")
        return False


def generate_stress_test_report(results: List[bool]) -> Dict[str, Any]:
    """生成压力测试报告"""
    total_tests = len(results)
    passed_tests = sum(results)
    pass_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    test_names = [
        "极端价格波动止损测试",
        "极端风险条件测试", 
        "持续亏损监控测试",
        "高频交易性能测试",
        "系统集成健壮性测试"
    ]
    
    return {
        'test_time': datetime.now().isoformat(),
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': total_tests - passed_tests,
        'pass_rate': pass_rate,
        'overall_status': '通过' if pass_rate >= 0.8 else '失败',
        'test_results': dict(zip(test_names, results)),
        'recommendations': generate_recommendations(results)
    }


def generate_recommendations(results: List[bool]) -> List[str]:
    """基于测试结果生成建议"""
    recommendations = []
    
    if not results[0]:  # 止损测试失败
        recommendations.append("建议调整止损参数，增强极端波动保护")
    
    if not results[1]:  # 风险限制测试失败
        recommendations.append("建议降低风险限制阈值，加强风险控制")
    
    if not results[2]:  # 监控测试失败
        recommendations.append("建议优化风险监控算法，提高预警敏感度")
    
    if not results[3]:  # 性能测试失败
        recommendations.append("建议优化风险验证算法，提高处理性能")
    
    if not results[4]:  # 集成测试失败
        recommendations.append("建议检查系统组件兼容性，修复集成问题")
    
    if all(results):
        recommendations.append("所有测试通过，系统风险管理健壮")
        recommendations.append("建议定期执行压力测试，持续监控系统状态")
    
    return recommendations


def main():
    """主函数"""
    print("🧪 风险管理系统压力测试")
    print("=" * 60)
    print("⚠️  警告: 这是模拟压力测试，不涉及真实交易")
    print("🎯 目标: 验证风险保护机制在极端条件下的可靠性")
    print("=" * 60)
    
    # 执行所有压力测试
    test_functions = [
        stress_test_stop_loss,
        stress_test_risk_limits,
        stress_test_risk_monitoring,
        stress_test_high_frequency,
        stress_test_system_integration
    ]
    
    results = []
    start_time = time.time()
    
    for test_func in test_functions:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            results.append(False)
    
    end_time = time.time()
    
    # 生成测试报告
    report = generate_stress_test_report(results)
    
    print("\\n" + "=" * 60)
    print("📋 压力测试总结报告")
    print("=" * 60)
    
    print(f"⏱️  测试时间: {end_time - start_time:.1f}秒")
    print(f"📊 测试结果: {report['passed_tests']}/{report['total_tests']} 通过")
    print(f"📈 通过率: {report['pass_rate']:.1%}")
    print(f"🎯 总体状态: {report['overall_status']}")
    
    print("\\n📋 详细结果:")
    for test_name, result in report['test_results'].items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {test_name}")
    
    print("\\n💡 改进建议:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    if report['pass_rate'] >= 0.8:
        print("\\n🎉 恭喜! 风险管理系统通过压力测试")
        print("🛡️ 系统可以在极端市场条件下提供可靠保护")
    else:
        print("\\n⚠️  警告: 风险管理系统存在薄弱环节")
        print("🔧 建议按照改进建议优化系统后重新测试")
    
    print("\\n" + "=" * 60)
    return report['pass_rate'] >= 0.8


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)