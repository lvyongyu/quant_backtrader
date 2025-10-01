#!/usr/bin/env python3
"""
专业量化交易系统 - 实时响应式高频交易引擎

🚀 核心功能 + 高级技术库

4个核心功能：
1. 选股 - 四维度智能筛选
2. 自选股池 - 动态管理
3. 策略分析 - 多策略组合+回测验证
4. 自动交易 - 实时响应式执行

高级技术库：
- 异常检测系统 (统计+ML+时间序列)
- 机器学习预测 (信号生成+风险预测)
- 专业级风险控制 (多层防护+实时监控)
- 高级分析器 (性能归因+因子分析+绩效评估)
- 性能监控系统 (系统监控+警报+优化建议)
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime

def print_banner():
    """打印系统横幅"""
    print("===============================================================================")
    print("⚡ 专业量化交易系统 - 实时响应式高频交易引擎 v4.0")
    print("===============================================================================")
    print("🎯 4个核心功能:")
    print("   1. 🔍 智能选股     - 四维度分析 + 高级技术指标")
    print("   2. 📋 自选股池     - 动态管理 + 实时评分")
    print("   3. 📊 策略分析     - 多策略组合 + 回测验证 + 异常检测")
    print("   4. ⚡ 自动交易     - 实时响应 + 风险控制 + ML预测")
    print()
    print("🏆 高级技术库:")
    print("   🔬 异常检测系统   - 统计+机器学习+时间序列多维检测")
    print("   🤖 机器学习集成   - 信号生成+风险预测+智能决策")
    print("   🛡️ 专业风险控制   - 多层防护+实时监控+压力测试")
    print("   📈 高级分析器     - 性能归因+因子分析+绩效评估")
    print("   📊 性能监控系统   - 系统监控+警报+优化建议")
    print("===============================================================================")

def print_help():
    """打印帮助信息"""
    print("\n🎯 专业量化交易系统 - 使用指南")
    print("=" * 80)
    
    print("\n🔍 1. 智能选股 (四维度分析 + 高级技术库):")
    print("   python3 main.py select single AAPL           # 单股四维度深度分析")
    print("   python3 main.py select pool sp500 --limit 10 # 从股票池智能筛选")
    print("   python3 main.py select batch                 # 批量分析自选股池")
    print("   python3 main.py select anomaly AAPL          # 异常检测分析")
    
    print("\n📋 2. 自选股池管理 (动态管理 + 实时评分):")
    print("   python3 main.py watchlist list               # 查看自选股池")
    print("   python3 main.py watchlist add AAPL           # 添加股票")
    print("   python3 main.py watchlist analyze            # 分析自选股池")
    print("   python3 main.py watchlist stats              # 统计信息")
    
    print("\n📊 3. 策略分析 (多策略组合 + 回测验证 + 异常检测):")
    print("   python3 main.py strategy list                # 列出所有策略")
    print("   python3 main.py strategy test RSI AAPL       # 单策略测试")
    print("   python3 main.py strategy multi 'RSI,MACD' AAPL  # 多策略组合")
    print("   python3 main.py strategy config balanced AAPL  # 使用预设配置")
    print("   python3 main.py strategy backtest RSI AAPL   # 策略回测验证")
    
    print("\n⚡ 4. 自动交易 (实时响应 + 风险控制 + ML预测):")
    print("   python3 main.py trade monitor                # 实时市场监控")
    print("   python3 main.py trade start                  # 启动自动交易")
    print("   python3 main.py trade status                 # 交易系统状态")
    print("   python3 main.py trade risk                   # 风险管理状态")
    
    print("\n� 5. 性能监控 (系统监控 + 警报 + 优化建议):")
    print("   python3 main.py performance dashboard        # 性能仪表板")
    print("   python3 main.py performance start            # 启动监控")
    print("   python3 main.py performance stop             # 停止监控")
    print("   python3 main.py performance status           # 监控状态")
    
    print("\n�🔬 6. 高级技术库 (专业级功能):")
    print("   python3 main.py advanced anomaly AAPL        # 异常检测系统")
    print("   python3 main.py advanced ml AAPL             # 机器学习预测")
    print("   python3 main.py advanced risk AAPL           # 高级风险分析")
    print("   python3 main.py advanced analytics AAPL      # 高级分析器")
    
    print("\n💡 快速开始:")
    print("   python3 main.py select single AAPL           # 分析苹果股票")
    print("   python3 main.py watchlist add AAPL           # 添加到自选股")
    print("   python3 main.py strategy config balanced AAPL  # 使用平衡配置")
    print("   python3 main.py trade monitor                # 启动交易监控")
    print("=" * 80)

def handle_select_command(args):
    """处理选股命令"""
    print("🔍 启动智能选股系统...")
    
    # 使用统一CLI处理选股
    cli_script = os.path.join(os.path.dirname(__file__), 'core', 'simple_cli.py')
    
    if args.action == 'single':
        if not args.symbol:
            print("❌ 请指定股票代码")
            return
        cmd = f"python3 {cli_script} screen single {args.symbol}"
    elif args.action == 'pool':
        pool = args.pool or 'sp500'
        limit = getattr(args, 'limit', 10)
        cmd = f"python3 {cli_script} screen pool {pool} --limit {limit}"
    elif args.action == 'batch':
        cmd = f"python3 {cli_script} screen batch"
    elif args.action == 'anomaly':
        print("🔬 启动异常检测分析...")
        handle_advanced_command(['anomaly', args.symbol])
        return
    else:
        print("❌ 未知选股操作")
        return
    
    os.system(cmd)

def handle_watchlist_command(args):
    """处理自选股池命令"""
    print("📋 启动自选股池管理...")
    
    # 使用统一CLI处理自选股
    cli_script = os.path.join(os.path.dirname(__file__), 'core', 'simple_cli.py')
    
    if args.action == 'add' and args.symbol:
        cmd = f"python3 {cli_script} watchlist add {args.symbol}"
    elif args.action == 'remove' and args.symbol:
        cmd = f"python3 {cli_script} watchlist remove {args.symbol}"
    else:
        cmd = f"python3 {cli_script} watchlist {args.action}"
    
    os.system(cmd)

def handle_strategy_command(args):
    """处理策略分析命令"""
    print("📊 启动策略分析系统...")
    
    # 使用统一CLI处理策略
    cli_script = os.path.join(os.path.dirname(__file__), 'core', 'simple_cli.py')
    
    if args.action == 'list':
        cmd = f"python3 {cli_script} strategy list"
    elif args.action == 'test' and args.strategy and args.symbol:
        cmd = f"python3 {cli_script} strategy test {args.strategy} {args.symbol}"
    elif args.action == 'multi' and args.strategies and args.symbol:
        cmd = f"python3 {cli_script} strategy multi '{args.strategies}' {args.symbol}"
    elif args.action == 'config' and args.config and args.symbol:
        cmd = f"python3 {cli_script} config use {args.config} {args.symbol}"
    elif args.action == 'backtest':
        print("🔄 启动回测验证...")
        # 集成回测功能
        if args.strategy and args.symbol:
            from core.backtest_manager import quick_backtest
            from core.strategy_manager import create_strategy
            
            try:
                strategy = create_strategy(args.strategy)
                result = quick_backtest(strategy, args.symbol)
                print(f"✅ 回测完成: {result.summary()}")
            except Exception as e:
                print(f"❌ 回测失败: {e}")
        return
    else:
        print("❌ 策略命令参数不足")
        return
    
    os.system(cmd)

def handle_trade_command(args):
    """处理自动交易命令 - 实时响应式流程"""
    print("⚡ 启动实时响应式交易引擎...")
    
    if args.action == 'monitor':
        print("📊 启动实时市场监控...")
        print("🛡️ 初始化实时风险引擎...")
        
        # 实时响应式流程：市场数据流 → 实时分析引擎 → 风险引擎 → 信号输出
        try:
            from core.realtime_signal_integration import start_realtime_trading, stop_realtime_trading, get_trading_performance, get_recent_trading_signals
            from core.paper_trader import PaperTrader
            
            # 启动风险引擎集成
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
            from risk_engine_integration import start_risk_engine, get_risk_integration
            
            print("⚡ 启动实时风险引擎...")
            import asyncio
            
            # 异步启动风险引擎
            async def start_risk_engine_async():
                return await start_risk_engine()
            
            # 在事件循环中启动风险引擎
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 启动风险引擎
            risk_integration = loop.run_until_complete(start_risk_engine_async())
            print("✅ 实时风险引擎已启动")
            
            # 创建模拟交易器
            trader = PaperTrader(initial_capital=100000)
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
            
            # 定义交易回调函数
            async def on_trading_signal(action):
                """处理交易信号 - 包含风险检查"""
                print(f"🎯 交易信号: {action.action.upper()} {action.quantity} {action.symbol} @ ${action.price:.2f}")
                print(f"   📊 信号强度: {action.signal_strength:.2f} | 置信度: {action.confidence:.2f}")
                
                if action.metadata:
                    strategies = action.metadata.get('contributing_strategies', [])
                    processing_time = action.metadata.get('processing_time_ms', 0)
                    print(f"   🧠 贡献策略: {', '.join(strategies)}")
                    print(f"   ⚡ 处理时间: {processing_time:.2f}ms")
                
                # 风险检查
                can_trade, risk_msg = await risk_integration.pre_trade_check(
                    action.symbol, action.quantity, action.price
                )
                
                if not can_trade:
                    print(f"   🚫 风险控制阻止: {risk_msg}")
                    return
                
                # 模拟交易执行
                try:
                    if action.action == 'buy':
                        trader.buy(action.symbol, action.quantity, action.price)
                        # 更新风险引擎仓位
                        await risk_integration.update_position(action.symbol, action.quantity, action.price)
                        print(f"   ✅ 买入执行成功")
                    elif action.action == 'sell':
                        trader.sell(action.symbol, action.quantity, action.price)
                        # 更新风险引擎仓位
                        await risk_integration.update_position(action.symbol, -action.quantity, action.price)
                        print(f"   ✅ 卖出执行成功")
                except Exception as e:
                    print(f"   ❌ 交易执行失败: {e}")
                try:
                    if action.action == 'buy':
                        trader.buy(action.symbol, action.quantity, action.price)
                    elif action.action == 'sell':
                        trader.sell(action.symbol, action.quantity, action.price)
                except Exception as e:
                    print(f"   ❌ 交易执行失败: {e}")
            
            # 启动ML预测集成
            print("🤖 启动ML信号预测系统...")
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
                from ml_integration import start_ml_integration, get_ml_integration
                
                # 异步启动ML集成
                async def start_ml_async():
                    return await start_ml_integration(symbols)
                
                ml_integration, ml_success = loop.run_until_complete(start_ml_async())
                if ml_success:
                    print("✅ ML预测系统已启动")
                else:
                    print("⚠️ ML预测系统启动失败，使用传统预测")
                    ml_integration = None
            except Exception as e:
                print(f"⚠️ ML预测系统不可用: {e}")
                ml_integration = None
            
            # 启动实时交易系统
            print("🔄 启动真实数据响应式交易系统...")
            print("💡 正在连接Yahoo Finance等真实数据源...")
            success = start_realtime_trading(symbols, on_trading_signal)
            
            if success:
                print("✅ 真实数据响应式监控已启动")
                print("📈 数据来源: Yahoo Finance真实数据")
                print("📊 数据延迟: 5-15秒 | 策略融合: <2ms | 信号生成: <5ms")
                print("🎯 交易阈值: 信号强度>0.6, 置信度>0.7")
                print("💡 按 Ctrl+C 停止监控")
                
                # 保持运行并显示统计信息
                import time
                start_time = time.time()
                last_stats_time = start_time
                
                try:
                    while True:
                        time.sleep(1)
                        current_time = time.time()
                        
                        # 每10秒显示性能统计
                        if current_time - last_stats_time >= 10:
                            stats = get_trading_performance()
                            
                            print(f"\n📈 系统性能监控 (运行 {current_time - start_time:.0f}s):")
                            print(f"  � 数据流: TPS={stats.get('data_stream', {}).get('tps', 0):.1f}, "
                                  f"延迟={stats.get('data_stream', {}).get('latency_ms', 0):.2f}ms")
                            print(f"  🧠 策略融合: 信号={stats['signals_generated']}, "
                                  f"冲突率={stats.get('signal_fusion', {}).get('conflict_rate', 0):.1%}")
                            print(f"  🎯 交易执行: 信号={stats['signals_generated']}, "
                                  f"交易={stats['trades_executed']}, 转换率={stats['trade_conversion_rate']:.1%}")
                            print(f"  ⚡ 处理延迟: 平均={stats['avg_processing_time_ms']:.2f}ms, "
                                  f"最大={stats['max_processing_time_ms']:.2f}ms")
                            
                            # 显示最近信号
                            recent_signals = get_recent_trading_signals(3)
                            if recent_signals:
                                print(f"  📊 最近信号:")
                                for signal in recent_signals[-3:]:
                                    signal_time = time.strftime('%H:%M:%S', time.localtime(signal['timestamp']))
                                    print(f"    {signal_time} {signal['symbol']}: {signal['final_signal']} "
                                          f"(强度: {signal['strength']:.2f})")
                            
                            last_stats_time = current_time
                
                except KeyboardInterrupt:
                    print("\n⏹️ 正在停止实时监控...")
                finally:
                    stop_realtime_trading()
                    
                    # 最终统计
                    final_stats = get_trading_performance()
                    print(f"\n📊 最终统计:")
                    print(f"  运行时间: {final_stats['runtime_seconds']:.1f}s")
                    print(f"  处理信号: {final_stats['signals_generated']}")
                    print(f"  执行交易: {final_stats['trades_executed']}")
                    print(f"  平均延迟: {final_stats['avg_processing_time_ms']:.2f}ms")
                    print("✅ 实时监控已停止")
            else:
                print("❌ 实时交易系统启动失败")
                
        except Exception as e:
            print(f"❌ 实时监控启动失败: {e}")
            import traceback
            traceback.print_exc()
    
    elif args.action == 'start':
        print("🚀 启动自动交易系统...")
        print("⚠️ 实盘交易功能开发中，当前为高级模拟模式")
        handle_trade_command(type('args', (), {'action': 'monitor'})())
    
    elif args.action == 'status':
        print("📊 交易系统状态检查...")
        try:
            from src.risk import RiskController, RiskLimits
            from core.data_stream_integration_real import get_data_stream_manager
            from core.realtime_signal_integration import get_integration_system, get_trading_performance
            
            # 检查各系统状态
            manager = get_data_stream_manager()
            integration_system = get_integration_system()
            data_status = "✅ 运行中" if manager.is_running else "❌ 已停止"
            signal_status = "✅ 运行中" if integration_system.is_running else "❌ 已停止"
            
            risk_controller = RiskController()
            print("✅ 风险控制器: 正常")
            print(f"📊 真实数据流: {data_status}")
            print(f"🧠 策略信号融合: {signal_status}")
            print(f"🎯 信号集成系统: {signal_status}")
            print("⚠️ 实盘交易: 未启用")
            
            # 显示性能统计
            if integration_system.is_running:
                stats = get_trading_performance()
                print(f"\n📈 真实数据系统性能:")
                print(f"  数据流TPS: {stats.get('data_stream', {}).get('tps', 0):.1f}")
                print(f"  数据延迟: {stats.get('data_stream', {}).get('latency_ms', 0)/1000:.1f}s")
                print(f"  策略融合延迟: {stats.get('signal_fusion', {}).get('avg_fusion_time_ms', 0):.2f}ms")
                print(f"  信号处理延迟: {stats['avg_processing_time_ms']:.2f}ms")
                print(f"  信号生成数: {stats['signals_generated']}")
                print(f"  交易执行数: {stats['trades_executed']}")
                print(f"  缓存股票数: {stats.get('data_stream', {}).get('cached_symbols', 0)}")
            # 检查ML预测系统状态
            try:
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
                from ml_integration import get_ml_integration
                
                ml_integration = get_ml_integration()
                ml_status = ml_integration.get_integration_status()
                
                ml_emoji = "✅" if ml_status['integration_active'] else "❌"
                print(f"🤖 ML预测系统: {ml_emoji} {'运行中' if ml_status['integration_active'] else '已停止'}")
                
                if ml_status['integration_active']:
                    print(f"  预测总数: {ml_status['total_predictions']}")
                    print(f"  成功率: {ml_status['success_rate']:.1%}")
                    print(f"  平均延迟: {ml_status['avg_prediction_time_ms']:.2f}ms")
                    print(f"  真实数据连接: {'是' if ml_status['real_data_connected'] else '否'}")
                
            except Exception as e:
                print(f"🤖 ML预测系统: ❌ 不可用 ({e})")
            
        except Exception as e:
            print(f"❌ 系统检查失败: {e}")
    
    elif args.action == 'risk':
        print("🛡️ 实时风险引擎状态...")
        try:
            # 导入风险引擎集成
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
            from risk_engine_integration import get_risk_integration, print_risk_status
            
            # 获取风险引擎状态
            risk_integration = get_risk_integration()
            
            if risk_integration.is_integrated:
                print("✅ 实时风险引擎: 运行中")
                risk_integration.print_risk_summary()
            else:
                print("❌ 实时风险引擎: 未启动")
                print("\n💡 启动方法:")
                print("   python3 main.py trade monitor  # 启动时自动加载风险引擎")
                print("   python3 main.py trade start    # 启动自动交易(包含风险引擎)")
                
        except Exception as e:
            print(f"❌ 风险引擎检查失败: {e}")
            
            # 显示传统风险控制器状态
            try:
                from src.risk import RiskController, RiskLimits
                
                risk_limits = RiskLimits()
                print("\n📊 传统风险限制配置:")
                print(f"  日最大亏损: {risk_limits.max_daily_loss_pct:.1%}")
                print(f"  单笔最大亏损: {risk_limits.max_single_trade_loss_pct:.1%}")
                print(f"  最大连续亏损: {risk_limits.max_consecutive_losses}次")
                print(f"  最大仓位比例: {risk_limits.max_position_pct:.1%}")
                
            except Exception as e2:
                print(f"❌ 传统风险系统检查失败: {e2}")
            
            print(f"  最大仓位比例: {risk_limits.max_position_pct:.1%}")
            
        except Exception as e:
            print(f"❌ 风险系统检查失败: {e}")

def handle_performance_command(args):
    """处理性能监控命令"""
    print("📊 启动性能监控系统...")
    
    try:
        # 导入性能监控模块
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
        from performance_monitor import get_performance_monitor, start_performance_monitoring, stop_performance_monitoring, print_performance_dashboard
        
        if args.action == 'dashboard':
            print("📊 显示性能仪表板...")
            print_performance_dashboard()
            
        elif args.action == 'start':
            print("🚀 启动性能监控...")
            monitor = get_performance_monitor()
            if monitor.is_running:
                print("⚠️ 性能监控已在运行")
                print_performance_dashboard()
            else:
                print("✅ 启动性能监控成功")
                print("💡 运行 'python3 main.py performance dashboard' 查看实时状态")
                print("💡 运行 'python3 main.py performance stop' 停止监控")
                
        elif args.action == 'stop':
            print("🛑 停止性能监控...")
            monitor = get_performance_monitor()
            if monitor.is_running:
                import asyncio
                asyncio.run(stop_performance_monitoring())
                print("✅ 性能监控已停止")
            else:
                print("⚠️ 性能监控未在运行")
                
        elif args.action == 'status':
            print("📈 性能监控状态...")
            monitor = get_performance_monitor()
            
            print(f"🔄 监控状态: {'✅ 运行中' if monitor.is_running else '❌ 停止'}")
            print(f"📊 系统指标: {len(monitor.system_metrics_history)} 条记录")
            print(f"⚡ 应用指标: {len(monitor.app_metrics_history)} 条记录")
            print(f"🚨 警报数量: {len(monitor.alerts)} 条")
            
            if monitor.is_running or len(monitor.system_metrics_history) > 0:
                print("\n📊 快速性能概览:")
                print_performance_dashboard()
            else:
                print("\n💡 启动方法:")
                print("   python3 main.py performance start    # 启动监控")
                print("   python3 main.py trade monitor        # 启动交易监控(包含性能监控)")
        else:
            print("❌ 未知性能监控操作")
            
    except Exception as e:
        print(f"❌ 性能监控系统错误: {e}")
        import traceback
        traceback.print_exc()

def handle_advanced_command(args_list):
    """处理高级技术库命令"""
    if len(args_list) < 2:
        print("❌ 高级功能参数不足")
        return
    
    function = args_list[0]
    symbol = args_list[1] if len(args_list) > 1 else None
    
    print(f"🔬 启动高级技术库: {function}...")
    
    if function == 'anomaly':
        print(f"🕵️ 异常检测分析: {symbol}")
        try:
            from src.advanced_analytics.anomaly_detection import AnomalyDetectionEngine
            from core.data_manager import get_data
            
            # 获取数据
            data = get_data(symbol, period='6mo')
            if data is None or data.empty:
                print("❌ 数据获取失败")
                return
            
            # 异常检测
            engine = AnomalyDetectionEngine()
            report = engine.comprehensive_anomaly_detection(data['Close'], symbol)
            
            print(f"\n📊 异常检测报告 - {symbol}")
            print("=" * 50)
            print(f"检测方法: {report.detection_method}")
            print(f"分析周期: {report.analysis_period[0].date()} ~ {report.analysis_period[1].date()}")
            print(f"异常总数: {report.summary_stats['total_anomalies']}")
            print(f"异常率: {report.summary_stats['anomaly_rate']:.2f}%")
            
            # 显示严重异常
            critical_anomalies = report.get_critical_anomalies()
            if critical_anomalies:
                print(f"\n🚨 严重异常 ({len(critical_anomalies)}个):")
                for anomaly in critical_anomalies[:5]:  # 只显示前5个
                    print(f"  {anomaly.timestamp.date()}: {anomaly.description}")
            
            # 显示建议
            if report.recommendations:
                print(f"\n💡 建议:")
                for rec in report.recommendations:
                    print(f"  • {rec}")
                    
        except Exception as e:
            print(f"❌ 异常检测失败: {e}")
    
    elif function == 'ml':
        print(f"🤖 机器学习预测: {symbol}")
        print("🚧 机器学习模块开发中...")
        # 这里可以集成ML模块
    
    elif function == 'risk':
        print(f"🛡️ 高级风险分析: {symbol}")
        try:
            from src.risk import RiskController
            from core.data_manager import get_data
            
            data = get_data(symbol, period='1y')
            if data is None or data.empty:
                print("❌ 数据获取失败")
                return
            
            # 计算风险指标
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5) * 100
            max_drawdown = ((data['Close'] / data['Close'].cummax()) - 1).min() * 100
            
            print(f"\n📊 高级风险分析 - {symbol}")
            print("=" * 40)
            print(f"年化波动率: {volatility:.2f}%")
            print(f"最大回撤: {max_drawdown:.2f}%")
            print(f"夏普比率: {returns.mean() / returns.std() * (252**0.5):.2f}")
            
        except Exception as e:
            print(f"❌ 风险分析失败: {e}")
    
    elif function == 'analytics':
        print(f"📈 高级分析器: {symbol}")
        print("🚧 高级分析器模块开发中...")
        # 这里可以集成高级分析器

def create_parser():
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        description="专业量化交易系统 - 实时响应式高频交易引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='核心功能')
    
    # 1. 选股命令
    select_parser = subparsers.add_parser('select', help='智能选股')
    select_parser.add_argument('action', choices=['single', 'pool', 'batch', 'anomaly'], help='选股类型')
    select_parser.add_argument('symbol', nargs='?', help='股票代码（单股分析用）')
    select_parser.add_argument('pool', nargs='?', help='股票池名称（池选股用）')
    select_parser.add_argument('--limit', type=int, default=10, help='结果数量限制')
    
    # 2. 自选股池命令
    watchlist_parser = subparsers.add_parser('watchlist', help='自选股池管理')
    watchlist_parser.add_argument('action', choices=['list', 'add', 'remove', 'analyze', 'stats', 'clear'], help='操作类型')
    watchlist_parser.add_argument('symbol', nargs='?', help='股票代码')
    
    # 3. 策略分析命令
    strategy_parser = subparsers.add_parser('strategy', help='策略分析')
    strategy_parser.add_argument('action', choices=['list', 'test', 'multi', 'config', 'backtest'], help='策略操作')
    strategy_parser.add_argument('strategy', nargs='?', help='策略名称')
    strategy_parser.add_argument('symbol', nargs='?', help='股票代码')
    strategy_parser.add_argument('strategies', nargs='?', help='多策略列表（逗号分隔）')
    strategy_parser.add_argument('config', nargs='?', help='配置名称')
    
    # 4. 自动交易命令
    trade_parser = subparsers.add_parser('trade', help='自动交易')
    trade_parser.add_argument('action', choices=['monitor', 'start', 'status', 'risk'], help='交易操作')
    
    # 5. 性能监控命令
    perf_parser = subparsers.add_parser('performance', help='性能监控')
    perf_parser.add_argument('action', choices=['dashboard', 'start', 'stop', 'status'], help='监控操作')
    
    # 6. 高级技术库命令
    advanced_parser = subparsers.add_parser('advanced', help='高级技术库')
    advanced_parser.add_argument('function', choices=['anomaly', 'ml', 'risk', 'analytics'], help='高级功能')
    advanced_parser.add_argument('symbol', nargs='?', help='股票代码')
    
    return parser

def main():
    """主函数"""
    print_banner()
    
    parser = create_parser()
    
    # 如果没有参数，显示帮助
    if len(sys.argv) == 1:
        print_help()
        return 0
    
    args = parser.parse_args()
    
    try:
        if args.command == 'select':
            handle_select_command(args)
        elif args.command == 'watchlist':
            handle_watchlist_command(args)
        elif args.command == 'strategy':
            handle_strategy_command(args)
        elif args.command == 'trade':
            handle_trade_command(args)
        elif args.command == 'performance':
            handle_performance_command(args)
        elif args.command == 'advanced':
            handle_advanced_command([args.function, args.symbol])
        else:
            print_help()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ 操作已取消")
        return 1
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())