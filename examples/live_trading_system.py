#!/usr/bin/env python3
"""
实盘交易接口系统
Live Trading Interface System

提供券商API集成、订单管理和风险控制的完整实盘交易解决方案
"""

import backtrader as bt
import threading
import time
import datetime
import json
import logging
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import queue
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """订单方向枚举"""
    BUY = "buy"
    SELL = "sell"

@dataclass
class LiveOrder:
    """实盘订单数据类"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    timestamp: datetime.datetime = None
    broker_order_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now()

@dataclass
class LivePosition:
    """实盘持仓数据类"""
    symbol: str
    quantity: float
    avg_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    timestamp: datetime.datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now()

@dataclass
class AccountInfo:
    """账户信息数据类"""
    account_id: str
    cash_balance: float
    buying_power: float
    total_value: float
    day_pnl: float
    total_pnl: float
    positions: List[LivePosition]
    timestamp: datetime.datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.datetime.now()

class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Dict):
        self.max_position_size = config.get('max_position_size', 0.1)  # 最大单只股票仓位10%
        self.max_daily_loss = config.get('max_daily_loss', 0.02)       # 最大日亏损2%
        self.max_total_exposure = config.get('max_total_exposure', 0.8) # 最大总仓位80%
        self.min_cash_reserve = config.get('min_cash_reserve', 0.1)     # 最小现金储备10%
        
        self.daily_pnl = 0.0
        self.initial_account_value = 0.0
        self.position_limits = {}
        
        logger.info(f"🛡️ 风险管理器初始化:")
        logger.info(f"   最大单仓位: {self.max_position_size*100}%")
        logger.info(f"   最大日亏损: {self.max_daily_loss*100}%")
        logger.info(f"   最大总仓位: {self.max_total_exposure*100}%")
    
    def set_initial_account_value(self, value: float):
        """设置初始账户价值"""
        self.initial_account_value = value
        logger.info(f"💰 设置初始账户价值: ${value:,.2f}")
    
    def check_order_risk(self, order: LiveOrder, account: AccountInfo) -> tuple[bool, str]:
        """检查订单风险"""
        
        # 检查日亏损限制
        if account.day_pnl < -self.max_daily_loss * self.initial_account_value:
            return False, f"超过日亏损限制: {account.day_pnl:.2f}"
        
        # 检查现金储备
        if order.side == OrderSide.BUY:
            required_cash = order.quantity * (order.price or 0)
            available_cash = account.cash_balance
            
            if required_cash > available_cash * (1 - self.min_cash_reserve):
                return False, f"现金不足，需要保留{self.min_cash_reserve*100}%储备"
        
        # 检查单股票仓位限制
        if order.side == OrderSide.BUY:
            current_position = 0
            for pos in account.positions:
                if pos.symbol == order.symbol:
                    current_position = pos.quantity
                    break
            
            new_position_value = (current_position + order.quantity) * (order.price or 0)
            max_position_value = account.total_value * self.max_position_size
            
            if new_position_value > max_position_value:
                return False, f"超过单股票仓位限制: {order.symbol}"
        
        # 检查总仓位限制
        total_position_value = sum(pos.market_value for pos in account.positions)
        if order.side == OrderSide.BUY:
            total_position_value += order.quantity * (order.price or 0)
        
        if total_position_value > account.total_value * self.max_total_exposure:
            return False, f"超过总仓位限制: {total_position_value/account.total_value*100:.1f}%"
        
        return True, "风险检查通过"
    
    def update_daily_pnl(self, pnl: float):
        """更新当日盈亏"""
        self.daily_pnl = pnl
        
        # 检查是否触发风险警报
        if self.initial_account_value > 0:
            loss_pct = abs(pnl) / self.initial_account_value
            if pnl < 0 and loss_pct > self.max_daily_loss * 0.8:  # 80%阈值警报
                logger.warning(f"⚠️ 日亏损接近限制: {loss_pct*100:.2f}%")

class MockBrokerAPI:
    """模拟券商API"""
    
    def __init__(self, initial_cash: float = 100000):
        self.account_id = "MOCK_ACCOUNT_001"
        self.cash_balance = initial_cash
        self.positions = {}
        self.orders = {}
        self.order_counter = 1
        self.connected = False
        
        # 模拟市场价格
        self.market_prices = {
            'AAPL': 150.0,
            'GOOGL': 2800.0,
            'MSFT': 350.0,
            'TSLA': 200.0,
            'NVDA': 800.0
        }
        
        # 价格更新线程
        self.price_update_thread = None
        self.running = False
        
    def connect(self) -> bool:
        """连接到券商"""
        try:
            logger.info("🔌 连接到模拟券商...")
            time.sleep(1)  # 模拟连接延迟
            self.connected = True
            self.running = True
            
            # 启动价格更新线程
            self.price_update_thread = threading.Thread(target=self._update_prices)
            self.price_update_thread.daemon = True
            self.price_update_thread.start()
            
            logger.info("✅ 券商连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ 券商连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.price_update_thread:
            self.price_update_thread.join()
        self.connected = False
        logger.info("🔌 已断开券商连接")
    
    def _update_prices(self):
        """更新市场价格（模拟）"""
        import random
        
        while self.running:
            for symbol in self.market_prices:
                # 模拟价格波动
                change_pct = random.gauss(0, 0.005)  # 0.5%标准差
                self.market_prices[symbol] *= (1 + change_pct)
                self.market_prices[symbol] = max(1.0, self.market_prices[symbol])
            
            time.sleep(5)  # 每5秒更新一次
    
    def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        if not self.connected:
            raise Exception("未连接到券商")
        
        positions = []
        total_position_value = 0
        total_unrealized_pnl = 0
        
        for symbol, pos_data in self.positions.items():
            current_price = self.market_prices.get(symbol, pos_data['avg_price'])
            market_value = pos_data['quantity'] * current_price
            unrealized_pnl = (current_price - pos_data['avg_price']) * pos_data['quantity']
            
            position = LivePosition(
                symbol=symbol,
                quantity=pos_data['quantity'],
                avg_price=pos_data['avg_price'],
                market_value=market_value,
                unrealized_pnl=unrealized_pnl
            )
            positions.append(position)
            
            total_position_value += market_value
            total_unrealized_pnl += unrealized_pnl
        
        total_value = self.cash_balance + total_position_value
        
        return AccountInfo(
            account_id=self.account_id,
            cash_balance=self.cash_balance,
            buying_power=self.cash_balance,
            total_value=total_value,
            day_pnl=total_unrealized_pnl,  # 简化为未实现盈亏
            total_pnl=total_unrealized_pnl,
            positions=positions
        )
    
    def submit_order(self, order: LiveOrder) -> str:
        """提交订单"""
        if not self.connected:
            raise Exception("未连接到券商")
        
        # 生成订单ID
        broker_order_id = f"ORD_{self.order_counter:06d}"
        self.order_counter += 1
        
        # 模拟订单处理
        order.broker_order_id = broker_order_id
        order.status = OrderStatus.SUBMITTED
        
        # 存储订单
        self.orders[broker_order_id] = order
        
        # 模拟订单执行（简化为立即成交）
        threading.Thread(target=self._process_order, args=(broker_order_id,)).start()
        
        logger.info(f"📋 订单已提交: {broker_order_id} - {order.side.value} {order.quantity} {order.symbol}")
        
        return broker_order_id
    
    def _process_order(self, broker_order_id: str):
        """处理订单执行（模拟）"""
        time.sleep(1)  # 模拟处理延迟
        
        order = self.orders.get(broker_order_id)
        if not order:
            return
        
        # 模拟订单执行
        current_price = self.market_prices.get(order.symbol, order.price or 100.0)
        
        # 添加一点滑点
        import random
        slippage = random.gauss(0, 0.001)  # 0.1%滑点
        execution_price = current_price * (1 + slippage)
        
        # 检查余额（买入时）
        if order.side == OrderSide.BUY:
            required_cash = order.quantity * execution_price
            if required_cash > self.cash_balance:
                order.status = OrderStatus.REJECTED
                logger.warning(f"❌ 订单被拒绝: 现金不足 {broker_order_id}")
                return
        
        # 执行订单
        order.status = OrderStatus.COMPLETED
        order.filled_quantity = order.quantity
        order.avg_fill_price = execution_price
        
        # 更新持仓和现金
        if order.side == OrderSide.BUY:
            self.cash_balance -= order.quantity * execution_price
            
            if order.symbol in self.positions:
                # 更新现有持仓
                pos = self.positions[order.symbol]
                total_quantity = pos['quantity'] + order.quantity
                total_cost = (pos['quantity'] * pos['avg_price']) + (order.quantity * execution_price)
                pos['avg_price'] = total_cost / total_quantity
                pos['quantity'] = total_quantity
            else:
                # 新建持仓
                self.positions[order.symbol] = {
                    'quantity': order.quantity,
                    'avg_price': execution_price
                }
        
        else:  # SELL
            self.cash_balance += order.quantity * execution_price
            
            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                pos['quantity'] -= order.quantity
                
                if pos['quantity'] <= 0:
                    del self.positions[order.symbol]
        
        logger.info(f"✅ 订单执行完成: {broker_order_id} @ ${execution_price:.2f}")
    
    def cancel_order(self, broker_order_id: str) -> bool:
        """取消订单"""
        if broker_order_id in self.orders:
            order = self.orders[broker_order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]:
                order.status = OrderStatus.CANCELLED
                logger.info(f"🚫 订单已取消: {broker_order_id}")
                return True
        return False
    
    def get_order_status(self, broker_order_id: str) -> Optional[LiveOrder]:
        """获取订单状态"""
        return self.orders.get(broker_order_id)
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        return self.market_prices.get(symbol, 0.0)

class LiveTradingEngine:
    """实盘交易引擎"""
    
    def __init__(self, broker_api, risk_config: Dict = None):
        self.broker_api = broker_api
        self.risk_manager = RiskManager(risk_config or {})
        
        # 订单管理
        self.pending_orders = {}
        self.order_callbacks = {}
        
        # 状态监控
        self.running = False
        self.monitor_thread = None
        
        # 事件队列
        self.event_queue = queue.Queue()
        
        logger.info("🚀 实盘交易引擎初始化完成")
    
    def start(self) -> bool:
        """启动交易引擎"""
        try:
            # 连接券商
            if not self.broker_api.connect():
                return False
            
            # 获取初始账户信息
            account = self.broker_api.get_account_info()
            self.risk_manager.set_initial_account_value(account.total_value)
            
            # 启动监控线程
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_orders)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            logger.info("🎯 实盘交易引擎启动成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 交易引擎启动失败: {e}")
            return False
    
    def stop(self):
        """停止交易引擎"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        self.broker_api.disconnect()
        logger.info("🛑 实盘交易引擎已停止")
    
    def _monitor_orders(self):
        """监控订单状态"""
        while self.running:
            try:
                # 检查待处理订单
                for order_id in list(self.pending_orders.keys()):
                    order = self.broker_api.get_order_status(order_id)
                    if order and order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                        # 订单结束，移除监控
                        del self.pending_orders[order_id]
                        
                        # 调用回调函数
                        if order_id in self.order_callbacks:
                            callback = self.order_callbacks[order_id]
                            try:
                                callback(order)
                            except Exception as e:
                                logger.error(f"订单回调执行失败: {e}")
                            del self.order_callbacks[order_id]
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"订单监控异常: {e}")
                time.sleep(5)
    
    def submit_order(self, symbol: str, side: OrderSide, quantity: float, 
                    order_type: OrderType = OrderType.MARKET, 
                    price: Optional[float] = None,
                    callback: Optional[Callable] = None) -> Optional[str]:
        """提交订单"""
        
        try:
            # 创建订单对象
            order = LiveOrder(
                order_id=f"CLIENT_{int(time.time()*1000)}",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price
            )
            
            # 获取当前账户信息
            account = self.broker_api.get_account_info()
            
            # 风险检查
            risk_ok, risk_msg = self.risk_manager.check_order_risk(order, account)
            if not risk_ok:
                logger.warning(f"🛡️ 订单被风控拒绝: {risk_msg}")
                return None
            
            # 提交到券商
            broker_order_id = self.broker_api.submit_order(order)
            
            # 添加到监控列表
            self.pending_orders[broker_order_id] = order
            if callback:
                self.order_callbacks[broker_order_id] = callback
            
            logger.info(f"✅ 订单提交成功: {symbol} {side.value} {quantity}")
            return broker_order_id
            
        except Exception as e:
            logger.error(f"❌ 订单提交失败: {e}")
            return None
    
    def cancel_order(self, broker_order_id: str) -> bool:
        """取消订单"""
        return self.broker_api.cancel_order(broker_order_id)
    
    def get_account_status(self) -> AccountInfo:
        """获取账户状态"""
        account = self.broker_api.get_account_info()
        self.risk_manager.update_daily_pnl(account.day_pnl)
        return account
    
    def get_position(self, symbol: str) -> Optional[LivePosition]:
        """获取指定股票持仓"""
        account = self.get_account_status()
        for pos in account.positions:
            if pos.symbol == symbol:
                return pos
        return None

