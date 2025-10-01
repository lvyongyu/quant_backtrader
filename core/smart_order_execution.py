#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能订单执行系统
实现智能订单路由、分割执行、滑点控制和多种订单类型支持
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union, Callable, Tuple
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================= 订单模型 =================================

class OrderType(Enum):
    """订单类型"""
    MARKET = "market"          # 市价单
    LIMIT = "limit"           # 限价单
    STOP = "stop"             # 停损单
    STOP_LIMIT = "stop_limit" # 停损限价单
    CONDITIONAL = "conditional" # 条件单
    ICEBERG = "iceberg"       # 冰山单

class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"       # 待执行
    PARTIAL = "partial"       # 部分成交
    FILLED = "filled"         # 完全成交
    CANCELLED = "cancelled"   # 已取消
    REJECTED = "rejected"     # 被拒绝
    EXPIRED = "expired"       # 已过期

class ExecutionStrategy(Enum):
    """执行策略"""
    AGGRESSIVE = "aggressive"  # 激进执行
    PASSIVE = "passive"       # 被动执行
    BALANCED = "balanced"     # 平衡执行
    VWAP = "vwap"            # 成交量加权平均价格
    TWAP = "twap"            # 时间加权平均价格

@dataclass
class Order:
    """订单对象"""
    order_id: str
    symbol: str
    side: str                 # 'buy' or 'sell'
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # 限价单价格
    stop_price: Optional[float] = None  # 停损价格
    
    # 高级参数
    execution_strategy: ExecutionStrategy = ExecutionStrategy.BALANCED
    max_slippage: float = 0.01  # 最大滑点 (1%)
    time_in_force: str = "DAY"  # DAY, GTC, IOC, FOK
    min_quantity: float = 1.0   # 最小执行数量
    
    # 冰山单参数
    iceberg_visible_qty: Optional[float] = None
    
    # 条件单参数
    condition: Optional[str] = None  # 触发条件
    
    # 状态信息
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    
    # 时间信息
    created_time: float = 0.0
    updated_time: float = 0.0
    expiry_time: Optional[float] = None
    
    # 执行信息
    total_slippage: float = 0.0
    execution_cost: float = 0.0
    
    def __post_init__(self):
        if self.created_time == 0.0:
            self.created_time = time.time()
        self.updated_time = self.created_time

@dataclass
class OrderExecution:
    """订单执行记录"""
    execution_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: float
    slippage: float
    commission: float = 0.0
    
    # 市场信息
    bid_price: float = 0.0
    ask_price: float = 0.0
    spread: float = 0.0
    market_impact: float = 0.0

@dataclass
class SlippageControl:
    """滑点控制配置"""
    max_slippage_pct: float = 0.01  # 最大滑点百分比
    price_buffer_pct: float = 0.002  # 价格缓冲区
    market_impact_limit: float = 0.005  # 市场冲击限制
    adaptive_pricing: bool = True   # 自适应定价
    
    # 分割执行参数
    enable_order_splitting: bool = True
    max_order_size: float = 10000.0  # 最大单笔订单金额
    min_split_size: float = 100.0    # 最小分割大小
    split_time_interval: float = 2.0  # 分割执行间隔(秒)

# ================================= 智能订单执行引擎 =================================

