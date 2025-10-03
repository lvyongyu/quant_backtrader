/**
 * 📈 回测页面专用JavaScript
 */

// 策略名称映射
const STRATEGY_NAMES = {
    'buy_hold': '买入持有策略',
    'ma_cross': '移动平均交叉策略',
    'rsi_strategy': 'RSI相对强弱指标策略',
    'bollinger': '布林带策略',
    'macd_strategy': 'MACD策略',
    'dual_ma': '双移动平均线策略',
    'rsi_macd': 'RSI+MACD组合策略',
    'momentum': '动量策略',
    'mean_reversion': '均值回归策略'
};

// 周期名称映射
const PERIOD_NAMES = {
    '6m': '近6个月',
    '1y': '近1年',
    '2y': '近2年',
    '3y': '近3年',
    '5y': '近5年'
};

// 股票名称映射
const STOCK_NAMES = {
    'AAPL': '苹果公司',
    'TSLA': '特斯拉',
    'NVDA': '英伟达',
    'MSFT': '微软',
    'GOOGL': '谷歌',
    'AMZN': '亚马逊',
    'META': 'Meta',
    'NFLX': '奈飞'
};

/**
 * 回测管理类
 */
class BacktestManager {
    constructor() {
        this.initializeEventListeners();
    }

    /**
     * 初始化事件监听器
     */
    initializeEventListeners() {
        // 单股回测表单提交
        const singleForm = document.getElementById('single-backtest-form');
        if (singleForm) {
            singleForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.runSingleBacktest(new FormData(singleForm));
            });
        }

        // 组合回测表单提交
        const portfolioForm = document.getElementById('portfolio-backtest-form');
        if (portfolioForm) {
            portfolioForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.runPortfolioBacktest(new FormData(portfolioForm));
            });
        }
    }

    /**
     * 运行单股回测
     */
    async runSingleBacktest(formData) {
        const resultsElement = document.getElementById('single-results');
        const params = {
            type: 'single',
            symbol: formData.get('symbol'),
            strategy: formData.get('strategy'),
            period: formData.get('period'),
            capital: parseInt(formData.get('capital'))
        };

        try {
            UIUtils.showLoading(resultsElement, '🔄 正在运行单股回测...');

            // 验证参数
            const errors = DataUtils.validateForm(params, {
                symbol: { required: true, label: '股票代码' },
                strategy: { required: true, label: '策略类型' },
                period: { required: true, label: '回测周期' },
                capital: { required: true, type: 'number', min: 1000, label: '投资金额' }
            });

            if (errors.length > 0) {
                throw new Error(errors.join(', '));
            }

            // 模拟API调用延迟
            await new Promise(resolve => setTimeout(resolve, 2000));

            // 生成模拟结果
            const result = DataUtils.generateMockBacktestResult(params);
            
            // 显示结果
            this.displaySingleBacktestResult(result, resultsElement);

            UIUtils.showNotification('单股回测完成！', 'success');

        } catch (error) {
            console.error('单股回测失败:', error);
            UIUtils.showError(resultsElement, error.message);
            UIUtils.showNotification('回测失败: ' + error.message, 'error');
        }
    }

    /**
     * 运行组合回测
     */
    async runPortfolioBacktest(formData) {
        const resultsElement = document.getElementById('portfolio-results');
        const params = {
            type: 'portfolio',
            strategy: formData.get('strategy'),
            period: formData.get('period'),
            capital: parseInt(formData.get('capital')),
            stocks: formData.get('stocks')
        };

        try {
            UIUtils.showLoading(resultsElement, '🔄 正在运行组合回测...');

            // 验证参数
            const errors = DataUtils.validateForm(params, {
                strategy: { required: true, label: '策略类型' },
                period: { required: true, label: '时间范围' },
                capital: { required: true, type: 'number', min: 10000, label: '初始资金' },
                stocks: { required: true, label: '股票池' }
            });

            if (errors.length > 0) {
                throw new Error(errors.join(', '));
            }

            // 模拟API调用延迟
            await new Promise(resolve => setTimeout(resolve, 2500));

            // 生成模拟结果
            const result = this.generatePortfolioBacktestResult(params);
            
            // 显示结果
            this.displayPortfolioBacktestResult(result, resultsElement);

            UIUtils.showNotification('组合回测完成！', 'success');

        } catch (error) {
            console.error('组合回测失败:', error);
            UIUtils.showError(resultsElement, error.message);
            UIUtils.showNotification('回测失败: ' + error.message, 'error');
        }
    }

    /**
     * 显示单股回测结果
     */
    displaySingleBacktestResult(result, element) {
        const strategyAnalysis = this.getStrategyAnalysis(result.strategy);
        const performance = this.getPerformanceLevel(result.totalReturn);

        element.innerHTML = `🎯 ${result.symbol} 单股回测完成 - ${result.timestamp}
==================================================
📈 股票: ${result.symbol} - ${STOCK_NAMES[result.symbol] || result.symbol}
📊 策略: ${STRATEGY_NAMES[result.strategy] || result.strategy}
⏱️  回测周期: ${PERIOD_NAMES[result.period] || result.period}
💰 投资金额: ${UIUtils.formatCurrency(result.initialCapital)}

💵 最终价值: ${UIUtils.formatCurrency(result.finalValue)}
📊 总收益率: ${UIUtils.formatPercentage(result.totalReturn)}
📈 年化收益率: ${UIUtils.formatPercentage(result.annualizedReturn)}
📉 最大回撤: ${UIUtils.formatPercentage(result.maxDrawdown)}
🎯 胜率: ${result.winRate.toFixed(1)}%
📊 夏普比率: ${result.sharpeRatio.toFixed(2)}
💼 总交易次数: ${result.totalTrades} 次

📈 价格走势:
  • 起始价格: $150.25
  • 最高价格: $185.20
  • 最低价格: $142.10
  • 结束价格: $${(150.25 * (1 + result.totalReturn)).toFixed(2)}

🔍 策略分析:
${strategyAnalysis}

${performance}`;
    }

    /**
     * 显示组合回测结果
     */
    displayPortfolioBacktestResult(result, element) {
        const performance = this.getPerformanceLevel(result.totalReturn);

        element.innerHTML = `📈 组合回测完成 - ${result.timestamp}
==================================================
📊 策略: ${STRATEGY_NAMES[result.strategy] || result.strategy}
⏱️  回测周期: ${PERIOD_NAMES[result.period] || result.period}
💰 初始资金: ${UIUtils.formatCurrency(result.initialCapital)}
📦 股票池: ${this.getStockPoolName(result.stocks)}

💵 最终资金: ${UIUtils.formatCurrency(result.finalValue)}
📊 总收益率: ${UIUtils.formatPercentage(result.totalReturn)}
📈 年化收益率: ${UIUtils.formatPercentage(result.annualizedReturn)}
📉 最大回撤: ${UIUtils.formatPercentage(result.maxDrawdown)}
🎯 胜率: ${result.winRate.toFixed(1)}%
📊 夏普比率: ${result.sharpeRatio.toFixed(2)}
💼 总交易次数: ${result.totalTrades} 次

🏆 最佳股票: NVDA (+85.2%)
⚠️  最差股票: TSLA (-12.3%)
📊 资产分配:
  • AAPL: 25% (+35.2%)
  • NVDA: 25% (+85.2%)  
  • MSFT: 20% (+28.4%)
  • GOOGL: 20% (+15.8%)
  • TSLA: 10% (-12.3%)

${performance}`;
    }

    /**
     * 生成组合回测结果
     */
    generatePortfolioBacktestResult(params) {
        const returnRate = Math.random() * 0.5 + 0.2; // 20% - 70% 收益
        const finalValue = Math.floor(params.capital * (1 + returnRate));
        const annualizedReturn = returnRate / (params.period === '1y' ? 1 : 
                                             params.period === '2y' ? 2 : 
                                             params.period === '3y' ? 3 : 5);

        return {
            strategy: params.strategy,
            period: params.period,
            stocks: params.stocks,
            initialCapital: params.capital,
            finalValue,
            totalReturn: returnRate,
            annualizedReturn,
            maxDrawdown: -(Math.random() * 10 + 5) / 100,
            sharpeRatio: Math.random() * 1.5 + 1,
            winRate: Math.random() * 20 + 60,
            totalTrades: Math.floor(Math.random() * 50) + 100,
            timestamp: new Date().toLocaleString()
        };
    }

    /**
     * 获取策略分析
     */
    getStrategyAnalysis(strategy) {
        const analysis = {
            'buy_hold': '• 简单有效的长期投资策略\n• 适合优质成长股\n• 减少交易成本和税务负担\n• 依赖股票长期上涨趋势',
            'ma_cross': '• 使用5日和20日移动平均线\n• 金叉买入，死叉卖出\n• 适合趋势明显的市场\n• 可能产生假信号',
            'rsi_strategy': '• RSI < 30 超卖买入\n• RSI > 70 超买卖出\n• 适合震荡市场\n• 需要结合其他指标',
            'bollinger': '• 价格触及下轨买入\n• 价格触及上轨卖出\n• 基于价格回归特性\n• 适合波动性较大的股票',
            'macd_strategy': '• MACD金叉买入信号\n• MACD死叉卖出信号\n• 结合MACD柱状图\n• 适合中期趋势判断'
        };
        return analysis[strategy] || '• 策略分析不可用';
    }

    /**
     * 获取股票池名称
     */
    getStockPoolName(stocks) {
        const names = {
            'tech5': '科技五强 (AAPL, TSLA, NVDA, MSFT, GOOGL)',
            'sp500': '标普500前10',
            'custom': '自定义股票池'
        };
        return names[stocks] || stocks;
    }

    /**
     * 获取表现评级
     */
    getPerformanceLevel(returnRate) {
        if (returnRate > 0.3) {
            return '🏆 策略表现优秀！';
        } else if (returnRate > 0.1) {
            return '✅ 策略表现良好';
        } else if (returnRate > 0) {
            return '📊 策略表现一般';
        } else {
            return '⚠️  策略需要优化';
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    new BacktestManager();
    console.log('📈 回测页面已初始化');
});