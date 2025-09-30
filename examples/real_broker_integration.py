#!/usr/bin/env python3
"""
真实券商集成示例
Real Broker Integration Examples

演示如何集成主流券商API，包括Interactive Brokers、Alpaca、TD Ameritrade等
"""

import backtrader as bt
import requests
import json
import threading
import time
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
import logging

# WebSocket在实际使用时需要安装: pip install websocket-client

logger = logging.getLogger(__name__)

class BrokerAPIInterface(ABC):
    """券商API接口抽象基类"""
    
    @abstractmethod
    def connect(self) -> bool:
        """连接到券商"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> dict:
        """获取账户信息"""
        pass
    
    @abstractmethod
    def submit_order(self, order_data: dict) -> str:
        """提交订单"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[dict]:
        """获取持仓"""
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> dict:
        """获取订单状态"""
        pass

class AlpacaAPI(BrokerAPIInterface):
    """Alpaca券商API集成"""
    
    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_trading = paper_trading
        
        # API端点
        if paper_trading:
            self.base_url = "https://paper-api.alpaca.markets"
            self.data_url = "https://data.alpaca.markets"
        else:
            self.base_url = "https://api.alpaca.markets"
            self.data_url = "https://data.alpaca.markets"
        
        # 请求头
        self.headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': secret_key,
            'Content-Type': 'application/json'
        }
        
        self.connected = False
        
        print(f"📱 Alpaca API初始化 ({'模拟' if paper_trading else '实盘'})")
    
    def connect(self) -> bool:
        """连接到Alpaca"""
        try:
            # 测试连接
            response = self._get('/v2/account')
            if response.status_code == 200:
                self.connected = True
                account_data = response.json()
                print(f"✅ Alpaca连接成功")
                print(f"   账户ID: {account_data.get('id')}")
                print(f"   状态: {account_data.get('status')}")
                return True
            else:
                print(f"❌ Alpaca连接失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Alpaca连接异常: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        print("🔌 Alpaca连接已断开")
    
    def _get(self, endpoint: str):
        """GET请求"""
        url = self.base_url + endpoint
        return requests.get(url, headers=self.headers)
    
    def _post(self, endpoint: str, data: dict):
        """POST请求"""
        url = self.base_url + endpoint
        return requests.post(url, headers=self.headers, json=data)
    
    def _delete(self, endpoint: str):
        """DELETE请求"""
        url = self.base_url + endpoint
        return requests.delete(url, headers=self.headers)
    
    def get_account_info(self) -> dict:
        """获取账户信息"""
        if not self.connected:
            raise Exception("未连接到Alpaca")
        
        response = self._get('/v2/account')
        if response.status_code == 200:
            account = response.json()
            return {
                'account_id': account['id'],
                'cash': float(account['cash']),
                'buying_power': float(account['buying_power']),
                'portfolio_value': float(account['portfolio_value']),
                'day_trade_buying_power': float(account['daytrading_buying_power']),
                'status': account['status']
            }
        else:
            raise Exception(f"获取账户信息失败: {response.text}")
    
    def submit_order(self, order_data: dict) -> str:
        """提交订单到Alpaca"""
        if not self.connected:
            raise Exception("未连接到Alpaca")
        
        # 转换订单格式
        alpaca_order = {
            'symbol': order_data['symbol'],
            'qty': str(order_data['quantity']),
            'side': order_data['side'],  # 'buy' or 'sell'
            'type': order_data['type'],  # 'market', 'limit', 'stop', 'stop_limit'
            'time_in_force': order_data.get('time_in_force', 'day')
        }
        
        # 添加价格信息
        if order_data['type'] in ['limit', 'stop_limit']:
            alpaca_order['limit_price'] = str(order_data['price'])
        
        if order_data['type'] in ['stop', 'stop_limit']:
            alpaca_order['stop_price'] = str(order_data['stop_price'])
        
        response = self._post('/v2/orders', alpaca_order)
        
        if response.status_code == 201:
            order_result = response.json()
            print(f"✅ Alpaca订单提交成功: {order_result['id']}")
            return order_result['id']
        else:
            error_msg = f"Alpaca订单提交失败: {response.text}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        if not self.connected:
            raise Exception("未连接到Alpaca")
        
        response = self._delete(f'/v2/orders/{order_id}')
        success = response.status_code == 204
        
        if success:
            print(f"✅ Alpaca订单取消成功: {order_id}")
        else:
            print(f"❌ Alpaca订单取消失败: {response.text}")
        
        return success
    
    def get_positions(self) -> List[dict]:
        """获取持仓"""
        if not self.connected:
            raise Exception("未连接到Alpaca")
        
        response = self._get('/v2/positions')
        if response.status_code == 200:
            positions = response.json()
            result = []
            
            for pos in positions:
                result.append({
                    'symbol': pos['symbol'],
                    'quantity': float(pos['qty']),
                    'avg_price': float(pos['avg_entry_price']),
                    'market_value': float(pos['market_value']),
                    'unrealized_pnl': float(pos['unrealized_pl']),
                    'side': pos['side']
                })
            
            return result
        else:
            raise Exception(f"获取持仓失败: {response.text}")
    
    def get_order_status(self, order_id: str) -> dict:
        """获取订单状态"""
        if not self.connected:
            raise Exception("未连接到Alpaca")
        
        response = self._get(f'/v2/orders/{order_id}')
        if response.status_code == 200:
            order = response.json()
            return {
                'order_id': order['id'],
                'status': order['status'],
                'symbol': order['symbol'],
                'quantity': float(order['qty']),
                'filled_qty': float(order['filled_qty']),
                'side': order['side'],
                'type': order['order_type'],
                'submitted_at': order['submitted_at']
            }
        else:
            raise Exception(f"获取订单状态失败: {response.text}")
    
    def get_market_data(self, symbol: str) -> dict:
        """获取市场数据"""
        try:
            # 获取最新报价
            response = requests.get(
                f"{self.data_url}/v2/stocks/{symbol}/quotes/latest",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                quote = data['quote']
                return {
                    'symbol': symbol,
                    'bid': quote['bp'],
                    'ask': quote['ap'],
                    'bid_size': quote['bs'],
                    'ask_size': quote['as'],
                    'timestamp': quote['t']
                }
            else:
                print(f"⚠️ 获取{symbol}市场数据失败: {response.text}")
                return {}
        
        except Exception as e:
            print(f"❌ 市场数据获取异常: {e}")
            return {}

class InteractiveBrokersAPI(BrokerAPIInterface):
    """Interactive Brokers API集成 (简化示例)"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        
        print(f"📱 Interactive Brokers API初始化")
        print(f"   连接地址: {host}:{port}")
        print(f"   客户端ID: {client_id}")
        print(f"   ⚠️ 需要先启动TWS或IB Gateway")
    
    def connect(self) -> bool:
        """连接到IB TWS/Gateway"""
        try:
            # 这里需要使用ib_insync或ibapi库
            # 简化示例，实际需要安装: pip install ib_insync
            
            print("🔌 尝试连接Interactive Brokers...")
            print("   ⚠️ 此为示例代码，需要安装ib_insync库")
            print("   pip install ib_insync")
            
            # 模拟连接成功
            self.connected = True
            print("✅ IB连接成功 (模拟)")
            return True
            
        except Exception as e:
            print(f"❌ IB连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        print("🔌 IB连接已断开")
    
    def get_account_info(self) -> dict:
        """获取账户信息"""
        # IB API实现示例
        return {
            'account_id': 'DU12345',
            'cash': 100000.0,
            'buying_power': 400000.0,
            'portfolio_value': 150000.0,
            'net_liquidation': 150000.0
        }
    
    def submit_order(self, order_data: dict) -> str:
        """提交订单"""
        print(f"📋 IB订单提交: {order_data}")
        return f"IB_{int(time.time())}"
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        print(f"🚫 IB订单取消: {order_id}")
        return True
    
    def get_positions(self) -> List[dict]:
        """获取持仓"""
        return []
    
    def get_order_status(self, order_id: str) -> dict:
        """获取订单状态"""
        return {
            'order_id': order_id,
            'status': 'filled',
            'filled_qty': 100
        }

class TDAmeritradeBrokerAPI(BrokerAPIInterface):
    """TD Ameritrade API集成 (简化示例)"""
    
    def __init__(self, api_key: str, refresh_token: str = None):
        self.api_key = api_key
        self.refresh_token = refresh_token
        self.access_token = None
        self.base_url = "https://api.tdameritrade.com"
        self.connected = False
        
        print("📱 TD Ameritrade API初始化")
        print("   ⚠️ 需要OAuth认证流程")
    
    def connect(self) -> bool:
        """连接到TD Ameritrade"""
        try:
            # OAuth认证流程 (简化)
            if self.refresh_token:
                success = self._refresh_access_token()
                if success:
                    self.connected = True
                    print("✅ TD Ameritrade连接成功")
                    return True
            
            print("❌ TD Ameritrade连接失败: 需要有效的refresh_token")
            return False
            
        except Exception as e:
            print(f"❌ TD Ameritrade连接异常: {e}")
            return False
    
    def _refresh_access_token(self) -> bool:
        """刷新访问令牌"""
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.api_key
            }
            
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                data=data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                return True
            
            return False
            
        except Exception as e:
            print(f"Token刷新失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        self.access_token = None
        print("🔌 TD Ameritrade连接已断开")
    
    def get_account_info(self) -> dict:
        """获取账户信息"""
        if not self.connected or not self.access_token:
            raise Exception("未连接到TD Ameritrade")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        # 实际API调用示例
        # response = requests.get(f"{self.base_url}/v1/accounts", headers=headers)
        
        # 模拟返回
        return {
            'account_id': 'TD123456789',
            'cash': 50000.0,
            'buying_power': 200000.0,
            'portfolio_value': 75000.0
        }
    
    def submit_order(self, order_data: dict) -> str:
        """提交订单"""
        print(f"📋 TD Ameritrade订单提交: {order_data}")
        return f"TD_{int(time.time())}"
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        print(f"🚫 TD Ameritrade订单取消: {order_id}")
        return True
    
    def get_positions(self) -> List[dict]:
        """获取持仓"""
        return []
    
    def get_order_status(self, order_id: str) -> dict:
        """获取订单状态"""
        return {
            'order_id': order_id,
            'status': 'filled'
        }

class BrokerFactory:
    """券商工厂类"""
    
    @staticmethod
    def create_broker(broker_type: str, config: dict) -> BrokerAPIInterface:
        """创建券商API实例"""
        
        if broker_type.lower() == 'alpaca':
            return AlpacaAPI(
                api_key=config['api_key'],
                secret_key=config['secret_key'],
                paper_trading=config.get('paper_trading', True)
            )
        
        elif broker_type.lower() == 'interactive_brokers':
            return InteractiveBrokersAPI(
                host=config.get('host', '127.0.0.1'),
                port=config.get('port', 7497),
                client_id=config.get('client_id', 1)
            )
        
        elif broker_type.lower() == 'td_ameritrade':
            return TDAmeritradeBrokerAPI(
                api_key=config['api_key'],
                refresh_token=config.get('refresh_token')
            )
        
        else:
            raise ValueError(f"不支持的券商类型: {broker_type}")

def demo_alpaca_integration():
    """演示Alpaca集成"""
    
    print("🎯 Alpaca券商集成演示")
    print("="*50)
    
    # 注意：这里使用示例密钥，实际使用时需要替换
    config = {
        'api_key': 'PKTEST12345',  # 替换为真实API Key
        'secret_key': 'your_secret_key_here',  # 替换为真实Secret Key
        'paper_trading': True
    }
    
    try:
        # 创建Alpaca API实例
        alpaca = BrokerFactory.create_broker('alpaca', config)
        
        # 模拟连接 (实际需要有效的API密钥)
        print("⚠️ 使用示例API密钥，连接将失败")
        print("   请替换为真实的Alpaca API密钥进行测试")
        
        # 连接测试
        connected = alpaca.connect()
        
        if connected:
            # 获取账户信息
            account = alpaca.get_account_info()
            print(f"💰 账户信息:")
            print(f"   现金: ${account['cash']:,.2f}")
            print(f"   购买力: ${account['buying_power']:,.2f}")
            print(f"   组合价值: ${account['portfolio_value']:,.2f}")
            
            # 获取持仓
            positions = alpaca.get_positions()
            if positions:
                print(f"📊 持仓信息:")
                for pos in positions:
                    print(f"   {pos['symbol']}: {pos['quantity']} 股")
            else:
                print("📊 无持仓")
            
            # 获取市场数据
            market_data = alpaca.get_market_data('AAPL')
            if market_data:
                print(f"📈 AAPL市场数据:")
                print(f"   买价: ${market_data['bid']:.2f}")
                print(f"   卖价: ${market_data['ask']:.2f}")
            
        alpaca.disconnect()
        
    except Exception as e:
        print(f"❌ Alpaca演示失败: {e}")

def demo_broker_comparison():
    """券商API对比演示"""
    
    print("\n🎯 券商API功能对比")
    print("="*60)
    
    brokers_info = {
        'Alpaca': {
            '📱 API类型': 'REST API + WebSocket',
            '🎯 市场': '美股 + 加密货币',
            '💰 最低资金': '$0 (模拟账户)',
            '📊 数据源': '实时 + 历史数据',
            '🔧 集成难度': '简单',
            '💡 特色': '免佣金交易, 强大API'
        },
        'Interactive Brokers': {
            '📱 API类型': 'TWS API + Gateway',
            '🎯 市场': '全球股票, 期货, 期权, 外汇',
            '💰 最低资金': '$10,000',
            '📊 数据源': '实时 + 历史数据',
            '🔧 集成难度': '中等',
            '💡 特色': '低佣金, 全球市场, 专业工具'
        },
        'TD Ameritrade': {
            '📱 API类型': 'REST API',
            '🎯 市场': '美股, 期权, 期货',
            '💰 最低资金': '$0',
            '📊 数据源': '实时 + 历史数据',
            '🔧 集成难度': '中等',
            '💡 特色': '免佣金股票交易, OAuth认证'
        }
    }
    
    for broker, info in brokers_info.items():
        print(f"\n🏢 {broker}:")
        for key, value in info.items():
            print(f"   {key}: {value}")

def create_broker_integration_guide():
    """创建券商集成指南"""
    
    guide = """
# 券商API集成指南

## 🏢 支持的券商

### 1. Alpaca Markets
- **优势**: 免佣金、API友好、支持加密货币
- **适用**: 个人投资者、量化交易入门
- **申请流程**: alpaca.markets 注册账户
- **API文档**: https://alpaca.markets/docs/

### 2. Interactive Brokers (IB)
- **优势**: 全球市场、低佣金、专业工具
- **适用**: 专业交易者、大资金量化交易
- **申请流程**: www.interactivebrokers.com 开户
- **API文档**: https://interactivebrokers.github.io/

### 3. TD Ameritrade
- **优势**: 美国本土券商、免佣金股票交易
- **适用**: 美股交易、期权策略
- **申请流程**: www.tdameritrade.com 开户
- **API文档**: https://developer.tdameritrade.com/

## 🔧 集成步骤

### 步骤1: 申请API访问权限
1. 在券商官网注册账户
2. 完成身份验证和资金存入
3. 申请API访问权限
4. 获取API密钥和认证信息

### 步骤2: 安装依赖库
```bash
# Alpaca
pip install alpaca-trade-api

# Interactive Brokers
pip install ib_insync

# TD Ameritrade
pip install requests tda-api
```

### 步骤3: 配置API连接
```python
# 配置文件示例
{
    "broker": "alpaca",
    "api_key": "your_api_key",
    "secret_key": "your_secret_key",
    "paper_trading": true
}
```

### 步骤4: 测试连接
```python
# 测试连接代码
broker = BrokerFactory.create_broker('alpaca', config)
if broker.connect():
    print("连接成功")
    account = broker.get_account_info()
    print(f"账户余额: {account['cash']}")
```

## ⚠️ 注意事项

### 1. 风险管理
- 始终在模拟环境中充分测试
- 设置合理的风险控制参数
- 定期监控交易系统状态

### 2. API限制
- 了解各券商的API调用频率限制
- 处理网络连接异常和重连逻辑
- 实现订单状态同步机制

### 3. 合规要求
- 遵守各国金融监管规定
- 了解税务申报要求
- 保持交易记录和审计日志

### 4. 技术架构
- 使用VPS确保网络稳定性
- 实现故障转移和备份机制
- 建立监控和告警系统

## 📚 学习资源

1. **官方文档**: 各券商API官方文档
2. **社区论坛**: Reddit r/algotrading
3. **开源项目**: GitHub相关项目
4. **在线课程**: Quantitative Finance课程
5. **技术博客**: 量化交易技术博客

## 🛠️ 调试技巧

1. **日志记录**: 详细记录API调用和响应
2. **错误处理**: 实现完善的异常处理机制
3. **单元测试**: 编写API接口的单元测试
4. **模拟测试**: 使用模拟环境测试交易逻辑
5. **性能监控**: 监控API响应时间和成功率

## 📞 技术支持

如遇到技术问题，建议：
1. 查阅官方文档和FAQ
2. 搜索社区讨论和解决方案
3. 联系券商技术支持
4. 参与开发者社区讨论
"""
    
    with open('broker_integration_guide.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("📚 券商集成指南已创建: broker_integration_guide.md")

if __name__ == '__main__':
    """主程序"""
    
    print("🎯 真实券商集成演示")
    print("="*60)
    
    try:
        # 1. Alpaca集成演示
        demo_alpaca_integration()
        
        # 2. 券商对比
        demo_broker_comparison()
        
        # 3. 创建集成指南
        print(f"\n" + "="*60)
        create_broker_integration_guide()
        
        print(f"\n" + "="*60)
        print("🎉 券商集成演示完成!")
        
        print(f"\n🚀 支持的券商:")
        print("  ✅ Alpaca Markets - 免佣金美股+加密货币")
        print("  ✅ Interactive Brokers - 全球市场专业交易")
        print("  ✅ TD Ameritrade - 美国本土券商")
        
        print(f"\n💡 集成特点:")
        print("  🔸 统一的API接口抽象")
        print("  🔸 工厂模式支持多券商")
        print("  🔸 完整的错误处理机制")
        print("  🔸 OAuth认证流程支持")
        print("  🔸 实时数据和历史数据接口")
        print("  🔸 订单生命周期管理")
        
        print(f"\n⚠️ 使用提醒:")
        print("  • 替换示例代码中的API密钥")
        print("  • 先在模拟环境充分测试")
        print("  • 了解各券商API限制和费用")
        print("  • 遵守相关法规和合规要求")
        print("  • 建立完善的风险控制机制")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()