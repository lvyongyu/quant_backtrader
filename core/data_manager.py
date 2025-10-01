"""
简化数据管理模块 - Simplified Data Manager

统一的数据获取接口，支持历史数据和实时数据，
自动选择最佳数据源，内置智能缓存。

核心设计原则：
- 简化优于复杂：一个接口解决所有数据需求
- 默认配置：开箱即用，无需复杂配置
- 自动选择：智能选择最佳数据源
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging
import os
import pickle
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """
    简化的数据管理器
    
    特点：
    - 统一接口获取历史数据和实时数据
    - 自动缓存，提高性能
    - 智能错误处理和重试
    - 支持多种时间周期
    """
    
    def __init__(self, cache_dir: str = None):
        """
        初始化数据管理器
        
        Args:
            cache_dir: 缓存目录，默认为 ./data/cache
        """
        self.cache_dir = Path(cache_dir or "./data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存配置
        self.cache_enabled = True
        self.cache_expiry_hours = 24  # 缓存24小时
        
        logger.info(f"数据管理器初始化完成，缓存目录：{self.cache_dir}")
    
    def get_data(self, 
                 symbol: str, 
                 period: str = "1y",
                 interval: str = "1d") -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码，如 'AAPL', 'GOOGL'
            period: 时间周期，支持 '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
            interval: 数据间隔，支持 '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'
        
        Returns:
            包含OHLCV数据的DataFrame
        """
        try:
            # 检查缓存
            cache_key = f"{symbol}_{period}_{interval}"
            cached_data = self._get_cache(cache_key)
            if cached_data is not None:
                logger.info(f"从缓存获取数据：{symbol}")
                return cached_data
            
            # 从数据源获取
            logger.info(f"正在获取数据：{symbol}, 周期：{period}, 间隔：{interval}")
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                raise ValueError(f"未获取到数据：{symbol}")
            
            # 数据清洗
            data = self._clean_data(data)
            
            # 保存缓存
            self._save_cache(cache_key, data)
            
            logger.info(f"数据获取成功：{symbol}, {len(data)}条记录")
            return data
            
        except Exception as e:
            logger.error(f"数据获取失败：{symbol} - {e}")
            raise
    
    def get_data_by_date(self, 
                        symbol: str, 
                        start_date: str = None, 
                        end_date: str = None) -> pd.DataFrame:
        """
        根据日期范围获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，格式：'YYYY-MM-DD'
            end_date: 结束日期，格式：'YYYY-MM-DD'
            
        Returns:
            股票数据DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            
            if start_date and end_date:
                # 使用指定的日期范围
                data = ticker.history(start=start_date, end=end_date)
            elif start_date:
                # 只有开始日期，获取到今天
                data = ticker.history(start=start_date)
            else:
                # 默认获取1年数据
                data = ticker.history(period="1y")
            
            if data.empty:
                raise ValueError(f"未获取到数据：{symbol}")
            
            # 数据清洗
            data = self._clean_data(data)
            
            logger.info(f"日期范围数据获取成功：{symbol}, {len(data)}条记录")
            return data
            
        except Exception as e:
            logger.error(f"日期范围数据获取失败：{symbol} - {e}")
            raise
    
    def get_realtime(self, symbol: str) -> Dict:
        """
        获取实时数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            包含实时价格信息的字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 获取最新价格
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                latest = hist.iloc[-1]
                
                realtime_data = {
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']),
                    'timestamp': latest.name.isoformat(),
                    'change': 0.0,
                    'change_percent': 0.0
                }
                
                # 计算涨跌
                if len(hist) > 1:
                    prev_close = float(hist.iloc[-2]['Close'])
                    realtime_data['change'] = realtime_data['price'] - prev_close
                    realtime_data['change_percent'] = (realtime_data['change'] / prev_close) * 100
                
                logger.info(f"实时数据获取成功：{symbol}, 价格：{realtime_data['price']}")
                return realtime_data
            
            raise ValueError(f"无法获取实时数据：{symbol}")
            
        except Exception as e:
            logger.error(f"实时数据获取失败：{symbol} - {e}")
            raise
    
    def get_info(self, symbol: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            包含股票基本信息的字典
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键信息
            basic_info = {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'description': info.get('longBusinessSummary', 'N/A')[:200] + '...'
            }
            
            logger.info(f"基本信息获取成功：{symbol}")
            return basic_info
            
        except Exception as e:
            logger.error(f"基本信息获取失败：{symbol} - {e}")
            raise
    
    def get_multiple(self, symbols: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票数据
        
        Args:
            symbols: 股票代码列表
            period: 时间周期
            
        Returns:
            股票代码为键，DataFrame为值的字典
        """
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_data(symbol, period)
                logger.info(f"批量获取成功：{symbol}")
            except Exception as e:
                logger.warning(f"批量获取失败：{symbol} - {e}")
                continue
        
        logger.info(f"批量获取完成：{len(results)}/{len(symbols)}只股票")
        return results
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        # 移除空值
        data = data.dropna()
        
        # 确保列名标准化
        data.columns = [col.title() for col in data.columns]
        
        # 确保数据类型正确
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        return data
    
    def _get_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        if not self.cache_enabled:
            return None
            
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            # 检查缓存时间
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - cache_time < timedelta(hours=self.cache_expiry_hours):
                try:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                except Exception:
                    # 缓存文件损坏，删除
                    cache_file.unlink()
        
        return None
    
    def _save_cache(self, cache_key: str, data: pd.DataFrame):
        """保存缓存数据"""
        if not self.cache_enabled:
            return
            
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"缓存保存失败：{e}")
    
    def clear_cache(self):
        """清除所有缓存"""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        for cache_file in cache_files:
            cache_file.unlink()
        
        logger.info(f"缓存清除完成：{len(cache_files)}个文件")
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'cache_enabled': self.cache_enabled,
            'cache_dir': str(self.cache_dir),
            'file_count': len(cache_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'expiry_hours': self.cache_expiry_hours
        }


# 便捷函数
def get_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    便捷函数：获取股票数据
    
    Args:
        symbol: 股票代码
        period: 时间周期
        
    Returns:
        股票数据DataFrame
    """
    manager = DataManager()
    return manager.get_data(symbol, period)


def get_realtime_price(symbol: str) -> float:
    """
    便捷函数：获取实时价格
    
    Args:
        symbol: 股票代码
        
    Returns:
        当前价格
    """
    manager = DataManager()
    data = manager.get_realtime(symbol)
    return data['price']


# 使用示例和测试
if __name__ == "__main__":
    print("🚀 简化数据管理模块测试")
    print("=" * 50)
    
    # 创建数据管理器
    dm = DataManager()
    
    # 测试1：获取历史数据
    print("\n📊 测试历史数据获取...")
    try:
        aapl_data = dm.get_data("AAPL", "1mo")
        print(f"✅ AAPL数据获取成功：{len(aapl_data)}条记录")
        print(f"   数据范围：{aapl_data.index[0].date()} - {aapl_data.index[-1].date()}")
        print(f"   最新收盘价：${aapl_data['Close'].iloc[-1]:.2f}")
    except Exception as e:
        print(f"❌ 历史数据获取失败：{e}")
    
    # 测试2：获取实时数据
    print("\n⚡ 测试实时数据获取...")
    try:
        realtime = dm.get_realtime("AAPL")
        print(f"✅ 实时数据获取成功")
        print(f"   当前价格：${realtime['price']:.2f}")
        print(f"   涨跌幅：{realtime['change_percent']:+.2f}%")
    except Exception as e:
        print(f"❌ 实时数据获取失败：{e}")
    
    # 测试3：获取基本信息
    print("\n📋 测试基本信息获取...")
    try:
        info = dm.get_info("AAPL")
        print(f"✅ 基本信息获取成功")
        print(f"   公司名称：{info['name']}")
        print(f"   行业：{info['sector']} - {info['industry']}")
        print(f"   市值：${info['market_cap']:,}")
    except Exception as e:
        print(f"❌ 基本信息获取失败：{e}")
    
    # 测试4：批量获取
    print("\n📈 测试批量数据获取...")
    try:
        symbols = ["AAPL", "GOOGL", "MSFT"]
        multiple_data = dm.get_multiple(symbols, "1mo")
        print(f"✅ 批量获取成功：{len(multiple_data)}只股票")
        for symbol, data in multiple_data.items():
            print(f"   {symbol}：{len(data)}条记录")
    except Exception as e:
        print(f"❌ 批量获取失败：{e}")
    
    # 测试5：缓存信息
    print("\n💾 缓存信息...")
    cache_info = dm.get_cache_info()
    print(f"   缓存状态：{'启用' if cache_info['cache_enabled'] else '禁用'}")
    print(f"   缓存文件：{cache_info['file_count']}个")
    print(f"   缓存大小：{cache_info['total_size_mb']}MB")
    
    # 测试6：便捷函数
    print("\n🔧 测试便捷函数...")
    try:
        price = get_realtime_price("AAPL")
        print(f"✅ 便捷函数测试成功：AAPL当前价格 ${price:.2f}")
    except Exception as e:
        print(f"❌ 便捷函数测试失败：{e}")
    
    print("\n" + "=" * 50)
    print("🎯 简化数据管理模块核心特性：")
    print("  ✅ 统一接口 - 一个类解决所有数据需求")
    print("  ✅ 智能缓存 - 自动缓存，提高性能") 
    print("  ✅ 错误处理 - 友好的错误提示")
    print("  ✅ 便捷函数 - 简化常用操作")
    print("  ✅ 批量处理 - 支持多股票数据获取")
    print("=" * 50)

# ==================== 便捷函数 ====================

# 创建全局数据管理器实例
_global_data_manager = DataManager()

def get_data(symbol: str, start_date: str = None, end_date: str = None, period: str = '1d') -> pd.DataFrame:
    """
    便捷函数：获取股票数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期，格式：'YYYY-MM-DD'
        end_date: 结束日期，格式：'YYYY-MM-DD'
        period: 时间周期 (当start_date和end_date为None时使用)
        
    Returns:
        股票数据DataFrame
    """
    if start_date or end_date:
        return _global_data_manager.get_data_by_date(symbol, start_date, end_date)
    else:
        # 转换period到yfinance格式
        if period == '1d':
            yf_period = '1y'
        elif period in ['1mo', '3mo', '6mo', '1y', '2y', '5y']:
            yf_period = period
        else:
            yf_period = '1y'
        return _global_data_manager.get_data(symbol, period=yf_period)

def get_realtime_price(symbol: str) -> float:
    """
    便捷函数：获取实时价格
    
    Args:
        symbol: 股票代码
        
    Returns:
        当前价格
    """
    try:
        realtime_data = _global_data_manager.get_realtime(symbol)
        return realtime_data.get('price', 0.0)
    except:
        # 如果实时数据失败，使用最新历史数据
        try:
            data = _global_data_manager.get_data(symbol, period='1d')
            return float(data['Close'].iloc[-1]) if not data.empty else 0.0
        except:
            return 0.0

def get_stock_info(symbol: str) -> Dict:
    """
    便捷函数：获取股票信息
    
    Args:
        symbol: 股票代码
        
    Returns:
        股票信息字典
    """
    return _global_data_manager.get_info(symbol)

def get_multiple_data(symbols: List[str], period: str = '1mo') -> Dict[str, pd.DataFrame]:
    """
    便捷函数：批量获取股票数据
    
    Args:
        symbols: 股票代码列表
        period: 时间周期
        
    Returns:
        股票数据字典
    """
    return _global_data_manager.get_multiple(symbols, period)