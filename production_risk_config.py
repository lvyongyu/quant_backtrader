"""
生产环境风险管理配置

为实际交易环境设置保守的风险参数，确保资金安全。
配置遵循"安全第一"原则，宁可错过机会也不承担过大风险。
"""

from dataclasses import dataclass
from src.risk import RiskLimits
from typing import Dict, Any


@dataclass
class ProductionRiskConfig:
    """生产环境风险配置"""
    
    # 基础风险限制
    max_daily_loss_pct: float = 0.015      # 1.5% 日最大亏损（比默认更保守）
    max_single_trade_loss_pct: float = 0.003  # 0.3% 单笔最大亏损
    max_position_pct: float = 0.08         # 8% 单仓位最大比例
    max_total_position_pct: float = 0.70   # 70% 总仓位限制（保留30%现金）
    max_consecutive_losses: int = 3        # 最大连续亏损3次
    min_account_value: float = 50000.0     # 最小账户价值5万美元
    
    # 高级风险控制
    max_correlation: float = 0.6           # 最大相关性（降低集中风险）
    max_leverage: float = 1.0              # 禁用杠杆
    max_drawdown_threshold: float = 0.05   # 5%最大回撤警告线
    
    # 风险监控参数
    check_interval_seconds: int = 30       # 30秒监控间隔
    alert_cooldown_minutes: int = 5        # 5分钟警报冷却
    emergency_stop_enabled: bool = True    # 启用紧急停止
    
    # 市场条件参数
    volatility_threshold: float = 0.25     # 25%波动率阈值
    volume_threshold_pct: float = 0.5      # 50%成交量阈值
    market_hours_only: bool = True         # 仅在交易时间内交易
    
    def to_risk_limits(self) -> RiskLimits:
        """转换为RiskLimits对象"""
        return RiskLimits(
            max_daily_loss_pct=self.max_daily_loss_pct,
            max_single_loss_pct=self.max_single_trade_loss_pct,
            max_position_pct=self.max_position_pct,
            max_total_position_pct=self.max_total_position_pct,
            max_consecutive_losses=self.max_consecutive_losses,
            min_account_value=self.min_account_value,
            max_correlation=self.max_correlation,
            max_leverage=self.max_leverage
        )


@dataclass
class AggressiveRiskConfig:
    """激进交易风险配置（仅限有经验的交易者）"""
    
    max_daily_loss_pct: float = 0.025      # 2.5% 日最大亏损
    max_single_trade_loss_pct: float = 0.005  # 0.5% 单笔最大亏损
    max_position_pct: float = 0.15         # 15% 单仓位最大比例
    max_total_position_pct: float = 0.85   # 85% 总仓位限制
    max_consecutive_losses: int = 5        # 最大连续亏损5次
    min_account_value: float = 100000.0    # 最小账户价值10万美元
    max_correlation: float = 0.8
    max_leverage: float = 1.0
    max_drawdown_threshold: float = 0.08   # 8%最大回撤警告线
    
    def to_risk_limits(self) -> RiskLimits:
        """转换为RiskLimits对象"""
        return RiskLimits(
            max_daily_loss_pct=self.max_daily_loss_pct,
            max_single_loss_pct=self.max_single_trade_loss_pct,
            max_position_pct=self.max_position_pct,
            max_total_position_pct=self.max_total_position_pct,
            max_consecutive_losses=self.max_consecutive_losses,
            min_account_value=self.min_account_value,
            max_correlation=self.max_correlation,
            max_leverage=self.max_leverage
        )


@dataclass
class ConservativeRiskConfig:
    """保守交易风险配置（适合新手）"""
    
    max_daily_loss_pct: float = 0.01       # 1% 日最大亏损
    max_single_trade_loss_pct: float = 0.002  # 0.2% 单笔最大亏损
    max_position_pct: float = 0.05         # 5% 单仓位最大比例
    max_total_position_pct: float = 0.50   # 50% 总仓位限制
    max_consecutive_losses: int = 2        # 最大连续亏损2次
    min_account_value: float = 25000.0     # 最小账户价值2.5万美元
    max_correlation: float = 0.5
    max_leverage: float = 1.0
    max_drawdown_threshold: float = 0.03   # 3%最大回撤警告线
    
    def to_risk_limits(self) -> RiskLimits:
        """转换为RiskLimits对象"""
        return RiskLimits(
            max_daily_loss_pct=self.max_daily_loss_pct,
            max_single_loss_pct=self.max_single_trade_loss_pct,
            max_position_pct=self.max_position_pct,
            max_total_position_pct=self.max_total_position_pct,
            max_consecutive_losses=self.max_consecutive_losses,
            min_account_value=self.min_account_value,
            max_correlation=self.max_correlation,
            max_leverage=self.max_leverage
        )


