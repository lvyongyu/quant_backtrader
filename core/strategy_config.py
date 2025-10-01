"""
策略配置管理模块

允许用户创建、保存和管理自定义的策略组合配置。
"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class StrategyConfig:
    """策略配置类"""
    name: str
    strategies: List[str]
    weights: List[float]
    description: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'name': self.name,
            'strategies': self.strategies,
            'weights': self.weights,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyConfig':
        """从字典创建"""
        return cls(
            name=data['name'],
            strategies=data['strategies'],
            weights=data['weights'],
            description=data.get('description', '')
        )

class StrategyConfigManager:
    """策略配置管理器"""
    
    def __init__(self, config_file: str = "data/strategy_configs.json"):
        self.config_file = config_file
        self.configs: Dict[str, StrategyConfig] = {}
        self._ensure_config_dir()
        self._load_configs()
        self._create_default_configs()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
    
    def _load_configs(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, config_data in data.items():
                        self.configs[name] = StrategyConfig.from_dict(config_data)
                logger.info(f"已加载 {len(self.configs)} 个策略配置")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
    
    def _save_configs(self):
        """保存配置文件"""
        try:
            data = {name: config.to_dict() for name, config in self.configs.items()}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存 {len(self.configs)} 个策略配置")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def _create_default_configs(self):
        """创建默认配置"""
        default_configs = [
            StrategyConfig(
                name="conservative",
                strategies=["MeanReversion", "RSI", "BollingerBands"],
                weights=[0.4, 0.4, 0.2],
                description="保守型策略组合，注重风险控制，适合震荡市场"
            ),
            StrategyConfig(
                name="aggressive", 
                strategies=["MomentumBreakout", "MA_Cross", "MACD"],
                weights=[0.5, 0.3, 0.2],
                description="激进型策略组合，追求趋势突破，适合趋势市场"
            ),
            StrategyConfig(
                name="balanced",
                strategies=["MomentumBreakout", "MeanReversion", "RSI", "VolumeConfirmation"],
                weights=[0.3, 0.3, 0.25, 0.15],
                description="平衡型策略组合，兼顾趋势和反转，适合多数市场环境"
            ),
            StrategyConfig(
                name="volume_focus",
                strategies=["VolumeConfirmation", "MomentumBreakout", "MACD"],
                weights=[0.5, 0.3, 0.2],
                description="成交量导向策略，重视资金流向分析"
            ),
            StrategyConfig(
                name="technical_full",
                strategies=["MomentumBreakout", "MeanReversion", "VolumeConfirmation", "RSI", "MACD", "MA_Cross", "BollingerBands"],
                weights=[0.2, 0.15, 0.15, 0.15, 0.15, 0.1, 0.1],
                description="全技术分析策略，包含所有可用策略的综合分析"
            )
        ]
        
        # 只添加不存在的默认配置
        for config in default_configs:
            if config.name not in self.configs:
                self.configs[config.name] = config
        
        # 如果有新的默认配置，保存到文件
        if any(config.name not in self.configs for config in default_configs):
            self._save_configs()
    
    def list_configs(self) -> List[StrategyConfig]:
        """列出所有配置"""
        return list(self.configs.values())
    
    def get_config(self, name: str) -> Optional[StrategyConfig]:
        """获取指定配置"""
        return self.configs.get(name)
    
    def create_config(self, name: str, strategies: List[str], weights: List[float], description: str = "") -> bool:
        """创建新配置"""
        if len(strategies) != len(weights):
            raise ValueError("策略数量和权重数量必须一致")
        
        if abs(sum(weights) - 1.0) > 0.01:
            raise ValueError("权重总和必须等于1.0")
        
        # 验证策略名称
        from strategy_manager import get_available_strategies
        available_strategies = get_available_strategies()
        for strategy in strategies:
            if strategy not in available_strategies:
                raise ValueError(f"未知策略: {strategy}")
        
        config = StrategyConfig(name, strategies, weights, description)
        self.configs[name] = config
        self._save_configs()
        return True
    
    def delete_config(self, name: str) -> bool:
        """删除配置"""
        if name not in self.configs:
            return False
        
        # 不允许删除默认配置
        default_names = ["conservative", "aggressive", "balanced", "volume_focus", "technical_full"]
        if name in default_names:
            raise ValueError(f"不能删除默认配置: {name}")
        
        del self.configs[name]
        self._save_configs()
        return True
    
    def get_default_config(self) -> str:
        """获取默认配置名称"""
        return "balanced"

# 全局配置管理器实例
_config_manager = None

def get_config_manager() -> StrategyConfigManager:
    """获取配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = StrategyConfigManager()
    return _config_manager

def list_strategy_configs() -> List[StrategyConfig]:
    """列出所有策略配置"""
    return get_config_manager().list_configs()

def get_strategy_config(name: str) -> Optional[StrategyConfig]:
    """获取指定策略配置"""
    return get_config_manager().get_config(name)

def create_strategy_config(name: str, strategies: List[str], weights: List[float], description: str = "") -> bool:
    """创建策略配置"""
    return get_config_manager().create_config(name, strategies, weights, description)

def delete_strategy_config(name: str) -> bool:
    """删除策略配置"""
    return get_config_manager().delete_config(name)

def get_default_strategy_config() -> str:
    """获取默认策略配置名称"""
    return get_config_manager().get_default_config()

# 使用示例
if __name__ == "__main__":
    print("🔧 策略配置管理器演示")
    print("=" * 50)
    
    # 列出所有配置
    configs = list_strategy_configs()
    print(f"✅ 可用配置 ({len(configs)}个):")
    for config in configs:
        print(f"  • {config.name}: {config.description}")
        print(f"    策略: {', '.join(config.strategies)}")
        print(f"    权重: {config.weights}")
        print()
    
    # 获取默认配置
    default_name = get_default_strategy_config()
    default_config = get_strategy_config(default_name)
    print(f"🎯 默认配置: {default_name}")
    if default_config:
        print(f"  描述: {default_config.description}")
        print(f"  策略: {', '.join(default_config.strategies)}")
        print(f"  权重: {default_config.weights}")