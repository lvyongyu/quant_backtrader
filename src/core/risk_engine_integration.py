#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险引擎集成模块
将实时风险引擎集成到现有交易系统中
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Callable
from realtime_risk_engine import RealtimeRiskEngine, RiskLimits, RiskAlert

logger = logging.getLogger(__name__)

class RiskEngineIntegration:
    """风险引擎集成类 - 桥接风险引擎与交易系统"""
    
    def __init__(self, risk_limits: Optional[RiskLimits] = None):
        """初始化风险引擎集成"""
        self.risk_engine = RealtimeRiskEngine(risk_limits)
        self.is_integrated = False
        self.trade_blocked = False
        
        # 集成状态
        self.total_alerts = 0
        self.critical_alerts = 0
        self.last_alert_time = 0.0
        
        # 设置回调
        self.risk_engine.add_alert_callback(self._handle_risk_alert)
        self.risk_engine.add_emergency_callback(self._handle_emergency)
        
        logger.info("✅ 风险引擎集成初始化完成")
    
    async def start_integration(self):
        """启动风险引擎集成"""
        if self.is_integrated:
            logger.warning("⚠️ 风险引擎已集成")
            return
        
        # 启动风险引擎 (后台任务)
        self.risk_task = asyncio.create_task(self.risk_engine.start())
        self.is_integrated = True
        
        logger.info("🚀 风险引擎集成启动成功")
    
    async def stop_integration(self):
        """停止风险引擎集成"""
        if not self.is_integrated:
            return
        
        await self.risk_engine.stop()
        if hasattr(self, 'risk_task'):
            self.risk_task.cancel()
        
        self.is_integrated = False
        logger.info("🛑 风险引擎集成已停止")
    
    # ================================= 交易前检查 =================================
    
    async def pre_trade_check(self, symbol: str, order_size: float, order_price: float) -> tuple:
        """交易前风险检查 - 供交易系统调用"""
        if not self.is_integrated:
            return True, "风险引擎未启动"
        
        if self.trade_blocked:
            return False, "交易被风险控制阻止"
        
        # 调用风险引擎检查
        can_trade, message = await self.risk_engine.check_pre_trade_risk(
            symbol, order_size, order_price
        )
        
        if not can_trade:
            logger.warning(f"🚫 交易被阻止: {symbol} {order_size}@{order_price} - {message}")
        
        return can_trade, message
    
    # ================================= 数据更新 =================================
    
    async def update_market_data(self, symbol: str, price: float, volume: float = 0.0):
        """更新市场数据 - 供数据引擎调用"""
        if self.is_integrated:
            await self.risk_engine.update_market_data(symbol, price, volume)
    
    async def update_position(self, symbol: str, position_size: float, trade_price: float):
        """更新仓位 - 供交易执行系统调用"""
        if self.is_integrated:
            await self.risk_engine.update_position(symbol, position_size, trade_price)
    
    # ================================= 回调处理 =================================
    
    def _handle_risk_alert(self, alert: RiskAlert):
        """处理风险警报"""
        self.total_alerts += 1
        self.last_alert_time = time.time()
        
        if alert.alert_type == "CRITICAL":
            self.critical_alerts += 1
            
            # 严重警报时暂时阻止交易
            if alert.severity >= 8:
                self.trade_blocked = True
                logger.critical(f"🚨 严重风险警报，暂停交易: {alert.message}")
        
        # 输出警报信息
        risk_level = "🟢" if alert.alert_type == "WARNING" else "🔴"
        print(f"{risk_level} 风险警报 [{alert.alert_type}]: {alert.message}")
        print(f"   股票: {alert.symbol} | 严重程度: {alert.severity}/10")
        print(f"   建议: {alert.action_required}")
    
    def _handle_emergency(self, alert: RiskAlert):
        """处理紧急停止"""
        self.trade_blocked = True
        
        print("🆘" * 10)
        print(f"紧急停止触发: {alert.message}")
        print("所有交易活动已暂停！")
        print("🆘" * 10)
        
        # 可以在这里添加额外的紧急措施
        # 例如：发送邮件/短信通知、记录日志、平仓等
    
    # ================================= 状态查询 =================================
    
    def get_integration_status(self) -> Dict:
        """获取集成状态"""
        engine_status = self.risk_engine.get_risk_status() if self.is_integrated else {}
        
        return {
            'integration_active': self.is_integrated,
            'trade_blocked': self.trade_blocked,
            'total_alerts': self.total_alerts,
            'critical_alerts': self.critical_alerts,
            'last_alert_time': self.last_alert_time,
            'engine_status': engine_status
        }
    
    def unblock_trading(self, reason: str = "手动解除"):
        """解除交易阻止"""
        if self.trade_blocked:
            self.trade_blocked = False
            logger.info(f"✅ 交易阻止已解除: {reason}")
    
    # ================================= 快速状态显示 =================================
    
    def print_risk_summary(self):
        """打印风险摘要"""
        if not self.is_integrated:
            print("❌ 风险引擎未启动")
            return
        
        status = self.get_integration_status()
        engine_status = status['engine_status']
        
        print("\n" + "="*50)
        print("📊 实时风险引擎状态")
        print("="*50)
        
        # 引擎状态
        status_emoji = "🟢" if engine_status.get('engine_status') == 'RUNNING' else "🔴"
        emergency_emoji = "🆘" if engine_status.get('emergency_stop', False) else "✅"
        trade_emoji = "🚫" if self.trade_blocked else "✅"
        
        print(f"引擎状态: {status_emoji} {engine_status.get('engine_status', 'UNKNOWN')}")
        print(f"紧急停止: {emergency_emoji} {'是' if engine_status.get('emergency_stop', False) else '否'}")
        print(f"交易状态: {trade_emoji} {'阻止' if self.trade_blocked else '正常'}")
        
        # 组合信息
        print(f"\n💰 组合信息:")
        print(f"   组合价值: ${engine_status.get('portfolio_value', 0):,.2f}")
        print(f"   日损益:   ${engine_status.get('daily_pnl', 0):,.2f}")
        print(f"   总损益:   ${engine_status.get('total_pnl', 0):,.2f}")
        print(f"   最大回撤: {engine_status.get('max_drawdown', 0):.2%}")
        
        # 仓位信息
        positions = engine_status.get('current_positions', {})
        if positions:
            print(f"\n📈 当前仓位:")
            for symbol, size in positions.items():
                print(f"   {symbol}: {size}")
        else:
            print(f"\n📈 当前仓位: 无")
        
        # 警报统计
        print(f"\n⚠️ 风险警报:")
        print(f"   总警报数: {self.total_alerts}")
        print(f"   严重警报: {self.critical_alerts}")
        
        recent_alerts = engine_status.get('recent_alerts', [])
        if recent_alerts:
            print(f"   最近警报: {recent_alerts[-1].get('message', 'N/A')}")
        
        # 风险限制
        risk_limits = engine_status.get('risk_limits', {})
        print(f"\n🛡️ 风险限制:")
        print(f"   最大仓位: ${risk_limits.get('max_position_size', 0):,.0f}")
        print(f"   最大日损: ${risk_limits.get('max_daily_loss', 0):,.0f}")
        print(f"   最大波动: {risk_limits.get('max_volatility', 0):.1%}")
        
        print("="*50)

