#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML信号预测集成接口
将机器学习预测模型集成到实时交易流程中，使用真实数据源
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Callable, List
from dataclasses import asdict

try:
    from ml_signal_prediction import MLSignalPredictionSystem, MLPrediction
    ML_INTEGRATION_AVAILABLE = True
except ImportError:
    ML_INTEGRATION_AVAILABLE = False
    logging.warning("⚠️ ML信号预测模块不可用")

# 集成真实数据流
try:
    from data_stream_integration_real import get_data_stream_manager
    REAL_DATA_AVAILABLE = True
except ImportError:
    try:
        # 尝试相对导入
        from .data_stream_integration_real import get_data_stream_manager
        REAL_DATA_AVAILABLE = True
    except ImportError:
        REAL_DATA_AVAILABLE = False
        logging.warning("⚠️ 真实数据流不可用")

logger = logging.getLogger(__name__)

class MLIntegrationSystem:
    """ML信号预测集成系统 - 使用真实数据源"""
    
    def __init__(self, model_dir: str = "models"):
        """初始化ML集成系统"""
        if ML_INTEGRATION_AVAILABLE:
            self.ml_system = MLSignalPredictionSystem(model_dir)
        else:
            self.ml_system = None
        
        self.is_integrated = False
        self.prediction_callbacks: List[Callable] = []
        
        # 真实数据流集成
        self.data_stream_manager = None
        self.subscribed_symbols = set()
        
        # 性能统计
        self.total_predictions = 0
        self.successful_predictions = 0
        self.total_prediction_time = 0.0
        self.last_prediction_time = 0.0
        
        # 预测缓存
        self.latest_predictions: Dict[str, MLPrediction] = {}
        
        logger.info("✅ ML集成系统初始化完成（真实数据源模式）")
    
    async def start_integration(self, symbols: List[str] = None):
        """启动ML集成 - 自动连接真实数据源"""
        if not ML_INTEGRATION_AVAILABLE:
            logger.warning("⚠️ ML集成不可用，跳过启动")
            return False
        
        if self.is_integrated:
            logger.warning("⚠️ ML系统已集成")
            return True
        
        # 启动ML系统
        await self.ml_system.start()
        
        # 连接真实数据流
        if REAL_DATA_AVAILABLE and symbols:
            try:
                self.data_stream_manager = get_data_stream_manager()
                
                # 订阅真实数据更新
                for symbol in symbols:
                    self.data_stream_manager.subscribe_to_symbol(symbol, self._on_real_data_update)
                    self.subscribed_symbols.add(symbol)
                
                logger.info(f"✅ 已订阅真实数据源: {symbols}")
            except Exception as e:
                logger.warning(f"⚠️ 真实数据源连接失败，使用手动数据更新: {e}")
        
        self.is_integrated = True
        
        logger.info("🚀 ML信号预测集成启动成功（真实数据源模式）")
        return True
    
    def _on_real_data_update(self, symbol: str, data: Dict):
        """处理真实数据更新"""
        try:
            price = data.get('price', 0.0)
            volume = data.get('volume', 0.0)
            
            # 提取技术指标（如果有）
            technical_indicators = {}
            if 'rsi' in data:
                technical_indicators['rsi'] = data['rsi']
            if 'macd' in data:
                technical_indicators['macd'] = data['macd']
            if 'macd_signal' in data:
                technical_indicators['macd_signal'] = data['macd_signal']
            
            # 异步更新ML系统
            if self.ml_system:
                asyncio.create_task(
                    self.ml_system.update_market_data(symbol, price, volume, technical_indicators)
                )
                
        except Exception as e:
            logger.error(f"真实数据更新处理失败: {e}")
    
    async def stop_integration(self):
        """停止ML集成"""
        if not self.is_integrated:
            return
        
        # 停止真实数据订阅
        if self.data_stream_manager and self.subscribed_symbols:
            try:
                for symbol in self.subscribed_symbols:
                    self.data_stream_manager.unsubscribe_from_symbol(symbol, self._on_real_data_update)
                self.subscribed_symbols.clear()
                logger.info("✅ 已取消真实数据源订阅")
            except Exception as e:
                logger.warning(f"⚠️ 取消数据订阅失败: {e}")
        
        # 停止ML系统
        if self.ml_system:
            await self.ml_system.stop()
        
        self.is_integrated = False
        logger.info("🛑 ML信号预测集成已停止")
    
    # ================================= 数据更新接口 =================================
    
    async def update_market_data(self, symbol: str, price: float, volume: float = 0.0, 
                               technical_indicators: Dict = None):
        """更新市场数据 - 供数据引擎调用（手动模式或补充数据）"""
        if self.is_integrated and self.ml_system:
            await self.ml_system.update_market_data(symbol, price, volume, technical_indicators)
    
    def connect_to_real_data_stream(self, symbols: List[str]):
        """连接到真实数据流（运行时连接）"""
        if not REAL_DATA_AVAILABLE:
            logger.warning("⚠️ 真实数据流不可用")
            return False
        
        try:
            if not self.data_stream_manager:
                self.data_stream_manager = get_data_stream_manager()
            
            for symbol in symbols:
                if symbol not in self.subscribed_symbols:
                    self.data_stream_manager.subscribe_to_symbol(symbol, self._on_real_data_update)
                    self.subscribed_symbols.add(symbol)
            
            logger.info(f"✅ 已连接真实数据流: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"真实数据流连接失败: {e}")
            return False
    
    # ================================= 预测接口 =================================
    
    async def get_enhanced_prediction(self, symbol: str, 
                                    technical_indicators: Dict = None) -> Optional[Dict]:
        """获取增强型预测 - 供策略系统调用"""
        if not self.is_integrated or not self.ml_system:
            return self._get_simple_prediction(symbol, technical_indicators)
        
        start_time = time.perf_counter()
        
        try:
            self.total_predictions += 1
            
            # 获取ML预测
            prediction = await self.ml_system.get_ml_prediction(symbol, technical_indicators)
            
            if prediction:
                self.successful_predictions += 1
                
                # 更新缓存
                self.latest_predictions[symbol] = prediction
                
                # 计算处理时间
                processing_time = (time.perf_counter() - start_time) * 1000
                self.total_prediction_time += processing_time
                self.last_prediction_time = time.time()
                
                # 构建增强预测结果
                enhanced_prediction = {
                    'ml_available': True,
                    'prediction': asdict(prediction),
                    'processing_time_ms': processing_time,
                    'timestamp': prediction.timestamp,
                    
                    # 增强信息
                    'recommendation': self._generate_recommendation(prediction),
                    'risk_assessment': self._assess_risk(prediction),
                    'confidence_level': self._get_confidence_level(prediction.confidence),
                    'trading_signals': self._generate_trading_signals(prediction)
                }
                
                # 触发回调
                for callback in self.prediction_callbacks:
                    try:
                        callback(symbol, enhanced_prediction)
                    except Exception as e:
                        logger.error(f"ML预测回调失败: {e}")
                
                return enhanced_prediction
            
        except Exception as e:
            logger.error(f"ML预测获取失败: {e}")
        
        # 降级到简单预测
        return self._get_simple_prediction(symbol, technical_indicators)
    
    def _get_simple_prediction(self, symbol: str, technical_indicators: Dict = None) -> Dict:
        """简单预测（ML不可用时的降级方案）"""
        current_time = time.time()
        
        # 基于技术指标的简单分析
        if technical_indicators:
            rsi = technical_indicators.get('rsi', 50.0)
            macd = technical_indicators.get('macd', 0.0)
            macd_signal = technical_indicators.get('macd_signal', 0.0)
            
            # 简单信号强度计算
            signal_strength = 0.5
            if rsi < 30:
                signal_strength += 0.2  # 超卖
            elif rsi > 70:
                signal_strength += 0.2  # 超买
            
            if macd > macd_signal:
                signal_strength += 0.1
            else:
                signal_strength -= 0.1
            
            signal_strength = max(0.0, min(1.0, signal_strength))
            
            signal_direction = 'BUY' if signal_strength > 0.6 else 'SELL' if signal_strength < 0.4 else 'HOLD'
        else:
            signal_strength = 0.5
            signal_direction = 'HOLD'
        
        return {
            'ml_available': False,
            'prediction': {
                'timestamp': current_time,
                'symbol': symbol,
                'signal_strength': signal_strength,
                'signal_direction': signal_direction,
                'confidence': 0.5,
                'trend_short': 'SIDEWAYS',
                'model_accuracy': 0.5,
                'prediction_latency_ms': 1.0
            },
            'processing_time_ms': 1.0,
            'timestamp': current_time,
            'recommendation': f"{signal_direction} (简化模式)",
            'risk_assessment': '中等风险',
            'confidence_level': '中等',
            'trading_signals': {'action': signal_direction.lower(), 'strength': signal_strength}
        }
    
    # ================================= 增强功能 =================================
    
    def _generate_recommendation(self, prediction: MLPrediction) -> str:
        """生成交易建议"""
        direction = prediction.signal_direction
        strength = prediction.signal_strength
        confidence = prediction.confidence
        
        if direction == 'BUY':
            if strength > 0.8 and confidence > 0.8:
                return "强烈建议买入"
            elif strength > 0.6 and confidence > 0.6:
                return "建议买入"
            else:
                return "谨慎买入"
        elif direction == 'SELL':
            if strength > 0.8 and confidence > 0.8:
                return "强烈建议卖出"
            elif strength > 0.6 and confidence > 0.6:
                return "建议卖出"
            else:
                return "谨慎卖出"
        else:
            return "建议持有观望"
    
    def _assess_risk(self, prediction: MLPrediction) -> str:
        """评估风险水平"""
        risk_score = prediction.risk_score
        volatility = prediction.volatility_prediction
        
        if risk_score > 0.7 or volatility > 0.03:
            return "高风险"
        elif risk_score > 0.4 or volatility > 0.015:
            return "中等风险"
        else:
            return "低风险"
    
    def _get_confidence_level(self, confidence: float) -> str:
        """获取置信度级别"""
        if confidence > 0.8:
            return "高置信度"
        elif confidence > 0.6:
            return "中等置信度"
        elif confidence > 0.4:
            return "低置信度"
        else:
            return "极低置信度"
    
    def _generate_trading_signals(self, prediction: MLPrediction) -> Dict:
        """生成交易信号"""
        return {
            'action': prediction.signal_direction.lower(),
            'strength': prediction.signal_strength,
            'confidence': prediction.confidence,
            'urgency': 'high' if prediction.signal_strength > 0.8 else 'medium' if prediction.signal_strength > 0.6 else 'low',
            'price_targets': {
                '1m': prediction.predicted_price_1m,
                '5m': prediction.predicted_price_5m,
                '15m': prediction.predicted_price_15m
            },
            'risk_level': prediction.risk_score,
            'trend': prediction.trend_short.lower()
        }
    
    # ================================= 回调管理 =================================
    
    def add_prediction_callback(self, callback: Callable):
        """添加预测回调"""
        self.prediction_callbacks.append(callback)
    
    # ================================= 状态查询 =================================
    
    def get_integration_status(self) -> Dict:
        """获取集成状态"""
        avg_prediction_time = (self.total_prediction_time / self.total_predictions 
                             if self.total_predictions > 0 else 0.0)
        
        success_rate = (self.successful_predictions / self.total_predictions 
                       if self.total_predictions > 0 else 0.0)
        
        base_status = {
            'integration_active': self.is_integrated,
            'ml_available': ML_INTEGRATION_AVAILABLE,
            'real_data_available': REAL_DATA_AVAILABLE,
            'real_data_connected': self.data_stream_manager is not None,
            'subscribed_symbols': list(self.subscribed_symbols),
            'total_predictions': self.total_predictions,
            'successful_predictions': self.successful_predictions,
            'success_rate': success_rate,
            'avg_prediction_time_ms': avg_prediction_time,
            'last_prediction_time': self.last_prediction_time,
            'cached_predictions': len(self.latest_predictions)
        }
        
        if self.is_integrated and self.ml_system:
            ml_status = self.ml_system.get_system_status()
            base_status.update({
                'ml_system_status': ml_status
            })
        
        return base_status
    
    def print_ml_summary(self):
        """打印ML系统摘要"""
        status = self.get_integration_status()
        
        print("\n" + "="*50)
        print("🤖 ML信号预测系统状态")
        print("="*50)
        
        # 基本状态
        status_emoji = "🟢" if status['integration_active'] else "🔴"
        ml_emoji = "✅" if status['ml_available'] else "❌"
        data_emoji = "✅" if status['real_data_connected'] else "🔶" if status['real_data_available'] else "❌"
        
        print(f"集成状态: {status_emoji} {'激活' if status['integration_active'] else '未激活'}")
        print(f"ML可用性: {ml_emoji} {'可用' if status['ml_available'] else '不可用'}")
        print(f"真实数据: {data_emoji} {'已连接' if status['real_data_connected'] else '可用但未连接' if status['real_data_available'] else '不可用'}")
        
        # 数据订阅
        if status['subscribed_symbols']:
            print(f"订阅股票: {', '.join(status['subscribed_symbols'])}")
        
        # 性能统计
        print(f"\n📊 性能统计:")
        print(f"   总预测数: {status['total_predictions']}")
        print(f"   成功预测: {status['successful_predictions']}")
        print(f"   成功率:   {status['success_rate']:.1%}")
        print(f"   平均延迟: {status['avg_prediction_time_ms']:.2f}ms")
        
        # 最近预测
        if status['cached_predictions'] > 0:
            print(f"\n🎯 最近预测:")
            for symbol, prediction in list(self.latest_predictions.items())[-3:]:
                pred_time = time.strftime('%H:%M:%S', time.localtime(prediction.timestamp))
                print(f"   {symbol}: {prediction.signal_direction} "
                      f"(强度:{prediction.signal_strength:.2f}, "
                      f"置信度:{prediction.confidence:.2f}) [{pred_time}]")
        
        # ML系统详细状态
        if self.is_integrated and 'ml_system_status' in status:
            ml_status = status['ml_system_status']
            print(f"\n🔬 ML模型状态:")
            print(f"   模型延迟: {ml_status.get('avg_prediction_latency_ms', 0):.2f}ms")
            print(f"   缓存股票: {ml_status.get('cached_symbols', 0)}")
            
            model_status = ml_status.get('model_status', {})
            trained_models = sum(1 for trained in model_status.values() if trained)
            print(f"   训练模型: {trained_models}/{len(model_status)}")
        
        print("="*50)

# ================================= 全局实例管理 =================================

_global_ml_integration: Optional[MLIntegrationSystem] = None

def get_ml_integration() -> MLIntegrationSystem:
    """获取全局ML集成实例"""
    global _global_ml_integration
    if _global_ml_integration is None:
        _global_ml_integration = MLIntegrationSystem()
    return _global_ml_integration

async def start_ml_integration(symbols: List[str] = None):
    """启动全局ML集成 - 自动连接真实数据源"""
    integration = get_ml_integration()
    success = await integration.start_integration(symbols or ['AAPL', 'MSFT', 'GOOGL', 'TSLA'])
    return integration, success

async def stop_ml_integration():
    """停止全局ML集成"""
    integration = get_ml_integration()
    await integration.stop_integration()

def print_ml_status():
    """打印ML状态"""
    integration = get_ml_integration()
    integration.print_ml_summary()

# ================================= 测试代码 =================================

async def test_ml_integration():
    """测试ML集成 - 使用真实数据源"""
    print("🧪 测试ML信号预测集成（真实数据源模式）...")
    
    # 启动集成
    symbols = ["AAPL", "MSFT"]
    integration, success = await start_ml_integration(symbols)
    
    if success:
        print("✅ ML集成启动成功")
        
        # 等待真实数据
        print("⏳ 等待真实数据流...")
        await asyncio.sleep(3)
        
        # 模拟技术指标（补充数据）
        technical_indicators = {
            'rsi': 55.0,
            'macd': 0.5,
            'macd_signal': 0.3
        }
        
        # 测试每个股票的预测
        for symbol in symbols:
            print(f"\n🎯 获取 {symbol} 预测:")
            
            # 手动更新一些数据（模拟补充技术指标）
            await integration.update_market_data(symbol, 150.0, 1000000, technical_indicators)
            
            # 获取预测
            prediction = await integration.get_enhanced_prediction(symbol, technical_indicators)
            
            if prediction:
                print(f"   ML可用: {prediction['ml_available']}")
                print(f"   建议: {prediction['recommendation']}")
                print(f"   风险评估: {prediction['risk_assessment']}")
                print(f"   置信度: {prediction['confidence_level']}")
                print(f"   处理时间: {prediction['processing_time_ms']:.2f}ms")
        
        # 显示状态
        print("\n📊 系统状态:")
        integration.print_ml_summary()
        
    else:
        print("❌ ML集成启动失败")
    
    await stop_ml_integration()
    print("\n✅ ML集成测试完成")

# 为兼容性添加别名
MLIntegration = MLIntegrationSystem

if __name__ == "__main__":
    asyncio.run(test_ml_integration())