# 自选股池功能使用指南

## 📝 功能概述

自选股池是智能股票筛选器的重要功能，可以：
- 🔄 **自动保存**：每次筛选后自动保存TOP5股票到自选股池
- 📊 **历史追踪**：记录股票得分变化历史，最多保留10次记录
- 🎯 **专项分析**：可以只对自选股池中的股票进行分析
- 📈 **去重管理**：避免重复添加，更新已存在股票的得分

## 🚀 快速开始

### 1. 基础筛选（自动保存TOP5）
```bash
# 分析标普500前10只股票，自动保存TOP5到自选股池
python3 examples/stock_screener.py sp500 10

# 分析纳斯达克100前5只股票
python3 examples/stock_screener.py nasdaq100 5
```

### 2. 查看自选股池
```bash
# 显示自选股池
python3 examples/stock_screener.py watchlist

# 或使用专用工具
python3 watchlist_tool.py show
```

### 3. 分析自选股池
```bash
# 只分析自选股池中的股票
python3 examples/stock_screener.py watchlist analyze
```

## 📋 完整命令列表

### 主筛选器命令
```bash
# 股票筛选（自动保存TOP5）
python3 examples/stock_screener.py sp500 [数量]     # 标普500
python3 examples/stock_screener.py nasdaq100 [数量] # 纳斯达克100
python3 examples/stock_screener.py chinese [数量]   # 中概股
python3 examples/stock_screener.py crypto [数量]    # 加密货币相关
python3 examples/stock_screener.py etfs [数量]      # 热门ETF

# 自选股池操作
python3 examples/stock_screener.py watchlist        # 显示自选股池
python3 examples/stock_screener.py watchlist analyze # 分析自选股池
python3 examples/stock_screener.py watchlist clear  # 清空自选股池
python3 examples/stock_screener.py watchlist remove AAPL # 移除指定股票
```

### 专用管理工具
```bash
# 查看操作
python3 watchlist_tool.py show        # 显示自选股池
python3 watchlist_tool.py stats       # 显示统计信息

# 管理操作
python3 watchlist_tool.py add AAPL    # 手动添加股票
python3 watchlist_tool.py remove AAPL # 移除股票
python3 watchlist_tool.py clear       # 清空股票池

# 分析操作
python3 watchlist_tool.py analyze     # 分析自选股池
```

## 📊 数据结构

自选股池数据保存在 `data/watchlist.json` 文件中：

```json
{
  "created_at": "2025-09-30T11:49:23.485858",
  "last_updated": "2025-09-30T11:50:45.123456",
  "stocks": {
    "AAPL": {
      "symbol": "AAPL",
      "added_at": "2025-09-30T11:49:23.485858",
      "last_score": 89.5,
      "last_price": 175.50,
      "score_history": [
        {
          "date": "2025-09-30T11:49:23.485876",
          "score": 89.5,
          "price": 175.50
        }
      ]
    }
  },
  "metadata": {
    "total_stocks": 1,
    "description": "智能股票筛选器自选股池"
  }
}
```

## 🎯 使用场景

### 场景1：构建个人投资组合
```bash
# 步骤1：从不同板块筛选
python3 examples/stock_screener.py sp500 20      # 大盘蓝筹
python3 examples/stock_screener.py nasdaq100 10  # 科技成长
python3 examples/stock_screener.py etfs 5        # ETF基金

# 步骤2：查看汇总结果
python3 watchlist_tool.py show

# 步骤3：定期重新评估
python3 examples/stock_screener.py watchlist analyze
```

### 场景2：跟踪特定股票
```bash
# 手动添加关注的股票
python3 watchlist_tool.py add NVDA
python3 watchlist_tool.py add TSLA
python3 watchlist_tool.py add AMZN

# 定期分析
python3 watchlist_tool.py analyze
```

### 场景3：清理和维护
```bash
# 查看统计信息
python3 watchlist_tool.py stats

# 移除低分股票
python3 watchlist_tool.py remove LOW_SCORE_STOCK

# 重新开始
python3 watchlist_tool.py clear
```

## 📈 评分系统

自选股池记录的得分基于三维度分析：
- 🔧 **技术分析** (50%): RSI、MACD、布林带等技术指标
- 📊 **基本面分析** (30%): 估值、财务健康、盈利能力、成长性
- 🌍 **市场环境匹配** (20%): Beta系数与当前市场环境的匹配度

总分范围：0-100分，分数越高投资价值越大。

## 🔧 高级功能

### 历史得分追踪
每次重新分析时会记录新的得分，可以观察股票表现趋势：
```bash
# 今天分析
python3 examples/stock_screener.py sp500 10

# 明天再次分析，会更新得分历史
python3 examples/stock_screener.py watchlist analyze
```

### 智能去重
相同股票不会重复添加，而是更新得分和价格信息。

### 数据持久化
所有数据自动保存到JSON文件，程序重启后数据依然存在。

## 🚨 注意事项

1. **API限制**：系统已优化API调用频率，避免触发限制
2. **数据时效**：股票数据具有时效性，建议定期重新分析
3. **风险提示**：投资有风险，分析结果仅供参考，请结合实际情况决策
4. **文件备份**：建议定期备份 `data/watchlist.json` 文件

## 📞 技术支持

如果遇到问题：
1. 检查网络连接
2. 确认股票代码正确
3. 查看错误信息
4. 重试操作

祝您投资顺利！ 🎉