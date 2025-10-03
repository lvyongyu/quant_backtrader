/**
 * 股票监控页面JavaScript
 * 处理股票实时数据获取、显示和自动刷新功能
 */

class StockMonitor {
    constructor() {
        this.api = new TradingAPI();
        this.watchlist = [];
        this.autoRefresh = false;
        this.refreshInterval = null;
        this.refreshIntervalSeconds = 10;
        
        this.init();
    }
    
    init() {
        this.loadWatchlist();
        this.bindEvents();
        this.updateUI();
    }
    
    bindEvents() {
        // 添加股票
        document.getElementById('add-stock-btn').addEventListener('click', () => this.addStock());
        document.getElementById('stock-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addStock();
        });
        
        // 快速添加按钮
        document.querySelectorAll('.quick-add button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const symbol = e.target.dataset.symbol;
                if (symbol) this.addStockBySymbol(symbol);
            });
        });
        
        // 刷新控制
        document.getElementById('refresh-btn').addEventListener('click', () => this.refreshData());
        document.getElementById('auto-refresh-btn').addEventListener('click', () => this.toggleAutoRefresh());
        document.getElementById('refresh-interval').addEventListener('change', (e) => {
            this.refreshIntervalSeconds = parseInt(e.target.value);
            if (this.autoRefresh) {
                this.stopAutoRefresh();
                this.startAutoRefresh();
            }
        });
    }
    
    async loadWatchlist() {
        try {
            const response = await this.api.get('/api/watchlist');
            if (response.success && response.data) {
                this.watchlist = response.data;
                console.log('✅ 自选股列表加载成功:', this.watchlist);
            } else {
                console.log('ℹ️ 使用默认自选股列表');
                // 使用默认监控列表
                this.watchlist = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'];
            }
            this.updateStocksDisplay();
        } catch (error) {
            console.error('❌ 加载自选股列表失败:', error);
            // 使用默认列表
            this.watchlist = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL'];
            this.updateStocksDisplay();
        }
    }
    
    async addStock() {
        const input = document.getElementById('stock-search');
        const symbol = input.value.trim().toUpperCase();
        
        if (!symbol) {
            UIUtils.showAlert('请输入股票代码', 'warning');
            return;
        }
        
        if (this.watchlist.includes(symbol)) {
            UIUtils.showAlert('该股票已在自选股列表中', 'info');
            return;
        }
        
        await this.addStockBySymbol(symbol);
        input.value = '';
    }
    
    async addStockBySymbol(symbol) {
        try {
            const response = await this.api.post('/api/watchlist/add', { symbol: symbol });
            if (response.success) {
                this.watchlist = response.data; // 更新本地列表
                this.updateStocksDisplay();
                UIUtils.showAlert(`✅ 已添加 ${symbol} 到自选股`, 'success');
            } else {
                UIUtils.showAlert(`❌ 添加失败: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('添加股票失败:', error);
            UIUtils.showAlert(`❌ 添加 ${symbol} 失败: 网络错误`, 'error');
        }
    }
    
    async removeStock(symbol) {
        try {
            const response = await this.api.post('/api/watchlist/remove', { symbol: symbol });
            if (response.success) {
                this.watchlist = response.data; // 更新本地列表
                this.updateStocksDisplay();
                UIUtils.showAlert(`✅ 已从自选股移除 ${symbol}`, 'info');
            } else {
                UIUtils.showAlert(`❌ 移除失败: ${response.error}`, 'error');
            }
        } catch (error) {
            console.error('移除股票失败:', error);
            UIUtils.showAlert(`❌ 移除 ${symbol} 失败: 网络错误`, 'error');
        }
    }
    
    async refreshData() {
        this.updateStocksDisplay();
        this.updateTime();
    }
    
    toggleAutoRefresh() {
        const btn = document.getElementById('auto-refresh-btn');
        
        if (this.autoRefresh) {
            this.stopAutoRefresh();
            btn.textContent = '⏰ 自动刷新';
            btn.classList.remove('active');
        } else {
            this.startAutoRefresh();
            btn.textContent = '⏸️ 停止刷新';
            btn.classList.add('active');
        }
    }
    
    startAutoRefresh() {
        this.autoRefresh = true;
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, this.refreshIntervalSeconds * 1000);
    }
    
    stopAutoRefresh() {
        this.autoRefresh = false;
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    async updateStocksDisplay() {
        const grid = document.getElementById('stocks-grid');
        
        if (this.watchlist.length === 0) {
            grid.innerHTML = `
                <div class="stock-placeholder">
                    🎯 自选股列表为空
                    <br>请使用上方搜索框添加股票到自选股
                </div>
            `;
            return;
        }
        
        // 显示加载状态
        grid.innerHTML = this.watchlist.map(symbol => this.createStockCardLoading(symbol)).join('');
        
        // 获取股票数据
        try {
            const promises = this.watchlist.map(symbol => this.getStockData(symbol));
            const results = await Promise.all(promises);
            
            grid.innerHTML = results.map(data => this.createStockCard(data)).join('');
        } catch (error) {
            console.error('获取股票数据失败:', error);
            UIUtils.showAlert('获取股票数据失败', 'error');
        }
    }
    
    async getStockData(symbol) {
        try {
            const response = await this.api.get(`/api/stock/${symbol}`);
            if (response.success) {
                return response.data;
            } else {
                return this.createMockStockData(symbol);
            }
        } catch (error) {
            console.error(`获取 ${symbol} 数据失败:`, error);
            return this.createMockStockData(symbol);
        }
    }
    
    createMockStockData(symbol) {
        const basePrice = Math.random() * 300 + 50;
        const change = (Math.random() - 0.5) * 10;
        const changePercent = (change / basePrice) * 100;
        
        return {
            symbol: symbol,
            name: this.getStockName(symbol),
            price: basePrice.toFixed(2),
            change: change.toFixed(2),
            changePercent: changePercent.toFixed(2),
            volume: Math.floor(Math.random() * 10000000),
            marketCap: (basePrice * Math.random() * 1000000000).toFixed(0)
        };
    }
    
    createStockCardLoading(symbol) {
        return `
            <div class="stock-card loading">
                <div class="stock-header">
                    <div class="stock-symbol">${symbol}</div>
                    <button class="remove-btn" onclick="stockMonitor.removeStock('${symbol}')">×</button>
                </div>
                <div class="stock-name">加载中...</div>
                <div class="stock-price">--</div>
                <div class="stock-change">--</div>
            </div>
        `;
    }
    
    createStockCard(data) {
        const isPositive = parseFloat(data.change) >= 0;
        const changeClass = isPositive ? 'positive' : 'negative';
        const changeSign = isPositive ? '+' : '';
        
        return `
            <div class="stock-card ${changeClass}" onclick="stockMonitor.showStockDetail('${data.symbol}')">
                <div class="stock-header">
                    <div class="stock-symbol">${data.symbol}</div>
                    <button class="remove-btn" onclick="event.stopPropagation(); stockMonitor.removeStock('${data.symbol}')">×</button>
                </div>
                <div class="stock-name">${data.name}</div>
                <div class="stock-price">$${data.price}</div>
                <div class="stock-change ${changeClass}">
                    ${changeSign}$${data.change} (${changeSign}${data.changePercent}%)
                </div>
                <div class="stock-details">
                    <div>成交量: ${this.formatVolume(data.volume)}</div>
                    <div>市值: ${this.formatMarketCap(data.marketCap)}</div>
                </div>
            </div>
        `;
    }
    
    showStockDetail(symbol) {
        UIUtils.showAlert(`点击查看 ${symbol} 详细信息\n(功能开发中...)`, 'info');
    }
    
    updateTime() {
        const timeElement = document.getElementById('update-time');
        const now = new Date();
        timeElement.textContent = `(更新时间: ${now.toLocaleTimeString()})`;
    }
    
    updateUI() {
        this.updateTime();
    }
    
    getStockName(symbol) {
        const names = {
            'AAPL': '苹果公司',
            'TSLA': '特斯拉',
            'NVDA': '英伟达',
            'MSFT': '微软',
            'GOOGL': '谷歌',
            'AMZN': '亚马逊',
            'META': 'Meta',
            'NFLX': '奈飞',
            'AMD': '超微半导体',
            'INTC': '英特尔'
        };
        return names[symbol] || symbol + ' Inc.';
    }
    
    formatVolume(volume) {
        if (volume >= 1000000) {
            return (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(1) + 'K';
        }
        return volume.toString();
    }
    
    formatMarketCap(marketCap) {
        const value = parseFloat(marketCap);
        if (value >= 1000000000000) {
            return (value / 1000000000000).toFixed(1) + 'T';
        } else if (value >= 1000000000) {
            return (value / 1000000000).toFixed(1) + 'B';
        } else if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
        }
        return value.toFixed(0);
    }
}

// 全局实例
let stockMonitor;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    stockMonitor = new StockMonitor();
});