class LiveTradingStrategy(bt.Strategy):
    """实盘交易策略基类"""
    
    def __init__(self):
        self.trading_engine = None
        self.position_sizes = {}
        self.last_prices = {}
        
        # 技术指标
        self.sma_short = bt.indicators.SMA(period=10)
        self.sma_long = bt.indicators.SMA(period=20)
        self.rsi = bt.indicators.RSI(period=14)
        
        print("🎯 实盘交易策略初始化")
    
    def set_trading_engine(self, engine: LiveTradingEngine):
        """设置交易引擎"""
        self.trading_engine = engine
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status == order.Completed:
            if order.isbuy():
                print(f"✅ 买入执行: {order.data._name} @ ${order.executed.price:.2f}")
            else:
                print(f"✅ 卖出执行: {order.data._name} @ ${order.executed.price:.2f}")
    
    def next(self):
        """策略主逻辑"""
        if not self.trading_engine:
            return
        
        symbol = self.data._name
        current_price = self.data.close[0]
        self.last_prices[symbol] = current_price
        
        # 检查技术信号
        if len(self) < 20:  # 等待足够数据
            return
        
        # 获取当前持仓
        position = self.trading_engine.get_position(symbol)
        current_quantity = position.quantity if position else 0
        
        # 简单策略：SMA交叉
        if (self.sma_short[0] > self.sma_long[0] and 
            self.sma_short[-1] <= self.sma_long[-1] and 
            current_quantity == 0):
            
            # 买入信号
            account = self.trading_engine.get_account_status()
            position_value = account.total_value * 0.1  # 10%仓位
            quantity = int(position_value / current_price)
            
            if quantity > 0:
                print(f"🚀 买入信号: {symbol}")
                self.trading_engine.submit_order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    callback=self._order_callback
                )
        
        elif (self.sma_short[0] < self.sma_long[0] and 
              self.sma_short[-1] >= self.sma_long[-1] and 
              current_quantity > 0):
            
            # 卖出信号
            print(f"🔻 卖出信号: {symbol}")
            self.trading_engine.submit_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=current_quantity,
                callback=self._order_callback
            )
    
    def _order_callback(self, order: LiveOrder):
        """订单回调函数"""
        print(f"📞 订单回调: {order.symbol} {order.status.value}")