class SmartOrderExecutionEngine:
    """智能订单执行引擎"""
    
    def __init__(self, slippage_control: SlippageControl = None):
        """初始化执行引擎"""
        self.slippage_control = slippage_control or SlippageControl()
        self.is_running = False
        
        # 订单管理
        self.active_orders: Dict[str, Order] = {}
        self.order_history: deque = deque(maxlen=10000)
        self.execution_history: deque = deque(maxlen=10000)
        
        # 市场数据缓存
        self.market_data: Dict[str, Dict] = {}
        self.price_history: Dict[str, deque] = {}
        
        # 执行策略
        self.execution_strategies: Dict[ExecutionStrategy, Callable] = {
            ExecutionStrategy.AGGRESSIVE: self._aggressive_execution,
            ExecutionStrategy.PASSIVE: self._passive_execution,
            ExecutionStrategy.BALANCED: self._balanced_execution,
            ExecutionStrategy.VWAP: self._vwap_execution,
            ExecutionStrategy.TWAP: self._twap_execution
        }
        
        # 性能统计
        self.total_orders = 0
        self.successful_executions = 0
        self.total_slippage = 0.0
        self.total_execution_time = 0.0
        
        # 回调函数
        self.execution_callbacks: List[Callable] = []
        self.order_status_callbacks: List[Callable] = []
        
        logger.info("✅ 智能订单执行引擎初始化完成")
    
    async def start(self):
        """启动执行引擎"""
        if self.is_running:
            logger.warning("⚠️ 执行引擎已在运行")
            return
        
        self.is_running = True
        
        # 启动后台任务
        monitoring_task = asyncio.create_task(self._order_monitoring_loop())
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("🚀 智能订单执行引擎启动成功")
        
        # 等待任务完成
        await asyncio.gather(monitoring_task, cleanup_task)
    
    async def stop(self):
        """停止执行引擎"""
        self.is_running = False
        
        # 取消所有活跃订单
        for order in list(self.active_orders.values()):
            await self.cancel_order(order.order_id, "系统停止")
        
        logger.info("🛑 智能订单执行引擎已停止")
    
    # ================================= 订单提交 =================================
    
    async def submit_order(self, symbol: str, side: str, quantity: float,
                          order_type: OrderType = OrderType.MARKET,
                          price: Optional[float] = None,
                          **kwargs) -> str:
        """提交订单"""
        start_time = time.perf_counter()
        
        try:
            # 生成订单ID
            order_id = f"{symbol}_{side}_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"
            
            # 创建订单对象
            order = Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                **kwargs
            )
            
            # 订单验证
            validation_result = await self._validate_order(order)
            if not validation_result[0]:
                order.status = OrderStatus.REJECTED
                self.order_history.append(order)
                logger.warning(f"❌ 订单被拒绝: {validation_result[1]}")
                return order_id
            
            # 滑点预检查
            slippage_check = await self._pre_execution_slippage_check(order)
            if not slippage_check[0]:
                order.status = OrderStatus.REJECTED
                self.order_history.append(order)
                logger.warning(f"❌ 滑点检查失败: {slippage_check[1]}")
                return order_id
            
            # 添加到活跃订单
            self.active_orders[order_id] = order
            self.total_orders += 1
            
            # 异步执行订单
            asyncio.create_task(self._execute_order(order))
            
            # 计算提交延迟
            submission_latency = (time.perf_counter() - start_time) * 1000
            if submission_latency > 50:  # 50ms阈值
                logger.warning(f"⚠️ 订单提交延迟过高: {submission_latency:.2f}ms")
            
            logger.info(f"📝 订单已提交: {order_id} ({side} {quantity} {symbol})")
            return order_id
            
        except Exception as e:
            logger.error(f"订单提交失败: {e}")
            return ""
    
    async def _validate_order(self, order: Order) -> Tuple[bool, str]:
        """订单验证"""
        try:
            # 基本验证
            if order.quantity <= 0:
                return False, "订单数量必须大于0"
            
            if order.side not in ['buy', 'sell']:
                return False, "订单方向必须是 buy 或 sell"
            
            # 限价单验证
            if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                if order.price is None or order.price <= 0:
                    return False, "限价单必须指定有效价格"
            
            # 停损单验证
            if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                if order.stop_price is None or order.stop_price <= 0:
                    return False, "停损单必须指定有效停损价格"
            
            # 市场数据验证
            if order.symbol not in self.market_data:
                return False, f"缺少 {order.symbol} 的市场数据"
            
            market_data = self.market_data[order.symbol]
            current_price = market_data.get('price', 0)
            
            if current_price <= 0:
                return False, f"{order.symbol} 当前价格无效"
            
            # 价格合理性检查
            if order.order_type == OrderType.LIMIT and order.price:
                price_deviation = abs(order.price - current_price) / current_price
                if price_deviation > 0.1:  # 10%偏差限制
                    return False, f"限价偏离市场价格过大: {price_deviation:.1%}"
            
            return True, "订单验证通过"
            
        except Exception as e:
            return False, f"订单验证错误: {str(e)}"
    
    async def _pre_execution_slippage_check(self, order: Order) -> Tuple[bool, str]:
        """执行前滑点检查"""
        try:
            market_data = self.market_data.get(order.symbol, {})
            current_price = market_data.get('price', 0)
            bid = market_data.get('bid', current_price * 0.999)
            ask = market_data.get('ask', current_price * 1.001)
            
            # 估算执行价格
            if order.side == 'buy':
                estimated_price = ask if order.order_type == OrderType.MARKET else order.price
                reference_price = current_price
            else:
                estimated_price = bid if order.order_type == OrderType.MARKET else order.price
                reference_price = current_price
            
            # 计算预期滑点
            if estimated_price and reference_price > 0:
                estimated_slippage = abs(estimated_price - reference_price) / reference_price
                
                if estimated_slippage > order.max_slippage:
                    return False, f"预期滑点过高: {estimated_slippage:.2%} > {order.max_slippage:.2%}"
            
            return True, "滑点检查通过"
            
        except Exception as e:
            return False, f"滑点检查错误: {str(e)}"
    
    # ================================= 订单执行 =================================
    
    async def _execute_order(self, order: Order):
        """执行订单"""
        start_time = time.perf_counter()
        
        try:
            logger.info(f"🔄 开始执行订单: {order.order_id}")
            
            # 选择执行策略
            execution_func = self.execution_strategies.get(
                order.execution_strategy, 
                self._balanced_execution
            )
            
            # 执行订单
            success = await execution_func(order)
            
            if success:
                order.status = OrderStatus.FILLED
                self.successful_executions += 1
                logger.info(f"✅ 订单执行成功: {order.order_id}")
            else:
                order.status = OrderStatus.REJECTED
                logger.warning(f"❌ 订单执行失败: {order.order_id}")
            
            # 更新统计
            execution_time = (time.perf_counter() - start_time) * 1000
            self.total_execution_time += execution_time
            
            if execution_time > 200:  # 200ms阈值
                logger.warning(f"⚠️ 订单执行延迟过高: {execution_time:.2f}ms")
            
            # 移动到历史记录
            order.updated_time = time.time()
            self.order_history.append(order)
            
            if order.order_id in self.active_orders:
                del self.active_orders[order.order_id]
            
            # 触发回调
            for callback in self.order_status_callbacks:
                try:
                    callback(order)
                except Exception as e:
                    logger.error(f"订单状态回调失败: {e}")
                    
        except Exception as e:
            logger.error(f"订单执行错误: {e}")
            order.status = OrderStatus.REJECTED
            order.updated_time = time.time()
            self.order_history.append(order)
            
            if order.order_id in self.active_orders:
                del self.active_orders[order.order_id]
    
    # ================================= 执行策略 =================================
    
    async def _aggressive_execution(self, order: Order) -> bool:
        """激进执行策略 - 快速成交"""
        try:
            market_data = self.market_data.get(order.symbol, {})
            current_price = market_data.get('price', 0)
            bid = market_data.get('bid', current_price * 0.999)
            ask = market_data.get('ask', current_price * 1.001)
            
            # 激进定价
            if order.side == 'buy':
                execution_price = ask * 1.001  # 略高于卖价
            else:
                execution_price = bid * 0.999  # 略低于买价
            
            # 执行订单
            success = await self._execute_at_price(order, execution_price)
            return success
            
        except Exception as e:
            logger.error(f"激进执行失败: {e}")
            return False
    
    async def _passive_execution(self, order: Order) -> bool:
        """被动执行策略 - 等待更好价格"""
        try:
            market_data = self.market_data.get(order.symbol, {})
            current_price = market_data.get('price', 0)
            bid = market_data.get('bid', current_price * 0.999)
            ask = market_data.get('ask', current_price * 1.001)
            
            # 被动定价
            if order.side == 'buy':
                execution_price = bid  # 按买价挂单
            else:
                execution_price = ask  # 按卖价挂单
            
            # 模拟等待
            await asyncio.sleep(0.5)
            
            # 执行订单
            success = await self._execute_at_price(order, execution_price)
            return success
            
        except Exception as e:
            logger.error(f"被动执行失败: {e}")
            return False
    
    async def _balanced_execution(self, order: Order) -> bool:
        """平衡执行策略 - 平衡速度和成本"""
        try:
            market_data = self.market_data.get(order.symbol, {})
            current_price = market_data.get('price', 0)
            bid = market_data.get('bid', current_price * 0.999)
            ask = market_data.get('ask', current_price * 1.001)
            
            # 平衡定价 - 中间价格
            if order.side == 'buy':
                execution_price = (current_price + ask) / 2
            else:
                execution_price = (current_price + bid) / 2
            
            # 执行订单
            success = await self._execute_at_price(order, execution_price)
            return success
            
        except Exception as e:
            logger.error(f"平衡执行失败: {e}")
            return False
    
    async def _vwap_execution(self, order: Order) -> bool:
        """VWAP执行策略 - 成交量加权平均价格"""
        try:
            # 简化版VWAP - 基于历史价格和成交量
            if order.symbol in self.price_history:
                prices = list(self.price_history[order.symbol])
                if len(prices) >= 10:
                    # 简单VWAP计算
                    vwap_price = np.mean(prices[-10:])
                    execution_price = vwap_price
                else:
                    # 降级到平衡执行
                    return await self._balanced_execution(order)
            else:
                return await self._balanced_execution(order)
            
            success = await self._execute_at_price(order, execution_price)
            return success
            
        except Exception as e:
            logger.error(f"VWAP执行失败: {e}")
            return False
    
    async def _twap_execution(self, order: Order) -> bool:
        """TWAP执行策略 - 时间加权平均价格"""
        try:
            # 简化版TWAP - 分时段执行
            total_quantity = order.quantity
            split_count = min(5, max(2, int(total_quantity / 100)))  # 分割次数
            split_quantity = total_quantity / split_count
            
            executed_quantity = 0.0
            total_cost = 0.0
            
            for i in range(split_count):
                market_data = self.market_data.get(order.symbol, {})
                current_price = market_data.get('price', 0)
                
                # 执行部分订单
                partial_success = await self._execute_at_price(
                    order, current_price, split_quantity
                )
                
                if partial_success:
                    executed_quantity += split_quantity
                    total_cost += split_quantity * current_price
                
                # 等待间隔
                if i < split_count - 1:
                    await asyncio.sleep(1.0)
            
            # 更新订单状态
            if executed_quantity > 0:
                order.filled_quantity = executed_quantity
                order.avg_fill_price = total_cost / executed_quantity
                return executed_quantity >= total_quantity * 0.95  # 95%执行率认为成功
            
            return False
            
        except Exception as e:
            logger.error(f"TWAP执行失败: {e}")
            return False
    
    async def _execute_at_price(self, order: Order, execution_price: float, 
                              quantity: Optional[float] = None) -> bool:
        """以指定价格执行订单"""
        try:
            exec_quantity = quantity or order.quantity
            market_data = self.market_data.get(order.symbol, {})
            current_price = market_data.get('price', execution_price)
            
            # 计算滑点
            slippage = abs(execution_price - current_price) / current_price
            
            # 滑点检查
            if slippage > order.max_slippage:
                logger.warning(f"⚠️ 滑点超限: {slippage:.2%} > {order.max_slippage:.2%}")
                return False
            
            # 创建执行记录
            execution = OrderExecution(
                execution_id=f"{order.order_id}_{int(time.time()*1000)}",
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=exec_quantity,
                price=execution_price,
                timestamp=time.time(),
                slippage=slippage,
                bid_price=market_data.get('bid', execution_price * 0.999),
                ask_price=market_data.get('ask', execution_price * 1.001),
                spread=market_data.get('ask', execution_price * 1.001) - 
                       market_data.get('bid', execution_price * 0.999)
            )
            
            # 更新订单状态
            order.filled_quantity += exec_quantity
            order.total_slippage += slippage * exec_quantity
            
            if order.filled_quantity >= order.quantity:
                order.avg_fill_price = (order.avg_fill_price * (order.filled_quantity - exec_quantity) + 
                                      execution_price * exec_quantity) / order.filled_quantity
            else:
                order.status = OrderStatus.PARTIAL
            
            # 保存执行记录
            self.execution_history.append(execution)
            self.total_slippage += slippage
            
            # 触发执行回调
            for callback in self.execution_callbacks:
                try:
                    callback(execution)
                except Exception as e:
                    logger.error(f"执行回调失败: {e}")
            
            logger.info(f"📈 订单执行: {order.symbol} {order.side} {exec_quantity}@{execution_price:.2f} (滑点: {slippage:.2%})")
            return True
            
        except Exception as e:
            logger.error(f"订单执行失败: {e}")
            return False
    
    # ================================= 订单管理 =================================
    
    async def cancel_order(self, order_id: str, reason: str = "") -> bool:
        """取消订单"""
        try:
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                order.status = OrderStatus.CANCELLED
                order.updated_time = time.time()
                
                # 移动到历史记录
                self.order_history.append(order)
                del self.active_orders[order_id]
                
                logger.info(f"🚫 订单已取消: {order_id} ({reason})")
                return True
            else:
                logger.warning(f"⚠️ 订单未找到: {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取订单状态"""
        # 先查活跃订单
        if order_id in self.active_orders:
            return self.active_orders[order_id]
        
        # 再查历史订单
        for order in reversed(self.order_history):
            if order.order_id == order_id:
                return order
        
        return None
    
    # ================================= 市场数据更新 =================================
    
    async def update_market_data(self, symbol: str, price: float, 
                               bid: Optional[float] = None, 
                               ask: Optional[float] = None,
                               volume: float = 0.0):
        """更新市场数据"""
        self.market_data[symbol] = {
            'price': price,
            'bid': bid or price * 0.999,
            'ask': ask or price * 1.001,
            'volume': volume,
            'timestamp': time.time()
        }
        
        # 更新价格历史
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=100)
        
        self.price_history[symbol].append(price)
    
    # ================================= 后台任务 =================================
    
    async def _order_monitoring_loop(self):
        """订单监控循环"""
        logger.info("📊 订单监控循环启动")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # 检查过期订单
                expired_orders = []
                for order_id, order in self.active_orders.items():
                    if order.expiry_time and current_time > order.expiry_time:
                        expired_orders.append(order_id)
                
                # 处理过期订单
                for order_id in expired_orders:
                    await self.cancel_order(order_id, "订单过期")
                
                # 监控间隔
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"订单监控错误: {e}")
                await asyncio.sleep(5.0)
    
    async def _cleanup_loop(self):
        """数据清理循环"""
        while self.is_running:
            try:
                # 清理过期的市场数据
                current_time = time.time()
                for symbol in list(self.market_data.keys()):
                    data = self.market_data[symbol]
                    if current_time - data['timestamp'] > 300:  # 5分钟过期
                        logger.warning(f"⚠️ 清理过期市场数据: {symbol}")
                        del self.market_data[symbol]
                
                # 每5分钟清理一次
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"数据清理错误: {e}")
                await asyncio.sleep(60)
    
    # ================================= 回调管理 =================================
    
    def add_execution_callback(self, callback: Callable):
        """添加执行回调"""
        self.execution_callbacks.append(callback)
    
    def add_order_status_callback(self, callback: Callable):
        """添加订单状态回调"""
        self.order_status_callbacks.append(callback)
    
    # ================================= 状态查询 =================================
    
    def get_execution_statistics(self) -> Dict:
        """获取执行统计"""
        avg_execution_time = (self.total_execution_time / max(1, self.total_orders))
        success_rate = (self.successful_executions / max(1, self.total_orders))
        avg_slippage = (self.total_slippage / max(1, self.successful_executions))
        
        recent_executions = list(self.execution_history)[-10:] if self.execution_history else []
        recent_orders = list(self.order_history)[-10:] if self.order_history else []
        
        return {
            'is_running': self.is_running,
            'total_orders': self.total_orders,
            'successful_executions': self.successful_executions,
            'success_rate': success_rate,
            'avg_execution_time_ms': avg_execution_time,
            'avg_slippage': avg_slippage,
            'active_orders_count': len(self.active_orders),
            'recent_executions': [asdict(e) for e in recent_executions],
            'recent_orders': [asdict(o) for o in recent_orders],
            'supported_symbols': list(self.market_data.keys())
        }

