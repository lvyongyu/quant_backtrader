"""
经济数据源实现

提供宏观经济指标数据：
- FRED (Federal Reserve Economic Data) - 美联储经济数据
- World Bank API - 世界银行数据
- OECD API - 经合组织数据
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import logging

from . import BaseDataSource, EconomicData, DataType, DataFrequency, DataSourceError


class FREDSource(BaseDataSource):
    """美联储经济数据源 (FRED)"""
    
    def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
        super().__init__("FRED", config)
        self.api_key = api_key or self.config.get('api_key')
        self.base_url = "https://api.stlouisfed.org/fred"
        self.session = requests.Session()
        
        if not self.api_key:
            self.logger.warning("FRED API key not provided, using demo mode with limited data")
        
        # FRED API限制：120次/分钟
        self._rate_limit = 120
    
    async def get_data(self, symbol: str, data_type: DataType,
                      frequency: DataFrequency = DataFrequency.DAY_1,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> List[EconomicData]:
        """获取经济指标数据"""
        
        if data_type != DataType.ECONOMIC_INDICATOR:
            raise DataSourceError(f"FRED doesn't support {data_type}")
        
        self._check_rate_limit()
        
        try:
            # 获取FRED系列ID
            series_id = self._get_series_id(symbol)
            if not series_id:
                raise DataSourceError(f"Unsupported economic indicator: {symbol}")
            
            # 设置默认日期范围
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=365*2)  # 默认2年数据
            
            # 获取数据
            url = f"{self.base_url}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key or 'demo',
                'file_type': 'json',
                'observation_start': start_date.strftime('%Y-%m-%d'),
                'observation_end': end_date.strftime('%Y-%m-%d'),
                'frequency': self._convert_frequency(frequency),
                'aggregation_method': 'avg'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_fred_data(symbol, series_id, data, frequency)
            
        except requests.RequestException as e:
            self.logger.error(f"FRED API error: {e}")
            raise DataSourceError(f"Failed to fetch data from FRED: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise DataSourceError(f"Unexpected error: {e}")
    
    def get_indicator_info(self, symbol: str) -> Dict[str, Any]:
        """获取经济指标信息"""
        try:
            self._check_rate_limit()
            
            series_id = self._get_series_id(symbol)
            if not series_id:
                raise DataSourceError(f"Unsupported economic indicator: {symbol}")
            
            url = f"{self.base_url}/series"
            params = {
                'series_id': series_id,
                'api_key': self.api_key or 'demo',
                'file_type': 'json'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'seriess' in data and data['seriess']:
                series_info = data['seriess'][0]
                return {
                    'id': series_info['id'],
                    'title': series_info['title'],
                    'units': series_info['units'],
                    'frequency': series_info['frequency'],
                    'seasonal_adjustment': series_info['seasonal_adjustment'],
                    'last_updated': series_info['last_updated'],
                    'observation_start': series_info['observation_start'],
                    'observation_end': series_info['observation_end'],
                    'popularity': series_info.get('popularity', 0)
                }
            else:
                raise DataSourceError("No series information found")
            
        except Exception as e:
            self.logger.error(f"Failed to get indicator info for {symbol}: {e}")
            raise DataSourceError(f"Indicator info error: {e}")
    
    def get_latest_indicators(self, indicators: List[str] = None) -> Dict[str, Any]:
        """获取最新的经济指标数据"""
        try:
            if not indicators:
                indicators = ['GDP', 'CPI', 'UNEMPLOYMENT', 'FEDFUNDS', 'DGS10']  # 默认重要指标
            
            latest_data = {}
            
            for indicator in indicators:
                try:
                    # 获取最近的数据点
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=180)  # 最近6个月
                    
                    data = await self.get_data(indicator, DataType.ECONOMIC_INDICATOR,
                                             DataFrequency.MONTH_1, start_date, end_date)
                    
                    if data:
                        latest = data[-1]
                        latest_data[indicator] = {
                            'value': latest.value,
                            'unit': latest.unit,
                            'date': latest.release_date,
                            'previous_value': latest.previous_value
                        }
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get data for {indicator}: {e}")
                    continue
            
            return latest_data
            
        except Exception as e:
            self.logger.error(f"Failed to get latest indicators: {e}")
            raise DataSourceError(f"Latest indicators error: {e}")
    
    def get_supported_symbols(self) -> List[str]:
        """获取支持的经济指标代码"""
        return [
            # 主要经济指标
            'GDP',          # 国内生产总值
            'CPI',          # 消费者价格指数
            'UNEMPLOYMENT', # 失业率
            'FEDFUNDS',     # 联邦基金利率
            'DGS10',        # 10年期国债收益率
            'DGS2',         # 2年期国债收益率
            'DGS30',        # 30年期国债收益率
            'DEXUSEU',      # 美元欧元汇率
            'DEXCHUS',      # 人民币美元汇率
            'VIXCLS',       # VIX恐慌指数
            
            # 制造业和商业
            'INDPRO',       # 工业生产指数
            'HOUST',        # 新房开工数
            'PAYEMS',       # 非农就业人数
            'RETAIL',       # 零售销售
            'UMCSENT',      # 密歇根消费者信心指数
            
            # 货币供应量
            'M1SL',         # M1货币供应量
            'M2SL',         # M2货币供应量
            'BASE',         # 货币基础
            
            # 价格和通胀
            'CPILFESL',     # 核心CPI
            'PCEPI',        # PCE价格指数
            'DFEDTARU',     # 联邦目标利率上限
            'DFEDTARL',     # 联邦目标利率下限
        ]
    
    def _get_series_id(self, symbol: str) -> Optional[str]:
        """获取FRED数据系列ID"""
        symbol_to_series = {
            'GDP': 'GDP',
            'CPI': 'CPIAUCSL',
            'UNEMPLOYMENT': 'UNRATE',
            'FEDFUNDS': 'FEDFUNDS',
            'DGS10': 'DGS10',
            'DGS2': 'DGS2',
            'DGS30': 'DGS30',
            'DEXUSEU': 'DEXUSEU',
            'DEXCHUS': 'DEXCHUS',
            'VIXCLS': 'VIXCLS',
            'INDPRO': 'INDPRO',
            'HOUST': 'HOUST',
            'PAYEMS': 'PAYEMS',
            'RETAIL': 'RSAFS',
            'UMCSENT': 'UMCSENT',
            'M1SL': 'M1SL',
            'M2SL': 'M2SL',
            'BASE': 'BASE',
            'CPILFESL': 'CPILFESL',
            'PCEPI': 'PCEPI',
            'DFEDTARU': 'DFEDTARU',
            'DFEDTARL': 'DFEDTARL'
        }
        
        return symbol_to_series.get(symbol.upper())
    
    def _convert_frequency(self, frequency: DataFrequency) -> str:
        """转换频率格式"""
        mapping = {
            DataFrequency.DAY_1: 'd',
            DataFrequency.WEEK_1: 'w',
            DataFrequency.MONTH_1: 'm',
        }
        return mapping.get(frequency, 'm')  # 默认月度
    
    def _parse_fred_data(self, symbol: str, series_id: str, data: Dict, frequency: DataFrequency) -> List[EconomicData]:
        """解析FRED返回的数据"""
        try:
            observations = data.get('observations', [])
            
            economic_data_list = []
            previous_value = None
            
            for obs in observations:
                value_str = obs['value']
                date_str = obs['date']
                
                # 跳过无效数据
                if value_str == '.' or value_str == '' or value_str is None:
                    continue
                
                try:
                    value = float(value_str)
                    release_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    # 获取指标单位信息
                    indicator_info = self._get_indicator_unit(symbol)
                    
                    economic_data = EconomicData(
                        symbol=symbol.upper(),
                        timestamp=release_date,
                        data_type=DataType.ECONOMIC_INDICATOR,
                        frequency=frequency,
                        data={'series_id': series_id},
                        source=self.name,
                        indicator_name=indicator_info['name'],
                        value=value,
                        unit=indicator_info['unit'],
                        release_date=release_date,
                        previous_value=previous_value
                    )
                    
                    economic_data_list.append(economic_data)
                    previous_value = value
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Invalid data value: {value_str}, error: {e}")
                    continue
            
            self.logger.info(f"Successfully parsed {len(economic_data_list)} economic data points for {symbol}")
            return economic_data_list
            
        except KeyError as e:
            raise DataSourceError(f"Unexpected data format from FRED: {e}")
        except Exception as e:
            raise DataSourceError(f"Failed to parse FRED data: {e}")
    
    def _get_indicator_unit(self, symbol: str) -> Dict[str, str]:
        """获取指标名称和单位"""
        indicator_info = {
            'GDP': {'name': 'Gross Domestic Product', 'unit': 'Billions of Dollars'},
            'CPI': {'name': 'Consumer Price Index', 'unit': 'Index 1982-1984=100'},
            'UNEMPLOYMENT': {'name': 'Unemployment Rate', 'unit': 'Percent'},
            'FEDFUNDS': {'name': 'Federal Funds Rate', 'unit': 'Percent'},
            'DGS10': {'name': '10-Year Treasury Rate', 'unit': 'Percent'},
            'DGS2': {'name': '2-Year Treasury Rate', 'unit': 'Percent'},
            'DGS30': {'name': '30-Year Treasury Rate', 'unit': 'Percent'},
            'DEXUSEU': {'name': 'US Dollar to Euro', 'unit': 'Exchange Rate'},
            'DEXCHUS': {'name': 'Chinese Yuan to US Dollar', 'unit': 'Exchange Rate'},
            'VIXCLS': {'name': 'CBOE Volatility Index', 'unit': 'Index'},
            'INDPRO': {'name': 'Industrial Production Index', 'unit': 'Index 2017=100'},
            'HOUST': {'name': 'Housing Starts', 'unit': 'Thousands of Units'},
            'PAYEMS': {'name': 'Nonfarm Payrolls', 'unit': 'Thousands of Persons'},
            'RETAIL': {'name': 'Retail Sales', 'unit': 'Millions of Dollars'},
            'UMCSENT': {'name': 'University of Michigan Consumer Sentiment', 'unit': 'Index 1966:Q1=100'}
        }
        
        return indicator_info.get(symbol.upper(), {'name': symbol, 'unit': 'Unknown'})


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_fred():
        """测试FRED数据源"""
        # 注意：需要FRED API key，这里使用demo模式
        fred = FREDSource()
        
        try:
            # 测试指标信息
            print("📊 测试经济指标信息...")
            gdp_info = fred.get_indicator_info("GDP")
            print(f"✅ GDP指标信息:")
            print(f"   标题: {gdp_info['title']}")
            print(f"   单位: {gdp_info['units']}")
            print(f"   频率: {gdp_info['frequency']}")
            
            # 测试历史数据
            print("\n📈 测试历史数据获取...")
            start_date = datetime.now() - timedelta(days=365)
            unemployment_data = await fred.get_data("UNEMPLOYMENT", DataType.ECONOMIC_INDICATOR,
                                                   DataFrequency.MONTH_1, start_date)
            print(f"✅ 获取到 {len(unemployment_data)} 条失业率数据")
            
            if unemployment_data:
                latest = unemployment_data[-1]
                print(f"   最新失业率: {latest.value}%")
                print(f"   发布日期: {latest.release_date}")
                print(f"   前值: {latest.previous_value}%")
            
            # 测试最新指标
            print("\n📊 测试最新指标...")
            latest_indicators = await fred.get_latest_indicators(['FEDFUNDS', 'DGS10', 'CPI'])
            
            for indicator, data in latest_indicators.items():
                print(f"   {indicator}: {data['value']}{data['unit']} (发布: {data['date'].strftime('%Y-%m-%d')})")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    # 运行测试
    print("🧪 FRED经济数据源测试")
    print("=" * 40)
    asyncio.run(test_fred())