def run_live_trading_demo():
    """运行实盘交易演示"""
    
    print("🎯 实盘交易系统演示")
    print("="*50)
    
    # 风险配置
    risk_config = {
        'max_position_size': 0.1,    # 最大单仓位10%
        'max_daily_loss': 0.02,      # 最大日亏损2%
        'max_total_exposure': 0.8,   # 最大总仓位80%
        'min_cash_reserve': 0.1      # 最小现金储备10%
    }
    
    # 创建模拟券商
    broker = MockBrokerAPI(initial_cash=100000)
    
    # 创建交易引擎
    engine = LiveTradingEngine(broker, risk_config)
    
    try:
        # 启动交易引擎
        if not engine.start():
            print("❌ 交易引擎启动失败")
            return
        
        print("✅ 交易引擎启动成功")
        
        # 获取账户状态
        account = engine.get_account_status()
        print(f"\n💰 账户状态:")
        print(f"   现金余额: ${account.cash_balance:,.2f}")
        print(f"   总价值: ${account.total_value:,.2f}")
        print(f"   当日盈亏: ${account.day_pnl:+,.2f}")
        
        # 演示交易操作
        print(f"\n🔄 演示交易操作:")
        
        # 1. 提交买入订单
        print("1. 提交买入订单...")
        order_id1 = engine.submit_order(
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.MARKET
        )
        
        if order_id1:
            print(f"   ✅ 买入订单提交: {order_id1}")
        else:
            print("   ❌ 买入订单提交失败")
        
        # 等待订单执行
        time.sleep(2)
        
        # 2. 检查持仓
        print("\n2. 检查持仓...")
        position = engine.get_position('AAPL')
        if position:
            print(f"   AAPL持仓: {position.quantity} 股")
            print(f"   平均价格: ${position.avg_price:.2f}")
            print(f"   市值: ${position.market_value:.2f}")
            print(f"   未实现盈亏: ${position.unrealized_pnl:+.2f}")
        else:
            print("   无AAPL持仓")
        
        # 3. 提交卖出订单
        if position and position.quantity > 0:
            print("\n3. 提交卖出订单...")
            order_id2 = engine.submit_order(
                symbol='AAPL',
                side=OrderSide.SELL,
                quantity=5,  # 卖出一半
                order_type=OrderType.MARKET
            )
            
            if order_id2:
                print(f"   ✅ 卖出订单提交: {order_id2}")
                time.sleep(2)
            
        # 4. 风险控制测试
        print("\n4. 测试风险控制...")
        
        # 尝试提交超大订单（应被风控拒绝）
        large_order_id = engine.submit_order(
            symbol='GOOGL',
            side=OrderSide.BUY,
            quantity=100,  # 大订单
            order_type=OrderType.MARKET
        )
        
        if not large_order_id:
            print("   ✅ 大订单被风控正确拒绝")
        else:
            print("   ⚠️ 大订单未被风控拒绝")
        
        # 5. 最终账户状态
        print("\n💰 最终账户状态:")
        final_account = engine.get_account_status()
        print(f"   现金余额: ${final_account.cash_balance:,.2f}")
        print(f"   总价值: ${final_account.total_value:,.2f}")
        print(f"   当日盈亏: ${final_account.day_pnl:+,.2f}")
        
        if final_account.positions:
            print("   持仓明细:")
            for pos in final_account.positions:
                print(f"     {pos.symbol}: {pos.quantity} 股, 市值 ${pos.market_value:.2f}")
        
        # 等待一段时间观察价格变化
        print(f"\n⏰ 等待5秒观察价格变化...")
        time.sleep(5)
        
        # 显示价格变化
        print("📈 当前市场价格:")
        for symbol, price in broker.market_prices.items():
            print(f"   {symbol}: ${price:.2f}")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断演示")
    
    finally:
        # 停止交易引擎
        engine.stop()
        print("🛑 交易引擎已停止")