class RiskConfigManager:
    """风险配置管理器"""
    
    PROFILES = {
        'conservative': ConservativeRiskConfig,
        'production': ProductionRiskConfig,
        'aggressive': AggressiveRiskConfig
    }
    
    @classmethod
    def get_config(cls, profile: str = 'production') -> RiskLimits:
        """获取指定配置文件的风险限制"""
        if profile not in cls.PROFILES:
            raise ValueError(f"未知配置文件: {profile}. 可用: {list(cls.PROFILES.keys())}")
        
        config_class = cls.PROFILES[profile]
        config = config_class()
        return config.to_risk_limits()
    
    @classmethod
    def get_config_summary(cls, profile: str = 'production') -> Dict[str, Any]:
        """获取配置摘要"""
        config_class = cls.PROFILES[profile]
        config = config_class()
        
        return {
            'profile': profile,
            'description': cls._get_profile_description(profile),
            'daily_loss_limit': f"{config.max_daily_loss_pct:.1%}",
            'single_trade_limit': f"{config.max_single_trade_loss_pct:.1%}",
            'max_position': f"{config.max_position_pct:.0%}",
            'total_position_limit': f"{config.max_total_position_pct:.0%}",
            'consecutive_losses': config.max_consecutive_losses,
            'min_account': f"${config.min_account_value:,.0f}",
            'suitable_for': cls._get_suitable_for(profile)
        }
    
    @classmethod
    def _get_profile_description(cls, profile: str) -> str:
        """获取配置文件描述"""
        descriptions = {
            'conservative': '保守配置 - 适合新手交易者，风险极低',
            'production': '生产配置 - 平衡风险与收益，适合日常交易',
            'aggressive': '激进配置 - 高风险高收益，仅限有经验交易者'
        }
        return descriptions.get(profile, '未知配置')
    
    @classmethod
    def _get_suitable_for(cls, profile: str) -> str:
        """获取适用人群"""
        suitable = {
            'conservative': '交易新手，小资金账户，风险厌恶者',
            'production': '有经验交易者，中等资金，稳健策略',
            'aggressive': '专业交易者，大资金账户，高风险承受力'
        }
        return suitable.get(profile, '未知')
    
    @classmethod
    def list_all_profiles(cls) -> Dict[str, Dict[str, Any]]:
        """列出所有配置文件"""
        result = {}
        for profile in cls.PROFILES.keys():
            result[profile] = cls.get_config_summary(profile)
        return result


# 预定义配置实例
CONSERVATIVE_CONFIG = ConservativeRiskConfig()
PRODUCTION_CONFIG = ProductionRiskConfig()
AGGRESSIVE_CONFIG = AggressiveRiskConfig()


def create_custom_config(
    daily_loss_pct: float = 0.015,
    single_trade_loss_pct: float = 0.003,
    position_pct: float = 0.08,
    consecutive_losses: int = 3,
    min_account_value: float = 50000.0
) -> RiskLimits:
    """创建自定义风险配置"""
    
    return RiskLimits(
        max_daily_loss_pct=daily_loss_pct,
        max_single_loss_pct=single_trade_loss_pct,
        max_position_pct=position_pct,
        max_total_position_pct=0.80,  # 固定80%
        max_consecutive_losses=consecutive_losses,
        min_account_value=min_account_value,
        max_correlation=0.7,
        max_leverage=1.0
    )


if __name__ == "__main__":
    print("🛡️ 风险管理配置文件")
    print("=" * 50)
    
    # 显示所有配置
    profiles = RiskConfigManager.list_all_profiles()
    
    for profile_name, details in profiles.items():
        print(f"\\n📋 {profile_name.upper()} 配置:")
        print(f"  描述: {details['description']}")
        print(f"  日亏损限制: {details['daily_loss_limit']}")
        print(f"  单笔亏损限制: {details['single_trade_limit']}")
        print(f"  最大仓位: {details['max_position']}")
        print(f"  连续亏损限制: {details['consecutive_losses']}次")
        print(f"  最小账户: {details['min_account']}")
        print(f"  适用人群: {details['suitable_for']}")
    
    print("\\n💡 配置选择建议:")
    print("  🔰 新手: conservative (安全第一)")
    print("  📈 日常: production (平衡风险)")
    print("  🚀 专业: aggressive (高风险高收益)")
    
    print("\\n⚙️ 使用方法:")
    print("  from production_risk_config import RiskConfigManager")
    print("  risk_limits = RiskConfigManager.get_config('production')")