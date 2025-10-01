# 📋 完整命令参考手册

## 🎯 基础命令格式

```bash
python3 main.py [模块] [操作] [参数]
```

---

## 🔍 **选股筛选 (screen)**

### 基本用法
```bash
python3 main.py screen [市场] [数量]
```

### 支持的市场
```bash
python3 main.py screen sp500 10        # 筛选S&P500前10只
python3 main.py screen nasdaq100 5     # 筛选NASDAQ100前5只
python3 main.py screen chinese 3       # 筛选中概股前3只
python3 main.py screen popular_etfs 5  # 筛选热门ETF前5只
python3 main.py screen crypto_stocks 3 # 筛选加密货币相关股票前3只
```

---

## 📋 **自选股管理 (watchlist)**

### 查看和分析
```bash
python3 main.py watchlist show         # 显示自选股池
python3 main.py watchlist analyze      # 分析自选股池
```

### 添加和删除
```bash
python3 main.py watchlist add AAPL     # 添加苹果股票
python3 main.py watchlist add AAPL GOOGL MSFT  # 批量添加
python3 main.py watchlist remove AAPL  # 移除苹果股票
python3 main.py watchlist clear        # 清空股池
```

---

## 📈 **单股分析 (analyze)**

### 基本分析
```bash
python3 main.py analyze AAPL           # 分析苹果股票
python3 main.py analyze TSLA           # 分析特斯拉股票
python3 main.py analyze GOOGL          # 分析谷歌股票
```

---

## 💼 **投资组合管理 (portfolio)**

### 状态查看
```bash
python3 main.py portfolio status       # 查看投资组合状态
python3 main.py portfolio history      # 查看交易历史
```

### 交易操作
```bash
python3 main.py portfolio simulate     # 模拟自动交易(安全测试)
python3 main.py portfolio trade        # 执行实际交易(需API配置)
python3 main.py portfolio reset        # 重置投资组合(谨慎使用)
```

---

## ⚡ **日内交易系统 (intraday)**

### 系统监控
```bash
python3 main.py intraday status        # 查看系统状态
python3 main.py intraday monitor       # 启动实时监控(默认AAPL)
python3 main.py intraday monitor --symbol TSLA  # 监控指定股票
```

### 交易操作
```bash
python3 main.py intraday start         # 启动自动交易
python3 main.py intraday test          # 性能测试
python3 main.py intraday config        # 配置管理
```

### 策略管理
```bash
python3 main.py intraday strategy      # 策略引擎管理
python3 main.py intraday signals       # 信号监控模式
```

### 风险管理
```bash
python3 main.py intraday risk --risk-action status   # 风险管理状态
python3 main.py intraday risk --risk-action monitor  # 风险监控
python3 main.py intraday risk --risk-action test     # 风险压力测试
python3 main.py intraday risk --risk-action config   # 风险参数配置
python3 main.py intraday risk --risk-action report   # 风险管理报告
```

---

## 🎯 **常用命令组合**

### 🔰 **新手快速上手**
```bash
# 1. 选股
python3 main.py screen sp500 5

# 2. 分析
python3 main.py watchlist analyze

# 3. 模拟交易
python3 main.py portfolio simulate

# 4. 查看结果
python3 main.py portfolio history
```

### 🚀 **专业交易流程**
```bash
# 1. 选股
python3 main.py screen nasdaq100 10

# 2. 深度分析
python3 main.py analyze AAPL
python3 main.py analyze GOOGL

# 3. 监控准备
python3 main.py intraday status

# 4. 启动监控
python3 main.py intraday monitor --symbol AAPL

# 5. 风险检查
python3 main.py intraday risk --risk-action status

# 6. 实盘交易
python3 main.py portfolio trade
```

### ⚡ **日内交易流程**
```bash
# 1. 系统检查
python3 main.py intraday status

# 2. 启动监控
python3 main.py intraday monitor --symbol AAPL

# 3. 风险监控
python3 main.py intraday risk --risk-action monitor

# 4. 开始交易
python3 main.py intraday start

# 5. 查看状态
python3 main.py intraday status
```

---

## 📊 **高级功能**

### P1-2高级组件
```bash
# P1-2完整示例
python3 examples/p1_2_working_examples.py

# P1-2核心验证
python3 test_p1_2_core_validation.py

# P1-2集成测试
python3 test_p1_2_integration.py
```

### 系统测试
```bash
# 统一架构测试
python3 test_unified_architecture.py

# 风险集成测试
python3 test_risk_integration.py

# 回测框架测试
python3 test_backtest_framework.py
```

---

## ⚠️ **重要提示**

### 🛡️ **安全使用**
1. **模拟先行**: 实盘前务必先使用 `simulate` 模式测试
2. **小额开始**: 首次实盘从小资金开始
3. **监控为主**: 使用 `monitor` 模式观察市场

### 🔧 **参数说明**
- `--symbol`: 指定股票代码 (如 AAPL, TSLA, GOOGL)
- `--risk-action`: 风险管理操作类型
- `[数量]`: 筛选结果数量限制

### 💡 **使用技巧**
1. **组合使用**: 先选股，再分析，后交易
2. **持续监控**: 使用 `status` 命令定期检查系统状态
3. **风险优先**: 交易前务必检查风险管理状态

---

## 🆘 **故障排除**

### 常见错误
```bash
# 错误: argument action: invalid choice
# 原因: 缺少必需的action参数
# 解决: python3 main.py intraday [action]

# 错误: unrecognized arguments: --auto
# 原因: --auto参数不存在
# 解决: 使用 python3 main.py intraday start

# 错误: the following arguments are required: action
# 原因: intraday模块需要指定具体操作
# 解决: 添加action参数，如 monitor, status, start等
```

### 获取帮助
```bash
python3 main.py -h                     # 查看主帮助
python3 main.py intraday -h            # 查看intraday帮助
python3 main.py portfolio -h           # 查看portfolio帮助
```

---

## 📚 **相关文档**

- 📖 [完整使用指南](USER_GUIDE_COMPLETE.md)
- 🚀 [5分钟快速开始](QUICK_START.md)
- 📊 [P1-2用户手册](P1-2_USER_MANUAL.md)
- 🔧 [API参考文档](API_REFERENCE.md)

---

*最后更新: 2025年10月1日*