def create_live_trading_config():
    """创建实盘交易配置文件"""
    
    config = {
        "broker": {
            "name": "interactive_brokers",  # 或 "alpaca", "td_ameritrade"
            "api_key": "your_api_key_here",
            "secret_key": "your_secret_key_here",
            "base_url": "https://api.broker.com",
            "paper_trading": True
        },
        "risk_management": {
            "max_position_size": 0.1,
            "max_daily_loss": 0.02,
            "max_total_exposure": 0.8,
            "min_cash_reserve": 0.1,
            "stop_loss_percent": 0.05,
            "take_profit_percent": 0.15
        },
        "trading": {
            "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
            "strategy_params": {
                "sma_short": 10,
                "sma_long": 20,
                "rsi_period": 14,
                "position_size_percent": 0.1
            }
        },
        "logging": {
            "level": "INFO",
            "file": "live_trading.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    config_path = "live_trading_config.json"
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"📄 配置文件已创建: {config_path}")
    print("请修改配置文件中的API密钥和参数")
    
    return config_path

if __name__ == '__main__':
    """运行实盘交易演示"""
    
    print("🎯 实盘交易接口系统")
    print("="*60)
    
    try:
        # 1. 运行演示
        run_live_trading_demo()
        
        # 2. 创建配置文件
        print(f"\n" + "="*60)
        print("📄 创建配置文件模板...")
        config_path = create_live_trading_config()
        
        print(f"\n" + "="*60)
        print("🎉 实盘交易系统演示完成!")
        
        print(f"\n🚀 系统特色:")
        print("  ✅ 券商API抽象层 - 支持多种券商接口")
        print("  ✅ 风险管理系统 - 多维度风险控制")
        print("  ✅ 订单管理引擎 - 实时订单状态监控")
        print("  ✅ 异步处理架构 - 非阻塞订单执行")
        print("  ✅ 事件驱动设计 - 灵活的回调机制")
        print("  ✅ 配置化管理 - 参数化风险和策略设置")
        
        print(f"\n💡 核心功能:")
        print("  🔸 多券商API集成")
        print("  🔸 实时持仓和账户监控")
        print("  🔸 智能风险控制")
        print("  🔸 订单生命周期管理")
        print("  🔸 策略回测到实盘的无缝切换")
        print("  🔸 详细的交易日志和审计")
        
        print(f"\n⚠️ 实盘交易注意事项:")
        print("  • 充分测试后再投入实盘")
        print("  • 从小资金开始验证")
        print("  • 严格遵循风险管理规则")
        print("  • 定期检查和更新策略")
        print("  • 保持交易日志和记录")
        print("  • 了解券商API限制和费用")
        
        print(f"\n🔧 部署建议:")
        print("  • 使用VPS确保稳定运行")
        print("  • 设置监控和告警机制")
        print("  • 定期备份配置和数据")
        print("  • 准备应急处理方案")
        print("  • 考虑灾备和故障转移")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()