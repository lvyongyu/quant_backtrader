"""
策略回测数据管理器

负责历史数据获取、清洗、存储和管理，
支持多种数据源和数据格式。

核心功能：
1. 历史数据获取
2. 数据清洗和验证
3. 数据缓存管理
4. 数据格式标准化
5. 基准数据管理
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import logging

# 基础数据结构
class MarketData:
    """市场数据基础类"""
    def __init__(self, symbol: str, date: datetime, 
                 open_price: float, high: float, low: float, 
                 close: float, volume: int = 0):
        self.symbol = symbol
        self.date = date
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.adjusted_close = close  # 复权价格
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'date': self.date.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'adjusted_close': self.adjusted_close
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MarketData':
        """从字典创建"""
        return cls(
            symbol=data['symbol'],
            date=datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date'],
            open_price=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data.get('volume', 0)
        )
    
    def validate(self) -> bool:
        """数据验证"""
        if self.high < max(self.open, self.close):
            return False
        if self.low > min(self.open, self.close):
            return False
        if any(price < 0 for price in [self.open, self.high, self.low, self.close]):
            return False
        if self.volume < 0:
            return False
        return True


class DataProvider:
    """数据提供者基础接口"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"DataProvider.{name}")
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                           interval: str = "1d") -> List[MarketData]:
        """获取历史数据"""
        raise NotImplementedError("子类必须实现此方法")
    
    def get_symbols_list(self, market: str = "US") -> List[str]:
        """获取可用股票列表"""
        raise NotImplementedError("子类必须实现此方法")


class CSVDataProvider(DataProvider):
    """CSV文件数据提供者"""
    
    def __init__(self, data_dir: str):
        super().__init__("CSV")
        self.data_dir = data_dir
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                           interval: str = "1d") -> List[MarketData]:
        """从CSV文件读取历史数据"""
        file_path = os.path.join(self.data_dir, f"{symbol}.csv")
        
        if not os.path.exists(file_path):
            self.logger.warning(f"数据文件不存在: {file_path}")
            return []
        
        data_list = []
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 跳过表头
                if lines and lines[0].startswith('date'):
                    lines = lines[1:]
                
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) >= 6:
                        try:
                            date = datetime.strptime(parts[0], "%Y-%m-%d")
                            
                            # 日期过滤
                            if start_dt <= date <= end_dt:
                                market_data = MarketData(
                                    symbol=symbol,
                                    date=date,
                                    open_price=float(parts[1]),
                                    high=float(parts[2]),
                                    low=float(parts[3]),
                                    close=float(parts[4]),
                                    volume=int(float(parts[5])) if parts[5] else 0
                                )
                                
                                if market_data.validate():
                                    data_list.append(market_data)
                        
                        except (ValueError, IndexError) as e:
                            self.logger.warning(f"数据解析错误: {line.strip()}, {e}")
                            continue
        
        except Exception as e:
            self.logger.error(f"读取CSV文件失败: {e}")
            return []
        
        return sorted(data_list, key=lambda x: x.date)
    
    def save_data(self, symbol: str, data: List[MarketData]):
        """保存数据到CSV文件"""
        file_path = os.path.join(self.data_dir, f"{symbol}.csv")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入表头
                f.write("date,open,high,low,close,volume\\n")
                
                # 写入数据
                for market_data in sorted(data, key=lambda x: x.date):
                    f.write(f"{market_data.date.strftime('%Y-%m-%d')},"
                           f"{market_data.open},{market_data.high},"
                           f"{market_data.low},{market_data.close},"
                           f"{market_data.volume}\\n")
            
            self.logger.info(f"数据保存成功: {symbol}, {len(data)}条记录")
        
        except Exception as e:
            self.logger.error(f"保存CSV文件失败: {e}")