# ================================= 测试代码 =================================

async def test_smart_execution():
    """测试智能订单执行"""
    print("🧪 开始测试智能订单执行系统...")
    
    # 创建执行引擎
    slippage_control = SlippageControl(
        max_slippage_pct=0.005,  # 0.5%
        enable_order_splitting=True
    )
    
    engine = SmartOrderExecutionEngine(slippage_control)
    
    # 添加回调
    def execution_callback(execution):
        print(f"💰 订单执行: {execution.symbol} {execution.side} "
              f"{execution.quantity}@{execution.price:.2f} "
              f"(滑点: {execution.slippage:.2%})")
    
    def status_callback(order):
        print(f"📋 订单状态更新: {order.order_id} -> {order.status.value}")
    
    engine.add_execution_callback(execution_callback)
    engine.add_order_status_callback(status_callback)
    
    # 启动测试任务
    async def test_scenario():
        await asyncio.sleep(1)
        
        # 更新市场数据
        await engine.update_market_data("AAPL", 150.0, 149.8, 150.2, 10000)
        await engine.update_market_data("MSFT", 300.0, 299.5, 300.5, 8000)
        
        print("\n1. 测试市价单...")
        order_id1 = await engine.submit_order(
            "AAPL", "buy", 100, OrderType.MARKET,
            execution_strategy=ExecutionStrategy.AGGRESSIVE
        )
        
        await asyncio.sleep(1)
        
        print("\n2. 测试限价单...")
        order_id2 = await engine.submit_order(
            "MSFT", "sell", 50, OrderType.LIMIT, 
            price=301.0,
            execution_strategy=ExecutionStrategy.PASSIVE
        )
        
        await asyncio.sleep(1)
        
        print("\n3. 测试TWAP策略...")
        order_id3 = await engine.submit_order(
            "AAPL", "buy", 500, OrderType.MARKET,
            execution_strategy=ExecutionStrategy.TWAP
        )
        
        await asyncio.sleep(3)
        
        # 查看统计
        stats = engine.get_execution_statistics()
        print(f"\n📊 执行统计:")
        print(f"   总订单数: {stats['total_orders']}")
        print(f"   成功执行: {stats['successful_executions']}")
        print(f"   成功率: {stats['success_rate']:.1%}")
        print(f"   平均延迟: {stats['avg_execution_time_ms']:.2f}ms")
        print(f"   平均滑点: {stats['avg_slippage']:.2%}")
        print(f"   活跃订单: {stats['active_orders_count']}")
        
        await engine.stop()
    
    # 并行运行引擎和测试
    try:
        await asyncio.gather(
            engine.start(),
            test_scenario()
        )
    except Exception as e:
        print(f"测试出错: {e}")
    
    print("\n✅ 智能订单执行系统测试完成")

if __name__ == "__main__":
    asyncio.run(test_smart_execution())