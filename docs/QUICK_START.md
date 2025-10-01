# 🚀 快速开始 - 5分钟上手量化交易

## 🎯 **第一次使用? 从这里开始!**

### ⚡ **1分钟选股**
```bash
# 筛选S&P500前5只优质股票
python3 main.py screen sp500 5

# 查看自动加入的自选股
python3 main.py watchlist show
```

**系统会自动**:
- ✅ 分析100+ 技术指标
- ✅ 计算综合评分(100分制)
- ✅ 生成买卖建议
- ✅ TOP5自动加入自选股池

### 📊 **2分钟深度分析**
```bash
# 深度分析推荐股票
python3 main.py analyze AAPL

# 批量分析所有自选股
python3 main.py watchlist analyze
```

**获得专业分析**:
- 📈 **技术指标**: RSI、MACD、布林带等
- 💰 **买卖点位**: 具体进出场价格
- ⚠️ **风险提示**: 专业风险评估

### 🤖 **3分钟模拟交易**
```bash
# 模拟自动交易(安全测试)
python3 main.py portfolio simulate

# 查看交易结果
python3 main.py portfolio history
```

**体验自动交易**:
- 🎯 **智能决策**: 基于四维分析的买卖信号
- 🛡️ **风险控制**: 自动止损、仓位管理
- 📊 **收益追踪**: 实时PnL和绩效指标

### 🚀 **高级功能体验**
```bash
# P1-2高级量化组件演示
python3 examples/p1_2_working_examples.py

# 核心功能验证
python3 test_p1_2_core_validation.py
```

**解锁企业级能力**:
- 🤖 **机器学习**: 价格预测、趋势分析
- 📊 **投资组合优化**: 现代投资组合理论
- 🔬 **专业风险管理**: VaR、压力测试

---

## 📋 **新手完整流程**

### **Step 1: 选股** 🔍
```bash
# 从不同市场选择优质股票
python3 main.py screen sp500 5      # 美股大盘
python3 main.py screen nasdaq100 3  # 科技股
python3 main.py screen chinese 2    # 中概股
```

### **Step 2: 分析** 📊
```bash
# 深度分析重点股票
python3 main.py analyze AAPL
python3 main.py analyze GOOGL
python3 main.py analyze TSLA
```

### **Step 3: 测试** 🧪
```bash
# 模拟交易验证策略
python3 main.py portfolio simulate
```

### **Step 4: 监控** 👀
```bash
# 查看投资组合状态
python3 main.py portfolio status

# 查看交易历史
python3 main.py portfolio history

# 启动日内交易监控
python3 main.py intraday monitor
```

---

## 🎯 **进阶使用**

准备好进入专业量化交易了吗?

📚 **[查看完整使用指南](docs/USER_GUIDE_COMPLETE.md)** - 从选股到自动交易的详细教程

### 🚀 **解锁更多功能**:
- ⚡ **日内交易**: 毫秒级高频交易
- 🤖 **机器学习**: 智能预测和决策
- 📊 **投资组合优化**: 科学资产配置
- 🛡️ **专业风险管理**: 企业级风控能力

---

## 💡 **小贴士**

### ⚠️ **安全第一**
- 始终先使用模拟交易测试
- 从小资金开始实盘交易
- 设置合理的止损和仓位限制

### 📈 **最佳实践**
- 分散投资，不要把鸡蛋放在一个篮子里
- 定期检查和调整策略
- 关注市场变化和风险变化

### 🔧 **遇到问题?**
- 查看 [P1-2用户手册](docs/P1-2_USER_MANUAL.md)
- 参考 [API文档](docs/API_REFERENCE.md)
- 运行工作示例获得帮助

---

🎉 **开始你的量化交易之旅**: `python3 main.py screen sp500 5`

*5分钟后，你就能看到系统为你筛选出的优质投资机会!* 🚀