class MockDataProvider(DataProvider):
    """模拟数据提供者（用于测试）"""
    
    def __init__(self):
        super().__init__("Mock")
        # 使用简单的随机数生成器（避免numpy依赖）
        import random
        self.random = random
        self.random.seed(42)  # 固定种子确保可重复
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, 
                           interval: str = "1d") -> List[MarketData]:
        """生成模拟历史数据"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        data_list = []
        current_date = start_dt
        current_price = 100.0  # 初始价格
        
        while current_date <= end_dt:
            # 随机价格变动
            change_pct = (self.random.random() - 0.5) * 0.04  # -2% to +2%
            new_price = current_price * (1 + change_pct)
            
            # 生成OHLC数据
            high_offset = self.random.random() * 0.02  # 0-2%
            low_offset = self.random.random() * 0.02   # 0-2%
            
            open_price = current_price
            close_price = new_price
            high_price = max(open_price, close_price) * (1 + high_offset)
            low_price = min(open_price, close_price) * (1 - low_offset)
            
            # 生成成交量
            volume = int(self.random.uniform(100000, 1000000))
            
            market_data = MarketData(
                symbol=symbol,
                date=current_date,
                open_price=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            )
            
            data_list.append(market_data)
            current_price = new_price
            current_date += timedelta(days=1)
            
            # 跳过周末
            if current_date.weekday() >= 5:
                current_date += timedelta(days=2)
        
        return data_list
    
    def get_symbols_list(self, market: str = "US") -> List[str]:
        """获取模拟股票列表"""
        return ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META"]


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.logger = logging.getLogger("DataCache")
    
    def get_cache_key(self, symbol: str, start_date: str, end_date: str, interval: str) -> str:
        """生成缓存键"""
        return f"{symbol}_{start_date}_{end_date}_{interval}"
    
    def get_cache_file(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")
    
    def is_cached(self, symbol: str, start_date: str, end_date: str, interval: str) -> bool:
        """检查数据是否已缓存"""
        cache_key = self.get_cache_key(symbol, start_date, end_date, interval)
        cache_file = self.get_cache_file(cache_key)
        return os.path.exists(cache_file)
    
    def get_cached_data(self, symbol: str, start_date: str, end_date: str, 
                       interval: str) -> Optional[List[MarketData]]:
        """获取缓存数据"""
        if not self.is_cached(symbol, start_date, end_date, interval):
            return None
        
        cache_key = self.get_cache_key(symbol, start_date, end_date, interval)
        cache_file = self.get_cache_file(cache_key)
        
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
                # 验证缓存数据
                if isinstance(cached_data, dict) and 'data' in cached_data:
                    cache_time = cached_data.get('timestamp', 0)
                    
                    # 缓存有效期检查（24小时）
                    if datetime.now().timestamp() - cache_time < 86400:
                        self.logger.debug(f"缓存命中: {cache_key}")
                        return cached_data['data']
                    else:
                        self.logger.debug(f"缓存过期: {cache_key}")
                        return None
        
        except Exception as e:
            self.logger.warning(f"读取缓存失败: {cache_key}, {e}")
            return None
        
        return None
    
    def cache_data(self, symbol: str, start_date: str, end_date: str, 
                   interval: str, data: List[MarketData]):
        """缓存数据"""
        cache_key = self.get_cache_key(symbol, start_date, end_date, interval)
        cache_file = self.get_cache_file(cache_key)
        
        try:
            cache_data = {
                'timestamp': datetime.now().timestamp(),
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date,
                'interval': interval,
                'data': data
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            self.logger.debug(f"数据已缓存: {cache_key}, {len(data)}条记录")
        
        except Exception as e:
            self.logger.warning(f"缓存数据失败: {cache_key}, {e}")
    
    def clear_cache(self, symbol: str = None):
        """清理缓存"""
        try:
            if symbol:
                # 清理特定股票的缓存
                for file_name in os.listdir(self.cache_dir):
                    if file_name.startswith(f"{symbol}_"):
                        file_path = os.path.join(self.cache_dir, file_name)
                        os.remove(file_path)
                        self.logger.info(f"清理缓存: {file_name}")
            else:
                # 清理所有缓存
                for file_name in os.listdir(self.cache_dir):
                    if file_name.endswith('.pkl'):
                        file_path = os.path.join(self.cache_dir, file_name)
                        os.remove(file_path)
                        self.logger.info(f"清理缓存: {file_name}")
        
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")


class HistoricalDataManager:
    """
    历史数据管理器
    
    统一管理多种数据源，提供缓存机制，
    确保数据质量和访问效率。
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.providers = {}
        self.cache = DataCache(cache_dir)
        self.logger = logging.getLogger("HistoricalDataManager")
        
        # 注册默认数据提供者
        self.register_provider("mock", MockDataProvider())
        self.register_provider("csv", CSVDataProvider("data/historical"))
    
    def register_provider(self, name: str, provider: DataProvider):
        """注册数据提供者"""
        self.providers[name] = provider
        self.logger.info(f"注册数据提供者: {name}")
    
    def get_data(self, symbol: str, start_date: str, end_date: str, 
                 interval: str = "1d", provider: str = "mock", 
                 use_cache: bool = True) -> List[MarketData]:
        """
        获取历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 数据间隔
            provider: 数据提供者名称
            use_cache: 是否使用缓存
        
        Returns:
            历史数据列表
        """
        # 检查缓存
        if use_cache:
            cached_data = self.cache.get_cached_data(symbol, start_date, end_date, interval)
            if cached_data:
                return cached_data
        
        # 获取数据提供者
        if provider not in self.providers:
            raise ValueError(f"未知的数据提供者: {provider}")
        
        data_provider = self.providers[provider]
        
        try:
            # 获取数据
            data = data_provider.get_historical_data(symbol, start_date, end_date, interval)
            
            # 数据验证和清洗
            cleaned_data = self._clean_data(data)
            
            # 缓存数据
            if use_cache and cleaned_data:
                self.cache.cache_data(symbol, start_date, end_date, interval, cleaned_data)
            
            self.logger.info(f"获取数据成功: {symbol} {start_date}-{end_date}, {len(cleaned_data)}条记录")
            
            return cleaned_data
        
        except Exception as e:
            self.logger.error(f"获取数据失败: {symbol}, {e}")
            return []
    
    def _clean_data(self, data: List[MarketData]) -> List[MarketData]:
        """数据清洗"""
        if not data:
            return []
        
        cleaned_data = []
        
        for market_data in data:
            # 数据验证
            if not market_data.validate():
                self.logger.warning(f"无效数据: {market_data.symbol} {market_data.date}")
                continue
            
            # 价格合理性检查
            if market_data.close <= 0 or market_data.close > 10000:
                self.logger.warning(f"异常价格: {market_data.symbol} {market_data.date} ${market_data.close}")
                continue
            
            cleaned_data.append(market_data)
        
        # 按日期排序
        cleaned_data.sort(key=lambda x: x.date)
        
        # 检查数据连续性
        if len(cleaned_data) > 1:
            gaps = self._check_data_gaps(cleaned_data)
            if gaps:
                self.logger.warning(f"数据缺口: {len(gaps)}个")
        
        return cleaned_data
    
    def _check_data_gaps(self, data: List[MarketData]) -> List[Tuple[datetime, datetime]]:
        """检查数据缺口"""
        gaps = []
        
        for i in range(1, len(data)):
            prev_date = data[i-1].date
            curr_date = data[i].date
            
            # 计算预期的下一个交易日
            expected_date = prev_date + timedelta(days=1)
            
            # 跳过周末
            while expected_date.weekday() >= 5:
                expected_date += timedelta(days=1)
            
            # 检查是否有缺口（超过3天）
            if (curr_date - prev_date).days > 3:
                gaps.append((prev_date, curr_date))
        
        return gaps
    
    def get_symbols_list(self, provider: str = "mock", market: str = "US") -> List[str]:
        """获取可用股票列表"""
        if provider not in self.providers:
            raise ValueError(f"未知的数据提供者: {provider}")
        
        return self.providers[provider].get_symbols_list(market)
    
    def preload_data(self, symbols: List[str], start_date: str, end_date: str,
                     provider: str = "mock", interval: str = "1d"):
        """预加载数据"""
        self.logger.info(f"开始预加载数据: {len(symbols)}个股票")
        
        for symbol in symbols:
            try:
                self.get_data(symbol, start_date, end_date, interval, provider)
                self.logger.debug(f"预加载完成: {symbol}")
            except Exception as e:
                self.logger.error(f"预加载失败: {symbol}, {e}")
        
        self.logger.info("数据预加载完成")
    
    def get_data_info(self, symbol: str, provider: str = "mock") -> Dict:
        """获取数据信息"""
        try:
            # 获取最近一年的数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            data = self.get_data(symbol, start_date, end_date, provider=provider)
            
            if not data:
                return {"symbol": symbol, "available": False}
            
            return {
                "symbol": symbol,
                "available": True,
                "records": len(data),
                "start_date": data[0].date.strftime("%Y-%m-%d"),
                "end_date": data[-1].date.strftime("%Y-%m-%d"),
                "price_range": {
                    "min": min(d.low for d in data),
                    "max": max(d.high for d in data),
                    "latest": data[-1].close
                },
                "volume_stats": {
                    "avg": sum(d.volume for d in data) / len(data),
                    "max": max(d.volume for d in data)
                }
            }
        
        except Exception as e:
            self.logger.error(f"获取数据信息失败: {symbol}, {e}")
            return {"symbol": symbol, "available": False, "error": str(e)}


