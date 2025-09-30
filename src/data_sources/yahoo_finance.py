"""
Yahoo Finance数据源实现

提供免费的股票市场数据，包括：
- 实时和历史股价数据
- 基本面财务数据
- 股票信息和统计数据
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import logging

from . import BaseDataSource, StockData, DataType, DataFrequency, DataSourceError


class YahooFinanceSource(BaseDataSource):
    """Yahoo Finance数据源"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("YahooFinance", config)
        self.base_url = "https://query1.finance.yahoo.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
    async def get_data(self, symbol: str, data_type: DataType, 
                      frequency: DataFrequency = DataFrequency.DAY_1,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[StockData]:
        """获取Yahoo Finance数据"""
        
        if data_type != DataType.STOCK_PRICE:
            raise DataSourceError(f"Yahoo Finance doesn't support {data_type}")
        
        self._check_rate_limit()
        
        # 设置默认日期范围
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        try:
            # 转换频率
            interval = self._convert_frequency(frequency)
            
            # 构建URL
            period1 = int(start_date.timestamp())
            period2 = int(end_date.timestamp())
            
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'period1': period1,
                'period2': period2,
                'interval': interval,
                'includePrePost': 'true',
                'events': 'div,splits'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_yahoo_data(symbol, data, frequency)
            
        except requests.RequestException as e:
            self.logger.error(f"Yahoo Finance API error: {e}")
            raise DataSourceError(f"Failed to fetch data from Yahoo Finance: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise DataSourceError(f"Unexpected error: {e}")
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时价格"""
        try:
            self._check_rate_limit()
            
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'range': '1d',
                'interval': '1m',
                'includePrePost': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            result = data['chart']['result'][0]
            
            # 获取最新数据
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            
            if timestamps and quote['close']:
                latest_idx = -1
                while latest_idx >= -len(timestamps) and quote['close'][latest_idx] is None:
                    latest_idx -= 1
                
                if latest_idx >= -len(timestamps):
                    return {
                        'symbol': symbol,
                        'price': quote['close'][latest_idx],
                        'timestamp': datetime.fromtimestamp(timestamps[latest_idx]),
                        'volume': quote['volume'][latest_idx] if quote['volume'][latest_idx] else 0,
                        'change': self._calculate_change(quote, latest_idx),
                        'change_percent': self._calculate_change_percent(quote, latest_idx)
                    }
            
            raise DataSourceError("No valid price data found")
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time price for {symbol}: {e}")
            raise DataSourceError(f"Real-time price error: {e}")
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            self._check_rate_limit()
            
            # 使用Yahoo Finance的股票信息API
            url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            params = {
                'modules': 'price,summaryDetail,defaultKeyStatistics,financialData'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            result = data['quoteSummary']['result'][0]
            
            info = {}
            
            # 基本价格信息
            if 'price' in result:
                price_data = result['price']
                info.update({
                    'current_price': price_data.get('regularMarketPrice', {}).get('raw'),
                    'previous_close': price_data.get('regularMarketPreviousClose', {}).get('raw'),
                    'market_cap': price_data.get('marketCap', {}).get('raw'),
                    'currency': price_data.get('currency')
                })
            
            # 详细统计信息
            if 'summaryDetail' in result:
                summary = result['summaryDetail']
                info.update({
                    'day_high': summary.get('dayHigh', {}).get('raw'),
                    'day_low': summary.get('dayLow', {}).get('raw'),
                    'fifty_two_week_high': summary.get('fiftyTwoWeekHigh', {}).get('raw'),
                    'fifty_two_week_low': summary.get('fiftyTwoWeekLow', {}).get('raw'),
                    'volume': summary.get('volume', {}).get('raw'),
                    'avg_volume': summary.get('averageVolume', {}).get('raw'),
                    'pe_ratio': summary.get('trailingPE', {}).get('raw'),
                    'dividend_yield': summary.get('dividendYield', {}).get('raw')
                })
            
            # 关键统计数据
            if 'defaultKeyStatistics' in result:
                stats = result['defaultKeyStatistics']
                info.update({
                    'beta': stats.get('beta', {}).get('raw'),
                    'shares_outstanding': stats.get('sharesOutstanding', {}).get('raw'),
                    'float_shares': stats.get('floatShares', {}).get('raw')
                })
            
            # 财务数据
            if 'financialData' in result:
                financial = result['financialData']
                info.update({
                    'total_cash': financial.get('totalCash', {}).get('raw'),
                    'total_debt': financial.get('totalDebt', {}).get('raw'),
                    'revenue': financial.get('totalRevenue', {}).get('raw'),
                    'gross_profit': financial.get('grossProfits', {}).get('raw'),
                    'free_cash_flow': financial.get('freeCashflow', {}).get('raw')
                })
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get stock info for {symbol}: {e}")
            raise DataSourceError(f"Stock info error: {e}")
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的股票代码列表"""
        # Yahoo Finance支持的主要股票代码
        return [
            # 美股主要指数
            "^GSPC", "^DJI", "^IXIC", "^RUT",
            # 主要科技股
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            # 金融股
            "JPM", "BAC", "WFC", "GS", "MS",
            # 医疗保健
            "JNJ", "PFE", "UNH", "ABBV",
            # 消费品
            "KO", "PG", "WMT", "HD", "MCD",
            # 工业
            "BA", "CAT", "GE", "MMM",
            # 能源
            "XOM", "CVX", "COP"
        ]
    
    def _convert_frequency(self, frequency: DataFrequency) -> str:
        """转换频率格式"""
        mapping = {
            DataFrequency.MINUTE_1: "1m",
            DataFrequency.MINUTE_5: "5m",
            DataFrequency.MINUTE_15: "15m",
            DataFrequency.HOUR_1: "1h",
            DataFrequency.DAY_1: "1d",
            DataFrequency.WEEK_1: "1wk",
            DataFrequency.MONTH_1: "1mo"
        }
        return mapping.get(frequency, "1d")
    
    def _parse_yahoo_data(self, symbol: str, data: Dict, frequency: DataFrequency) -> List[StockData]:
        """解析Yahoo Finance返回的数据"""
        try:
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            
            stock_data_list = []
            
            for i, timestamp in enumerate(timestamps):
                # 跳过无效数据
                if (quote['close'][i] is None or 
                    quote['open'][i] is None or 
                    quote['high'][i] is None or 
                    quote['low'][i] is None):
                    continue
                
                stock_data = StockData(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(timestamp),
                    data_type=DataType.STOCK_PRICE,
                    frequency=frequency,
                    data={},
                    source=self.name,
                    open_price=float(quote['open'][i]),
                    high_price=float(quote['high'][i]),
                    low_price=float(quote['low'][i]),
                    close_price=float(quote['close'][i]),
                    volume=int(quote['volume'][i]) if quote['volume'][i] else 0
                )
                
                # 添加调整后价格（如果有）
                if 'adjclose' in result['indicators']:
                    adj_close = result['indicators']['adjclose'][0]['adjclose'][i]
                    if adj_close is not None:
                        stock_data.adjusted_close = float(adj_close)
                
                if self.validate_data(stock_data):
                    stock_data_list.append(stock_data)
                else:
                    self.logger.warning(f"Invalid data point skipped: {timestamp}")
            
            self.logger.info(f"Successfully parsed {len(stock_data_list)} data points for {symbol}")
            return stock_data_list
            
        except KeyError as e:
            raise DataSourceError(f"Unexpected data format from Yahoo Finance: {e}")
        except Exception as e:
            raise DataSourceError(f"Failed to parse Yahoo Finance data: {e}")
    
    def _calculate_change(self, quote: Dict, latest_idx: int) -> Optional[float]:
        """计算价格变化"""
        try:
            if latest_idx == 0 or not quote['close']:
                return None
            
            current_price = quote['close'][latest_idx]
            previous_price = quote['close'][latest_idx - 1]
            
            if current_price is not None and previous_price is not None:
                return current_price - previous_price
            
        except (IndexError, TypeError):
            pass
        
        return None
    
    def _calculate_change_percent(self, quote: Dict, latest_idx: int) -> Optional[float]:
        """计算价格变化百分比"""
        try:
            change = self._calculate_change(quote, latest_idx)
            if change is not None and latest_idx > 0:
                previous_price = quote['close'][latest_idx - 1]
                if previous_price and previous_price != 0:
                    return (change / previous_price) * 100
        
        except (IndexError, TypeError, ZeroDivisionError):
            pass
        
        return None


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_yahoo_finance():
        """测试Yahoo Finance数据源"""
        yahoo = YahooFinanceSource()
        
        try:
            # 测试历史数据
            print("📈 测试历史数据获取...")
            start_date = datetime.now() - timedelta(days=30)
            data = await yahoo.get_data("AAPL", DataType.STOCK_PRICE, 
                                       DataFrequency.DAY_1, start_date)
            print(f"✅ 获取到 {len(data)} 条AAPL历史数据")
            
            if data:
                latest = data[-1]
                print(f"   最新价格: ${latest.close_price:.2f}")
                print(f"   成交量: {latest.volume:,}")
                print(f"   时间: {latest.timestamp}")
            
            # 测试实时价格
            print("\n💰 测试实时价格...")
            real_time = yahoo.get_real_time_price("AAPL")
            print(f"✅ AAPL实时价格: ${real_time['price']:.2f}")
            print(f"   变化: {real_time['change']:.2f} ({real_time['change_percent']:.2f}%)")
            
            # 测试股票信息
            print("\n📊 测试股票信息...")
            info = yahoo.get_stock_info("AAPL")
            print(f"✅ 市值: ${info.get('market_cap', 0):,.0f}")
            print(f"   PE比率: {info.get('pe_ratio', 'N/A')}")
            print(f"   Beta: {info.get('beta', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    # 运行测试
    print("🧪 Yahoo Finance数据源测试")
    print("=" * 40)
    asyncio.run(test_yahoo_finance())