# ================================= 便捷函数 =================================

# 全局风险引擎实例
_global_risk_integration: Optional[RiskEngineIntegration] = None

def get_risk_integration() -> RiskEngineIntegration:
    """获取全局风险引擎集成实例"""
    global _global_risk_integration
    if _global_risk_integration is None:
        _global_risk_integration = RiskEngineIntegration()
    return _global_risk_integration

async def start_risk_engine():
    """启动全局风险引擎"""
    integration = get_risk_integration()
    await integration.start_integration()
    return integration

async def stop_risk_engine():
    """停止全局风险引擎"""
    integration = get_risk_integration()
    await integration.stop_integration()

def print_risk_status():
    """打印风险状态"""
    integration = get_risk_integration()
    integration.print_risk_summary()

# ================================= 测试代码 =================================

async def test_integration():
    """测试风险引擎集成"""
    print("🧪 测试风险引擎集成...")
    
    # 启动集成
    integration = await start_risk_engine()
    
    # 等待引擎启动
    await asyncio.sleep(1)
    
    # 模拟交易检查
    print("\n1. 测试交易前检查...")
    can_trade, msg = await integration.pre_trade_check("AAPL", 100, 150.0)
    print(f"   交易检查结果: {can_trade} - {msg}")
    
    # 模拟市场数据更新
    print("\n2. 更新市场数据...")
    await integration.update_market_data("AAPL", 150.0, 10000)
    
    if can_trade:
        await integration.update_position("AAPL", 100, 150.0)
    
    # 打印状态
    print("\n3. 风险状态:")
    integration.print_risk_summary()
    
    # 停止集成
    await stop_risk_engine()
    print("\n✅ 集成测试完成")

if __name__ == "__main__":
    asyncio.run(test_integration())