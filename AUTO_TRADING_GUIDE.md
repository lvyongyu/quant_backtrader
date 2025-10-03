# 🚀 自动交易完整操作指南

## 📋 概述
这个指南将带你从零开始配置并启动基于自选股票的实时自动交易系统。

## 🎯 第一步：配置自选股票池

### 1.1 查看当前自选股
```bash
python3 main.py watchlist list
```

### 1.2 添加股票到自选股池
```bash
# 添加单只股票
python3 main.py watchlist add AAPL
python3 main.py watchlist add MSFT
python3 main.py watchlist add GOOGL
python3 main.py watchlist add TSLA

# 查看股票分析
python3 main.py watchlist analyze AAPL
```

### 1.3 管理自选股池
```bash
# 移除股票
python3 main.py watchlist remove XYZ

# 查看统计信息
python3 main.py watchlist stats

# 清空所有（慎用）
python3 main.py watchlist clear
```

## ⚙️ 第二步：选择和测试交易策略

### 2.1 可用策略类型
系统提供以下预配置策略组合：

- **conservative**: 保守型策略（MeanReversion + RSI + BollingerBands）
- **aggressive**: 激进型策略（MomentumBreakout + MA_Cross + MACD）
- **balanced**: 平衡型策略（MomentumBreakout + MeanReversion + RSI + VolumeConfirmation）
- **volume_focus**: 成交量导向策略
- **technical_full**: 全技术分析策略
- **my_custom**: 自定义策略（可修改）

### 2.2 测试单个策略
```bash
# 测试RSI策略在特定股票上的表现
python3 main.py strategy test RSI TSLA
python3 main.py strategy test MACD AAPL
python3 main.py strategy test MomentumBreakout MSFT
```

### 2.3 可用的单个策略
- MomentumBreakout: 动量突破策略
- MeanReversion: 均值回归策略  
- VolumeConfirmation: 成交量确认策略
- MA_Cross: 移动平均交叉策略
- RSI: 相对强弱指数策略
- MACD: 指数平滑移动平均策略
- BollingerBands: 布林带策略

## 🚀 第三步：启动自动交易

### 3.1 启动实时监控模式
```bash
# 启动实时交易监控（推荐新手先用这个观察）
python3 main.py trade monitor
```

这个命令会：
- 启动实时数据获取
- 应用配置的策略组合分析自选股
- 显示实时信号但不执行真实交易
- 提供性能监控和统计

### 3.2 查看交易状态
```bash
# 查看当前交易状态
python3 main.py trade status

# 查看风险监控
python3 main.py trade risk
```

### 3.3 启动实际自动交易（高级用户）
```bash
# 启动实际自动交易（需要配置真实券商接口）
python3 main.py trade start
```

## 📊 第四步：监控和分析

### 4.1 性能监控
```bash
# 查看交易性能
python3 main.py performance stats
python3 main.py performance report
python3 main.py performance analysis
```

### 4.2 高级功能
```bash
# 异常检测
python3 main.py advanced anomaly

# 机器学习增强
python3 main.py advanced ml

# 风险压力测试
python3 main.py advanced stress-test
```

## 🔧 第五步：自定义配置

### 5.1 修改策略配置
编辑 `data/strategy_configs.json` 文件来自定义策略组合：

```json
{
  "my_custom": {
    "name": "my_custom",
    "strategies": [
      "RSI",
      "MACD", 
      "MomentumBreakout"
    ],
    "weights": [
      0.4,
      0.3,
      0.3
    ],
    "description": "我的自定义策略组合"
  }
}
```

### 5.2 风险控制设置
编辑 `production_risk_config.py` 调整风险参数：

```python
# 风险控制参数
MAX_POSITION_SIZE = 0.1  # 单只股票最大仓位10%
STOP_LOSS_PERCENT = 0.05  # 止损5%
TAKE_PROFIT_PERCENT = 0.15  # 止盈15%
MAX_DAILY_LOSS = 0.02  # 日最大亏损2%
```

## ⚡ 每日自动交易流程

### 推荐的日常操作流程：

1. **早上开盘前 (9:00 AM)**:
   ```bash
   # 检查系统状态
   python3 system_status_check.py
   
   # 查看自选股池
   python3 main.py watchlist stats
   ```

2. **开盘后启动监控 (9:30 AM)**:
   ```bash
   # 启动实时监控
   python3 main.py trade monitor
   ```

3. **盘中监控**:
   - 系统会自动分析实时数据
   - 根据配置的策略生成交易信号
   - 显示实时性能统计

4. **收盘后分析 (4:30 PM)**:
   ```bash
   # 查看当日表现
   python3 main.py performance report
   
   # 更新自选股评分
   python3 main.py watchlist analyze
   ```

## 🛡️ 安全提醒

1. **模拟交易**: 新手建议先使用 `trade monitor` 模式观察信号
2. **风险控制**: 确保设置合理的止损和仓位限制
3. **资金管理**: 不要投入超过可承受损失的资金
4. **策略测试**: 新策略要先充分回测验证
5. **市场风险**: 任何策略都不能保证盈利，注意市场风险

## 📞 故障排除

### 常见问题：
1. **数据获取失败**: 检查网络连接和Yahoo Finance访问
2. **策略错误**: 确认策略名称拼写正确
3. **事件循环错误**: 重启系统或检查系统状态

### 获取帮助：
```bash
# 系统诊断
python3 system_status_check.py

# 查看日志
tail -f logs/trading.log
```

## 🎯 开始使用

现在你可以按照以下步骤开始：

1. 配置你的自选股池
2. 选择适合的策略组合  
3. 启动监控模式观察
4. 优化策略参数
5. 谨慎开始实盘交易

**祝你交易顺利！** 🚀