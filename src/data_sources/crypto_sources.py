"""
加密货币数据源实现

集成多个加密货币数据源：
- CoinGecko API (免费，较为稳定)
- Binance API (实时交易数据)
- CoinMarketCap API (市场数据)
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import logging

from . import BaseDataSource, CryptoData, DataType, DataFrequency, DataSourceError


class CoinGeckoSource(BaseDataSource):
    """CoinGecko加密货币数据源"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("CoinGecko", config)
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BacktraderTradingSystem/1.0'
        })
        
        # CoinGecko免费API限制：50次/分钟
        self._rate_limit = 50
    
    async def get_data(self, symbol: str, data_type: DataType,
                      frequency: DataFrequency = DataFrequency.DAY_1,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[CryptoData]:
        """获取加密货币数据"""
        
        if data_type != DataType.CRYPTO_PRICE:
            raise DataSourceError(f"CoinGecko doesn't support {data_type}")
        
        self._check_rate_limit()
        
        try:
            # 获取币种ID
            coin_id = self._get_coin_id(symbol)
            if not coin_id:
                raise DataSourceError(f"Unsupported cryptocurrency: {symbol}")
            
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # CoinGecko免费版限制90天
            
            # 获取历史数据
            days = (end_date - start_date).days
            if days > 90:
                self.logger.warning(f"Date range too large, limiting to 90 days")
                start_date = end_date - timedelta(days=90)
                days = 90
            
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': self._convert_frequency(frequency)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_coingecko_data(symbol, data, frequency)
            
        except requests.RequestException as e:
            self.logger.error(f"CoinGecko API error: {e}")
            raise DataSourceError(f"Failed to fetch data from CoinGecko: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise DataSourceError(f"Unexpected error: {e}")
    
    def get_real_time_price(self, symbol: str) -> Dict[str, Any]:
        """获取实时加密货币价格"""
        try:
            self._check_rate_limit()
            
            coin_id = self._get_coin_id(symbol)
            if not coin_id:
                raise DataSourceError(f"Unsupported cryptocurrency: {symbol}")
            
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if coin_id not in data:
                raise DataSourceError(f"No data found for {symbol}")
            
            coin_data = data[coin_id]
            
            return {
                'symbol': symbol.upper(),
                'price': coin_data['usd'],
                'market_cap': coin_data.get('usd_market_cap'),
                'volume_24h': coin_data.get('usd_24h_vol', 0),
                'change_24h': coin_data.get('usd_24h_change'),
                'timestamp': datetime.fromtimestamp(coin_data.get('last_updated_at', time.time()))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get real-time price for {symbol}: {e}")
            raise DataSourceError(f"Real-time price error: {e}")
    
    def get_market_data(self, symbols: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取加密货币市场数据"""
        try:
            self._check_rate_limit()
            
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': min(limit, 250),  # CoinGecko限制每页最多250个
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h,7d,30d'
            }
            
            if symbols:
                # 转换为coin_id
                coin_ids = []
                for symbol in symbols:
                    coin_id = self._get_coin_id(symbol)
                    if coin_id:
                        coin_ids.append(coin_id)
                
                if coin_ids:
                    params['ids'] = ','.join(coin_ids)
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            market_data = []
            for coin in data:
                market_data.append({
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'price': coin['current_price'],
                    'market_cap': coin['market_cap'],
                    'market_cap_rank': coin['market_cap_rank'],
                    'volume_24h': coin['total_volume'],
                    'price_change_24h': coin['price_change_24h'],
                    'price_change_percentage_24h': coin['price_change_percentage_24h'],
                    'price_change_percentage_7d': coin.get('price_change_percentage_7d_in_currency'),
                    'price_change_percentage_30d': coin.get('price_change_percentage_30d_in_currency'),
                    'circulating_supply': coin['circulating_supply'],
                    'total_supply': coin['total_supply'],
                    'max_supply': coin['max_supply'],
                    'ath': coin['ath'],  # All-time high
                    'ath_date': coin['ath_date'],
                    'atl': coin['atl'],  # All-time low
                    'atl_date': coin['atl_date'],
                    'last_updated': coin['last_updated']
                })
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Failed to get market data: {e}")
            raise DataSourceError(f"Market data error: {e}")
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的加密货币代码"""
        # 主要加密货币列表
        return [
            # 主流币
            "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "AVAX", "SHIB",
            # DeFi代币
            "UNI", "LINK", "AAVE", "SUSHI", "COMP", "MKR", "YFI", "CRV", "BAL",
            # Layer 1
            "LUNA", "ATOM", "NEAR", "ALGO", "EGLD", "FLOW", "ICP", "FTM", "ONE",
            # 稳定币
            "USDT", "USDC", "BUSD", "DAI", "FRAX", "TUSD", "USDP", "LUSD",
            # 其他
            "LTC", "BCH", "ETC", "XLM", "VET", "FIL", "THETA", "TRX", "EOS"
        ]
    
    def _get_coin_id(self, symbol: str) -> Optional[str]:
        """获取CoinGecko的币种ID"""
        # 常用币种的symbol到id映射
        symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOGE': 'dogecoin',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2',
            'SHIB': 'shiba-inu',
            'MATIC': 'matic-network',
            'UNI': 'uniswap',
            'LINK': 'chainlink',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'ATOM': 'cosmos',
            'NEAR': 'near',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'FIL': 'filecoin',
            'THETA': 'theta-token',
            'TRX': 'tron',
            'EOS': 'eos',
            'XLM': 'stellar',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'BUSD': 'binance-usd',
            'DAI': 'dai'
        }
        
        return symbol_to_id.get(symbol.upper())
    
    def _convert_frequency(self, frequency: DataFrequency) -> str:
        """转换频率格式"""
        # CoinGecko支持的间隔：daily, hourly (仅限1-7天数据)
        mapping = {
            DataFrequency.MINUTE_1: "hourly",
            DataFrequency.MINUTE_5: "hourly", 
            DataFrequency.MINUTE_15: "hourly",
            DataFrequency.HOUR_1: "hourly",
            DataFrequency.DAY_1: "daily",
            DataFrequency.WEEK_1: "daily",
            DataFrequency.MONTH_1: "daily"
        }
        return mapping.get(frequency, "daily")
    
    def _parse_coingecko_data(self, symbol: str, data: Dict, frequency: DataFrequency) -> List[CryptoData]:
        """解析CoinGecko返回的数据"""
        try:
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            market_caps = data.get('market_caps', [])
            
            crypto_data_list = []
            
            # 确保所有数据长度一致
            min_length = min(len(prices), len(volumes), len(market_caps))
            
            for i in range(min_length):
                timestamp_ms, price = prices[i]
                _, volume = volumes[i]
                _, market_cap = market_caps[i]
                
                # 跳过无效数据
                if price is None or price <= 0:
                    continue
                
                crypto_data = CryptoData(
                    symbol=symbol.upper(),
                    timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                    data_type=DataType.CRYPTO_PRICE,
                    frequency=frequency,
                    data={'market_cap': market_cap},
                    source=self.name,
                    price=float(price),
                    volume_24h=float(volume) if volume else 0,
                    market_cap=float(market_cap) if market_cap else None
                )
                
                if self.validate_data(crypto_data):
                    crypto_data_list.append(crypto_data)
                else:
                    self.logger.warning(f"Invalid crypto data point skipped: {timestamp_ms}")
            
            self.logger.info(f"Successfully parsed {len(crypto_data_list)} crypto data points for {symbol}")
            return crypto_data_list
            
        except KeyError as e:
            raise DataSourceError(f"Unexpected data format from CoinGecko: {e}")
        except Exception as e:
            raise DataSourceError(f"Failed to parse CoinGecko data: {e}")


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_coingecko():
        """测试CoinGecko数据源"""
        coingecko = CoinGeckoSource()
        
        try:
            # 测试实时价格
            print("💰 测试加密货币实时价格...")
            btc_price = coingecko.get_real_time_price("BTC")
            print(f"✅ BTC价格: ${btc_price['price']:,.2f}")
            print(f"   24h变化: {btc_price['change_24h']:.2f}%")
            print(f"   市值: ${btc_price['market_cap']:,.0f}")
            
            # 测试历史数据
            print("\n📈 测试历史数据获取...")
            start_date = datetime.now() - timedelta(days=7)
            eth_data = await coingecko.get_data("ETH", DataType.CRYPTO_PRICE,
                                               DataFrequency.DAY_1, start_date)
            print(f"✅ 获取到 {len(eth_data)} 条ETH历史数据")
            
            if eth_data:
                latest = eth_data[-1]
                print(f"   最新价格: ${latest.price:.2f}")
                print(f"   24h成交量: ${latest.volume_24h:,.0f}")
                print(f"   时间: {latest.timestamp}")
            
            # 测试市场数据
            print("\n📊 测试市场数据...")
            market_data = coingecko.get_market_data(['BTC', 'ETH', 'BNB'], limit=3)
            print(f"✅ 获取到 {len(market_data)} 个币种的市场数据")
            
            for coin in market_data:
                print(f"   {coin['symbol']}: ${coin['price']:,.2f} (市值排名: #{coin['market_cap_rank']})")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    # 运行测试
    print("🧪 CoinGecko数据源测试")
    print("=" * 40)
    asyncio.run(test_coingecko())