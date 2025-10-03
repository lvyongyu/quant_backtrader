/**
 * 监控报告页面JavaScript
 * 处理系统状态监控、日志管理、交易历史等功能
 */

class MonitoringManager {
    constructor() {
        this.api = new TradingAPI();
        this.startTime = new Date();
        this.autoUpdate = true;
        this.updateInterval = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.startAutoUpdate();
        this.loadSystemData();
    }
    
    bindEvents() {
        // 日志控制
        document.getElementById('log-level').addEventListener('change', (e) => {
            this.filterLogs(e.target.value);
        });
        
        document.getElementById('clear-log-btn').addEventListener('click', () => {
            this.clearLogs();
        });
        
        document.getElementById('export-log-btn').addEventListener('click', () => {
            this.exportLogs();
        });
    }
    
    startAutoUpdate() {
        this.updateInterval = setInterval(() => {
            this.updateSystemStatus();
            this.updateUptime();
        }, 60000); // 每分钟更新
        
        // 立即更新一次
        this.updateSystemStatus();
        this.updateUptime();
    }
    
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    async loadSystemData() {
        try {
            await Promise.all([
                this.loadTradingData(),
                this.loadLogData(),
                this.updateRiskMetrics()
            ]);
        } catch (error) {
            console.error('加载系统数据失败:', error);
        }
    }
    
    async loadTradingData() {
        try {
            // 模拟加载交易数据
            const trades = await this.generateMockTrades();
            this.updateTradesTable(trades);
            this.updateMetrics(trades);
        } catch (error) {
            console.error('加载交易数据失败:', error);
        }
    }
    
    async loadLogData() {
        try {
            // 模拟系统日志
            this.simulateSystemLogs();
        } catch (error) {
            console.error('加载日志数据失败:', error);
        }
    }
    
    updateSystemStatus() {
        // 更新系统状态
        const metrics = this.calculateSystemMetrics();
        
        document.getElementById('monitored-stocks').textContent = `${metrics.stocks}只`;
        document.getElementById('active-strategies').textContent = `${metrics.strategies}个`;
        document.getElementById('today-trades').textContent = `${metrics.trades}笔`;
        
        const pnlElement = document.getElementById('total-pnl');
        const pnl = metrics.totalPnL;
        pnlElement.textContent = pnl >= 0 ? `+$${pnl.toFixed(2)}` : `-$${Math.abs(pnl).toFixed(2)}`;
        pnlElement.className = `status-value ${pnl >= 0 ? 'positive' : 'negative'}`;
    }
    
    updateUptime() {
        const now = new Date();
        const diff = now - this.startTime;
        const hours = Math.floor(diff / 3600000);
        const minutes = Math.floor((diff % 3600000) / 60000);
        
        document.getElementById('uptime').textContent = `${hours}小时${minutes}分钟`;
    }
    
    calculateSystemMetrics() {
        return {
            stocks: 5 + Math.floor(Math.random() * 3),
            strategies: 3 + Math.floor(Math.random() * 2),
            trades: 10 + Math.floor(Math.random() * 15),
            totalPnL: (Math.random() - 0.3) * 2000 + 1000
        };
    }
    
    updateMetrics(trades) {
        // 计算交易指标
        const totalTrades = trades.length;
        const profitableTrades = trades.filter(t => t.pnl > 0).length;
        const winRate = totalTrades > 0 ? (profitableTrades / totalTrades * 100).toFixed(1) : '0.0';
        
        // 更新胜率显示
        const winRateElements = document.querySelectorAll('.metric-value');
        if (winRateElements[1]) {
            winRateElements[1].textContent = `${winRate}%`;
        }
    }
    
    async generateMockTrades() {
        const symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'];
        const actions = ['买入', '卖出'];
        const trades = [];
        
        for (let i = 0; i < 8; i++) {
            const time = new Date();
            time.setMinutes(time.getMinutes() - i * 15);
            
            trades.push({
                time: time.toTimeString().slice(0, 8),
                symbol: symbols[Math.floor(Math.random() * symbols.length)],
                action: actions[Math.floor(Math.random() * actions.length)],
                quantity: Math.floor(Math.random() * 100 + 10),
                price: (Math.random() * 300 + 50).toFixed(2),
                pnl: (Math.random() - 0.4) * 500
            });
        }
        
        return trades;
    }
    
