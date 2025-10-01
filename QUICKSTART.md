# 🚀 5分钟快速开始指南

## 💡 三种使用方式

### 🎯 **方式一：一键配置分析（推荐新手）**

```bash
# 查看所有预设配置
python3 core/simple_cli.py config list

# 使用平衡配置分析（推荐默认）
python3 core/simple_cli.py config use balanced AAPL

# 使用激进配置分析
python3 core/simple_cli.py config use aggressive TSLA

# 使用保守配置分析
python3 core/simple_cli.py config use conservative MSFT
```

### 🔧 **方式二：创建个人配置**

```bash
# 创建自定义配置
python3 core/simple_cli.py config create my_config \
  --strategies "RSI,MACD,BollingerBands" \
  --weights "[0.5,0.3,0.2]" \
  --description "我的自定义策略"

# 使用自定义配置
python3 core/simple_cli.py config use my_config AAPL

# 查看配置详情
python3 core/simple_cli.py config show my_config
```

### 🛠️ **方式三：手动策略组合（高级用法）**

```bash
# 自定义策略组合
python3 core/simple_cli.py strategy multi "RSI,MACD,VolumeConfirmation" NVDA \
  --weights "[0.5,0.3,0.2]"

# 测试单个策略
python3 core/simple_cli.py strategy test RSI AAPL

# 列出所有可用策略
python3 core/simple_cli.py strategy list
```

---

## 📊 5种预设配置选择指南

| 配置名称 | 适用场景 | 风险等级 | 推荐人群 |
|---------|---------|---------|---------|
| `balanced` ⭐ | 通用，适合多数市场 | 中等 | 新手、普通投资者 |
| `conservative` | 震荡市场、风险控制 | 低 | 保守投资者 |
| `aggressive` | 趋势市场、追求收益 | 高 | 激进投资者 |
| `volume_focus` | 大盘股、资金流向 | 中等 | 价值投资者 |
| `technical_full` | 全面分析、确认信号 | 中低 | 专业交易者 |

---

## 🎯 实战建议

### 🔰 **新手三步走**
1. **先用平衡配置**: `python3 core/simple_cli.py config use balanced AAPL`
2. **观察分析结果**: 关注信号类型、置信度、决策依据
3. **多股票验证**: 测试不同股票，理解策略特点

### 👨‍💼 **进阶使用**
1. **根据市场选配置**: 牛市用激进、震荡用保守
2. **创建个人配置**: 根据投资偏好自定义策略组合
3. **结合基本面**: 策略信号+公司基本面=更好决策

### 🎓 **专业应用**
1. **多时间框架**: 日线、周线、月线多维度验证
2. **风险管理**: 设置止损止盈，控制仓位大小
3. **组合投资**: 多股票分散投资，降低单一风险

---

## 📈 理解分析结果

### 信号类型
- **BUY**: 买入信号，建议开仓或加仓
- **SELL**: 卖出信号，建议减仓或清仓  
- **HOLD**: 持有信号，维持当前仓位

### 置信度评分（0-1）
- **0.7+**: 高置信度，强烈建议
- **0.5-0.7**: 中等置信度，谨慎参考
- **0.3-0.5**: 低置信度，观望为主
- **0-0.3**: 极低置信度，无明确信号

### 组合策略优势
- **降低误判**: 多策略相互验证
- **风险分散**: 不依赖单一指标
- **信号稳定**: 权重分配平衡风险

---

## 🔗 更多资源

- 📖 [完整README](README.md) - 详细系统介绍
- 🎮 [演示脚本](DEMO.py) - 运行 `python3 DEMO.py` 体验
- 📋 [命令参考](docs/COMMAND_REFERENCE.md) - 所有命令说明
- 🛠️ [开发文档](docs/API_REFERENCE.md) - 二次开发指南

---

**让专业的量化交易变得像使用计算器一样简单！** 🚀