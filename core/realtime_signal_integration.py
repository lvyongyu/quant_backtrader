#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时交易信号集成系统
整合实时数据流和策略信号融合系统，为高频交易提供完整的信号处理管道

功能特点:
- 实时数据 → 策略分析 → 信号融合 → 交易执行
- 多策略并行处理
- 性能监控和延迟追踪
- 灵活的信号回调机制
"""

import asyncio
import logging
import time
import sys
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import json

# 添加路径以支持导入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # 使用绝对导入方式
    import data_stream_integration_real
    import strategy_signal_fusion
    
    DataStreamManager = data_stream_integration_real.DataStreamManager
    start_realtime_data = data_stream_integration_real.start_realtime_data
    subscribe_to_symbol = data_stream_integration_real.subscribe_to_symbol
    stop_realtime_data = data_stream_integration_real.stop_realtime_data
    get_data_stream_manager = data_stream_integration_real.get_data_stream_manager
    
    StrategySignalFusion = strategy_signal_fusion.StrategySignalFusion
    create_default_fusion_system = strategy_signal_fusion.create_default_fusion_system
    FusedSignal = strategy_signal_fusion.FusedSignal
    SignalType = strategy_signal_fusion.SignalType
    
    SIGNAL_INTEGRATION_AVAILABLE = True
    logger.info("✅ 信号集成模块导入成功")
except ImportError as e:
    logger.warning(f"导入模块失败: {e}")
    # 提供备用导入或模拟类
    DataStreamManager = None
    StrategySignalFusion = None
    FusedSignal = None
    SignalType = None
    start_realtime_data = None
    subscribe_to_symbol = None
    stop_realtime_data = None
    create_default_fusion_system = None
    get_data_stream_manager = None
    SIGNAL_INTEGRATION_AVAILABLE = False

@dataclass
class TradingAction:
    """交易动作"""
    symbol: str
    action: str  # buy, sell, hold
    quantity: int
    price: float
    signal_strength: float
    confidence: float
    timestamp: float
    metadata: Dict[str, Any] = None

class RealTimeSignalIntegration:
    """实时交易信号集成系统"""
    
    def __init__(self):
        self.data_manager = None  # Optional[DataStreamManager]
        self.fusion_system = None  # Optional[StrategySignalFusion]
        self.is_running = False
        self.trading_callbacks = []
        self.signal_history = []
        self.event_loop = None  # 保存事件循环引用
        self.performance_stats = {
            'signals_generated': 0,
            'trades_executed': 0,
            'start_time': 0,
            'processing_times': []
        }
        
    def add_trading_callback(self, callback: Callable[[TradingAction], None]):
        """添加交易回调函数"""
        self.trading_callbacks.append(callback)
        
    def start_integration(self, symbols: List[str]):
        """启动实时信号集成系统"""
        logger.info("🚀 启动实时信号集成系统...")
        
        if not SIGNAL_INTEGRATION_AVAILABLE:
            logger.error("❌ 信号集成模块不可用，无法启动")
            return False
        
        try:
            # 检查必要的函数是否可用
            if start_realtime_data is None or create_default_fusion_system is None:
                logger.error("❌ 关键函数不可用")
                return False
            
            # 尝试获取或创建事件循环
            try:
                self.event_loop = asyncio.get_event_loop()
                if self.event_loop.is_closed():
                    self.event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.event_loop)
            except RuntimeError:
                self.event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.event_loop)
            
            # 启动实时数据流
            self.data_manager = start_realtime_data(symbols)
            if self.data_manager is None:
                logger.error("❌ 数据管理器启动失败")
                return False
            
            # 创建策略融合系统
            self.fusion_system = create_default_fusion_system()
            if self.fusion_system is None:
                logger.error("❌ 策略融合系统创建失败")
                return False
            
            # 添加信号回调
            self.fusion_system.add_signal_callback(self._on_fused_signal)
            
            # 启动融合系统
            self.fusion_system.start()
            
            # 订阅实时数据
            if subscribe_to_symbol is not None:
                for symbol in symbols:
                    subscribe_to_symbol(symbol, self._on_market_data)
            else:
                logger.warning("⚠️ 数据订阅功能不可用")
            
            self.is_running = True
            self.performance_stats['start_time'] = time.time()
            
            logger.info(f"✅ 实时信号集成已启动，监控股票: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 实时信号集成启动失败: {e}")
            return False
    
    def stop_integration(self):
        """停止实时信号集成系统"""
        logger.info("⏹️ 停止实时信号集成系统...")
        
        try:
            self.is_running = False
            
            if self.fusion_system:
                self.fusion_system.stop()
                
            if stop_realtime_data:
                stop_realtime_data()
            
            # 清理事件循环任务
            if self.event_loop and not self.event_loop.is_closed():
                try:
                    # 取消所有待处理的任务
                    pending_tasks = asyncio.all_tasks(self.event_loop)
                    for task in pending_tasks:
                        if not task.done():
                            task.cancel()
                    
                    # 等待任务完成或取消
                    if pending_tasks:
                        self.event_loop.run_until_complete(
                            asyncio.gather(*pending_tasks, return_exceptions=True)
                        )
                except Exception as e:
                    logger.warning(f"清理异步任务时出现问题: {e}")
            
            logger.info("✅ 实时信号集成已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止实时信号集成失败: {e}")
    
    def _on_market_data(self, market_data: Dict):
        """处理实时市场数据"""
        if not self.is_running or not self.fusion_system:
            return
            
        try:
            symbol = market_data.get('symbol')
            if symbol:
                # 检查事件循环状态并安全地处理市场数据
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running() and not loop.is_closed():
                        # 异步处理市场数据，生成信号
                        asyncio.create_task(
                            self.fusion_system.process_market_data(symbol, market_data)
                        )
                    else:
                        # 同步处理数据作为备用方案
                        self.fusion_system.process_market_data_sync(symbol, market_data)
                except RuntimeError:
                    # 如果没有事件循环，使用同步处理
                    if hasattr(self.fusion_system, 'process_market_data_sync'):
                        self.fusion_system.process_market_data_sync(symbol, market_data)
                    else:
                        logger.warning(f"无法处理市场数据: 事件循环不可用，symbol: {symbol}")
                
        except Exception as e:
            logger.error(f"市场数据处理失败: {e}")
    
    def _on_fused_signal(self, fused_signal):
        """处理融合信号"""
        try:
            start_time = time.time()
            
            # 记录信号历史
            self.signal_history.append(fused_signal)
            
            # 保持最近1000条记录
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
            
            # 生成交易动作
            trading_action = self._generate_trading_action(fused_signal)
            
            if trading_action:
                # 触发交易回调
                for callback in self.trading_callbacks:
                    try:
                        callback(trading_action)
                    except Exception as e:
                        logger.error(f"交易回调执行失败: {e}")
                
                # 更新统计
                self.performance_stats['trades_executed'] += 1
            
            # 记录处理时间
            processing_time = (time.time() - start_time) * 1000
            self.performance_stats['processing_times'].append(processing_time)
            self.performance_stats['signals_generated'] += 1
            
            # 保持最近1000次记录
            if len(self.performance_stats['processing_times']) > 1000:
                self.performance_stats['processing_times'] = self.performance_stats['processing_times'][-1000:]
                
        except Exception as e:
            logger.error(f"融合信号处理失败: {e}")
    
    def _generate_trading_action(self, fused_signal) -> Optional[TradingAction]:
        """将融合信号转换为交易动作"""
        try:
            # 设置交易阈值
            MIN_SIGNAL_STRENGTH = 0.6
            MIN_CONFIDENCE = 0.7
            
            # 检查信号强度和置信度
            if (fused_signal.aggregated_strength < MIN_SIGNAL_STRENGTH or 
                fused_signal.confidence_score < MIN_CONFIDENCE):
                return None
            
            # 确定交易动作
            action = "hold"
            if SignalType is not None:
                if hasattr(fused_signal.final_signal, 'value'):
                    signal_value = fused_signal.final_signal.value
                else:
                    signal_value = str(fused_signal.final_signal)
                
                if signal_value in ["buy", "strong_buy"]:
                    action = "buy"
                elif signal_value in ["sell", "strong_sell"]:
                    action = "sell"
            else:
                # 备用逻辑：基于字符串值判断
                signal_str = str(fused_signal.final_signal).lower()
                if "buy" in signal_str:
                    action = "buy"
                elif "sell" in signal_str:
                    action = "sell"
            
            if action == "hold":
                return None
            
            # 计算交易数量（基于信号强度）
            base_quantity = 100
            quantity = int(base_quantity * fused_signal.aggregated_strength)
            
            # 获取当前价格
            current_price = 0
            if self.data_manager and hasattr(self.data_manager, 'get_latest_price'):
                try:
                    latest_price = self.data_manager.get_latest_price(fused_signal.symbol)
                    if latest_price:
                        current_price = latest_price.get('price', 0)
                except AttributeError:
                    # 如果方法不存在，使用默认价格
                    current_price = 100.0
            
            return TradingAction(
                symbol=fused_signal.symbol,
                action=action,
                quantity=quantity,
                price=current_price,
                signal_strength=fused_signal.aggregated_strength,
                confidence=fused_signal.confidence_score,
                timestamp=time.time(),
                metadata={
                    'contributing_strategies': fused_signal.contributing_strategies,
                    'signal_weights': fused_signal.signal_weights,
                    'processing_time_ms': getattr(fused_signal, 'processing_time_ms', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"交易动作生成失败: {e}")
            return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        runtime = time.time() - self.performance_stats['start_time'] if self.performance_stats['start_time'] > 0 else 0
        processing_times = self.performance_stats['processing_times']
        
        stats = {
            'runtime_seconds': runtime,
            'signals_generated': self.performance_stats['signals_generated'],
            'trades_executed': self.performance_stats['trades_executed'],
            'signals_per_second': self.performance_stats['signals_generated'] / runtime if runtime > 0 else 0,
            'trades_per_second': self.performance_stats['trades_executed'] / runtime if runtime > 0 else 0,
            'avg_processing_time_ms': sum(processing_times) / len(processing_times) if processing_times else 0,
            'max_processing_time_ms': max(processing_times) if processing_times else 0,
            'recent_signals_count': len(self.signal_history),
            'trade_conversion_rate': (self.performance_stats['trades_executed'] / 
                                    max(1, self.performance_stats['signals_generated']))
        }
        
        # 添加数据流和融合系统统计
        if self.data_manager:
            data_stats = self.data_manager.get_performance_stats()
            stats['data_stream'] = data_stats
            
        if self.fusion_system:
            fusion_stats = self.fusion_system.get_performance_stats()
            stats['signal_fusion'] = fusion_stats
            
        return stats
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """获取最近的信号记录"""
        recent_signals = self.signal_history[-limit:] if self.signal_history else []
        return [
            {
                'symbol': signal.symbol,
                'final_signal': signal.final_signal.value,
                'strength': signal.aggregated_strength,
                'confidence': signal.confidence_score,
                'strategies': signal.contributing_strategies,
                'timestamp': signal.timestamp,
                'processing_time_ms': signal.processing_time_ms
            }
            for signal in recent_signals
        ]

# 全局实例
_global_integration_system: Optional[RealTimeSignalIntegration] = None

def get_integration_system() -> RealTimeSignalIntegration:
    """获取全局集成系统实例"""
    global _global_integration_system
    if _global_integration_system is None:
        _global_integration_system = RealTimeSignalIntegration()
    return _global_integration_system

def start_realtime_trading(symbols: List[str], trading_callback: Optional[Callable] = None) -> bool:
    """启动实时交易系统"""
    integration_system = get_integration_system()
    
    if trading_callback:
        integration_system.add_trading_callback(trading_callback)
    
    return integration_system.start_integration(symbols)

def stop_realtime_trading():
    """停止实时交易系统"""
    integration_system = get_integration_system()
    integration_system.stop_integration()

def get_trading_performance() -> Dict[str, Any]:
    """获取交易性能统计"""
    integration_system = get_integration_system()
    return integration_system.get_performance_stats()

def get_recent_trading_signals(limit: int = 10) -> List[Dict]:
    """获取最近的交易信号"""
    integration_system = get_integration_system()
    return integration_system.get_recent_signals(limit)

# 测试函数
def test_integration():
    """测试实时信号集成系统"""
    print("🧪 测试实时信号集成系统...")
    
    def on_trading_action(action: TradingAction):
        print(f"🎯 交易信号: {action.action.upper()} {action.quantity} {action.symbol} @ ${action.price:.2f}")
        print(f"   信号强度: {action.signal_strength:.2f} | 置信度: {action.confidence:.2f}")
        if action.metadata:
            strategies = action.metadata.get('contributing_strategies', [])
            print(f"   贡献策略: {', '.join(strategies)}")
    
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    # 启动系统
    success = start_realtime_trading(symbols, on_trading_action)
    
    if success:
        print("✅ 实时交易系统已启动")
        print("💡 系统将运行30秒进行测试...")
        
        try:
            time.sleep(30)
            
            # 显示性能统计
            stats = get_trading_performance()
            print(f"\n📈 性能统计:")
            print(f"  运行时间: {stats['runtime_seconds']:.1f}s")
            print(f"  生成信号: {stats['signals_generated']}")
            print(f"  执行交易: {stats['trades_executed']}")
            print(f"  信号转换率: {stats['trade_conversion_rate']:.1%}")
            print(f"  平均处理时间: {stats['avg_processing_time_ms']:.2f}ms")
            
            # 显示最近信号
            recent_signals = get_recent_trading_signals(5)
            if recent_signals:
                print(f"\n📊 最近信号:")
                for signal in recent_signals[-5:]:
                    print(f"  {signal['symbol']}: {signal['final_signal']} "
                          f"(强度: {signal['strength']:.2f}, 置信度: {signal['confidence']:.2f})")
            
        finally:
            stop_realtime_trading()
            print("✅ 测试完成")
    else:
        print("❌ 系统启动失败")

# 为兼容性添加别名
RealtimeSignalIntegration = RealTimeSignalIntegration

if __name__ == "__main__":
    test_integration()