    updateTradesTable(trades) {
        const tbody = document.getElementById('trades-tbody');
        tbody.innerHTML = trades.map(trade => {
            const pnlClass = trade.pnl >= 0 ? 'positive' : 'negative';
            const pnlText = trade.pnl >= 0 ? `+$${trade.pnl.toFixed(2)}` : `-$${Math.abs(trade.pnl).toFixed(2)}`;
            const actionClass = trade.action === '买入' ? 'buy' : 'sell';
            
            return `
                <tr>
                    <td>${trade.time}</td>
                    <td>${trade.symbol}</td>
                    <td class="${actionClass}">${trade.action}</td>
                    <td>${trade.quantity}</td>
                    <td>$${trade.price}</td>
                    <td class="${pnlClass}">${pnlText}</td>
                </tr>
            `;
        }).join('');
    }
    
    simulateSystemLogs() {
        const logContainer = document.getElementById('system-log');
        
        // 定期添加新日志
        setInterval(() => {
            const newLog = this.generateRandomLog();
            const logElement = this.createLogElement(newLog);
            logContainer.insertBefore(logElement, logContainer.firstChild);
            
            // 限制日志数量
            const logs = logContainer.children;
            if (logs.length > 20) {
                logContainer.removeChild(logs[logs.length - 1]);
            }
        }, 30000); // 每30秒添加一条日志
    }
    
    generateRandomLog() {
        const levels = ['INFO', 'SUCCESS', 'WARNING', 'ERROR'];
        const messages = [
            '数据更新完成，获取到最新股价信息',
            '策略信号生成：MA交叉买入信号',
            '风险检查通过，执行交易操作',
            '连接数据源成功',
            '股价异常波动检测',
            '止损订单执行完成',
            '系统内存使用率正常',
            '网络延迟检测: 45ms'
        ];
        
        const level = levels[Math.floor(Math.random() * levels.length)];
        const message = messages[Math.floor(Math.random() * messages.length)];
        const time = new Date().toTimeString().slice(0, 8);
        
        return { time, level, message };
    }
    
    createLogElement(log) {
        const div = document.createElement('div');
        div.className = `log-entry ${log.level.toLowerCase()}`;
        div.innerHTML = `
            <span class="log-time">[${log.time}]</span>
            <span class="log-level">${log.level}</span>
            <span class="log-message">${log.message}</span>
        `;
        return div;
    }
    
    filterLogs(level) {
        const logs = document.querySelectorAll('.log-entry');
        
        logs.forEach(log => {
            if (level === 'all') {
                log.style.display = 'block';
            } else {
                const logLevel = log.classList[1];
                log.style.display = logLevel === level ? 'block' : 'none';
            }
        });
    }
    
    clearLogs() {
        const logContainer = document.getElementById('system-log');
        logContainer.innerHTML = `
            <div class="log-entry info">
                <span class="log-time">[${new Date().toTimeString().slice(0, 8)}]</span>
                <span class="log-level">INFO</span>
                <span class="log-message">日志已清空</span>
            </div>
        `;
        UIUtils.showAlert('日志已清空', 'success');
    }
    
    exportLogs() {
        const logs = document.querySelectorAll('.log-entry');
        let logText = '系统日志导出\n';
        logText += '='.repeat(50) + '\n';
        logText += `导出时间: ${new Date().toLocaleString()}\n\n`;
        
        logs.forEach(log => {
            const time = log.querySelector('.log-time').textContent;
            const level = log.querySelector('.log-level').textContent;
            const message = log.querySelector('.log-message').textContent;
            logText += `${time} [${level}] ${message}\n`;
        });
        
        // 创建下载链接
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `system_log_${new Date().toISOString().slice(0, 10)}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        
        UIUtils.showAlert('日志导出成功', 'success');
    }
    
    updateRiskMetrics() {
        // 模拟风险指标更新
        const riskBars = document.querySelectorAll('.risk-bar');
        
        riskBars.forEach(bar => {
            const currentWidth = parseInt(bar.style.width);
            const change = (Math.random() - 0.5) * 10;
            let newWidth = Math.max(0, Math.min(100, currentWidth + change));
            
            bar.style.width = `${newWidth}%`;
            
            // 更新颜色
            if (newWidth < 30) {
                bar.style.background = '#4caf50';
            } else if (newWidth < 70) {
                bar.style.background = '#ff9800';
            } else {
                bar.style.background = '#f44336';
            }
            
            // 更新文本
            const riskItem = bar.closest('.risk-item');
            const valueElement = riskItem.querySelector('.risk-value');
            let riskLevel = '';
            
            if (newWidth < 30) riskLevel = '低';
            else if (newWidth < 70) riskLevel = '中等';
            else riskLevel = '高';
            
            valueElement.textContent = `${riskLevel} (${newWidth.toFixed(0)}%)`;
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new MonitoringManager();
});