# 使用示例和测试
if __name__ == "__main__":
    print("📈 策略回测数据管理器")
    print("=" * 50)
    
    # 创建数据管理器
    data_manager = HistoricalDataManager()
    print("✅ 数据管理器创建成功")
    
    # 测试模拟数据提供者
    print("\\n🔧 测试模拟数据...")
    test_data = data_manager.get_data(
        symbol="AAPL",
        start_date="2023-01-01",
        end_date="2023-01-31",
        provider="mock"
    )
    
    print(f"✅ 获取数据: {len(test_data)}条记录")
    if test_data:
        print(f"  日期范围: {test_data[0].date.strftime('%Y-%m-%d')} - {test_data[-1].date.strftime('%Y-%m-%d')}")
        print(f"  价格范围: ${test_data[0].close:.2f} - ${test_data[-1].close:.2f}")
    
    # 测试数据缓存
    print("\\n💾 测试数据缓存...")
    cached_data = data_manager.get_data(
        symbol="AAPL",
        start_date="2023-01-01",
        end_date="2023-01-31",
        provider="mock",
        use_cache=True
    )
    print(f"✅ 缓存测试: {len(cached_data)}条记录")
    
    # 测试数据信息
    print("\\n📊 测试数据信息...")
    info = data_manager.get_data_info("AAPL", "mock")
    print(f"✅ 数据信息: {info}")
    
    # 测试股票列表
    print("\\n📋 测试股票列表...")
    symbols = data_manager.get_symbols_list("mock")
    print(f"✅ 可用股票: {symbols}")
    
    print("\\n🎯 数据管理器核心功能:")
    print("  - 多数据源支持 ✅")
    print("  - 数据缓存机制 ✅") 
    print("  - 数据清洗验证 ✅")
    print("  - 数据缺口检测 ✅")
    print("  - 批量数据预加载 ✅")
    
    print("\\n🔧 下一步集成:")
    print("  1. Yahoo Finance API集成")
    print("  2. 实时数据源集成")
    print("  3. 基准数据管理")
    print("  4. 数据质量监控")
    
    print("\\n" + "=" * 50)