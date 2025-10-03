/**
 * 自动交易页面JavaScript
 * 处理自动交易配置、启动/停止、实时状态更新等功能
 */

class AutoTradeManager {
    constructor() {
        this.api = new TradingAPI();
        this.isRunning = false;
        this.intervalId = null;
        this.tradeCount = 0;
        this.startTime = null;
        this.totalProfit = 0;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateUI();
    }
    
    bindEvents() {
        document.getElementById('start-btn').addEventListener('click', () => this.startTrading());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopTrading());
        
        // 配置变化时更新状态显示
        const form = document.getElementById('auto-trade-config');
        form.addEventListener('change', () => this.updateStatusDisplay());
    }
    
    async startTrading() {
        const config = this.getConfig();
        
        if (!this.validateConfig(config)) {
            return;
        }
        
        try {
            // 启动自动交易
            const response = await this.api.post('/api/auto_trade/start', config);
            
            if (response.success) {
                this.isRunning = true;
                this.startTime = new Date();
                this.tradeCount = 0;
                this.totalProfit = 0;
                
                // 更新UI状态
                this.updateUI();
                this.startStatusUpdates();
                
                UIUtils.showAlert('✅ 自动交易已启动！', 'success');
                this.logTrade('🚀 自动交易系统启动', '开始监控市场并执行交易策略...');
            } else {
                UIUtils.showAlert('❌ 启动失败: ' + (response.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('启动自动交易失败:', error);
            UIUtils.showAlert('❌ 启动失败: 网络错误', 'error');
        }
    }
    
    async stopTrading() {
        try {
            const response = await this.api.post('/api/auto_trade/stop');
            
            if (response.success) {
                this.isRunning = false;
                this.stopStatusUpdates();
                this.updateUI();
                
                UIUtils.showAlert('🛑 自动交易已停止', 'info');
                this.logTrade('🛑 自动交易系统停止', this.generateSummary());
            } else {
                UIUtils.showAlert('❌ 停止失败: ' + (response.error || '未知错误'), 'error');
            }
        } catch (error) {
            console.error('停止自动交易失败:', error);
            UIUtils.showAlert('❌ 停止失败: 网络错误', 'error');
        }
    }
    
    getConfig() {
        const form = document.getElementById('auto-trade-config');
        const formData = new FormData(form);
        
        return {
            mode: formData.get('mode'),
            stocks: formData.get('stocks'),
            strategy: formData.get('strategy'),
            capital: parseFloat(formData.get('capital')),
            stopLoss: parseFloat(formData.get('stopLoss')),
            takeProfit: parseFloat(formData.get('takeProfit'))
        };
    }
    
    validateConfig(config) {
        if (config.capital < 10000) {
            UIUtils.showAlert('❌ 初始资金不能少于 $10,000', 'error');
            return false;
        }
        
        if (config.stopLoss >= config.takeProfit) {
            UIUtils.showAlert('❌ 止盈比例必须大于止损比例', 'error');
            return false;
        }
        
        return true;
    }
    
    updateUI() {
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const form = document.getElementById('auto-trade-config');
        
        if (this.isRunning) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // 禁用配置表单
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => input.disabled = true);
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            // 启用配置表单
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => input.disabled = false);
        }
        
        this.updateStatusDisplay();
    }
    
    updateStatusDisplay() {
        const config = this.getConfig();
        const statusDiv = document.getElementById('trading-status');
        
        if (this.isRunning) {
            const runtime = this.getRuntime();
            const profitStr = this.totalProfit >= 0 ? `+$${this.totalProfit.toFixed(2)}` : `-$${Math.abs(this.totalProfit).toFixed(2)}`;
            
            statusDiv.innerHTML = `
🟢 自动交易运行中...
⏱️ 运行时间: ${runtime}
💼 交易次数: ${this.tradeCount}
💰 当前盈亏: ${profitStr}
📊 策略: ${this.getStrategyName(config.strategy)}
🎯 股票池: ${this.getStockPoolName(config.stocks)}
🛡️ 风险控制: 止损${config.stopLoss}%, 止盈${config.takeProfit}%`;
        } else {
            statusDiv.innerHTML = `
🎯 自动交易系统待命中...
📋 配置: ${this.getModeLabel(config.mode)}，${this.getStockPoolName(config.stocks)}
💰 初始资金: $${config.capital.toLocaleString()}
🛡️ 风险控制: 止损${config.stopLoss}%, 止盈${config.takeProfit}%
⚡ 点击"启动自动交易"开始监控...`;
        }
    }
    
    startStatusUpdates() {
        // 每5秒更新一次状态
        this.intervalId = setInterval(() => {
            this.updateStatusDisplay();
            this.simulateTrading();
        }, 5000);
    }
    
    stopStatusUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    // 模拟交易活动
    simulateTrading() {
        // 模拟随机交易
        if (Math.random() < 0.3) { // 30%概率产生交易
            const actions = ['买入', '卖出'];
            const stocks = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'];
            const action = actions[Math.floor(Math.random() * actions.length)];
            const stock = stocks[Math.floor(Math.random() * stocks.length)];
            const price = (Math.random() * 200 + 50).toFixed(2);
            const shares = Math.floor(Math.random() * 100 + 10);
            const profit = (Math.random() - 0.5) * 1000;
            
            this.tradeCount++;
            this.totalProfit += profit;
            
            const profitStr = profit >= 0 ? `+$${profit.toFixed(2)}` : `-$${Math.abs(profit).toFixed(2)}`;
            this.logTrade(
                `📈 ${action} ${stock}`,
                `价格: $${price}, 数量: ${shares}股, 盈亏: ${profitStr}`
            );
        }
    }
    
    logTrade(title, details) {
        const logDiv = document.getElementById('trade-log');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = `
[${timestamp}] ${title}
${details}
`;
        
        if (logDiv.textContent.includes('暂无交易记录')) {
            logDiv.textContent = logEntry;
        } else {
            logDiv.textContent = logEntry + '\n' + logDiv.textContent;
        }
        
        // 限制日志长度
        const lines = logDiv.textContent.split('\n');
        if (lines.length > 50) {
            logDiv.textContent = lines.slice(0, 50).join('\n');
        }
    }
    
    getRuntime() {
        if (!this.startTime) return '0分钟';
        
        const now = new Date();
        const diff = now - this.startTime;
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        
        if (minutes > 0) {
            return `${minutes}分${seconds}秒`;
        } else {
            return `${seconds}秒`;
        }
    }
    
    generateSummary() {
        const runtime = this.getRuntime();
        const profitStr = this.totalProfit >= 0 ? `盈利$${this.totalProfit.toFixed(2)}` : `亏损$${Math.abs(this.totalProfit).toFixed(2)}`;
        
        return `运行时间: ${runtime}, 总交易: ${this.tradeCount}次, 总${profitStr}`;
    }
    
    getModeLabel(mode) {
        const modes = {
            'paper': '纸面交易模式',
            'simulate': '模拟交易模式',
            'live': '实盘交易模式'
        };
        return modes[mode] || mode;
    }
    
    getStrategyName(strategy) {
        const strategies = {
            'conservative': '保守型策略',
            'balanced': '均衡型策略',
            'aggressive': '积极型策略'
        };
        return strategies[strategy] || strategy;
    }
    
    getStockPoolName(stocks) {
        const pools = {
            'tech5': '科技五强',
            'sp500': '标普500前10',
            'custom': '自定义股票池'
        };
        return pools[stocks] || stocks;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new AutoTradeManager();
});